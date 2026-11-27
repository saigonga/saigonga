"""Release cards (Linear-style rail): assets/release-v{N}-{wide,narrow}-{dark,light}.svg

Screenshots are 1280x800 PNGs of the live demos. Run locally when a release changes:
  uv run --no-project --with 'fonttools[woff]' --with pillow scripts/releases.py <shots_dir>
"""
import base64, io, sys
from pathlib import Path
from html import escape
from PIL import Image
from design import THEMES, SIZES, style, wrap, chip

OUT = Path(__file__).resolve().parent.parent / "assets"

# version, title, dates, summary, screenshots (front first), projects (name, line, live)
RELEASES = [
    ("v3", "Client work", "Jun 2026 → now",
     "Internal tools and client apps for brand and marketing teams",
     ["unseen-men"],
     [("NODD MEN", "Facial analysis for men's grooming from one photo", True),
      ("Creator search", "Search Instagram creators, build campaign shortlists", True),
      ("SOV dashboard", "Share-of-voice analytics for brand campaigns", True),
      ("Team project board", "One board for two teams, money views gated", False),
      ("Case-study site", "Agency site with an admin page to edit it live", True)]),
    ("v2", "Backend and data", "Jan → Apr 2026",
     "APIs, scraping, auth and automation, each with a real use behind it",
     ["web-scrapper"],
     [("Web Scrapper", "Static and JavaScript pages into structured JSON", True),
      ("finance-backend", "FastAPI and Postgres API with role-based access", False),
      ("TaskFlow", "Task manager with accounts and JWT auth", True),
      ("n8n workflow", "An agentic automation workflow", False)]),
    ("v1", "React apps", "May → Jul 2025",
     "Eleven projects in three months, from clones to a working dashboard",
     ["dashboard"],
     [("Dashboard", "", True), ("Todo", "", True), ("Form validation", "", True),
      ("Gemini 2.0 clone", "", False), ("Spotify 2.0", "", False), ("File sharing", "", False),
      ("E-commerce", "", False), ("Movie app", "", False), ("Shoe brand page", "", False),
      ("Blockchain voting", "", False), ("DSA practice", "", False)]),
    ("v0", "HTML and CSS", "Jan → Mar 2025",
     "Layout fundamentals, one design challenge at a time",
     ["news-homepage", "conference-ticket"],
     [("Bento grid", "", True), ("Conference ticket", "", True),
      ("News homepage", "", True), ("Social link page", "", True)]),
]

L = {  # DESIGN.md: rail column 176 wide; narrow collapses the rail to a top row
    "wide": dict(rail_x=48, col=216, right=840, title=32, summary=14, row=30, desc_x=176, cols=3),
    "narrow": dict(rail_x=12, col=32, right=424, title=28, summary=13, row=44, desc_x=0, cols=2),
}


def shot(png: Path, w: int) -> str:
    h = round(w * 9 / 16)
    im = Image.open(png).convert("RGB").crop((0, 0, 1280, 720)).resize((w * 2, h * 2), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=78, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def card(t, size, rel, imgs, current) -> str:
    v, title, dates, summary, _, projects = rel
    W, c = SIZES[size], L[size]
    x, right = c["col"], c["right"]
    o: list[str] = []
    a = o.append
    if size == "wide":
        a(chip(c["rail_x"] + 20, 52, v, t, current))
        a(f'<text x="{c["rail_x"]+20}" y="{104}" font-size="12" fill="{t["muted"]}">{dates}</text>')
        y = 72
    else:
        a(chip(x, 24, v, t, current))
        a(f'<text x="{x + len(v)*7.2 + 28}" y="40.5" font-size="12" fill="{t["muted"]}">{dates}</text>')
        y = 100
    a(f'<text class="s" x="{x-2}" y="{y}" font-size="{c["title"]}" fill="{t["text"]}">{title}</text>')
    for i, line in enumerate(wrap(summary, c["summary"], right - x)):
        y2 = y + 32 + i * 20
        a(f'<text x="{x}" y="{y2}" font-size="{c["summary"]}" fill="{t["text2"]}">{line}</text>')
    y = y2 + 28

    # the visual: one screenshot, or two overlapped like stacked cards
    vw = right - x - (48 if len(imgs) > 1 else 0) * (1 if size == "wide" else .5)
    vw = round(vw)
    vh = round(vw * 9 / 16)
    off = 0 if len(imgs) == 1 else (48 if size == "wide" else 24)
    for i, src in reversed(list(enumerate(imgs))):
        ix, iy = x + (off if i else 0), y + (0 if i else off)
        cid = f"c{i}"
        a(f'<clipPath id="{cid}"><rect x="{ix}" y="{iy}" width="{vw}" height="{vh}" rx="8"/></clipPath>')
        if i == 0 and off:  # front card hides the back one
            a(f'<rect x="{ix}" y="{iy}" width="{vw}" height="{vh}" rx="8" fill="{t["card"]}"/>')
        a(f'<image clip-path="url(#{cid})" x="{ix}" y="{iy}" width="{vw}" height="{vh}" href="{src}"'
          f'{" opacity=\".55\"" if i else ""}/>')
        a(f'<rect x="{ix+.5}" y="{iy+.5}" width="{vw-1}" height="{vh-1}" rx="8" fill="none" stroke="{t["line"]}"/>')
    y += vh + off + 40

    # project list
    has_desc = any(d for _, d, _ in projects)
    if has_desc:
        for name, desc, live in projects:
            dot = (f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{t["accent"]}"/>' if live else
                   f'<circle cx="{x+4}" cy="{y-4}" r="3.5" fill="none" stroke="{t["ring"]}" stroke-width="1.5"/>')
            a(dot + f'<text x="{x+16}" y="{y}" font-size="14" font-weight="500" fill="{t["text"]}">{escape(name)}</text>')
            dx, dy = (x + c["desc_x"], y) if size == "wide" else (x + 16, y + 19)
            lines = wrap(desc, 13, right - dx)
            assert size == "narrow" or len(lines) == 1, name  # wide: one line per project
            for j, line in enumerate(lines):
                a(f'<text x="{dx}" y="{dy + j*18}" font-size="13" fill="{t["text2"]}">{escape(line)}</text>')
            y += c["row"] + 18 * (len(lines) - 1)
    else:
        colw = (right - x) / c["cols"]
        for i, (name, _, live) in enumerate(projects):
            px, py = x + (i % c["cols"]) * colw, y + (i // c["cols"]) * 28
            dot = (f'<circle cx="{px+4}" cy="{py-4}" r="4" fill="{t["accent"]}"/>' if live else
                   f'<circle cx="{px+4}" cy="{py-4}" r="3.5" fill="none" stroke="{t["ring"]}" stroke-width="1.5"/>')
            a(dot + f'<text x="{px+16}" y="{py}" font-size="13" fill="{t["text"]}">{escape(name)}</text>')
        y += ((len(projects) - 1) // c["cols"] + 1) * 28
    H = y + 24

    rail = c["rail_x"]
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Release {v}: {escape(title)}, {dates}. {escape(summary)}.">', style(),
            # rail runs edge to edge so stacked releases read as one line
            f'<line x1="{rail}" y1="0" x2="{rail}" y2="{H}" stroke="{t["line"]}"/>',
            f'<circle cx="{rail}" cy="{64 if size == "wide" else 36}" r="5" fill="{t["accent"] if current else t["card"]}" stroke="{t["accent"] if current else t["ring"]}"/>']
    return "\n".join(head + o + ["</svg>"])


if __name__ == "__main__":
    shots = Path(sys.argv[1])
    for n, rel in enumerate(RELEASES):
        for size in SIZES:
            c = L[size]
            vw = round(c["right"] - c["col"] - (48 if len(rel[4]) > 1 else 0) * (1 if size == "wide" else .5))
            imgs = [shot(shots / f"{s}.png", vw) for s in rel[4]]
            for name, t in THEMES.items():
                p = OUT / f"release-{rel[0]}-{size}-{name}.svg"
                p.write_text(card(t, size, rel, imgs, current=n == 0))
                print(p.name, p.stat().st_size)
