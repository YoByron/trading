"""Trading policy drift detection and monitoring."""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_POLICY_DOC_PATHS = [
    "docs/trading/policy.md",
    "docs/trading/risk_management.md",
    "docs/trading/compliance.md",
]

CANONICAL_POLICY_VALUES = {
    "max_position_size": 0.02,
    "max_daily_loss": 0.01,
    "max_sector_concentration": 0.15,
    "required_stop_loss": True,
    "minimum_liquidity_threshold": 1000000,
}

def canonical_policy_values() -> Dict:
    """Return canonical policy configuration values."""
    return CANONICAL_POLICY_VALUES.copy()

@dataclass
class PolicySnapshot:
    """Snapshot of policy state at a point in time."""
    
    timestamp: str
    file_hashes: Dict[str, str]
    extracted_values: Dict[str, any]
    metadata: Dict[str, any]

class PolicyDriftMonitor:
    """Monitor trading policy documents for drift and changes."""
    
    def __init__(self, policy_paths: Optional[List[str]] = None):
        self.policy_paths = policy_paths or DEFAULT_POLICY_DOC_PATHS
        self.baseline_snapshot: Optional[PolicySnapshot] = None
        
    def take_snapshot(self) -> PolicySnapshot:
        """Take a snapshot of current policy state."""
        file_hashes = {}
        extracted_values = {}
        
        for policy_path in self.policy_paths:
            path = Path(policy_path)
            if path.exists():
                content = path.read_text()
                file_hashes[policy_path] = hashlib.md5(content.encode()).hexdigest()
                
                # Extract policy values from content
                extracted = self._extract_policy_values(content)
                extracted_values.update(extracted)
        
        return PolicySnapshot(
            timestamp=str(Path().resolve()),
            file_hashes=file_hashes,
            extracted_values=extracted_values,
            metadata={"policy_paths": self.policy_paths}
        )
    
    def _extract_policy_values(self, content: str) -> Dict[str, any]:
        """Extract policy values from document content."""
        # Simple extraction - look for key patterns
        values = {}
        lines = content.lower().split('\n')
        
        for line in lines:
            if 'max_position_size' in line and ':' in line:
                try:
                    value = float(line.split(':')[1].strip().rstrip('%'))
                    values['max_position_size'] = value / 100 if '%' in line else value
                except (ValueError, IndexError):
                    pass
                    
            elif 'max_daily_loss' in line and ':' in line:
                try:
                    value = float(line.split(':')[1].strip().rstrip('%'))
                    values['max_daily_loss'] = value / 100 if '%' in line else value
                except (ValueError, IndexError):
                    pass
                    
        return values
    
    def detect_drift(self, current_snapshot: Optional[PolicySnapshot] = None) -> Dict[str, any]:
        """Detect policy drift from baseline."""
        if not self.baseline_snapshot:
            logger.warning("No baseline snapshot available for drift detection")
            return {"drift_detected": False, "changes": []}
            
        if current_snapshot is None:
            current_snapshot = self.take_snapshot()
            
        changes = []
        
        # Check file hash changes
        for path, baseline_hash in self.baseline_snapshot.file_hashes.items():
            current_hash = current_snapshot.file_hashes.get(path)
            if current_hash != baseline_hash:
                changes.append({
                    "type": "file_change",
                    "path": path,
                    "baseline_hash": baseline_hash,
                    "current_hash": current_hash
                })
        
        # Check extracted value changes
        for key, baseline_value in self.baseline_snapshot.extracted_values.items():
            current_value = current_snapshot.extracted_values.get(key)
            if current_value != baseline_value:
                changes.append({
                    "type": "value_change",
                    "key": key,
                    "baseline_value": baseline_value,
                    "current_value": current_value
                })
        
        return {
            "drift_detected": len(changes) > 0,
            "changes": changes,
            "baseline_timestamp": self.baseline_snapshot.timestamp,
            "current_timestamp": current_snapshot.timestamp
        }
    
    def set_baseline(self, snapshot: Optional[PolicySnapshot] = None) -> None:
        """Set baseline snapshot for drift detection."""
        if snapshot is None:
            snapshot = self.take_snapshot()
        self.baseline_snapshot = snapshot
        logger.info(f"Set policy baseline with {len(snapshot.file_hashes)} files")