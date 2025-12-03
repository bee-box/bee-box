#!/usr/bin/env python3
"""
365 Bee Image Prompts Generator
Automatically submits prompts to OpenAI's DALL-E or Grok's image API
"""

import os
import time
import base64
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import requests

# ============================================================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================================================

# Choose your API: "openai" or "grok"
API_PROVIDER = "openai"  # Change to "grok" if using Grok

# API Keys (set these as environment variables)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROK_API_KEY = os.environ.get("GROK_API_KEY", "")

# Image settings
IMAGE_SIZE = "1024x1024"  # Options: "1024x1024", "1792x1024", "1024x1792"
IMAGE_QUALITY = "standard"  # Options: "standard", "hd" (hd costs more)

# Output directory for images
OUTPUT_DIR = "./bee_images"

# Delay between API calls (in seconds) to avoid rate limits
DELAY_BETWEEN_CALLS = 3

# General prompt additions (prepended or appended to each prompt)
PROMPT_PREFIX = ""
PROMPT_SUFFIX = ", high quality, detailed, professional photography"

# Resume from specific date if script was interrupted (format: "January 1st" or leave empty)
RESUME_FROM_DATE = ""

# Limit generation (set to 0 for all 365, or set a number to test with fewer images)
LIMIT_IMAGES = 3  # Set to like 5 for testing, then 0 for all 365

# ============================================================================
# API FUNCTIONS
# ============================================================================

def generate_image_openai(prompt, date_str):
    """Generate image using OpenAI's DALL-E API"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": IMAGE_SIZE,
        "quality": IMAGE_QUALITY,
        "response_format": "b64_json"
    }
    
    print(f"  Calling OpenAI DALL-E API...")
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers=headers,
        json=data,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        image_data = base64.b64decode(result['data'][0]['b64_json'])
        return image_data
    else:
        raise Exception(f"OpenAI API Error: {response.status_code} - {response.text}")


def generate_image_grok(prompt, date_str):
    """Generate image using Grok's image API (xAI)"""
    # Note: Grok/xAI API endpoint may vary - adjust as needed
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": prompt,
        "size": IMAGE_SIZE,
        "n": 1
    }
    
    print(f"  Calling Grok API...")
    # This endpoint is hypothetical - adjust based on actual Grok API documentation
    response = requests.post(
        "https://api.x.ai/v1/images/generations",  # Update with actual endpoint
        headers=headers,
        json=data,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        # Adjust based on actual response format
        if 'data' in result and len(result['data']) > 0:
            if 'b64_json' in result['data'][0]:
                image_data = base64.b64decode(result['data'][0]['b64_json'])
            elif 'url' in result['data'][0]:
                # Download from URL
                img_response = requests.get(result['data'][0]['url'])
                image_data = img_response.content
            else:
                raise Exception("Unknown response format from Grok API")
            return image_data
    else:
        raise Exception(f"Grok API Error: {response.status_code} - {response.text}")


def save_image(image_data, date_str, output_dir):
    """Save image data to PNG file"""
    # Create safe filename from date
    safe_filename = date_str.replace(" ", "_").replace("/", "-")
    filepath = Path(output_dir) / f"{safe_filename}.png"
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    print(f"  Saved: {filepath}")
    return filepath


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def load_prompts(xml_file):
    """Load prompts from XML file"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    prompts = []
    for prompt_elem in root.findall('.//prompt'):
        day = prompt_elem.get('day')
        prompt_text = prompt_elem.text
        prompts.append((day, prompt_text))
    
    return prompts


def main():
    print("=" * 70)
    print("365 BEE IMAGE PROMPTS GENERATOR")
    print("=" * 70)
    print(f"API Provider: {API_PROVIDER.upper()}")
    print(f"Image Size: {IMAGE_SIZE}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Limit: {LIMIT_IMAGES if LIMIT_IMAGES > 0 else 'ALL 365 IMAGES'}")
    print("=" * 70)
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load prompts from XML
    xml_file = "365beeimageprompts.xml"
    if not os.path.exists(xml_file):
        print(f"ERROR: {xml_file} not found!")
        print("Make sure the XML file is in the same directory as this script.")
        return
    
    print(f"\nLoading prompts from {xml_file}...")
    prompts = load_prompts(xml_file)
    print(f"Loaded {len(prompts)} prompts")
    
    # Check if resuming
    start_index = 0
    if RESUME_FROM_DATE:
        for i, (date, _) in enumerate(prompts):
            if date == RESUME_FROM_DATE:
                start_index = i
                print(f"Resuming from: {RESUME_FROM_DATE}")
                break
    
    # Limit if specified
    if LIMIT_IMAGES > 0:
        prompts = prompts[start_index:start_index + LIMIT_IMAGES]
    else:
        prompts = prompts[start_index:]
    
    # Verify API key is set
    if API_PROVIDER == "openai" and not OPENAI_API_KEY:
        print("\nWARNING: You need to set your OPENAI_API_KEY!")
        print("Set it as an environment variable.")
        return
    elif API_PROVIDER == "grok" and not GROK_API_KEY:
        print("\nWARNING: You need to set your GROK_API_KEY!")
        print("Set it as an environment variable.")
        return
    
    # Generate images
    print(f"\nStarting generation of {len(prompts)} images...")
    print(f"Estimated time: ~{len(prompts) * (DELAY_BETWEEN_CALLS + 10) / 60:.1f} minutes")
    print("\n" + "=" * 70)
    
    success_count = 0
    error_count = 0
    
    for i, (date, prompt) in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {date}")
        print(f"  Prompt: {prompt[:80]}...")
        
        # Enhance prompt with prefix/suffix
        full_prompt = f"{PROMPT_PREFIX}{prompt}{PROMPT_SUFFIX}".strip()
        
        try:
            # Generate image
            if API_PROVIDER == "openai":
                image_data = generate_image_openai(full_prompt, date)
            elif API_PROVIDER == "grok":
                image_data = generate_image_grok(full_prompt, date)
            else:
                raise Exception(f"Unknown API provider: {API_PROVIDER}")
            
            # Save image
            save_image(image_data, date, OUTPUT_DIR)
            success_count += 1
            print(f"  SUCCESS")
            
        except Exception as e:
            print(f"  X ERROR: {str(e)}")
            error_count += 1
            
            # Log error to file
            with open(Path(OUTPUT_DIR) / "errors.log", 'a') as f:
                f.write(f"{datetime.now()}: {date} - {str(e)}\n")
        
        # Delay between calls to respect rate limits
        if i < len(prompts):
            print(f"  Waiting {DELAY_BETWEEN_CALLS} seconds...")
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()