"""Box workspace mirroring utilities."""
import os
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MirrorEntry:
    """Represents a file or folder in the mirror."""
    path: str
    size: Optional[int]
    last_modified: datetime
    checksum: Optional[str] = None
    is_directory: bool = False


@dataclass
class MirrorState:
    """State of the workspace mirror."""
    entries: List[MirrorEntry]
    last_sync: datetime
    sync_status: str = "pending"


def calculate_file_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return ""


def scan_local_workspace(workspace_path: str) -> List[MirrorEntry]:
    """Scan local workspace and create mirror entries."""
    entries = []
    
    if not os.path.exists(workspace_path):
        return entries
        
    for root, dirs, files in os.walk(workspace_path):
        # Add directories
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(dir_path, workspace_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(dir_path))
            
            entries.append(MirrorEntry(
                path=rel_path,
                size=None,
                last_modified=mod_time,
                is_directory=True
            ))
            
        # Add files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(file_path, workspace_path)
            
            try:
                stat = os.stat(file_path)
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                checksum = calculate_file_checksum(file_path)
                
                entries.append(MirrorEntry(
                    path=rel_path,
                    size=stat.st_size,
                    last_modified=mod_time,
                    checksum=checksum,
                    is_directory=False
                ))
            except Exception:
                continue
                
    return entries


def create_mirror_state(workspace_path: str) -> MirrorState:
    """Create a mirror state for the workspace."""
    entries = scan_local_workspace(workspace_path)
    return MirrorState(
        entries=entries,
        last_sync=datetime.now(),
        sync_status="completed"
    )


def compare_mirror_states(old_state: MirrorState, new_state: MirrorState) -> Dict[str, List[str]]:
    """Compare two mirror states and return differences."""
    old_paths = {entry.path: entry for entry in old_state.entries}
    new_paths = {entry.path: entry for entry in new_state.entries}
    
    added = []
    removed = []
    modified = []
    
    # Find added files
    for path in new_paths:
        if path not in old_paths:
            added.append(path)
            
    # Find removed files
    for path in old_paths:
        if path not in new_paths:
            removed.append(path)
            
    # Find modified files
    for path in new_paths:
        if path in old_paths:
            old_entry = old_paths[path]
            new_entry = new_paths[path]
            
            if (not old_entry.is_directory and 
                old_entry.checksum != new_entry.checksum):
                modified.append(path)
                
    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }


if __name__ == "__main__":
    workspace_path = "."
    state = create_mirror_state(workspace_path)
    print(f"Mirror created with {len(state.entries)} entries")