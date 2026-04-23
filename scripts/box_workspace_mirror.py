#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import List, Dict

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def build_manifest_entries() -> List[Dict]:
    """Build manifest entries for box workspace mirror."""
    entries = []
    
    # Scan workspace directory for files
    workspace_dir = REPO_ROOT / "workspace"
    if workspace_dir.exists():
        for file_path in workspace_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(workspace_dir)
                entries.append({
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
    
    return entries

def main():
    """Main entry point for box workspace mirror."""
    entries = build_manifest_entries()
    print(f"Built {len(entries)} manifest entries")

if __name__ == "__main__":
    main()