@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD="
where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
    where py >nul 2>nul && set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    echo Python was not found. Install Python or add it to PATH.
    pause
    exit /b 1
)

echo Starting DOM Control server...
set "DOM_URL=http://127.0.0.1:8000/dom_pro2.html"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $r=Invoke-WebRequest -Uri '%DOM_URL%' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1"

if errorlevel 1 (
    start "DOM Control Server" cmd /k "cd /d ""%~dp0"" && %PYTHON_CMD% ""%~dp0dom_server.py"""
)

echo Waiting for %DOM_URL% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok=$false; for ($i=0; $i -lt 60; $i++) { try { $r=Invoke-WebRequest -Uri '%DOM_URL%' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if (-not $ok) { exit 1 }"

if errorlevel 1 (
    echo.
    echo The server did not start on port 8000.
    echo Look at the "DOM Control Server" window for the Python error.
    echo If that window says port 8000 is already in use, close the old DOM Control Server window and run this again.
    echo.
    pause
    exit /b 1
)

start "" "%DOM_URL%"

endlocal
