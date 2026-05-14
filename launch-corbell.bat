@echo off
setlocal

set "ROOT=%~dp0"
set "PORT=7433"
cd /d "%ROOT%" || exit /b 1

echo Starting Corbell UI on http://127.0.0.1:%PORT%/
echo Press Ctrl+C to stop.
echo.

if exist "%ROOT%.venv\Scripts\corbell.exe" (
    "%ROOT%.venv\Scripts\corbell.exe" ui serve --port %PORT%
) else if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" -m corbell.cli.main ui serve --port %PORT%
) else (
    python -m corbell.cli.main ui serve --port %PORT%
)

set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
    echo.
    echo Corbell exited with code %EXITCODE%.
)
exit /b %EXITCODE%
