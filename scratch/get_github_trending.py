# -*- coding: utf-8 -*-
import requests
import re

def fetch():
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching trending: {r.status_code}")
        return

    content = r.text
    print("Page length:", len(content))
    
    # Print first few h2 tags or article tags to inspect
    h2_tags = re.findall(r'<h2[^>]*>.*?</h2>', content, re.DOTALL)
    print(f"Found {len(h2_tags)} h2 tags:")
    for tag in h2_tags[:10]:
        print("-", tag.strip().replace("\n", " "))
        
    # Check for Box-row or article
    articles = re.findall(r'<article[^>]*>.*?</article>', content, re.DOTALL)
    print(f"Found {len(articles)} article tags.")
    if articles:
        print("First article tag snippet:")
        print(articles[0][:800].replace("\n", " "))

if __name__ == "__main__":
    fetch()
