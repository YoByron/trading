#!/usr/bin/env python3
"""Update prd.json iteration count."""

import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    prd_file = Path(".claude/prd.json")
    if not prd_file.exists():
        print("prd.json not found")
        return

    try:
        data = json.loads(prd_file.read_text())
        current = data.get("metadata", {}).get("total_iterations", 0)
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"]["total_iterations"] = current + 1
        data["metadata"]["notes"] = "Weekly digest - Ralph Mode active"
        data["metadata"]["last_digest"] = datetime.now(timezone.utc).isoformat()
        prd_file.write_text(json.dumps(data, indent=2))
        print(f"Updated iterations: {current} -> {current + 1}")
    except Exception as e:
        print(f"Could not update prd.json: {e}")


if __name__ == "__main__":
    main()
