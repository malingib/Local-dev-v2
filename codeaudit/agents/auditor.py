"""
Auditor Agent - finds bugs, anti-patterns, dead code, and logic errors.
"""
import re
from pathlib import Path
from typing import List, Dict, Any
from backend.models import Finding, FindingType, Severity, AgentType
from backend.constants import CODE_EXTENSIONS
from agents.base_agent import BaseAgent


class AuditorAgent(BaseAgent):
    """Agent for code quality and bug detection."""
    
    agent_type = AgentType.AUDITOR
    
    CODE_EXTENSIONS = CODE_EXTENSIONS
    
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan for code quality issues."""
        await self.log("Starting code quality scan...")
        
        findings = []
        files = self._get_files(project_path, self.CODE_EXTENSIONS)
        
        await self.log(f"Found {len(files)} files to analyze")
        
        # Process files in batches to avoid overwhelming
        batch_size = 20
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            for file_path in batch:
                file_findings = await self._analyze_file(file_path, project_path)
                findings.extend(file_findings)
            
            if (i // batch_size) % 5 == 0:
                await self.log(f"Analyzed {min(i + batch_size, len(files))}/{len(files)} files...")
        
        findings = self._deduplicate_findings(findings)
        findings = self._sort_by_severity(findings)
        
        await self.log(f"Code scan complete: {len(findings)} findings")
        return findings
    
    async def _analyze_file(self, file_path: Path, project_path: str) -> List[Finding]:
        """Analyze a single file for issues."""
        findings = []
        content = self._read_file(file_path)
        lines = content.split('\n')
        rel_path = str(file_path.relative_to(project_path))
        ext = file_path.suffix.lower()
        
        # Pattern-based checks (fast)
        findings.extend(self._check_common_issues(content, lines, rel_path, ext))
        
        # LLM-based deep analysis (slower, sample of files)
        if len(content) < 10000 and self._should_deep_analyze(file_path):
            llm_findings = await self._deep_analyze(content, rel_path, ext)
            findings.extend(llm_findings)
        
        return findings
    
    def _should_deep_analyze(self, file_path: Path) -> bool:
        """Determine if file should get LLM analysis."""
        name = file_path.name.lower()
        key_patterns = ['app', 'main', 'index', 'router', 'controller', 'service', 'api',
                        'auth', 'login', 'config', 'db', 'database', 'store', 'util',
                        'middleware', 'handler', 'command', 'event', 'model', 'schema']
        if any(p in name for p in key_patterns):
            return True

        ext = file_path.suffix.lower()
        priority_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.rb'}
        if ext not in priority_extensions:
            return False

        size = file_path.stat().st_size
        if size < 500:
            return True
        if size > 50000:
            return False

        import hashlib
        seed = str(file_path.relative_to(file_path.anchor)).encode() if file_path.anchor else str(file_path).encode()
        hash_val = int(hashlib.md5(seed).hexdigest(), 16)
        return hash_val % 3 == 0  # ~33% of remaining files
    
    def _check_common_issues(
        self,
        content: str,
        lines: List[str],
        file_path: str,
        ext: str
    ) -> List[Finding]:
        """Check for common code issues using regex patterns."""
        findings = []
        
        # Python-specific checks
        if ext == '.py':
            findings.extend(self._check_python_issues(content, lines, file_path))
        
        # JavaScript/TypeScript checks
        if ext in ('.js', '.jsx', '.ts', '.tsx'):
            findings.extend(self._check_js_issues(content, lines, file_path))
        
        # Generic checks for all languages
        findings.extend(self._check_generic_issues(content, lines, file_path))
        
        return findings
    
    def _check_python_issues(
        self,
        content: str,
        lines: List[str],
        file_path: str
    ) -> List[Finding]:
        """Check for Python-specific issues."""
        findings = []
        
        # Bare except clause
        for i, line in enumerate(lines, 1):
            if re.search(r'^\s*except\s*:', line):
                findings.append(self._create_finding(
                    title="Bare except clause",
                    description="Using bare 'except:' catches all exceptions including KeyboardInterrupt and SystemExit. Use 'except Exception:' instead.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.BUG,
                    location={"file": file_path, "line_start": i},
                    code_snippet=line.strip()
                ))
        
        # Mutable default arguments
        if re.search(r'def\s+\w+\s*\([^)]*=\s*(\[|\{)', content):
            findings.append(self._create_finding(
                title="Mutable default argument",
                description="Using mutable default arguments (list or dict) can lead to unexpected behavior as they persist between function calls.",
                severity=Severity.HIGH,
                finding_type=FindingType.BUG,
                location={"file": file_path},
                suggested_fix="Use None as default and initialize mutable inside the function"
            ))
        
        # SQL string formatting
        if re.search(r'(%s|\.format\(|f["\'].*SELECT|f["\'].*INSERT|f["\'].*UPDATE)', content, re.IGNORECASE):
            if 'param' not in content.lower():
                findings.append(self._create_finding(
                    title="Potential SQL injection",
                    description="String formatting in SQL queries can lead to SQL injection vulnerabilities. Use parameterized queries.",
                    severity=Severity.CRITICAL,
                    finding_type=FindingType.SECURITY,
                    location={"file": file_path},
                    suggested_fix="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
                ))
        
        # Print statements (should use logging)
        if re.search(r'\bprint\s*\(', content):
            findings.append(self._create_finding(
                title="Print statement found",
                description="Using print() for debugging/output. Consider using the logging module for better control.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Use import logging; logging.info('message')"
            ))
        
        # Hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token"),
        ]
        
        for pattern, title in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(self._create_finding(
                    title=title,
                    description=f"Potential {title.lower()} detected in source code. Secrets should be loaded from environment variables.",
                    severity=Severity.CRITICAL,
                    finding_type=FindingType.SECURITY,
                    location={"file": file_path},
                    suggested_fix="Use os.environ.get('SECRET_NAME') or python-dotenv"
                ))
        
        return findings
    
    def _check_js_issues(
        self,
        content: str,
        lines: List[str],
        file_path: str
    ) -> List[Finding]:
        """Check for JavaScript/TypeScript issues."""
        findings = []
        
        # console.log statements
        if 'console.log' in content:
            findings.append(self._create_finding(
                title="Console.log statement found",
                description="Console.log statements should be removed in production code.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Remove console.log or use a proper logging library"
            ))
        
        # == instead of ===
        if re.search(r'(?<![=!])==(?!=)', content):
            findings.append(self._create_finding(
                title="Loose equality operator",
                description="Using == instead of === can lead to unexpected type coercion.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.BUG,
                location={"file": file_path},
                suggested_fix="Use === for strict equality comparison"
            ))
        
        # var usage (should use let/const)
        if re.search(r'\bvar\s+', content):
            findings.append(self._create_finding(
                title="Using var instead of let/const",
                description="'var' has function scope and hoisting behavior that can cause bugs. Use 'let' or 'const' instead.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Replace 'var' with 'const' (or 'let' if reassignment needed)"
            ))
        
        # eval usage
        if 'eval(' in content:
            findings.append(self._create_finding(
                title="Dangerous eval() usage",
                description="eval() can execute arbitrary code and is a security risk.",
                severity=Severity.CRITICAL,
                finding_type=FindingType.SECURITY,
                location={"file": file_path},
                suggested_fix="Use JSON.parse for JSON, or safer alternatives"
            ))
        
        # innerHTML with user input potential
        if 'innerHTML' in content:
            findings.append(self._create_finding(
                title="Potential XSS via innerHTML",
                description="innerHTML can execute scripts if user input is inserted. Use textContent or sanitize input.",
                severity=Severity.HIGH,
                finding_type=FindingType.SECURITY,
                location={"file": file_path},
                suggested_fix="Use element.textContent or DOMPurify for sanitization"
            ))
        
        # Missing error handling in async
        if re.search(r'await\s+\w+\([^)]*\)(?!\s*[;\n]\s*catch)', content):
            if 'try' not in content and '.catch' not in content:
                findings.append(self._create_finding(
                    title="Unhandled async/await",
                    description="Async operations without try/catch can cause unhandled promise rejections.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.BUG,
                    location={"file": file_path},
                    suggested_fix="Wrap await calls in try/catch blocks"
                ))
        
        return findings
    
    def _check_generic_issues(
        self,
        content: str,
        lines: List[str],
        file_path: str
    ) -> List[Finding]:
        """Check for language-agnostic issues."""
        findings = []
        
        # TODO/FIXME comments
        todo_count = len(re.findall(r'\b(TODO|FIXME|XXX|HACK)\b', content, re.IGNORECASE))
        if todo_count > 5:
            findings.append(self._create_finding(
                title=f"Many TODO/FIXME comments ({todo_count})",
                description="High number of TODO/FIXME comments indicates incomplete code.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path}
            ))
        
        # Very long lines
        long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120]
        if len(long_lines) > 10:
            findings.append(self._create_finding(
                title=f"Many long lines ({len(long_lines)} > 120 chars)",
                description="Long lines reduce readability. Consider breaking them up.",
                severity=Severity.INFO,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path}
            ))
        
        # Trailing whitespace
        trailing_ws = [i for i, line in enumerate(lines, 1) if line.rstrip() != line.rstrip('\n').rstrip()]
        if len(trailing_ws) > 20:
            findings.append(self._create_finding(
                title=f"Trailing whitespace in {len(trailing_ws)} lines",
                description="Trailing whitespace causes unnecessary diff noise.",
                severity=Severity.INFO,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path}
            ))
        
        return findings
    
    async def _deep_analyze(
        self,
        content: str,
        file_path: str,
        ext: str
    ) -> List[Finding]:
        """Use LLM for deep code analysis."""
        language = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript (React)',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (React)',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
        }.get(ext, 'Unknown')
        
        prompt = f"""Analyze this {language} code for bugs, logic errors, and code quality issues.

FILE: {file_path}

CODE:
```
{content[:5000]}
```

Identify issues and return as JSON array:
[{{
  "title": "Brief issue title",
  "description": "Detailed explanation of the problem",
  "severity": "critical|high|medium|low|info",
  "type": "bug|security|performance|code_quality",
  "line": 42,
  "suggested_fix": "How to fix it"
}}]

Return empty array [] if no significant issues found."""
        
        try:
            result = await self._analyze_with_llm(prompt)
            if not isinstance(result, list):
                return []
            
            findings = []
            for item in result:
                severity_map = {
                    "critical": Severity.CRITICAL,
                    "high": Severity.HIGH,
                    "medium": Severity.MEDIUM,
                    "low": Severity.LOW,
                    "info": Severity.INFO
                }
                type_map = {
                    "bug": FindingType.BUG,
                    "security": FindingType.SECURITY,
                    "performance": FindingType.PERFORMANCE,
                    "code_quality": FindingType.CODE_QUALITY
                }
                
                findings.append(self._create_finding(
                    title=item.get("title", "Unknown issue"),
                    description=item.get("description", ""),
                    severity=severity_map.get(item.get("severity", "medium"), Severity.MEDIUM),
                    finding_type=type_map.get(item.get("type", "code_quality"), FindingType.CODE_QUALITY),
                    location={
                        "file": file_path,
                        "line_start": item.get("line")
                    },
                    suggested_fix=item.get("suggested_fix", "")
                ))
            
            return findings
        except Exception as e:
            await self.log(f"Deep analysis failed for {file_path}: {e}", "warning")
            return []
