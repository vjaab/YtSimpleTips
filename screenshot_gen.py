import os
import subprocess
import requests
from config import ASSETS_DIR

def capture_article_screenshot(url, output_filename, desktop=False):
    """
    Captures a screenshot of the article URL using Playwright via npx.
    """
    if not url:
        return None
    
    try:
        resp = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, allow_redirects=True)
        if resp.status_code >= 400:
            print(f"⚠️ URL unreachable or 404: {url} (Status: {resp.status_code})")
            return None
    except Exception as e:
        print(f"⚠️ URL pre-flight check failed for {url}: {e}")
        pass

    output_path = os.path.join(ASSETS_DIR, "screenshots", output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    viewport = "1920,1080" if desktop else "1080,1920"
    
    cmd = [
        "npx", "-y", "playwright", "screenshot",
        f"--viewport-size={viewport}",
        "--wait-for-timeout=8000",
        url,
        output_path
    ]
    
    try:
        print(f"📸 Capturing screenshot: {url} -> {output_path}")
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"❌ Screenshot capture failed for {url}: {e}")
        
    return None
