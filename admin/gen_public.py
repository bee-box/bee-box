import xml.etree.ElementTree as ET
import requests
import jwt
import time
from datetime import datetime, timedelta
import pytz
import os
import json
import calendar

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
    puzzle_id = puzzle.attrib.get("id", "unknown")

    return f"""
<div style="background: white; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; border-radius: 8px; overflow: hidden;">
    <div style="padding: 30px 20px; background: white;">
        <div style="text-align: center; margin-bottom: 30px;">
            <p style="margin: 0 0 20px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; color: #666; line-height: 1.5;">Here is our entire archive of tools to help you with the Bee. To get TODAY'S tools delivered to your email every morning subscribe for free at the bottom of this post.</p>
            <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 1px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Toolbox Archives</h1>
        </div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 30px;">
            <a href="https://bee-box.github.io/bee-box/sheet.html?puzzleid={puzzle_id}" style="background: #FFDC00; border: 3px solid #333; border-radius: 8px; padding: 18px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: #333; text-decoration: none; display: flex; align-items: center; justify-content: center; text-align: center; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; min-height: 56px;">
                Bee Sheet
            </a>
            <a href="https://bee-box.github.io/bee-box/jumble.html?puzzleid={puzzle_id}" style="background: #8A2BE2; border: 3px solid #333; border-radius: 8px; padding: 18px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white; text-decoration: none; display: flex; align-items: center; justify-content: center; text-align: center; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; min-height: 56px;">
                Bee Jumble
            </a>
            <a href="https://bee-box.github.io/bee-box/peek.html?puzzleid={puzzle_id}" style="background: #00B050; border: 3px solid #333; border-radius: 8px; padding: 18px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white; text-decoration: none; display: flex; align-items: center; justify-content: center; text-align: center; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; min-height: 56px;">
                Bee Peek
            </a>
            <a href="https://bee-box.github.io/bee-box/grid.html?puzzleid={puzzle_id}" style="background: #0023FF; border: 3px solid #333; border-radius: 8px; padding: 18px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white; text-decoration: none; display: flex; align-items: center; justify-content: center; text-align: center; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; min-height: 56px;">
                Bee Grid
            </a>
        </div>
        
        <div style="background: #FFDC00; border: 3px solid #333; border-radius: 12px; padding: 25px; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
            <h2 style="margin: 0 0 10px 0; font-size: 22px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 1px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Today's New York Times Spelling Bee</h2>
            <p style="margin: 5px 0 20px 0; font-size: 16px; font-weight: 600; color: #333; text-transform: uppercase; letter-spacing: 0.5px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Skip all this other stuff...</p>
            <a href="https://www.nytimes.com/puzzles/spelling-bee/hub" style="background: #333; color: #FFDC00; border: none; border-radius: 8px; padding: 15px 30px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: 700; text-decoration: none; display: inline-block; cursor: pointer; text-transform: uppercase; letter-spacing: 1px;">
                Play Now
            </a>
        </div>
        
        <div style="text-align: center; padding: 20px 0 0 0;">
            <a href="https://thecompletelyunauthorizedgamestoolbox.com/" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 700; color: #333; text-decoration: underline;">
                The Completely Unauthorized Games Toolbox
            </a>
        </div>
    </div>
</div>    """
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
    print(f"Found {len(root.findall('puzzle'))} puzzles in XML")
    token = create_token(GHOST_ADMIN_API_KEY)
    headers = {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

    # Collect matching puzzles first
    matching_puzzles = []
    for puzzle in root.findall("puzzle"):
        date_str = puzzle.attrib.get("date")
        if not date_str:
            print(f"Skipping puzzle with no date attribute")
            continue

        try:
            puzzle_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Skipping puzzle with invalid date: {date_str}")
            continue

        if date_filter(puzzle_date):
            matching_puzzles.append((puzzle, puzzle_date))

    if not matching_puzzles:
        print("No matching puzzles found.")
        return

    # Sort by date in descending order (latest to earliest)
    matching_puzzles.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Processing {len(matching_puzzles)} puzzles in reverse chronological order...")

    for puzzle, puzzle_date in matching_puzzles:
        puzzle_id = puzzle.attrib.get("id", "unknown")
        date_str = puzzle_date.strftime("%Y-%m-%d")
        print(f"Processing puzzle for {date_str}, ID: {puzzle_id}, Words: {len(puzzle.findall('word'))}")
        
        day_suffix = lambda d: f"{d}{'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')}"
        day_ordinal = day_suffix(puzzle_date.day)
        pretty_date = puzzle_date.strftime("%A, %B") + f" {day_ordinal}"
        title = f"{pretty_date} \U0001F41D Games Toolbox Archive"
        local_dt = local_tz.localize(puzzle_date.replace(hour=3))
        # Add 24 hours to the publish time
        local_dt = local_dt + timedelta(days=1)
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

        # Fixed settings for post-only (no email, public visibility)
        payload = {
            "posts": [{
                "title": title,
                "mobiledoc": mobiledoc,
                "custom_excerpt": "The Completely Unauthorized Games Toolbox",
                "status": "scheduled",
                "visibility": "public",
                "feature_image": feature_image_url,
                "published_at": utc_dt.isoformat(),
                "send_email_when_published": False
            }]
        }

        response = requests.post(f"{GHOST_ADMIN_API_URL}/posts/", headers=headers, json=payload)
        if response.ok:
            print(f"\u2713 Scheduled (post only): {title} ({utc_dt.strftime('%Y-%m-%d %H:%M')} UTC)")
        else:
            print(f"\u2717 Failed: {title} — {response.status_code}, {response.text}")
# === END: main function ===

# === START: script entry point ===
if __name__ == "__main__":
    generate_newsletters()
# === END: script entry point ===