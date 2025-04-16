#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# 🐝 NYT Spelling Bee Puzzle Harvester – harvest.py
#
# This script fetches the **New York Times Spelling Bee** puzzle for today,
# extracts the answers and letter set from embedded JSON, and appends it to
# a structured XML archive (`xml/bees.xml`). It avoids duplicates, ensures
# each puzzle has a unique UUID, and logs skipped duplicates.
#
# 📁 Output:
#   - XML:   xml/bees.xml  ← stores all puzzles
#   - LOG:   logs/skipped_dupes.log ← records duplicate skips
#
# 📦 Features:
#   - Auto-creates the XML file if missing
#   - Ensures consistent letter ordering and puzzle UUIDs
#   - Tracks and counts puzzles by date
#
# 🛠️ Usage:
#   - Run manually or schedule via cron/GitHub Actions
#     $ python harvest.py
#
# 🔁 Daily GitHub Action compatible
#
# -------------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import date, datetime
import os
import json
from xml.dom import minidom
from uuid import uuid4

# Set up file and folder locations
os.makedirs("xml", exist_ok=True)
XML_FILE = os.path.join("xml", "bees.xml")

NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"
nyt_added = 0

# [ ... rest of the script stays unchanged ... ]
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import date, datetime
import os
import json
from xml.dom import minidom
from uuid import uuid4

XML_FILE = "bees.xml"
NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"
nyt_added = 0

def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        return {p.attrib.get("date") for p in root.findall("puzzle")}
    except ET.ParseError:
        print("⚠️ Warning: bees.xml exists but is not readable.")
        return set()

def indent(elem, level=0):
    i = "\n" + "  " * level
    j = "\n" + "  " * (level + 1)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = j
        for idx, child in enumerate(elem):
            indent(child, level + 1)
            child.tail = i if idx == len(elem) - 1 else j
    else:
        elem.text = elem.text or ''
        elem.tail = elem.tail or i

def find_common_letter(words):
    letter_sets = [set(word) for word in words if word.isalpha()]
    common = set.intersection(*letter_sets) if letter_sets else set()
    return sorted(common)[0] if common else None

def calculate_letters_attribute(words):
    words = [w.upper() for w in words]
    common_letter = find_common_letter(words)
    if not common_letter:
        return None
    all_letters = set("".join(words))
    all_letters.discard(common_letter)
    other_letters = sorted(all_letters)[:6]
    return (common_letter + "".join(other_letters)).upper()

def add_letter_elements(puzzle_el, words, letters):
    from collections import Counter
    first_letter_counts = Counter(word[0] for word in words if word)
    for idx, letter in enumerate(letters):
        tag = f"letter{idx+1}"
        el = ET.SubElement(puzzle_el, tag)
        el.text = str(first_letter_counts.get(letter, 0))

def append_puzzle(root, date_str, url, words):
    puzzle_el = ET.SubElement(root, "puzzle", date=date_str, url=url)
    puzzle_el.set("puzzleid", str(uuid4()))

    for word in words:
        word_el = ET.SubElement(puzzle_el, "word", length=str(len(word)))
        word_el.text = word.upper()

    letter_attr = calculate_letters_attribute(words)
    if letter_attr:
        puzzle_el.set("letters", letter_attr)
        add_letter_elements(puzzle_el, words, letter_attr)

def fetch_from_nyt():
    global nyt_added
    today = date.today().strftime("%Y-%m-%d")
    existing_dates = load_existing_dates()
    if today in existing_dates:
        return

    print("🔍 Fetching from NYT site")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(NYT_URL, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ NYT fetch failed: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    script = next((s.string for s in soup.find_all("script") if s.string and "window.gameData" in s.string), None)
    if not script:
        return

    json_start = script.find("{")
    brace_count = 0
    for i in range(json_start, len(script)):
        if script[i] == "{":
            brace_count += 1
        elif script[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                json_str = script[json_start:i+1]
                break
    else:
        return

    try:
        data = json.loads(json_str)
        words = [w.upper() for w in data.get("today", {}).get("answers", [])]
        if not words:
            return

        new_letters = calculate_letters_attribute(words)
        if not new_letters:
            return

        # Load or create root
        if os.path.exists(XML_FILE):
            tree = ET.parse(XML_FILE)
            root = tree.getroot()

            # Get most recent puzzle and its letters
            last_puzzle = root.findall("puzzle")[-1] if len(root) else None
            last_letters = last_puzzle.get("letters") if last_puzzle is not None else None

            if new_letters == last_letters:
                print("🚫 Today's puzzle isn't yet available.")

                # ✅ Archive skipped dupe to logs
                os.makedirs("logs", exist_ok=True)
                log_path = os.path.join("logs", "skipped_dupes.log")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{timestamp} — Skipped duplicate puzzle with letters: {new_letters}\n")
                return
        else:
            root = ET.Element("spelling_bees")
            tree = ET.ElementTree(root)

        append_puzzle(root, today, NYT_URL, words)
        nyt_added += 1
        indent(root)
        tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
        print(f"✅ NYT puzzle added.")

    except json.JSONDecodeError:
        print("❌ JSON parsing failed.")

def patch_missing_puzzleids(xml_file):
    if not os.path.exists(xml_file):
        print("❌ bees.xml not found.")
        return

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        added = 0
        for puzzle in root.findall("puzzle"):
            if "puzzleid" not in puzzle.attrib:
                puzzle.set("puzzleid", str(uuid4()))
                added += 1
        if added > 0:
            indent(root)
            tree.write(xml_file, encoding="utf-8", xml_declaration=True)
            print(f"🛠️ Patched {added} puzzle(s) with missing puzzleid.")
    except Exception as e:
        print(f"⚠️ Failed to patch puzzleids: {e}")

if __name__ == "__main__":
    fetch_from_nyt()
    patch_missing_puzzleids(XML_FILE)

    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        print("\n📊 Summary:")
        print(f"➕ NYT puzzle added: {nyt_added}")
        print(f"📆 Total puzzles in bees.xml: {len(root)}")
    except Exception as e:
        print(f"⚠️ Could not parse bees.xml to count total puzzles: {e}")
