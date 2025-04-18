#!/usr/bin/env python3
# -------------------------------------------------------------------
# 🐝 BEE PLUS BUILDER – builder.py (v3.1)
#
# Consolidates puzzles from `xml/bees.xml` into a single
# `xml/beesplus.xml` archive. For each puzzle:
#   • Reformats date to "Month DD, YYYY"
#   • Copies attributes: url, puzzleid, letters
#   • Copies <letter1> through <letter7> elements
#   • Wraps all word entries under a single <words> element
#   • Each <word> has attributes:
#       original (uppercase), scrambled, startletter, firsttwo, length
# Puzzles are sorted chronologically; the most recent puzzle is marked with
# subscribersonly="yes".
#
# Input:
#   xml/bees.xml
# Output:
#   xml/beesplus.xml
#
# Usage:
#   python builder.py
#
# Dependencies:
#   Python 3.x standard library
# -------------------------------------------------------------------

import os
import xml.etree.ElementTree as ET
import random
from datetime import datetime

# Ensure xml directory exists
os.makedirs("xml", exist_ok=True)

INPUT_FILE  = os.path.join("xml", "bees.xml")
OUTPUT_FILE = os.path.join("xml", "beesplus.xml")


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
        if not elem.text or not elem.text.strip():
            elem.text = ''
        if not elem.tail or not elem.tail.strip():
            elem.tail = i


def scramble_word(word):
    word = word.upper()
    if len(word) <= 1:
        return word
    scrambled = word
    attempts = 0
    while scrambled == word and attempts < 10:
        chars = list(word)
        random.shuffle(chars)
        scrambled = ''.join(chars)
        attempts += 1
    if scrambled == word:
        scrambled = word[::-1]
    return scrambled


def build_beeplus():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Source file {INPUT_FILE} not found.")
        return

    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    plus_root = ET.Element("bees")

    for puzzle in root.findall("puzzle"):
        # Reformat date
        date_str = puzzle.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            formatted = dt.strftime("%B %d, %Y")
        except:
            formatted = date_str

        # Puzzle attributes
        attrs = {
            "date": formatted,
            "url": puzzle.get("url", ""),
            "puzzleid": puzzle.get("puzzleid", ""),
            "letters": puzzle.get("letters", "")
        }
        new_puz = ET.SubElement(plus_root, "puzzle", attrs)

        # Copy letter1..letter7
        for i in range(1, 8):
            tag = f"letter{i}"
            orig = puzzle.find(tag)
            if orig is not None and orig.text:
                el = ET.SubElement(new_puz, tag)
                el.text = orig.text

        # Words container
        words_el = ET.SubElement(new_puz, "words")
        for w in puzzle.findall("word"):
            txt       = (w.text or "").upper().strip()
            start     = txt[:1]
            firsttwo  = txt[:2]
            length    = str(len(txt))
            scrambled = scramble_word(txt)

            word_attrs = {
                "original":    txt,
                "scrambled":   scrambled,
                "startletter": start,
                "firsttwo":    firsttwo,
                "length":      length
            }
            ET.SubElement(words_el, "word", word_attrs)

    # Sort puzzles chronologically by parsed date
    def iso_key(p):
        d = p.get("date", "")
        try:
            return datetime.strptime(d, "%B %d, %Y")
        except:
            return datetime.min
    plus_root[:] = sorted(plus_root, key=iso_key)

    # Mark the latest puzzle
    if len(plus_root):
        for p in plus_root:
            p.attrib.pop("subscribersonly", None)
        plus_root[-1].set("subscribersonly", "yes")

    indent(plus_root)
    ET.ElementTree(plus_root).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ '{OUTPUT_FILE}' created.")

if __name__ == "__main__":
    build_beeplus()
