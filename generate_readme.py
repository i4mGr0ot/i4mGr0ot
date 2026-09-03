#!/usr/bin/env python3
"""
Builds the GitHub profile README: ASCII portrait on the left, neofetch-style
info block on the right, inside one fenced code block.

Usage:
    python generate_readme.py            # writes README.md
    python generate_readme.py --stdout   # print instead of writing

Live fields (uptime, repo/star/follower counts) are recomputed on every run,
so pair this with the GitHub Action in .github/workflows/readme.yml to keep
the block current without touching it by hand.
"""

import argparse
import datetime
import json
import os
import pathlib
import urllib.request

# ---------------------------------------------------------------- config ----

USERNAME = "i4mGr0ot"
HANDLE = "ashray@github"
BIRTHDAY = "2005-11-16"  # TODO: set your real date of birth -> drives "Uptime"

ART_FILE = "portrait.txt"
LAYOUT = "stacked"  # "stacked" = info block under the art; "side" = beside it
GAP = 3             # spaces between the art column and the info column (side layout)
LEADER_WIDTH = 24  # column where the dotted leader ends

# Each entry is (label, value) or one of:
#   ("---", "Section Title")  -> section header rule
#   ("", "")                  -> blank spacer line
ROWS = [
    ("OS", "Windows 11, Ubuntu 22.04 (WSL2)"),
    ("Uptime", "{uptime}"),
    ("Host", "Institute of Aerospace Systems, RWTH Aachen, Aachen DE"),
    ("Kernel", "B.E. Mech. Eng., BITS Pilani"),
    ("Shell", "Project ATLAS - ILR"),
    ("IDE", "VSCode, MATLAB, Vim, Arduino, Raspberry Pi"),
    ("", ""),
    ("Languages.Programming", "Python, C++, C, MATLAB"),
    ("Languages.Markup", "LaTeX, YAML, JSON, Bash"),
    ("Languages.Real", "English, Hindi, German"),
    ("", ""),
    ("Stack.Simulation", "OpenFOAM, SU2, XFOIL, UNICADO, ANSYS, FlexCompute, COMSOL,  SimScale"),
    ("Stack.Robotics", "ROS2, PX4, STM32, Embedded C"),
    ("Stack.Learning", "PyTorch, scikit-learn, Optuna, Tensor Flow"),
    ("", ""),
    ("Focus.Thesis", "Credibility Estimation for 2045 EIS Aircrafts using Evidence Theory"),
    ("Focus.Research", "CUAS, Autonomy, Robotics, Aeroacoustics, MDO, VIO, Combustion, Gas Turbine Engine"),
    ("Focus.Papers", "NN for Airfoil Optimization for Wing Design, Thermoacoustics, F1 lap-time OC"),
    ("Focus.Building", "GNSS-denied positioning"),
    ("", ""),
    ("---", "Contact"),
    ("Email.Personal", "aashraysaxena@gmail.com"),
    ("Email.Academic", "ashray.saxena@rwth-aachen.de"),
    ("LinkedIn", "https://www.linkedin.com/in/ashraysaxena/"),
    ("ORCiD", "0009-0001-8570-9160"),
    ("", ""),
    ("---", "GitHub Stats"),
    ("Repos", "{repos}   |   Stars: {stars}"),
    ("Followers", "{followers}   |   Following: {following}"),
    ("Pinned", "Airfoil-Opt, F1-Aero-ERS, Acoustics"),
]

# ------------------------------------------------------------- live data ----


def uptime(birthday: str) -> str:
    b = datetime.date.fromisoformat(birthday)
    t = datetime.date.today()
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    anniversary = datetime.date(t.year - (1 if (t.month, t.day) < (b.month, b.day) else 0),
                                b.month, b.day)
    days = (t - anniversary).days
    months, days = days // 30, days % 30
    return f"{years} years, {months} months, {days} days"


def github_stats(user: str) -> dict:
    """Best-effort. Falls back to placeholders when the API is unreachable."""
    fallback = {"repos": "11", "stars": "0", "followers": "1", "following": "0"}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{user}",
            headers={"User-Agent": "readme-generator"},
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as r:
            u = json.load(r)

        stars = 0
        page = 1
        while True:
            rr = urllib.request.Request(
                f"https://api.github.com/users/{user}/repos?per_page=100&page={page}",
                headers={"User-Agent": "readme-generator"},
            )
            if token:
                rr.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(rr, timeout=10) as r:
                batch = json.load(r)
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


def info_lines(ctx: dict) -> list:
    out = [f"{HANDLE} " + "-" * 40]
    for label, value in ROWS:
        if label == "" and value == "":
            out.append("")
        elif label == "---":
            out.append(f"- {value} " + "-" * max(0, 40 - len(value)))
        else:
            dots = "." * max(1, LEADER_WIDTH - len(label) - 2)
            out.append(f"- {label}: {dots} {value.format(**ctx)}")
    return out


def build() -> str:
    here = pathlib.Path(__file__).parent
    art = (here / ART_FILE).read_text(encoding="utf-8").split("\n")
    while art and not art[-1].strip():
        art.pop()

    ctx = {"uptime": uptime(BIRTHDAY), **github_stats(USERNAME)}
    info = info_lines(ctx)

    if LAYOUT == "side":
        art_w = max(len(x) for x in art)
        rows = max(len(art), len(info))
        art += [""] * (rows - len(art))
        info += [""] * (rows - len(info))
        body = "\n".join(
            (a.ljust(art_w) + " " * GAP + b).rstrip() for a, b in zip(art, info)
        )
    else:
        body = "\n".join(art + [""] + [x.rstrip() for x in info])
    header = ("<!-- Generated by generate_readme.py. Do not hand-edit; "
              "change ROWS in that file and re-run. -->\n\n")
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
