#!/usr/bin/env python3
"""MCP server providing Visual Studio MSBuild project build tools."""

import re
import sys
import os
from pathlib import Path, PureWindowsPath

from mcp.server.fastmcp import FastMCP

from build import build_project as _build_project

mcp = FastMCP("vs-build")


def wsl_to_windows_path(path_str: str) -> str:
    """Convert a WSL2-style path to a Windows-style path.

    Passes through non-WSL2 paths unchanged.

    Examples:
        /mnt/c/Users/foo  -> C:\\Users\\foo
        /mnt/d/bar/baz    -> D:\\bar\\baz
        C:\\Users\\foo     -> C:\\Users\\foo  (unchanged)
        src/main.c        -> src/main.c      (unchanged)
    """
    m = re.match(r"^/mnt/([a-zA-Z])(/.*)?$", path_str)
    if m:
        drive = m.group(1).upper()
        rest = m.group(2) or ""
        return drive + ":" + rest.replace("/", "\\")
    return path_str


# --- Parse repo directory from CLI ---------------------------------------------------
if len(sys.argv) < 2:
    print("Usage: python server.py <repo_directory>", file=sys.stderr)
    sys.exit(1)

_raw_repo = wsl_to_windows_path(sys.argv[1])
REPO_DIR = PureWindowsPath(_raw_repo)

# Validate using a platform-native Path so os.path.isdir works correctly
if not os.path.isdir(str(Path(_raw_repo))):
    print(f"Error: repository directory does not exist: {REPO_DIR}", file=sys.stderr)
    sys.exit(1)


@mcp.tool()
def build_project(
    project_file: str,
    platform: str = "x64",
) -> dict:
    """Build a .vcxproj project using MSBuild (Debug configuration).

    Args:
        project_file: Path to the .vcxproj file. Relative paths are resolved
            against the repository root. WSL2 paths are converted automatically.
        platform: Target platform — "x64" (default) or "Win32".

    Returns:
        A dict with success, output, and exit_code.
    """
    win_path = PureWindowsPath(wsl_to_windows_path(project_file))

    if not win_path.is_absolute():
        win_path = REPO_DIR / win_path

    return _build_project(str(win_path), platform, str(REPO_DIR))


if __name__ == "__main__":
    # Remove the repo directory argument so FastMCP only sees its own args
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    mcp.run()
