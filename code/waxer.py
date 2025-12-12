#!/usr/bin/env python3
"""
🏈 Waxer – waxer.py (newest 5 only)

Processes Spelling Bee puzzles:
- Only processes the newest 5 puzzles from words.xml
- Fills placeholders and preserves IDs
- Appends blank puzzles through Jan 3 of next year
- Logs all activity to log/log.txt with New Orleans timestamps
"""

import os
from datetime import date, timedelta, datetime
import xml.etree.ElementTree as ET
from uuid import uuid4
import random
from collections import Counter
import pytz  # Added for timezone support

# Constants for file paths
WORDS_XML = "xml/words.xml"
PUZZLES_XML = "xml/puzzles.xml"
LOG_FILE = "log/log.txt"

# Create necessary directories if they don't exist
os.makedirs("xml", exist_ok=True)
os.makedirs("log", exist_ok=True)

def log(message):
    """
    Logs a message with a timestamp in New Orleans time zone.
    
    Args:
        message (str): The message to log
    """
    # Get current time in New Orleans timezone (America/Chicago)
    new_orleans_tz = pytz.timezone('America/Chicago')
    # Get current time in UTC and convert to New Orleans time
    current_time = datetime.now(pytz.utc).astimezone(new_orleans_tz)
    # Format timestamp with New Orleans time
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    
    # Print to console (with error handling for emoji characters)
    try:
        print(full_msg)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        print(full_msg.encode('ascii', 'replace').decode('ascii'))
    
    # Write to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def indent(elem, level=0):
    """
    Properly indents an XML ElementTree element for pretty printing.
    
    Args:
        elem (Element): The XML element to indent
        level (int): The current indentation level
    """
    i = "\n" + "  " * level
    j = "\n" + "  " * (level + 1)
    
    if len(elem):  # If element has children
        if not elem.text or not elem.text.strip():
            elem.text = j  # Add indentation before first child
        
        # Process all children
        for idx, child in enumerate(elem):
            indent(child, level + 1)  # Recursively indent children
            # Add appropriate indentation after each child
            child.tail = j if idx < len(elem) - 1 else i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i  # Add indentation after element

def get_puzzle_dates(root):
    """
    Extracts all puzzle dates from the XML root.
    
    Args:
        root (Element): The XML root element
    
    Returns:
        set: A set of date strings for all puzzles
    """
    return {p.attrib.get("date") for p in root.findall("puzzle")}

def get_existing_ids(root):
    """
    Extracts all existing puzzle IDs from the XML root.
    
    Args:
        root (Element): The XML root element
    
    Returns:
        set: A set of ID strings for all puzzles with IDs
    """
    return {p.attrib.get("id") for p in root.findall("puzzle") if "id" in p.attrib}

def generate_id(date_str, existing_ids):
    """
    Generates a unique ID for a puzzle based on date and random suffix.
    
    Args:
        date_str (str): The date string in ISO format
        existing_ids (set): Set of existing IDs to avoid duplicates
    
    Returns:
        str: A new unique ID
    """
    # Create base ID from date by removing hyphens
    base = date_str.replace("-", "")
    
    # Keep generating IDs until a unique one is found
    while True:
        # Generate a random 6-character hex suffix
        suffix = uuid4().hex[:6]
        new_id = f"{base}-{suffix}"
        
        # Check if ID is unique
        if new_id not in existing_ids:
            return new_id

def generate_jumble(word):
    """
    Generates a randomized jumble of a word.
    
    Args:
        word (str): The word to jumble
    
    Returns:
        str: The jumbled word
    """
    if len(word) < 2:
        return word  # Can't jumble a single character
    
    chars = list(word)
    attempts = 0
    
    # Try up to 10 times to get a different arrangement
    while attempts < 10:
        random.shuffle(chars)
        jumbled = ''.join(chars)
        
        # Return if successful jumble (different from original)
        if jumbled != word:
            return jumbled
        attempts += 1
    
    # If shuffle didn't work after 10 attempts, reverse the word
    # (but check that reversed isn't same as original, e.g. for palindromes)
    return word[::-1] if word[::-1] != word else word

def add_word_attributes(word_el, letterset=None):
    """
    Adds metadata attributes to a word element.
    
    Args:
        word_el (Element): The word XML element
        letterset (set, optional): Set of required letters for pangram checking
    """
    # Normalize word text to uppercase
    text = word_el.text.strip().upper() if word_el.text else ""
    word_el.text = text
    
    if not text:
        return  # Skip empty words
    
    # Set basic attributes
    word_el.set("length", str(len(text)))
    word_el.set("first", text[0])  # First letter
    word_el.set("firsttwo", text[:2])  # First two letters
    word_el.set("jumbled", generate_jumble(text))  # Jumbled version
    
    # Check if word is a pangram (contains all required letters)
    pangram = False
    if letterset:
        wordset = set(text)
        if wordset >= letterset:
            pangram = True
            word_el.set("pangram", "yes")
            
            # Check for perfect pangram (uses exactly the 7 required letters)
            if len(text) == 7 and wordset == letterset:
                word_el.set("perfectpangram", "yes")
    
    # Calculate points
    # 1 point for 4-letter words, otherwise 1 point per letter
    base_points = 1 if len(text) == 4 else len(text)
    
    # Add 7 bonus points for pangrams
    if pangram:
        base_points += 7
        
    word_el.set("points", str(base_points))

def get_letters_from_words(words):
    """
    Determines the set of required letters from a list of words.
    
    Args:
        words (list): List of words
    
    Returns:
        str: String of required letters, first letter followed by others
    """
    # Create set of letters for each word
    sets = [set(w) for w in words]
    
    if not sets:
        return ""
    
    # Find letters common to all words
    common = sorted(set.intersection(*sets))
    
    if not common:
        return ""
    
    # First letter is the required center letter
    first = common[0]
    
    # Get all unique letters from all words
    all_letters = set("".join(words))
    
    # The remaining letters (excluding the center letter)
    rest = sorted(all_letters - {first})
    
    # Return center letter followed by remaining letters
    return first + ''.join(rest)

def update_puzzle_metadata(puzzle, existing_ids):
    """
    Updates all metadata for a puzzle based on its words.
    
    Args:
        puzzle (Element): The puzzle XML element
        existing_ids (set): Set of existing IDs
    """
    # Generate ID if missing
    if "id" not in puzzle.attrib:
        date_str = puzzle.attrib.get("date", "unknown")
        new_id = generate_id(date_str, existing_ids)
        puzzle.set("id", new_id)
        existing_ids.add(new_id)
    
    # Extract words from puzzle
    words = [w_el.text.strip().upper() for w_el in puzzle.findall("word") if w_el.text]
    
    if not words:
        return  # Skip empty puzzles
    
    # Set word count
    puzzle.set("count", str(len(words)))
    
    # Generate letters attribute if missing
    if "letters" not in puzzle.attrib:
        letters = get_letters_from_words(words)
        if letters and len(letters) == 7:  # Valid if 7 letters
            puzzle.set("letters", letters)
    
    # Get the set of required letters
    letterset = set(puzzle.attrib["letters"]) if "letters" in puzzle.attrib else None
    
    # Update attributes for each word
    for word_el in puzzle.findall("word"):
        add_word_attributes(word_el, letterset)
    
    # Set additional metadata if letters are known
    if "letters" in puzzle.attrib:
        letters = puzzle.attrib["letters"]
        
        # Count words starting with each letter
        starts = {ch: 0 for ch in letters}
        for w_el in puzzle.findall("word"):
            first = w_el.attrib.get("first")
            if first in starts:
                starts[first] += 1
        
        # Set letter attributes
        for i, ch in enumerate(letters):
            puzzle.set(f"letter{i+1}", ch)
            puzzle.set(f"letter{i+1}count", str(starts[ch]))
        
        # Count pangrams and perfect pangrams
        pgram_count = sum(1 for w in puzzle.findall("word") if w.attrib.get("pangram") == "yes")
        perfect_count = sum(1 for w in puzzle.findall("word") if w.attrib.get("perfectpangram") == "yes")
        puzzle.set("pangrams", str(pgram_count))
        puzzle.set("perfectpangrams", str(perfect_count))
    
    # Calculate total points (Queen Bee score)
    total = sum(int(w.attrib.get("points", "0")) for w in puzzle.findall("word"))
    puzzle.set("queenbee", str(total))
    
    # Set BINGO attribute if there are words starting with each letter
    if "letters" in puzzle.attrib:
        letters = puzzle.attrib["letters"]
        starts = {ch: 0 for ch in letters}
        for w_el in puzzle.findall("word"):
            first = w_el.attrib.get("first")
            if first in starts:
                starts[first] += 1
        # "BINGO" if there's at least one word starting with each letter
        puzzle.set("bingo", "BINGO" if all(starts[ch] > 0 for ch in letters) else "")

def wax():
    """
    Main function that processes word puzzles:
    - Takes newest 5 puzzles from words.xml
    - Updates puzzles.xml with new data
    - Fills placeholder puzzles
    - Adds new placeholders for future dates
    """
    log("🕯 Starting waxer process...")
    
    # Check if words.xml exists
    if not os.path.exists("xml/words.xml"):
        log("❌ words.xml not found.")
        return
    
    # Parse words.xml
    words_root = ET.parse("xml/words.xml").getroot()
    
    # Get the newest 5 puzzles, sorted by date
    puzzles = sorted(words_root.findall("puzzle"), 
                    key=lambda p: p.attrib.get("date", ""), 
                    reverse=True)[:5]
    
    # Load or create puzzles.xml
    if os.path.exists("xml/puzzles.xml"):
        puzzles_tree = ET.parse("xml/puzzles.xml")
        puzzles_root = puzzles_tree.getroot()
    else:
        puzzles_root = ET.Element("puzzles")
        puzzles_tree = ET.ElementTree(puzzles_root)
    
    # Get existing IDs and puzzles
    existing_ids = get_existing_ids(puzzles_root)
    existing_puzzles = {p.attrib.get("date"): p for p in puzzles_root.findall("puzzle")}
    
    # Process each of the 5 newest puzzles
    for puzzle in puzzles:
        date_str = puzzle.attrib.get("date")
        if not date_str:
            continue
        
        # Check if puzzle already exists for this date
        existing = existing_puzzles.get(date_str)
        if existing is not None:
            # Check if it's a placeholder (no word elements)
            is_placeholder = not any(child.tag == "word" for child in existing)
            
            if is_placeholder:
                # Fill the placeholder with real data
                preserved_id = existing.attrib.get("id")
                existing.attrib.clear()
                existing.attrib.update(puzzle.attrib)
                existing.set("id", preserved_id)  # Keep original ID
                existing[:] = []  # Clear all children
                
                # Add words
                for word_el in puzzle.findall("word"):
                    new_word = ET.Element("word")
                    new_word.text = word_el.text.strip().upper()
                    existing.append(new_word)
                
                log(f"🔄 Filled placeholder puzzle for {date_str}.")
            else:
                log(f"⚠️ Puzzle for {date_str} already populated. Skipping.")
        else:
            # Create a new puzzle element
            new_puzzle = ET.Element("puzzle", attrib=dict(puzzle.attrib))
            
            # Add words to the new puzzle
            for word_el in puzzle.findall("word"):
                new_word = ET.Element("word")
                new_word.text = word_el.text.strip().upper()
                new_puzzle.append(new_word)
            
            # Add to puzzles root
            puzzles_root.append(new_puzzle)
            log(f"➕ Added new puzzle for {date_str}.")
    
    # Get dates of all existing puzzles
    existing_dates = get_puzzle_dates(puzzles_root)
    
    # Calculate date range for placeholders
    today = date.today()
    end_date = date(today.year, 12, 31) + timedelta(days=95)  # Through ~April 5 of next year
    
    # Add placeholders for missing dates
    for delta in range((end_date - today).days + 1):
        target_date = today + timedelta(days=delta)
        target_str = target_date.isoformat()
        
        # Only add if date doesn't exist yet
        if target_str not in existing_dates:
            new_puzzle = ET.Element("puzzle", attrib={"date": target_str})
            new_id = generate_id(target_str, existing_ids)
            new_puzzle.set("id", new_id)
            new_puzzle.text = "\n"  # Ensure proper formatting
            
            puzzles_root.append(new_puzzle)
            log(f"➕ Added placeholder puzzle for {target_str}.")
            existing_dates.add(target_str)
    
    # Update metadata for all puzzles
    for puzzle in puzzles_root.findall("puzzle"):
        # Skip placeholders with IDs (they don't need metadata updates)
        if not puzzle.findall("word") and "id" in puzzle.attrib:
            continue
        
        update_puzzle_metadata(puzzle, existing_ids)
    
    # Apply proper indentation
    indent(puzzles_root)
    
    # Write updated XML to file
    puzzles_tree.write("xml/puzzles.xml", encoding="utf-8", xml_declaration=True)
    
    log("✅ Wax complete.")

if __name__ == "__main__":
    wax()