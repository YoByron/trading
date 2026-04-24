import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

class ManifestEntry:
    def __init__(self, file_path: str, file_hash: str, size: int):
        self.file_path = file_path
        self.file_hash = file_hash
        self.size = size
        self.last_modified = ""
        self.metadata: Dict[str, Any] = {}

def build_manifest_entries(workspace_path: Path) -> List[ManifestEntry]:
    """Build manifest entries for workspace files."""
    entries = []
    
    if not workspace_path.exists():
        return entries
    
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file():
            try:
                content = file_path.read_bytes()
                file_hash = hashlib.md5(content).hexdigest()
                size = len(content)
                
                entry = ManifestEntry(
                    file_path=str(file_path.relative_to(workspace_path)),
                    file_hash=file_hash,
                    size=size
                )
                entries.append(entry)
            except Exception:
                continue
    
    return entries

class BoxWorkspaceMirror:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.manifest_entries: List[ManifestEntry] = []

    def sync_workspace(self) -> bool:
        try:
            self.manifest_entries = build_manifest_entries(self.workspace_path)
            return True
        except Exception:
            return False

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "entries": [
                {
                    "path": entry.file_path,
                    "hash": entry.file_hash,
                    "size": entry.size
                }
                for entry in self.manifest_entries
            ]
        }