#!/usr/bin/env python3
"""
Spelling Bee Harvester – harvest.py

This script:
- Scrapes today's New York Times Spelling Bee word list
- Saves it to xml/words.xml if the date isn't already present
- Backs up words.xml to xml/backups/words.xml.bak ONLY if the backup is smaller 
- Uses lxml for fast and clean XML handling
- Logs minimal information: start time, success/failure, end time

Author: Kevin Kolb
Last updated: May 18, 2025
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

# Retry settings
MAX_RETRIES = 3     # Maximum number of attempts for fetching
RETRY_DELAY = 5     # Seconds between retry attempts

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
        
        # Also print to stdout for visibility
        print(f"{timestamp} [{status}] {message}")
    except Exception as e:
        # If logging itself fails, at least try to print to stderr
        print(f"ERROR: Failed to write to log file: {str(e)}", file=sys.stderr)

# ───────────────────────────────────────────────────────────────────────────────
# ─── BACKUP AND FILE OPERATIONS ───────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def verify_xml(file_path):
    """
    Verify that a file contains valid XML
    
    Args:
        file_path (str): Path to the XML file
        
    Returns:
        bool: True if the file contains valid XML, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        ET.parse(file_path)
        return True
    except Exception:
        return False

def backup_xml_file():
    """
    Create a backup of words.xml, but ONLY if the current file is LARGER than the existing backup.
    
    - If backup doesn't exist yet, create it
    - If current file is smaller than backup, do nothing
    - If current file is larger than backup, update the backup
    
    Returns:
        bool: True if backup operation completed successfully, False on error
    """
    # Check if words.xml exists - if not, nothing to back up
    if not os.path.exists(XML_FILE):
        log_simple("No backup needed - words.xml doesn't exist", "INFO")
        return True
    
    try:
        # Verify that the source file contains valid XML
        if not verify_xml(XML_FILE):
            log_simple("Skipping backup - source file does not contain valid XML", "WARNING")
            return False
            
        # Get size of current words.xml
        current_size = os.path.getsize(XML_FILE)
        
        # Check if backup exists
        if os.path.exists(BACKUP_FILE):
            backup_size = os.path.getsize(BACKUP_FILE)
            
            # Compare sizes - only back up if current file is larger
            if current_size <= backup_size:
                log_simple(f"Skipping backup - current file ({current_size} bytes) is not larger than backup ({backup_size} bytes)", "INFO")
                return True
            
            log_simple(f"Current file ({current_size} bytes) is larger than backup ({backup_size} bytes) - updating backup", "INFO")
        else:
            log_simple(f"No existing backup found - creating new backup ({current_size} bytes)", "INFO")
        
        # Make the backup using a temporary file for safety
        temp_backup = BACKUP_FILE + ".tmp"
        shutil.copy2(XML_FILE, temp_backup)
        
        # Verify the copy worked before moving to final location
        if verify_xml(temp_backup):
            shutil.move(temp_backup, BACKUP_FILE)
            log_simple(f"Successfully backed up words.xml to {BACKUP_FILE}", "INFO")
            return True
        else:
            log_simple("Backup failed - temporary file verification failed", "FAILURE")
            # Clean up the temp file
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            return False
        
    except Exception as e:
        log_simple(f"Backup failed: {str(e)}", "FAILURE")
        return False

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
    except Exception as e:
        log_simple(f"Error loading dates: {str(e)}", "FAILURE")
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
        
        # Sort puzzles by date to find the latest
        sorted_puzzles = sorted(puzzles, key=lambda p: p.get("date", ""), reverse=True)
        latest = sorted_puzzles[0]
        
        words = sorted([w.text.strip().upper() for w in latest.findall("word") if w.text])
        return words
    except Exception as e:
        log_simple(f"Error loading latest words: {str(e)}", "FAILURE")
        return []

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
        # First check if we can read the existing file
        if os.path.exists(XML_FILE):
            # Verify file is readable and contains valid XML
            try:
                tree = ET.parse(XML_FILE)
                root = tree.getroot()
                log_simple(f"Successfully loaded existing words.xml with {len(root.findall('puzzle'))} puzzles", "INFO")
            except Exception as e:
                log_simple(f"Error parsing existing XML file: {str(e)}", "FAILURE")
                
                # Create a special backup of the corrupted file 
                corrupt_backup = os.path.join(BACKUP_DIR, f"words.xml.corrupted")
                try:
                    shutil.copy2(XML_FILE, corrupt_backup)
                    log_simple(f"Created backup of corrupted file at {corrupt_backup}", "INFO")
                except Exception as backup_error:
                    log_simple(f"Failed to backup corrupted file: {str(backup_error)}", "FAILURE")
                
                # Create new root
                root = ET.Element("words")
                tree = ET.ElementTree(root)
        else:
            # Create new XML structure
            root = ET.Element("words")
            tree = ET.ElementTree(root)

        # Add new puzzle
        puzzle = ET.SubElement(root, "puzzle", date=date_str)
        
        # Sort words alphabetically before adding
        sorted_words = sorted(words)
        for word in sorted_words:
            ET.SubElement(puzzle, "word").text = word

        # Generate XML string with pretty print
        xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        # Write to temporary file first
        temp_file = XML_FILE + ".tmp"
        with open(temp_file, 'wb') as f:
            f.write(xml_str)
        
        # Verify the temporary file
        if not verify_xml(temp_file):
            log_simple("Failed to create valid XML file", "FAILURE")
            return False
            
        # Now move the temporary file to the real location
        shutil.move(temp_file, XML_FILE)
        
        log_simple(f"Successfully wrote {os.path.getsize(XML_FILE)} bytes to words.xml", "INFO")
        return True
    except Exception as e:
        log_simple(f"Error appending puzzle: {str(e)}", "FAILURE")
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
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Make the request with a user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            log_simple(f"Fetching puzzle from NYT (attempt {attempt}/{MAX_RETRIES})", "INFO")
            response = requests.get(NYT_URL, headers=headers, timeout=30)
            
            # Check for different HTTP status codes
            if response.status_code == 403:
                log_simple("Access forbidden - NYT may be blocking scrapers", "FAILURE")
                # Wait longer for this type of error
                time.sleep(RETRY_DELAY * 2)
                continue
            elif response.status_code == 429:
                log_simple("Rate limited by NYT - too many requests", "FAILURE")
                # Wait even longer for rate limiting
                time.sleep(RETRY_DELAY * 3)
                continue
            elif response.status_code != 200:
                log_simple(f"HTTP error: {response.status_code}", "FAILURE")
                time.sleep(RETRY_DELAY)
                continue
                
            # If we get here, status code is 200 OK
            response.raise_for_status()  # Just in case
            
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

            log_simple(f"Successfully fetched puzzle for {date_str} with {len(answers)} words", "INFO")
            return date_str, [w.upper() for w in answers]

        except json.JSONDecodeError:
            log_simple("Error parsing JSON from NYT response", "FAILURE")
        except requests.exceptions.RequestException as e:
            log_simple(f"Request failed: {str(e)}", "FAILURE")
        except Exception as e:
            log_simple(f"Fetch attempt {attempt} failed: {str(e)}", "FAILURE")
            
        # If we get here, there was an error - retry after delay
        if attempt < MAX_RETRIES:
            log_simple(f"Retrying in {RETRY_DELAY} seconds...", "INFO")
            time.sleep(RETRY_DELAY)
        else:
            # Last attempt failed, notify if possible
            try:
                from archive.emailer import send_email_notification
                send_email_notification("❌ Spelling Bee Harvest Error", 
                                      f"Failed to fetch puzzle after {MAX_RETRIES} attempts")
            except Exception:
                pass
            
            return None, []

# ───────────────────────────────────────────────────────────────────────────────
# ─── MAIN PROGRAM ─────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────

def main():
    """
    Main program flow.
    
    1. Back up existing XML file (if current file is larger than backup)
    2. Check if today's puzzle is already harvested
    3. Fetch puzzle from NYT
    4. Validate the puzzle data
    5. Add puzzle to XML file
    """
    # Log start
    log_simple("Harvest process started", "START")
    
    # Back up words.xml, but only if current file is larger than backup
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
        
    # Make sure we have a reasonable number of words (most puzzles have 20+ words)
    if len(words) < 10:
        log_simple(f"Warning: Unusually small number of words ({len(words)})", "WARNING")

    # Check if the puzzle is identical to the previous one
    latest_words = load_latest_words()
    if sorted(words) == latest_words:
        log_simple("Harvest process completed with warnings - duplicate puzzle", "SUCCESS")
        return True

    # Add the new puzzle to the XML
    success = append_puzzle(date_str, words)
    
    if success:
        # Now that we've successfully updated words.xml, check if we should update the backup
        backup_xml_file()
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
        # Get the full traceback for better debugging
        import traceback
        tb = traceback.format_exc()
        log_simple(f"Harvest process failed - unhandled exception: {str(e)}\n{tb}", "FAILURE")
        sys.exit(1)