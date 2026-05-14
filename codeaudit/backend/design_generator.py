"""
HTML-native design generator — inspired by alchaincyf/huashu-design.
Generates interactive HTML prototypes, slide decks, and design previews.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.design_system import suggest_design, get_style, get_palette, get_font_pairing


def generate_prototype(
    title: str,
    screens: List[Dict[str, Any]],
    style_name: str = "glassmorphism",
    palette_name: str = "ocean",
    font_pair_name: str = "modern",
    mobile_frame: bool = True,
) -> Dict[str, Any]:
    style = get_style(style_name) or {}
    palette = get_palette(palette_name) or {}
    font_pair = get_font_pairing(font_pair_name) or {}

    colors = palette.get("colors", ["#6366f1", "#4f46e5", "#e0e7ff", "#f0f0ff"])
    heading_font = font_pair.get("heading", "Inter")
    body_font = font_pair.get("body", "Inter")

    screens_html = ""
    for i, screen in enumerate(screens):
        is_active = "active" if i == 0 else ""
        screens_html += f"""
        <div class="screen {is_active}" id="screen-{i}">
            <div class="screen-header">{screen.get("name", f"Screen {i+1}")}</div>
            <div class="screen-content">
                {screen.get("content", "")}
            </div>
        </div>"""

    nav_dots = "".join(
        f'<span class="dot {"active" if i == 0 else ""}" onclick="showScreen({i})"></span>'
        for i in range(len(screens))
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: '{body_font}', Arial, sans-serif;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: #f0f2f5;
}}
.prototype {{
    {style.get("css", "background: white; border-radius: 16px;")}
    {f"width: 390px; height: 844px;" if mobile_frame else "width: 100%; max-width: 1200px; min-height: 600px;"}
    overflow: hidden; display: flex; flex-direction: column;
    position: relative; font-family: '{body_font}', sans-serif;
}}
{mobile_frame and '''
.notch {{
    position: absolute; top: 0; left: 50%; transform: translateX(-50%);
    width: 150px; height: 30px; background: #000;
    border-radius: 0 0 16px 16px; z-index: 100;
    display: flex; justify-content: center; align-items: center;
    gap: 6px;
}}
.notch::before {{ content: ''; width: 60px; height: 6px; background: #333; border-radius: 3px; }}
.notch::after {{ content: ''; width: 10px; height: 10px; border-radius: 50%; border: 2px solid #333; }}
''' or ''}
.screen {{ display: none; flex: 1; flex-direction: column; }}
.screen.active {{ display: flex; }}
.screen-header {{
    padding: {f"44px 16px 12px" if mobile_frame else "16px"};
    font-weight: 600; font-size: 18px;
    border-bottom: 1px solid rgba(0,0,0,0.1);
    font-family: '{heading_font}', sans-serif;
}}
.screen-content {{ flex: 1; padding: 16px; overflow-y: auto; }}
.nav-dots {{
    display: flex; justify-content: center; gap: 8px;
    padding: 12px; background: inherit;
}}
.dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {colors[3]}; cursor: pointer; transition: all 0.3s;
}}
.dot.active {{ background: {colors[0]}; width: 24px; border-radius: 4px; }}
.btn {{
    display: inline-block; padding: 10px 24px; border-radius: 8px;
    background: {colors[0]}; color: white; border: none;
    cursor: pointer; font-family: '{body_font}', sans-serif;
    font-size: 14px; transition: opacity 0.2s;
    text-decoration: none;
}}
.btn:hover {{ opacity: 0.9; }}
.card {{
    background: white; border-radius: 12px; padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 12px;
}}
.input {{
    width: 100%; padding: 10px 14px; border: 1px solid {colors[3]};
    border-radius: 8px; font-family: '{body_font}', sans-serif;
    font-size: 14px; margin-bottom: 12px;
}}
</style>
</head>
<body>
<div class="prototype">
    {f'<div class="notch"></div>' if mobile_frame else ''}
    {screens_html}
    <div class="nav-dots">{nav_dots}</div>
</div>
<script>
const screens = document.querySelectorAll('.screen');
const dots = document.querySelectorAll('.dot');
let current = 0;
function showScreen(idx) {{
    screens.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    screens[idx].classList.add('active');
    dots[idx].classList.add('active');
    current = idx;
}}
function nextScreen() {{ showScreen(Math.min(current + 1, screens.length - 1)); }}
function prevScreen() {{ showScreen(Math.max(current - 1, 0)); }}
document.addEventListener('keydown', e => {{
    if (e.key === 'ArrowRight') nextScreen();
    if (e.key === 'ArrowLeft') prevScreen();
}});
</script>
</body>
</html>"""

    output = {
        "title": title,
        "html": html,
        "screens": len(screens),
        "style": style_name,
        "palette": palette_name,
        "mobile_frame": mobile_frame,
        "size_bytes": len(html),
        "generated_at": datetime.utcnow().isoformat(),
    }
    return output


def generate_slide_deck(
    title: str,
    slides: List[Dict[str, Any]],
    palette_name: str = "midnight",
) -> Dict[str, Any]:
    palette = get_palette(palette_name) or {}
    colors = palette.get("colors", ["#1e293b", "#334155", "#94a3b8", "#cbd5e1"])

    slides_html = ""
    for i, slide in enumerate(slides):
        is_active = "active" if i == 0 else ""
        slides_html += f"""
        <div class="slide {is_active}" id="slide-{i}">
            <div class="slide-number">{i + 1}/{len(slides)}</div>
            <h1 class="slide-title">{slide.get("title", "")}</h1>
            <div class="slide-body">{slide.get("content", "")}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: #1a1a2e;
    font-family: 'Inter', system-ui, sans-serif;
}}
.deck {{
    width: 100%; max-width: 1024px; height: 768px;
    background: white; border-radius: 8px; overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    position: relative; display: flex; flex-direction: column;
}}
.slide {{ display: none; flex: 1; padding: 48px 64px; flex-direction: column; }}
.slide.active {{ display: flex; }}
.slide-number {{ position: absolute; bottom: 16px; right: 24px; font-size: 12px; color: {colors[2]}; }}
.slide-title {{ font-size: 36px; font-weight: 700; color: {colors[0]}; margin-bottom: 24px; }}
.slide-body {{ font-size: 18px; line-height: 1.6; color: {colors[1]}; flex: 1; }}
.slide-body ul {{ padding-left: 24px; }}
.slide-body li {{ margin-bottom: 8px; }}
.nav {{
    display: flex; justify-content: center; gap: 16px;
    padding: 16px; background: #f8fafc; border-top: 1px solid #e2e8f0;
}}
.nav button {{
    padding: 8px 20px; border: none; border-radius: 6px;
    cursor: pointer; font-size: 14px;
    background: {colors[0]}; color: white; transition: opacity 0.2s;
}}
.nav button:hover {{ opacity: 0.85; }}
.nav button:disabled {{ opacity: 0.4; cursor: default; }}
</style>
</head>
<body>
<div class="deck">
    {slides_html}
    <div class="nav">
        <button onclick="changeSlide(-1)" id="prevBtn">← Previous</button>
        <span style="align-self:center;font-size:13px;color:{colors[2]}">{title}</span>
        <button onclick="changeSlide(1)" id="nextBtn">Next →</button>
    </div>
</div>
<script>
let current = 0;
const slides = document.querySelectorAll('.slide');
function changeSlide(dir) {{
    slides[current].classList.remove('active');
    current = Math.max(0, Math.min(current + dir, slides.length - 1));
    slides[current].classList.add('active');
    document.getElementById('prevBtn').disabled = current === 0;
    document.getElementById('nextBtn').disabled = current === slides.length - 1;
}}
document.addEventListener('keydown', e => {{
    if (e.key === 'ArrowRight') changeSlide(1);
    if (e.key === 'ArrowLeft') changeSlide(-1);
}});
</script>
</body>
</html>"""

    return {
        "title": title,
        "html": html,
        "slides": len(slides),
        "size_bytes": len(html),
    }


def generate_design_review(
    project_name: str,
    issues: List[Dict[str, Any]],
    palette_name: str = "neutral",
) -> str:
    palette = get_palette(palette_name) or {}
    colors = palette.get("colors", ["#6b7280", "#4b5563", "#d1d5db"])

    issues_html = ""
    for i, issue in enumerate(issues):
        sev_color = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#6b7280"}.get(
            issue.get("severity", "medium"), "#6b7280"
        )
        issues_html += f"""
        <div style="border-left: 3px solid {sev_color}; padding: 8px 12px; margin-bottom: 8px; background: #f9fafb; border-radius: 0 6px 6px 0;">
            <div style="font-weight: 600; font-size: 13px;">{issue.get("title", "")}</div>
            <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">{issue.get("description", "")}</div>
            <div style="font-size: 11px; color: {sev_color}; margin-top: 2px;">{issue.get("severity", "medium")}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Design Review: {project_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', system-ui, sans-serif; background: #f0f2f5; padding: 24px; }}
.review {{ max-width: 800px; margin: 0 auto; }}
h1 {{ font-size: 24px; color: {colors[0]}; margin-bottom: 4px; }}
h2 {{ font-size: 14px; color: {colors[1]}; margin: 16px 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
.summary {{ display: flex; gap: 12px; margin: 16px 0; }}
.stat {{ background: white; padding: 12px 20px; border-radius: 8px; text-align: center; flex: 1; }}
.stat-num {{ font-size: 24px; font-weight: 700; }}
.stat-label {{ font-size: 11px; color: {colors[2]}; }}
</style>
</head>
<body>
<div class="review">
    <h1>Design Review: {project_name}</h1>
    <div class="summary">
        <div class="stat"><div class="stat-num">{len(issues)}</div><div class="stat-label">Issues</div></div>
        <div class="stat"><div class="stat-num">{sum(1 for i in issues if i.get("severity") == "critical")}</div><div class="stat-label">Critical</div></div>
        <div class="stat"><div class="stat-num">{sum(1 for i in issues if i.get("severity") == "high")}</div><div class="stat-label">High</div></div>
    </div>
    <h2>Findings</h2>
    {issues_html}
</div>
</body>
</html>"""


def save_html(html: str, filepath: str) -> str:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return str(path.resolve())
