import requests
from bs4 import BeautifulSoup
import os
import time
import re
import glob

BASE_URL = "https://yournovel.org"
NOVEL_SLUG = "shadow-slave"
OUTPUT_DIR = "chapters"
CHAPTERS_TO_DOWNLOAD = 10  # number of new chapters to get

def get_last_chapter_number():
    """Find the highest chapter number already saved in the chapters folder."""
    if not os.path.exists(OUTPUT_DIR):
        return 0
    
    # Look for files matching pattern: chapter-####.txt
    files = glob.glob(os.path.join(OUTPUT_DIR, "chapter-*.txt"))
    if not files:
        return 0
    
    # Extract numbers from filenames
    numbers = []
    for f in files:
        match = re.search(r'chapter-(\d+)\.txt', f)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) if numbers else 0

def get_chapter_urls(start, end):
    """Scrape the novel's category page to get the exact URLs (with slug) for each chapter."""
    url = f"{BASE_URL}/category/{NOVEL_SLUG}/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    chapter_map = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Match pattern like /shadow-slave-chapter-1591-something/
        m = re.search(r'shadow-slave-chapter-(\d+)-([\w-]+)/', href)
        if m:
            num = int(m.group(1))
            if start <= num <= end:
                full = href if href.startswith('http') else BASE_URL + href
                chapter_map[num] = full
    return chapter_map

def extract_story_text(html):
    """
    Extract the actual story content while removing the table-of-contents list
    that appears on many pages.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find the main content container
    content = soup.find('div', class_='entry-content') or soup.find('article')
    if not content:
        return None

    # Remove common navigation / chapter-list widgets to avoid picking up TOC text
    for unwanted in content.find_all(['ul', 'ol', 'div', 'nav'],
                                     class_=re.compile(r'chapter|episode|su-posts|navigation|toc|list', re.I)):
        unwanted.decompose()

    # Also remove any <aside> or <nav> tags
    for tag in content.find_all(['aside', 'nav']):
        tag.decompose()

    # Extract text, preserving paragraph breaks
    text = content.get_text(separator='\n', strip=True)
    return text

def download_chapter(url, number):
    try:
        resp = requests.get(url)
        story = extract_story_text(resp.text)
        if not story:
            print(f"Chapter {number}: content not found")
            return False

        # Clean up: remove the chapter-title line if it's repeated, and any extra artifacts
        lines = story.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are just a list of chapter titles (e.g., "Shadow Slave Chapter 1 ...")
            if re.match(r'Shadow Slave Chapter \d+', line) and len(line) < 100:
                continue   # likely a TOC entry, skip
            cleaned_lines.append(line)

        final_text = '\n'.join(cleaned_lines).strip()
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = os.path.join(OUTPUT_DIR, f"chapter-{number:04d}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Chapter {number}\n\n{final_text}")
        print(f"✓ Chapter {number} saved")
        return True

    except Exception as e:
        print(f"✗ Chapter {number} error: {e}")
        return False

def main():
    # Find where we left off
    last_chapter = get_last_chapter_number()
    
    if last_chapter == 0:
        print("No existing chapters found. Please set a starting point.")
        print("Example: Create an empty file chapters/chapter-1590.txt and run again")
        return
    
    start = last_chapter + 1
    end = last_chapter + CHAPTERS_TO_DOWNLOAD
    
    print(f"Last downloaded: Chapter {last_chapter}")
    print(f"Will download: Chapters {start} to {end}")
    print("-" * 40)
    
    print("Fetching chapter URLs...")
    chapter_urls = get_chapter_urls(start, end)
    
    if not chapter_urls:
        print("Could not find chapter links from the category page.")
        print("Trying fallback: constructing URLs directly...")
        for num in range(start, end + 1):
            url = f"{BASE_URL}/shadow-slave-chapter-{num}/"
            download_chapter(url, num)
    else:
        for num in sorted(chapter_urls.keys()):
            download_chapter(chapter_urls[num], num)
            time.sleep(2)  # be polite to the server
    
    print("-" * 40)
    print(f"Done! Chapters {start}-{end} processed.")

if __name__ == "__main__":
    main()
