---
name: msvc-build
description: >-
  Builds Visual Studio C++ projects (.vcxproj) using MSBuild on Windows or WSL2.
  Runs a Debug build and returns compiler output including errors and warnings.
  Use after editing C/C++ source files to verify the project still compiles,
  or when the user asks to build, compile, or check a .vcxproj project.
compatibility: Requires Windows or WSL2 with Visual Studio 2022 and Python 3.10+.
metadata:
  author: natekot
  version: "1.0"
allowed-tools: Bash(python:*) Bash(cmd.exe:*)
---

# msvc-build

Build Visual Studio C++ projects (.vcxproj) using MSBuild from the command line.

## When to use

- After modifying C/C++ source files, to verify the project still compiles.
- When the user asks to build, compile, or check a `.vcxproj` project.
- To get compiler errors and warnings for diagnosis.

## How to build

Run the build script with the path to a `.vcxproj` file:

```bash
python <skill-path>/scripts/build.py <path-to-project.vcxproj>
```

### Arguments

| Argument          | Required | Description                                       |
|-------------------|----------|---------------------------------------------------|
| `project_file`    | Yes      | Path to the `.vcxproj` file.                      |
| `--repo-dir DIR`  | No       | Repository root directory (default: cwd).         |
| `-32`             | No       | Build for Win32 platform instead of x64 (default).|

### Examples

**x64 Debug build (default):**
```bash
python <skill-path>/scripts/build.py MyApp.vcxproj
```

**Win32 build:**
```bash
python <skill-path>/scripts/build.py MyApp.vcxproj -32
```

**Explicit repo directory:**
```bash
python <skill-path>/scripts/build.py MyApp.vcxproj --repo-dir /mnt/c/repos/myproject
```

**Using the Windows batch wrapper (from repo root):**
```batch
vs-build.bat MyApp.vcxproj
```

## Finding .vcxproj files

The `.vcxproj` file is almost always in the same directory as the source file
you are editing. To search the repo:

```bash
find . -name "*.vcxproj" -type f
```

## Interpreting build output

- **Exit code 0**: Build succeeded. Output contains the MSBuild summary.
- **Exit code non-zero**: Build failed. Look for `error C` (compiler) or
  `error LNK` (linker) lines in the output.
- **Warnings**: Lines containing `warning C` indicate non-fatal issues.

Common error patterns:

| Pattern         | Meaning                        |
|-----------------|--------------------------------|
| `error C2065`   | Undeclared identifier          |
| `error C2146`   | Syntax error (missing token)   |
| `error C1083`   | Cannot open include file       |
| `error LNK2019` | Unresolved external symbol     |
| `error LNK1120` | Unresolved externals (summary) |

## Environment configuration

| Variable        | Default                                                                       | Description                  |
|-----------------|-------------------------------------------------------------------------------|------------------------------|
| `VSDEVCMD_PATH` | `C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat` | Path to VS Developer Cmd. |

Set `VSDEVCMD_PATH` if Visual Studio is installed in a non-default location.

## Technical details

See [references/REFERENCE.md](references/REFERENCE.md) for MSBuild flags,
path conversion logic, security constraints, and internal implementation details.
