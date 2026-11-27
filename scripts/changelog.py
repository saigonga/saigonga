"""Rebuild assets/changelog-{wide,narrow}-{dark,light}.svg from live GitHub data.

Runs daily in .github/workflows/changelog.yml. Locally:
  GITHUB_TOKEN=$(gh auth token) uv run --no-project --with 'fonttools[woff]' scripts/changelog.py
"""
import datetime as dt, json, os, urllib.request
from collections import Counter
from pathlib import Path
from design import THEMES, SIZES, style, wrap

USER = "saigonga"
OUT = Path(__file__).resolve().parent.parent / "assets"
START = dt.date(2025, 1, 1)
# editorial: (first month, last month, version, description); the last release runs to today
RELEASES = [(0, 2, "v0", "html + css"), (4, 6, "v1", "react apps"),
            (12, 15, "v2", "backend + data"), (17, None, "v3", "client work")]
# private client repos the Action token cannot see: (created, display name, live).
# Display names are generic on purpose: the client is not named on the profile.
PRIVATE = [("2026-06-22", "sov-dashboard", True), ("2026-07-30", "creator-search", True),
           ("2026-08-31", "sov-planner", False), ("2026-11-23", "case-study-site", True)]
SENTENCE = "I build dashboards, scrapers and APIs, and ship them live"

# per-size layout (DESIGN.md: wide 880, narrow 440)
L = {
    "wide": dict(pad=40, label=13, name=72, name_y=128, sent=26, sent_y=172, meta=13, meta_y=210,
                 x_in=56, brk_y=272, desc=True, axis=400, step=14, r=4.5, bar_max=96,
                 month_every=3, legend_gap=30),
    "narrow": dict(pad=24, label=12, name=52, name_y=108, sent=20, sent_y=146, meta=12, meta_y=210,
                   x_in=40, brk_y=272, desc=False, axis=372, step=12, r=3.5, bar_max=72,
                   month_every=6, legend_gap=44),
}


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


def card(t, size, dots, commits, months, latest, total) -> str:
    W, c = SIZES[size], L[size]
    P, rx = c["pad"], SIZES[size] - c["pad"]
    X0, X1, AX = c["x_in"], W - c["x_in"], c["axis"]
    base = AX + 12
    H = base + 24 + c["legend_gap"] + 40

    def x_of(m): return X0 + m * (X1 - X0) / (months - 1)
    dot_x = rx - 152
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Sai Gonga, full-stack developer. {len(dots)} repos and {total} contributions since January 2025.">',
         style(f".p{{animation:p 2.4s cubic-bezier(.2,.7,.2,1) infinite;transform-origin:{dot_x}px {P+14}px}}"
               "@keyframes p{0%{opacity:.5;transform:scale(1)}70%,100%{opacity:0;transform:scale(2.6)}}"
               "@media (prefers-reduced-motion:reduce){.p{animation:none;opacity:0}}"),
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}"/>',
         f'<text x="{P}" y="{P+18}" font-size="{c["label"]}" fill="{t["muted"]}">{USER} · changelog</text>',
         # live status: the only motion, because it is live
         f'<rect x="{rx-168}" y="{P}" width="168" height="28" rx="8" fill="none" stroke="{t["line"]}"/>',
         f'<circle class="p" cx="{dot_x}" cy="{P+14}" r="4" fill="{t["accent"]}"/>',
         f'<circle cx="{dot_x}" cy="{P+14}" r="4" fill="{t["accent"]}"/>',
         f'<text x="{rx-140}" y="{P+18.5}" font-size="13" fill="{t["text"]}">open to SDE roles</text>',
         f'<text class="s" x="{P-3}" y="{c["name_y"]}" font-size="{c["name"]}" letter-spacing="-1" fill="{t["text"]}">Sai Gonga</text>']
    a = o.append
    # serif sentence: ~0.42em per glyph
    for i, line in enumerate(wrap(SENTENCE, c["sent"] * 0.7, W - 2 * P)):
        a(f'<text class="s" x="{P}" y="{c["sent_y"] + i * c["sent"] * 1.25}" font-size="{c["sent"]}" fill="{t["text2"]}">{line}</text>')
    meta = ["Mumbai · Class of 2026 · Full-stack developer", f"{len(dots)} repos · {total:,} contributions since Jan 2025"]
    if size == "wide":
        meta = [" · ".join(meta)]
    for i, line in enumerate(meta):
        a(f'<text x="{P}" y="{c["meta_y"] + i*20}" font-size="{c["meta"]}" fill="{t["muted"]}">{line}</text>')

    by = c["brk_y"]
    for s, e, v, desc in RELEASES:
        e = months - 1 if e is None else e
        cur = v == RELEASES[-1][2]
        xs, xe = x_of(s) - 8, x_of(e) + 8
        a(f'<text x="{xs}" y="{by}" font-size="13" font-weight="500" fill="{t["text"] if cur else t["text2"]}">{v}{" · now" if cur else ""}</text>')
        if c["desc"]:
            a(f'<text x="{xs}" y="{by+16}" font-size="11" fill="{t["muted"]}">{desc}</text>')
        ty = by + (30 if c["desc"] else 14)
        a(f'<path d="M{xs} {ty+6} V{ty} H{xe} V{ty+6}" fill="none" stroke="{t["accent"] if cur else t["ring"]}" stroke-width="1"/>')

    peak = max(commits.values() or [1])
    bw = 20 if size == "wide" else 10
    for m in range(months):  # contributions per month, behind the dots
        h = round(commits.get(m, 0) / peak * c["bar_max"])
        if h:
            a(f'<rect x="{x_of(m)-bw/2:.1f}" y="{base-h}" width="{bw}" height="{h}" rx="2" fill="{t["bar"]}"><title>{commits[m]} contributions</title></rect>')
    a(f'<line x1="{X0-8}" y1="{base}" x2="{X1+8}" y2="{base}" stroke="{t["line"]}"/>')
    for m in range(0, months - 2, c["month_every"]):
        lab = "Jan " + str(START.year + m // 12)[2:] if m % 12 == 0 else ["Apr", "Jul", "Oct"][m % 12 // 3 - 1]
        a(f'<line x1="{x_of(m)}" y1="{base-4}" x2="{x_of(m)}" y2="{base+4}" stroke="{t["ring"]}"/>')
        a(f'<text x="{x_of(m)}" y="{base+24}" font-size="11" text-anchor="middle" fill="{t["muted"]}">{lab}</text>')
    a(f'<text x="{x_of(months-1)}" y="{base+24}" font-size="11" text-anchor="middle" fill="{t["accent"]}">now</text>')

    seen: Counter = Counter()
    for m, name, live in dots:
        x, y = x_of(m), AX - seen[m] * c["step"]
        seen[m] += 1
        assert X0 - 1 <= x <= X1 + 1 and y > ty + 10, (size, name, x, y)  # inside plot, below brackets
        if live:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="{c["r"]}" fill="{t["accent"]}"><title>{name}</title></circle>')
        else:
            a(f'<circle cx="{x:.1f}" cy="{y}" r="{c["r"]-.5}" fill="none" stroke="{t["ring"]}" stroke-width="1.5"><title>{name}</title></circle>')

    ly = base + 24 + c["legend_gap"]
    a(f'<circle cx="{P+4}" cy="{ly-4}" r="4" fill="{t["accent"]}"/><text x="{P+14}" y="{ly}" font-size="11" fill="{t["muted"]}">live repo</text>')
    a(f'<circle cx="{P+102}" cy="{ly-4}" r="3.5" fill="none" stroke="{t["ring"]}" stroke-width="1.5"/><text x="{P+112}" y="{ly}" font-size="11" fill="{t["muted"]}">code only</text>')
    a(f'<rect x="{P+196}" y="{ly-10}" width="8" height="12" rx="2" fill="{t["ring"]}" opacity=".5"/><text x="{P+212}" y="{ly}" font-size="11" fill="{t["muted"]}">contributions</text>')
    if size == "wide":
        a(f'<text x="{rx}" y="{ly}" font-size="11" text-anchor="end" fill="{t["muted"]}">latest push · {latest}</text>')
    else:
        a(f'<text x="{P}" y="{ly+20}" font-size="11" fill="{t["muted"]}">latest push · {latest}</text>')
    a("</svg>")
    return "\n".join(o)


def main():
    today = dt.date.today()
    months = month_idx(today.isoformat()) + 1
    dots, commits, latest = fetch(today)
    total = sum(commits.values())
    for size in SIZES:
        for name, t in THEMES.items():
            p = OUT / f"changelog-{size}-{name}.svg"
            p.write_text(card(t, size, dots, commits, months, latest, total))
            print(p.name, p.stat().st_size, f"{len(dots)} repos, {total} contributions")


if __name__ == "__main__":
    main()
