#!/usr/bin/env python3
"""MCP server providing Visual Studio MSBuild project build tools."""

import sys
import os
from pathlib import Path, PureWindowsPath

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "msvc-build", "scripts"))
from build import build_project as _build_project, to_windows_path

mcp = FastMCP(
    "dts",
    instructions=(
        "This server builds Visual Studio C++ projects in the DTS "
        "codebase using MSBuild. The repository root was provided at "
        "server startup and all relative .vcxproj paths are resolved "
        "against it.\n\n"
        "Typical workflow:\n"
        "1. Edit C/C++ source files.\n"
        "2. Call build_project with the relevant .vcxproj file to verify "
        "the change compiles. The .vcxproj file is almost always in the "
        "same directory as the source file you edited.\n"
        "3. If the build fails, examine the 'output' field for compiler "
        "errors and fix them.\n\n"
        "The build always uses Debug configuration. "
        "Use platform='Win32' only when targeting 32-bit."
    ),
)


# --- Parse repo directory from CLI ---------------------------------------------------
if len(sys.argv) < 2:
    print("Usage: python server.py <repo_directory>", file=sys.stderr)
    sys.exit(1)

_raw_repo = sys.argv[1]

# Platform-native path for OS operations (cwd, isdir, temp files)
REPO_DIR_NATIVE = str(Path(_raw_repo))

# Windows-format path for resolving project file names passed to MSBuild
REPO_DIR_WIN = PureWindowsPath(to_windows_path(_raw_repo))

if not os.path.isdir(REPO_DIR_NATIVE):
    print(f"Error: repository directory does not exist: {_raw_repo}", file=sys.stderr)
    sys.exit(1)


@mcp.tool()
def build_project(
    project_file: str,
    platform: str = "x64",
) -> dict:
    """Build a Visual Studio C++ project (.vcxproj) using MSBuild.

    Use this tool after modifying C/C++ source files to verify the project
    still compiles. It runs a Debug build and returns the full MSBuild
    output including any compiler errors or warnings.

    Args:
        project_file: Path to the .vcxproj file (e.g. "MyApp.vcxproj").
            Relative paths are resolved against the repository root.
            WSL2-style paths like /mnt/c/... are converted automatically.
            Hint: the .vcxproj is almost always in the same directory as
            the source file you are editing.
        platform: Target platform — "x64" (default) or "Win32".
            Use "Win32" only when the project specifically targets 32-bit.

    Returns:
        A dict with:
        - success: Whether the build succeeded (bool).
        - output: Full MSBuild stdout/stderr — contains compiler errors,
          warnings, and the build summary.
        - exit_code: MSBuild process exit code (0 = success).
    """
    win_path = PureWindowsPath(to_windows_path(project_file))

    if not win_path.is_absolute():
        win_path = REPO_DIR_WIN / win_path

    return _build_project(str(win_path), platform, REPO_DIR_NATIVE)


if __name__ == "__main__":
    # Remove the repo directory argument so FastMCP only sees its own args
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    mcp.run()
