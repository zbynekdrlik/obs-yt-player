@echo off
:: YouTube Player Instance Creator
:: Creates a new YouTube player instance from the template

setlocal enabledelayedexpansion

:: Check if instance name was provided
if "%~1"=="" (
    echo.
    echo YouTube Player Instance Creator
    echo ===============================
    echo.
    echo Usage: create_new_ytplayer.bat ^<instance_name^>
    echo.
    echo Example: create_new_ytplayer.bat worship
    echo.
    echo This will create:
    echo   - Folder: yt-player-worship
    echo   - Script: worship.py  
    echo   - Module: worship_modules
    echo   - Scene:  worship
    echo.
    exit /b 1
)

set INSTANCE_NAME=%~1
set SOURCE_DIR=yt-player-main
set TARGET_DIR=yt-player-%INSTANCE_NAME%
set SOURCE_SCRIPT=ytplay.py
set TARGET_SCRIPT=%INSTANCE_NAME%.py
set SOURCE_MODULES=ytplay_modules
set TARGET_MODULES=%INSTANCE_NAME%_modules

:: Validate instance name (alphanumeric and underscore only)
echo %INSTANCE_NAME%| findstr /r "^[a-zA-Z0-9_]*$" >nul
if errorlevel 1 (
    echo.
    echo ERROR: Instance name can only contain letters, numbers, and underscores
    echo.
    exit /b 1
)

:: Check if source template exists
if not exist "%SOURCE_DIR%" (
    echo.
    echo ERROR: Template directory '%SOURCE_DIR%' not found!
    echo Please ensure yt-player-main exists with the template files.
    echo.
    exit /b 1
)

:: Check if target already exists
if exist "%TARGET_DIR%" (
    echo.
    echo WARNING: Directory '%TARGET_DIR%' already exists!
    echo.
    set /p CONFIRM="Do you want to overwrite it? (Y/N): "
    if /i not "!CONFIRM!"=="Y" (
        echo Operation cancelled.
        exit /b 0
    )
    echo.
    echo Removing existing directory...
    rmdir /s /q "%TARGET_DIR%"
)

echo.
echo Creating new YouTube player instance: %INSTANCE_NAME%
echo =====================================================
echo Source: %SOURCE_DIR%
echo Target: %TARGET_DIR%
echo.

:: Copy the entire folder
echo Copying folder structure...
xcopy /e /i /q "%SOURCE_DIR%" "%TARGET_DIR%" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy folder
    exit /b 1
)
echo [OK] Folder copied

:: Rename main script
if exist "%TARGET_DIR%\%SOURCE_SCRIPT%" (
    echo Renaming main script...
    ren "%TARGET_DIR%\%SOURCE_SCRIPT%" "%TARGET_SCRIPT%"
    echo [OK] %SOURCE_SCRIPT% -^> %TARGET_SCRIPT%
) else (
    echo WARNING: Main script %SOURCE_SCRIPT% not found
)

:: Rename modules folder
if exist "%TARGET_DIR%\%SOURCE_MODULES%" (
    echo Renaming modules folder...
    ren "%TARGET_DIR%\%SOURCE_MODULES%" "%TARGET_MODULES%"
    echo [OK] %SOURCE_MODULES%\ -^> %TARGET_MODULES%\
) else (
    echo WARNING: Modules folder %SOURCE_MODULES% not found
)

:: Clean cache directory
if exist "%TARGET_DIR%\cache" (
    echo.
    echo Cleaning cache directory...
    del /q "%TARGET_DIR%\cache\*.*" 2>nul
    echo [OK] Cache cleaned
)

:: Create success message
echo.
echo ========================================
echo SUCCESS! New instance '%INSTANCE_NAME%' created
echo ========================================
echo.
echo Configuration Summary:
echo   Directory:    %TARGET_DIR%\
echo   Main Script:  %TARGET_SCRIPT%
echo   Modules:      %TARGET_MODULES%\
echo   OBS Scene:    %INSTANCE_NAME%
echo.
echo Next Steps:
echo   1. In OBS Studio: Tools -^> Scripts -^> Add Script (+)
echo   2. Navigate to: %CD%\%TARGET_DIR%\%TARGET_SCRIPT%
echo   3. Create a scene named: %INSTANCE_NAME%
echo   4. Add sources to the scene:
echo      - Media Source named "video"
echo      - Text Source named "title" (optional)
echo   5. Configure the playlist URL in script settings
echo.
pause
