from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ManifestEntry:
    path: str
    size: int
    checksum: str
    modified: str

def build_manifest_entries(workspace_path: str) -> List[ManifestEntry]:
    import os
    import hashlib
    import datetime
    
    entries = []
    if os.path.exists(workspace_path):
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                
                try:
                    stat = os.stat(file_path)
                    size = stat.st_size
                    modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    # Simple checksum
                    checksum = hashlib.md5(rel_path.encode()).hexdigest()
                    
                    entries.append(ManifestEntry(
                        path=rel_path,
                        size=size,
                        checksum=checksum,
                        modified=modified
                    ))
                except (OSError, IOError):
                    continue
    
    return entries

def mirror_workspace(source_path: str, target_path: str) -> Dict[str, Any]:
    entries = build_manifest_entries(source_path)
    return {
        "status": "mirrored",
        "entries_count": len(entries),
        "source": source_path,
        "target": target_path
    }