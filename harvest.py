#!/usr/bin/env python3
"""
🐝 Spelling Bee Harvester – harvest.py

Fetches today's NYT Spelling Bee puzzle (date + words only) and
appends it to `xml/words.xml` if that date isn't already present.
Also logs any missing dates between the earliest and latest puzzles.

────────────────────────────────────────────────────────────────────
CHANGES:
- 🛠️ Retry fetching puzzle up to 3 times
- 🛠️ Friendly error messages on failure
- 🛠️ Detect if today's puzzle is identical to yesterday (skip if same)
────────────────────────────────────────────────────────────────────
"""

import os
import json
import time   # 🛠️ (New) Needed for retry delay
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import argparse
import sys

# ─── Configuration ─────────────────────────────────────────────────────────────
XML_DIR = "xml"
XML_FILE = os.path.join(XML_DIR, "words.xml")
NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"
os.makedirs(XML_DIR, exist_ok=True)

# ─── Colorized Output ──────────────────────────────────────────────────────────
def colored(text, color_code):
    if sys.platform == "win32":
        return text  # Skip coloring on Windows CMD
    return f"\033[{color_code}m{text}\033[0m"

# ─── CLI Args ──────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Harvest today's Spelling Bee puzzle.")
    parser.add_argument("--no-gap-check", action="store_true", help="Skip the missing date report.")
    return parser.parse_args()

# ─── Load Existing Puzzle Dates ─────────────────────────────────────────────────
def load_existing_dates():
    """
    Parses `words.xml` and returns a set of puzzle dates already stored.
    """
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}

# ─── Load Latest Puzzle Words ───────────────────────────────────────────────────
def load_latest_words():
    """
    Returns the list of words from the most recent puzzle in `words.xml`.
    """
    if not os.path.exists(XML_FILE):
        return []
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    puzzles = root.findall("puzzle")
    if not puzzles:
        return []
    latest_puzzle = puzzles[-1]
    return sorted([w.text.strip().upper() for w in latest_puzzle.findall("word") if w.text])

# ─── Scrape Puzzle from NYT ─────────────────────────────────────────────────────
def fetch_puzzle():
    """
    Scrapes the NYT Spelling Bee page to extract the printDate and answers.
    Retries up to 3 times if the request fails.
    Returns:
        tuple: (date string in YYYY-MM-DD format, list of uppercase words)
    """
    max_retries = 3
    retry_delay = 5  # seconds between retries

    for attempt in range(1, max_retries + 1):
        try:
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
            return date_str, [w.upper() for w in answers]

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 500:
                print(colored(f"🛑 Attempt {attempt}: NYT website is returning a 500 error (Internal Server Error).", "31"))
            else:
                print(colored(f"🛑 Attempt {attempt}: HTTP error: {e}", "31"))
        except requests.exceptions.RequestException as e:
            print(colored(f"🛑 Attempt {attempt}: Network error: {e}", "31"))
        except Exception as e:
            print(colored(f"🛑 Attempt {attempt}: Unexpected error: {e}", "31"))

        if attempt < max_retries:
            print(colored(f"⏳ Retrying in {retry_delay} seconds...", "33"))
            time.sleep(retry_delay)
        else:
            print(colored("❌ All retry attempts failed. Exiting.", "31"))
            sys.exit(1)

# ─── Pretty-Print XML ──────────────────────────────────────────────────────────
def indent(elem, level=0):
    """
    Adds indentation to an ElementTree element for pretty-printing.
    """
    indent_str = "\n" + "  " * level
    child_indent = "\n" + "  " * (level + 1)

    if list(elem):
        if not elem.text or not elem.text.strip():
            elem.text = child_indent
        for i, child in enumerate(elem):
            indent(child, level + 1)
            child.tail = child_indent if i < len(elem) - 1 else indent_str
    else:
        if not elem.text:
            elem.text = ''
        if not elem.tail:
            elem.tail = indent_str

# ─── Append Puzzle to XML ──────────────────────────────────────────────────────
def append_puzzle(date_str, words):
    """
    Adds a new puzzle block with <word> elements to the XML tree.
    """
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

# ─── Report Missing Dates ──────────────────────────────────────────────────────
def report_missing_dates(date_set):
    """
    Prints a list of missing dates between the first and last puzzle dates.
    """
    if not date_set:
        print("ℹ️  No dates found in words.xml. Skipping gap check.")
        return

    all_dates = sorted(datetime.strptime(d, "%Y-%m-%d") for d in date_set)
    start = all_dates[0]
    end = all_dates[-1]

    current = start
    missing = []

    while current <= end:
        d_str = current.strftime("%Y-%m-%d")
        if d_str not in date_set:
            missing.append(d_str)
        current += timedelta(days=1)

    if missing:
        print(colored(f"🛑 Missing {len(missing)} date(s):", "31"))
        for m in missing:
            print(f"  - {m}")
        with open("missing_dates.log", "w") as f:
            for m in missing:
                f.write(m + "\n")
    else:
        print(colored("✅ No missing dates found in the range.", "32"))

# ─── Main Logic ────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    date_str, words = fetch_puzzle()
    existing_dates = load_existing_dates()

    if not args.no_gap_check:
        report_missing_dates(existing_dates)

    if date_str in existing_dates:
        print(colored(f"🛑 Puzzle for {date_str} already exists. No action taken.", "33"))
        return
    if not words:
        print(colored(f"⚠️ No words fetched for {date_str}.", "33"))
        return

    # 🛠️ (New) Check if today's words are identical to yesterday's
    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        print(colored(f"🛑 Today's puzzle ({date_str}) is identical to the most recent puzzle. No action taken.", "31"))
        sys.exit(1)

    append_puzzle(date_str, words)
    print(colored(f"✅ Appended puzzle for {date_str} with {len(words)} words.", "32"))

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
