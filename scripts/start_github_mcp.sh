#!/bin/bash
set -euo pipefail

# Helper script to launch the GitHub MCP server container locally.
# Requires Docker Desktop running and GITHUB_PERSONAL_ACCESS_TOKEN exported.

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but not found in PATH." >&2
  exit 1
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  echo "Set GITHUB_PERSONAL_ACCESS_TOKEN before running this script." >&2
  exit 1
fi

docker run \
  --rm \
  -i \
  --name github-mcp-server \
  -e GITHUB_PERSONAL_ACCESS_TOKEN \
  ghcr.io/github/github-mcp-server:latest
