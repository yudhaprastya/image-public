# download_images_by_date.py
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
from typing import Iterable

BASE_URL = os.getenv("BASE_URL", "https://storage-media.kejaksaanri.id/absen/upload")
SUFFIXES = os.getenv("SUFFIXES", "in").split(",")  # e.g., "in,out" if you want both
EXT = os.getenv("EXT", "png")  # default file extension
ID_FILE = os.getenv("ID_FILE", "ids.txt")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "60"))
RETRIES = int(os.getenv("HTTP_RETRIES", "2"))  # simple retry for transient errors

def read_ids(path: str) -> Iterable[str]:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: Missing {path}")
        sys.exit(1)
    with p.open() as f:
        for line in f:
            s = line.strip()
            if s:
                yield s

def fetch(url: str, out_path: Path) -> bool:
    tries = 0
    while True:
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("wb") as f:
                    for chunk in r.iterate_content(1024 * 64):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            tries += 1
            if tries > RETRIES:
                print(f"FAIL ({tries}/{RETRIES}): {url} → {e}")
                return False
            else:
                print(f"Retry {tries}/{RETRIES} for {url} due to: {e}")

def main():
    # Today in Asia/Jakarta
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")

    ids = list(read_ids(ID_FILE))
    if not ids:
        print("No IDs found in ids.txt")
        return

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    ok = 0

    for idx, emp_id in enumerate(ids, start=1):
        for sfx in SUFFIXES:
            # Construct daily URL:
            # https://storage-media.kejaksaanri.id/absen/upload/<ID>_<YYYY-MM-DD>_<suffix>.png
            tail = f"{emp_id}_{today}_{sfx.strip()}.{EXT}"
            url = f"{BASE_URL.rstrip('/')}/{tail}"

            # Stable (overwritten daily) and dated copies
            fixed_name = f"{emp_id}-latest-{sfx.strip()}.{EXT}"
            dated_name = f"{emp_id}_{today}_{sfx.strip()}.{EXT}"

            fixed_path = out_dir / fixed_name
            dated_path = out_dir / dated_name

            print(f"[{idx}] Downloading {url} → {fixed_path}")
            total += 1

            if fetch(url, fixed_path):
                # also keep a dated copy (history)
                dated_path.write_bytes(fixed_path.read_bytes())
                ok += 1

    print(f"Done: {ok}/{total} files succeeded.")

if __name__ == "__main__":
    main()
