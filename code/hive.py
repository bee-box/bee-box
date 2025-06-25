"""
Spelling Bee Hive Image Generator

Generates high-quality hive visualizations as SVG files
that can be easily converted to JPG using any browser or online tool.

Author: Generated for professional use
License: MIT
"""

import xml.etree.ElementTree as ET
import math
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from urllib.request import urlopen
from urllib.error import URLError
import argparse
import webbrowser
import sys


@dataclass
class HiveConfig:
    """Configuration for hive generation."""
    width: int = 280
    height: int = 260
    viewbox: str = "-120 -110 240 220"
    hex_size: int = 40
    center_color: str = "#FFDC00"
    outer_color: str = "#E6E6E6"
    stroke_color: str = "#FFFFFF"
    stroke_width: int = 2
    font_family: str = "'Helvetica Neue', Arial, sans-serif"
    font_size: int = 24
    font_weight: str = "bold"


@dataclass
class PuzzleData:
    """Structured puzzle data."""
    date: str
    puzzle_id: str
    center_letter: str
    outer_letters: List[str]
    word_count: int


class SVGRenderer:
    """High-quality SVG hive renderer matching the original design."""
    
    def __init__(self, config: HiveConfig = None):
        self.config = config or HiveConfig()
    
    def create_svg(self, puzzle: PuzzleData) -> str:
        """Generate SVG content for the hive."""
        
        # Calculate hexagon positions (matching sheet.html exactly)
        positions = [
            {"x": 0, "y": 0, "letter": puzzle.center_letter, "fill": self.config.center_color},     # Center
            {"x": 0, "y": -70, "letter": puzzle.outer_letters[0] if len(puzzle.outer_letters) > 0 else "", "fill": self.config.outer_color},  # Top
            {"x": 60, "y": -35, "letter": puzzle.outer_letters[1] if len(puzzle.outer_letters) > 1 else "", "fill": self.config.outer_color}, # Top right
            {"x": 60, "y": 35, "letter": puzzle.outer_letters[2] if len(puzzle.outer_letters) > 2 else "", "fill": self.config.outer_color},   # Bottom right
            {"x": 0, "y": 70, "letter": puzzle.outer_letters[3] if len(puzzle.outer_letters) > 3 else "", "fill": self.config.outer_color},    # Bottom
            {"x": -60, "y": 35, "letter": puzzle.outer_letters[4] if len(puzzle.outer_letters) > 4 else "", "fill": self.config.outer_color},  # Bottom left
            {"x": -60, "y": -35, "letter": puzzle.outer_letters[5] if len(puzzle.outer_letters) > 5 else "", "fill": self.config.outer_color}  # Top left
        ]
        
        # Generate SVG content
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{self.config.width}" height="{self.config.height}" 
     viewBox="{self.config.viewbox}" 
     xmlns="http://www.w3.org/2000/svg">
'''
        
        # Add hexagons and text
        for pos in positions:
            if pos["letter"]:  # Only render if letter exists
                # Generate hexagon points
                points = self._calculate_hexagon_points(pos["x"], pos["y"])
                points_str = " ".join([f"{x},{y}" for x, y in points])
                
                # Add hexagon
                svg_content += f'''
    <polygon points="{points_str}" 
             fill="{pos["fill"]}" 
             stroke="{self.config.stroke_color}" 
             stroke-width="{self.config.stroke_width}"/>'''
                
                # Add text
                svg_content += f'''
    <text x="{pos["x"]}" y="{pos["y"] + 2}" 
          text-anchor="middle" 
          dominant-baseline="middle" 
          font-size="{self.config.font_size}" 
          font-weight="{self.config.font_weight}" 
          font-family="{self.config.font_family}">{pos["letter"]}</text>'''
        
        svg_content += '\n</svg>'
        return svg_content
    
    def create_svg_display_html(self, puzzle: PuzzleData, svg_content: str) -> str:
        """Create HTML page to display SVG code for copy/paste."""
        # Escape SVG content for display in textarea
        escaped_svg = svg_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVG Code - Hive {puzzle.date}</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .preview {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        .code-section {{
            margin: 20px 0;
        }}
        .code-section h3 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .code-textarea {{
            width: 100%;
            height: 400px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            background: #f9f9f9;
            resize: vertical;
        }}
        .buttons {{
            text-align: center;
            margin: 20px 0;
        }}
        .btn {{
            margin: 5px 10px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-primary {{
            background: #FFDC00;
            color: #333;
        }}
        .btn-primary:hover {{
            background: #F0C000;
        }}
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        .btn-secondary:hover {{
            background: #545b62;
        }}
        .info {{
            color: #666;
            font-size: 14px;
            margin: 10px 0;
        }}
        .success {{
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SVG Code - Spelling Bee Hive</h1>
            <div class="info">
                <strong>Date:</strong> {puzzle.date} | 
                <strong>Letters:</strong> {puzzle.center_letter} + {' '.join(puzzle.outer_letters)} | 
                <strong>Words:</strong> {puzzle.word_count}
            </div>
        </div>
        
        <div class="preview">
            <h3>Preview:</h3>
            {svg_content}
        </div>
        
        <div class="code-section">
            <h3>SVG Code (click to select all):</h3>
            <textarea id="svgCode" class="code-textarea" readonly onclick="this.select()">{svg_content}</textarea>
        </div>
        
        <div class="buttons">
            <button class="btn btn-primary" onclick="copyToClipboard()">📋 Copy SVG Code</button>
            <button class="btn btn-secondary" onclick="selectAll()">📝 Select All</button>
            <button class="btn btn-secondary" onclick="downloadSVG()">💾 Download SVG File</button>
        </div>
        
        <div id="successMessage" class="success">✅ SVG code copied to clipboard!</div>
        
        <div class="info">
            <h4>💡 Usage Tips:</h4>
            <ul>
                <li><strong>Copy & Paste:</strong> Click "Copy SVG Code" then paste into your editor</li>
                <li><strong>Save as File:</strong> Click "Download SVG File" to save {puzzle.date}.svg</li>
                <li><strong>Convert to JPG:</strong> Open SVG in browser, right-click → "Save image as"</li>
                <li><strong>Online Converters:</strong> Use CloudConvert, Convertio, or similar with this SVG code</li>
            </ul>
        </div>
    </div>

    <script>
        function copyToClipboard() {{
            const textarea = document.getElementById('svgCode');
            textarea.select();
            textarea.setSelectionRange(0, 99999); // For mobile devices
            
            try {{
                document.execCommand('copy');
                showSuccess();
            }} catch (err) {{
                // Fallback for modern browsers
                navigator.clipboard.writeText(textarea.value).then(function() {{
                    showSuccess();
                }}).catch(function(err) {{
                    alert('Failed to copy to clipboard. Please select all and copy manually.');
                }});
            }}
        }}
        
        function selectAll() {{
            const textarea = document.getElementById('svgCode');
            textarea.select();
            textarea.setSelectionRange(0, 99999);
        }}
        
        function downloadSVG() {{
            const svgContent = document.getElementById('svgCode').value;
            const blob = new Blob([svgContent], {{ type: 'image/svg+xml' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{puzzle.date}.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
        
        function showSuccess() {{
            const msg = document.getElementById('successMessage');
            msg.style.display = 'block';
            setTimeout(() => {{
                msg.style.display = 'none';
            }}, 3000);
        }}
    </script>
</body>
</html>'''
    
    def _calculate_hexagon_points(self, center_x: float, center_y: float) -> List[tuple]:
        """Calculate hexagon vertices exactly like the original JavaScript."""
        points = []
        for i in range(6):
            angle = (math.pi / 3) * i
            x = center_x + self.config.hex_size * math.cos(angle)
            y = center_y + self.config.hex_size * math.sin(angle)
            points.append((x, y))
        return points


class PuzzleParser:
    """Handles XML puzzle data parsing."""
    
    @staticmethod
    def load_xml(source: str) -> Optional[ET.Element]:
        """Load XML from file path or URL."""
        try:
            if source.startswith(('http://', 'https://')):
                with urlopen(source, timeout=10) as response:
                    return ET.fromstring(response.read())
            else:
                return ET.parse(source).getroot()
        except (ET.ParseError, URLError, FileNotFoundError) as e:
            logging.error(f"Failed to load XML from {source}: {e}")
            return None
    
    @staticmethod
    def extract_puzzles(root: ET.Element) -> List[ET.Element]:
        """Extract puzzles with words, sorted by date."""
        puzzles = [p for p in root.findall('puzzle') if p.find('word') is not None]
        return sorted(puzzles, key=lambda p: p.get('date', ''))
    
    @staticmethod
    def parse_puzzle(puzzle_elem: ET.Element) -> Optional[PuzzleData]:
        """Parse puzzle element into structured data."""
        date = puzzle_elem.get('date')
        puzzle_id = puzzle_elem.get('id')
        
        if not date or not puzzle_id:
            return None
        
        # Extract letters (matching sheet.html logic)
        letters_attr = puzzle_elem.get('letters')
        if letters_attr:
            letters_all = sorted(letters_attr.upper())
        else:
            letters_all = []
            for i in range(1, 8):
                letter = puzzle_elem.get(f'letter{i}')
                if letter:
                    letters_all.append(letter.upper())
        
        if len(letters_all) < 7:
            logging.warning(f"Insufficient letters in puzzle {puzzle_id}")
            return None
        
        # Get center letter (letter1) and others
        center_letter = puzzle_elem.get('letter1', letters_all[0]).upper()
        outer_letters = [l for l in letters_all if l != center_letter][:6]
        word_count = len(puzzle_elem.findall('word'))
        
        return PuzzleData(
            date=date,
            puzzle_id=puzzle_id,
            center_letter=center_letter,
            outer_letters=outer_letters,
            word_count=word_count
        )


class HiveGenerator:
    """Main hive generator class."""
    
    def __init__(self, config: HiveConfig = None):
        self.config = config or HiveConfig()
        self.svg_renderer = SVGRenderer(self.config)
        self.parser = PuzzleParser()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
    
    def generate_from_xml(
        self,
        xml_source: str,
        date: Optional[str] = None,
        puzzle_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
        open_browser: bool = True
    ) -> Optional[Path]:
        """Generate hive from XML source."""
        
        # Load and parse XML
        root = self.parser.load_xml(xml_source)
        if root is None:
            return None
        
        puzzles_elements = self.parser.extract_puzzles(root)
        if not puzzles_elements:
            logging.error("No valid puzzles found")
            return None
        
        logging.info(f"Found {len(puzzles_elements)} valid puzzles")
        
        # Select target puzzle
        target_puzzle = self._select_puzzle(puzzles_elements, date, puzzle_id)
        if not target_puzzle:
            return None
        
        puzzle_data = self.parser.parse_puzzle(target_puzzle)
        if not puzzle_data:
            logging.error("Failed to parse selected puzzle")
            return None
        
        return self._generate_hive(puzzle_data, output_dir, open_browser)
    
    def generate_from_letters(
        self,
        letters: str,
        filename: Optional[str] = None,
        output_dir: Optional[Path] = None,
        open_browser: bool = True
    ) -> Optional[Path]:
        """Generate hive from manual letter input."""
        if len(letters) < 7:
            logging.error("At least 7 letters required")
            return None
        
        puzzle_data = PuzzleData(
            date=filename or "manual",
            puzzle_id="manual",
            center_letter=letters[0].upper(),
            outer_letters=list(letters[1:7].upper()),
            word_count=0
        )
        
        return self._generate_hive(puzzle_data, output_dir, open_browser)
    
    def _generate_hive(self, puzzle_data: PuzzleData, output_dir: Optional[Path], open_browser: bool) -> Optional[Path]:
        """Generate the hive files."""
        # Generate SVG
        svg_content = self.svg_renderer.create_svg(puzzle_data)
        
        # Determine output path - just save as YYYY-MM-DD.svg
        output_path = self._get_output_path(puzzle_data.date, output_dir)
        svg_path = output_path.with_suffix('.svg')
        
        # Save SVG file
        try:
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            logging.info(f"Generated hive for {puzzle_data.date} ({puzzle_data.word_count} words)")
            logging.info(f"Letters: {puzzle_data.center_letter} + {puzzle_data.outer_letters}")
            logging.info(f"Saved SVG: {svg_path}")
            
            return svg_path
            
        except Exception as e:
            logging.error(f"Failed to save SVG: {e}")
            return None
    
    def _select_puzzle(self, puzzles: List[ET.Element], date: Optional[str], puzzle_id: Optional[str]) -> Optional[ET.Element]:
        """Select puzzle based on criteria."""
        if puzzle_id:
            for puzzle in puzzles:
                if puzzle.get('id') == puzzle_id:
                    return puzzle
            logging.error(f"Puzzle ID '{puzzle_id}' not found")
            return None
        
        if date:
            for puzzle in puzzles:
                if puzzle.get('date') == date:
                    return puzzle
            logging.error(f"Date '{date}' not found")
            self._show_available_dates(puzzles)
            return None
        
        # Return most recent puzzle
        return puzzles[-1]
    
    def _get_output_path(self, name: str, output_dir: Optional[Path]) -> Path:
        """Generate output file path."""
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / name
        
        # Save to images folder relative to script location
        script_dir = Path(__file__).parent
        images_dir = script_dir.parent / "images"  # Go up one level then into images
        images_dir.mkdir(exist_ok=True)
        return images_dir / name
    
    def _show_available_dates(self, puzzles: List[ET.Element]):
        """Show available puzzle dates."""
        logging.info("Available dates (last 10):")
        for puzzle in puzzles[-10:]:
            date = puzzle.get('date')
            puzzle_id = puzzle.get('id')
            word_count = len(puzzle.findall('word'))
            logging.info(f"  {date} ({puzzle_id}) - {word_count} words")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate professional Spelling Bee hive images as beautiful SVG + conversion HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hive.py                           # Use xml/puzzles.xml, most recent
  python hive.py --xml puzzles.xml --date 2025-06-24
  python hive.py --letters ACEIPTV --output custom-hive
        """
    )
    
    parser.add_argument('--xml', help='XML file path or URL')
    parser.add_argument('--date', help='Puzzle date (YYYY-MM-DD)')
    parser.add_argument('--puzzle-id', help='Specific puzzle ID')
    parser.add_argument('--letters', help='Manual letters (7+ chars, first is center)')
    parser.add_argument('--output', help='Output filename (without extension)')
    parser.add_argument('--output-dir', type=Path, help='Output directory')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser automatically")
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create generator
    generator = HiveGenerator()
    
    # Generate from letters or XML
    if args.letters:
        result = generator.generate_from_letters(
            args.letters,
            args.output,
            args.output_dir,
            not args.no_browser
        )
    elif args.xml:
        result = generator.generate_from_xml(
            args.xml,
            args.date,
            args.puzzle_id,
            args.output_dir,
            not args.no_browser
        )
    else:
        # Default: try to find xml/puzzles.xml and use most recent
        default_xml = Path("xml/puzzles.xml")
        if default_xml.exists():
            print("Using default xml/puzzles.xml...")
            result = generator.generate_from_xml(
                str(default_xml),
                None,  # No specific date - use most recent
                None,  # No specific puzzle ID
                args.output_dir,
                False  # Don't open browser in CI
            )
        else:
            print("No XML file found. Please use --xml or --letters")
            parser.print_help()
            return
    
    if result:
        print(f"✓ Generated: {result}")
        print("💡 Click the download buttons in your browser to save as JPG/PNG")
    else:
        print("✗ Generation failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()