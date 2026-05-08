import requests
from bs4 import BeautifulSoup
import os
import time
import re

# Base URL and chapter range
BASE_URL = "https://yournovel.org"
NOVEL_SLUG = "shadow-slave"
CHAPTER_START = 1591
CHAPTER_END = 1620
OUTPUT_DIR = "chapters"

def get_chapter_urls():
    """Scrape chapter links from the novel's page and return a dict of {number: url}."""
    url = f"{BASE_URL}/category/{NOVEL_SLUG}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    chapter_links = {}
    # Find all <a> tags that look like chapter links
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Match pattern: shadow-slave-chapter-{number}-{slug}/
        match = re.search(r'shadow-slave-chapter-(\d+)-([\w-]+)/', href)
        if match:
            chapter_num = int(match.group(1))
            if CHAPTER_START <= chapter_num <= CHAPTER_END:
                full_url = href if href.startswith('http') else BASE_URL + href
                chapter_links[chapter_num] = full_url
    
    return chapter_links

def scrape_chapter(url, number):
    """Download a single chapter and save it as a .txt file."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the main content (adjust selector if needed)
        content_div = soup.find('div', class_='entry-content')
        if not content_div:
            content_div = soup.find('article')
        
        if content_div:
            text = content_div.get_text(strip=True)
            # Optionally clean up the text
            text = re.sub(r'\n+', '\n', text)
            
            filename = f"{OUTPUT_DIR}/chapter-{number:04d}.txt"
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Chapter {number}\n\n{text}")
            print(f"Downloaded chapter {number}")
        else:
            print(f"Failed to extract content for chapter {number}")
    except Exception as e:
        print(f"Error downloading chapter {number}: {e}")

def main():
    print(f"Fetching chapter list from {NOVEL_SLUG}...")
    chapter_urls = get_chapter_urls()
    
    if not chapter_urls:
        print("No chapter URLs found. The site structure might have changed.")
        # Fallback: attempt to construct URLs directly
        print("Attempting fallback URL pattern...")
        for num in range(CHAPTER_START, CHAPTER_END + 1):
            # We'll try a common slug pattern; may require manual update
            fallback_url = f"{BASE_URL}/shadow-slave-chapter-{num}/"
            scrape_chapter(fallback_url, num)
    else:
        for num in sorted(chapter_urls.keys()):
            scrape_chapter(chapter_urls[num], num)
            time.sleep(2)  # Be polite to the server

if __name__ == "__main__":
    main()
