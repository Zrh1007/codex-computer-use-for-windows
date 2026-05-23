@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "SERVER=%SCRIPT_DIR%windows_computer_use_mcp.py"
set "PLUGIN_ROOT=%SCRIPT_DIR%.."
set "VENV_PYTHON=%PLUGIN_ROOT%\.venv\Scripts\python.exe"
set "VENV_PYTHON_POSIX=%PLUGIN_ROOT%\.venv\bin\python.exe"

if not exist "%VENV_PYTHON%" if not exist "%VENV_PYTHON_POSIX%" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%ensure_venv.ps1" 1>nul
)

if exist "%VENV_PYTHON%" (
  "%VENV_PYTHON%" "%SERVER%"
  exit /b %ERRORLEVEL%
)

if exist "%VENV_PYTHON_POSIX%" (
  "%VENV_PYTHON_POSIX%" "%SERVER%"
  exit /b %ERRORLEVEL%
)

if exist "C:\Python313\python.exe" (
  "C:\Python313\python.exe" "%SERVER%"
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%SERVER%"
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%SERVER%"
  exit /b %ERRORLEVEL%
)

echo Unable to find Python 3 for Windows Computer Use MCP. 1>&2
exit /b 9009
