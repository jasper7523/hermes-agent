import os
import json
import shutil
from pathlib import Path

TRANSCRIPT_PATH = Path("C:/Users/promy/.gemini/antigravity-ide/brain/e4c99172-6a55-4cf0-82b8-e0978d7c6361/.system_generated/logs/transcript.jsonl")
BACKUP_PATH = TRANSCRIPT_PATH.with_suffix(".jsonl.bak")

def main():
    if not TRANSCRIPT_PATH.exists():
        print(f"[ERROR] Transcript not found at {TRANSCRIPT_PATH}")
        return

    # Create backup if not exists
    if not BACKUP_PATH.exists():
        shutil.copy2(TRANSCRIPT_PATH, BACKUP_PATH)
        print(f"[BACKUP] Created backup of transcript at {BACKUP_PATH}")
    else:
        print(f"[INFO] Backup already exists at {BACKUP_PATH}")

    # Read and filter
    lines = open(TRANSCRIPT_PATH, "r", encoding="utf-8", errors="ignore").readlines()
    print(f"[INFO] Total lines to process: {len(lines)}")

    success_lines = []
    skipped_count = 0

    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            # Test JSON load
            json.loads(line_str)
            success_lines.append(line_str)
        except json.JSONDecodeError as e:
            print(f"[WARNING] Skipping Line {idx} due to JSONDecodeError: {e}")
            skipped_count += 1

    # Write back
    with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
        for line in success_lines:
            f.write(line + "\n")

    print(f"[DONE] Successfully repaired transcript. jsonl.")
    print(f"       Retained: {len(success_lines)} lines")
    print(f"       Skipped: {skipped_count} invalid JSON lines")

if __name__ == "__main__":
    main()
