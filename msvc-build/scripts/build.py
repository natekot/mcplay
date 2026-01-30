"""MSBuild build logic for Visual Studio C++ projects.

Standalone script and importable module. Builds .vcxproj files using MSBuild
via the VS Developer Command Prompt. Works on both native Windows and WSL2
(via cmd.exe interop).

Usage:
    python build.py <project.vcxproj> [--repo-dir DIR] [-32]
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import PureWindowsPath

VSDEVCMD_PATH = os.environ.get(
    "VSDEVCMD_PATH",
    r"C:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\Tools\VsDevCmd.bat",
)


def to_windows_path(path_str):
    """Ensure a path is in Windows format.

    Converts WSL2 /mnt/<drive>/... and /<drive>/... paths to <DRIVE>:\\...
    Passes through paths that are already in Windows format.
    """
    m = re.match(r"^(?:/mnt)?/([a-zA-Z])(/.*)?$", path_str)
    if m:
        drive = m.group(1).upper()
        rest = m.group(2) or ""
        return drive + ":" + rest.replace("/", "\\")
    return path_str


def build_project(
    project_file: str,
    platform: str = "x64",
    repo_dir: str = "",
) -> dict:
    """Build a .vcxproj project using MSBuild via the VS Developer Command Prompt.

    Args:
        project_file: Path to the .vcxproj file (Windows-style).
        platform: "x64" or "Win32".
        repo_dir: Repository root directory in platform-native format
            (POSIX on WSL2, Windows-style on Windows). Used as cwd and
            converted to Windows format for SolutionDir.

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
    # batch file, so only allow safe characters.
    if not re.fullmatch(r"[A-Za-z0-9_.\-\\/: ]+", project_file):
        return {
            "success": False,
            "output": (
                "Project file path contains disallowed characters. "
                "Only alphanumerics, spaces, and _ . - \\ / : are permitted."
            ),
            "exit_code": -1,
        }

    # SolutionDir must be Windows-format with forward slashes + trailing /
    win_repo = to_windows_path(repo_dir)
    solution_dir = win_repo.replace("\\", "/")
    if not solution_dir.endswith("/"):
        solution_dir += "/"

    # --- Write a temporary .bat file ------------------------------------------
    # This avoids all cmd.exe / WSL-interop quoting issues: the complex
    # command syntax lives inside the file, and subprocess only needs to
    # pass a simple file path.
    # Batch files use %%V for loop variables (vs %V in cmd /c inline).
    lines = ["@echo off"]

    if platform == "x64":
        lines.append(
            'for /f "usebackq delims=" %%P in '
            '(`py -3.11 -c "import sys; print(sys.executable)"`) '
            'do @set "PYTHON3=%%P"'
        )

    lines.append(f'call "{VSDEVCMD_PATH}"')
    lines.append(
        f'msbuild "{project_file}"'
        f" /p:Configuration=Debug"
        f" /p:Platform={platform}"
        f" /p:BuildProjectReferences=false"
        f' /p:SolutionDir="{solution_dir}"'
    )

    bat_content = "\r\n".join(lines) + "\r\n"

    # Create the temp .bat in repo_dir so it sits on a Windows-accessible
    # filesystem (required for WSL2 when repo_dir is under /mnt/).
    fd, bat_path = tempfile.mkstemp(suffix=".bat", dir=repo_dir)
    try:
        with os.fdopen(fd, "w", newline="") as f:
            f.write(bat_content)

        # cmd.exe needs the Windows-format path to the batch file
        bat_win_path = to_windows_path(bat_path)

        result = subprocess.run(
            ["cmd.exe", "/c", bat_win_path],
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
            "output": "cmd.exe not found. This tool requires Windows or WSL2.",
            "exit_code": -1,
        }
    finally:
        try:
            os.unlink(bat_path)
        except OSError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a Visual Studio C++ project (.vcxproj) using MSBuild.",
    )
    parser.add_argument(
        "project_file",
        help="Path to the .vcxproj file to build.",
    )
    parser.add_argument(
        "--repo-dir",
        default=os.getcwd(),
        help="Repository root directory (default: current working directory).",
    )
    parser.add_argument(
        "-32",
        dest="win32",
        action="store_true",
        help="Build for Win32 platform instead of x64.",
    )
    args = parser.parse_args()

    plat = "Win32" if args.win32 else "x64"
    result = build_project(args.project_file, platform=plat, repo_dir=args.repo_dir)
    print(result["output"])
    sys.exit(result["exit_code"])
