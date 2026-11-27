"""Build the profile release card (dark + light SVG) for saigonga/saigonga.

Usage: uv run --with 'fonttools[woff]' make_card.py <out_dir>
"""
import base64, io, sys
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

OUT = Path(sys.argv[1])
FONTS = Path.home() / "Library/Fonts"

# (month index from Jan 2025, repo, live?)  month = repo creation, Bento Grid = first deploy
REPOS = [
    (0, "Bento-Grid", 1), (1, "Conference-Ticket-Generator", 1), (1, "social-link-page", 1),
    (2, "news-homepage", 1),
    (4, "DSA", 0), (4, "Blockchain_based_voting_system", 0), (4, "MovieApp", 0),
    (4, "Shoe_Brand_page", 0), (4, "Gemini_2.0-clone", 0), (4, "File-Sharing-App", 0),
    (4, "Form-Validation", 1),
    (5, "TODO-App", 1), (5, "Dashboard", 1), (5, "Spotify-2.0", 0), (6, "E-Commerce-Website", 0),
    (12, "N8N-workflow", 0), (12, "Web-Scrapper", 1), (14, "Product-Validator", 0),
    (15, "finance-backend", 0), (15, "Task-Manager", 1),
    (17, "SOV-Dashboard", 1), (18, "INSTAGRAMTBM", 1), (19, "Final-SOV-panel", 0),
    (21, "Unseen-Men", 1), (21, "BrandSolution-panel", 0), (22, "TBMPortfolio", 1),
]
RELEASES = [(0, 2, "v0", "html + css"), (4, 6, "v1", "react apps"),
            (12, 15, "v2", "backend + data"), (17, 22, "v3", "client work at TBM")]
MONTHS = 23  # Jan 2025 .. Nov 2026

THEMES = {
    "dark": dict(bg="#0d1117", card="#12161c", line="rgba(230,237,243,0.09)",
                 text="#e6e8eb", text2="#9aa3ad", muted="#6b7480", accent="#3fb950",
                 ring="#4a525c"),
    "light": dict(bg="#ffffff", card="#f8f9fa", line="rgba(31,35,40,0.10)",
                  text="#1f2328", text2="#4b535d", muted="#6e7781", accent="#1a7f37",
                  ring="#b6bcc3"),
}

W, H, PAD = 880, 380, 40
X0, X1, AXIS_Y, STEP = 56, W - 56, 316, 14


def x_of(m: int) -> float:
    return X0 + m * (X1 - X0) / (MONTHS - 1)


TEXTS = ["saigonga · changelog", "Sai Gonga", "open to SDE roles", "v3 · now",
         "Full-stack developer. Dashboards, scrapers and APIs, shipped live",
         "Mumbai · Class of 2026 · Full-stack at TBM", "live", "code only", "now",
         "Jan 25 Apr Jul Oct Jan 26", "26 repos since January 2025"] + [
    f"{v} {d}" for *_, v, d in RELEASES]


def font_b64(file: str) -> str:
    chars = "".join(sorted(set("".join(TEXTS))))
    f = TTFont(FONTS / file)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern"]
    s = subset.Subsetter(opts); s.populate(text=chars); s.subset(f)
    buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def card(t: dict, reg: str, med: str) -> str:
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="Sai Gonga, full-stack developer. Timeline of 26 repos from January 2025 to November 2026.">')
    a(f"""<style>
@font-face{{font-family:J;font-weight:400;src:url(data:font/woff2;base64,{reg}) format('woff2')}}
@font-face{{font-family:J;font-weight:500;src:url(data:font/woff2;base64,{med}) format('woff2')}}
text{{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}}
</style>""")  # no entrance animation: some README viewers freeze SVG at frame 0
    a(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}"/>')

    # header
    a(f'<text x="{PAD}" y="52" font-size="13" fill="{t["muted"]}">saigonga · changelog</text>')
    a(f'<text x="{PAD}" y="100" font-size="40" font-weight="500" letter-spacing="-1" fill="{t["text"]}">Sai Gonga</text>')
    a(f'<text x="{PAD}" y="132" font-size="15" fill="{t["text2"]}">Full-stack developer. Dashboards, scrapers and APIs, shipped live</text>')
    a(f'<text x="{PAD}" y="156" font-size="13" fill="{t["muted"]}">Mumbai · Class of 2026 · Full-stack at TBM</text>')

    # status, top right
    rx = W - PAD
    a(f'<rect x="{rx-168}" y="34" width="168" height="28" rx="8" fill="none" stroke="{t["line"]}"/>')
    a(f'<circle cx="{rx-152}" cy="48" r="4" fill="{t["accent"]}"/>')
    a(f'<text x="{rx-140}" y="52.5" font-size="13" fill="{t["text"]}">open to SDE roles</text>')
    # legend
    a(f'<circle cx="{rx-150}" cy="86" r="4" fill="{t["accent"]}"/>')
    a(f'<text x="{rx-140}" y="90" font-size="12" fill="{t["muted"]}">live</text>')
    a(f'<circle cx="{rx-86}" cy="86" r="3.5" fill="none" stroke="{t["ring"]}" stroke-width="1.5"/>')
    a(f'<text x="{rx-76}" y="90" font-size="12" fill="{t["muted"]}">code only</text>')

    # release brackets
    for s, e, v, desc in RELEASES:
        cur = v == "v3"
        col = t["accent"] if cur else t["ring"]
        xs, xe = x_of(s) - 8, x_of(e) + 8
        a(f'<text x="{xs}" y="196" font-size="13" font-weight="500" fill="{t["text"] if cur else t["text2"]}">{v}{" · now" if cur else ""}</text>')
        a(f'<text x="{xs}" y="212" font-size="11" fill="{t["muted"]}">{desc}</text>')
        a(f'<path d="M{xs} 226 V220 H{xe} V226" fill="none" stroke="{col}" stroke-width="1"/>')

    # axis: solid where work happened, dashed through the quiet months
    a(f'<line x1="{X0-8}" y1="{AXIS_Y+12}" x2="{X1+8}" y2="{AXIS_Y+12}" stroke="{t["line"]}" stroke-width="1"/>')
    a(f'<line x1="{x_of(7)}" y1="{AXIS_Y+12}" x2="{x_of(11)}" y2="{AXIS_Y+12}" stroke="{t["card"]}" stroke-width="2"/>')
    a(f'<line x1="{x_of(7)}" y1="{AXIS_Y+12}" x2="{x_of(11)}" y2="{AXIS_Y+12}" stroke="{t["ring"]}" stroke-width="1" stroke-dasharray="2 4"/>')
    for m, lab in [(0, "Jan 25"), (3, "Apr"), (6, "Jul"), (9, "Oct"), (12, "Jan 26"), (15, "Apr"), (18, "Jul"), (21, "Oct")]:
        x = x_of(m)
        a(f'<line x1="{x}" y1="{AXIS_Y+8}" x2="{x}" y2="{AXIS_Y+16}" stroke="{t["ring"]}" stroke-width="1"/>')
        a(f'<text x="{x}" y="{AXIS_Y+36}" font-size="11" text-anchor="middle" fill="{t["muted"]}">{lab}</text>')
    a(f'<text x="{x_of(22)}" y="{AXIS_Y+36}" font-size="11" text-anchor="middle" fill="{t["accent"]}">now</text>')

    # dots, stacked per month
    seen: dict[int, int] = {}
    for m, name, live in sorted(REPOS, key=lambda r: (r[0], -r[2])):  # live dots sit on the axis
        k = seen.get(m, 0); seen[m] = k + 1
        x, y = x_of(m), AXIS_Y - k * STEP
        assert X0 - 1 <= x <= X1 + 1 and y > 230, (name, x, y)  # self-check: inside plot, below brackets
        if live:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="4.5" fill="{t["accent"]}"><title>{name}</title></circle>')
        else:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="none" stroke="{t["ring"]}" stroke-width="1.5"><title>{name}</title></circle>')
    a("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    reg, med = font_b64("JetBrainsMono-Regular.ttf"), font_b64("JetBrainsMono-Medium.ttf")
    assert len(REPOS) == 26
    for name, t in THEMES.items():
        p = OUT / f"changelog-{name}.svg"
        p.write_text(card(t, reg, med))
        print(p, p.stat().st_size)
