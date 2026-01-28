"""Shared MSBuild build logic for VS C++ projects.

Used by server.py (MCP tool) and vs-build.bat (CLI wrapper).
"""

import os
import re
import subprocess
import sys
from pathlib import PureWindowsPath

VSDEVCMD_PATH = (
    r"C:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\Tools\VsDevCmd.bat"
)


def build_project(
    project_file: str,
    platform: str = "x64",
    repo_dir: str = "",
) -> dict:
    """Build a .vcxproj project using MSBuild via the VS Developer Command Prompt.

    Args:
        project_file: Path to the .vcxproj file (Windows-style).
        platform: "x64" or "Win32".
        repo_dir: Repository root directory (used as cwd and SolutionDir).

    Returns:
        A dict with success, output, and exit_code.
    """
    # Validate platform
    if platform not in ("x64", "Win32"):
        return {
            "success": False,
            "output": f"Invalid platform: {platform!r}. Must be 'x64' or 'Win32'.",
            "exit_code": -1,
        }

    # Validate project file extension
    win_path = PureWindowsPath(project_file)
    if win_path.suffix.lower() != ".vcxproj":
        return {
            "success": False,
            "output": f"Expected .vcxproj file, got: {win_path.suffix!r}",
            "exit_code": -1,
        }

    # Guard against command injection — the path is interpolated into a
    # cmd /c string, so only allow safe characters.
    if not re.fullmatch(r"[A-Za-z0-9_.\-\\/: ]+", project_file):
        return {
            "success": False,
            "output": (
                "Project file path contains disallowed characters. "
                "Only alphanumerics, spaces, and _ . - \\ / : are permitted."
            ),
            "exit_code": -1,
        }

    # SolutionDir: use forward slashes and ensure trailing slash
    solution_dir = repo_dir.replace("\\", "/")
    if not solution_dir.endswith("/"):
        solution_dir += "/"

    # Build the cmd /c command chain
    parts = []

    # x64 builds need the PYTHON3 env var set
    if platform == "x64":
        parts.append(
            'for /f "usebackq delims=" %P in '
            "(`py -3.11 -c \"import sys; print(sys.executable)\"`)"
            ' do @set "PYTHON3=%P"'
        )

    parts.append(f'call "{VSDEVCMD_PATH}"')
    parts.append(
        f'msbuild "{project_file}"'
        f" /p:Configuration=Debug"
        f" /p:Platform={platform}"
        f" /p:BuildProjectReferences=false"
        f' /p:SolutionDir="{solution_dir}"'
    )

    cmd_script = " && ".join(parts)

    try:
        result = subprocess.run(
            ["cmd", "/c", cmd_script],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=repo_dir,
        )

        output = result.stdout + result.stderr
        return {
            "success": result.returncode == 0,
            "output": output.strip() if output.strip() else "Build successful.",
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Build timed out after 120 seconds.",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "cmd.exe not found. This tool requires Windows.",
            "exit_code": -1,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].endswith(".vcxproj"):
        print("Usage: python build.py <project.vcxproj> [-32]", file=sys.stderr)
        sys.exit(1)

    proj = sys.argv[1]
    plat = "Win32" if "-32" in sys.argv[2:] else "x64"
    cwd = os.getcwd()

    result = build_project(proj, platform=plat, repo_dir=cwd)
    print(result["output"])
    sys.exit(result["exit_code"])
