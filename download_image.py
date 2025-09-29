# download_images_by_date.py
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

BASE_URL = os.getenv("BASE_URL", "https://storage-media.kejaksaanri.id/absen/upload").rstrip("/")
SUFFIXES = [s.strip() for s in os.getenv("SUFFIXES", "in").split(",") if s.strip()]
EXT = os.getenv("EXT", "png").lstrip(".")
ID_FILE = os.getenv("ID_FILE", "ids.txt")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "60"))
RETRIES = int(os.getenv("HTTP_RETRIES", "2"))

# Optional: override the date for testing: YYYY-MM-DD
DATE_OVERRIDE = os.getenv("DATE_OVERRIDE", "").strip()

def today_str():
    if DATE_OVERRIDE:
        return DATE_OVERRIDE
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")

def read_ids():
    p = Path(ID_FILE)
    if not p.exists():
        print(f"ERROR: Missing {ID_FILE}")
        sys.exit(3)
    ids = [line.strip() for line in p.read_text().splitlines() if line.strip()]
    return ids

def fetch(url: str, out_path: Path) -> bool:
    tries = 0
    while True:
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("wb") as f:
                    for chunk in r.iter_content(1024 * 64):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            tries += 1
            if tries > RETRIES:
                print(f"[FAIL] {url} -> {e}")
                return False
            print(f"[Retry {tries}/{RETRIES}] {url} -> {e}")

def main():
    date_str = today_str()
    ids = read_ids()
    if not ids:
        print("ERROR: ids.txt has no IDs")
        sys.exit(4)

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    total_attempts = 0
    successes = 0
    failures = 0

    print(f"Config -> BASE_URL={BASE_URL}, EXT=.{EXT}, SUFFIXES={SUFFIXES}, DATE={date_str}")
    print(f"IDs -> count={len(ids)}")

    for emp_id in ids:
        for sfx in SUFFIXES:
            tail = f"{emp_id}_{date_str}_{sfx}.{EXT}"
            url = f"{BASE_URL}/{tail}"
   # overwritten daily
            dated_name = f"{emp_id}_{date_str}_{sfx}.{EXT}"  # history

            dated_path = out_dir / dated_name

            total_attempts += 1
            print(f"[GET] {url}")

            if fetch(url, dated_path):
                dated_path.write_bytes(dated_path.read_bytes())
                successes += 1
            else:
                failures += 1

    print(f"Summary: attempts={total_attempts}, success={successes}, fail={failures}")

    # Exit code rules:
    # - If at least 1 succeeded, return 0 (let the workflow continue / upload what we have)
    # - If none succeeded, return 1 (surface the problem)
    if successes == 0:
        print("ERROR: No images were successfully downloaded.")
        sys.exit(1)

if __name__ == "__main__":
    main()
