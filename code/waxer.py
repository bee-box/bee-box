#!/usr/bin/env python3
"""
🏈 Waxer – waxer.py

Processes Spelling Bee puzzles:
- Adds new puzzles from words.xml into puzzles.xml (like recruiting rookies to the team)
- Ensures each puzzle has a unique ID and full metadata (contract signed!)
- Appends blank puzzles through Jan 3 of next year (depth chart padding)
- Logs all activity to xml/log.txt (play-by-play commentary)
"""

import os
from datetime import date, timedelta, datetime
import xml.etree.ElementTree as ET
from uuid import uuid4
import random
from collections import Counter

# ─── KICKOFF CONFIG ───────────────────────────────────────────────────────────
# We're setting the field for the game here: defining file paths and making sure the XML folder exists.
WORDS_XML = "xml/words.xml"       # Playbook with word formations
PUZZLES_XML = "xml/puzzles.xml"   # The season schedule
LOG_FILE = "log/log.txt"          # Sideline commentary (aka logs)
os.makedirs("xml", exist_ok=True)

# ─── PLAY-BY-PLAY LOGGER ──────────────────────────────────────────────────────
# Logs messages like a game recap, putting the latest plays at the top of the scroll.
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

# ─── HUDDLE UP: MAKE THE XML PRETTY ───────────────────────────────────────────
# We’re calling a timeout to make the playbook readable — properly indented XML.
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

# ─── SCOUTING REPORT ──────────────────────────────────────────────────────────
# These help us track the dates and IDs already on the roster.
def get_puzzle_dates(root):
    return {p.attrib.get("date") for p in root.findall("puzzle")}

def get_existing_ids(root):
    return {p.attrib.get("id") for p in root.findall("puzzle") if "id" in p.attrib}

# Think of this as issuing a jersey number: make it unique.
def generate_id(date_str, existing_ids):
    base = date_str.replace("-", "")
    while True:
        suffix = uuid4().hex[:6]
        new_id = f"{base}-{suffix}"
        if new_id not in existing_ids:
            return new_id

# Trick play: scramble the letters (but don’t fumble the original).
def generate_jumble(word):
    if len(word) < 2:
        return word
    chars = list(word)
    attempts = 0
    while attempts < 10:
        random.shuffle(chars)
        jumbled = ''.join(chars)
        if jumbled != word:
            return jumbled
        attempts += 1
    return word[::-1] if word[::-1] != word else word

# ─── STATS DEPARTMENT ─────────────────────────────────────────────────────────
# Adds all the extra info to each word — kind of like tracking a player's speed, yards, and fantasy points.
def add_word_attributes(word_el, letterset=None):
    added = Counter()
    text = word_el.text.strip().upper() if word_el.text else ""
    word_el.text = text
    if not text:
        return added

    if "points" in word_el.attrib:
        return added

    if "length" not in word_el.attrib:
        word_el.set("length", str(len(text)))
        added["length"] += 1
    if "first" not in word_el.attrib:
        word_el.set("first", text[0])
        added["first"] += 1
    if "firsttwo" not in word_el.attrib:
        word_el.set("firsttwo", text[:2])
        added["firsttwo"] += 1
    if "jumbled" not in word_el.attrib:
        word_el.set("jumbled", generate_jumble(text))
        added["jumbled"] += 1

    pangram = False
    if letterset:
        wordset = set(text)
        if wordset >= letterset:
            pangram = True
            if "pangram" not in word_el.attrib:
                word_el.set("pangram", "yes")
                added["pangram"] += 1
            if len(text) == 7 and wordset == letterset and "perfectpangram" not in word_el.attrib:
                word_el.set("perfectpangram", "yes")
                added["perfectpangram"] += 1

    base_points = 1 if len(text) == 4 else len(text)
    if pangram:
        base_points += 7
    word_el.set("points", str(base_points))
    added["points"] += 1

    return added

# This finds the "center letter" and the supporting squad.
def get_letters_from_words(words):
    sets = [set(w) for w in words]
    if not sets:
        return ""
    common = sorted(set.intersection(*sets))
    if not common:
        return ""
    first = common[0]
    all_letters = set("".join(words))
    rest = sorted(all_letters - {first})
    return first + ''.join(rest)

# ─── COACHING STRATEGY (PUZZLE METADATA) ──────────────────────────────────────
# Add all the calculated metrics — we’re prepping for game day.
def update_puzzle_metadata(puzzle, existing_ids):
    if "id" not in puzzle.attrib:
        date_str = puzzle.attrib.get("date", "unknown")
        new_id = generate_id(date_str, existing_ids)
        puzzle.set("id", new_id)
        existing_ids.add(new_id)

    words = [w_el.text.strip().upper() for w_el in puzzle.findall("word") if w_el.text]
    if not words:
        return

    if "count" not in puzzle.attrib:
        puzzle.set("count", str(len(words)))

    if "letters" not in puzzle.attrib:
        letters = get_letters_from_words(words)
        if letters and len(letters) == 7:
            puzzle.set("letters", letters)

    letterset = set(puzzle.attrib["letters"]) if "letters" in puzzle.attrib else None

    for word_el in puzzle.findall("word"):
        add_word_attributes(word_el, letterset)

    if "letters" in puzzle.attrib:
        letters = puzzle.attrib["letters"]
        starts = {ch: 0 for ch in letters}
        for w_el in puzzle.findall("word"):
            first = w_el.attrib.get("first")
            if first in starts:
                starts[first] += 1
        for i, ch in enumerate(letters):
            puzzle.set(f"letter{i+1}", ch)
            puzzle.set(f"letter{i+1}count", str(starts[ch]))

        if "pangrams" not in puzzle.attrib or "perfectpangrams" not in puzzle.attrib:
            pgram_count = 0
            perfect_count = 0
            for w_el in puzzle.findall("word"):
                if w_el.attrib.get("pangram") == "yes":
                    pgram_count += 1
                if w_el.attrib.get("perfectpangram") == "yes":
                    perfect_count += 1
            puzzle.set("pangrams", str(pgram_count))
            puzzle.set("perfectpangrams", str(perfect_count))

    if "queenbee" not in puzzle.attrib:
        total = sum(int(w.attrib.get("points", "0")) for w in puzzle.findall("word"))
        puzzle.set("queenbee", str(total))

    if "letters" in puzzle.attrib:
        letters = puzzle.attrib["letters"]
        starts = {ch: 0 for ch in letters}
        for w_el in puzzle.findall("word"):
            first = w_el.attrib.get("first")
            if first in starts:
                starts[first] += 1
        puzzle.set("bingo", "BINGO" if all(starts[ch] > 0 for ch in letters) else "")

# ─── DEPTH CHART: FILL OUT THE SCHEDULE ───────────────────────────────────────
# We don’t want to run out of puzzles, so this adds blank ones into the future — think of it as building the season schedule.
def add_blank_puzzles_to_end_of_year_plus_3(root, existing_ids):
    today = date.today()
    end_date = date(today.year, 12, 31) + timedelta(days=3)
    existing_dates = get_puzzle_dates(root)
    added = 0

    for delta in range((end_date - today).days + 1):
        target_date = today + timedelta(days=delta)
        target_str = target_date.isoformat()
        if target_str not in existing_dates:
            new_puzzle = ET.SubElement(root, "puzzle", attrib={"date": target_str})
            new_id = generate_id(target_str, existing_ids)
            new_puzzle.set("id", new_id)
            existing_ids.add(new_id)
            added += 1
    log(f"Added {added} blank puzzles through Jan 3.")
    return added

# ─── GAME TIME – MAIN FUNCTION ────────────────────────────────────────────────
def wax():
    log("🕯 Starting waxer process...")

    if not os.path.exists(WORDS_XML):
        raise FileNotFoundError(f"{WORDS_XML} not found.")
    words_root = ET.parse(WORDS_XML).getroot()

    if os.path.exists(PUZZLES_XML):
        puzzles_tree = ET.parse(PUZZLES_XML)
        puzzles_root = puzzles_tree.getroot()
    else:
        puzzles_root = ET.Element("puzzles")
        puzzles_tree = ET.ElementTree(puzzles_root)

    existing_dates = get_puzzle_dates(puzzles_root)
    existing_ids = get_existing_ids(puzzles_root)
    seen_dates = set()

    added = 0
    for puzzle in words_root.findall("puzzle"):
        date_str = puzzle.attrib.get("date")
        if not date_str or date_str in existing_dates or date_str in seen_dates:
            continue
        seen_dates.add(date_str)
        new_puzzle = ET.Element("puzzle", attrib=dict(puzzle.attrib))
        for word_el in puzzle.findall("word"):
            new_word = ET.Element("word")
            new_word.text = word_el.text.strip().upper()
            new_puzzle.append(new_word)
        puzzles_root.append(new_puzzle)
        added += 1

    log(f"Imported {added} new puzzles from words.xml.")
    add_blank_puzzles_to_end_of_year_plus_3(puzzles_root, existing_ids)

    for puzzle in puzzles_root.findall("puzzle"):
        if not puzzle.findall("word") and "id" in puzzle.attrib:
            continue
        update_puzzle_metadata(puzzle, existing_ids)

    indent(puzzles_root)
    puzzles_tree.write(PUZZLES_XML, encoding="utf-8", xml_declaration=True)
    log("✅ Wax complete.\n")

# ─── TWO-MINUTE WARNING: ENTRYPOINT ───────────────────────────────────────────
if __name__ == "__main__":
    wax()
