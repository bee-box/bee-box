#!/usr/bin/env python3
"""
Newsletter Generator for Games Toolbox
Generates and schedules email-only newsletters for spelling bee puzzles.
"""

import xml.etree.ElementTree as ET
import requests
import jwt
import time
from datetime import datetime
import pytz
import os
import json

# === START: configuration ===
GHOST_ADMIN_API_URL = 'https://beebox.ghost.io/ghost/api/admin'
GHOST_ADMIN_API_KEY = '68890d47ec9644000185b866:36724bdf69b417f92fec3ef552fdf14f297935007748e877145f05feaa966499'
XML_FILE = os.path.join(os.path.dirname(__file__), '..', 'xml', 'puzzles.xml')
local_tz = pytz.timezone('America/Chicago')
# === END: configuration ===

# === START: token creation ===
def create_token(api_key):
    """Create JWT token for Ghost Admin API authentication."""
    key_id, secret = api_key.split(':')
    iat = int(time.time())
    exp = iat + 5 * 602
    return jwt.encode(
        {'iat': iat, 'exp': exp, 'aud': '/admin/'},
        bytes.fromhex(secret),
        algorithm='HS256',
        headers={'kid': key_id}
    )
# === END: token creation ===

# === START: HTML formatter ===
def format_html(puzzle):
    """Format puzzle data into HTML email template."""
    puzzle_id = puzzle.attrib.get("id", "unknown")

    return f"""
<div style="max-width: 600px; margin: 0 auto;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: white; border: 1px solid #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <tr>
        <td style="padding: 30px 20px; background-color: white;">
            <!-- Header -->
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                    <td style="text-align: center; padding-bottom: 20px;">
                        <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 1px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Subscribers Only</h1>
                    </td>
                </tr>
            </table>
            
            <!-- Button Grid (2x2) -->
            <table cellpadding="0" cellspacing="7" border="0" width="100%" style="margin-bottom: 30px;">
                <tr>
                    <!-- First Row -->
                    <td width="50%" style="vertical-align: top;">
                        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 3px solid #333; background-color: #FFDC00;">
                            <tr>
                                <td style="padding: 0; text-align: center; height: 56px; vertical-align: middle;">
                                    <a href="https://bee-box.github.io/bee-box/sheet.html?puzzleid={puzzle_id}" style="text-decoration: none !important; display: block; white-space: nowrap; padding: 18px 12px; width: 100%; height: 100%; box-sizing: border-box;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: #333 !important; text-transform: uppercase; letter-spacing: 0.5px;">BEE SHEET</span>
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td width="50%" style="vertical-align: top;">
                        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 3px solid #333; background-color: #8A2BE2;">
                            <tr>
                                <td style="padding: 0; text-align: center; height: 56px; vertical-align: middle;">
                                    <a href="https://bee-box.github.io/bee-box/jumble.html?puzzleid={puzzle_id}" style="text-decoration: none !important; display: block; white-space: nowrap; padding: 18px 12px; width: 100%; height: 100%; box-sizing: border-box;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white !important; text-transform: uppercase; letter-spacing: 0.5px;">BEE JUMBLE</span>
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <!-- Second Row -->
                    <td width="50%" style="vertical-align: top;">
                        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 3px solid #333; background-color: #00B050;">
                            <tr>
                                <td style="padding: 0; text-align: center; height: 56px; vertical-align: middle;">
                                    <a href="https://bee-box.github.io/bee-box/peek.html?puzzleid={puzzle_id}" style="text-decoration: none !important; display: block; white-space: nowrap; padding: 18px 12px; width: 100%; height: 100%; box-sizing: border-box;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white !important; text-transform: uppercase; letter-spacing: 0.5px;">BEE PEEK</span>
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td width="50%" style="vertical-align: top;">
                        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 3px solid #333; background-color: #0023FF;">
                            <tr>
                                <td style="padding: 0; text-align: center; height: 56px; vertical-align: middle;">
                                    <a href="https://bee-box.github.io/bee-box/grid.html?puzzleid={puzzle_id}" style="text-decoration: none !important; display: block; white-space: nowrap; padding: 18px 12px; width: 100%; height: 100%; box-sizing: border-box;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; font-weight: 700; color: white !important; text-transform: uppercase; letter-spacing: 0.5px;">BEE GRID</span>
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    
    <!-- NYT Spelling Bee Section -->
    <tr>
        <td style="padding: 0 20px 30px 20px;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 3px solid #333; background-color: #FFDC00;">
                <tr>
                    <td style="padding: 25px; text-align: center;">
                        <h2 style="margin: 0 0 10px 0; font-size: 22px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 1px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Today's New York Times Spelling Bee</h2>
                        <p style="margin: 5px 0 20px 0; font-size: 16px; font-weight: 600; color: #333; text-transform: uppercase; letter-spacing: 0.5px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Skip all this other stuff...</p>
                        <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto; border: none; background-color: #333; width: auto;">
                            <tr>
                                <td style="padding: 0; text-align: center;">
                                    <a href="https://www.nytimes.com/puzzles/spelling-bee/hub" style="text-decoration: none !important; display: block; padding: 15px 30px; width: 100%; box-sizing: border-box;">
                                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: 700; color: #FFDC00 !important; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap;">PLAY NOW</span>
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    
    <!-- Footer -->
    <tr>
        <td style="text-align: center; padding: 20px;">
            <a href="https://thecompletelyunauthorizedgamestoolbox.com/" style="text-decoration: underline;">
                <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 700; color: #333 !important;">The Completely Unauthorized Games Toolbox</span>
            </a>
        </td>
    </tr>
</table>
</div>"""
# === END: HTML formatter ===

# === START: main function ===
def generate_newsletters():
    """Main function to generate and schedule newsletters."""
    print("What do you want to send?")
    print("1. A full month (e.g. August 2025)")
    print("2. A specific day (e.g. 2025-08-03)")
    print("3. A week (7 days starting from a date)")
    choice = input("Enter 1, 2, or 3: ").strip()

    if choice == "1":
        month = input("Enter month (1–12): ").zfill(2)
        year = input("Enter year (e.g. 2025): ")
        date_filter = lambda d: d.strftime("%Y") == year and d.strftime("%m") == month
        process_reverse = True  # Flag to process in reverse order for full month
    elif choice == "2":
        target_date = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            day = datetime.strptime(target_date, "%Y-%m-%d").date()
            date_filter = lambda d: d.date() == day
            process_reverse = False  # No need to reverse for single day
        except ValueError:
            print("Invalid date format.")
            return
    elif choice == "3":
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
        try:
            from datetime import timedelta
            start_day = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_day = start_day + timedelta(days=6)
            date_filter = lambda d: start_day <= d.date() <= end_day
            process_reverse = False  # No need to reverse for week
        except ValueError:
            print("Invalid date format.")
            return
    else:
        print("Invalid choice.")
        return

    print("Email-only delivery selected (no website posts will be created)")

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

    # Sort puzzles by date (reverse order for full month, normal for single day)
    if process_reverse:
        matching_puzzles.sort(key=lambda x: x[1], reverse=True)
        print(f"Processing {len(matching_puzzles)} puzzles in reverse chronological order (last day to first day)")
    else:
        matching_puzzles.sort(key=lambda x: x[1])
        print(f"Processing {len(matching_puzzles)} puzzles")

    # Process the sorted puzzles
    for puzzle, puzzle_date in matching_puzzles:
        puzzle_id = puzzle.attrib.get("id", "unknown")
        date_str = puzzle_date.strftime("%Y-%m-%d")
        print(f"Processing puzzle for {date_str}, ID: {puzzle_id}, Words: {len(puzzle.findall('word'))}")
        
        # Create pretty date string with ordinal suffix
        day_suffix = lambda d: f"{d}{'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')}"
        day_ordinal = day_suffix(puzzle_date.day)
        pretty_date = puzzle_date.strftime("%A, %B") + f" {day_ordinal}"
        title = f"{pretty_date} \U0001F41D Games Toolbox"
        
        # Convert to UTC for scheduling
        local_dt = local_tz.localize(puzzle_date.replace(hour=3))
        utc_dt = local_dt.astimezone(pytz.utc)
        
        # Feature image URL
        mm_dd = puzzle_date.strftime("%m-%d")
        feature_image_url = f"https://bee-box.github.io/bee-box/images/{mm_dd}.png"

        formatted_html = format_html(puzzle)

        # Create mobiledoc structure for Ghost
        mobiledoc = json.dumps({
            "version": "0.3.1",
            "atoms": [],
            "cards": [["html", {"cardName": "html", "html": formatted_html}]],
            "markups": [],
            "sections": [[10, 0]]
        })

        # Step 1: Create the post as a draft first
        draft_payload = {
            "posts": [{
                "title": title,
                "mobiledoc": mobiledoc,
                "custom_excerpt": "The Completely Unauthorized Games Toolbox",
                "status": "draft",
                "visibility": "public",
                "feature_image": feature_image_url,
                "email_only": True
            }]
        }

        # Create the draft post
        response = requests.post(f"{GHOST_ADMIN_API_URL}/posts/", headers=headers, json=draft_payload)
        
        if not response.ok:
            print(f"\u2717 Failed to create draft: {title} — {response.status_code}, {response.text}")
            continue
            
        draft_data = response.json()
        post_id = draft_data['posts'][0]['id']
        updated_at = draft_data['posts'][0]['updated_at']
        
        # Step 2: Edit the post to schedule it as email-only
        schedule_payload = {
            "posts": [{
                "id": post_id,
                "updated_at": updated_at,
                "status": "scheduled",
                "published_at": utc_dt.isoformat(),
                "email_only": True
            }]
        }
        
        # Schedule the post with newsletter parameters
        schedule_response = requests.put(
            f"{GHOST_ADMIN_API_URL}/posts/{post_id}/", 
            headers=headers, 
            json=schedule_payload,
            params={
                'newsletter': 'default-newsletter',
                'email_segment': 'all'
            }
        )
        
        if schedule_response.ok:
            print(f"\u2713 Scheduled (email only): {title} ({utc_dt.strftime('%Y-%m-%d %H:%M')} UTC)")
        else:
            print(f"\u2717 Failed to schedule: {title} — {schedule_response.status_code}, {schedule_response.text}")

# === END: main function ===

# === START: script entry point ===
if __name__ == "__main__":
    generate_newsletters()
# === END: script entry point ===