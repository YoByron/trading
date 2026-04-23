#!/usr/bin/env python3
"""Agent handoff gate for trading system safety checks."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateResult:
    """Result from a gate check."""
    success: bool
    message: str
    details: List[str]


def parse_changed_paths(changed_files_str: str) -> Set[str]:
    """Parse changed file paths from a string."""
    if not changed_files_str or changed_files_str.strip() == "":
        return set()
    
    paths = set()
    for line in changed_files_str.strip().split('\n'):
        if line.strip():
            paths.add(line.strip())
    return paths


def check_policy_drift() -> GateResult:
    """Check for policy drift in trading documents."""
    try:
        monitor = PolicyDriftMonitor(
            policy_docs=DEFAULT_POLICY_DOC_PATHS,
            output_file=REPO_ROOT / "data" / "policy_drift_analysis.json"
        )
        
        drift_results = monitor.analyze_drift()
        
        if drift_results.has_significant_drift:
            return GateResult(
                success=False,
                message="Significant policy drift detected",
                details=[
                    f"Overall drift score: {drift_results.overall_drift_score:.3f}",
                    f"Files with high drift: {len(drift_results.high_drift_files)}",
                    f"Threshold: {drift_results.drift_threshold}"
                ]
            )
        
        return GateResult(
            success=True,
            message="No significant policy drift detected",
            details=[
                f"Overall drift score: {drift_results.overall_drift_score:.3f}",
                f"All files within acceptable drift threshold"
            ]
        )
        
    except Exception as e:
        return GateResult(
            success=False,
            message=f"Policy drift check failed with error: {str(e)}",
            details=[]
        )


def main():
    """Main entry point for the agent handoff gate."""
    print("🔍 Running agent handoff gate checks...")

    # Run policy drift check
    policy_result = check_policy_drift()

    if not policy_result.success:
        print("❌ Policy drift check failed:")
        print(f"   {policy_result.message}")
        for detail in policy_result.details:
            print(f"   - {detail}")
        sys.exit(1)
    else:
        print("✅ Policy drift check passed")

    print("🎉 All gate checks passed!")


if __name__ == "__main__":
    main()