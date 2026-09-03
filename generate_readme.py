#!/usr/bin/env python3
"""
Builds the GitHub profile README: ASCII portrait on the left, neofetch-style
info block on the right.

    python generate_readme.py            # writes README.md
    python generate_readme.py --stdout   # print instead of writing

LAYOUT = "image" puts the two in an HTML table, the portrait as a scaled-down
PNG. That is the only arrangement that fits side by side without horizontal
scroll: in a plain code block both columns share one line, and GitHub starts
scrolling past ~105 characters, which is not enough for a legible portrait
plus this much text. In a table the columns size independently.

Regenerate the PNGs with render_art.py whenever portrait.txt changes.

Live fields (uptime, repo/star/follower counts) are recomputed on every run,
so pair this with the GitHub Action in .github/workflows/readme.yml.
"""

import argparse
import datetime
import html
import json
import os
import pathlib
import textwrap
import urllib.request

# ---------------------------------------------------------------- config ----

USERNAME = "i4mGr0ot"
HANDLE = "ashray@github"
BIRTHDAY = "2005-11-16"

ART_FILE = "portrait.txt"
ART_PNG = "portrait-light.png"  # one image, used in every colour scheme
ART_DISPLAY_WIDTH = 360     # px in the README; raise it and lower VALUE_WRAP

LAYOUT = "image"            # "image" | "side" | "stacked"
GAP = 3                     # spaces between columns, "side" layout only
LEADER_WIDTH = 20           # column where the dotted leader ends
VALUE_WRAP = 36             # wrap long values; keeps the text column narrow
RULE = 40                   # length of the header/section rules

# (label, value); ("---", "Section") = rule, ("", "") = blank line
ROWS = [
    ("OS", "Windows 11, Ubuntu 22.04 (WSL2)"),
    ("Uptime", "{uptime}"),
    ("Host", "Institute of Aerospace Systems, RWTH Aachen, Aachen DE"),
    ("Kernel", "B.E. Mech. Eng., BITS Pilani"),
    ("Shell", "Project ATLAS - ILR"),
    ("IDE", "VSCode, MATLAB, Vim, Arduino, Raspberry Pi"),
    ("", ""),
    ("Lang.Programming", "Python, C++, C, MATLAB"),
    ("Lang.Markup", "LaTeX, YAML, JSON, Bash"),
    ("Lang.Real", "English, Hindi, German"),
    ("", ""),
    ("Stack.Simulation", "OpenFOAM, SU2, XFOIL, UNICADO, ANSYS, "
                         "FlexCompute, COMSOL, SimScale"),
    ("Stack.Robotics", "ROS2, PX4, STM32, Embedded C"),
    ("Stack.Learning", "PyTorch, scikit-learn, Optuna, TensorFlow"),
    ("", ""),
    ("Focus.Thesis", "Credibility estimation for 2045 EIS aircraft "
                     "using evidence theory"),
    ("Focus.Research", "CUAS, autonomy, robotics, aeroacoustics, MDO, "
                       "VIO, combustion, gas turbine engines"),
    ("Focus.Papers", "NN airfoil optimisation for wing design, "
                     "thermoacoustics, F1 lap-time OC"),
    ("Focus.Building", "GNSS-denied positioning"),
    ("", ""),
    ("---", "Contact"),
    ("Email.Personal", "aashraysaxena@gmail.com"),
    ("Email.Academic", "ashray.saxena@rwth-aachen.de"),
    ("LinkedIn", "in/ashraysaxena"),
    ("ORCiD", "0009-0001-8570-9160"),
    ("", ""),
    ("---", "GitHub Stats"),
    ("Repos", "{repos}   |   Stars: {stars}"),
    ("Followers", "{followers}   |   Following: {following}"),
    ("Pinned", "Airfoil-Opt, F1-Aero-ERS, Acoustics"),
]

# label -> href, applied in the "image" layout only
LINKS = {
    "Email.Personal": "mailto:aashraysaxena@gmail.com",
    "Email.Academic": "mailto:ashray.saxena@rwth-aachen.de",
    "LinkedIn": "https://www.linkedin.com/in/ashraysaxena/",
    "ORCiD": "https://orcid.org/0009-0001-8570-9160",
}

# ------------------------------------------------------------- live data ----


def uptime(birthday: str) -> str:
    b = datetime.date.fromisoformat(birthday)
    t = datetime.date.today()
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    anniversary = datetime.date(
        t.year - (1 if (t.month, t.day) < (b.month, b.day) else 0), b.month, b.day)
    days = (t - anniversary).days
    months, days = days // 30, days % 30
    return f"{years} years, {months} months, {days} days"


def _get(url, token):
    req = urllib.request.Request(url, headers={"User-Agent": "readme-generator"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def github_stats(user: str) -> dict:
    """Best-effort. Falls back to placeholders when the API is unreachable."""
    fallback = {"repos": "11", "stars": "0", "followers": "1", "following": "0"}
    try:
        token = os.environ.get("GITHUB_TOKEN")
        u = _get(f"https://api.github.com/users/{user}", token)
        stars, page = 0, 1
        while True:
            batch = _get(
                f"https://api.github.com/users/{user}/repos?per_page=100&page={page}",
                token)
            if not batch:
                break
            stars += sum(x.get("stargazers_count", 0) for x in batch)
            if len(batch) < 100:
                break
            page += 1
        return {
            "repos": str(u.get("public_repos", fallback["repos"])),
            "stars": str(stars),
            "followers": str(u.get("followers", fallback["followers"])),
            "following": str(u.get("following", fallback["following"])),
        }
    except Exception:
        return fallback


# ---------------------------------------------------------------- layout ----


def info_lines(ctx, linkify=False):
    """Returns the info block. Long values wrap with a hanging indent so the
    text column stays narrow enough to sit beside the portrait."""
    # each entry: (text, href, head_len, bold_span) where bold_span is the
    # (start, end) slice of the line to embolden, or None
    out = [(f"{HANDLE} " + "-" * RULE, None, 0, (0, len(HANDLE)))]
    for label, value in ROWS:
        if not label and not value:
            out.append(("", None, 0, None))
        elif label == "---":
            out.append((f"- {value} " + "-" * max(0, RULE - len(value)),
                        None, 0, (2, 2 + len(value))))
        else:
            value = value.format(**ctx)
            dots = "." * max(1, LEADER_WIDTH - len(label) - 2)
            head = f"- {label}: {dots} "
            chunks = textwrap.wrap(value, VALUE_WRAP) or [""]
            href = LINKS.get(label) if linkify else None
            for i, chunk in enumerate(chunks):
                prefix = head if i == 0 else " " * len(head)
                bold = (2, 2 + len(label) + 1) if i == 0 else None
                out.append((prefix + chunk, href, len(head), bold))
    return out


def _pre_block(lines):
    body = []
    for text, href, head_len, bold in lines:
        if not text.strip():
            # A truly blank line would close the surrounding HTML block and
            # hand the rest of the table back to the Markdown parser, which
            # turns "- Label: ..." into bullet points. &nbsp; keeps the line
            # visually empty while stopping that.
            body.append("&nbsp;")
            continue
        parts, i = [], 0
        if bold:
            bs, be = bold
            parts.append(html.escape(text[:bs]))
            parts.append(f"<b>{html.escape(text[bs:be])}</b>")
            i = be
        if href and len(text) > head_len:
            parts.append(html.escape(text[i:head_len]))
            parts.append(f'<a href="{href}">{html.escape(text[head_len:])}</a>')
        else:
            parts.append(html.escape(text[i:]))
        body.append("".join(parts))
    return "\n".join(body)


def build() -> str:
    here = pathlib.Path(__file__).parent
    art = (here / ART_FILE).read_text(encoding="utf-8").split("\n")
    while art and not art[-1].strip():
        art.pop()

    ctx = {"uptime": uptime(BIRTHDAY), **github_stats(USERNAME)}
    header = ("<!-- Generated by generate_readme.py. Do not hand-edit; change "
              "ROWS in that file and re-run. -->\n\n")

    if LAYOUT == "image":
        pre = _pre_block(info_lines(ctx, linkify=True))
        return header + (
            '<table>\n<tr>\n'
            f'<td valign="top" align="center">\n'
            f'<img src="{ART_PNG}" alt="ASCII portrait"'
            f' width="{ART_DISPLAY_WIDTH}">\n'
            '</td>\n'
            f'<td valign="top">\n<pre>\n{pre}\n</pre>\n</td>\n'
            '</tr>\n</table>\n'
        )

    info = [t for t, _, _, _ in info_lines(ctx)]
    if LAYOUT == "side":
        w = max(len(x) for x in art)
        n = max(len(art), len(info))
        art += [""] * (n - len(art))
        info += [""] * (n - len(info))
        body = "\n".join((a.ljust(w) + " " * GAP + b).rstrip()
                         for a, b in zip(art, info))
    else:
        body = "\n".join(art + [""] + [x.rstrip() for x in info])
    return f"{header}```text\n{body}\n```\n"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stdout", action="store_true")
    a = p.parse_args()
    md = build()
    if a.stdout:
        print(md)
    else:
        pathlib.Path(__file__).with_name("README.md").write_text(md, encoding="utf-8")
        print("wrote README.md")
