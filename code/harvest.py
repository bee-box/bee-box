#!/usr/bin/env python3
"""
🐝 Spelling Bee Harvester – harvest.py

Fetches today's NYT Spelling Bee puzzle (date + words only) and
appends it to `xml/words.xml` if that date isn't already present.

All events are logged to log/log.txt
and also printed to the screen.
"""

import os
import sys
import time
import json
import argparse
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta

# ─── Configuration ─────────────────────────────────────────────────────────────
XML_DIR = "xml"
LOG_DIR = "log"
XML_FILE = os.path.join(XML_DIR, "words.xml")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")
NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"

os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ─── Logging ───────────────────────────────────────────────────────────────────
def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def log_separator():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("────────────────────────────────────────────\n\n")

# ─── Command Line Arguments ────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Harvest today's Spelling Bee puzzle.")
    parser.add_argument("--no-gap-check", action="store_true", help="Skip the missing date report.")
    parser.add_argument("--test-error", action="store_true", help="Trigger a test error and send a notification.")
    return parser.parse_args()

# ─── Date Gap Checker ──────────────────────────────────────────────────────────
def log_date_gaps(existing_dates):
    if not existing_dates:
        log("⚠️ No existing dates found.")
        return

    sorted_dates = sorted(existing_dates)
    missing = []

    for i in range(1, len(sorted_dates)):
        d1 = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
        d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        gap = (d2 - d1).days

        if gap > 1:
            for j in range(1, gap):
                missing_date = (d1 + timedelta(days=j)).strftime("%Y-%m-%d")
                missing.append(missing_date)

    if missing:
        log("📅 Missing puzzle dates:")
        for m in missing:
            log(f"  - {m}")
    else:
        log("✅ No missing puzzle dates detected.")

# ─── Load Existing Puzzle Dates ────────────────────────────────────────────────
def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    root = ET.parse(XML_FILE).getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}

def load_latest_words():
    if not os.path.exists(XML_FILE):
        return []
    root = ET.parse(XML_FILE).getroot()
    puzzles = root.findall("puzzle")
    if not puzzles:
        return []
    latest_puzzle = puzzles[-1]
    return sorted([w.text.strip().upper() for w in latest_puzzle.findall("word") if w.text])

# ─── Fetch Puzzle Data ─────────────────────────────────────────────────────────
def fetch_puzzle():
    log("📡 Fetching Spelling Bee puzzle from NYT...")
    max_retries = 3
    retry_delay = 5

    for attempt in range(1, max_retries + 1):
        try:
            log(f"Attempt {attempt}...")
            with requests.get(NYT_URL, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

            script_tag = next(
                (s.string for s in soup.find_all("script") if s.string and "window.gameData" in s.string),
                None
            )
            if not script_tag:
                raise RuntimeError("Cannot find gameData in page source.")

            start = script_tag.find("{")
            brace_count = 0
            for i in range(start, len(script_tag)):
                if script_tag[i] == '{':
                    brace_count += 1
                elif script_tag[i] == '}':
                    brace_count -= 1
                if brace_count == 0:
                    json_str = script_tag[start:i + 1]
                    break

            data = json.loads(json_str)
            today_data = data.get("today", {})

            raw_date = today_data.get("printDate")
            date_str = raw_date.replace("/", "-") if raw_date else date.today().strftime("%Y-%m-%d")
            answers = today_data.get("answers", [])

            log(f"📅 Puzzle for {date_str} fetched with {len(answers)} words.")
            return date_str, [w.upper() for w in answers]

        except Exception as e:
            log(f"⚠️ Error: {e}")
            try:
                from emailer import send_email_notification
                send_email_notification("❌ Harvest Error", str(e))
            except Exception as mailerr:
                log(f"⚠️ Failed to send error email: {mailerr}")
            sys.exit(1)
        log("🔁 Retrying in 5 seconds...")
        time.sleep(retry_delay)

# ─── XML Pretty Formatter ──────────────────────────────────────────────────────
def indent(elem, level=0):
    i = "\n" + "  " * level
    j = "\n" + "  " * (level + 1)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = j
        for idx, child in enumerate(elem):
            indent(child, level + 1)
            child.tail = j if idx < len(elem) - 1 else i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i

# ─── Append Puzzle to XML ──────────────────────────────────────────────────────
def append_puzzle(date_str, words):
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("words")
        tree = ET.ElementTree(root)

    puzzle_el = ET.SubElement(root, "puzzle", date=date_str)
    for word in words:
        word_el = ET.SubElement(puzzle_el, "word")
        word_el.text = word

    indent(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    log(f"✅ Puzzle for {date_str} appended to words.xml.")

# ─── Main Function ─────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    log("🟡 START HARVEST RUN")

    if args.test_error:
        log("🚨 Test error triggered via --test-error flag.")
        from emailer import send_email_notification
        send_email_notification("🚨 Test Error Notification", "This is a test of the emergency bee-cast system.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    existing_dates = load_existing_dates()

    if not args.no_gap_check:
        log_date_gaps(sorted(existing_dates))

    today_str = date.today().strftime("%Y-%m-%d")
    if today_str in existing_dates:
        log(f"ℹ️ Puzzle for {today_str} already exists in words.xml. Skipping scrape.")
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
        log(f"⚠️ Puzzle for {date_str} has no words. Skipping.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        log("ℹ️ Words identical to previous puzzle. Skipping.")
        log("🔚 END HARVEST RUN")
        log_separator()
        return

    append_puzzle(date_str, words)
    log("✅ Harvest complete.")
    log("🔚 END HARVEST RUN")
    log_separator()

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
