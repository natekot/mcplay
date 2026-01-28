#!/usr/bin/env python3
"""MCP server providing C code compilation verification tools."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("c-tools")


@mcp.tool()
def check_compilation(
    file_path: str,
    compiler_flags: str = "-Wall -Wextra",
) -> dict:
    """
    Check if a C source file compiles successfully using gcc.

    Args:
        file_path: Path to the C source file to compile.
        compiler_flags: Optional compiler flags (default: "-Wall -Wextra").

    Returns:
        A dict with:
        - success: Whether compilation succeeded.
        - output: Compiler output (stdout and stderr).
        - exit_code: The compiler's exit code.
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "output": f"File not found: {file_path}",
            "exit_code": -1,
        }

    if not path.suffix == ".c":
        return {
            "success": False,
            "output": f"Expected .c file, got: {path.suffix}",
            "exit_code": -1,
        }

    # Build the gcc command
    # -c: compile only (don't link)
    # -o: output to temp file
    def run_compilation(tmp_name: str) -> dict:
        cmd = ["gcc", "-c"]

        if compiler_flags:
            cmd.extend(compiler_flags.split())

        cmd.extend(["-o", tmp_name, str(path)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout + result.stderr

            return {
                "success": result.returncode == 0,
                "output": output.strip() if output.strip() else "Compilation successful.",
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "Compilation timed out after 30 seconds.",
                "exit_code": -1,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "gcc not found. Please ensure gcc is installed and in PATH.",
                "exit_code": -1,
            }

    # Create a temporary file for the output (we don't need the binary)
    # Windows can't delete open files, so we use delete=False and clean up manually
    if IS_WINDOWS:
        tmp = tempfile.NamedTemporaryFile(suffix=".o", delete=False)
        tmp_name = tmp.name
        tmp.close()
        try:
            return run_compilation(tmp_name)
        finally:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
    else:
        with tempfile.NamedTemporaryFile(suffix=".o", delete=True) as tmp:
            return run_compilation(tmp.name)


if __name__ == "__main__":
    mcp.run()
