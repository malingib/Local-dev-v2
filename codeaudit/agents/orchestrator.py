"""
Orchestrator - runs the full audit pipeline.
Manages parallel agent execution, merges findings, drives the session state machine.

Features:
  - Incremental analysis (skips unchanged files)
  - Batched file analysis (multiple files per LLM call)
  - Tiered analysis (fast scan → deep scan for suspicious files)
"""
import asyncio
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from backend.models import (
    Session, SessionState, SessionMode, Finding, FindingStatus,
    ProjectInfo, AgentType, Severity
)
from backend.session_store import get_store
from backend.config import get_config
from backend.incremental import (
    compute_all_file_hashes, load_previous_hashes, save_current_hashes,
    detect_changed_files, get_incremental_stats
)
from agents.stack_detector import detect_stack
from agents.auditor import AuditorAgent
from agents.ui_agent import UIAgent
from agents.security_agent import SecurityAgent
from agents.performance_agent import PerformanceAgent
from agents.mobile_agent import MobileAgent
from backend.constants import ALL_AUDIT_EXTENSIONS


class Orchestrator:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.store = get_store()
        self.config = get_config()

    async def log(self, message: str, level: str = "info"):
        await self.store.log_activity(self.session_id, "orchestrator", message, level)

    async def run_ingest(self, project_path: str) -> Session:
        session = await self.store.get(self.session_id)
        session.state = SessionState.INGEST
        await self.store.update(session)

        await self.log(f"Ingesting project: {project_path}")

        # Detect stack
        await self.log("Detecting tech stack...")
        stack_info = detect_stack(project_path)
        await self.log(f"Detected: {', '.join(stack_info['stack']) or 'unknown'}", "success")

        # Build project info
        project = ProjectInfo(
            name=Path(project_path).name,
            path=project_path,
            detected_stack=stack_info["stack"],
            routes=stack_info.get("routes", []),
        )

        session.project = project
        session.state = SessionState.AUDIT
        await self.store.update(session)
        await self.store.log_event(self.session_id, "ingest_complete", stack_info)

        return session

    async def run_audit(self, project_path: str) -> Session:
        session = await self.store.get(self.session_id)
        enabled = self.config.enabled_agents

        # ─── Incremental analysis check ──────────────────────────────────────
        all_extensions = ALL_AUDIT_EXTENSIONS
        changes = detect_changed_files(project_path, all_extensions)
        unchanged = changes.get("unchanged", [])
        changed = changes.get("changed", [])
        new_files = changes.get("new", [])

        if unchanged:
            await self.log(
                f"Incremental: {len(unchanged)} unchanged, "
                f"{len(changed)} changed, {len(new_files)} new files"
            )

        # ─── Tiered analysis decision ────────────────────────────────────────
        use_tiered = self.config.default_model == "gemini-pro"

        # Run all enabled agents in parallel
        tasks = []

        if "auditor" in enabled:
            agent = AuditorAgent(self.session_id)
            if use_tiered:
                tasks.append(("auditor", self._run_tiered_audit(agent, project_path, unchanged)))
            else:
                tasks.append(("auditor", agent.scan(project_path)))
        if "ui" in enabled:
            agent = UIAgent(self.session_id)
            if use_tiered:
                tasks.append(("ui", self._run_tiered_ui(agent, project_path, unchanged)))
            else:
                tasks.append(("ui", agent.scan(project_path)))
        if "security" in enabled:
            agent = SecurityAgent(self.session_id)
            if use_tiered:
                tasks.append(("security", self._run_tiered_security(agent, project_path, unchanged)))
            else:
                tasks.append(("security", agent.scan(project_path)))
        if "performance_static" in enabled:
            tasks.append(("performance", PerformanceAgent(self.session_id).scan(project_path)))
        if "mobile_responsiveness" in enabled:
            tasks.append(("mobile", MobileAgent(self.session_id).scan(project_path)))

        # Execute all in parallel
        await self.log("Starting parallel agent scan...")
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        all_findings = []
        for (name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                await self.log(f"{name} agent error: {result}", "warning")
            else:
                await self.log(f"{name}: {len(result)} findings", "success")
                all_findings.extend(result)

        # Merge and deduplicate
        merged = self._merge_findings(all_findings)

        # Save file hashes for next incremental scan
        await self.log(f"Saving file hashes for incremental analysis...")
        current_hashes = compute_all_file_hashes(project_path, all_extensions)
        save_current_hashes(project_path, current_hashes)

        session.findings = merged
        session.state = SessionState.AUDIT
        await self.store.update(session)
        await self.log(f"Audit complete: {len(merged)} total findings", "success")

        # Log incremental stats
        stats = get_incremental_stats(project_path, all_extensions)
        await self.log(
            f"Next scan savings: {stats['scan_savings_percent']}% "
            f"({stats['unchanged_files']}/{stats['total_files']} files unchanged)"
        )

        return session

    # ─── Tiered analysis helpers ───────────────────────────────────────────────

    async def _run_tiered_audit(self, agent, project_path: str, unchanged: List[str]) -> List[Finding]:
        """Run tiered audit: Flash fast scan → Pro deep scan on findings."""
        return await agent._tiered_scan(
            project_path,
            ["py", "js", "jsx", "ts", "tsx"],
            fast_prompt="""Analyze these files for bugs, logic errors, dead code, and anti-patterns.
Return findings as JSON array with: file, line_start, title, severity (critical/high/medium/low/info),
type (bug/security/performance/code_quality/best_practice), description, suggested_fix, code_snippet.""",
            deep_prompt="""Perform a deep code review of these files. Analyze:
1. Logic errors and edge cases
2. Error handling gaps
3. Resource leaks (memory, file handles, connections)
4. Dead code and unused imports
5. Anti-patterns and architectural issues
6. Type safety issues
Return findings as JSON array with: file, line_start, title, severity, type, description, suggested_fix, code_snippet.""",
            agent_name="Code Auditor",
            fast_model="gemini-flash",
            deep_model="gemini-pro",
        )

    async def _run_tiered_ui(self, agent, project_path: str, unchanged: List[str]) -> List[Finding]:
        """Run tiered UI analysis."""
        return await agent._tiered_scan(
            project_path,
            ["tsx", "jsx", "vue", "svelte", "html"],
            fast_prompt="""Analyze these UI files for accessibility issues, design problems, and missing semantic elements.
Return findings as JSON array with: file, line_start, title, severity, type, description, suggested_fix, code_snippet.""",
            deep_prompt="""Deep UI review:
1. WCAG 2.1 AA compliance (contrast, ARIA labels, focus management, keyboard navigation)
2. Semantic HTML usage
3. Responsive design issues
4. Missing alt text, labels, and descriptions
5. Color contrast ratios
6. Touch target sizes
Return findings as JSON array with: file, line_start, title, severity, type, description, suggested_fix, code_snippet.""",
            agent_name="UI Agent",
        )

    async def _run_tiered_security(self, agent, project_path: str, unchanged: List[str]) -> List[Finding]:
        """Run tiered security analysis."""
        return await agent._tiered_scan(
            project_path,
            ["py", "js", "jsx", "ts", "tsx", "html", "env"],
            fast_prompt="""Analyze these files for security vulnerabilities: secrets, injection attacks, XSS, auth gaps.
Return findings as JSON array with: file, line_start, title, severity, type, description, suggested_fix, code_snippet.""",
            deep_prompt="""Deep security audit:
1. SQL/NoSQL injection vectors
2. XSS and CSRF vulnerabilities
3. Authentication and authorization gaps
4. Secrets in code/config files
5. Insecure dependencies
6. Input validation gaps
7. Rate limiting and DoS protection
Return findings as JSON array with: file, line_start, title, severity, type, description, suggested_fix, code_snippet.""",
            agent_name="Security Agent",
        )

    async def run_fix_finding(self, finding_id: str, project_path: str) -> Session:
        session = await self.store.get(self.session_id)
        finding = next((f for f in session.findings if f.id == finding_id), None)

        if not finding:
            await self.log(f"Finding {finding_id} not found", "error")
            return session

        # Delegate complex findings to Swarm if enabled
        if getattr(self.config, "use_swarm", False):
            await self.log(f"Delegating complex finding to Swarm: {finding.title}")
            from backend.swarm_api import get_coordinator
            swarm = get_coordinator()
            await swarm.start()

            task_id = await swarm.submit_task(
                description=f"Fix finding: {finding.title}\nDescription: {finding.description}\nLocation: {finding.location}",
                task_type="fix_finding",
                priority="high"
            )
            await self.log(f"Swarm task submitted: {task_id}")
            # In a real system, we'd wait for completion. For now, we continue traditional path as fallback or parallel.

        # Auto-approve check
        if self._is_auto_approvable(finding):
            await self.log(f"Auto-approving: {finding.title}")
            finding.status = FindingStatus.APPROVED
            await self._apply_auto_fix(finding, project_path)
            finding.status = FindingStatus.APPLIED
            await self.store.update(session)
            return session

        # Run hypothesis loop
        session.state = SessionState.HYPOTHESIS_LOOP
        session.current_finding_id = finding_id
        await self.store.update(session)

        from agents.hypothesis_engine import HypothesisEngine
        engine = HypothesisEngine(self.session_id, self.config.max_steps)
        updated_finding = await engine.run(finding, project_path)

        # Update finding in session
        for i, f in enumerate(session.findings):
            if f.id == finding_id:
                session.findings[i] = updated_finding
                break

        if updated_finding.status == FindingStatus.AWAITING_APPROVAL:
            session.state = SessionState.APPROVAL_FLOW
            session.approval_queue.append(finding_id)
        elif updated_finding.status == FindingStatus.ESCALATED:
            session.state = SessionState.AUDIT

        await self.store.update(session)
        return session

    async def apply_patch(self, finding_id: str, project_path: str) -> bool:
        session = await self.store.get(self.session_id)
        finding = next((f for f in session.findings if f.id == finding_id), None)

        if not finding or not finding.proposed_patch:
            return False

        import json as json_mod
        try:
            changes = json_mod.loads(finding.proposed_patch)
            path = Path(project_path)

            for change in changes:
                fp = path / change.get("file", "")
                if not fp.exists():
                    await self.log(f"Skipped missing file: {change.get('file', '')}", "warning")
                    continue

                content = fp.read_text(errors="ignore")
                find_text = change.get("find", "")
                replace_text = change.get("replace", "")
                line_start = change.get("line_start")
                line_end = change.get("line_end")

                if not find_text:
                    await self.log(f"Empty find text in patch for {change.get('file', '')}", "warning")
                    continue

                if find_text not in content:
                    await self.log(f"Find text not found in {change.get('file', '')} — skipping", "warning")
                    continue

                occurrences = content.count(find_text)
                if occurrences > 1:
                    if line_start is not None:
                        lines = content.splitlines(True)
                        target = find_text.rstrip("\n")
                        replaced = False
                        for i in range(len(lines)):
                            if target in lines[i]:
                                lines[i] = lines[i].replace(target, replace_text.rstrip("\n"), 1)
                                replaced = True
                                break
                        if replaced:
                            new_content = "".join(lines)
                        else:
                            await self.log(f"Line-based fallback failed for {change['file']}", "warning")
                            continue
                    else:
                        await self.log(f"{occurrences} matches in {change['file']} — using first occurrence", "warning")
                        new_content = content.replace(find_text, replace_text, 1)
                else:
                    new_content = content.replace(find_text, replace_text, 1)

                fp.write_text(new_content)
                await self.log(f"Patched: {change['file']}", "success")

            finding.status = FindingStatus.APPLIED
            for i, f in enumerate(session.findings):
                if f.id == finding_id:
                    session.findings[i] = finding
                    break

            await self.store.update(session)
            return True

        except Exception as e:
            await self.log(f"Patch apply failed: {e}", "error")
            return False

    def _merge_findings(self, findings: List[Finding]) -> List[Finding]:
        """Deduplicate and sort by severity."""
        seen = set()
        unique = []
        for f in findings:
            key = f"{f.type}:{f.location.get('file', '')}:{f.title[:30]}"
            if key not in seen:
                seen.add(key)
                unique.append(f)

        severity_order = {
            Severity.CRITICAL: 0, Severity.HIGH: 1,
            Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4
        }
        return sorted(unique, key=lambda f: severity_order.get(f.severity, 5))

    def _is_auto_approvable(self, finding: Finding) -> bool:
        auto = self.config.auto_approve
        return (
            (auto.get("missing_alt_text") and "alt text" in finding.title.lower()) or
            (auto.get("missing_meta_viewport") and "viewport" in finding.title.lower()) or
            (auto.get("missing_lazy_loading") and "lazy loading" in finding.title.lower()) or
            (auto.get("input_type_fix") and "input type" in finding.title.lower()) or
            finding.auto_approvable
        )

    async def _apply_auto_fix(self, finding: Finding, project_path: str):
        """Apply simple auto-fixes that don't need approval."""
        path = Path(project_path)
        file_path = finding.location.get("file", "")
        if not file_path:
            return

        fp = path / file_path
        if not fp.exists():
            return

        content = fp.read_text(errors="ignore")

        # Add loading="lazy" to images
        if "lazy loading" in finding.title.lower():
            import re
            new_content = re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy"', content)
            if new_content != content:
                fp.write_text(new_content)
                await self.log(f"Added lazy loading to images in {file_path}", "success")

        # Fix input types
        elif "input type" in finding.title.lower():
            new_content = content
            if 'type="text"' in content and "email" in content.lower():
                new_content = content.replace(
                    'type="text"', 'type="email"', 1
                )
            if new_content != content:
                fp.write_text(new_content)
                await self.log(f"Fixed input type in {file_path}", "success")
