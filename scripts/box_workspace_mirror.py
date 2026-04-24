import os
import shutil
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class MirrorEntry:
    source_path: str
    destination_path: str
    last_synced: str
    status: str
    file_size: int

@dataclass
class SyncReport:
    total_files: int
    synced_files: int
    failed_files: int
    errors: List[str]
    duration: float

def scan_workspace(workspace_path: str) -> List[str]:
    """Scan workspace directory and return list of files."""
    files = []
    for root, dirs, filenames in os.walk(workspace_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in filenames:
            if not filename.startswith('.'):
                file_path = os.path.join(root, filename)
                files.append(file_path)
    
    return files

def create_mirror_entry(source_path: str, destination_path: str) -> MirrorEntry:
    """Create a mirror entry for a file."""
    file_size = 0
    status = "PENDING"
    
    try:
        if os.path.exists(source_path):
            file_size = os.path.getsize(source_path)
            status = "READY"
    except Exception:
        status = "ERROR"
    
    return MirrorEntry(
        source_path=source_path,
        destination_path=destination_path,
        last_synced=datetime.now().isoformat(),
        status=status,
        file_size=file_size
    )

def sync_file(entry: MirrorEntry) -> bool:
    """Sync a single file from source to destination."""
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(entry.destination_path)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy file
        shutil.copy2(entry.source_path, entry.destination_path)
        entry.status = "SYNCED"
        entry.last_synced = datetime.now().isoformat()
        return True
    except Exception:
        entry.status = "FAILED"
        return False

def mirror_workspace(source_dir: str, destination_dir: str) -> SyncReport:
    """Mirror workspace from source to destination."""
    start_time = datetime.now()
    files = scan_workspace(source_dir)
    entries = []
    errors = []
    synced_count = 0
    
    for file_path in files:
        rel_path = os.path.relpath(file_path, source_dir)
        dest_path = os.path.join(destination_dir, rel_path)
        
        entry = create_mirror_entry(file_path, dest_path)
        entries.append(entry)
        
        if entry.status == "READY":
            if sync_file(entry):
                synced_count += 1
            else:
                errors.append(f"Failed to sync {file_path}")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return SyncReport(
        total_files=len(files),
        synced_files=synced_count,
        failed_files=len(files) - synced_count,
        errors=errors,
        duration=duration
    )

def validate_mirror(source_dir: str, destination_dir: str) -> Dict[str, bool]:
    """Validate that mirror is consistent with source."""
    results = {}
    source_files = scan_workspace(source_dir)
    
    for source_file in source_files:
        rel_path = os.path.relpath(source_file, source_dir)
        dest_file = os.path.join(destination_dir, rel_path)
        
        # Check if destination file exists and has same size
        if os.path.exists(dest_file):
            source_size = os.path.getsize(source_file)
            dest_size = os.path.getsize(dest_file)
            results[rel_path] = source_size == dest_size
        else:
            results[rel_path] = False
    
    return results