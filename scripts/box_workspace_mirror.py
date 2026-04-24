import os
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ManifestEntry:
    file_path: str
    file_hash: str
    size: int
    last_modified: str
    metadata: Dict[str, Any]

@dataclass
class WorkspaceMirror:
    source_path: str
    mirror_path: str
    manifest: List[ManifestEntry]
    sync_timestamp: str
    metadata: Dict[str, Any]

class BoxWorkspaceMirror:
    """Box workspace mirroring utility"""
    
    def __init__(self, source_dir: str, mirror_dir: str):
        self.source_dir = source_dir
        self.mirror_dir = mirror_dir
        self.manifest_entries: List[ManifestEntry] = []
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def create_manifest_entry(self, file_path: str) -> Optional[ManifestEntry]:
        """Create a manifest entry for a file"""
        if not os.path.exists(file_path):
            return None
            
        try:
            stat = os.stat(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            return ManifestEntry(
                file_path=file_path,
                file_hash=file_hash,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                metadata={"type": "file"}
            )
        except Exception:
            return None
    
    def build_manifest_entries(self, directory: str) -> List[ManifestEntry]:
        """Build manifest entries for all files in directory"""
        entries = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                entry = self.create_manifest_entry(file_path)
                if entry:
                    entries.append(entry)
        
        self.manifest_entries = entries
        return entries
    
    def create_workspace_mirror(self) -> WorkspaceMirror:
        """Create a complete workspace mirror"""
        manifest = self.build_manifest_entries(self.source_dir)
        
        return WorkspaceMirror(
            source_path=self.source_dir,
            mirror_path=self.mirror_dir,
            manifest=manifest,
            sync_timestamp=datetime.now().isoformat(),
            metadata={"version": "1.0", "total_files": len(manifest)}
        )
    
    def save_manifest(self, mirror: WorkspaceMirror, manifest_path: str) -> None:
        """Save manifest to JSON file"""
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, 'w') as f:
            json.dump(asdict(mirror), f, indent=2)

def build_manifest_entries(directory: str) -> List[ManifestEntry]:
    """Standalone function to build manifest entries"""
    mirror = BoxWorkspaceMirror(directory, "")
    return mirror.build_manifest_entries(directory)

def create_workspace_mirror(source_dir: str, mirror_dir: str) -> BoxWorkspaceMirror:
    """Factory function to create workspace mirror"""
    return BoxWorkspaceMirror(source_dir, mirror_dir)

def main():
    """Main function for testing workspace mirroring"""
    mirror = create_workspace_mirror("src", "mirror")
    workspace_mirror = mirror.create_workspace_mirror()
    print(f"Created mirror with {len(workspace_mirror.manifest)} files")

if __name__ == "__main__":
    main()