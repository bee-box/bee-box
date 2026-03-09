import webbrowser
import pyperclip
import time
import os

# Output directory
OUTPUT_DIR = r"C:\Code\bee-box\images"

MISSING_DATES = [
    "03-15", "03-23", "03-24", "03-25", "03-26", "03-27", "03-28", "03-29", "03-30", "03-31",
    "04-08", "04-09", "04-10", "04-11", "04-12", "04-13", "04-14", "04-15", "04-16", "04-17",
    "04-18", "04-19", "04-20", "04-21", "04-22", "04-23", "04-24", "04-25", "04-26", "04-27",
    "04-28", "04-29", "04-30",
]

MONTH_NAMES = {
    "03": "March", "04": "April",
}

NATIONAL_DAYS = {
    "03-15": "National Peanut Lover's Day",
    "03-23": "National Puppy Day",
    "03-24": "National Cheesesteak Day",
    "03-25": "National Waffle Day",
    "03-26": "National Spinach Day",
    "03-27": "National Spanish Paella Day",
    "03-28": "National Black Forest Cake Day",
    "03-29": "National Mom and Pop Business Owners Day",
    "03-30": "National Doctors Day",
    "03-31": "National Crayon Day",
    "04-08": "National Empanada Day",
    "04-09": "National Unicorn Day",
    "04-10": "National Siblings Day",
    "04-11": "National Pet Day",
    "04-12": "National Grilled Cheese Day",
    "04-13": "National Scrabble Day",
    "04-14": "National Gardening Day",
    "04-15": "National Tax Day",
    "04-16": "National Orchid Day",
    "04-17": "National Cheese Ball Day",
    "04-18": "National Animal Crackers Day",
    "04-19": "National Garlic Day",
    "04-20": "National Pineapple Upside Down Cake Day",
    "04-21": "National Kindergarten Day",
    "04-22": "National Earth Day",
    "04-23": "National Picnic Day",
    "04-24": "National Pigs in a Blanket Day",
    "04-25": "National DNA Day",
    "04-26": "National Pretzel Day",
    "04-27": "National Prime Rib Day",
    "04-28": "National Superhero Day",
    "04-29": "National Zipper Day",
    "04-30": "National Honesty Day",
}

def get_prompt(mm_dd):
    mm, dd = mm_dd.split("-")
    month = MONTH_NAMES[mm]
    day = int(dd)
    national_day = NATIONAL_DAYS.get(mm_dd, f"a special day on {month} {day}")
    return (
        f"Create a vibrant, cheerful bee-themed illustration for {month} {day} ({national_day}). "
        f"Feature cute cartoon bees and honeycomb elements prominently. "
        f"Incorporate the theme of '{national_day}' into the scene. "
        f"Include the date '{month} {day}' as bold, decorative text in the image. "
        f"Style: colorful, warm, professional digital art with a golden honey color palette. banner format."
    )

def main():
    # Filter to only dates that don't already have an image
    remaining = [d for d in MISSING_DATES if not os.path.exists(os.path.join(OUTPUT_DIR, f"{d}.png"))]

    if not remaining:
        print("✅ All images already exist!")
        return

    print(f"🐝 Bee-Box Browser Image Generator")
    print(f"   {len(remaining)} images to generate")
    print()
    print("INSTRUCTIONS:")
    print("  1. The script will copy a prompt to your clipboard")
    print("  2. It will open ChatGPT in your browser")
    print("  3. Paste (Ctrl+V) into the ChatGPT prompt box and hit Enter")
    print("  4. Wait for the image to generate")
    print("  5. Right-click the image > Save As")
    print(f"  6. Save to: {OUTPUT_DIR}")
    print(f"  7. Name the file exactly as shown (e.g. 03-15.png)")
    print("  8. Come back to this window and press Enter to continue to the next date")
    print()

    for i, mm_dd in enumerate(remaining, 1):
        prompt = get_prompt(mm_dd)
        pyperclip.copy(prompt)

        print(f"[{i}/{len(remaining)}] Date: {mm_dd}")
        print(f"  Prompt copied to clipboard!")
        print(f"  Save the image as: {mm_dd}.png")
        print()

        # Open ChatGPT in browser
        webbrowser.open("https://chatgpt.com")

        input("  ⏎  Press Enter when you've saved the image and are ready for the next one...")

        # Check if file was saved
        filepath = os.path.join(OUTPUT_DIR, f"{mm_dd}.png")
        if os.path.exists(filepath):
            print(f"  ✅ Found {mm_dd}.png — moving on!\n")
        else:
            print(f"  ⚠️  Couldn't find {mm_dd}.png in {OUTPUT_DIR} — continuing anyway.\n")

    print("🎉 All done!")

if __name__ == "__main__":
    main()