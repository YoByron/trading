import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

def build_manifest_entries(workspace_path: str) -> List[Dict[str, Any]]:
    """Build manifest entries for files in the workspace."""
    manifest_entries = []
    
    try:
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, workspace_path)
                
                # Get file stats
                stat_info = os.stat(file_path)
                
                entry = {
                    "path": relative_path,
                    "size": stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "type": "file"
                }
                
                manifest_entries.append(entry)
    
    except Exception as e:
        # Add error entry
        manifest_entries.append({
            "path": "ERROR",
            "error": str(e),
            "type": "error"
        })
    
    return manifest_entries

def sync_workspace_to_box(workspace_path: str, box_folder_id: str) -> Dict[str, Any]:
    """Sync local workspace to Box folder."""
    
    result = {
        "status": "success",
        "synced_at": datetime.now().isoformat(),
        "workspace_path": workspace_path,
        "box_folder_id": box_folder_id,
        "files_synced": 0,
        "errors": []
    }
    
    try:
        # Build manifest of local files
        manifest = build_manifest_entries(workspace_path)
        
        # Simulate sync process
        for entry in manifest:
            if entry.get("type") == "file":
                result["files_synced"] += 1
            elif entry.get("type") == "error":
                result["errors"].append(entry.get("error", "Unknown error"))
        
        if result["errors"]:
            result["status"] = "partial_success"
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def create_box_mirror_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create configuration for Box workspace mirroring."""
    
    config = {
        "created_at": datetime.now().isoformat(),
        "workspace_path": config_data.get("workspace_path", "./workspace"),
        "box_folder_id": config_data.get("box_folder_id"),
        "sync_interval": config_data.get("sync_interval", 3600),  # 1 hour default
        "exclude_patterns": config_data.get("exclude_patterns", ["*.tmp", "*.log"]),
        "auto_sync": config_data.get("auto_sync", True)
    }
    
    return config