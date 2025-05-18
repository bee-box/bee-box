#!/usr/bin/env python3
"""
Spelling Bee Harvester – harvest.py

This script:
- Scrapes today's New York Times Spelling Bee word list
- Saves it to xml/words.xml if the date isn't already present
- Always backs up words.xml to xml/backups/words.xml.bak
- Uses lxml for fast and clean XML handling
- Logs minimal information: start time, success/failure, end time

Author: Kevin Kolb
Last updated: May 13, 2025
"""

import os
import sys
import time
import json
import shutil
import requests
import pytz  # For timezone handling
from lxml import etree as ET
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta

# ───────────────────────────────────────────────────────────────────────────────
# ─── CONFIGURATION AND SETUP ───────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

# Folder and file paths
XML_DIR = "xml"                                  # Main directory for XML files
BACKUP_DIR = os.path.join(XML_DIR, "backups")    # Directory for backups
LOG_DIR = "log"                                  # Directory for log files

XML_FILE = os.path.join(XML_DIR, "words.xml")           # Primary XML data file
BACKUP_FILE = os.path.join(BACKUP_DIR, "words.xml.bak") # Backup file location
LOG_FILE = os.path.join(LOG_DIR, "log.txt")             # Log file location

NYT_URL = "https://www.nytimes.com/puzzles/spelling-bee"  # URL to scrape

# New Orleans timezone - handles DST automatically
NOLA_TIMEZONE = pytz.timezone('America/Chicago')  # Central Time Zone for New Orleans

# Create necessary directories if they don't exist
os.makedirs(XML_DIR, exist_ok=True)      # Create XML directory
os.makedirs(BACKUP_DIR, exist_ok=True)   # Create backup directory
os.makedirs(LOG_DIR, exist_ok=True)      # Create log directory

# ───────────────────────────────────────────────────────────────────────────────
# ─── SIMPLE LOGGING ────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def get_timestamp():
    """Get current timestamp in New Orleans timezone with 12-hour format"""
    utc_now = datetime.now(pytz.utc)
    nola_now = utc_now.astimezone(NOLA_TIMEZONE)
    return nola_now.strftime('%Y-%m-%d %I:%M:%S %p %Z')  # 12-hour format with AM/PM

def log_simple(message, status="INFO"):
    """
    Write a simple log entry with timestamp
    """
    timestamp = get_timestamp()
    
    # Check if the log file exists
    file_exists = os.path.exists(LOG_FILE)
    
    # Open in append mode, but if the file doesn't exist, we'll add headers first
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        # Write headers if creating a new file
        if not file_exists:
            f.write("TIMESTAMP,STATUS,MESSAGE\n")
        
        # Append the log entry
        f.write(f"{timestamp},{status},\"{message}\"\n")

# ───────────────────────────────────────────────────────────────────────────────
# ─── XML DATA HANDLING ──────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def load_existing_dates():
    """
    Returns a set of all puzzle dates already stored in words.xml.
    
    Returns:
        set: A set of date strings for puzzles already in the XML file
    """
    if not os.path.exists(XML_FILE):
        return set()
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        dates = {p.get("date") for p in root.findall("puzzle")}
        return dates
    except Exception:
        return set()

def load_latest_words():
    """
    Returns the word list from the most recent puzzle.
    
    Returns:
        list: Sorted list of words from the most recent puzzle
    """
    if not os.path.exists(XML_FILE):
        return []
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        puzzles = root.findall("puzzle")
        
        if not puzzles:
            return []
        
        latest = puzzles[-1]
        words = sorted([w.text.strip().upper() for w in latest.findall("word") if w.text])
        return words
    except Exception:
        return []

def backup_xml_file():
    """
    Create a backup of the words.xml file.
    
    Returns:
        bool: True if backup was successful, False otherwise
    """
    if os.path.exists(XML_FILE):
        try:
            shutil.copyfile(XML_FILE, BACKUP_FILE)
            return True
        except Exception:
            return False
    else:
        return True

def append_puzzle(date_str, words):
    """
    Adds the puzzle to xml/words.xml using lxml, with pretty print.
    
    Args:
        date_str (str): The date of the puzzle in ISO format (YYYY-MM-DD)
        words (list): List of words for the puzzle
        
    Returns:
        bool: True if the puzzle was successfully added, False otherwise
    """
    try:
        # If file exists, parse it; otherwise create new root
        if os.path.exists(XML_FILE):
            tree = ET.parse(XML_FILE)
            root = tree.getroot()
        else:
            root = ET.Element("words")
            tree = ET.ElementTree(root)

        # Create new puzzle element
        puzzle = ET.SubElement(root, "puzzle", date=date_str)
        for word in words:
            ET.SubElement(puzzle, "word").text = word

        # Generate XML string with pretty print
        xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        # Ensure the closing </words> tag is on its own line
        xml_str = xml_str.replace(b'</words>', b'\n</words>')
        
        # Write the modified XML to file
        with open(XML_FILE, 'wb') as f:
            f.write(xml_str)
            
        return True
    except Exception:
        return False

# ───────────────────────────────────────────────────────────────────────────────
# ─── NYT SCRAPING FUNCTIONS ───────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def fetch_puzzle():
    """
    Scrapes the NYT Spelling Bee puzzle and returns the date and words.
    
    Returns:
        tuple: (date_str, words_list) containing the puzzle date and words
    """
    max_retries = 3
    delay = 5  # seconds between retries

    for attempt in range(1, max_retries + 1):
        try:
            # Make the request with a user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.get(NYT_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the script containing the game data
            script = next((s.string for s in soup.find_all("script") 
                          if s.string and "window.gameData" in s.string), None)
                          
            if not script:
                raise RuntimeError("Game data not found in page source.")

            # Extract the JSON data from the script
            start = script.find("{")
            brace_count = 0
            for i in range(start, len(script)):
                if script[i] == '{':
                    brace_count += 1
                elif script[i] == '}':
                    brace_count -= 1
                if brace_count == 0:
                    json_str = script[start:i + 1]
                    break

            # Parse the JSON data
            data = json.loads(json_str)
            today_data = data.get("today", {})
            
            # Extract date and answers
            raw_date = today_data.get("printDate")
            date_str = raw_date.replace("/", "-") if raw_date else date.today().isoformat()
            answers = today_data.get("answers", [])

            return date_str, [w.upper() for w in answers]

        except Exception:
            # If this is the last attempt, exit
            if attempt == max_retries:
                try:
                    from archive.emailer import send_email_notification
                    send_email_notification("❌ Spelling Bee Harvest Error", 
                                          f"Failed to fetch puzzle")
                except Exception:
                    pass
                
                return None, []
                
            # Otherwise, wait and retry
            time.sleep(delay)

# ───────────────────────────────────────────────────────────────────────────────
# ─── MAIN PROGRAM ─────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def main():
    """
    Main program flow.
    
    1. Back up existing XML file
    2. Check if today's puzzle is already harvested
    3. Fetch puzzle from NYT
    4. Validate the puzzle data
    5. Add puzzle to XML file
    """
    # Log start
    log_simple("Harvest process started", "START")
    
    # Always back up words.xml before doing anything
    backup_xml_file()

    # Check if today's puzzle is already in the XML
    existing_dates = load_existing_dates()
    today_str = date.today().isoformat()

    if today_str in existing_dates:
        log_simple("Harvest process completed - puzzle already exists", "SUCCESS")
        return True

    # Fetch the puzzle from NYT
    date_str, words = fetch_puzzle()
    
    # Check if fetch failed
    if date_str is None:
        log_simple("Harvest process failed - could not fetch puzzle", "FAILURE")
        return False

    # Double-check if the fetched date is already in our XML
    if date_str in existing_dates:
        log_simple("Harvest process completed - puzzle already exists", "SUCCESS")
        return True

    # Validate that we have words to save
    if not words:
        log_simple("Harvest process failed - no words found", "FAILURE")
        return False

    # Check if the puzzle is identical to the previous one
    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        log_simple("Harvest process completed with warnings - duplicate puzzle", "SUCCESS")
        return True

    # Add the new puzzle to the XML
    success = append_puzzle(date_str, words)
    
    if success:
        log_simple("Harvest process completed successfully", "SUCCESS")
        return True
    else:
        log_simple("Harvest process failed - could not save puzzle", "FAILURE")
        return False

# ───────────────────────────────────────────────────────────────────────────────
# ─── SCRIPT ENTRY POINT ─────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":    
    try:
        # Run the main program
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        log_simple(f"Harvest process failed - unhandled exception", "FAILURE")
        sys.exit(1)