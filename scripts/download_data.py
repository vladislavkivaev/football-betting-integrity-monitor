import requests
import time
from pathlib import Path

# Leagues and seasons to download
LEAGUES = ["D1", "E0", "T1", "G1"]  # Bundesliga, EPL, Turkey, Greece
SEASONS = [
    "1718", "1819", "1920", "2021",
    "2122", "2223", "2324", "2425", "2526"
]  # 9 seasons: 2017/18 → 2025/26

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
OUTPUT_DIR = Path("data/raw")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.football-data.co.uk/"
}

def download_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success, skipped, failed = 0, 0, 0

    for season in SEASONS:
        for league in LEAGUES:
            url = BASE_URL.format(season=season, league=league)
            filename = OUTPUT_DIR / f"{league}_{season}.csv"

            if filename.exists():
                print(f"[SKIP]  {filename.name}")
                skipped += 1
                continue

            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                filename.write_bytes(response.content)
                print(f"[OK]    {filename.name}")
                success += 1
            except requests.HTTPError as e:
                print(f"[FAIL]  {league}_{season}.csv — {e}")
                failed += 1
            except Exception as e:
                print(f"[ERROR] {league}_{season}.csv — {e}")
                failed += 1

            time.sleep(1)

    print(f"\nDone: {success} downloaded, {skipped} skipped, {failed} failed")
    print(f"Files in data/raw/: {len(list(OUTPUT_DIR.glob('*.csv')))}")

if __name__ == "__main__":
    download_all()