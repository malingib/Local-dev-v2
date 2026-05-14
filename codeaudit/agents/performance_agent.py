"""
Performance Agent - finds performance issues and optimization opportunities.
"""
import re
import json
from pathlib import Path
from typing import List
from backend.models import Finding, FindingType, Severity, AgentType
from backend.constants import PERFORMANCE_EXTENSIONS
from agents.base_agent import BaseAgent


class PerformanceAgent(BaseAgent):
    """Agent for performance issue detection."""
    
    agent_type = AgentType.PERFORMANCE
    CODE_EXTENSIONS = PERFORMANCE_EXTENSIONS
    
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan for performance issues."""
        await self.log("Starting performance scan...")
        
        findings = []
        files = self._get_files(project_path, list(self.CODE_EXTENSIONS))
        
        await self.log(f"Found {len(files)} files to analyze")
        
        # Check bundle size
        bundle_findings = await self._check_bundle_size(project_path)
        findings.extend(bundle_findings)
        
        # Check each file
        for file_path in files:
            file_findings = await self._analyze_performance_file(file_path, project_path)
            findings.extend(file_findings)
        
        findings = self._deduplicate_findings(findings)
        findings = self._sort_by_severity(findings)
        
        await self.log(f"Performance scan complete: {len(findings)} findings")
        return findings
    
    async def _check_bundle_size(self, project_path: str) -> List[Finding]:
        """Check for bundle size issues."""
        findings = []
        path = Path(project_path)
        
        # Check for large dependencies
        package_json = path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                
                deps = pkg.get("dependencies", {})
                
                # Known large packages
                large_packages = {
                    "lodash": "Consider using lodash-es for tree-shaking or specific function imports",
                    "moment": "Consider using date-fns or day.js (smaller alternatives)",
                    "jquery": "Consider vanilla JS or smaller alternatives",
                    "bootstrap": "Consider PurgeCSS or using only needed components",
                    "fontawesome": "Consider subsetting icons or using SVG sprites",
                }
                
                for pkg_name, suggestion in large_packages.items():
                    if pkg_name in deps:
                        findings.append(self._create_finding(
                            title=f"Large dependency: {pkg_name}",
                            description=f"{pkg_name} can significantly increase bundle size. {suggestion}",
                            severity=Severity.LOW,
                            finding_type=FindingType.PERFORMANCE,
                            location={"file": "package.json"},
                            suggested_fix=suggestion
                        ))
                
            except Exception:
                pass
        
        return findings
    
    async def _analyze_performance_file(self, file_path: Path, project_path: str) -> List[Finding]:
        """Analyze a file for performance issues."""
        findings = []
        content = self._read_file(file_path)
        rel_path = str(file_path.relative_to(project_path))
        ext = file_path.suffix.lower()
        
        # JavaScript/TypeScript performance checks
        if ext in ('.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'):
            findings.extend(self._check_js_performance(content, rel_path))
        
        # Python performance checks
        if ext == '.py':
            findings.extend(self._check_python_performance(content, rel_path))
        
        # SQL performance checks
        if ext == '.sql':
            findings.extend(self._check_sql_performance(content, rel_path))
        
        return findings
    
    def _check_js_performance(self, content: str, file_path: str) -> List[Finding]:
        """Check JavaScript for performance issues."""
        findings = []
        
        # Large arrays/objects in component
        if 'const' in content and re.search(r'const\s+\w+\s*=\s*\[[^\]]{500,}\]', content):
            findings.append(self._create_finding(
                title="Large inline array",
                description="Large arrays defined inline can cause unnecessary re-renders and memory usage.",
                severity=Severity.LOW,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Move large data outside component or use useMemo"
            ))
        
        # Missing useMemo for expensive calculations
        if 'useEffect' in content and 'useMemo' not in content:
            if re.search(r'\.(map|filter|reduce|sort)\s*\(', content):
                findings.append(self._create_finding(
                    title="Potential missing useMemo",
                    description="Array operations in render can be expensive. Consider useMemo for expensive calculations.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Wrap expensive operations in useMemo"
                ))
        
        # Missing key prop in loops
        if re.search(r'\.map\s*\([^)]*=>\s*<\w+', content):
            if 'key=' not in content:
                findings.append(self._create_finding(
                    title="Missing key prop in list rendering",
                    description="React lists need unique key props for efficient reconciliation.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Add key prop with unique identifier"
                ))
        
        # Inline function definitions in render
        inline_func_pattern = r'on\w+\s*=\s*\{?\s*\([^)]*\)\s*=>'
        if len(re.findall(inline_func_pattern, content)) > 5:
            findings.append(self._create_finding(
                title="Many inline function definitions",
                description="Inline functions in JSX create new function instances on every render.",
                severity=Severity.LOW,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Use useCallback for event handlers or define functions outside component"
            ))
        
        # setState in loops
        if re.search(r'for\s*\([^)]*\)\s*\{[^}]*setState', content):
            findings.append(self._create_finding(
                title="setState inside loop",
                description="Calling setState in a loop causes multiple re-renders.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Batch updates or compute final state before calling setState"
            ))
        
        # Large images without optimization
        if '<img' in content:
            if 'next/image' not in content and 'gatsby-image' not in content:
                findings.append(self._create_finding(
                    title="Unoptimized images",
                    description="Consider using Next.js Image or similar for automatic image optimization.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Use next/image or implement responsive images"
                ))
        
        # No code splitting indicators
        if 'import(' not in content and 'React.lazy' not in content:
            if 'Router' in content or 'Routes' in content:
                findings.append(self._create_finding(
                    title="No code splitting detected",
                    description="Large applications benefit from code splitting to reduce initial load time.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Use React.lazy() and dynamic imports for route-based code splitting"
                ))
        
        # Synchronous XMLHttpRequest
        if 'XMLHttpRequest' in content and 'open(' in content:
            if 'false' in content:  # Likely synchronous
                findings.append(self._create_finding(
                    title="Potentially synchronous XHR",
                    description="Synchronous XMLHttpRequest blocks the main thread.",
                    severity=Severity.HIGH,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Use async XHR or fetch API"
                ))
        
        return findings
    
    def _check_python_performance(self, content: str, file_path: str) -> List[Finding]:
        """Check Python for performance issues."""
        findings = []
        
        # N+1 query pattern (basic detection)
        if 'for' in content and ('query' in content.lower() or 'filter(' in content or 'objects.' in content):
            if re.search(r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s+\w+\.(filter|get|objects)', content):
                findings.append(self._create_finding(
                    title="Potential N+1 query",
                    description="Query inside a loop can cause N+1 query problem.",
                    severity=Severity.HIGH,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Use select_related(), prefetch_related(), or batch queries"
                ))
        
        # List comprehension vs filter
        if re.search(r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s+if\s+.*:\s*\n\s+result\.', content):
            findings.append(self._create_finding(
                title="Loop with condition can be optimized",
                description="Consider using list comprehension or filter() for better performance.",
                severity=Severity.LOW,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Use [x for x in items if condition] instead of loop + append"
            ))
        
        # String concatenation in loop
        if re.search(r'for\s+[^:]*:\s*[^=]*=\s*[^+]*\+', content):
            findings.append(self._create_finding(
                title="String concatenation in loop",
                description="String concatenation in loops is O(n²). Use list + join() or io.StringIO.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Use ''.join(list_of_strings) instead of += in loop"
            ))
        
        # Inefficient list search
        if re.search(r'if\s+\w+\s+in\s+\w+:', content):
            if 'set(' not in content and 'dict(' not in content:
                findings.append(self._create_finding(
                    title="List membership test",
                    description="'in' operator on lists is O(n). Use set() for frequent lookups.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Convert to set: if item in set(items):"
                ))
        
        # Global variables in loops
        if re.search(r'for\s+[^:]*:\s*\n\s+global\s+', content):
            findings.append(self._create_finding(
                title="Global variable in loop",
                description="Global variables are slower to access than local variables.",
                severity=Severity.LOW,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Assign to local variable before loop"
            ))
        
        return findings
    
    def _check_sql_performance(self, content: str, file_path: str) -> List[Finding]:
        """Check SQL for performance issues."""
        findings = []
        
        # Missing index hints
        if 'SELECT' in content.upper():
            if 'WHERE' in content.upper():
                # Check for common patterns that need indexes
                if re.search(r'WHERE\s+\w+\s*=\s*', content, re.IGNORECASE):
                    findings.append(self._create_finding(
                        title="Query may benefit from index",
                        description="WHERE clause on columns should have database indexes.",
                        severity=Severity.LOW,
                        finding_type=FindingType.PERFORMANCE,
                        location={"file": file_path},
                        suggested_fix="Ensure columns in WHERE clause have indexes"
                    ))
        
        # SELECT *
        if re.search(r'SELECT\s+\*\s+FROM', content, re.IGNORECASE):
            findings.append(self._create_finding(
                title="SELECT * used",
                description="SELECT * retrieves unnecessary columns. Specify only needed columns.",
                severity=Severity.LOW,
                finding_type=FindingType.PERFORMANCE,
                location={"file": file_path},
                suggested_fix="Specify exact columns needed instead of *"
            ))
        
        # Missing LIMIT
        if 'SELECT' in content.upper() and 'LIMIT' not in content.upper():
            if 'WHERE' not in content.upper():
                findings.append(self._create_finding(
                    title="Query without LIMIT",
                    description="Unbounded queries can return excessive data.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    suggested_fix="Add LIMIT clause for pagination"
                ))
        
        return findings
