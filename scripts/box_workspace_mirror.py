from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


@dataclass
class MirrorEntry:
    local_path: str
    remote_path: str
    last_sync: datetime
    size_bytes: int
    status: str


class BoxWorkspaceMirror:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.entries: List[MirrorEntry] = []
    
    def sync_workspace(self) -> Dict[str, Any]:
        """Sync the workspace with Box."""
        # Mock implementation
        for root, dirs, files in os.walk(self.workspace_path):
            for file in files:
                local_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(local_path)
                    entry = MirrorEntry(
                        local_path=local_path,
                        remote_path=f"/box/{file}",
                        last_sync=datetime.now(),
                        size_bytes=size,
                        status="synced"
                    )
                    self.entries.append(entry)
                except OSError:
                    continue
        
        return {
            'synced_files': len(self.entries),
            'total_size': sum(e.size_bytes for e in self.entries),
            'status': 'completed'
        }


def create_mirror(workspace_path: str) -> BoxWorkspaceMirror:
    """Create a new Box workspace mirror."""
    return BoxWorkspaceMirror(workspace_path)