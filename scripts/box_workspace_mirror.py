import os
import shutil
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class MirrorEntry:
    source_path: str
    target_path: str
    file_type: str
    size: int
    modified: datetime
    sync_status: str


@dataclass
class SyncResult:
    success: bool
    entries_synced: int
    errors: List[str]
    duration: float


class BoxWorkspaceMirror:
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.mirror_entries: List[MirrorEntry] = []
    
    def scan_source_directory(self) -> List[MirrorEntry]:
        entries = []
        
        if not self.source_dir.exists():
            return entries
        
        for file_path in self.source_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.source_dir)
                target_path = self.target_dir / relative_path
                
                entry = MirrorEntry(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    file_type=file_path.suffix or "unknown",
                    size=file_path.stat().st_size,
                    modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                    sync_status="pending"
                )
                entries.append(entry)
        
        self.mirror_entries = entries
        return entries
    
    def sync_file(self, entry: MirrorEntry) -> bool:
        try:
            target_path = Path(entry.target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry.source_path, entry.target_path)
            entry.sync_status = "synced"
            return True
        except Exception:
            entry.sync_status = "failed"
            return False
    
    def execute_mirror_sync(self) -> SyncResult:
        start_time = datetime.now()
        errors = []
        synced_count = 0
        
        entries = self.scan_source_directory()
        
        for entry in entries:
            if self.sync_file(entry):
                synced_count += 1
            else:
                errors.append(f"Failed to sync: {entry.source_path}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SyncResult(
            success=len(errors) == 0,
            entries_synced=synced_count,
            errors=errors,
            duration=duration
        )
    
    def get_mirror_status(self) -> Dict[str, int]:
        status_counts = {}
        for entry in self.mirror_entries:
            status_counts[entry.sync_status] = status_counts.get(entry.sync_status, 0) + 1
        return status_counts


def create_workspace_mirror(source: str, target: str) -> BoxWorkspaceMirror:
    return BoxWorkspaceMirror(source, target)


def main():
    mirror = BoxWorkspaceMirror("./source", "./target")
    result = mirror.execute_mirror_sync()
    print(f"Sync completed: {result.entries_synced} files in {result.duration:.2f}s")
    if result.errors:
        print(f"Errors: {len(result.errors)}")


if __name__ == "__main__":
    main()