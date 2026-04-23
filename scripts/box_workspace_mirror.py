import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import shutil

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class MirrorEntry:
    """Entry representing a file/folder to be mirrored."""
    source_path: Path
    target_path: Path
    is_directory: bool
    last_modified: Optional[float] = None
    size: Optional[int] = None
    checksum: Optional[str] = None

class BoxWorkspaceMirror:
    """Mirror Box workspace files to local filesystem."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or REPO_ROOT / "config" / "box_mirror.json"
        self.config = self._load_config()
        self.mirror_entries: List[MirrorEntry] = []
    
    def _load_config(self) -> Dict:
        """Load mirror configuration."""
        if not self.config_path.exists():
            return {
                "source_folder": "/Box/Trading Workspace",
                "target_folder": str(REPO_ROOT / "data" / "box_mirror"),
                "exclude_patterns": ["*.tmp", "~*", ".DS_Store"],
                "include_extensions": [".pdf", ".xlsx", ".docx", ".txt", ".md"]
            }
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def scan_source(self) -> List[MirrorEntry]:
        """Scan source directory for files to mirror."""
        source_path = Path(self.config["source_folder"])
        target_base = Path(self.config["target_folder"])
        entries = []
        
        if not source_path.exists():
            print(f"Source path does not exist: {source_path}")
            return entries
        
        for item in source_path.rglob("*"):
            if self._should_include(item):
                relative_path = item.relative_to(source_path)
                target_path = target_base / relative_path
                
                entry = MirrorEntry(
                    source_path=item,
                    target_path=target_path,
                    is_directory=item.is_dir(),
                    last_modified=item.stat().st_mtime if item.exists() else None,
                    size=item.stat().st_size if item.is_file() else None
                )
                entries.append(entry)
        
        self.mirror_entries = entries
        return entries
    
    def _should_include(self, path: Path) -> bool:
        """Check if path should be included in mirror."""
        # Check exclude patterns
        for pattern in self.config["exclude_patterns"]:
            if path.match(pattern):
                return False
        
        # For files, check extensions
        if path.is_file():
            extensions = self.config["include_extensions"]
            if extensions and path.suffix.lower() not in extensions:
                return False
        
        return True
    
    def sync_files(self) -> Dict[str, int]:
        """Sync files from source to target."""
        stats = {"copied": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        for entry in self.mirror_entries:
            try:
                if entry.is_directory:
                    entry.target_path.mkdir(parents=True, exist_ok=True)
                    stats["skipped"] += 1
                else:
                    self._sync_file(entry, stats)
            except Exception as e:
                print(f"Error syncing {entry.source_path}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def _sync_file(self, entry: MirrorEntry, stats: Dict[str, int]):
        """Sync a single file."""
        entry.target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not entry.target_path.exists():
            shutil.copy2(entry.source_path, entry.target_path)
            stats["copied"] += 1
        elif entry.last_modified and entry.target_path.stat().st_mtime < entry.last_modified:
            shutil.copy2(entry.source_path, entry.target_path)
            stats["updated"] += 1
        else:
            stats["skipped"] += 1

def main() -> bool:
    """Main entry point for Box workspace mirror."""
    mirror = BoxWorkspaceMirror()
    
    print("Scanning source directory...")
    entries = mirror.scan_source()
    print(f"Found {len(entries)} items to process")
    
    if entries:
        print("Syncing files...")
        stats = mirror.sync_files()
        print(f"Sync complete: {stats}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)