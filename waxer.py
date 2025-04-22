#!/usr/bin/env python3
"""
🐝 Waxer – waxer.py

Processes Spelling Bee puzzles:
- Appends unique puzzles from words.xml to puzzles.xml
- Adds to each puzzle: id, count, letters, letter1–7, letter1count–7count,
  pangrams, perfectpangrams
- Adds to each word: length, first, firsttwo, jumbled, pangram, perfectpangram

Never modifies words.xml.
"""

import os
import xml.etree.ElementTree as ET
from uuid import uuid4
import random
from collections import Counter

WORDS_XML = "xml/words.xml"
PUZZLES_XML = "xml/puzzles.xml"

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
    base = date_str.replace("-", "")  # YYYYMMDD
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
    added = Counter()
    text = word_el.text.strip().upper() if word_el.text else ""
    word_el.text = text
    if not text:
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

    if letterset:
        wordset = set(text)
        if wordset >= letterset and "pangram" not in word_el.attrib:
            word_el.set("pangram", "yes")
            added["pangram"] += 1
            if len(text) == 7 and wordset == letterset and "perfectpangram" not in word_el.attrib:
                word_el.set("perfectpangram", "yes")
                added["perfectpangram"] += 1

    return added

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
    id_added = False
    count_added = False
    letters_added = False
    lettercounts_added = False
    pangrams_added = False
    perfects_added = False

    word_attr_counts = Counter()

    if "id" not in puzzle.attrib:
        date = puzzle.attrib.get("date", "unknown")
        new_id = generate_id(date, existing_ids)
        puzzle.set("id", new_id)
        existing_ids.add(new_id)
        id_added = True

    # Letters
    letterset = None
    if "letters" not in puzzle.attrib:
        words = [w_el.text.strip().upper() for w_el in puzzle.findall("word") if w_el.text]
        letters = get_letters_from_words(words)
        if letters and len(letters) == 7:
            puzzle.set("letters", letters)
            letters_added = True

    if "letters" in puzzle.attrib:
        letterset = set(puzzle.attrib["letters"])

    # Word attributes
    for word_el in puzzle.findall("word"):
        updates = add_word_attributes(word_el, letterset)
        word_attr_counts.update(updates)

    # Count
    if "count" not in puzzle.attrib:
        puzzle.set("count", str(len(puzzle.findall("word"))))
        count_added = True

    # letter1–7 and counts
    if "letters" in puzzle.attrib:
        letters = puzzle.attrib["letters"]
        if all(f"letter{i+1}" not in puzzle.attrib for i in range(7)):
            starts = {ch: 0 for ch in letters}
            for w_el in puzzle.findall("word"):
                first = w_el.attrib.get("first")
                if first in starts:
                    starts[first] += 1
            for i, ch in enumerate(letters):
                puzzle.set(f"letter{i+1}", ch)
                puzzle.set(f"letter{i+1}count", str(starts[ch]))
            lettercounts_added = True

    # Puzzle-level pangram counts
    if "letters" in puzzle.attrib and (
        "pangrams" not in puzzle.attrib or "perfectpangrams" not in puzzle.attrib
    ):
        pgram_count = 0
        perfect_count = 0
        for w_el in puzzle.findall("word"):
            if w_el.attrib.get("pangram") == "yes":
                pgram_count += 1
            if w_el.attrib.get("perfectpangram") == "yes":
                perfect_count += 1
        if "pangrams" not in puzzle.attrib:
            puzzle.set("pangrams", str(pgram_count))
            pangrams_added = True
        if "perfectpangrams" not in puzzle.attrib:
            puzzle.set("perfectpangrams", str(perfect_count))
            perfects_added = True

    return (
        id_added, count_added, word_attr_counts,
        letters_added, lettercounts_added,
        pangrams_added, perfects_added
    )

def wax():
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

    added_puzzles = 0
    added_ids = 0
    added_counts = 0
    added_letters = 0
    added_lettercounts = 0
    added_pangrams = 0
    added_perfects = 0
    word_attr_totals = Counter()

    seen_dates = set()

    for puzzle in words_root.findall("puzzle"):
        date = puzzle.attrib.get("date")
        if not date or date in existing_dates or date in seen_dates:
            continue
        seen_dates.add(date)

        new_puzzle = ET.Element("puzzle", attrib=dict(puzzle.attrib))
        for word_el in puzzle.findall("word"):
            new_word = ET.Element("word")
            new_word.text = word_el.text.strip().upper()
            new_puzzle.append(new_word)

        puzzles_root.append(new_puzzle)
        added_puzzles += 1

    # Process all puzzles
    for puzzle in puzzles_root.findall("puzzle"):
        result = update_puzzle_metadata(puzzle, existing_ids)
        id_added, count_added, word_attr_added, letters_added, lettercounts_added, pangrams_added, perfects_added = result
        if id_added: added_ids += 1
        if count_added: added_counts += 1
        if letters_added: added_letters += 1
        if lettercounts_added: added_lettercounts += 1
        if pangrams_added: added_pangrams += 1
        if perfects_added: added_perfects += 1
        word_attr_totals.update(word_attr_added)

    indent(puzzles_root)
    puzzles_tree.write(PUZZLES_XML, encoding="utf-8", xml_declaration=True)

    print("🕯 Wax complete.")
    print(f"➕ New puzzles added:         {added_puzzles}")
    print(f"🆔 Puzzle IDs added:          {added_ids}")
    print(f"#️⃣ Word counts added:        {added_counts}")
    print(f"🔤 Letters strings added:     {added_letters}")
    print(f"🔢 Letter counts added:       {added_lettercounts}")
    print(f"🥚 Pangram counts added:      {added_pangrams}")
    print(f"💎 Perfect pangrams added:    {added_perfects}")
    print(f"🔠 Word attributes newly added:")
    for key in ["length", "first", "firsttwo", "jumbled", "pangram", "perfectpangram"]:
        print(f"    {key}: {word_attr_totals[key]}")

if __name__ == "__main__":
    wax()
