from typing import Dict, Any, List
from dataclasses import dataclass
import os

@dataclass
class MirrorEntry:
    source_path: str
    target_path: str
    file_hash: str
    last_synced: str
    sync_status: str

@dataclass
class SyncResult:
    success: bool
    entries_synced: int
    errors: List[str]
    timestamp: str

class BoxWorkspaceMirror:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.mirror_entries = []

    def add_entry(self, entry: MirrorEntry):
        self.mirror_entries.append(entry)

    def sync(self) -> SyncResult:
        # Mock sync implementation
        return SyncResult(
            success=True,
            entries_synced=len(self.mirror_entries),
            errors=[],
            timestamp="2023-01-01T00:00:00"
        )

def create_mirror_entry(source: str, target: str) -> MirrorEntry:
    return MirrorEntry(
        source_path=source,
        target_path=target,
        file_hash="mock_hash",
        last_synced="2023-01-01T00:00:00",
        sync_status="synced"
    )