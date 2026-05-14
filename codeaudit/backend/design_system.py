"""
Design system intelligence — inspired by ui-ux-pro-max-skill.
Provides curated UI styles, color palettes, font pairings, and design rules.
"""
from typing import List, Dict, Any, Optional


UI_STYLES = {
    "glassmorphism": {
        "name": "Glassmorphism",
        "description": "Frosted glass effect with backdrop blur, semi-transparent backgrounds, and subtle borders.",
        "css": "background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);",
        "tags": ["modern", "trending", "light"],
    },
    "neumorphism": {
        "name": "Neumorphism",
        "description": "Soft UI with extruded elements using dual box-shadows for a plastic/embossed look.",
        "css": "box-shadow: 8px 8px 16px #d1d1d1, -8px -8px 16px #ffffff; border-radius: 12px;",
        "tags": ["soft", "trending"],
    },
    "claymorphism": {
        "name": "Claymorphism",
        "description": "Rounded, bulging elements with distinct top lighting and rich colors.",
        "css": "border-radius: 20px; box-shadow: 0 10px 20px -5px rgba(0,0,0,0.3), inset 0 -3px 0 rgba(0,0,0,0.1);",
        "tags": ["playful", "colorful"],
    },
    "brutalism": {
        "name": "Brutalism",
        "description": "Raw, harsh design with thick borders, bold typography, and stark color contrasts.",
        "css": "border: 3px solid #000; box-shadow: 5px 5px 0 #000; font-weight: 900;",
        "tags": ["bold", "edgy", "raw"],
    },
    "minimalism": {
        "name": "Minimalism",
        "description": "Clean, sparse design with maximum whitespace, limited colors, and precise typography.",
        "css": "padding: 2rem; max-width: 720px; color: #1a1a1a;",
        "tags": ["clean", "professional", "fast"],
    },
    "bento_grid": {
        "name": "Bento Grid",
        "description": "Japanese bento-box-inspired asymmetric grid layout with varied cell sizes.",
        "css": "display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; grid-auto-rows: minmax(100px, auto);",
        "tags": ["modern", "structured", "trending"],
    },
    "dark_mode": {
        "name": "Dark Mode",
        "description": "Dark background with light text, reduced blue light, and accent colors that pop.",
        "css": "background: #0a0a0a; color: #e0e0e0; accent-color: #6366f1;",
        "tags": ["modern", "accessible", "popular"],
    },
    "retro": {
        "name": "Retro/Vaporwave",
        "description": "Neon gradients, chrome text, grid backgrounds, and 80s/90s synthwave aesthetic.",
        "css": "background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #ff00ff; font-family: 'Courier New';",
        "tags": ["nostalgic", "colorful", "trending"],
    },
    "corporate": {
        "name": "Corporate Clean",
        "description": "Professional, trustworthy design with blue tones, clean lines, and conservative spacing.",
        "css": "font-family: 'Inter', Arial, sans-serif; color: #1e293b; max-width: 1200px;",
        "tags": ["professional", "business", "clean"],
    },
    "playful": {
        "name": "Playful/Kid-friendly",
        "description": "Rounded corners, bright saturated colors, bouncy animations, and fun illustrations.",
        "css": "border-radius: 16px; font-family: 'Nunito', sans-serif; transition: transform 0.2s ease;",
        "tags": ["fun", "colorful", "accessible"],
    },
}

COLOR_PALETTES = {
    "ocean": {"name": "Ocean Blues", "colors": ["#0ea5e9", "#0284c7", "#0369a1", "#bae6fd", "#e0f2fe"], "industry": ["tech", "saas", "finance"]},
    "forest": {"name": "Forest Green", "colors": ["#22c55e", "#16a34a", "#15803d", "#bbf7d0", "#dcfce7"], "industry": ["environment", "health", "organic"]},
    "sunset": {"name": "Sunset Warm", "colors": ["#f97316", "#ea580c", "#c2410c", "#fed7aa", "#ffedd5"], "industry": ["food", "travel", "ecommerce"]},
    "royal": {"name": "Royal Purple", "colors": ["#8b5cf6", "#7c3aed", "#6d28d9", "#ddd6fe", "#ede9fe"], "industry": ["luxury", "beauty", "education"]},
    "rose": {"name": "Rose Pink", "colors": ["#f43f5e", "#e11d48", "#be123c", "#fecdd3", "#ffe4e6"], "industry": ["fashion", "dating", "media"]},
    "midnight": {"name": "Midnight", "colors": ["#1e293b", "#334155", "#475569", "#94a3b8", "#cbd5e1"], "industry": ["finance", "legal", "enterprise"]},
    "amber": {"name": "Amber Glow", "colors": ["#f59e0b", "#d97706", "#b45309", "#fde68a", "#fef3c7"], "industry": ["automotive", "industrial", "logistics"]},
    "teal": {"name": "Teal Modern", "colors": ["#14b8a6", "#0d9488", "#0f766e", "#99f6e4", "#ccfbf1"], "industry": ["healthcare", "wellness", "science"]},
    "neutral": {"name": "Neutral Gray", "colors": ["#6b7280", "#4b5563", "#374151", "#d1d5db", "#e5e7eb"], "industry": ["any", "minimal"]},
    "vibrant": {"name": "Vibrant Pop", "colors": ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff6eb4"], "industry": ["creative", "agency", "startup"]},
}

FONT_PAIRINGS = {
    "classic": {"heading": "Playfair Display", "body": "Source Sans Pro", "mood": "elegant"},
    "modern": {"heading": "Inter", "body": "Inter", "mood": "clean"},
    "friendly": {"heading": "Nunito", "body": "Open Sans", "mood": "warm"},
    "technical": {"heading": "JetBrains Mono", "body": "IBM Plex Sans", "mood": "technical"},
    "editorial": {"heading": "Lora", "body": "Proza Libre", "mood": "editorial"},
    "bold": {"heading": "Montserrat", "body": "Merriweather", "mood": "bold"},
    "playful": {"heading": "Fredoka One", "body": "Quicksand", "mood": "playful"},
    "minimal": {"heading": "DM Sans", "body": "DM Sans", "mood": "minimal"},
    "luxury": {"heading": "Cormorant Garamond", "body": "Proza Libre", "mood": "luxury"},
    "startup": {"heading": "Clash Display", "body": "Satoshi", "mood": "modern"},
}


def get_style(name: str) -> Optional[Dict[str, Any]]:
    return UI_STYLES.get(name)


def list_styles(tag: Optional[str] = None) -> List[Dict[str, Any]]:
    if tag:
        return [s for s in UI_STYLES.values() if tag in s["tags"]]
    return list(UI_STYLES.values())


def get_palette(name: str) -> Optional[Dict[str, Any]]:
    return COLOR_PALETTES.get(name)


def list_palettes(industry: Optional[str] = None) -> List[Dict[str, Any]]:
    if industry:
        return [p for p in COLOR_PALETTES.values() if industry in p["industry"]]
    return list(COLOR_PALETTES.values())


def get_font_pairing(name: str) -> Optional[Dict[str, Any]]:
    return FONT_PAIRINGS.get(name)


def list_font_pairings(mood: Optional[str] = None) -> List[Dict[str, Any]]:
    if mood:
        return [f for f in FONT_PAIRINGS.values() if f["mood"] == mood]
    return list(FONT_PAIRINGS.values())


def suggest_design(project_type: str = "web") -> Dict[str, Any]:
    industry_map = {
        "saas": "tech", "ecommerce": "retail", "blog": "media",
        "portfolio": "creative", "dashboard": "tech", "landing": "startup",
        "mobile": "tech", "enterprise": "finance",
    }
    industry = industry_map.get(project_type, "tech")

    palette_industry_map = {
        "tech": "ocean", "retail": "sunset", "media": "royal",
        "creative": "vibrant", "finance": "midnight", "health": "teal",
        "food": "sunset", "education": "royal", "startup": "vibrant",
    }
    palette_name = palette_industry_map.get(industry, "neutral")
    palette = get_palette(palette_name)

    style_map = {
        "tech": "glassmorphism", "retail": "playful", "startup": "bento_grid",
        "creative": "brutalism", "finance": "corporate", "professional": "corporate",
    }
    style_name = style_map.get(industry, "minimalism")
    style = get_style(style_name)

    font_pair = get_font_pairing("modern")

    return {
        "style": style,
        "palette": palette,
        "font_pairing": font_pair,
        "industry": industry,
    }
