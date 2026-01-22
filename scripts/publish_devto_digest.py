#!/usr/bin/env python3
"""Publish Ralph digest to Dev.to."""

import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed, skipping Dev.to publish")
    sys.exit(0)


def main():
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("No Dev.to API key")
        return

    digest_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not digest_file or not digest_file.exists():
        print(f"Digest file not found: {digest_file}")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    content = digest_file.read_text()
    parts = content.split("---", 2)
    body = parts[-1].strip() if len(parts) > 2 else content

    article = {
        "article": {
            "title": f"Ralph Weekly Digest: AI Trading System Update ({today})",
            "published": True,
            "body_markdown": body,
            "tags": ["ai", "trading", "automation", "python"],
            "series": "AI Trading Journey",
        }
    }

    try:
        resp = requests.post(
            "https://dev.to/api/articles",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=article,
            timeout=30,
        )
        if resp.status_code in [200, 201]:
            print(f"Published to Dev.to: {resp.json().get('url')}")
        else:
            print(f"Dev.to publish failed: {resp.status_code}")
    except Exception as e:
        print(f"Dev.to error: {e}")


if __name__ == "__main__":
    main()
