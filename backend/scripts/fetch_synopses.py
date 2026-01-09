#!/usr/bin/env python3
"""Fetch anime synopses from Jikan API and add them to anime_clean.csv.

Usage examples:
  python backend/scripts/fetch_synopses.py --sample 10
  python backend/scripts/fetch_synopses.py --delay 1 --out data/anime_with_synopsis.csv

This script respects a small delay between requests to avoid hammering the API.
"""

import argparse
import time
import requests
import pandas as pd
import sys
from typing import Optional

API_URL = "https://api.jikan.moe/v4/anime"


def fetch_synopsis(name: str, timeout: int = 10) -> Optional[str]:
    try:
        params = {"q": name, "limit": 1}
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        j = r.json()
        entry = j.get("data") and (j.get("data")[0] if len(j.get("data")) > 0 else None)
        if not entry:
            return None
        return entry.get("synopsis")
    except Exception:
        return None


def main():
    p = argparse.ArgumentParser(description="Enrich anime CSV with synopses from Jikan")
    p.add_argument("--in", dest="infile", default="data/anime_clean.csv", help="input CSV path")
    p.add_argument("--out", dest="outfile", default="data/anime_with_synopsis.csv", help="output CSV path")
    p.add_argument("--sample", type=int, default=0, help="only process first N rows (0 = all)")
    p.add_argument("--start", type=int, default=0, help="start index (0-based)")
    p.add_argument("--delay", type=float, default=1.0, help="seconds to wait between requests")
    p.add_argument("--force", action="store_true", help="refetch synopses even if present")
    args = p.parse_args()

    infile = args.infile
    outfile = args.outfile

    try:
        df = pd.read_csv(infile, dtype=str)
    except FileNotFoundError:
        print(f"Input file not found: {infile}")
        sys.exit(2)

    # Ensure 'name' column exists
    if "name" not in df.columns:
        print("CSV does not contain 'name' column")
        sys.exit(2)

    # Add synopsis column if missing
    if "synopsis" not in df.columns:
        df["synopsis"] = ""

    total = len(df)
    start = max(0, args.start)
    end = total if args.sample <= 0 else min(total, start + args.sample)

    print(f"Processing rows {start}..{end - 1} (total {total}), delay={args.delay}s")

    for idx in range(start, end):
        name = df.at[idx, "name"] if pd.notna(df.at[idx, "name"]) else ""
        if not name:
            continue
        current = df.at[idx, "synopsis"] if pd.notna(df.at[idx, "synopsis"]) else ""
        if current and not args.force:
            continue

        synopsis = fetch_synopsis(name)
        if synopsis:
            df.at[idx, "synopsis"] = synopsis
            print(f"[{idx}] fetched synopsis for: {name}")
        else:
            print(f"[{idx}] no synopsis found for: {name}")

        time.sleep(args.delay)

    # Write out CSV preserving original columns order plus synopsis at end
    try:
        df.to_csv(outfile, index=False)
    except Exception as e:
        print(f"Failed to write output CSV: {e}")
        sys.exit(1)

    print(f"Finished. Output written to {outfile}")


if __name__ == "__main__":
    main()
