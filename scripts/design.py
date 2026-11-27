"""Shared design tokens and SVG helpers. Source of truth: DESIGN.md in the project folder."""
import base64, glob, io
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

THEMES = {
    "dark": dict(card="#12161c", line="rgba(230,237,243,0.09)", bar="rgba(230,237,243,0.11)",
                 text="#e6e8eb", text2="#9aa3ad", muted="#848d97", accent="#3fb950", ring="#4a525c"),
    "light": dict(card="#f8f9fa", line="rgba(31,35,40,0.10)", bar="rgba(31,35,40,0.09)",
                  text="#1f2328", text2="#4b535d", muted="#5f6873", accent="#1a7f37", ring="#b6bcc3"),
}
SIZES = {"wide": 880, "narrow": 440}  # narrow is picked on phones via <picture media>
FONT_DIRS = [str(Path.home() / "Library/Fonts"), "fonts",
             str(Path.home() / "Desktop/Projects/Web-Design/skills-library/parked/ui-styling/canvas-fonts"),
             "/usr/share/fonts/**"]
CHARS = "".join(chr(c) for c in range(32, 127)) + "·×→"
MONO_W = 0.6  # JetBrains Mono advance width per px of font size

_cache: dict[str, str] = {}


def font_b64(name: str, chars: str = CHARS) -> str:
    key = name + chars
    if key not in _cache:
        path = next(p for d in FONT_DIRS for p in glob.glob(f"{d}/{name}", recursive=True))
        f = TTFont(path)
        opts = subset.Options(); opts.flavor = "woff2"
        s = subset.Subsetter(opts); s.populate(text=chars); s.subset(f)
        buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
        _cache[key] = base64.b64encode(buf.getvalue()).decode()
    return _cache[key]


def style(extra: str = "", serif: bool = True) -> str:
    faces = [("J", 400, "JetBrainsMono-Regular.ttf"), ("J", 500, "JetBrainsMono-Medium.ttf")]
    if serif:
        faces.append(("S", 400, "InstrumentSerif-Regular.ttf"))
    css = "".join(f"@font-face{{font-family:{fam};font-weight:{w};src:url(data:font/woff2;base64,{font_b64(f)}) format('woff2')}}"
                  for fam, w, f in faces)
    return (f"<style>{css}text{{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace;"
            f"font-variant-numeric:tabular-nums}}.s{{font-family:S,Georgia,serif}}{extra}</style>")


def wrap(text: str, size: float, width: float) -> list[str]:
    """Word-wrap mono text to a pixel width."""
    per_line = int(width / (size * MONO_W))
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > per_line:
            lines.append(cur); cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur else lines


def chip(x: float, y: float, label: str, t: dict, current: bool) -> str:
    """Version chip, e.g. v3. Returns svg; width = len*7.2+16."""
    w = len(label) * 12 * MONO_W + 16
    col = t["accent"] if current else t["text2"]
    return (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="24" rx="6" fill="none" stroke="{col if current else t["line"]}"/>'
            f'<text x="{x + w/2:.1f}" y="{y+16.5}" font-size="12" font-weight="500" text-anchor="middle" fill="{col}">{label}</text>')


def picture(base: str, alt: str, href: str | None = None) -> str:
    """README markup: 4 variants (narrow/wide x dark/light)."""
    p = (f'<picture>'
         f'<source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="./assets/{base}-narrow-dark.svg">'
         f'<source media="(max-width: 600px)" srcset="./assets/{base}-narrow-light.svg">'
         f'<source media="(prefers-color-scheme: dark)" srcset="./assets/{base}-wide-dark.svg">'
         f'<img src="./assets/{base}-wide-light.svg" width="100%" alt="{alt}"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p
