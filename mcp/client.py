"""
Lightweight MCP client abstraction.

This module provides a thin wrapper around the `claude` CLI (or any compatible
MCP client binary) so that agents can execute MCP tools from Python code.  The
goal is to keep tool invocation logic out of the prompt loop and inside the code
execution harness, following Anthropic's guidance on context-efficient MCP
usage.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Optional

DEFAULT_CLI_BIN = os.environ.get("MCP_CLI_BIN", "claude")
DEFAULT_PROFILE = os.environ.get("MCP_PROFILE")

_DEFAULT_CLIENT_LOCK = Lock()
_DEFAULT_CLIENT: Optional["MCPClient"] = None


class MCPError(RuntimeError):
    """Raised when an MCP tool invocation fails."""


@dataclass(slots=True)
class MCPClient:
    """
    Simple shell-based MCP client.

    Args:
        cli_bin: Path to the CLI binary (defaults to env `MCP_CLI_BIN` or
                 `claude`).
        profile: Optional CLI profile to pass (via `--profile` flag).
        env: Extra environment variables to include when invoking the CLI.
    """

    cli_bin: str = DEFAULT_CLI_BIN
    profile: Optional[str] = DEFAULT_PROFILE
    env: Optional[Dict[str, str]] = None

    def call_tool(
        self,
        server: str,
        tool: str,
        payload: Dict[str, Any],
        *,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool via the CLI.

        Args:
            server: MCP server identifier.
            tool: Tool name on the server.
            payload: JSON-serialisable arguments for the tool.
            timeout: Maximum number of seconds to wait for the command.

        Returns:
            Parsed JSON response from the tool.

        Raises:
            MCPError: If the command exits non-zero or returns invalid JSON.
        """
        cmd = [self.cli_bin, "mcp", "run", server, tool]
        if self.profile:
            cmd.extend(["--profile", self.profile])

        try:
            process = subprocess.run(
                cmd,
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                env=self._build_env(),
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise MCPError(
                f"MCP CLI binary '{self.cli_bin}' not found. "
                "Set MCP_CLI_BIN to the correct executable."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise MCPError(
                f"MCP tool '{server}:{tool}' timed out after {timeout} seconds."
            ) from exc

        if process.returncode != 0:
            raise MCPError(
                "\n".join(
                    [
                        f"MCP tool '{server}:{tool}' failed "
                        f"(exit {process.returncode}).",
                        "STDOUT:",
                        process.stdout or "<empty>",
                        "STDERR:",
                        process.stderr or "<empty>",
                    ]
                )
            )

        stdout = process.stdout.strip()
        if not stdout:
            return {}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise MCPError(
                f"MCP tool '{server}:{tool}' returned non-JSON output: {stdout}"
            ) from exc

    def _build_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        if self.env:
            env.update(self.env)
        return env


def default_client() -> MCPClient:
    """
    Return a singleton MCPClient, lazily configured from environment variables.
    """
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        with _DEFAULT_CLIENT_LOCK:
            if _DEFAULT_CLIENT is None:
                _DEFAULT_CLIENT = MCPClient()
    return _DEFAULT_CLIENT

