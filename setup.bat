@echo off
REM visual-prompt — Antigravity / Gemini CLI installer (Windows)
setlocal enabledelayedexpansion

set REPO=%~dp0
if "%REPO:~-1%"=="\" set REPO=%REPO:~0,-1%
set SKILL_NAME=visual-prompt

echo ================================
echo  visual-prompt setup
echo  repo: %REPO%
echo ================================

REM 1. Python check
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i

REM 2. Create dirs
if not exist "%USERPROFILE%\.gemini\extensions" mkdir "%USERPROFILE%\.gemini\extensions"
if not exist "%USERPROFILE%\.gemini\commands" mkdir "%USERPROFILE%\.gemini\commands"
if not exist "%USERPROFILE%\.gemini\antigravity-cli\plugins" mkdir "%USERPROFILE%\.gemini\antigravity-cli\plugins"

REM 3. Try symlinks (requires admin OR Developer Mode on Win10/11)
mklink /D "%USERPROFILE%\.gemini\extensions\%SKILL_NAME%" "%REPO%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Symlink failed (no admin / Developer Mode). Falling back to copy.
    echo        IMPORTANT: After any update to this folder, re-run setup.bat to re-sync.
    xcopy "%REPO%" "%USERPROFILE%\.gemini\extensions\%SKILL_NAME%\" /E /I /Y >nul
    copy /Y "%REPO%\commands\%SKILL_NAME%.toml" "%USERPROFILE%\.gemini\commands\%SKILL_NAME%.toml" >nul
    xcopy "%REPO%" "%USERPROFILE%\.gemini\antigravity-cli\plugins\%SKILL_NAME%\" /E /I /Y >nul
) else (
    mklink "%USERPROFILE%\.gemini\commands\%SKILL_NAME%.toml" "%REPO%\commands\%SKILL_NAME%.toml" >nul
    mklink /D "%USERPROFILE%\.gemini\antigravity-cli\plugins\%SKILL_NAME%" "%REPO%" >nul
    echo [OK] Symlinks created.
)

REM 4. Inner skill mirror
if not exist "%REPO%\skills\%SKILL_NAME%" mkdir "%REPO%\skills\%SKILL_NAME%"

REM 5. Plugin manifest
if not exist "%REPO%\plugin.json" (
    echo {"name": "visual-prompt"} > "%REPO%\plugin.json"
)

echo.
echo [OK] Setup completed.
echo.
echo Test: open Antigravity, type /visual-prompt and confirm autocomplete works.
echo Usage: /visual-prompt ^<input.txt^> [--series NAME] [--genre NAME] [--images N] [--videos M] [--force-redo]
pause
