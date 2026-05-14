"""
Base Agent class - all agents inherit from this.
Provides common functionality for scanning, logging, and LLM interaction.

Supports:
  - Single file analysis (traditional)
  - Batch file analysis (multiple files per LLM call)
  - Tiered analysis (fast scan → deep scan for suspicious files)
  - Incremental analysis (skip unchanged files)
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models import Finding, FindingType, Severity, AgentType
from backend.llm_router import llm_json, llm_call
from backend.batch_analyzer import (
    group_files_by_type, create_batches, build_batch_prompt,
    parse_batch_findings, analyze_batch
)
from backend.session_store import get_store
from backend.constants import IGNORE_DIRS


class BaseAgent(ABC):
    """Base class for all audit agents."""
    
    agent_type: AgentType = AgentType.AUDITOR
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.store = get_store()
        self.findings: List[Finding] = []
    
    async def log(self, message: str, level: str = "info"):
        """Log an activity."""
        await self.store.log_activity(
            self.session_id,
            self.agent_type.value,
            message,
            level
        )
    
    @abstractmethod
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan the project and return findings."""
        pass
    
    def _get_files(self, project_path: str, extensions: List[str]) -> List[Path]:
        """Get all files with given extensions."""
        path = Path(project_path)
        files = []
        
        for ext in extensions:
            for file_path in path.rglob(f"*.{ext}"):
                if any(part in IGNORE_DIRS for part in file_path.parts):
                    continue
                files.append(file_path)
        
        return files
    
    def _read_file(self, file_path: Path, max_size: int = 50000) -> str:
        """Read file content safely."""
        try:
            if file_path.stat().st_size > max_size:
                return file_path.read_text(errors='ignore')[:max_size]
            return file_path.read_text(errors='ignore')
        except Exception as e:
            return f"Error reading file: {e}"
    
    async def _analyze_with_llm(
        self,
        prompt: str,
        model: str = "gemini-flash"
    ) -> Dict[str, Any]:
        """Analyze with LLM and return structured JSON."""
        try:
            return await llm_json(prompt, model=model)
        except Exception as e:
            await self.log(f"LLM analysis failed: {e}", "error")
            return {}

    async def _scan_files_batched(
        self,
        project_path: str,
        extensions: List[str],
        analysis_prompt: str,
        agent_name: str = "Code Auditor",
        model: str = "gemini-flash",
        files_override: Optional[List[str]] = None,
    ) -> List[Finding]:
        """
        Scan files using batched LLM calls.

        Groups files by type, creates batches that fit within token limits,
        and analyzes each batch with a single LLM call.

        Args:
            project_path: Path to the project
            extensions: File extensions to include
            analysis_prompt: The analysis prompt for the LLM
            agent_name: Name displayed in logs
            model: LLM model to use
            files_override: Use these files instead of scanning (for incremental)

        Returns:
            List of findings
        """
        path = Path(project_path)

        # Read file helper
        def read_file(rel_path: str) -> str:
            fp = path / rel_path
            try:
                return fp.read_text(errors="ignore")
            except Exception:
                return ""

        # Get files
        if files_override:
            all_files = files_override
        else:
            all_files = [str(f.relative_to(path)) for f in self._get_files(project_path, extensions)]

        if not all_files:
            return []

        await self.log(f"Analyzing {len(all_files)} files in batches...")

        # Group files by type for better batching
        groups = group_files_by_type(all_files)
        all_batches = []
        for group_name, group_files in groups.items():
            if not group_files:
                continue
            batches = create_batches(group_files, read_file)
            for batch in batches:
                all_batches.append((group_name, batch))

        findings = []
        for i, (group_name, batch_files) in enumerate(all_batches):
            try:
                batch_findings = await analyze_batch(
                    batch_files,
                    read_file,
                    analysis_prompt,
                    agent_name,
                    model
                )

                for bd in batch_findings:
                    if "error" in bd:
                        await self.log(f"Batch {i+1} error: {bd['error']}", "warning")
                        continue

                    finding = self._create_finding(
                        title=bd.get("title", "Unknown issue"),
                        description=bd.get("description", ""),
                        severity=Severity(bd.get("severity", "medium")),
                        finding_type=FindingType(bd.get("type", "code_quality")),
                        location={"file": bd.get("file", ""), "line_start": bd.get("line_start")},
                        code_snippet=bd.get("code_snippet", ""),
                        suggested_fix=bd.get("suggested_fix", "")
                    )
                    findings.append(finding)

                await self.log(f"Batch {i+1}/{len(all_batches)}: {len(batch_findings)} findings in {group_name}")

            except Exception as e:
                await self.log(f"Batch {i+1} failed: {e}", "error")

        return self._deduplicate_findings(findings)

    async def _tiered_scan(
        self,
        project_path: str,
        extensions: List[str],
        fast_prompt: str,
        deep_prompt: str,
        agent_name: str = "Code Auditor",
        fast_model: str = "gemini-flash",
        deep_model: str = "gemini-pro",
        suspicious_files: Optional[List[str]] = None,
    ) -> List[Finding]:
        """
        Two-tier analysis:
          1. Fast scan (Gemini Flash) on ALL files — catches obvious issues
          2. Deep scan (Gemini Pro) on suspicious files only — thorough analysis

        Args:
            project_path: Path to the project
            extensions: File extensions to include
            fast_prompt: Prompt for initial fast scan
            deep_prompt: Prompt for deep analysis
            agent_name: Name displayed in logs
            fast_model: Model for fast scan
            deep_model: Model for deep scan
            suspicious_files: Files to deep scan (if None, uses files with findings from fast scan)

        Returns:
            Combined findings from both tiers
        """
        # Tier 1: Fast scan
        await self.log(f"Tier 1: Fast scan with {fast_model}...")
        fast_findings = await self._scan_files_batched(
            project_path, extensions, fast_prompt, agent_name, fast_model
        )
        await self.log(f"Tier 1 complete: {len(fast_findings)} findings")

        # Determine which files need deep scan
        if suspicious_files is None:
            # Deep scan files that had findings in the fast scan
            files_with_findings = set()
            for f in fast_findings:
                loc_file = f.location.get("file", "")
                if loc_file:
                    files_with_findings.add(loc_file)
                # Also deep scan files mentioned in the context
                if f.severity in (Severity.CRITICAL, Severity.HIGH):
                    if loc_file:
                        files_with_findings.add(loc_file)
            suspicious_files = list(files_with_findings)

        if not suspicious_files:
            await self.log("No files need deep analysis", "success")
            return fast_findings

        # Filter to files that actually exist
        path = Path(project_path)
        existing_suspicious = [f for f in suspicious_files if (path / f).exists()]

        if not existing_suspicious:
            await self.log("No suspicious files exist on disk", "success")
            return fast_findings

        # Tier 2: Deep scan on suspicious files only
        await self.log(f"Tier 2: Deep scan {len(existing_suspicious)} files with {deep_model}...")
        deep_findings = await self._scan_files_batched(
            project_path, extensions, deep_prompt, agent_name, deep_model,
            files_override=existing_suspicious
        )
        await self.log(f"Tier 2 complete: {len(deep_findings)} findings")

        # Merge: prefer deep findings for same files, keep fast findings for others
        # Simple merge — deduplicate by file + title
        seen = set()
        merged = []
        # Deep findings first (higher quality)
        for f in deep_findings:
            key = f"{f.location.get('file', '')}:{f.title[:30]}"
            if key not in seen:
                seen.add(key)
                merged.append(f)
        # Add fast findings that don't overlap
        for f in fast_findings:
            key = f"{f.location.get('file', '')}:{f.title[:30]}"
            if key not in seen:
                seen.add(key)
                merged.append(f)

        total_fast = len(fast_findings)
        total_deep = len(deep_findings)
        await self.log(f"Merged: {total_fast} fast + {total_deep} deep → {len(merged)} unique findings", "success")

        return self._sort_by_severity(merged)
    
    def _create_finding(
        self,
        title: str,
        description: str,
        severity: Severity,
        finding_type: FindingType,
        location: Dict[str, Any],
        code_snippet: str = "",
        suggested_fix: str = ""
    ) -> Finding:
        """Create a finding with proper metadata."""
        return Finding(
            title=title,
            description=description,
            type=finding_type,
            severity=severity,
            agent=self.agent_type,
            location=location,
            code_snippet=code_snippet[:2000],  # Cap size
            suggested_fix=suggested_fix
        )
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on location and title."""
        seen = set()
        unique = []
        
        for f in findings:
            key = f"{f.title}:{f.location.get('file', '')}:{f.location.get('line_start', 0)}"
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique
    
    def _sort_by_severity(self, findings: List[Finding]) -> List[Finding]:
        """Sort findings by severity (critical first)."""
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        return sorted(findings, key=lambda f: severity_order.get(f.severity, 5))
