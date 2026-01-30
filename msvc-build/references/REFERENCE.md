# MSBuild Build Reference

Detailed reference for the `msvc-build` skill internals.

## MSBuild Configuration

The build script invokes MSBuild with these fixed properties:

| Property                  | Value               | Notes                                      |
|---------------------------|---------------------|--------------------------------------------|
| `Configuration`           | `Debug`             | Always Debug; Release is not supported.    |
| `Platform`                | `x64` or `Win32`    | Controlled by the `-32` flag.              |
| `BuildProjectReferences` | `false`             | Skips building referenced projects.        |
| `SolutionDir`             | Repo root path      | Forward slashes, trailing `/`.             |

## Path Conversion (WSL2)

When running under WSL2, paths are automatically converted to Windows format:

| Input                    | Output              |
|--------------------------|---------------------|
| `/mnt/c/Users/foo/...`  | `C:\Users\foo\...`  |
| `/c/Users/foo/...`      | `C:\Users\foo\...`  |
| `C:\Users\foo\...`      | `C:\Users\foo\...`  |

The conversion uses the regex `^(?:/mnt)?/([a-zA-Z])(/.*)?$` to detect
POSIX-style drive paths and translates them to `<DRIVE>:\...` format.

## Security Constraints

The `.vcxproj` path is interpolated into a temporary batch file, so it must
pass a strict character allowlist to prevent command injection:

```
[A-Za-z0-9_.\-\\/: ]+
```

Only alphanumerics, spaces, and the characters `_ . - \ / :` are permitted.
Paths containing other characters (e.g., `&`, `|`, `"`, `$`) are rejected
with an error.

## Build Timeout

Builds are subject to a **120-second timeout**. If MSBuild does not complete
within this window, the process is killed and exit code `-1` is returned with
the message "Build timed out after 120 seconds."

## How It Works Internally

1. A temporary `.bat` file is created in the repo directory (so it is on a
   Windows-accessible filesystem, required for WSL2 `/mnt/` paths).
2. The batch file calls `VsDevCmd.bat` to set up the VS build environment.
3. For x64 builds, a `for /f` loop resolves the Python 3.11 executable path
   and sets the `PYTHON3` environment variable.
4. MSBuild is invoked with the project file and build properties.
5. stdout and stderr are captured and returned as the build output.
6. The temporary batch file is deleted in a `finally` block.

## Common MSVC Error Codes

### Compiler Errors (error C)

| Code    | Description                              | Typical Cause                           |
|---------|------------------------------------------|-----------------------------------------|
| C1083   | Cannot open include file                 | Missing header or wrong include path    |
| C2065   | Undeclared identifier                    | Typo, missing `#include`, or namespace  |
| C2146   | Syntax error: missing token              | Missing semicolon, brace, or paren      |
| C2059   | Syntax error: unexpected token           | Invalid syntax at the indicated token   |
| C2664   | Cannot convert argument                  | Type mismatch in function call          |
| C2440   | Cannot convert from type to type         | Invalid implicit or explicit cast       |
| C4996   | Deprecated function (warning by default) | Use of `strcpy`, `sprintf`, etc.        |

### Linker Errors (error LNK)

| Code     | Description                     | Typical Cause                            |
|----------|---------------------------------|------------------------------------------|
| LNK2019  | Unresolved external symbol      | Missing library, undefined function      |
| LNK1120  | N unresolved externals          | Summary of LNK2019 errors                |
| LNK1104  | Cannot open file                | Missing `.lib` or output directory       |
| LNK2005  | Symbol already defined          | Duplicate definition across object files |

## Environment Variables

| Variable        | Default                                                                                  | Description                                |
|-----------------|------------------------------------------------------------------------------------------|--------------------------------------------|
| `VSDEVCMD_PATH` | `C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat` | Full path to the VS Developer Command Prompt batch file. Override this if VS is installed in a non-default location (e.g., Community or Enterprise edition). |
