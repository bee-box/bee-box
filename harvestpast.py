#!/usr/bin/env python3
"""
📅 Spelling Bee Harvester – harvestpast.py

Automatically fetches Spelling Bee puzzles from yesterday through ten days ago
via archive URLs (YYYY-MM-DD format), adds them to `xml/words.xml` if missing,
deletes any duplicate puzzles, sorts words inside puzzles alphabetically,
and ensures all puzzles are chronologically sorted (newest at the bottom).
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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

# ─── Load Existing Puzzle Dates ─────────────────────────────────────────────────
def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}

# ─── Scrape Puzzle from Specific Date URL ──────────────────────────────────────
def fetch_puzzle(date_str):
    url = f"{BASE_URL}/{date_str}"  # URL expects YYYY-MM-DD
    try:
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

    except Exception as e:
        print(f"❌ Failed to fetch {date_str}: {e}")
        return None

# ─── Add New Puzzle if Needed ───────────────────────────────────────────────────
def add_puzzle_if_needed(date_str, words, existing_dates, root):
    if date_str in existing_dates:
        print(f"ℹ️ Puzzle for {date_str} already exists. Skipping.")
        return False

    if not words:
        print(f"⚠️ No words found for {date_str}. Skipping.")
        return False

    puzzle_el = ET.Element("puzzle", date=date_str)
    for word in sorted(words):  # 🛠️ Sort words alphabetically as we add them
        word_el = ET.SubElement(puzzle_el, "word")
        word_el.text = word
    root.append(puzzle_el)
    print(f"✅ Added puzzle for {date_str} with {len(words)} words.")
    return True

# ─── Deduplicate and Sort Puzzles ──────────────────────────────────────────────
def deduplicate_and_sort_puzzles(root):
    """
    Remove duplicate puzzles (keep one per date), sort puzzles by date,
    and sort words inside each puzzle alphabetically.
    """
    puzzles_by_date = {}
    for puzzle in root.findall("puzzle"):
        date = puzzle.attrib.get("date")
        if date and date not in puzzles_by_date:
            puzzles_by_date[date] = puzzle
        else:
            root.remove(puzzle)  # 🛠️ Remove duplicate

    # 🛠️ Sort puzzles by date
    sorted_dates = sorted(puzzles_by_date.keys(), key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
    root.clear()
    for date in sorted_dates:
        puzzle = puzzles_by_date[date]

        # 🛠️ Sort words inside each puzzle
        words = puzzle.findall("word")
        words_text = sorted(w.text.strip() for w in words if w.text)
        puzzle.clear()
        for word_text in words_text:
            word_el = ET.SubElement(puzzle, "word")
            word_el.text = word_text
        puzzle.attrib["date"] = date

        root.append(puzzle)

# ─── Main Logic ────────────────────────────────────────────────────────────────
def main():
    existing_dates = load_existing_dates()

    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("words")
        tree = ET.ElementTree(root)

    today = datetime.today()

    # ─── Loop from yesterday (-1) back to 10 days ago (-10) ───
    for offset in range(1, 11):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%Y-%m-%d")  # YYYY-MM-DD for URL and XML

        words = fetch_puzzle(date_str)
        if words is not None:
            add_puzzle_if_needed(date_str, words, existing_dates, root)

        time.sleep(1)  # polite delay between requests

    # ─── Deduplicate puzzles and sort ───
    deduplicate_and_sort_puzzles(root)

    indent(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    print("✅ Deduplicated, sorted, and saved all puzzles.")

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
