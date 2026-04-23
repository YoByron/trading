#!/usr/bin/env python3

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@dataclass
class MirrorEntry:
    """Represents a file/folder in the Box workspace mirror."""
    local_path: Path
    box_path: str
    file_type: str  # 'file' or 'folder'
    size: Optional[int] = None
    last_modified: Optional[str] = None
    synced: bool = False

class BoxWorkspaceMirror:
    """Manages local mirror of Box workspace."""
    
    def __init__(self, local_root: Path, box_root: str = "/"):
        self.local_root = Path(local_root)
        self.box_root = box_root
        self.entries: List[MirrorEntry] = []
        
    def scan_local_files(self) -> List[MirrorEntry]:
        """Scan local directory and create mirror entries."""
        entries = []
        
        if not self.local_root.exists():
            return entries
            
        for item in self.local_root.rglob("*"):
            relative_path = item.relative_to(self.local_root)
            box_path = str(relative_path).replace("\\", "/")
            
            if item.is_file():
                entry = MirrorEntry(
                    local_path=item,
                    box_path=f"{self.box_root.rstrip('/')}/{box_path}",
                    file_type="file",
                    size=item.stat().st_size,
                    last_modified=str(item.stat().st_mtime)
                )
            else:
                entry = MirrorEntry(
                    local_path=item,
                    box_path=f"{self.box_root.rstrip('/')}/{box_path}",
                    file_type="folder"
                )
                
            entries.append(entry)
            
        self.entries = entries
        return entries
        
    def create_mirror_manifest(self, output_path: Path):
        """Create a JSON manifest of the mirror."""
        manifest = {
            "local_root": str(self.local_root),
            "box_root": self.box_root,
            "entry_count": len(self.entries),
            "entries": [
                {
                    "local_path": str(entry.local_path),
                    "box_path": entry.box_path,
                    "file_type": entry.file_type,
                    "size": entry.size,
                    "last_modified": entry.last_modified,
                    "synced": entry.synced
                }
                for entry in self.entries
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

def main():
    """Main entry point."""
    print("Creating Box Workspace Mirror...")
    
    # Setup paths
    local_workspace = REPO_ROOT / "workspace"
    manifest_path = REPO_ROOT / "data" / "box_mirror_manifest.json"
    
    # Create mirror
    mirror = BoxWorkspaceMirror(local_workspace, "/trading-workspace")
    entries = mirror.scan_local_files()
    
    print(f"Scanned {len(entries)} items in local workspace")
    
    # Create manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    mirror.create_mirror_manifest(manifest_path)
    
    print(f"Mirror manifest created: {manifest_path}")

if __name__ == "__main__":
    main()