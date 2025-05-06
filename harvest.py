#!/usr/bin/env python3
"""
🐝 Spelling Bee Harvester – harvest.py

Fetches today's NYT Spelling Bee puzzle (date + words only) and
appends it to `xml/words.xml` if that date isn't already present.

Logs all activity to xml/log.txt (newest entries first).
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import date, datetime
import argparse
import sys

# ─── Config ────────────────────────────────────────────────────────────────────
XML_DIR = "xml"
XML_FILE = os.path.join(XML_DIR, "words.xml")
LOG_FILE = os.path.join(XML_DIR, "log.txt")
NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"
os.makedirs(XML_DIR, exist_ok=True)

# ─── Logging (Newest Entries First) ────────────────────────────────────────────
def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_entry = f"[{timestamp}] {message}\n"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r+", encoding="utf-8") as f:
            old = f.read()
            f.seek(0)
            f.write(new_entry + old)
    else:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(new_entry)

# ─── CLI Args ──────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Harvest today's Spelling Bee puzzle.")
    parser.add_argument("--no-gap-check", action="store_true", help="Skip the missing date report.")
    return parser.parse_args()

# ─── Load Dates & Words ────────────────────────────────────────────────────────
def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}

def load_latest_words():
    if not os.path.exists(XML_FILE):
        return []
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    puzzles = root.findall("puzzle")
    if not puzzles:
        return []
    latest_puzzle = puzzles[-1]
    return sorted([w.text.strip().upper() for w in latest_puzzle.findall("word") if w.text])

# ─── Fetch Puzzle from NYT ─────────────────────────────────────────────────────
def fetch_puzzle():
    max_retries = 3
    retry_delay = 5
    log("📡 Fetching Spelling Bee puzzle from NYT...")

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
            if attempt == max_retries:
                log("❌ Failed after max retries.")
                sys.exit(1)
            time.sleep(retry_delay)
            log("🔁 Retrying...")

# ─── XML Formatter ─────────────────────────────────────────────────────────────
def indent(elem, level=0):
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

# ─── Append Puzzle to words.xml ────────────────────────────────────────────────
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

# ─── Main Logic ────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    log("🚀 Starting Spelling Bee harvest.")
    date_str, words = fetch_puzzle()
    existing_dates = load_existing_dates()

    if date_str in existing_dates:
        log(f"⚠️ Puzzle for {date_str} already exists. Skipping.")
        return
    if not words:
        log(f"⚠️ Puzzle for {date_str} has no words. Skipping.")
        return

    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        log("⚠️ Words identical to previous puzzle. Skipping.")
        sys.exit(1)

    append_puzzle(date_str, words)
    log("✅ Harvest complete.\n")

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
