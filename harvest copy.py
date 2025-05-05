#!/usr/bin/env python3
"""
🐝 Harvest – harvest.py

Reads new puzzles from words.xml and:
- If puzzle with same date exists in puzzles.xml and has no words, inserts them (keeping the existing ID)
- If puzzle with that date doesn’t exist, adds it
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime

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

def get_existing_puzzles_by_date(root):
    return {p.attrib.get("date"): p for p in root.findall("puzzle") if "date" in p.attrib}

def insert_words_into_existing_puzzle(puzzle, word_list):
    if puzzle.findall("word"):
        return False  # already filled

    for word_el in puzzle.findall("word"):
        puzzle.remove(word_el)

    for word in word_list:
        el = ET.Element("word")
        el.text = word.strip().upper()
        puzzle.append(el)

    if puzzle.attrib.get("status") == "placeholder":
        del puzzle.attrib["status"]

    return True

def harvest():
    if not os.path.exists(WORDS_XML):
        raise FileNotFoundError(f"{WORDS_XML} not found.")

    words_tree = ET.parse(WORDS_XML)
    words_root = words_tree.getroot()

    if os.path.exists(PUZZLES_XML):
        puzzles_tree = ET.parse(PUZZLES_XML)
        puzzles_root = puzzles_tree.getroot()
    else:
        puzzles_root = ET.Element("puzzles")
        puzzles_tree = ET.ElementTree(puzzles_root)

    existing_by_date = get_existing_puzzles_by_date(puzzles_root)
    added = 0
    updated = 0
    skipped = 0

    for new_puzzle in words_root.findall("puzzle"):
        date = new_puzzle.attrib.get("date")
        if not date:
            continue

        words = [w_el.text.strip().upper() for w_el in new_puzzle.findall("word") if w_el.text and w_el.text.strip()]
        if not words:
            skipped += 1
            continue

        if date in existing_by_date:
            existing_puzzle = existing_by_date[date]
            if insert_words_into_existing_puzzle(existing_puzzle, words):
                updated += 1
            else:
                skipped += 1
        else:
            # Add new puzzle with just date and words
            new_el = ET.Element("puzzle", attrib={"date": date})
            for word in words:
                word_el = ET.Element("word")
                word_el.text = word
                new_el.append(word_el)
            puzzles_root.append(new_el)
            added += 1

    indent(puzzles_root)
    puzzles_tree.write(PUZZLES_XML, encoding="utf-8", xml_declaration=True)

    print("🌱 Harvest complete.")
    print(f"➕ Puzzles added:   {added}")
    print(f"✏️  Placeholders filled: {updated}")
    print(f"⏭  Puzzles skipped (already filled or no words): {skipped}")

if __name__ == "__main__":
    harvest()
