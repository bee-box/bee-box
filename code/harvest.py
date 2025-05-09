#!/usr/bin/env python3
"""
Spelling Bee Harvester – harvest.py

This script:
- Scrapes today’s New York Times Spelling Bee word list
- Saves it to xml/words.xml if the date isn’t already present
- Always backs up words.xml to xml/backups/words.xml.bak
- Uses lxml for fast and clean XML handling
- Logs all activity to log/log.txt and prints updates to the screen
"""

import os
import sys
import time
import json
import shutil
import requests
from lxml import etree as ET
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta

# ─── Folder and file paths ─────────────────────────────────────────────────────
XML_DIR = "xml"
BACKUP_DIR = os.path.join(XML_DIR, "backups")
LOG_DIR = "log"

XML_FILE = os.path.join(XML_DIR, "words.xml")
BACKUP_FILE = os.path.join(BACKUP_DIR, "words.xml.bak")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"

# Make sure all folders exist before use
os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ─── Logging ──────────────────────────────────────────────────────────────────
def log(message):
    """Log a message with timestamp to screen and log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def log_separator():
    """Adds a divider line to the end of the log entry."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("────────────────────────────────────────────\n\n")

# ─── Load saved puzzle data ───────────────────────────────────────────────────
def load_existing_dates():
    """Returns a set of all puzzle dates already stored in words.xml."""
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.get("date") for p in root.findall("puzzle")}

def load_latest_words():
    """Returns the word list from the most recent puzzle."""
    if not os.path.exists(XML_FILE):
        return []
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    puzzles = root.findall("puzzle")
    if not puzzles:
        return []
    latest = puzzles[-1]
    return sorted([w.text.strip().upper() for w in latest.findall("word") if w.text])

# ─── Scrape puzzle from NYT website ───────────────────────────────────────────
def fetch_puzzle():
    """Scrapes the NYT Spelling Bee puzzle and returns the date and words."""
    log("📡 Fetching puzzle from NYT...")
    max_retries = 3
    delay = 5

    for attempt in range(1, max_retries + 1):
        try:
            log(f"Attempt {attempt}...")
            response = requests.get(NYT_URL, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            script = next((s.string for s in soup.find_all("script") if s.string and "window.gameData" in s.string), None)
            if not script:
                raise RuntimeError("Game data not found in page source.")

            start = script.find("{")
            brace_count = 0
            for i in range(start, len(script)):
                if script[i] == '{':
                    brace_count += 1
                elif script[i] == '}':
                    brace_count -= 1
                if brace_count == 0:
                    json_str = script[start:i + 1]
                    break

            data = json.loads(json_str)
            today_data = data.get("today", {})
            raw_date = today_data.get("printDate")
            date_str = raw_date.replace("/", "-") if raw_date else date.today().isoformat()
            answers = today_data.get("answers", [])

            log(f"📅 Puzzle for {date_str} fetched with {len(answers)} words.")
            return date_str, [w.upper() for w in answers]

        except Exception as e:
            log(f"⚠️ Error: {e}")
            try:
                from emailer import send_email_notification
                send_email_notification("❌ Harvest Error", str(e))
            except Exception as mail_err:
                log(f"⚠️ Failed to send email alert: {mail_err}")
            sys.exit(1)
        log("🔁 Retrying in 5 seconds...")
        time.sleep(delay)

# ─── Save puzzle to XML using lxml ────────────────────────────────────────────
def append_puzzle(date_str, words):
    """Adds the puzzle to xml/words.xml using lxml, with pretty print."""
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("words")
        tree = ET.ElementTree(root)

    puzzle = ET.SubElement(root, "puzzle", date=date_str)
    for word in words:
        ET.SubElement(puzzle, "word").text = word

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True, pretty_print=True)
    log(f"✅ Puzzle for {date_str} added to words.xml.")

# ─── Main program ─────────────────────────────────────────────────────────────
def main():
    log("🟡 START HARVEST RUN")

    # Always back up words.xml before doing anything
    if os.path.exists(XML_FILE):
        shutil.copyfile(XML_FILE, BACKUP_FILE)
        log(f"🗂 Backup created: {BACKUP_FILE}")

    existing_dates = load_existing_dates()
    today_str = date.today().isoformat()

    if today_str in existing_dates:
        log(f"ℹ️ Puzzle for {today_str} already exists. Skipping.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    date_str, words = fetch_puzzle()

    if date_str in existing_dates:
        log(f"ℹ️ Puzzle for {date_str} already exists. Skipping.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    if not words:
        log(f"⚠️ No words found for {date_str}.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    if sorted(words) == load_latest_words():
        log("ℹ️ Puzzle is identical to the previous one. Skipping.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    append_puzzle(date_str, words)
    log("✅ Harvest complete.")
    log("🔚 END HARVEST RUN")
    log_separator()

# ─── Run the script ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
