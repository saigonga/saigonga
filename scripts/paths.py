"""'Pick your path' rows: assets/path-{slug}-{wide,narrow}-{dark,light}.svg

Each row is its own image wrapped in a link to its section, so it reads as a button.
  uv run --no-project --with 'fonttools[woff]' scripts/paths.py
"""
from pathlib import Path
from design import THEMES, SIZES, style, wrap

OUT = Path(__file__).resolve().parent.parent / "assets"
PATHS = [  # slug, number, title, promise
    ("hiring", "01", "Hiring?", "The 30-second version: what I ship and where I'd fit"),
    ("developer", "02", "A developer?", "How the scraper, the API and this profile are built"),
    ("client", "03", "Need something built?", "Dashboards, scrapers, APIs and sites your team can edit"),
]


def row(t, size, num, title, promise) -> str:
    W = SIZES[size]
    P = 32 if size == "wide" else 20
    lines = wrap(promise, 13, W - 2 * P - (300 if size == "wide" else 40))
    if size == "wide":
        H = 88
        body = [f'<text x="{P}" y="50" font-size="12" fill="{t["muted"]}">{num}</text>',
                f'<text class="s" x="{P+40}" y="54" font-size="28" fill="{t["text"]}">{title}</text>',
                f'<text x="{P+336}" y="49" font-size="13" fill="{t["text2"]}">{lines[0]}</text>']
        assert len(lines) == 1, title  # wide: promise fits beside the title
        ay = 49
    else:
        H = 92 + 18 * len(lines)  # 20px under the last line
        body = [f'<text x="{P}" y="{P+14}" font-size="12" fill="{t["muted"]}">{num}</text>',
                f'<text class="s" x="{P}" y="{P+46}" font-size="26" fill="{t["text"]}">{title}</text>']
        body += [f'<text x="{P}" y="{P+70+i*18}" font-size="13" fill="{t["text2"]}">{l}</text>' for i, l in enumerate(lines)]
        ay = P + 44
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title} {promise}">',
        style(),
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{t["card"]}" stroke="{t["line"]}"/>',
        *body,
        f'<text x="{W-P}" y="{ay+1}" font-size="18" text-anchor="end" fill="{t["accent"]}">→</text>',
        "</svg>"])


if __name__ == "__main__":
    for slug, num, title, promise in PATHS:
        for size in SIZES:
            for name, t in THEMES.items():
                p = OUT / f"path-{slug}-{size}-{name}.svg"
                p.write_text(row(t, size, num, title, promise))
        print(slug, "ok")
