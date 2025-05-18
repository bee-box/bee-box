#!/usr/bin/env python3
"""
🏈 Waxer – waxer.py (newest 5 only)

Processes Spelling Bee puzzles:
- Only processes the newest 5 puzzles from words.xml
- Fills placeholders and preserves IDs
- Appends blank puzzles through Jan 3 of next year
- Logs minimal information: start time, success/failure, end time
"""

import os
import sys
import traceback
from datetime import date, timedelta, datetime
import xml.etree.ElementTree as ET
from uuid import uuid4
import random
from collections import Counter
import pytz  # Added for timezone support

# Base directories - use absolute paths for GitHub Actions
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
XML_DIR = os.path.join(SCRIPT_DIR, "xml")
LOG_DIR = os.path.join(SCRIPT_DIR, "log")

# Specific files
WORDS_XML = os.path.join(XML_DIR, "words.xml")
PUZZLES_XML = os.path.join(XML_DIR, "puzzles.xml")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

# Create necessary directories if they don't exist
os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ───────────────────────────────────────────────────────────────────────────────
# ─── SIMPLE LOGGING ────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def get_timestamp():
    """Get current timestamp in New Orleans timezone with 12-hour format"""
    # New Orleans timezone - handles DST automatically
    nola_timezone = pytz.timezone('America/Chicago')  # Central Time Zone for New Orleans
    
    utc_now = datetime.now(pytz.utc)
    nola_now = utc_now.astimezone(nola_timezone)
    return nola_now.strftime('%Y-%m-%d %I:%M:%S %p %Z')  # 12-hour format with AM/PM

def log_simple(message, status="INFO"):
    """
    Write a simple log entry with timestamp
    """
    timestamp = get_timestamp()
    
    try:
        # Check if the log file exists
        file_exists = os.path.exists(LOG_FILE)
        
        # Open in append mode, but if the file doesn't exist, we'll add headers first
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            # Write headers if creating a new file
            if not file_exists:
                f.write("TIMESTAMP,STATUS,MESSAGE\n")
            
            # Append the log entry
            f.write(f"{timestamp},{status},\"{message}\"\n")
            
        # Also print to stdout for GitHub Actions logs
        print(f"{timestamp} [{status}] {message}")
    except Exception as e:
        # If logging fails, print to stderr
        print(f"ERROR: Failed to write to log file: {e}", file=sys.stderr)

# ───────────────────────────────────────────────────────────────────────────────
# ─── XML PROCESSING FUNCTIONS ────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def fix_xml_file(file_path):
    """
    Attempts to fix common XML syntax errors in a file.
    
    Args:
        file_path (str): Path to the XML file to fix
        
    Returns:
        bool: True if file was fixed or is already valid, False on failure
    """
    try:
        log_simple(f"Checking XML file: {file_path}", "INFO")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # First check if it's already valid XML
        try:
            ET.fromstring(content)
            log_simple(f"XML file is already valid: {file_path}", "INFO")
            return True
        except Exception as parse_error:
            log_simple(f"XML syntax error detected: {str(parse_error)}", "INFO")
        
        # Common XML fixes:
        
        # 1. Check if there's a UTF-8 BOM and remove it
        if content.startswith('\ufeff'):
            log_simple("Removing UTF-8 BOM from file", "INFO")
            content = content[1:]
        
        # 2. Ensure there's a proper XML declaration
        if not content.strip().startswith('<?xml'):
            log_simple("Adding XML declaration", "INFO")
            content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
        
        # 3. Check if root element is missing
        root_tags = ['<puzzles>', '<words>']
        root_found = any(tag in content for tag in root_tags)
        if not root_found:
            log_simple("Adding root element", "INFO")
            content = '<?xml version="1.0" encoding="UTF-8"?>\n<puzzles>\n' + content + '\n</puzzles>'
        
        # 4. Fix unclosed tags (this is a basic heuristic)
        # For each opening tag, ensure there's a corresponding closing tag
        if '<puzzle' in content and '</puzzle>' not in content:
            log_simple("Adding missing </puzzle> tags", "INFO")
            content = content.replace('<puzzle', '</puzzle>\n<puzzle')
            content = content.replace('</puzzle>\n<puzzle', '<puzzle', 1)  # Fix first occurrence
            if not content.rstrip().endswith('</puzzle>'):
                content += '\n</puzzle>'
        
        # 5. Fix malformed attribute quotes
        if '=" ' in content:
            log_simple("Fixing malformed attribute quotes", "INFO")
            content = content.replace('=" ', '="')
        
        # 6. Remove any invalid characters
        for char in ['&', '<', '>', '"', "'", '\ufeff']:
            if f"&{char};" not in content and char in content[content.find('>')+1:]:
                log_simple(f"Escaping invalid character: {char}", "INFO")
                valid_replacement = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&apos;'
                }.get(char, '')
                if valid_replacement:
                    # Only replace within text content, not in tags
                    in_tag = False
                    fixed_content = []
                    for i, c in enumerate(content):
                        if c == '<':
                            in_tag = True
                        elif c == '>':
                            in_tag = False
                        
                        if not in_tag and c == char:
                            fixed_content.append(valid_replacement)
                        else:
                            fixed_content.append(c)
                    
                    content = ''.join(fixed_content)
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Verify the file is now valid XML
        try:
            ET.parse(file_path)
            log_simple(f"Successfully fixed XML file: {file_path}", "INFO")
            return True
        except Exception as final_error:
            log_simple(f"Failed to fix XML: {str(final_error)}", "FAILURE")
            return False
            
    except Exception as e:
        log_simple(f"Error trying to fix XML file: {str(e)}", "FAILURE")
        return False

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

def create_default_words_xml():
    """
    Creates a default words.xml file if it doesn't exist.
    
    Returns:
        bool: True if file was created or already exists, False on failure
    """
    try:
        if os.path.exists(WORDS_XML):
            return True
            
        log_simple("Creating default words.xml file", "INFO")
        
        # Create a simple valid XML structure
        root = ET.Element("words")
        
        # Add a comment explaining the file purpose
        comment = ET.Comment(" This is a placeholder words.xml file. Replace with actual data. ")
        root.append(comment)
        
        # Create a sample puzzle
        today = date.today()
        puzzle = ET.SubElement(root, "puzzle", {"date": today.isoformat()})
        
        # Add some sample words
        sample_words = ["SAMPLE", "EXAMPLE", "TEST"]
        for word in sample_words:
            word_el = ET.SubElement(puzzle, "word")
            word_el.text = word
        
        # Apply proper indentation
        indent(root)
        
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(WORDS_XML, encoding="utf-8", xml_declaration=True)
        
        return os.path.exists(WORDS_XML)
    except Exception as e:
        log_simple(f"Error creating default words.xml: {str(e)}", "FAILURE")
        return False

def print_xml_file_preview(file_path, lines=10):
    """
    Prints a preview of an XML file for debugging
    
    Args:
        file_path (str): Path to the XML file
        lines (int): Number of lines to preview
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                
            preview = content[:min(lines, len(content))]
            log_simple(f"Preview of {file_path} (first {len(preview)} lines):", "INFO")
            for i, line in enumerate(preview):
                log_simple(f"Line {i+1}: {line.rstrip()}", "INFO")
        else:
            log_simple(f"File doesn't exist: {file_path}", "INFO")
    except Exception as e:
        log_simple(f"Error previewing file: {str(e)}", "INFO")

def wax():
    """
    Main function that processes word puzzles:
    - Takes newest 5 puzzles from words.xml
    - Updates puzzles.xml with new data
    - Fills placeholder puzzles
    - Adds new placeholders for future dates
    """
    log_simple("Waxer process started", "START")
    
    # Check environment
    log_simple(f"Running in directory: {os.getcwd()}", "INFO")
    log_simple(f"Script directory: {SCRIPT_DIR}", "INFO")
    log_simple(f"Looking for words.xml at: {WORDS_XML}", "INFO")
    
    # List files in xml directory to debug
    try:
        if os.path.exists(XML_DIR):
            files = os.listdir(XML_DIR)
            log_simple(f"Files in xml directory: {', '.join(files)}", "INFO")
        else:
            log_simple("xml directory does not exist yet", "INFO")
    except Exception as e:
        log_simple(f"Error listing xml directory: {str(e)}", "INFO")
    
    # Check if words.xml exists
    if not os.path.exists(WORDS_XML):
        log_simple("words.xml not found - creating default file", "INFO")
        if not create_default_words_xml():
            log_simple("Failed to create default words.xml file", "FAILURE")
            return False
    
    # Check file size
    if os.path.getsize(WORDS_XML) == 0:
        log_simple("words.xml is empty - creating default file", "INFO")
        if not create_default_words_xml():
            log_simple("Failed to create default words.xml file", "FAILURE")
            return False
    
    # Preview the beginning of the file
    print_xml_file_preview(WORDS_XML)
    
    # Try to fix XML file if it has syntax errors
    if not fix_xml_file(WORDS_XML):
        log_simple("Unable to fix XML syntax in words.xml", "FAILURE")
        return False
    
    # Parse words.xml
    try:
        log_simple("Parsing words.xml file", "INFO")
        words_tree = ET.parse(WORDS_XML)
        words_root = words_tree.getroot()
        
        # If the root element is not 'words', create a wrapper
        if words_root.tag != 'words':
            log_simple(f"Root element is not 'words', it's '{words_root.tag}' - wrapping it", "INFO")
            new_root = ET.Element("words")
            new_root.append(words_root)
            words_root = new_root
            words_tree = ET.ElementTree(words_root)
            
            # Save the fixed file
            words_tree.write(WORDS_XML, encoding="utf-8", xml_declaration=True)
        
        # Count puzzles for debugging
        puzzle_count = len(words_root.findall("puzzle"))
        log_simple(f"Found {puzzle_count} puzzles in words.xml", "INFO")
        
        if puzzle_count == 0:
            log_simple("No puzzles found in words.xml - creating sample puzzles", "INFO")
            # Create a sample puzzle for today
            today = date.today()
            puzzle = ET.SubElement(words_root, "puzzle", {"date": today.isoformat()})
            
            # Add some sample words
            sample_words = ["SAMPLE", "EXAMPLE", "TEST", "PUZZLE", "WORDS", "BASIC", "SEVEN"]
            for word in sample_words:
                word_el = ET.SubElement(puzzle, "word")
                word_el.text = word
                
            # Save the file with sample puzzle
            indent(words_root)
            words_tree.write(WORDS_XML, encoding="utf-8", xml_declaration=True)
            
            # Update count
            puzzle_count = 1
            log_simple(f"Created sample puzzle for today: {today.isoformat()}", "INFO")
        
        # Get the newest 5 puzzles, sorted by date
        puzzles = sorted(words_root.findall("puzzle"), 
                        key=lambda p: p.attrib.get("date", ""), 
                        reverse=True)[:5]
        
        log_simple(f"Selected {len(puzzles)} newest puzzles for processing", "INFO")
        
        # Load or create puzzles.xml
        if os.path.exists(PUZZLES_XML):
            log_simple(f"Loading existing puzzles.xml at {PUZZLES_XML}", "INFO")
            try:
                # Try to fix puzzles.xml if it exists but might have syntax issues
                fix_xml_file(PUZZLES_XML)
                puzzles_tree = ET.parse(PUZZLES_XML)
                puzzles_root = puzzles_tree.getroot()
                log_simple(f"Found {len(puzzles_root.findall('puzzle'))} existing puzzles", "INFO")
            except Exception as e:
                log_simple(f"Error parsing puzzles.xml: {str(e)} - creating new file", "INFO")
                puzzles_root = ET.Element("puzzles")
                puzzles_tree = ET.ElementTree(puzzles_root)
        else:
            log_simple("Creating new puzzles.xml file", "INFO")
            puzzles_root = ET.Element("puzzles")
            puzzles_tree = ET.ElementTree(puzzles_root)
        
        # Get existing IDs and puzzles
        existing_ids = get_existing_ids(puzzles_root)
        existing_puzzles = {p.attrib.get("date"): p for p in puzzles_root.findall("puzzle")}
        
        # Process each of the 5 newest puzzles
        updated_count = 0
        for puzzle in puzzles:
            date_str = puzzle.attrib.get("date")
            if not date_str:
                log_simple(f"Skipping puzzle with no date attribute", "INFO")
                continue
            
            log_simple(f"Processing puzzle for date: {date_str}", "INFO")
            
            # Check if puzzle already exists for this date
            existing = existing_puzzles.get(date_str)
            if existing is not None:
                # Check if it's a placeholder (no word elements)
                is_placeholder = not any(child.tag == "word" for child in existing)
                
                if is_placeholder:
                    log_simple(f"Filling placeholder for date: {date_str}", "INFO")
                    # Fill the placeholder with real data
                    preserved_id = existing.attrib.get("id")
                    existing.attrib.clear()
                    existing.attrib.update(puzzle.attrib)
                    if preserved_id:
                        existing.set("id", preserved_id)  # Keep original ID
                    existing[:] = []  # Clear all children
                    
                    # Add words
                    word_count = 0
                    for word_el in puzzle.findall("word"):
                        new_word = ET.Element("word")
                        new_word.text = word_el.text.strip().upper() if word_el.text else ""
                        existing.append(new_word)
                        word_count += 1
                    
                    log_simple(f"Added {word_count} words to puzzle for date: {date_str}", "INFO")
                    updated_count += 1
                else:
                    log_simple(f"Puzzle for date {date_str} already exists and has words - skipping", "INFO")
            else:
                log_simple(f"Creating new puzzle for date: {date_str}", "INFO")
                # Create a new puzzle element
                new_puzzle = ET.Element("puzzle", attrib=dict(puzzle.attrib))
                
                # Add words to the new puzzle
                word_count = 0
                for word_el in puzzle.findall("word"):
                    new_word = ET.Element("word")
                    new_word.text = word_el.text.strip().upper() if word_el.text else ""
                    new_puzzle.append(new_word)
                    word_count += 1
                
                log_simple(f"Added {word_count} words to new puzzle for date: {date_str}", "INFO")
                
                # Add to puzzles root
                puzzles_root.append(new_puzzle)
                updated_count += 1
        
        log_simple(f"Updated {updated_count} puzzles with new data", "INFO")
        
        # Get dates of all existing puzzles
        existing_dates = get_puzzle_dates(puzzles_root)
        
        # Calculate date range for placeholders
        today = date.today()
        end_date = date(today.year, 12, 31) + timedelta(days=3)  # Through Jan 3 of next year
        
        # Add placeholders for missing dates
        placeholder_count = 0
        for delta in range((end_date - today).days + 1):
            target_date = today + timedelta(days=delta)
            target_str = target_date.isoformat()
            
            # Only add if date doesn't exist yet
            if target_str not in existing_dates:
                log_simple(f"Adding placeholder for future date: {target_str}", "INFO")
                new_puzzle = ET.Element("puzzle", attrib={"date": target_str})
                new_id = generate_id(target_str, existing_ids)
                new_puzzle.set("id", new_id)
                new_puzzle.text = "\n"  # Ensure proper formatting
                
                puzzles_root.append(new_puzzle)
                existing_dates.add(target_str)
                placeholder_count += 1
        
        log_simple(f"Added {placeholder_count} placeholders for future dates", "INFO")
        
        # Update metadata for all puzzles
        metadata_count = 0
        for puzzle in puzzles_root.findall("puzzle"):
            # Skip placeholders with IDs (they don't need metadata updates)
            if not puzzle.findall("word") and "id" in puzzle.attrib:
                continue
            
            date_str = puzzle.attrib.get("date", "unknown")
            log_simple(f"Updating metadata for puzzle date: {date_str}", "INFO")
            update_puzzle_metadata(puzzle, existing_ids)
            metadata_count += 1
        
        log_simple(f"Updated metadata for {metadata_count} puzzles", "INFO")
        
        # Apply proper indentation
        indent(puzzles_root)
        
        # Write updated XML to file
        log_simple(f"Writing updated puzzles to {PUZZLES_XML}", "INFO")
        puzzles_tree.write(PUZZLES_XML, encoding="utf-8", xml_declaration=True)
        
        # Verify file was written successfully
        if os.path.exists(PUZZLES_XML) and os.path.getsize(PUZZLES_XML) > 0:
            log_simple(f"Successfully wrote {os.path.getsize(PUZZLES_XML)} bytes to {PUZZLES_XML}", "INFO")
        else:
            log_simple(f"File write verification failed for {PUZZLES_XML}", "FAILURE")
            return False
        
        log_simple("Waxer process completed successfully", "SUCCESS")
        return True
        
    except Exception as e:
        # Get full traceback
        tb = traceback.format_exc()
        log_simple(f"Waxer process failed - unhandled exception: {str(e)}\n{tb}", "FAILURE")
        sys.exit(1) process failed - {str(e)}\n{tb}", "FAILURE")
        return False

if __name__ == "__main__":
    try:
        # Print environment info for debugging
        log_simple(f"Python version: {sys.version}", "INFO")
        log_simple(f"Current directory: {os.getcwd()}", "INFO")
        log_simple(f"Script path: {os.path.abspath(__file__)}", "INFO")
        
        # Run the main function
        success = wax()
        if not success:
            log_simple("Exiting with code 1 due to processing failure", "FAILURE")
            sys.exit(1)
    except Exception as e:
        tb = traceback.format_exc()
        log_simple(f"Waxer