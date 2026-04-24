@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "SERVER=%SCRIPT_DIR%windows_computer_use_mcp.py"

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
