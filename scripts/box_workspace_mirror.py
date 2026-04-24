from typing import Dict, List, Any

class MirrorEntry:
    def __init__(self, source_path: str, target_path: str):
        self.source_path = source_path
        self.target_path = target_path
        self.status = "pending"
        self.last_sync = None

    def sync(self) -> bool:
        self.status = "synced"
        return True

class BoxWorkspaceMirror:
    def __init__(self):
        self.entries: List[MirrorEntry] = []

    def add_entry(self, entry: MirrorEntry):
        self.entries.append(entry)

    def sync_all(self) -> bool:
        success = True
        for entry in self.entries:
            if not entry.sync():
                success = False
        return success

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self.entries),
            "synced": len([e for e in self.entries if e.status == "synced"])
        }