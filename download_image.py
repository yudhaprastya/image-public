# download_image.py
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

IMAGE_URL = os.getenv("IMAGE_URL")
if not IMAGE_URL:
    print("ERROR: IMAGE_URL env var is required.")
    sys.exit(1)

# Timestamp in Asia/Jakarta
ts = datetime.now(ZoneInfo("Asia/Jakarta"))
stamp = ts.strftime("%Y-%m-%d")

out_dir = Path("out")
out_dir.mkdir(parents=True, exist_ok=True)

# Fixed filename for a stable public URL
fixed_name = "image-latest.jpg"
fixed_path = out_dir / fixed_name

# Also keep a dated copy if you want history (optional)
url_tail = IMAGE_URL.rstrip("/").split("/")[-1] or "image.jpg"
if "." in url_tail:
    base, ext = url_tail.rsplit(".", 1)
    dated_name = f"{base}_{stamp}.{ext}"
else:
    dated_name = f"image_{stamp}.jpg"
dated_path = out_dir / dated_name

print(f"Downloading {IMAGE_URL} → {fixed_path} and {dated_path}")

try:
    with requests.get(IMAGE_URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        # Save fixed (latest)
        with open(fixed_path, "wb") as f:
            for chunk in r.iter_content(1024 * 64):
                if chunk:
                    f.write(chunk)
    # Copy to dated filename
    with open(fixed_path, "rb") as src, open(dated_path, "wb") as dst:
        dst.write(src.read())

    print("Download complete.")
except Exception as e:
    print("Download failed:", e)
    sys.exit(2)
