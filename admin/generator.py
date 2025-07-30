# === START: imports ===
import xml.etree.ElementTree as ET
import requests
import jwt
import time
from datetime import datetime
import pytz
import os
import json
# === END: imports ===


# === START: configuration ===
GHOST_ADMIN_API_URL = 'https://beebox.ghost.io/ghost/api/admin'
GHOST_ADMIN_API_KEY = '68890d47ec9644000185b866:36724bdf69b417f92fec3ef552fdf14f297935007748e877145f05feaa966499'
XML_FILE = os.path.join(os.path.dirname(__file__), '..', 'xml', 'puzzles.xml')
local_tz = pytz.timezone('America/Chicago')
# === END: configuration ===


# === START: token creation ===
def create_token(api_key):
    key_id, secret = api_key.split(':')
    iat = int(time.time())
    exp = iat + 5 * 60
    return jwt.encode(
        {'iat': iat, 'exp': exp, 'aud': '/admin/'},
        bytes.fromhex(secret),
        algorithm='HS256',
        headers={'kid': key_id}
    )
# === END: token creation ===


# === START: HTML formatter ===
def format_html(puzzle):
    letters = puzzle.attrib.get("letters", "")
    count = puzzle.attrib.get("count", "0")
    pangrams = puzzle.attrib.get("pangrams", "0")
    perfect = puzzle.attrib.get("perfectpangrams", "0")
    queenbee = puzzle.attrib.get("queenbee", "—")

    words = puzzle.findall("word")
    if not words:
        return "<p>No words yet for this puzzle.</p>"

    words_html = "<ul>" + "".join(
        f"<li>{w.text} <span class='points'>({w.attrib['points']} pts)</span></li>" for w in words
    ) + "</ul>"

    return f"""
    <div class='swiss-post'>
        <p><strong>Letters:</strong> {letters}</p>
        <p><strong>Word count:</strong> {count} |
           <strong>Pangrams:</strong> {pangrams} |
           <strong>Perfect pangrams:</strong> {perfect} |
           <strong>Queen Bee score:</strong> {queenbee}</p>
        <h3>Today's Words</h3>
        {words_html}
        <div style='margin-top: 20px;'>
            <a href='#' style='display:inline-block;padding:10px 20px;margin:5px;background:black;color:white;text-decoration:none;font-weight:bold;border-radius:4px;'>Try Again</a>
            <a href='#' style='display:inline-block;padding:10px 20px;margin:5px;background:black;color:white;text-decoration:none;font-weight:bold;border-radius:4px;'>Shuffle</a>
            <a href='#' style='display:inline-block;padding:10px 20px;margin:5px;background:black;color:white;text-decoration:none;font-weight:bold;border-radius:4px;'>Hint</a>
            <a href='#' style='display:inline-block;padding:10px 20px;margin:5px;background:black;color:white;text-decoration:none;font-weight:bold;border-radius:4px;'>Reveal</a>
            <a href='https://bee-box.github.io/bee-box/sheet.html' style='display:inline-block;padding:10px 20px;margin:5px;background:#FFD700;color:black;text-decoration:none;font-weight:bold;border-radius:4px;'>BEE SHEET</a>
        </div>
    </div>
    """
# === END: HTML formatter ===


# === START: main function ===
def generate_newsletters():
    print("What do you want to send?")
    print("1. A full month (e.g. August 2025)")
    print("2. A specific day (e.g. 2025-08-03)")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        month = input("Enter month (1–12): ").zfill(2)
        year = input("Enter year (e.g. 2025): ")
        date_filter = lambda d: d.strftime("%Y") == year and d.strftime("%m") == month
    elif choice == "2":
        target_date = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            day = datetime.strptime(target_date, "%Y-%m-%d").date()
            date_filter = lambda d: d.date() == day
        except ValueError:
            print("Invalid date format.")
            return
    else:
        print("Invalid choice.")
        return

    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    token = create_token(GHOST_ADMIN_API_KEY)
    headers = {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

    found = False
    for puzzle in root.findall("puzzle"):
        date_str = puzzle.attrib.get("date")
        if not date_str:
            continue

        try:
            puzzle_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        if not date_filter(puzzle_date):
            continue

        found = True
        day_suffix = lambda d: f"{d}{'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')}"
        day_ordinal = day_suffix(puzzle_date.day)
        pretty_date = puzzle_date.strftime("%A, %B") + f" {day_ordinal}"
        title = f"\U0001F41D {pretty_date}"
        local_dt = local_tz.localize(puzzle_date.replace(hour=3))
        utc_dt = local_dt.astimezone(pytz.utc)
        mm_dd = puzzle_date.strftime("%m-%d")
        feature_image_url = f"https://bee-box.github.io/bee-box/images/{mm_dd}.png"

        formatted_html = format_html(puzzle)

        mobiledoc = json.dumps({
            "version": "0.3.1",
            "atoms": [],
            "cards": [["html", {"cardName": "html", "html": formatted_html}]],
            "markups": [],
            "sections": [[10, 0]]
        })

        payload = {
            "posts": [{
                "title": title,
                "mobiledoc": mobiledoc,
                "custom_excerpt": "The Completely Unauthorized Games Toolbox",
                "status": "scheduled",
                "feature_image": feature_image_url,
                "published_at": utc_dt.isoformat()
            }]
        }

        response = requests.post(f"{GHOST_ADMIN_API_URL}/posts/", headers=headers, json=payload)
        if response.ok:
            print(f"\u2713 Scheduled: {title} ({utc_dt.strftime('%Y-%m-%d %H:%M')} UTC)")
        else:
            print(f"\u2717 Failed: {title} — {response.status_code}, {response.text}")

    if not found:
        print("No matching puzzles found.")
# === END: main function ===


# === START: script entry point ===
if __name__ == "__main__":
    generate_newsletters()
# === END: script entry point ===
