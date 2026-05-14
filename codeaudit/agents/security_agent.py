"""
Security Agent - finds security vulnerabilities and best practice violations.
"""
import re
import json
from pathlib import Path
from typing import List
from backend.models import Finding, FindingType, Severity, AgentType
from backend.constants import CODE_EXTENSIONS as SEC_CODE_EXTENSIONS
from agents.base_agent import BaseAgent


class SecurityAgent(BaseAgent):
    """Agent for security vulnerability detection."""
    
    agent_type = AgentType.SECURITY
    CODE_EXTENSIONS = list(SEC_CODE_EXTENSIONS)
    
    # Dangerous patterns by language
    DANGEROUS_PATTERNS = {
        'py': [
            (r'eval\s*\(', "eval() usage", Severity.CRITICAL, "Never use eval() with untrusted input"),
            (r'exec\s*\(', "exec() usage", Severity.CRITICAL, "Never use exec() with untrusted input"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "Shell=True in subprocess", Severity.CRITICAL, "Avoid shell=True; use list of arguments instead"),
            (r'pickle\.(loads|load)\s*\(', "Pickle deserialization", Severity.HIGH, "Pickle can execute arbitrary code on deserialization"),
            (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', "Unsafe YAML load", Severity.HIGH, "Use yaml.safe_load() instead of yaml.load()"),
            (r'input\s*\(\s*\)', "Python 2 input()", Severity.CRITICAL, "input() in Python 2 is equivalent to eval(raw_input())"),
            (r'hashlib\.md5\s*\(', "MD5 hash usage", Severity.MEDIUM, "MD5 is cryptographically broken, use SHA-256 or better"),
            (r'hashlib\.sha1\s*\(', "SHA1 hash usage", Severity.MEDIUM, "SHA1 is cryptographically weak, use SHA-256 or better"),
            (r'random\.(random|randint|choice)', "Insecure random", Severity.MEDIUM, "Use secrets module for cryptographic randomness"),
            (r'debug\s*=\s*True', "Debug mode enabled", Severity.HIGH, "Never run debug mode in production"),
            (r'VERIFY\s*=\s*False|verify\s*=\s*False', "SSL verification disabled", Severity.CRITICAL, "Never disable SSL certificate verification"),
        ],
        'js': [
            (r'eval\s*\(', "eval() usage", Severity.CRITICAL, "eval() can execute arbitrary code"),
            (r'new\s+Function\s*\(', "Function constructor", Severity.CRITICAL, "Function constructor is similar to eval()"),
            (r'setTimeout\s*\(\s*["\']', "setTimeout with string", Severity.CRITICAL, "setTimeout with string executes like eval()"),
            (r'setInterval\s*\(\s*["\']', "setInterval with string", Severity.CRITICAL, "setInterval with string executes like eval()"),
            (r'innerHTML\s*=', "innerHTML assignment", Severity.HIGH, "Can lead to XSS if user input is used"),
            (r'document\.write\s*\(', "document.write", Severity.HIGH, "Can lead to XSS and blocks rendering"),
            (r'\.cookie\s*=', "Cookie manipulation", Severity.MEDIUM, "Ensure secure and httpOnly flags are set"),
            (r'localStorage\.[\w]+\s*=', "localStorage usage", Severity.LOW, "Don't store sensitive data in localStorage"),
            (r'sessionStorage\.[\w]+\s*=', "sessionStorage usage", Severity.LOW, "Don't store sensitive data in sessionStorage"),
            (r'postMessage\s*\([^)]*\)(?!.*origin)', "postMessage without origin check", Severity.HIGH, "Always verify message origin in postMessage handlers"),
            (r'window\.[\w]+\s*=\s*', "Global variable assignment", Severity.LOW, "Avoid polluting global namespace"),
        ],
        'generic': [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", Severity.CRITICAL, "Never hardcode passwords"),
            (r'secret[_\s]*=\s*["\'][^"\']+["\']', "Hardcoded secret", Severity.CRITICAL, "Never hardcode secrets"),
            (r'api[_\s]*key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", Severity.CRITICAL, "Never hardcode API keys"),
            (r'token\s*=\s*["\'][a-zA-Z0-9_-]{20,}["\']', "Hardcoded token", Severity.CRITICAL, "Never hardcode tokens"),
            (r'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY', "Private key in code", Severity.CRITICAL, "Never commit private keys"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID", Severity.CRITICAL, "AWS credentials in code"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token", Severity.CRITICAL, "GitHub token in code"),
            (r'glpat-[a-zA-Z0-9\-]{20}', "GitLab Personal Access Token", Severity.CRITICAL, "GitLab token in code"),
        ]
    }
    
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan for security vulnerabilities."""
        await self.log("Starting security scan...")
        
        findings = []
        files = self._get_files(project_path, self.CODE_EXTENSIONS)
        
        await self.log(f"Found {len(files)} files to analyze")
        
        # Check for dependency vulnerabilities
        dep_findings = await self._check_dependencies(project_path)
        findings.extend(dep_findings)
        
        # Check each file
        for file_path in files:
            file_findings = await self._analyze_security_file(file_path, project_path)
            findings.extend(file_findings)
        
        findings = self._deduplicate_findings(findings)
        findings = self._sort_by_severity(findings)
        
        await self.log(f"Security scan complete: {len(findings)} findings")
        return findings
    
    async def _check_dependencies(self, project_path: str) -> List[Finding]:
        """Check for known vulnerable dependencies."""
        findings = []
        path = Path(project_path)
        
        # Check package.json for known vulnerable packages
        package_json = path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                # Known vulnerable packages (simplified check)
                vulnerable_packages = {
                    "lodash": ("<4.17.21", "Prototype pollution vulnerability"),
                    "jquery": ("<3.5.0", "XSS vulnerability in htmlPrefilter"),
                    "axios": ("<0.21.1", "Server-Side Request Forgery vulnerability"),
                    "minimist": ("<1.2.6", "Prototype pollution vulnerability"),
                    "y18n": ("<4.0.1", "Prototype pollution vulnerability"),
                    "serialize-javascript": ("<3.1.0", "Remote code execution"),
                }
                
                for pkg_name, (vuln_version, description) in vulnerable_packages.items():
                    if pkg_name in deps:
                        findings.append(self._create_finding(
                            title=f"Potentially vulnerable dependency: {pkg_name}",
                            description=f"{pkg_name} version {deps[pkg_name]} may be vulnerable. {description}",
                            severity=Severity.HIGH,
                            finding_type=FindingType.SECURITY,
                            location={"file": "package.json"},
                            suggested_fix=f"Update {pkg_name} to latest version"
                        ))
                
            except Exception:
                pass
        
        # Check requirements.txt
        requirements = path / "requirements.txt"
        if requirements.exists():
            try:
                content = requirements.read_text().lower()
                
                # Known vulnerable Python packages
                vuln_py_packages = {
                    "django<3": ("Django < 3.0 has known security issues", Severity.HIGH),
                    "flask<1": ("Flask < 1.0 has known security issues", Severity.HIGH),
                    "requests<2.2": ("Requests < 2.20 has SSL verification issues", Severity.MEDIUM),
                }
                
                for pkg_pattern, (description, severity) in vuln_py_packages.items():
                    if pkg_pattern in content:
                        findings.append(self._create_finding(
                            title=f"Potentially vulnerable dependency",
                            description=description,
                            severity=severity,
                            finding_type=FindingType.SECURITY,
                            location={"file": "requirements.txt"},
                            suggested_fix="Update to latest stable version"
                        ))
                
            except Exception:
                pass
        
        return findings
    
    async def _analyze_security_file(self, file_path: Path, project_path: str) -> List[Finding]:
        """Analyze a file for security issues."""
        findings = []
        content = self._read_file(file_path)
        rel_path = str(file_path.relative_to(project_path))
        ext = file_path.suffix.lower().lstrip('.')
        
        # Get language-specific patterns
        patterns = []
        if ext in ('py',):
            patterns = self.DANGEROUS_PATTERNS.get('py', [])
        elif ext in ('js', 'jsx', 'ts', 'tsx', 'vue', 'svelte'):
            patterns = self.DANGEROUS_PATTERNS.get('js', [])
        
        # Always check generic patterns
        patterns.extend(self.DANGEROUS_PATTERNS.get('generic', []))
        
        # Apply patterns
        for pattern, title, severity, fix in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                
                # Skip if it's in a comment (basic check)
                line = content[:match.start()].split('\n')[-1] + match.group(0)
                if line.strip().startswith('#') or line.strip().startswith('//'):
                    continue
                
                findings.append(self._create_finding(
                    title=title,
                    description=f"Security issue detected: {title}",
                    severity=severity,
                    finding_type=FindingType.SECURITY,
                    location={"file": rel_path, "line_start": line_num},
                    code_snippet=match.group(0)[:200],
                    suggested_fix=fix
                ))
        
        # Check for CORS misconfiguration
        if 'cors' in content.lower():
            if re.search(r'allow.*origin.*\*', content, re.IGNORECASE):
                findings.append(self._create_finding(
                    title="Overly permissive CORS",
                    description="Allowing all origins (*) can expose your API to CSRF attacks.",
                    severity=Severity.HIGH,
                    finding_type=FindingType.SECURITY,
                    location={"file": rel_path},
                    suggested_fix="Specify exact allowed origins instead of *"
                ))
        
        # Check for insecure HTTP
        if re.search(r'http://(?!localhost|127\.0\.0\.1)', content):
            findings.append(self._create_finding(
                title="Insecure HTTP URL",
                description="Using HTTP instead of HTTPS is insecure.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.SECURITY,
                location={"file": rel_path},
                suggested_fix="Use HTTPS URLs"
            ))
        
        return findings
