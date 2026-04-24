from typing import Dict, List, Optional, Any
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

class MirrorEntry:
    def __init__(self, source_path: str, target_path: str, file_type: str = "file"):
        self.source_path = source_path
        self.target_path = target_path
        self.file_type = file_type
        self.created_at = datetime.now()
        self.last_synced = None
        self.sync_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mirror entry to dictionary."""
        return {
            'source_path': self.source_path,
            'target_path': self.target_path,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat(),
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'sync_count': self.sync_count
        }

class BoxWorkspaceMirror:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.logger = logging.getLogger(__name__)
        self.mirror_entries = {}
    
    def add_mirror_entry(self, source: str, target: str, file_type: str = "file") -> bool:
        """Add a new mirror entry."""
        try:
            entry_id = f"{source}::{target}"
            self.mirror_entries[entry_id] = MirrorEntry(source, target, file_type)
            self.logger.info(f"Added mirror entry: {source} -> {target}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add mirror entry: {e}")
            return False
    
    def sync_entry(self, entry_id: str) -> bool:
        """Sync a specific mirror entry."""
        if entry_id not in self.mirror_entries:
            self.logger.error(f"Mirror entry not found: {entry_id}")
            return False
        
        entry = self.mirror_entries[entry_id]
        try:
            source_path = Path(entry.source_path)
            target_path = Path(entry.target_path)
            
            if source_path.exists():
                if source_path.is_file():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                elif source_path.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                
                entry.last_synced = datetime.now()
                entry.sync_count += 1
                self.logger.info(f"Synced: {entry.source_path} -> {entry.target_path}")
                return True
            else:
                self.logger.warning(f"Source path does not exist: {entry.source_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to sync entry: {e}")
            return False
    
    def sync_all(self) -> Dict[str, bool]:
        """Sync all mirror entries."""
        results = {}
        for entry_id in self.mirror_entries:
            results[entry_id] = self.sync_entry(entry_id)
        return results
    
    def get_mirror_status(self) -> Dict[str, Any]:
        """Get status of all mirror entries."""
        return {
            entry_id: entry.to_dict()
            for entry_id, entry in self.mirror_entries.items()
        }