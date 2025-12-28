@echo off
REM OBS Portable Launcher - Handles updates for renamed OBS executables
REM
REM Usage: Rename this file to match your custom OBS executable name.
REM        Example: If you renamed obs64.exe to "stream.exe", rename this to "stream.bat"
REM
REM How it works:
REM   1. Gets custom exe name from this batch file's name (stream.bat -> stream.exe)
REM   2. If obs64.exe exists (OBS auto-updated), renames it to your custom name
REM   3. Starts your custom OBS executable in portable mode (-p flag)
REM
REM Place this file in your portable OBS root folder (next to bin/, config/, etc.)

setlocal

REM Get custom exe name from this batch file's name
set "CUSTOM_EXE=%~n0"

cd /d "%~dp0bin\64bit"

REM Skip update logic if using default obs64 name
if /i "%CUSTOM_EXE%"=="obs64" goto :start
if /i "%CUSTOM_EXE%"=="obs_launcher_template" (
    echo ERROR: Please rename this file to match your custom OBS executable name.
    echo Example: If your OBS is named "stream.exe", rename this to "stream.bat"
    pause
    exit /b 1
)

REM Check if obs64.exe exists (new update downloaded)
if exist "obs64.exe" (
    echo OBS update detected, updating %CUSTOM_EXE%.exe...
    if exist "%CUSTOM_EXE%.exe" del /f "%CUSTOM_EXE%.exe"
    move "obs64.exe" "%CUSTOM_EXE%.exe"
    echo Update complete.
)

:start
REM Start OBS in portable mode
start "" "%CUSTOM_EXE%.exe" -p
