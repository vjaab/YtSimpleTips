# -*- coding: utf-8 -*-
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from screenshot_gen import capture_article_screenshot

def main():
    print("📸 Capturing screenshot of GitHub Trending...")
    path = capture_article_screenshot("https://github.com/trending", "github_trending.png", desktop=True)
    if path and os.path.exists(path):
        print(f"✅ Screenshot captured successfully at: {path}")
    else:
        print("❌ Screenshot capture failed.")

if __name__ == "__main__":
    main()
