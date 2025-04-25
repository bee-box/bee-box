#!/usr/bin/env python3
"""
📅 Spelling Bee Harvester – harvestpast.py

Prompts for a date, fetches the Spelling Bee puzzle from that day
via archive URL, and ensures all puzzles in `xml/words.xml` are
chronologically sorted (newest at the bottom), whether the date is new or not.
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime

# ─── Configuration ─────────────────────────────────────────────────────────────
XML_DIR = "xml"
XML_FILE = os.path.join(XML_DIR, "words.xml")
BASE_URL = "https://www.nytimes.com/puzzles/spelling-bee"
os.makedirs(XML_DIR, exist_ok=True)

# ─── Pretty-Print XML ──────────────────────────────────────────────────────────
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

# ─── Load Existing Puzzle Dates ────────────────────────────────────────────────
def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}

# ─── Prompt for a Date ─────────────────────────────────────────────────────────
def prompt_date():
    while True:
        user_input = input("Enter date (YYYYMMDD): ").strip()
        try:
            dt = datetime.strptime(user_input, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid format. Try again (e.g., 20240417).")

# ─── Scrape Puzzle from Specific Date URL ──────────────────────────────────────
def fetch_puzzle(date_str):
    url = f"{BASE_URL}/{date_str}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
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
    puzzle_data = data.get("today", {})  # still called 'today' even for past dates

    answers = puzzle_data.get("answers", [])
    return [w.upper() for w in answers]

# ─── Add New Puzzle if Needed + Always Sort ────────────────────────────────────
def update_and_sort_puzzles(date_str, words, already_exists):
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("words")
        tree = ET.ElementTree(root)

    if not already_exists:
        puzzle_el = ET.Element("puzzle", date=date_str)
        for word in words:
            word_el = ET.SubElement(puzzle_el, "word")
            word_el.text = word
        root.append(puzzle_el)
        print(f"✅ Appended puzzle for {date_str} with {len(words)} words.")
    else:
        print(f"ℹ️ Puzzle for {date_str} already exists. Sorting anyway.")

    # Rebuild root in sorted order
    puzzles = list(root.findall("puzzle"))
    puzzles.sort(key=lambda p: datetime.strptime(p.attrib["date"], "%Y-%m-%d"))
    root.clear()
    for p in puzzles:
        root.append(p)

    indent(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    print("✅ All puzzles sorted by date.")

# ─── Main Logic ────────────────────────────────────────────────────────────────
def main():
    date_str = prompt_date()
    existing_dates = load_existing_dates()
    already_exists = date_str in existing_dates

    try:
        words = fetch_puzzle(date_str)
    except Exception as e:
        print(f"❌ Failed to fetch puzzle for {date_str}: {e}")
        return

    if not words and not already_exists:
        print(f"⚠️ No words found for {date_str}, and it's not in the file.")
        return

    update_and_sort_puzzles(date_str, words, already_exists)

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
