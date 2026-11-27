"""Rebuild assets/changelog-{dark,light}.svg from live GitHub data.

Runs daily in .github/workflows/changelog.yml. Locally:
  GITHUB_TOKEN=$(gh auth token) uv run --no-project --with 'fonttools[woff]' scripts/changelog.py
"""
import base64, datetime as dt, glob, io, json, os, urllib.request
from collections import Counter
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

USER = "saigonga"
OUT = Path(__file__).resolve().parent.parent / "assets"
START = dt.date(2025, 1, 1)
# editorial: (first month index, label, description); the last release runs to today
RELEASES = [(0, 2, "v0", "html + css"), (4, 6, "v1", "react apps"),
            (12, 15, "v2", "backend + data"), (17, None, "v3", "client work at TBM")]
# private client repos the Action token cannot see: (created, name, live)
PRIVATE = [("2026-06-22", "SOV-Dashboard-for-TBM", True), ("2026-07-30", "INSTAGRAMTBM", True),
           ("2026-08-31", "Final-SOV-plannel-", False), ("2026-11-23", "TBMPortfolio", True)]
FONT_DIRS =[str(Path.home() / "Library/Fonts"), "fonts",
             "/usr/share/fonts/**"]

THEMES = {
    "dark": dict(card="#12161c", line="rgba(230,237,243,0.09)", bar="rgba(230,237,243,0.11)",
                 text="#e6e8eb", text2="#9aa3ad", muted="#6b7480", accent="#3fb950", ring="#4a525c"),
    "light": dict(card="#f8f9fa", line="rgba(31,35,40,0.10)", bar="rgba(31,35,40,0.09)",
                  text="#1f2328", text2="#4b535d", muted="#6e7781", accent="#1a7f37", ring="#b6bcc3"),
}
W, H, PAD = 880, 412, 40
X0, X1, AXIS_Y, STEP, BAR_MAX = 56, W - 56, 316, 14, 96


def api(url: str, body: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def month_idx(iso: str) -> int:
    d = dt.date.fromisoformat(iso[:10])
    return max(0, (d.year - START.year) * 12 + d.month - 1)  # older repos count from Jan 2025


def fetch(today: dt.date):
    repos = [r for r in api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"] != USER]
    seen = {r["name"] for r in repos}
    dots = [(month_idx(r["created_at"]), r["name"], bool(r["homepage"])) for r in repos]
    dots += [(month_idx(c), n, live) for c, n, live in PRIVATE if n not in seen]
    dots.sort(key=lambda r: (r[0], -r[2]))  # live dots sit on the axis
    commits: Counter = Counter()
    for y in range(START.year, today.year + 1):
        q = ('query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t)'
             '{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}')
        data = api("https://api.github.com/graphql", {"query": q, "variables": {
            "u": USER, "f": f"{y}-01-01T00:00:00Z", "t": f"{y}-12-31T23:59:59Z"}})
        for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                if d["date"] >= START.isoformat():
                    commits[month_idx(d["date"])] += d["contributionCount"]
    latest = max(repos, key=lambda r: r["pushed_at"])["name"]
    return dots, commits, latest


def font_b64(name: str, chars: str) -> str:
    path = next(p for d in FONT_DIRS for p in glob.glob(f"{d}/{name}", recursive=True))
    f = TTFont(path)
    opts = subset.Options(); opts.flavor = "woff2"
    s = subset.Subsetter(opts); s.populate(text=chars); s.subset(f)
    buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def card(t, dots, commits, months, latest, total, reg, med) -> str:
    def x_of(m): return X0 + m * (X1 - X0) / (months - 1)
    rx = W - PAD
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Sai Gonga, full-stack developer. {len(dots)} repos and {total} contributions since January 2025.">',
         f"""<style>
@font-face{{font-family:J;font-weight:400;src:url(data:font/woff2;base64,{reg}) format('woff2')}}
@font-face{{font-family:J;font-weight:500;src:url(data:font/woff2;base64,{med}) format('woff2')}}
text{{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}}
.p{{animation:p 2.4s cubic-bezier(.2,.7,.2,1) infinite;transform-origin:{rx-152}px 48px}}
@keyframes p{{0%{{opacity:.5;transform:scale(1)}}70%,100%{{opacity:0;transform:scale(2.6)}}}}
@media (prefers-reduced-motion:reduce){{.p{{animation:none;opacity:0}}}}
</style>""",
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}"/>',
         f'<text x="{PAD}" y="52" font-size="13" fill="{t["muted"]}">{USER} · changelog</text>',
         f'<text x="{PAD}" y="100" font-size="40" font-weight="500" letter-spacing="-1" fill="{t["text"]}">Sai Gonga</text>',
         f'<text x="{PAD}" y="132" font-size="15" fill="{t["text2"]}">Full-stack developer. Dashboards, scrapers and APIs, shipped live</text>',
         f'<text x="{PAD}" y="156" font-size="13" fill="{t["muted"]}">Mumbai · Class of 2026 · Full-stack at TBM</text>',
         # live status: the only motion, because it is live
         f'<rect x="{rx-168}" y="34" width="168" height="28" rx="8" fill="none" stroke="{t["line"]}"/>',
         f'<circle class="p" cx="{rx-152}" cy="48" r="4" fill="{t["accent"]}"/>',
         f'<circle cx="{rx-152}" cy="48" r="4" fill="{t["accent"]}"/>',
         f'<text x="{rx-140}" y="52.5" font-size="13" fill="{t["text"]}">open to SDE roles</text>',
         f'<text x="{rx}" y="90" font-size="13" text-anchor="end" fill="{t["text2"]}">{len(dots)} repos · {total:,} contributions</text>',
         f'<text x="{rx}" y="110" font-size="12" text-anchor="end" fill="{t["muted"]}">since January 2025</text>']
    a = o.append

    for s, e, v, desc in RELEASES:
        e = months - 1 if e is None else e
        cur = v == RELEASES[-1][2]
        xs, xe = x_of(s) - 8, x_of(e) + 8
        a(f'<text x="{xs}" y="196" font-size="13" font-weight="500" fill="{t["text"] if cur else t["text2"]}">{v}{" · now" if cur else ""}</text>')
        a(f'<text x="{xs}" y="212" font-size="11" fill="{t["muted"]}">{desc}</text>')
        a(f'<path d="M{xs} 226 V220 H{xe} V226" fill="none" stroke="{t["accent"] if cur else t["ring"]}" stroke-width="1"/>')

    base = AXIS_Y + 12
    peak = max(commits.values() or [1])
    for m in range(months):  # contributions per month, behind the dots
        h = round(commits.get(m, 0) / peak * BAR_MAX)
        if h:
            a(f'<rect x="{x_of(m)-10:.1f}" y="{base-h}" width="20" height="{h}" rx="3" fill="{t["bar"]}"><title>{commits[m]} contributions</title></rect>')
    a(f'<line x1="{X0-8}" y1="{base}" x2="{X1+8}" y2="{base}" stroke="{t["line"]}"/>')
    labels = {m: ("Jan " + str(START.year + m // 12)[2:] if m % 12 == 0 else ["Apr", "Jul", "Oct"][m % 12 // 3 - 1])
              for m in range(0, months - 1, 3)}
    for m, lab in labels.items():
        a(f'<line x1="{x_of(m)}" y1="{base-4}" x2="{x_of(m)}" y2="{base+4}" stroke="{t["ring"]}"/>')
        a(f'<text x="{x_of(m)}" y="{base+24}" font-size="11" text-anchor="middle" fill="{t["muted"]}">{lab}</text>')
    a(f'<text x="{x_of(months-1)}" y="{base+24}" font-size="11" text-anchor="middle" fill="{t["accent"]}">now</text>')

    seen: Counter = Counter()
    for m, name, live in dots:
        x, y = x_of(m), AXIS_Y - seen[m] * STEP
        seen[m] += 1
        assert X0 - 1 <= x <= X1 + 1 and y > 230, (name, x, y)  # inside plot, below brackets
        if live:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="4.5" fill="{t["accent"]}"><title>{name}</title></circle>')
        else:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="none" stroke="{t["ring"]}" stroke-width="1.5"><title>{name}</title></circle>')

    # legend + freshness
    ly = H - 30
    a(f'<circle cx="{PAD+4}" cy="{ly-4}" r="4" fill="{t["accent"]}"/><text x="{PAD+14}" y="{ly}" font-size="11" fill="{t["muted"]}">live repo</text>')
    a(f'<circle cx="{PAD+102}" cy="{ly-4}" r="3.5" fill="none" stroke="{t["ring"]}" stroke-width="1.5"/><text x="{PAD+112}" y="{ly}" font-size="11" fill="{t["muted"]}">code only</text>')
    a(f'<rect x="{PAD+196}" y="{ly-10}" width="10" height="12" rx="2" fill="{t["ring"]}" opacity=".5"/><text x="{PAD+214}" y="{ly}" font-size="11" fill="{t["muted"]}">contributions per month</text>')
    a(f'<text x="{rx}" y="{ly}" font-size="11" text-anchor="end" fill="{t["muted"]}">latest push · {latest}</text>')
    a("</svg>")
    return "\n".join(o)


def main():
    today = dt.date.today()
    months = month_idx(today.isoformat()) + 1
    dots, commits, latest = fetch(today)
    total = sum(commits.values())
    chars = "".join(chr(c) for c in range(32, 127)) + "·×→"
    reg = font_b64("JetBrainsMono-Regular.ttf", chars)
    med = font_b64("JetBrainsMono-Medium.ttf", chars)
    for name, t in THEMES.items():
        p = OUT / f"changelog-{name}.svg"
        p.write_text(card(t, dots, commits, months, latest, total, reg, med))
        print(p.name, p.stat().st_size, f"{len(dots)} repos, {total} contributions")


if __name__ == "__main__":
    main()
