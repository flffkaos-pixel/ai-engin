"""
Batch translator: reads all en.md files under phases/ and writes ko.md files.
Translates in batches using the session's LLM via hermes_tools.
"""
import os
import json
import time
from pathlib import Path

BASE = Path(r"C:\Users\중진공39\ai-engineering-from-scratch\md_docs\phases")

def find_en_files():
    """Find all en.md files under phases/"""
    files = sorted(BASE.rglob("en.md"))  # changed from glob to rglob for deep subdirs
    return files

def main():
    files = find_en_files()
    print(f"Found {len(files)} en.md files")
    
    # Output the file list as JSON for the agent to consume
    file_list = []
    for f in files:
        rel = f.relative_to(BASE)
        file_list.append({
            "path": str(f),
            "rel": str(rel),
            "parent": str(f.parent),
        })
    
    print(json.dumps(file_list, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()