"""
Mobile Agent - checks mobile responsiveness and touch-friendly design.
"""
import re
from pathlib import Path
from typing import List
from backend.models import Finding, FindingType, Severity, AgentType
from backend.constants import UI_EXTENSIONS as MOBILE_EXTENSIONS
from agents.base_agent import BaseAgent


class MobileAgent(BaseAgent):
    """Agent for mobile responsiveness and touch optimization."""
    
    agent_type = AgentType.MOBILE
    UI_EXTENSIONS = MOBILE_EXTENSIONS
    
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan for mobile responsiveness issues."""
        await self.log("Starting mobile responsiveness scan...")
        
        findings = []
        files = self._get_files(project_path, list(self.UI_EXTENSIONS))
        
        await self.log(f"Found {len(files)} UI files to analyze")
        
        for file_path in files:
            file_findings = await self._analyze_mobile_file(file_path, project_path)
            findings.extend(file_findings)
        
        findings = self._deduplicate_findings(findings)
        findings = self._sort_by_severity(findings)
        
        await self.log(f"Mobile scan complete: {len(findings)} findings")
        return findings
    
    async def _analyze_mobile_file(self, file_path: Path, project_path: str) -> List[Finding]:
        """Analyze a file for mobile issues."""
        findings = []
        content = self._read_file(file_path)
        rel_path = str(file_path.relative_to(project_path))
        ext = file_path.suffix.lower()
        
        if ext in ('.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte'):
            findings.extend(self._check_mobile_html(content, rel_path))
        
        if ext in ('.css', '.scss'):
            findings.extend(self._check_mobile_css(content, rel_path))
        
        return findings
    
    def _check_mobile_html(self, content: str, file_path: str) -> List[Finding]:
        """Check HTML for mobile issues."""
        findings = []
        
        # Missing viewport meta
        if '<!DOCTYPE html>' in content or '<html' in content:
            if 'viewport' not in content.lower():
                findings.append(self._create_finding(
                    title="Missing viewport meta tag",
                    description="Without viewport meta, mobile devices will render at desktop width.",
                    severity=Severity.CRITICAL,
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                    suggested_fix='<meta name="viewport" content="width=device-width, initial-scale=1">',
                    auto_approvable=True
                ))
        
        # Fixed input types that should be mobile-friendly
        input_types = re.findall(r'type=["\']([^"\']+)["\']', content, re.IGNORECASE)
        for input_type in input_types:
            if input_type == 'text':
                # Check if it's likely an email/tel/number field by context
                context_pattern = r'<input[^>]*type=["\']text["\'][^>]*>'
                for match in re.finditer(context_pattern, content, re.IGNORECASE):
                    tag = match.group(0).lower()
                    if 'email' in tag or 'mail' in tag:
                        findings.append(self._create_finding(
                            title="Email input without type='email'",
                            description="Using type='email' shows appropriate mobile keyboard.",
                            severity=Severity.LOW,
                            finding_type=FindingType.UI,
                            location={"file": file_path},
                            code_snippet=match.group(0)[:100],
                            suggested_fix='Change type="text" to type="email"',
                            auto_approvable=True
                        ))
                    elif 'tel' in tag or 'phone' in tag:
                        findings.append(self._create_finding(
                            title="Phone input without type='tel'",
                            description="Using type='tel' shows numeric keypad on mobile.",
                            severity=Severity.LOW,
                            finding_type=FindingType.UI,
                            location={"file": file_path},
                            code_snippet=match.group(0)[:100],
                            suggested_fix='Change type="text" to type="tel"',
                            auto_approvable=True
                        ))
                    elif 'number' in tag or 'quantity' in tag or 'amount' in tag:
                        findings.append(self._create_finding(
                            title="Numeric input without type='number'",
                            description="Using type='number' shows numeric keypad on mobile.",
                            severity=Severity.LOW,
                            finding_type=FindingType.UI,
                            location={"file": file_path},
                            code_snippet=match.group(0)[:100],
                            suggested_fix='Change type="text" to type="number"',
                            auto_approvable=True
                        ))
        
        # Touch targets that are too small
        # Check for small width/height in inline styles
        small_touch_pattern = r'(width|height):\s*(\d+)px'
        for match in re.finditer(small_touch_pattern, content, re.IGNORECASE):
            prop = match.group(1).lower()
            size = int(match.group(2))
            if size < 44:  # WCAG recommends 44x44px minimum
                findings.append(self._create_finding(
                    title=f"Small touch target ({size}px)",
                    description=f"Touch targets should be at least 44x44px for accessibility.",
                    severity=Severity.LOW,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    code_snippet=match.group(0),
                    suggested_fix="Increase size to at least 44px or add padding"
                ))
        
        # Tables without responsive wrapper
        if '<table' in content.lower():
            if 'overflow' not in content.lower() and 'responsive' not in content.lower():
                findings.append(self._create_finding(
                    title="Table without responsive wrapper",
                    description="Tables can overflow on small screens without horizontal scroll wrapper.",
                    severity=Severity.LOW,
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                    suggested_fix="Wrap tables in a div with overflow-x: auto"
                ))
        
        # Fixed position elements that might cover content
        if 'position: fixed' in content.lower() or 'fixed;' in content.lower():
            findings.append(self._create_finding(
                title="Fixed position element",
                description="Fixed position elements can cause issues on mobile (zoom problems, content covering).",
                severity=Severity.LOW,
                finding_type=FindingType.UI,
                location={"file": file_path},
                suggested_fix="Consider sticky positioning or ensure proper viewport handling"
            ))
        
        # Images without srcset or sizes
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, content, re.IGNORECASE):
            img_tag = match.group(0)
            if 'srcset' not in img_tag.lower() and 'sizes' not in img_tag.lower():
                if 'next/image' not in content.lower():  # Next.js handles this automatically
                    findings.append(self._create_finding(
                        title="Image without responsive srcset",
                        description="Images should provide different sizes for different screen widths.",
                        severity=Severity.LOW,
                        finding_type=FindingType.PERFORMANCE,
                        location={"file": file_path},
                        code_snippet=img_tag[:100],
                        suggested_fix="Add srcset and sizes attributes for responsive images"
                    ))
        
        return findings
    
    def _check_mobile_css(self, content: str, file_path: str) -> List[Finding]:
        """Check CSS for mobile issues."""
        findings = []
        
        # Fixed widths that might not be responsive
        fixed_width_pattern = r'width:\s*(\d+)px'
        fixed_widths = re.findall(fixed_width_pattern, content, re.IGNORECASE)
        large_fixed = [w for w in fixed_widths if int(w) > 400]
        
        if len(large_fixed) > 5:
            findings.append(self._create_finding(
                title=f"Many fixed pixel widths ({len(large_fixed)} > 400px)",
                description="Fixed pixel widths can cause horizontal scroll on mobile devices.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.UI,
                location={"file": file_path},
                suggested_fix="Use max-width, %, or responsive units instead of fixed widths"
            ))
        
        # Media queries check
        if '@media' not in content:
            # Check if it's a main/app stylesheet (not a reset/normalize)
            if 'reset' not in file_path.lower() and 'normalize' not in file_path.lower():
                findings.append(self._create_finding(
                    title="No media queries found",
                    description="Stylesheet lacks responsive breakpoints for different screen sizes.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                    suggested_fix="Add @media queries for mobile, tablet, and desktop breakpoints"
                ))
        
        # Hover-only interactions (no touch alternative)
        if ':hover' in content:
            if ':active' not in content and ':focus' not in content:
                findings.append(self._create_finding(
                    title="Hover-only styles without touch alternative",
                    description=":hover doesn't work well on touch devices. Add :active or :focus states.",
                    severity=Severity.LOW,
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                    suggested_fix="Add :active or :focus styles alongside :hover"
                ))
        
        # Font sizes in px (don't scale with user preferences)
        font_size_px = re.findall(r'font-size:\s*(\d+)px', content, re.IGNORECASE)
        if font_size_px:
            findings.append(self._create_finding(
                title=f"Font sizes in pixels ({len(font_size_px)} instances)",
                description="Pixel font sizes don't respect user font size preferences on mobile.",
                severity=Severity.LOW,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix="Use rem units for font sizes: 16px = 1rem"
            ))
        
        # Small touch targets in CSS
        touch_size_pattern = r'(min-)?(width|height):\s*(\d+)px'
        for match in re.finditer(touch_size_pattern, content, re.IGNORECASE):
            size = int(match.group(3))
            if size < 44 and not match.group(1):  # Not min-width/height
                findings.append(self._create_finding(
                    title=f"Small touch target in CSS ({size}px)",
                    description="Interactive elements should be at least 44x44px for touch accessibility.",
                    severity=Severity.LOW,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    code_snippet=match.group(0),
                    suggested_fix="Use min-width: 44px and min-height: 44px for interactive elements"
                ))
        
        # Disable zoom (very bad for accessibility)
        if 'user-scalable=no' in content.lower():
            findings.append(self._create_finding(
                title="Zoom disabled",
                description="Preventing zoom is an accessibility violation and frustrates users.",
                severity=Severity.HIGH,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix="Remove user-scalable=no from viewport meta"
            ))
        
        # Maximum-scale less than 5
        if re.search(r'maximum-scale\s*=\s*[0-4]', content, re.IGNORECASE):
            findings.append(self._create_finding(
                title="Maximum scale too restrictive",
                description="Limiting maximum zoom level hinders accessibility for low-vision users.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix="Set maximum-scale=5 or higher, or remove the restriction"
            ))
        
        return findings
