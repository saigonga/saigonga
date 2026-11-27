"""Build project cards (assets/work/<slug>-{dark,light}.svg) from screenshots.

Screenshots are 1280x800 PNGs of the live demos. Run locally when a project changes:
  uv run --no-project --with 'fonttools[woff]' --with pillow scripts/cards.py <shots_dir>
"""
import base64, io, sys
from pathlib import Path
from PIL import Image
from changelog import THEMES, font_b64

OUT = Path(__file__).resolve().parent.parent / "assets/work"
W, H, P = 428, 384, 16
IW, IH = W - 2 * P, round((W - 2 * P) * 9 / 16)

PROJECTS = [  # slug, title, url, release, description lines, stack
    ("unseen-men", "NODD MEN", "unseen-men.vercel.app", "v3",
     ["Facial analysis for men's grooming. One", "photo in, nine structural attributes out"],
     "TypeScript · Vercel"),
    ("tbm-portfolio", "TBM Portfolio", "tbmportfolio.vercel.app", "v3",
     ["An agency's case-study site, with an", "admin page that edits it live"],
     "JavaScript · Vercel"),
    ("web-scrapper", "Web Scrapper", "web-scrapper-kohl.vercel.app", "v2",
     ["Turns any page, static or JavaScript-", "heavy, into structured JSON"],
     "FastAPI · Playwright · BeautifulSoup"),
    ("instagramtbm", "TBM Studio", "instagramtbm-alpha.vercel.app", "v3",
     ["Search Instagram's Creator Marketplace", "and build shortlists per campaign"],
     "Next.js · Supabase · Meta Graph API"),
]


def shot_b64(png: Path) -> str:
    im = Image.open(png).convert("RGB").crop((0, 0, 1280, 720)).resize((IW * 2, IH * 2), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def card(t, img, title, url, rel, desc, stack, reg, med) -> str:
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" role="img" aria-label="{title}: {" ".join(desc)}">',
         f"""<style>
@font-face{{font-family:J;font-weight:400;src:url(data:font/woff2;base64,{reg}) format('woff2')}}
@font-face{{font-family:J;font-weight:500;src:url(data:font/woff2;base64,{med}) format('woff2')}}
text{{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace}}
</style>""",
         f'<clipPath id="c"><rect x="{P}" y="{P}" width="{IW}" height="{IH}" rx="8"/></clipPath>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}"/>',
         f'<image clip-path="url(#c)" x="{P}" y="{P}" width="{IW}" height="{IH}" href="data:image/jpeg;base64,{img}"/>',
         f'<rect x="{P+.5}" y="{P+.5}" width="{IW-1}" height="{IH-1}" rx="8" fill="none" stroke="{t["line"]}"/>']
    y = P + IH + 28
    o += [f'<circle cx="{P+4}" cy="{y-4}" r="4" fill="{t["accent"]}"/>',
          f'<text x="{P+14}" y="{y}" font-size="11" fill="{t["muted"]}">{url}</text>',
          f'<text x="{W-P}" y="{y}" font-size="11" text-anchor="end" fill="{t["muted"]}">{rel}</text>',
          f'<text x="{P}" y="{y+30}" font-size="17" font-weight="500" fill="{t["text"]}">{title}</text>']
    for i, line in enumerate(desc):
        o.append(f'<text x="{P}" y="{y+54+i*19}" font-size="13" fill="{t["text2"]}">{line}</text>')
    o.append(f'<text x="{P}" y="{H-P-4}" font-size="11" fill="{t["muted"]}">{stack}</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    shots = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
    chars = "".join(chr(c) for c in range(32, 127)) + "·"
    reg, med = font_b64("JetBrainsMono-Regular.ttf", chars), font_b64("JetBrainsMono-Medium.ttf", chars)
    for slug, title, url, rel, desc, stack in PROJECTS:
        assert all(len(l) <= 50 for l in desc), slug  # 13px mono fits ~50 chars in the card
        img = shot_b64(shots / f"{slug}.png")
        for name, t in THEMES.items():
            p = OUT / f"{slug}-{name}.svg"
            p.write_text(card(t, img, title, url, rel, desc, stack, reg, med))
            print(p.name, p.stat().st_size)
