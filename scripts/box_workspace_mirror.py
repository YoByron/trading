"""Box workspace mirroring functionality."""

from dataclasses import dataclass
from typing import Dict, Any, List
from pathlib import Path


@dataclass
class ManifestEntry:
    """Entry in the workspace manifest."""
    file_id: str
    file_path: str
    checksum: str
    size: int
    last_modified: str
    sync_status: str


@dataclass
class WorkspaceManifest:
    """Manifest of workspace contents."""
    workspace_id: str
    entries: List[ManifestEntry]
    last_sync: str
    version: str


def build_manifest_entries(workspace_path: Path) -> List[ManifestEntry]:
    """Build manifest entries for workspace files."""
    entries = []
    
    if workspace_path.exists():
        for file_path in workspace_path.rglob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                entry = ManifestEntry(
                    file_id=str(hash(str(file_path))),
                    file_path=str(file_path.relative_to(workspace_path)),
                    checksum=f"sha256_{hash(file_path.read_bytes()) % 10000:04d}",
                    size=stat.st_size,
                    last_modified=str(stat.st_mtime),
                    sync_status="synced"
                )
                entries.append(entry)
    
    return entries


def create_workspace_manifest(workspace_id: str, workspace_path: Path) -> WorkspaceManifest:
    """Create a workspace manifest."""
    from datetime import datetime
    
    entries = build_manifest_entries(workspace_path)
    
    return WorkspaceManifest(
        workspace_id=workspace_id,
        entries=entries,
        last_sync=datetime.now().isoformat(),
        version="1.0"
    )


def sync_workspace_files(source_path: Path, target_path: Path) -> Dict[str, Any]:
    """Sync files between workspace directories."""
    if not source_path.exists():
        return {"status": "error", "message": "Source path does not exist"}
    
    target_path.mkdir(parents=True, exist_ok=True)
    synced_files = []
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_path)
            target_file = target_path / relative_path
            
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(file_path.read_bytes())
            synced_files.append(str(relative_path))
    
    return {
        "status": "success",
        "synced_files": synced_files,
        "file_count": len(synced_files)
    }


def validate_workspace_integrity(manifest: WorkspaceManifest, workspace_path: Path) -> bool:
    """Validate workspace integrity against manifest."""
    for entry in manifest.entries:
        file_path = workspace_path / entry.file_path
        if not file_path.exists():
            return False
        
        stat = file_path.stat()
        if stat.st_size != entry.size:
            return False
    
    return True