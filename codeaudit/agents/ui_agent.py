"""
UI Agent - checks accessibility, design quality, and WCAG compliance.
Also includes impeccable-style anti-pattern detection rules.
"""
import re
from pathlib import Path
from typing import List
from backend.models import Finding, FindingType, Severity, AgentType
from backend.constants import UI_EXTENSIONS
from agents.base_agent import BaseAgent


AI_SLOP_PATTERNS = {
    "side_tab_borders": {
        "pattern": r'border-bottom:\s*2px\s+solid\s+#?(?:3b82f6|6366f1|8b5cf6|06b6d4|0ea5e9)',
        "title": "Side tab bottom border (AI-slop pattern)",
        "desc": "Purple/blue bottom border on tabs is a common AI generation artifact. Use a proper active indicator instead.",
        "sev": Severity.LOW,
    },
    "purple_gradient_button": {
        "pattern": r'background:\s*linear-gradient\([^)]*?(?:8b5cf6|7c3aed|6366f1)[^)]*\)',
        "title": "Purple gradient button (AI-slop pattern)",
        "desc": "Purple/indigo gradient buttons are a default AI aesthetic. Use brand colors instead.",
        "sev": Severity.LOW,
    },
    "bounce_easing": {
        "pattern": r'(?:cubic-bezier|animation|transition)[^}]*?(?:0\.\d+,\s*1\.\d+|bounce|elastic)',
        "title": "Bounce/elastic easing (dated motion pattern)",
        "desc": "Bounce easing feels dated. Use spring or standard easing curves for modern motion design.",
        "sev": Severity.INFO,
    },
    "dark_glow_shadow": {
        "pattern": r'box-shadow:\s*0\s+0\s+\d+px\s+(?:rgba\(0,0,0,\d\.\d+|#000)',
        "title": "Dark glow box-shadow (AI-slop pattern)",
        "desc": "Pure black drop shadows are unnatural. Use colored shadows matching the element.",
        "sev": Severity.LOW,
    },
    "overly_rounded": {
        "pattern": r'border-radius:\s*(?:9999px|999px|100%)',
        "title": "Overly rounded corners on non-button elements",
        "desc": "border-radius: 9999px makes elements into pills. Reserve for buttons and badges.",
        "sev": Severity.LOW,
    },
    "skeuomorphic_card": {
        "pattern": r'background:\s*#[fF]{6}\s*;?\s*\n?\s*(?:border|box-shadow)[^;]*;\s*\n?\s*border-radius:\s*\d+px',
        "title": "Skeuomorphic white card pattern (dated)",
        "desc": "White card on light gray background with shadow is overused. Consider bordered or ghost cards.",
        "sev": Severity.INFO,
    },
    "generic_font_stack": {
        "pattern": r'font-family:\s*["\'](?:Inter|Poppins|Roboto|Open Sans|Lato|Montserrat)["\']',
        "title": "Generic AI-slop font (Inter/Poppins/Roboto)",
        "desc": "These fonts are AI defaults. Choose a font that fits your brand identity.",
        "sev": Severity.INFO,
    },
    "missing_focus_style": {
        "pattern": r'(?:button|a|input|select|textarea)(?:\s*\{[^}]*)(?!.*outline)(?!.*focus)',
        "title": "Interactive element without focus style",
        "desc": "Interactive elements need visible focus indicators for keyboard accessibility.",
        "sev": Severity.MEDIUM,
    },
    "excessive_border_radius_on_nav": {
        "pattern": r'(?:nav|header|aside)\s*\{[^}]*border-radius:\s*(?:8|10|12|16)px',
        "title": "Excessive border radius on navigation elements",
        "desc": "Navigation containers should use minimal border-radius (0-4px) for a professional look.",
        "sev": Severity.LOW,
    },
    "pure_black_text": {
        "pattern": r'color:\s*#000(?:000)?(?:\s|;|!|})',
        "title": "Pure black text (#000)",
        "desc": "Pure black text on white causes eye strain. Use a dark gray like #1a1a1a or #333.",
        "sev": Severity.LOW,
    },
    "pure_white_bg": {
        "pattern": r'background(?:-color)?:\s*#(?:FFF|fff)(?:\s|;|!|})',
        "title": "Pure white background (#FFF)",
        "desc": "Pure white backgrounds cause eye strain. Use an off-white like #fafafa or #f8f9fa.",
        "sev": Severity.INFO,
    },
    "card_inside_card": {
        "pattern": r'(?:card|\.card|<div[^>]*class[^>]*card)[\s\S]{0,500}(?:card|\.card|<div[^>]*class[^>]*card)',
        "title": "Card inside a card (AI-slop nesting)",
        "desc": "Nesting cards inside cards is a common AI generation artifact. Use alternative layouts.",
        "sev": Severity.LOW,
    },
}

DESIGN_QUALITY_ANTI_PATTERNS = {
    "tiny_touch_target": {
        "pattern": r'(?:button|a|input|select)[^}]*?(?:height|min-height|padding)[^}]*?(?:24|28|30)px',
        "title": "Small touch target (below 44px)",
        "desc": "Touch targets should be at least 44x44px for mobile accessibility (WCAG 2.5.5).",
        "sev": Severity.MEDIUM,
    },
    "line_length_too_long": {
        "pattern": r'max-width:\s*(?:60|65|70|75|80)rem',
        "title": "Line length may be too long for readability",
        "desc": "Optimal line length is 60-75 characters (about 35-40rem). Longer lines reduce readability.",
        "sev": Severity.INFO,
    },
    "skipped_heading_level": {
        "pattern": r'<h[23][^>]*>[\s\S]*?<h[45][^>]*>',
        "title": "Skipped heading level (a11y violation)",
        "desc": "Don't skip heading levels (e.g., h2 → h4). This breaks screen reader navigation.",
        "sev": Severity.MEDIUM,
    },
    "missing_h1": {
        "pattern": r'<html[\s\S]*?(?:<body|</head>)',
        "title": "Page may be missing an h1 heading",
        "desc": "Every page should have exactly one h1 element for accessibility and SEO.",
        "sev": Severity.MEDIUM,
    },
    "empty_button": {
        "pattern": r'<button[^>]*>\s*</button>|<button[^>]*>\s*\n\s*</button>',
        "title": "Empty button element",
        "desc": "Buttons must have accessible content (text or aria-label).",
        "sev": Severity.HIGH,
    },
    "div_as_button_no_role": {
        "pattern": r'<div[^>]*onClick[^>]*>(?![\s\S]*?role="button")',
        "title": "Div used as button without role attribute",
        "desc": "Clickable divs need role='button' for accessibility.",
        "sev": Severity.HIGH,
    },
    "missing_aria_live": {
        "pattern": r'(?:className|class)=["\'][^"\']*(?:toast|notification|alert|error-message)[^"\']*["\'][\s\S]{0,200}(?!aria-live)',
        "title": "Dynamic notification without aria-live region",
        "desc": "Dynamic alerts/notifications should use aria-live='polite' for screen readers.",
        "sev": Severity.MEDIUM,
    },
}

TASTE_SLOP_PATTERNS = {
    "generic_landing_layout": {
        "pattern": r'(?:hero|header)\s*\{[^}]*background:\s*linear-gradient\([^)]*to\s+(?:bottom|right)[^)]*\)\s*;?\s*[^}]*padding:\s*(?:80|100|120)px',
        "title": "Generic AI-slop landing page layout",
        "desc": "Full-width gradient hero with massive padding is the default AI layout. Use varied section structures instead.",
        "sev": Severity.LOW,
    },
    "three_card_row": {
        "pattern": r'grid-template-columns:\s*repeat\(3,\s*1fr\)[^}]*\.(?:card|feature|item)[^}]*text-align:\s*center',
        "title": "Three-card centered row (AI-slop pattern)",
        "desc": "Three identical centered cards is a default AI layout. Vary card sizes and alignment for visual interest.",
        "sev": Severity.INFO,
    },
    "centered_everything": {
        "pattern": r'display:\s*flex[^}]*justify-content:\s*center[^}]*align-items:\s*center[^}]*flex-direction:\s*column',
        "title": "Centered column layout overuse",
        "desc": "Vertically centering everything on every page flattens visual hierarchy. Use intentional asymmetry.",
        "sev": Severity.LOW,
    },
    "no_hover_states": {
        "pattern": r'a\s*\{[^}]*color:\s*#[0-9a-fA-F]{3,6}[^}]*\}(?:\s*a\s*:\s*hover\s*\{[^}]*\})?',
        "desc": "Interactive elements should have distinct hover states for better UX feedback.",
        "title": "Missing hover states on links",
        "sev": Severity.LOW,
    },
    "excessive_box_shadow": {
        "pattern": r'box-shadow:\s*(?:\d+px\s+){3}[^;]*;\s*\n?[^}]*box-shadow:\s*(?:\d+px\s+){3}',
        "title": "Multiple heavy box-shadows (performance + slop)",
        "desc": "Multiple heavy box-shadows degrade performance and look generic. Use one subtle shadow per layer.",
        "sev": Severity.LOW,
    },
    "no_transitions": {
        "pattern": r'(?:\.\w+\s*\{[^}]*)(?:(?!transition)[^}])*\}',
        "desc": "Interactive UI elements should have micro-interactions via CSS transitions for polish.",
        "title": "Missing CSS transitions on interactive elements",
        "sev": Severity.INFO,
    },
    "all_caps_nav": {
        "pattern": r'nav\s*\{[^}]*text-transform:\s*uppercase',
        "title": "ALL CAPS navigation (reduced readability)",
        "desc": "ALL CAPS text has reduced readability for body/navigation. Reserve for short labels only.",
        "sev": Severity.INFO,
    },
    "no_max_width": {
        "pattern": r'(?:\.container|\.wrapper|main)\s*\{[^}]*(?:width:\s*(?:100%|\d+px))(?![^}]*max-width)',
        "title": "Container without max-width constraint",
        "desc": "Content containers without max-width become unreadably wide on large screens (>75 chars per line).",
        "sev": Severity.LOW,
    },
    "skip_link_missing": {
        "pattern": r'<(?:body|div[^>]*id="app")',
        "desc": "Pages should include a skip-to-content link as the first focusable element for keyboard users.",
        "title": "Missing skip-to-content link (a11y)",
        "sev": Severity.MEDIUM,
    },
    "no_font_loading_strategy": {
        "pattern": r'@import\s+url\([^)]*(?:fonts\.googleapis|fonts\.gstatic)',
        "desc": "Use font-display: swap to prevent invisible text during font loading (FOUT).",
        "title": "Web fonts loaded without display strategy",
        "sev": Severity.LOW,
    },
}


class UIAgent(BaseAgent):
    """Agent for UI/UX and accessibility auditing."""
    
    agent_type = AgentType.UI
    UI_EXTENSIONS = UI_EXTENSIONS
    
    async def scan(self, project_path: str) -> List[Finding]:
        """Scan for UI/UX and accessibility issues."""
        await self.log("Starting UI/UX scan...")
        
        findings = []
        files = self._get_files(project_path, list(self.UI_EXTENSIONS))
        
        await self.log(f"Found {len(files)} UI files to analyze")
        
        for file_path in files:
            file_findings = await self._analyze_ui_file(file_path, project_path)
            findings.extend(file_findings)
        
        findings = self._deduplicate_findings(findings)
        findings = self._sort_by_severity(findings)
        
        await self.log(f"UI scan complete: {len(findings)} findings")
        return findings
    
    async def _analyze_ui_file(self, file_path: Path, project_path: str) -> List[Finding]:
        """Analyze a UI file for accessibility and design issues."""
        findings = []
        content = self._read_file(file_path)
        rel_path = str(file_path.relative_to(project_path))
        ext = file_path.suffix.lower()
        
        # HTML-based checks
        if ext in ('.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte'):
            findings.extend(self._check_html_accessibility(content, rel_path))
            findings.extend(self._check_design_quality(content, rel_path))
            findings.extend(self._check_anti_patterns(content, rel_path))
        
        # CSS checks
        if ext in ('.css', '.scss'):
            findings.extend(self._check_css_issues(content, rel_path))
        
        return findings
    
    def _check_anti_patterns(self, content: str, file_path: str) -> List[Finding]:
        """Check for impeccable + taste-skill style AI slop and design anti-patterns."""
        findings = []

        for name, rule in AI_SLOP_PATTERNS.items():
            if re.search(rule["pattern"], content, re.IGNORECASE | re.DOTALL):
                findings.append(self._create_finding(
                    title=rule["title"],
                    description=rule["desc"],
                    severity=rule["sev"],
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                ))

        for name, rule in DESIGN_QUALITY_ANTI_PATTERNS.items():
            if re.search(rule["pattern"], content, re.IGNORECASE | re.DOTALL):
                findings.append(self._create_finding(
                    title=rule["title"],
                    description=rule["desc"],
                    severity=rule["sev"],
                    finding_type=FindingType.ACCESSIBILITY if name in ("skipped_heading_level", "missing_h1", "missing_aria_live", "div_as_button_no_role") else FindingType.UI,
                    location={"file": file_path},
                ))

        for name, rule in TASTE_SLOP_PATTERNS.items():
            if re.search(rule["pattern"], content, re.IGNORECASE | re.DOTALL):
                findings.append(self._create_finding(
                    title=rule["title"],
                    description=rule["desc"],
                    severity=rule["sev"],
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                ))

        return findings

    def _check_html_accessibility(self, content: str, file_path: str) -> List[Finding]:
        """Check for HTML accessibility issues."""
        findings = []
        
        # Images without alt text
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, content, re.IGNORECASE):
            img_tag = match.group(0)
            if 'alt=' not in img_tag.lower():
                findings.append(self._create_finding(
                    title="Missing alt text on image",
                    description="Images without alt text are inaccessible to screen readers.",
                    severity=Severity.HIGH,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    code_snippet=img_tag[:100],
                    suggested_fix='Add alt="descriptive text" or alt="" for decorative images',
                    auto_approvable=True
                ))
        
        # Missing viewport meta tag (check in HTML files)
        if '<!DOCTYPE html>' in content or '<html' in content:
            if '<meta' not in content or 'viewport' not in content:
                findings.append(self._create_finding(
                    title="Missing viewport meta tag",
                    description="Without viewport meta tag, mobile rendering will be broken.",
                    severity=Severity.HIGH,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    suggested_fix='<meta name="viewport" content="width=device-width, initial-scale=1">',
                    auto_approvable=True
                ))
        
        # Missing lang attribute on html
        if '<html' in content and 'lang=' not in content:
            findings.append(self._create_finding(
                title="Missing lang attribute",
                description="HTML element should have a lang attribute for screen readers.",
                severity=Severity.MEDIUM,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix='<html lang="en">',
                auto_approvable=True
            ))
        
        # Form inputs without labels
        input_pattern = r'<input[^>]*>'
        for match in re.finditer(input_pattern, content, re.IGNORECASE):
            input_tag = match.group(0)
            if 'aria-label' not in input_tag.lower() and 'aria-labelledby' not in input_tag.lower():
                # Check if wrapped in label (simplified check)
                if '<label' not in content[max(0, match.start() - 200):match.start()]:
                    findings.append(self._create_finding(
                        title="Form input without label",
                        description="Form inputs should have associated labels for accessibility.",
                        severity=Severity.MEDIUM,
                        finding_type=FindingType.ACCESSIBILITY,
                        location={"file": file_path},
                        code_snippet=input_tag[:100],
                        suggested_fix='Add aria-label or wrap in <label> element'
                    ))
        
        # Low contrast indicators (inline styles)
        if 'color:' in content.lower():
            # Check for potentially low contrast combinations
            low_contrast_patterns = [
                (r'color:\s*#fff', r'background(?:-color)?:\s*#eee', "white on light gray"),
                (r'color:\s*#000', r'background(?:-color)?:\s*#333', "black on dark gray"),
            ]
            for color_pat, bg_pat, desc in low_contrast_patterns:
                if re.search(color_pat, content, re.IGNORECASE) and re.search(bg_pat, content, re.IGNORECASE):
                    findings.append(self._create_finding(
                        title=f"Potential low contrast: {desc}",
                        description="Low color contrast makes text hard to read for visually impaired users.",
                        severity=Severity.MEDIUM,
                        finding_type=FindingType.ACCESSIBILITY,
                        location={"file": file_path},
                        suggested_fix="Use contrast ratio of at least 4.5:1 for normal text"
                    ))
        
        # Missing button type
        button_pattern = r'<button[^>]*>'
        for match in re.finditer(button_pattern, content, re.IGNORECASE):
            button_tag = match.group(0)
            if 'type=' not in button_tag.lower():
                findings.append(self._create_finding(
                    title="Button without type attribute",
                    description="Buttons without type default to 'submit' which can cause unexpected form submissions.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.BUG,
                    location={"file": file_path},
                    code_snippet=button_tag[:100],
                    suggested_fix='Add type="button" for non-submit buttons'
                ))
        
        # Links without href or with #
        link_pattern = r'<a[^>]*>'
        for match in re.finditer(link_pattern, content, re.IGNORECASE):
            link_tag = match.group(0)
            if 'href=' not in link_tag.lower() or 'href="#"' in link_tag.lower():
                findings.append(self._create_finding(
                    title="Link without proper href",
                    description="Links should have meaningful href targets. Use <button> for actions.",
                    severity=Severity.LOW,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    code_snippet=link_tag[:100],
                    suggested_fix='Use proper URL or <button> for JavaScript actions'
                ))
        
        # Tables without proper structure
        if '<table' in content.lower():
            if '<th' not in content.lower():
                findings.append(self._create_finding(
                    title="Table without header cells",
                    description="Tables should use <th> elements for headers for screen reader compatibility.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    suggested_fix="Add <th> elements for column/row headers"
                ))
        
        # Autofocus usage
        if 'autofocus' in content.lower():
            findings.append(self._create_finding(
                title="Autofocus attribute used",
                description="Autofocus can disorient screen reader users and cause keyboard navigation issues.",
                severity=Severity.LOW,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix="Avoid autofocus; let users control focus"
            ))
        
        return findings
    
    def _check_design_quality(self, content: str, file_path: str) -> List[Finding]:
        """Check for design quality issues."""
        findings = []
        
        # Images without lazy loading
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, content, re.IGNORECASE):
            img_tag = match.group(0)
            if 'loading=' not in img_tag.lower():
                findings.append(self._create_finding(
                    title="Image without lazy loading",
                    description="Images below the fold should use lazy loading for better performance.",
                    severity=Severity.LOW,
                    finding_type=FindingType.PERFORMANCE,
                    location={"file": file_path},
                    code_snippet=img_tag[:100],
                    suggested_fix='Add loading="lazy" attribute',
                    auto_approvable=True
                ))
        
        # Inline styles
        inline_style_count = len(re.findall(r'style=["\']', content, re.IGNORECASE))
        if inline_style_count > 10:
            findings.append(self._create_finding(
                title=f"Many inline styles ({inline_style_count})",
                description="Inline styles are hard to maintain and override. Use CSS classes instead.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Move styles to CSS/SCSS files"
            ))
        
        # Hardcoded dimensions that might not be responsive
        if re.search(r'width=["\']\d+px["\']', content, re.IGNORECASE):
            findings.append(self._create_finding(
                title="Fixed pixel widths",
                description="Fixed pixel widths can cause overflow on smaller screens.",
                severity=Severity.LOW,
                finding_type=FindingType.UI,
                location={"file": file_path},
                suggested_fix="Use relative units (%, vw, rem) or max-width instead"
            ))
        
        # Missing title attribute on iframe
        iframe_pattern = r'<iframe[^>]*>'
        for match in re.finditer(iframe_pattern, content, re.IGNORECASE):
            iframe_tag = match.group(0)
            if 'title=' not in iframe_tag.lower():
                findings.append(self._create_finding(
                    title="Iframe without title",
                    description="Iframes should have title attributes for screen readers.",
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.ACCESSIBILITY,
                    location={"file": file_path},
                    code_snippet=iframe_tag[:100],
                    suggested_fix='Add title="Description of iframe content"'
                ))
        
        return findings
    
    def _check_css_issues(self, content: str, file_path: str) -> List[Finding]:
        """Check for CSS-specific issues."""
        findings = []
        
        # !important overuse
        important_count = content.count('!important')
        if important_count > 10:
            findings.append(self._create_finding(
                title=f"Excessive !important usage ({important_count})",
                description="Overuse of !important makes styles hard to maintain and override.",
                severity=Severity.LOW,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Increase selector specificity instead of using !important"
            ))
        
        # ID selectors (high specificity)
        id_selectors = len(re.findall(r'#[a-zA-Z][\w-]*\s*\{', content))
        if id_selectors > 20:
            findings.append(self._create_finding(
                title=f"Many ID selectors ({id_selectors})",
                description="ID selectors have high specificity and are hard to override. Prefer classes.",
                severity=Severity.INFO,
                finding_type=FindingType.CODE_QUALITY,
                location={"file": file_path},
                suggested_fix="Use class selectors instead of ID selectors"
            ))
        
        # Missing fallback fonts
        font_family_pattern = r'font-family:\s*([^;]+)'
        for match in re.finditer(font_family_pattern, content, re.IGNORECASE):
            font_list = match.group(1)
            if ',' not in font_list and 'sans-serif' not in font_list and 'serif' not in font_list:
                findings.append(self._create_finding(
                    title="Missing font fallback",
                    description="Font declarations should include generic fallback families.",
                    severity=Severity.LOW,
                    finding_type=FindingType.UI,
                    location={"file": file_path},
                    code_snippet=f"font-family: {font_list}",
                    suggested_fix='Add fallback: font-family: CustomFont, Arial, sans-serif'
                ))
        
        # px units for font sizes (should use rem)
        font_size_px = re.findall(r'font-size:\s*(\d+)px', content, re.IGNORECASE)
        if len(font_size_px) > 5:
            findings.append(self._create_finding(
                title=f"Pixel font sizes ({len(font_size_px)} instances)",
                description="Using px for font sizes prevents user font scaling. Use rem units instead.",
                severity=Severity.LOW,
                finding_type=FindingType.ACCESSIBILITY,
                location={"file": file_path},
                suggested_fix="Use rem units: 16px = 1rem"
            ))
        
        return findings
