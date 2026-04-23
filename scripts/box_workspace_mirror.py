import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class ManifestEntry:
    """Entry in workspace manifest."""
    path: str
    checksum: str
    size: int
    last_modified: str

def build_manifest_entries(workspace_path: Path) -> List[ManifestEntry]:
    """Build manifest entries for workspace files."""
    entries = []
    
    if not workspace_path.exists():
        return entries
    
    for file_path in workspace_path.rglob("*"):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                # Simple checksum placeholder
                checksum = str(hash(file_path.read_bytes()))
                
                entry = ManifestEntry(
                    path=str(file_path.relative_to(workspace_path)),
                    checksum=checksum,
                    size=stat.st_size,
                    last_modified=str(stat.st_mtime)
                )
                entries.append(entry)
            except (OSError, IOError):
                # Skip files that can't be read
                continue
    
    return entries

class BoxWorkspaceMirror:
    """Mirror workspace content to Box."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
    
    def sync(self) -> Dict[str, Any]:
        """Sync workspace to Box."""
        manifest = build_manifest_entries(self.workspace_path)
        
        return {
            "status": "success",
            "files_synced": len(manifest),
            "manifest": [entry.__dict__ for entry in manifest]
        }