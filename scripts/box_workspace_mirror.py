import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import json

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class ManifestEntry:
    """Entry in workspace manifest"""
    path: str
    size: int
    modified: str
    checksum: str

def build_manifest_entries(workspace_path: str) -> List[ManifestEntry]:
    """Build manifest entries for workspace files"""
    entries = []
    workspace = Path(workspace_path)
    
    if not workspace.exists():
        return entries
    
    for file_path in workspace.rglob('*'):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                relative_path = str(file_path.relative_to(workspace))
                
                entry = ManifestEntry(
                    path=relative_path,
                    size=stat.st_size,
                    modified=str(stat.st_mtime),
                    checksum=str(hash(file_path.read_bytes()))
                )
                entries.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    return entries

def sync_workspace_to_box(workspace_path: str, box_folder_id: str) -> Dict[str, Any]:
    """Sync workspace to Box folder"""
    entries = build_manifest_entries(workspace_path)
    
    manifest = {
        'workspace_path': workspace_path,
        'box_folder_id': box_folder_id,
        'total_files': len(entries),
        'entries': [
            {
                'path': entry.path,
                'size': entry.size,
                'modified': entry.modified,
                'checksum': entry.checksum
            }
            for entry in entries
        ]
    }
    
    # Save manifest
    manifest_path = Path(workspace_path) / 'box_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    """Main function for Box workspace mirror"""
    workspace_path = "workspace"
    box_folder_id = "123456789"
    
    manifest = sync_workspace_to_box(workspace_path, box_folder_id)
    print(f"Synced {manifest['total_files']} files to Box folder {box_folder_id}")

if __name__ == "__main__":
    main()