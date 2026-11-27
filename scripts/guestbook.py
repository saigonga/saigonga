"""Guestbook: visitors 'sign the release' by opening an issue titled 'sign: v3'.

  sign   — run by .github/workflows/guestbook.yml on a new issue; prints a reply for the bot
  render — rebuild assets/guestbook-{dark,light}.svg from data/guestbook.json
To remove someone: delete their entry from data/guestbook.json, then run the workflow manually.
"""
import base64, datetime as dt, json, os, re, sys, urllib.request
from html import escape
from pathlib import Path
from changelog import THEMES, font_b64

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/guestbook.json"
RELEASE = "v3"
SHOW_AVATARS, SHOW_NOTES, NOTE_MAX = 16, 2, 80
W, H, PAD = 880, 232, 40


def clean_note(body: str | None) -> str:
    """Untrusted text from a stranger: keep one short plain line, no links, mentions or markup."""
    text = (body or "").replace("\r", "")
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)  # template hint comment
    text = re.sub(r"<script.*?</script>|<[^>]*>", " ", text, flags=re.S | re.I)
    line = next((l.strip() for l in text.split("\n") if l.strip()), "")
    line = re.sub(r"^note\s*:\s*", "", line, flags=re.I)
    line = re.sub(r"(https?://|www\.)\S+|\S+\.(com|io|dev|net|org|xyz|app|me)\S*", "", line, flags=re.I)
    line = re.sub(r"@\w[\w-]*", "", line)  # no pings through the bot
    line = re.sub(r"[^A-Za-z0-9 .,!?'():&+\-]", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line[:NOTE_MAX].rstrip()


def load() -> list[dict]:
    return json.loads(DATA.read_text()) if DATA.exists() else []


def sign(event: dict) -> str:
    issue = event["issue"]
    user = issue["user"]
    if not re.match(rf"^\s*sign\s*:?\s*{RELEASE}\b", issue["title"], re.I):
        return ""  # a normal issue, leave it alone
    if user.get("type") != "User":
        return "Only people can sign the release."
    book = load()
    if any(s["login"].lower() == user["login"].lower() for s in book):
        return f"You already signed {RELEASE}, thank you. One signature per person."
    book.append({"login": user["login"], "note": clean_note(issue.get("body")),
                 "at": dt.date.today().isoformat()})
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(book, indent=2) + "\n")
    return (f"Thanks for signing {RELEASE}. You're #{len(book)} to sign. "
            f"Your avatar shows up on github.com/saigonga within a minute.")


def avatar_b64(login: str) -> str:
    url = f"https://avatars.githubusercontent.com/{login}?s=80"
    with urllib.request.urlopen(url, timeout=20) as r:
        kind = r.headers.get("Content-Type", "")
        assert kind.startswith("image/"), kind
        return f"data:{kind};base64,{base64.b64encode(r.read()).decode()}"


def card(t: dict, book: list[dict], avatars: dict, reg: str, med: str) -> str:
    n = len(book)
    rx = W - PAD
    head = f"Signed by {n} {'person' if n == 1 else 'people'}" if n else "No signatures yet"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Guestbook for release {RELEASE}. {escape(head)}. Click to sign.">',
         f"""<style>
@font-face{{font-family:J;font-weight:400;src:url(data:font/woff2;base64,{reg}) format('woff2')}}
@font-face{{font-family:J;font-weight:500;src:url(data:font/woff2;base64,{med}) format('woff2')}}
text{{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace}}
</style>""",
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}"/>',
         f'<text x="{PAD}" y="52" font-size="13" fill="{t["muted"]}">guestbook · release {RELEASE}</text>',
         f'<text x="{PAD}" y="84" font-size="22" font-weight="500" fill="{t["text"]}">{head}</text>',
         # the whole card is the link, this is its visible label
         f'<rect x="{rx-128}" y="34" width="128" height="32" rx="8" fill="none" stroke="{t["accent"]}"/>',
         f'<text x="{rx-64}" y="54.5" font-size="13" text-anchor="middle" fill="{t["accent"]}">Sign {RELEASE} →</text>']
    y, r, step = 128, 16, 40
    recent = book[::-1][:SHOW_AVATARS]
    for i in range(SHOW_AVATARS if not n else len(recent)):
        cx = PAD + r + i * step
        if i < len(recent):
            login = recent[i]["login"]
            o.append(f'<clipPath id="a{i}"><circle cx="{cx}" cy="{y}" r="{r}"/></clipPath>')
            o.append(f'<image clip-path="url(#a{i})" x="{cx-r}" y="{y-r}" width="{2*r}" height="{2*r}" href="{avatars[login]}"><title>{escape(login)}</title></image>')
            o.append(f'<circle cx="{cx}" cy="{y}" r="{r-.5}" fill="none" stroke="{t["line"]}"/>')
        else:  # empty state: open seats
            o.append(f'<circle cx="{cx}" cy="{y}" r="{r-1}" fill="none" stroke="{t["ring"]}" stroke-dasharray="3 4" opacity=".7"/>')
    if n > SHOW_AVATARS:
        o.append(f'<text x="{PAD + SHOW_AVATARS*step + 4}" y="{y+5}" font-size="13" fill="{t["muted"]}">+{n-SHOW_AVATARS}</text>')
    notes = [s for s in book[::-1] if s["note"]][:SHOW_NOTES]
    if not n:
        o.append(f'<text x="{PAD}" y="{y+52}" font-size="13" fill="{t["text2"]}">Be the first. Leave a one-line note and your avatar lands here</text>')
    for i, s in enumerate(notes):
        ny = y + 52 + i * 22
        o.append(f'<text x="{PAD}" y="{ny}" font-size="13"><tspan fill="{t["muted"]}">{escape(s["login"][:24])}</tspan>'
                 f'<tspan fill="{t["text2"]}" dx="12">{escape(s["note"][:60])}</tspan></text>')
    o.append("</svg>")
    return "\n".join(o)


def render():
    book = load()
    avatars = {s["login"]: avatar_b64(s["login"]) for s in book[::-1][:SHOW_AVATARS]}
    chars = "".join(chr(c) for c in range(32, 127)) + "·→"
    reg, med = font_b64("JetBrainsMono-Regular.ttf", chars), font_b64("JetBrainsMono-Medium.ttf", chars)
    for name, t in THEMES.items():
        p = ROOT / f"assets/guestbook-{name}.svg"
        p.write_text(card(t, book, avatars, reg, med))
        print(p.name, p.stat().st_size, f"{len(book)} signatures")


if __name__ == "__main__":
    if sys.argv[1] == "sign":
        reply = sign(json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text()))
        Path(os.environ.get("REPLY_FILE", "reply.txt")).write_text(reply)
        print(reply or "not a signature")
    else:
        render()
