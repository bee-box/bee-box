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
    """
    Load dates of puzzles already in the XML, to avoid duplicates.
    """
    if not os.path.exists(XML_FILE):
        return set()
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return {p.attrib.get("date") for p in root.findall("puzzle")}


def fetch_puzzle():
    """
    Scrape NYT Spelling Bee page for embedded JSON, extract the puzzle's
    printDate and answers list.
    Returns:
      tuple(date_str (YYYY-MM-DD), list of words)
    """
    resp = requests.get(NYT_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the <script> containing window.gameData
    script = next(
        (s.string for s in soup.find_all("script")
         if s.string and "window.gameData" in s.string),
        None
    )
    if not script:
        raise RuntimeError("Cannot find gameData in page source.")

    # Extract the JSON object from the script text
    start = script.find("{")
    brace_count = 0
    for i in range(start, len(script)):
        if script[i] == '{':
            brace_count += 1
        elif script[i] == '}':
            brace_count -= 1
        if brace_count == 0:
            json_str = script[start:i+1]
            break

    data = json.loads(json_str)
    today = data.get("today", {})

    # NYT's printDate is in "YYYY/MM/DD" format
    raw_date = today.get("printDate")  # e.g. "2025/04/17"
    if raw_date:
        date_str = raw_date.replace("/", "-")
    else:
        date_str = date.today().strftime("%Y-%m-%d")

    answers = today.get("answers", [])
    return date_str, [w.upper() for w in answers]


def indent(elem, level=0):
    """
    Helper to pretty-print XML by adding indentation.
    """
    indent_str = "\n" + "  " * level
    child_indent = "\n" + "  " * (level + 1)
    if list(elem):
        if not elem.text or not elem.text.strip():
            elem.text = child_indent
        for idx, child in enumerate(elem):
            indent(child, level + 1)
            if idx < len(elem) - 1:
                child.tail = child_indent
            else:
                child.tail = indent_str
    else:
        if not elem.text or not elem.text.strip():
            elem.text = ''
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent_str


def append_puzzle(date_str, words):
    """
    Append a <puzzle date="..."> block with <word> children to the XML.
    """
    # Load or initialize XML tree
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element("words")
        tree = ET.ElementTree(root)

    # Create and populate the puzzle element
    puzzle_el = ET.SubElement(root, "puzzle", date=date_str)
    for w in words:
        word_el = ET.SubElement(puzzle_el, "word")
        word_el.text = w

    # Pretty-print and write back
    indent(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)


def main():
    date_str, words = fetch_puzzle()
    existing = load_existing_dates()
    if date_str in existing:
        print(f"Puzzle for {date_str} already exists. No action taken.")
        return

    if not words:
        print(f"No words fetched for {date_str}.")
        return

    append_puzzle(date_str, words)
    print(f"Appended puzzle for {date_str} with {len(words)} words.")


if __name__ == "__main__":
    main()
