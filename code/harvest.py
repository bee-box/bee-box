#!/usr/bin/env python3
"""
Spelling Bee Harvester – harvest.py

This script:
- Scrapes today's New York Times Spelling Bee word list
- Saves it to xml/words.xml if the date isn't already present
- Always backs up words.xml to xml/backups/words.xml.bak
- Uses lxml for fast and clean XML handling
- Logs all activity to log/log.txt with timestamps in New Orleans, LA time (Central Time Zone)
- Handles Daylight Saving Time shifts automatically
- Provides detailed progress annotations and error reporting

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
# ─── LOGGING FUNCTIONS ──────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def get_nola_time():
    """
    Get the current time in New Orleans (Central Time Zone) with DST handling.
    
    Returns:
        str: A formatted timestamp string in New Orleans local time
    """
    utc_now = datetime.now(pytz.utc)                   # Get current UTC time
    nola_now = utc_now.astimezone(NOLA_TIMEZONE)       # Convert to New Orleans time
    
    # Format with timezone info to show CDT/CST as appropriate
    return nola_now.strftime('%Y-%m-%d %H:%M:%S %Z')

def log(message, level="INFO"):
    """
    Log a message with New Orleans timestamp to screen and log file.
    
    Args:
        message (str): The message to log
        level (str): The logging level (INFO, WARNING, ERROR, etc.)
    """
    timestamp = get_nola_time()
    full_msg = f"[{timestamp}] [{level}] {message}"
    print(full_msg)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def log_separator():
    """
    Adds a divider line to the end of the log entry.
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("─" * 60 + "\n\n")

def log_operation_start(operation):
    """
    Log the start of a specific operation with a distinctive marker.
    
    Args:
        operation (str): Name of the operation being started
    """
    log(f"▶️ Starting operation: {operation}")

def log_operation_end(operation, status="completed"):
    """
    Log the end of a specific operation with a distinctive marker.
    
    Args:
        operation (str): Name of the operation being completed
        status (str): Status of completion (completed, failed, etc.)
    """
    log(f"⏹️ Operation {status}: {operation}")

def log_error(message, exception=None):
    """
    Log an error with exception details if available.
    
    Args:
        message (str): Error description
        exception (Exception, optional): The exception object if available
    """
    error_details = f": {str(exception)}" if exception else ""
    log(f"❌ ERROR: {message}{error_details}", level="ERROR")

# ───────────────────────────────────────────────────────────────────────────────
# ─── XML DATA HANDLING ──────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def load_existing_dates():
    """
    Returns a set of all puzzle dates already stored in words.xml.
    
    Returns:
        set: A set of date strings for puzzles already in the XML file
    """
    log_operation_start("Loading existing dates from XML")
    
    if not os.path.exists(XML_FILE):
        log("XML file does not exist yet - no existing dates")
        log_operation_end("Loading existing dates")
        return set()
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        dates = {p.get("date") for p in root.findall("puzzle")}
        log(f"Found {len(dates)} existing puzzle dates in XML")
        log_operation_end("Loading existing dates")
        return dates
    except Exception as e:
        log_error("Failed to parse existing XML file", e)
        log_operation_end("Loading existing dates", "failed")
        return set()

def load_latest_words():
    """
    Returns the word list from the most recent puzzle.
    
    Returns:
        list: Sorted list of words from the most recent puzzle
    """
    log_operation_start("Loading latest word list")
    
    if not os.path.exists(XML_FILE):
        log("XML file does not exist yet - no latest words")
        log_operation_end("Loading latest word list")
        return []
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        puzzles = root.findall("puzzle")
        
        if not puzzles:
            log("No puzzles found in XML file")
            log_operation_end("Loading latest word list")
            return []
        
        latest = puzzles[-1]
        latest_date = latest.get("date", "unknown")
        words = sorted([w.text.strip().upper() for w in latest.findall("word") if w.text])
        
        log(f"Loaded {len(words)} words from latest puzzle ({latest_date})")
        log_operation_end("Loading latest word list")
        return words
    except Exception as e:
        log_error("Failed to load latest words", e)
        log_operation_end("Loading latest word list", "failed")
        return []

def backup_xml_file():
    """
    Create a backup of the words.xml file.
    
    Returns:
        bool: True if backup was successful, False otherwise
    """
    log_operation_start("Backing up XML file")
    
    if os.path.exists(XML_FILE):
        try:
            shutil.copyfile(XML_FILE, BACKUP_FILE)
            log(f"Backup created: {BACKUP_FILE}")
            log_operation_end("Backing up XML file")
            return True
        except Exception as e:
            log_error("Failed to create backup", e)
            log_operation_end("Backing up XML file", "failed")
            return False
    else:
        log("No existing XML file to back up")
        log_operation_end("Backing up XML file", "skipped")
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
    log_operation_start(f"Adding puzzle for {date_str} to XML")
    
    try:
        # If file exists, parse it; otherwise create new root
        if os.path.exists(XML_FILE):
            log("Parsing existing XML file")
            tree = ET.parse(XML_FILE)
            root = tree.getroot()
        else:
            log("Creating new XML structure")
            root = ET.Element("words")
            tree = ET.ElementTree(root)

        # Create new puzzle element
        log(f"Creating puzzle element with {len(words)} words")
        puzzle = ET.SubElement(root, "puzzle", date=date_str)
        for word in words:
            ET.SubElement(puzzle, "word").text = word

        # Write to file with pretty formatting
        log("Writing updated XML to file")
        tree.write(XML_FILE, encoding="utf-8", xml_declaration=True, pretty_print=True)
        log(f"✅ Puzzle for {date_str} successfully added to words.xml")
        log_operation_end(f"Adding puzzle for {date_str} to XML")
        return True
    except Exception as e:
        log_error(f"Failed to add puzzle for {date_str} to XML", e)
        log_operation_end(f"Adding puzzle for {date_str} to XML", "failed")
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
    log_operation_start("Fetching puzzle from NYT")
    
    max_retries = 3
    delay = 5  # seconds between retries

    for attempt in range(1, max_retries + 1):
        try:
            log(f"Attempt {attempt} of {max_retries}...")
            
            # Make the request with a user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9"
            }
            log("Sending HTTP request to NYT")
            response = requests.get(NYT_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            log("Parsing HTML response")
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the script containing the game data
            log("Searching for game data in page source")
            script = next((s.string for s in soup.find_all("script") 
                          if s.string and "window.gameData" in s.string), None)
                          
            if not script:
                raise RuntimeError("Game data not found in page source.")

            # Extract the JSON data from the script
            log("Extracting JSON data from script")
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
            log("Parsing JSON data")
            data = json.loads(json_str)
            today_data = data.get("today", {})
            
            # Extract date and answers
            raw_date = today_data.get("printDate")
            date_str = raw_date.replace("/", "-") if raw_date else date.today().isoformat()
            answers = today_data.get("answers", [])

            # Success!
            log(f"📅 Successfully fetched puzzle for {date_str} with {len(answers)} words")
            log_operation_end("Fetching puzzle from NYT")
            return date_str, [w.upper() for w in answers]

        except Exception as e:
            log_error(f"Error in fetch attempt {attempt}", e)
            
            # If this is the last attempt, try to send email notification and exit
            if attempt == max_retries:
                log("Maximum retry attempts reached")
                try:
                    from emailer import send_email_notification
                    log("Sending error notification email")
                    send_email_notification("❌ Spelling Bee Harvest Error", 
                                          f"Failed to fetch puzzle: {str(e)}")
                    log("Error notification email sent")
                except Exception as mail_err:
                    log_error("Failed to send email alert", mail_err)
                
                log_operation_end("Fetching puzzle from NYT", "failed")
                sys.exit(1)
                
            # Otherwise, wait and retry
            log(f"🔁 Waiting {delay} seconds before retry...")
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
    log("🟡 START HARVEST RUN", level="START")
    log(f"Running on system: {os.name}, Python: {sys.version.split()[0]}")

    # Always back up words.xml before doing anything
    backup_xml_file()

    # Check if today's puzzle is already in the XML
    existing_dates = load_existing_dates()
    today_str = date.today().isoformat()

    if today_str in existing_dates:
        log(f"ℹ️ Puzzle for {today_str} already exists in XML", level="INFO")
        log("🔚 END HARVEST RUN - No action needed", level="END")
        log_separator()
        return

    # Fetch the puzzle from NYT
    date_str, words = fetch_puzzle()

    # Double-check if the fetched date is already in our XML
    if date_str in existing_dates:
        log(f"ℹ️ Puzzle for {date_str} already exists in XML", level="INFO")
        log("🔚 END HARVEST RUN - No action needed", level="END")
        log_separator()
        return

    # Validate that we have words to save
    if not words:
        log_error(f"No words found for {date_str}")
        log("🔚 END HARVEST RUN - Failed: no words found", level="END")
        log_separator()
        return

    # Check if the puzzle is identical to the previous one
    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        log("ℹ️ Puzzle is identical to the previous one - potential error", level="WARNING")
        log(f"Latest: {len(latest_words)} words, New: {len(words)} words - same content")
        log("🔚 END HARVEST RUN - Skipped: duplicate puzzle", level="END")
        log_separator()
        return

    # Add the new puzzle to the XML
    success = append_puzzle(date_str, words)
    
    if success:
        log("✅ Harvest completed successfully", level="SUCCESS")
    else:
        log("❌ Harvest completed with errors", level="ERROR")
        
    log("🔚 END HARVEST RUN", level="END")
    log_separator()

# ───────────────────────────────────────────────────────────────────────────────
# ─── SCRIPT ENTRY POINT ─────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Record script start time
    start_time = time.time()
    
    try:
        # Run the main program
        main()
    except Exception as e:
        # Catch any unhandled exceptions
        log_error("Unhandled exception in main program", e)
        log_separator()
        sys.exit(1)
        
    # Calculate and log execution time
    execution_time = time.time() - start_time
    log(f"Total execution time: {execution_time:.2f} seconds", level="INFO")