"""
Skills library - predefined and custom skills for AI-assisted development.
Inspired by Hermes Desktop's skill system.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


# ─── Data directory ──────────────────────────────────────────────────────────

def _get_skills_dir() -> Path:
    env_dir = os.environ.get("CODEAUDIT_SKILLS_DIR")
    if env_dir:
        d = Path(env_dir)
    else:
        d = Path.home() / ".codeaudit" / "skills"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── Model ────────────────────────────────────────────────────────────────────

class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    category: str = "code-review"
    prompt_template: str = ""
    tags: List[str] = Field(default_factory=list)
    program_md: str = ""
    time_budget: int = 300
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


CATEGORIES = [
    "code-review",
    "testing",
    "security",
    "performance",
    "frontend",
    "devops",
    "data-science",
    "research",
    "autoresearch",
]

# ─── Predefined skills ──────────────────────────────────────────────────────

SKILLS_CATALOG: List[Dict[str, Any]] = [
    # code-review (3)
    {
        "id": "skill_cr_01",
        "name": "Code Review",
        "description": "Review code for bugs, style issues, and adherence to best practices. Provides line-level feedback with severity ratings.",
        "category": "code-review",
        "prompt_template": "Review the following code for bugs, style issues, security concerns, and best practices. For each issue, provide: file, line, severity (critical/high/medium/low), description, and suggested fix.\n\n```\n{code}\n```",
        "tags": ["review", "quality", "best-practices"],
    },
    {
        "id": "skill_cr_02",
        "name": "Dependency Review",
        "description": "Analyze project dependencies for outdated packages, compatibility issues, and security advisories.",
        "category": "code-review",
        "prompt_template": "Analyze the dependencies listed below. Check for: outdated versions, known vulnerabilities, breaking changes in major versions, and newer alternatives.\n\n{dependencies}",
        "tags": ["dependencies", "outdated", "compatibility"],
    },
    {
        "id": "skill_cr_03",
        "name": "Best Practices Audit",
        "description": "Audit codebase against language/framework best practices and community conventions.",
        "category": "code-review",
        "prompt_template": "Audit this code for adherence to {language}/{framework} best practices. Check: naming conventions, file structure, error handling, documentation, and common anti-patterns.\n\n{code}",
        "tags": ["best-practices", "conventions", "audit"],
    },
    # testing (3)
    {
        "id": "skill_test_01",
        "name": "Unit Test Generator",
        "description": "Generate comprehensive unit tests for functions and classes with edge case coverage.",
        "category": "testing",
        "prompt_template": "Write unit tests for the following {language} code. Cover: happy path, edge cases, error conditions, and boundary values. Use {test_framework} syntax.\n\n```\n{code}\n```",
        "tags": ["unit-test", "generation", "edge-cases"],
    },
    {
        "id": "skill_test_02",
        "name": "Integration Test Planner",
        "description": "Design integration test scenarios for service interactions and API endpoints.",
        "category": "testing",
        "prompt_template": "Design integration tests for the following API or service interface. Include: request/response validation, error propagation, timeout handling, and data flow verification.\n\n{specification}",
        "tags": ["integration-test", "api", "planning"],
    },
    {
        "id": "skill_test_03",
        "name": "Test Coverage Analysis",
        "description": "Identify untested code paths and suggest tests to improve coverage metrics.",
        "category": "testing",
        "prompt_template": "Analyze the test coverage report below. Identify: untested branches, missing edge cases, unused code paths, and suggest specific tests to add.\n\n{coverage_report}",
        "tags": ["coverage", "analysis", "quality"],
    },
    # security (3)
    {
        "id": "skill_sec_01",
        "name": "Vulnerability Scanner",
        "description": "Scan code for OWASP Top 10 vulnerabilities and common security flaws.",
        "category": "security",
        "prompt_template": "Scan the following code for security vulnerabilities. Check for: injection flaws, broken authentication, sensitive data exposure, XXE, broken access control, security misconfiguration, XSS, insecure deserialization, and known vulnerable components.\n\n{code}",
        "tags": ["vulnerability", "owasp", "injection", "xss"],
    },
    {
        "id": "skill_sec_02",
        "name": "Secret Detection",
        "description": "Detect hardcoded secrets, API keys, tokens, and credentials in source code.",
        "category": "security",
        "prompt_template": "Check the following content for hardcoded secrets: API keys, passwords, tokens, private keys, connection strings, and any credential-like patterns. Flag each finding with its location and type.\n\n{content}",
        "tags": ["secrets", "credentials", "detection"],
    },
    {
        "id": "skill_sec_03",
        "name": "Supply Chain Audit",
        "description": "Audit third-party dependencies for known vulnerabilities and license compliance.",
        "category": "security",
        "prompt_template": "Audit the following dependency manifest for: known CVEs, deprecated packages, license compliance issues, and maintainer activity concerns.\n\n{manifest}",
        "tags": ["supply-chain", "dependencies", "cve", "license"],
    },
    # performance (3)
    {
        "id": "skill_perf_01",
        "name": "Performance Profiler",
        "description": "Identify performance bottlenecks in code: N+1 queries, memory leaks, slow algorithms.",
        "category": "performance",
        "prompt_template": "Profile the following code for performance issues. Look for: inefficient algorithms, N+1 queries, memory allocation hot spots, unnecessary I/O, cache misses, and concurrency bottlenecks.\n\n{code}",
        "tags": ["profiling", "bottlenecks", "optimization"],
    },
    {
        "id": "skill_perf_02",
        "name": "Database Query Optimization",
        "description": "Optimize SQL queries: missing indexes, full table scans, suboptimal joins.",
        "category": "performance",
        "prompt_template": "Review the following database queries for optimization opportunities. Check: missing indexes, full table scans, inefficient joins, subquery optimizations, connection pooling, and query plan analysis.\n\n{queries}",
        "tags": ["database", "sql", "indexes", "optimization"],
    },
    {
        "id": "skill_perf_03",
        "name": "Memory Analysis",
        "description": "Analyze memory usage patterns and identify leaks or excessive allocation.",
        "category": "performance",
        "prompt_template": "Analyze the memory profile below. Identify: memory leaks, excessive allocation, reference cycles, buffer growth patterns, and cache management issues.\n\n{memory_profile}",
        "tags": ["memory", "leaks", "allocation"],
    },
    # frontend (3)
    {
        "id": "skill_fe_01",
        "name": "UI/UX Review",
        "description": "Review user interfaces for consistency, usability, and accessibility issues.",
        "category": "frontend",
        "prompt_template": "Review the following UI code for: accessibility violations (WCAG 2.1), usability issues, visual consistency, responsive design, loading states, and error handling.\n\n{code}",
        "tags": ["ui", "ux", "accessibility", "wcag"],
    },
    {
        "id": "skill_fe_02",
        "name": "Accessibility Checker",
        "description": "Check HTML/CSS for WCAG compliance: ARIA attributes, color contrast, keyboard navigation.",
        "category": "frontend",
        "prompt_template": "Check the following markup for WCAG 2.1 AA compliance. Verify: semantic HTML, ARIA attributes, keyboard navigation, focus management, color contrast, screen reader announcements, and touch targets.\n\n{markup}",
        "tags": ["a11y", "wcag", "aria", "keyboard"],
    },
    {
        "id": "skill_fe_03",
        "name": "Responsive Design Validator",
        "description": "Validate responsive breakpoints, fluid layouts, and mobile-first patterns.",
        "category": "frontend",
        "prompt_template": "Review the CSS/layout for responsive design issues. Check: breakpoint coverage, fluid typography, touch-friendly targets, overflow handling, and mobile-first approach.\n\n{code}",
        "tags": ["responsive", "mobile", "css", "layout"],
    },
    # devops (3)
    {
        "id": "skill_devops_01",
        "name": "Dockerfile Review",
        "description": "Review Dockerfiles for efficiency, security, and best practices.",
        "category": "devops",
        "prompt_template": "Review this Dockerfile for: layer optimization, image size reduction, security best practices (no root, minimal base), build cache usage, and multi-stage build opportunities.\n\n{dockerfile}",
        "tags": ["docker", "container", "image", "optimization"],
    },
    {
        "id": "skill_devops_02",
        "name": "CI/CD Pipeline Review",
        "description": "Review CI/CD configuration for reliability, speed, and security gates.",
        "category": "devops",
        "prompt_template": "Review this CI/CD configuration for: pipeline efficiency, caching strategy, parallel job opportunities, security scanning gates, deployment safety checks, and rollback procedures.\n\n{config}",
        "tags": ["ci-cd", "pipeline", "automation", "deployment"],
    },
    {
        "id": "skill_devops_03",
        "name": "Infrastructure as Code Review",
        "description": "Review Terraform/CloudFormation/Pulumi for security and reliability.",
        "category": "devops",
        "prompt_template": "Review this infrastructure definition for: security group rules, IAM least privilege, resource tagging, state management, cost optimization, and high availability patterns.\n\n{infra_code}",
        "tags": ["iac", "terraform", "cloud", "infrastructure"],
    },
    # data-science (2)
    {
        "id": "skill_ds_01",
        "name": "Data Quality Check",
        "description": "Validate data pipelines for quality: missing values, outliers, schema violations.",
        "category": "data-science",
        "prompt_template": "Analyze the data pipeline for quality issues. Check: missing value handling, outlier detection, schema validation, data type consistency, normalization, and bias assessment.\n\n{pipeline_code}",
        "tags": ["data-quality", "validation", "pipeline"],
    },
    {
        "id": "skill_ds_02",
        "name": "Model Review",
        "description": "Review ML model code for correctness, performance, and reproducibility.",
        "category": "data-science",
        "prompt_template": "Review this ML model implementation for: data leakage, proper train/test split, metric selection, hyperparameter validation, reproducibility, and model serialization.\n\n{model_code}",
        "tags": ["machine-learning", "model", "reproducibility"],
    },
    # research (2)
    {
        "id": "skill_res_01",
        "name": "Literature Review",
        "description": "Research and summarize relevant papers, articles, and documentation.",
        "category": "research",
        "prompt_template": "Research the following topic. Provide: key papers and their contributions, current state of the art, open problems, and practical implications. Format as a structured summary.\n\n{topic}",
        "tags": ["research", "papers", "survey"],
    },
    {
        "id": "skill_res_02",
        "name": "Architecture Analysis",
        "description": "Analyze software architecture: patterns, trade-offs, and improvement suggestions.",
        "category": "research",
        "prompt_template": "Analyze the following architecture description. Identify: architectural patterns in use, trade-offs made, potential scalability bottlenecks, coupling concerns, and improvement suggestions.\n\n{architecture}",
        "tags": ["architecture", "design", "patterns", "analysis"],
    },
    # design (4) — inspired by ui-ux-pro-max, huashu-design, taste-skill
    {
        "id": "skill_design_01",
        "name": "Design System Intelligence",
        "description": "Curated UI styles (glassmorphism, neumorphism, bento grid, etc.), 10 color palettes per industry, 10 font pairings. Suggests design direction per project type. Inspired by ui-ux-pro-max-skill (77k★).",
        "category": "autoresearch",
        "prompt_template": "Suggest a design direction for {project_type}. Consider: style ({styles}), palette by industry ({palettes}), font pairing ({fonts}). Provide CSS snippets and rationale.",
        "tags": ["design", "ui-ux", "styles", "palettes", "fonts"],
        "time_budget": 30,
    },
    {
        "id": "skill_design_02",
        "name": "HTML Prototype Generator",
        "description": "Generate interactive HTML prototypes from screen descriptions. Supports mobile frame, slide decks, and design reviews. Inspired by huashu-design (6.6k★).",
        "category": "autoresearch",
        "prompt_template": "Generate an interactive HTML prototype for: {description}. Style: {style}. Include {screen_count} screens with navigation between them. Make it clickable and realistic.",
        "tags": ["design", "prototype", "html", "huashu"],
        "time_budget": 120,
    },
    {
        "id": "skill_design_03",
        "name": "Anti-Slop Design Audit",
        "description": "Check for 30+ AI slop patterns and design anti-patterns: purple gradients, bounce easing, card-in-card, generic fonts, missing hover states, and more. Inspired by impeccable (20k★) + taste-skill (15k★).",
        "category": "autoresearch",
        "prompt_template": "Audit the following UI code for AI slop patterns and design anti-patterns. Check for: purple/indigo gradients, bounce easing, card-in-card nesting, generic fonts (Inter/Poppins/Roboto), pure black/white colors, missing focus styles, and over-rounded corners.\n\n{code}",
        "tags": ["design", "audit", "anti-patterns", "ai-slop"],
        "time_budget": 60,
    },
    {
        "id": "skill_design_04",
        "name": "Self-Improving Agent Loop",
        "description": "HALO-style recursive self-improvement: trace agent runs, analyze patterns, generate improvements, apply automatically, benchmark results. Inspired by context-labs/HALO (246★).",
        "category": "autoresearch",
        "prompt_template": "Run a self-improvement loop for agent {agent_name}. Collect traces, analyze failure patterns, generate improvement suggestions, apply top 3, and benchmark before/after. Target file: {target_file}.",
        "tags": ["self-improve", "halo", "agent-loop", "optimization"],
        "time_budget": 600,
    },
    # autoresearch (4) — inspired by karpathy/autoresearch
    {
        "id": "skill_auto_01",
        "name": "AutoExperiment Runner",
        "description": "Autonomous experiment loop: modifies code, runs with time budget, evaluates metric, keeps/discards. Based on karpathy/autoresearch.",
        "category": "autoresearch",
        "prompt_template": "You are an autonomous research agent running a fixed-time-budget experiment. Target file: {target_file}. Goal: improve {metric}. Run experiments in {time_budget}s windows, keep improvements, discard regressions.",
        "program_md": "# AutoExperiment Runner\n\n## Setup\n1. Read the target file: {target_file}\n2. Establish baseline by running without modifications\n3. Log all results to results.tsv\n\n## Experimentation\nEach experiment runs for {time_budget} seconds wall-clock time. The metric is {metric} (lower is better).\n\n**What you CAN do:**\n- Modify {target_file} — architecture, logic, hyperparameters\n\n**What you CANNOT do:**\n- Modify core framework files\n- Install new packages\n\n## Loop\nLOOP FOREVER:\n1. Propose a change\n2. Apply the change\n3. Run the experiment\n4. If metric improved → KEEP the change\n5. If metric regressed → DISCARD (revert)\n6. Log result to TSV\n7. Repeat",
        "tags": ["autoresearch", "experiment", "autonomous", "loop"],
        "time_budget": 300,
    },
    {
        "id": "skill_auto_02",
        "name": "program.md Generator",
        "description": "Generate program.md-style agent instruction files that define experiment protocols, like karpathy/autoresearch.",
        "category": "autoresearch",
        "prompt_template": "Generate a program.md file for an autonomous experiment. Include: setup instructions, experimentation protocol, output format, and the experiment loop. Target: {target}. Metric: {metric}. Time budget: {time_budget}s.",
        "program_md": "# program.md Generator\n\nGenerate a markdown instruction file that an AI agent can follow autonomously.\nThe file should define:\n1. What files the agent can modify\n2. What files are read-only\n3. The metric to optimize\n4. The time budget per experiment\n5. The experiment loop (modify → run → evaluate → keep/discard)\n6. Output format for results",
        "tags": ["autoresearch", "program-md", "instructions", "protocol"],
        "time_budget": 60,
    },
    {
        "id": "skill_auto_03",
        "name": "Self-Modifying Agent",
        "description": "Agent that can improve its own source code based on experiment outcomes. Enables recursive self-improvement.",
        "category": "autoresearch",
        "prompt_template": "You are a self-modifying agent. Review your own source code ({agent_file}) and propose improvements based on recent experiment results. Focus on: better experiment logic, improved evaluation, efficiency gains.",
        "program_md": "# Self-Modifying Agent\n\nYou have the ability to modify your own source code. This enables recursive self-improvement.\n\n## Guidelines\n1. Review your source code periodically\n2. Identify bottlenecks, bugs, or improvement opportunities\n3. Propose and apply changes to yourself\n4. Verify the changes work by running experiments\n5. If a self-modification degrades performance, revert it\n\n## Caution\n- Make incremental changes, not large rewrites\n- Always verify after changing yourself\n- Keep a backup of working versions",
        "tags": ["autoresearch", "self-modify", "recursive", "improvement"],
        "time_budget": 600,
    },
    {
        "id": "skill_auto_04",
        "name": "Experiment Tracking Dashboard",
        "description": "Log, track, and visualize experiment results in TSV format with baseline comparison, keep/discard decisions, and history.",
        "category": "autoresearch",
        "prompt_template": "Track experiments for project {project}. Log results to results.tsv with columns: commit, {metric}, memory_gb, status (keep/discard/crash), description. Compare against baseline: {baseline}.",
        "program_md": "# Experiment Tracking\n\nLog all experiments to a TSV file with these columns:\n- commit: git commit hash (7 chars)\n- val_bpb: the metric value (lower is better)\n- memory_gb: peak memory usage\n- status: keep, discard, or crash\n- description: what this experiment tried\n\n## Example\n```\ncommit\tval_bpb\tmemory_gb\tstatus\tdescription\na1b2c3d\t0.9979\t44.0\tkeep\tbaseline\nb2c3d4e\t0.9932\t44.2\tkeep\tincrease LR to 0.04\n```",
        "tags": ["autoresearch", "tracking", "tsv", "logging"],
        "time_budget": 60,
    },
]


# ─── Manager ─────────────────────────────────────────────────────────────────

_SKILLS_FILE = "skills.json"


class SkillsLibrary:
    """Manage predefined and custom skills."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or _get_skills_dir()
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[List[Skill]] = None

    def _file_path(self) -> Path:
        return self.skills_dir / _SKILLS_FILE

    def _load_all(self) -> List[Skill]:
        if self._cache is not None:
            return self._cache

        # Start with catalog
        catalog = [Skill(**s) for s in SKILLS_CATALOG]
        custom: List[Skill] = []

        path = self._file_path()
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                custom = [Skill(**s) for s in data]
            except Exception:
                pass

        merged = catalog + custom
        self._cache = merged
        return merged

    def _save_custom(self, custom: List[Skill]) -> None:
        # Filter only custom (non-catalog) skills
        catalog_ids = {s["id"] for s in SKILLS_CATALOG}
        custom_only = [s for s in custom if s.id not in catalog_ids]
        data = [s.model_dump(mode="json") for s in custom_only]
        with open(self._file_path(), "w") as f:
            json.dump(data, f, indent=2, default=str)
        self._cache = None  # invalidate cache

    # ── CRUD ──────────────────────────────────────────────────────────────

    def list_skills(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_skills = self._load_all()
        if category:
            all_skills = [s for s in all_skills if s.category == category]
        if tag:
            all_skills = [s for s in all_skills if tag in s.tags]
        return [s.model_dump(mode="json") for s in all_skills]

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        all_skills = self._load_all()
        for s in all_skills:
            if s.id == skill_id:
                return s.model_dump(mode="json")
        return None

    def create_skill(self, skill: Skill) -> Dict[str, Any]:
        all_skills = self._load_all()
        skill.id = str(uuid.uuid4())[:8]
        skill.created_at = datetime.utcnow()
        skill.updated_at = datetime.utcnow()
        all_skills.append(skill)
        self._save_custom(all_skills)
        return skill.model_dump(mode="json")

    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        catalog_ids = {s["id"] for s in SKILLS_CATALOG}
        if skill_id in catalog_ids:
            return None  # Cannot modify catalog skills

        all_skills = self._load_all()
        for i, s in enumerate(all_skills):
            if s.id == skill_id:
                for key, value in updates.items():
                    if hasattr(s, key) and key not in ("id", "created_at"):
                        setattr(s, key, value)
                s.updated_at = datetime.utcnow()
                all_skills[i] = s
                self._save_custom(all_skills)
                return s.model_dump(mode="json")
        return None

    def delete_skill(self, skill_id: str) -> bool:
        catalog_ids = {s["id"] for s in SKILLS_CATALOG}
        if skill_id in catalog_ids:
            return False  # Cannot delete catalog skills

        all_skills = self._load_all()
        for i, s in enumerate(all_skills):
            if s.id == skill_id:
                all_skills.pop(i)
                self._save_custom(all_skills)
                return True
        return False

    def list_categories(self) -> List[Dict[str, Any]]:
        all_skills = self._load_all()
        counts: Dict[str, int] = {}
        for s in all_skills:
            counts[s.category] = counts.get(s.category, 0) + 1
        return [
            {"name": cat, "count": counts.get(cat, 0)}
            for cat in CATEGORIES
        ]

    def list_tags(self) -> List[str]:
        all_skills = self._load_all()
        tags: set = set()
        for s in all_skills:
            tags.update(s.tags)
        return sorted(tags)


# ─── Singleton ────────────────────────────────────────────────────────────────

_skills_lib: Optional[SkillsLibrary] = None


def get_skills_library() -> SkillsLibrary:
    global _skills_lib
    if _skills_lib is None:
        _skills_lib = SkillsLibrary()
    return _skills_lib
