#!/usr/bin/env python3
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_puzzle_info(file_path):
    """
    Extract the most recent puzzle information from the file.
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Using regex to find all puzzle elements with date and letters attributes
    puzzle_pattern = r'<puzzle date="([^"]+)"[^>]*letters="([^"]+)"[^>]*>'
    puzzles = re.findall(puzzle_pattern, content)
    
    if not puzzles:
        print("No puzzles found in the file.")
        return None, None
    
    # Sort puzzles by date (newest first)
    puzzles.sort(key=lambda x: x[0], reverse=True)
    
    # Return the date and letters of the most recent puzzle
    return puzzles[0][0], puzzles[0][1]

def create_html_content(letters):
    """
    Create HTML content with the letters.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Today's Letters</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
        }}
        h1 {{
            color: #333;
        }}
    </style>
</head>
<body>
    <h1>Today's letters are {letters}</h1>
</body>
</html>
"""
    return html_content

def main(input_file="xml/puzzles.xml"):
    """
    Main function to process the XML file and create the HTML file.
    """
    date_str, letters = extract_puzzle_info(input_file)
    
    if not date_str or not letters:
        print("Could not extract required information.")
        return
    
    # Create html directory if it doesn't exist
    html_dir = Path("html")
    html_dir.mkdir(exist_ok=True)
    
    # Create HTML file with date as name
    html_file_path = html_dir / f"{date_str}.html"
    
    with open(html_file_path, 'w') as file:
        file.write(create_html_content(letters))
    
    print(f"HTML file created successfully: {html_file_path}")

if __name__ == "__main__":
    main()