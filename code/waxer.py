#!/usr/bin/env python3
"""
🏈 Waxer – waxer.py (newest 5 only)

Processes Spelling Bee puzzles:
- Only processes the newest 5 puzzles from words.xml
- Fills placeholders and preserves IDs
- Appends blank puzzles through Jan 3 of next year
- Logs all activity to log/log.txt
"""

import os
from datetime import date, timedelta, datetime
import xml.etree.ElementTree as ET
from uuid import uuid4
import random
from collections import Counter

WORDS_XML = "xml/words.xml"
PUZZLES_XML = "xml/puzzles.xml"
LOG_FILE = "log/log.txt"
os.makedirs("xml", exist_ok=True)
os.makedirs("log", exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

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

def get_puzzle_dates(root):
    return {p.attrib.get("date") for p in root.findall("puzzle")}

def get_existing_ids(root):
    return {p.attrib.get("id") for p in root.findall("puzzle") if "id" in p.attrib}

def generate_id(date_str, existing_ids):
    base = date_str.replace("-", "")
    while True:
        suffix = uuid4().hex[:6]
        new_id = f"{base}-{suffix}"
        if new_id not in existing_ids:
            return new_id

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

def add_word_attributes(word_el, letterset=None):
    text = word_el.text.strip().upper() if word_el.text else ""
    word_el.text = text
    if not text:
        return
    word_el.set("length", str(len(text)))
    word_el.set("first", text[0])
    word_el.set("firsttwo", text[:2])
    word_el.set("jumbled", generate_jumble(text))
    pangram = False
    if letterset:
        wordset = set(text)
        if wordset >= letterset:
            pangram = True
            word_el.set("pangram", "yes")
            if len(text) == 7 and wordset == letterset:
                word_el.set("perfectpangram", "yes")
    base_points = 1 if len(text) == 4 else len(text)
    if pangram:
        base_points += 7
    word_el.set("points", str(base_points))

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

def update_puzzle_metadata(puzzle, existing_ids):
    if "id" not in puzzle.attrib:
        date_str = puzzle.attrib.get("date", "unknown")
        new_id = generate_id(date_str, existing_ids)
        puzzle.set("id", new_id)
        existing_ids.add(new_id)
    words = [w_el.text.strip().upper() for w_el in puzzle.findall("word") if w_el.text]
    if not words:
        return
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
        pgram_count = sum(1 for w in puzzle.findall("word") if w.attrib.get("pangram") == "yes")
        perfect_count = sum(1 for w in puzzle.findall("word") if w.attrib.get("perfectpangram") == "yes")
        puzzle.set("pangrams", str(pgram_count))
        puzzle.set("perfectpangrams", str(perfect_count))
    total = sum(int(w.attrib.get("points", "0")) for w in puzzle.findall("word"))
    puzzle.set("queenbee", str(total))
    if "letters" in puzzle.attrib:
        starts = {ch: 0 for ch in letters}
        for w_el in puzzle.findall("word"):
            first = w_el.attrib.get("first")
            if first in starts:
                starts[first] += 1
        puzzle.set("bingo", "BINGO" if all(starts[ch] > 0 for ch in letters) else "")

def wax():
    log("🕯 Starting waxer process...")
    if not os.path.exists("xml/words.xml"):
        log("❌ words.xml not found.")
        return
    words_root = ET.parse("xml/words.xml").getroot()
    puzzles = sorted(words_root.findall("puzzle"), key=lambda p: p.attrib.get("date", ""), reverse=True)[:5]
    if os.path.exists("xml/puzzles.xml"):
        puzzles_tree = ET.parse("xml/puzzles.xml")
        puzzles_root = puzzles_tree.getroot()
    else:
        puzzles_root = ET.Element("puzzles")
        puzzles_tree = ET.ElementTree(puzzles_root)
    existing_ids = get_existing_ids(puzzles_root)
    existing_puzzles = {p.attrib.get("date"): p for p in puzzles_root.findall("puzzle")}
    for puzzle in puzzles:
        date_str = puzzle.attrib.get("date")
        if not date_str:
            continue
        existing = existing_puzzles.get(date_str)
        if existing is not None:
            is_placeholder = not any(child.tag == "word" for child in existing)
            if is_placeholder:
                preserved_id = existing.attrib.get("id")
                existing.attrib.clear()
                existing.attrib.update(puzzle.attrib)
                existing.set("id", preserved_id)
                existing[:] = []
                for word_el in puzzle.findall("word"):
                    new_word = ET.Element("word")
                    new_word.text = word_el.text.strip().upper()
                    existing.append(new_word)
                log(f"🔄 Filled placeholder puzzle for {date_str}.")
            else:
                log(f"⚠️ Puzzle for {date_str} already populated. Skipping.")
        else:
            new_puzzle = ET.Element("puzzle", attrib=dict(puzzle.attrib))
            for word_el in puzzle.findall("word"):
                new_word = ET.Element("word")
                new_word.text = word_el.text.strip().upper()
                new_puzzle.append(new_word)
            puzzles_root.append(new_puzzle)
            log(f"➕ Added new puzzle for {date_str}.")
    existing_dates = get_puzzle_dates(puzzles_root)
    today = date.today()
    end_date = date(today.year, 12, 31) + timedelta(days=3)
    for delta in range((end_date - today).days + 1):
        target_date = today + timedelta(days=delta)
        target_str = target_date.isoformat()
        if target_str not in existing_dates:
            new_puzzle = ET.Element("puzzle", attrib={"date": target_str})
            new_id = generate_id(target_str, existing_ids)
            new_puzzle.set("id", new_id)
            new_puzzle.text = "\n"
            puzzles_root.append(new_puzzle)
            log(f"➕ Added placeholder puzzle for {target_str}.")
            existing_dates.add(target_str)
    for puzzle in puzzles_root.findall("puzzle"):
        if not puzzle.findall("word") and "id" in puzzle.attrib:
            continue
        update_puzzle_metadata(puzzle, existing_ids)
    indent(puzzles_root)
    puzzles_tree.write("xml/puzzles.xml", encoding="utf-8", xml_declaration=True)
    log("✅ Wax complete.")

if __name__ == "__main__":
    wax()
