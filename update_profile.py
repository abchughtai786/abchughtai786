"""Builds the terminal-style profile card (dark_mode.svg and light_mode.svg).

Edit the PROFILE section below, then run:  python update_profile.py
GitHub Actions runs it every day so the stats stay current.
"""
import colorsys
import datetime as dt
import json
import os
import time
import urllib.request
from html import escape

USER = "abchughtai786"

# ---------------------------------------------------------------- PROFILE
BIRTHDAY = None  # e.g. dt.date(2000, 1, 31) to show your age as "Uptime"

SECTIONS = [
    [
        ("OS", "Linux (Ubuntu), Windows"),
        ("Uptime", "{uptime}"),
        ("Host", "Pintern (co-founder)"),
        ("Kernel", "Aspiring AI Developer"),
        ("IDE", "VS Code, Android Studio, Claude Code"),
    ],
    [
        ("Languages.Programming", "Python, JavaScript, Dart, SQL"),
        ("Languages.Real", "English, Urdu"),
        ("Hobbies", "Home automation, self-hosting"),
    ],
    [
        ("Projects", "AI pipeline, Flutter app, IoT, monitoring"),
        ("Homelab", "Docker, Home Assistant, Grafana, MQTT"),
    ],
    "Contact",
    [
        ("Email", "Ahsanchughtai.work@gmail.com"),
        ("LinkedIn", "in/ahsan-chughtai"),
        ("GitHub", f"github.com/{USER}"),
    ],
    "GitHub Stats",
    [
        ("Repos", "{repos} {{Contributed: {contributed}}} | Stars: {stars}"),
        ("Commits", "{commits} | Followers: {followers}"),
        ("Lines of Code", "{loc} ( {added}++, {removed}-- )"),
    ],
]

WIDTH_CHARS = 58  # width of the info column

# min_l / max_l keep the portrait readable on each background
THEMES = {
    "dark_mode.svg": dict(bg="#161b22", text="#c9d1d9", key="#ffa657",
                          value="#a5d6ff", dots="#616e7f", add="#3fb950",
                          rem="#f85149", min_l=0.45, max_l=1.0, dark=True),
    "light_mode.svg": dict(bg="#f6f8fa", text="#24292f", key="#953800",
                           value="#0a3069", dots="#c2cfde", add="#1a7f37",
                           rem="#cf222e", min_l=0.0, max_l=0.55, dark=False),
}

# ------------------------------------------------------------------ STATS


def api(path, tries=6):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    for _ in range(tries):
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 202:  # GitHub is still computing the statistics
                time.sleep(5)
                continue
            return json.load(resp)
    return None


def stats():
    user = api(f"/users/{USER}")
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
    contributed = api(f"/search/issues?q=type:pr+author:{USER}+-user:{USER}+is:merged&per_page=1")
    added = removed = 0
    for repo in repos:
        for c in api(f"/repos/{repo['full_name']}/stats/contributors") or []:
            if c.get("author") and c["author"]["login"].lower() == USER.lower():
                added += sum(w["a"] for w in c["weeks"])
                removed += sum(w["d"] for w in c["weeks"])
    return {
        "repos": len(repos),
        "contributed": contributed["total_count"] if contributed else 0,
        "stars": sum(r["stargazers_count"] for r in repos),
        "commits": commits,
        "followers": user["followers"],
        "loc": f"{added - removed:,}",
        "added": f"{added:,}",
        "removed": f"{removed:,}",
    }


def uptime():
    if not BIRTHDAY:
        return "Always learning, always building"
    today = dt.date.today()
    years = today.year - BIRTHDAY.year - ((today.month, today.day) < (BIRTHDAY.month, BIRTHDAY.day))
    last = BIRTHDAY.replace(year=BIRTHDAY.year + years)
    months = (today.year - last.year) * 12 + today.month - last.month - (today.day < last.day)
    days = (today - (last.replace(year=last.year + (last.month + months - 1) // 12,
                                  month=(last.month + months - 1) % 12 + 1))).days
    return f"{years} years, {months} months, {days} days"

# -------------------------------------------------------------------- SVG


def info_lines(values):
    lines = [[("key", f"{USER}"), ("text", "@github "), ("dots", "—" * (WIDTH_CHARS - len(USER) - 8))]]
    for section in SECTIONS:
        if isinstance(section, str):
            lines.append([])
            lines.append([("text", "— " + section + " "), ("dots", "—" * (WIDTH_CHARS - len(section) - 3))])
            continue
        if lines[-1] and not lines[-1][0][1].startswith("— "):
            lines.append([])
        for key, value in section:
            value = value.format(**values)
            fill = WIDTH_CHARS - len(key) - len(value) - 4
            parts = [("text", ". "), ("key", key), ("text", ": "), ("dots", "." * max(fill, 1) + " ")]
            if "++" in value:  # colour the added/removed numbers
                head, rest = value.split("(", 1)
                plus, minus = rest.rsplit(", ", 1)
                parts += [("value", head + "( "), ("add", plus.strip()), ("value", ", "),
                          ("rem", minus.replace(")", "").strip()), ("value", " )")]
            else:
                parts.append(("value", value))
            lines.append(parts)
    return lines


def art_colour(hex_colour, theme):
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(max(l, theme["min_l"]), theme["max_l"])
    return "#%02x%02x%02x" % tuple(round(v * 15) * 17 for v in colorsys.hls_to_rgb(h, l, min(1, s * 1.1)))


def art_line(row, theme):
    """One row of the portrait, joining neighbouring characters of the same colour."""
    out, run, colour = [], "", None
    for cell in row + [[" ", " ", None]]:
        char, raw = cell[0 if theme["dark"] else 1], cell[2]
        new = art_colour(raw, theme) if raw else None
        if new != colour and run:
            out.append(f'<tspan fill="{colour}">{escape(run)}</tspan>' if colour else escape(run))
            run = ""
        colour = new
        run += char
    return "".join(out).rstrip()


def svg(theme, art, lines):
    c = THEMES[theme]
    line_h, char_w = 20, 9.6
    art_line_h, art_char_w = 10, 4.8  # the portrait uses a smaller font for more detail
    art_w = len(art[0]) * art_char_w
    rows = max(len(art) * art_line_h // line_h + 1, len(lines))
    width = int(30 + art_w + 30 + WIDTH_CHARS * char_w + 30)
    height = rows * line_h + 50
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" '
           f'width="{width}px" height="{height}px" font-size="16px">',
           "<style>.key{fill:%s}.value{fill:%s}.dots{fill:%s}.add{fill:%s}.rem{fill:%s}</style>"
           % (c["key"], c["value"], c["dots"], c["add"], c["rem"]),
           f'<rect width="{width}px" height="{height}px" fill="{c["bg"]}" rx="15"/>',
           '<text x="30" y="30" font-size="8px" font-weight="bold" xml:space="preserve">']
    for i, row in enumerate(art):
        out.append(f'<tspan x="30" y="{30 + i * art_line_h}">{art_line(row, c)}</tspan>')
    out.append("</text>")
    x = 30 + art_w + 30
    out.append(f'<text x="{x:.0f}" y="35" fill="{c["text"]}" xml:space="preserve">')
    for i, parts in enumerate(lines):
        spans = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' if cls != "text" else escape(t)
                        for cls, t in parts)
        out.append(f'<tspan x="{x:.0f}" y="{35 + i * line_h}">{spans}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out) + "\n"


def main():
    with open(os.path.join(os.path.dirname(__file__) or ".", "ascii.json")) as f:
        art = json.load(f)
    cache = os.path.join(os.path.dirname(__file__) or ".", "stats.json")
    try:
        values = stats()
        with open(cache, "w") as f:
            json.dump(values, f, indent=2)
    except Exception as err:  # e.g. API rate limit: keep the last known numbers
        print("Could not fetch stats, using the last saved ones:", err)
        with open(cache) as f:
            values = json.load(f)
    values["uptime"] = uptime()
    lines = info_lines(values)
    # centre the info block next to the art
    pad = max(0, (len(art) * 10 // 20 - len(lines)) // 2)
    lines = [[]] * pad + lines
    for name in THEMES:
        with open(name, "w") as f:
            f.write(svg(name, art, lines))
    print(json.dumps(values))


if __name__ == "__main__":
    main()
