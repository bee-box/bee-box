#!/usr/bin/env python3
"""
🐝 Spelling Bee Puller – puller.py

Fetches today's NYT Spelling Bee puzzle (date + words only) and
appends it to `xml/words.xml` if that date isn't already present.
Each element is placed on its own line for readability; no length
attributes are added.
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import date

# Configuration
os.makedirs("xml", exist_ok=True)
XML_FILE = os.path.join("xml", "words.xml")
NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"


def load_existing_dates():
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}


def fetch_today_words():
    resp = requests.get(NYT_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Locate embedded JSON containing game data
    script = next(
        (s.string for s in soup.find_all("script")
         if s.string and "window.gameData" in s.string),
        None
    )
    if not script:
        raise RuntimeError("Cannot find gameData in page")

    start = script.find("{")
    count = 0
    for i in range(start, len(script)):
        if script[i] == '{':
            count += 1
        elif script[i] == '}':
            count -= 1
        if count == 0:
            json_str = script[start:i+1]
            break

    data = json.loads(json_str)
    answers = data.get("today", {}).get("answers", [])
    return [w.upper() for w in answers]


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


def append_puzzle(date_str, words):
    # Load or create XML root
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("spelling_bees")
        tree = ET.ElementTree(root)

    # Create puzzle element
    puzzle_el = ET.SubElement(root, "puzzle", date=date_str)
    for w in words:
        ET.SubElement(
            puzzle_el,
            "word"
        ).text = w

    # Pretty-print and save
    indent(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)


def main():
    date_str = date.today().strftime("%Y-%m-%d")
    existing = load_existing_dates()
    if date_str in existing:
        print(f"Puzzle for {date_str} already exists. No action taken.")
        return

    words = fetch_today_words()
    if not words:
        print(f"No words fetched for {date_str}.")
        return

    append_puzzle(date_str, words)
    print(f"Appended puzzle for {date_str} with {len(words)} words.")


if __name__ == "__main__":
    main()
