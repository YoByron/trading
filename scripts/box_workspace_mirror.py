import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import shutil

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@dataclass
class MirrorEntry:
    source_path: str
    destination_path: str
    last_sync: Optional[str] = None
    sync_status: str = "pending"
    file_size: int = 0

def create_mirror_entry(source: str, destination: str) -> MirrorEntry:
    """Create a new mirror entry"""
    source_path = Path(source)
    file_size = source_path.stat().st_size if source_path.exists() else 0
    
    return MirrorEntry(
        source_path=source,
        destination_path=destination,
        file_size=file_size
    )

def sync_file(entry: MirrorEntry) -> bool:
    """Sync a single file from source to destination"""
    source_path = Path(entry.source_path)
    dest_path = Path(entry.destination_path)
    
    if not source_path.exists():
        entry.sync_status = "source_not_found"
        return False
    
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        entry.sync_status = "synced"
        
        import datetime
        entry.last_sync = datetime.datetime.now().isoformat()
        return True
        
    except Exception as e:
        entry.sync_status = f"error: {str(e)}"
        return False

def mirror_workspace(source_dir: str, destination_dir: str) -> List[MirrorEntry]:
    """Mirror entire workspace from source to destination"""
    source_path = Path(source_dir)
    dest_path = Path(destination_dir)
    
    mirror_entries = []
    
    if not source_path.exists():
        print(f"Source directory {source_dir} does not exist")
        return mirror_entries
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_path)
            dest_file = dest_path / relative_path
            
            entry = create_mirror_entry(str(file_path), str(dest_file))
            sync_file(entry)
            mirror_entries.append(entry)
    
    return mirror_entries

def save_mirror_log(entries: List[MirrorEntry], log_file: str = "mirror_log.json"):
    """Save mirror entries to log file"""
    log_data = []
    
    for entry in entries:
        log_data.append({
            'source_path': entry.source_path,
            'destination_path': entry.destination_path,
            'last_sync': entry.last_sync,
            'sync_status': entry.sync_status,
            'file_size': entry.file_size
        })
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    """Main entry point for box workspace mirror"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mirror Box Workspace')
    parser.add_argument('--source', '-s', required=True,
                       help='Source directory to mirror')
    parser.add_argument('--destination', '-d', required=True,
                       help='Destination directory for mirror')
    parser.add_argument('--log', '-l', default='mirror_log.json',
                       help='Log file for mirror operations')
    
    args = parser.parse_args()
    
    entries = mirror_workspace(args.source, args.destination)
    save_mirror_log(entries, args.log)
    
    synced_count = sum(1 for entry in entries if entry.sync_status == "synced")
    print(f"Mirror complete: {synced_count}/{len(entries)} files synced")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())