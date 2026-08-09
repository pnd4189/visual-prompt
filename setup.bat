@echo off
REM visual-prompt — Antigravity, Codex CLI, and Claude Code installer (Windows)
setlocal enabledelayedexpansion

set REPO=%~dp0
if "%REPO:~-1%"=="\" set REPO=%REPO:~0,-1%
set SKILL_NAME=visual-prompt
if "%CODEX_HOME%"=="" (
    set CODEX_DIR=%USERPROFILE%\.codex
) else (
    set CODEX_DIR=%CODEX_HOME%
)
if "%CLAUDE_HOME%"=="" (
    set CLAUDE_DIR=%USERPROFILE%\.claude
) else (
    set CLAUDE_DIR=%CLAUDE_HOME%
)
set AGENT_SKILLS_DIR=%USERPROFILE%\.agents\skills

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
if not exist "%USERPROFILE%\.gemini\config" mkdir "%USERPROFILE%\.gemini\config"
if not exist "%AGENT_SKILLS_DIR%" mkdir "%AGENT_SKILLS_DIR%"
if not exist "%CODEX_DIR%\prompts" mkdir "%CODEX_DIR%\prompts"
if not exist "%CLAUDE_DIR%\skills" mkdir "%CLAUDE_DIR%\skills"

REM 3. Try Agy symlinks (requires admin OR Developer Mode on Win10/11)
fsutil reparsepoint query "%USERPROFILE%\.gemini\extensions\%SKILL_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Existing Agy symlink kept.
    goto agy_ready
)
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
:agy_ready

python "%REPO%\scripts\install_agy_guard.py" --repo-root "%REPO%" --target "%USERPROFILE%\.gemini\config\hooks.json"
if errorlevel 1 (
    echo ERROR: Failed to install the Agy runtime guard.
    exit /b 1
)

REM 4. Codex native skill + custom prompt shim
fsutil reparsepoint query "%AGENT_SKILLS_DIR%\%SKILL_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Existing Codex skill symlink kept.
    goto codex_skill_ready
)
mklink /D "%AGENT_SKILLS_DIR%\%SKILL_NAME%" "%REPO%\adapters\codex\%SKILL_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Codex skill symlink failed; copying a standalone bundle.
    if not exist "%AGENT_SKILLS_DIR%\%SKILL_NAME%" mkdir "%AGENT_SKILLS_DIR%\%SKILL_NAME%"
    xcopy "%REPO%\adapters\codex\%SKILL_NAME%" "%AGENT_SKILLS_DIR%\%SKILL_NAME%\" /E /I /Y >nul
    xcopy "%REPO%\commands" "%AGENT_SKILLS_DIR%\%SKILL_NAME%\commands\" /E /I /Y >nul
    xcopy "%REPO%\prompts" "%AGENT_SKILLS_DIR%\%SKILL_NAME%\prompts\" /E /I /Y >nul
    xcopy "%REPO%\references" "%AGENT_SKILLS_DIR%\%SKILL_NAME%\references\" /E /I /Y >nul
    xcopy "%REPO%\scripts" "%AGENT_SKILLS_DIR%\%SKILL_NAME%\scripts\" /E /I /Y >nul
)
:codex_skill_ready
fsutil reparsepoint query "%CODEX_DIR%\prompts\%SKILL_NAME%.md" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Existing Codex prompt symlink kept.
    goto codex_prompt_ready
)
mklink "%CODEX_DIR%\prompts\%SKILL_NAME%.md" "%REPO%\adapters\codex\%SKILL_NAME%.md" >nul 2>&1
if errorlevel 1 copy /Y "%REPO%\adapters\codex\%SKILL_NAME%.md" "%CODEX_DIR%\prompts\%SKILL_NAME%.md" >nul
:codex_prompt_ready

REM 5. Claude Code skill
fsutil reparsepoint query "%CLAUDE_DIR%\skills\%SKILL_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Existing Claude skill symlink kept.
    goto claude_skill_ready
)
mklink /D "%CLAUDE_DIR%\skills\%SKILL_NAME%" "%REPO%\adapters\claude-code\%SKILL_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Claude skill symlink failed; copying a standalone bundle.
    if not exist "%CLAUDE_DIR%\skills\%SKILL_NAME%" mkdir "%CLAUDE_DIR%\skills\%SKILL_NAME%"
    xcopy "%REPO%\adapters\claude-code\%SKILL_NAME%" "%CLAUDE_DIR%\skills\%SKILL_NAME%\" /E /I /Y >nul
    xcopy "%REPO%\commands" "%CLAUDE_DIR%\skills\%SKILL_NAME%\commands\" /E /I /Y >nul
    xcopy "%REPO%\prompts" "%CLAUDE_DIR%\skills\%SKILL_NAME%\prompts\" /E /I /Y >nul
    xcopy "%REPO%\references" "%CLAUDE_DIR%\skills\%SKILL_NAME%\references\" /E /I /Y >nul
    xcopy "%REPO%\scripts" "%CLAUDE_DIR%\skills\%SKILL_NAME%\scripts\" /E /I /Y >nul
)
:claude_skill_ready

REM 6. Plugin manifest
if not exist "%REPO%\plugin.json" (
    echo {"name": "visual-prompt"} > "%REPO%\plugin.json"
)

echo.
echo [OK] Setup completed.
echo.
echo Test Agy: /visual-prompt ^<input.txt^>
echo Test Codex native: $visual-prompt ^<input.txt^>
echo Test Codex slash shim: /prompts:visual-prompt ^<input.txt^>
echo Test Claude Code: /visual-prompt ^<input.txt^>
echo Default output: QA + image prompts. Add --video/--videos N and/or --music [N] explicitly.
pause
