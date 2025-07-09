@echo off
setlocal enabledelayedexpansion

:: YouTube Player Instance Creator with Safety Features
:: Version: 2.0.1

echo ==========================================
echo YouTube Player Instance Creator v2.0.1
echo ==========================================
echo.

:: Check if an instance name was provided
if "%~1"=="" (
    echo ERROR: No instance name provided!
    echo.
    echo Usage: %~nx0 ^<instance_name^>
    echo Example: %~nx0 worship
    echo.
    echo This will create a new instance named "worship"
    pause
    exit /b 1
)

:: Get the instance name and validate it
set "INSTANCE_NAME=%~1"

:: Remove quotes if present
set "INSTANCE_NAME=%INSTANCE_NAME:"=%"

:: Basic validation - only allow alphanumeric and basic characters
echo %INSTANCE_NAME%| findstr /R "^[a-zA-Z0-9_-]*$" >nul
if errorlevel 1 (
    echo ERROR: Invalid instance name!
    echo Instance names can only contain letters, numbers, underscore and hyphen.
    pause
    exit /b 1
)

:: Check for template directory
set "TEMPLATE_DIR=yt-player-main"
if not exist "%TEMPLATE_DIR%" (
    echo ERROR: Template directory not found!
    echo Please ensure %TEMPLATE_DIR% exists in the current directory.
    pause
    exit /b 1
)

:: Determine where to create instances
echo.
echo Where would you like to create the instance?
echo 1. In this repository (yt-player-%INSTANCE_NAME%)
echo 2. In parent directory (..\yt-player-%INSTANCE_NAME%)
echo 3. In custom location
echo.
set /p "LOCATION_CHOICE=Enter choice (1-3): "

if "%LOCATION_CHOICE%"=="1" (
    set "TARGET_DIR=yt-player-%INSTANCE_NAME%"
) else if "%LOCATION_CHOICE%"=="2" (
    set "TARGET_DIR=..\yt-player-%INSTANCE_NAME%"
) else if "%LOCATION_CHOICE%"=="3" (
    set /p "CUSTOM_PATH=Enter full path for instances directory: "
    set "TARGET_DIR=!CUSTOM_PATH!\yt-player-%INSTANCE_NAME%"
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

:: Check if target already exists
if exist "%TARGET_DIR%" (
    echo ERROR: Instance directory already exists: %TARGET_DIR%
    echo Please choose a different name or delete the existing directory.
    pause
    exit /b 1
)

:: Create the instance
echo.
echo Creating instance: %INSTANCE_NAME%
echo Target directory: %TARGET_DIR%
echo ========================================

:: Copy template to new instance
echo Copying template files...
xcopy /E /I /Q "%TEMPLATE_DIR%" "%TARGET_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to copy template files!
    pause
    exit /b 1
)

:: Rename the main script
echo Renaming main script...
move "%TARGET_DIR%\ytplay.py" "%TARGET_DIR%\%INSTANCE_NAME%.py" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to rename main script!
    pause
    exit /b 1
)

:: Rename the modules directory
echo Renaming modules directory...
move "%TARGET_DIR%\ytplay_modules" "%TARGET_DIR%\%INSTANCE_NAME%_modules" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to rename modules directory!
    pause
    exit /b 1
)

:: Clean up cache directory
echo Cleaning cache directory...
if exist "%TARGET_DIR%\cache" (
    del /Q "%TARGET_DIR%\cache\*.*" >nul 2>&1
)

:: Create a configuration note
echo Creating configuration note...
(
echo Instance: %INSTANCE_NAME%
echo Created: %DATE% %TIME%
echo Script: %INSTANCE_NAME%.py
echo Modules: %INSTANCE_NAME%_modules
echo.
echo This instance is completely independent and can be moved anywhere.
) > "%TARGET_DIR%\INSTANCE_INFO.txt"

:: Success message
echo.
echo ========================================
echo ✓ Instance created successfully!
echo ========================================
echo.
echo Instance Details:
echo - Location: %TARGET_DIR%
echo - Script name: %INSTANCE_NAME%.py
echo - Module directory: %INSTANCE_NAME%_modules
echo - Scene name: %INSTANCE_NAME%
echo.
echo OBS Setup Instructions:
echo 1. In OBS, go to Tools → Scripts → +
echo 2. Add: %TARGET_DIR%\%INSTANCE_NAME%.py
echo 3. Create a scene named: %INSTANCE_NAME%
echo 4. Add Media Source named: %INSTANCE_NAME%_video
echo 5. Add Text Source named: %INSTANCE_NAME%_title (optional)
echo.
echo IMPORTANT: This instance is portable!
echo You can move the entire %TARGET_DIR% folder
echo anywhere on your system and it will still work.
echo.
pause