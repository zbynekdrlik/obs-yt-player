@echo off
setlocal enabledelayedexpansion

:: YouTube Player Instance Creator - Simplified Version
:: Version: 2.2.4 - Final fix for parameter handling

echo ==========================================
echo YouTube Player Instance Creator v2.2.4
echo ==========================================
echo.

:: Check if an instance name was provided
if "%~1"=="" (
    echo ERROR: No instance name provided!
    echo.
    echo Usage: %~nx0 ^<instance_name^> [options]
    echo Example: %~nx0 worship
    echo.
    echo Options:
    echo   /repo         Create in repository directory
    echo   /path:^<dir^>   Create in custom directory
    echo.
    echo Default: Creates in parent directory
    pause
    exit /b 1
)

:: Get the instance name
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

:: Parse command line options - default to parent directory
set "TARGET_DIR=..\yt-player-%INSTANCE_NAME%"

:: Check for /repo option
if /i "%~2"=="/repo" (
    set "TARGET_DIR=yt-player-%INSTANCE_NAME%"
    echo Note: Creating in repository (not recommended for safety)
    goto :skip_further_params
)

:: Check for /path option (without directory)
if /i "%~2"=="/path" (
    echo ERROR: /path requires a directory. Use /path:C:\your\directory
    pause
    exit /b 1
)

:: Check for /path:directory option
if "%~2" NEQ "" (
    set "param2=%~2"
    set "prefix=!param2:~0,6!"
    if /i "!prefix!"=="/path:" (
        set "custom_path=!param2:~6!"
        set "TARGET_DIR=!custom_path!\yt-player-%INSTANCE_NAME%"
        echo Note: Creating in custom location: !custom_path!
    ) else (
        echo WARNING: Unknown option: %~2
        echo Continuing with default parent directory...
    )
)

:skip_further_params

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

:: Count copied files for feedback
set file_count=0
for /r "%TARGET_DIR%" %%f in (*) do set /a file_count+=1
echo   %file_count% files copied

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
echo [SUCCESS] Instance created successfully!
echo ========================================
echo.
echo Instance Details:
echo - Name: %INSTANCE_NAME%
echo - Location: %TARGET_DIR%
echo - Script: %INSTANCE_NAME%.py
echo - Modules: %INSTANCE_NAME%_modules
echo.
echo Quick OBS Setup:
echo 1. Tools -^> Scripts -^> + -^> Add %INSTANCE_NAME%.py
echo 2. Create scene: %INSTANCE_NAME%
echo 3. Add Media Source: %INSTANCE_NAME%_video
echo 4. Add Text Source: %INSTANCE_NAME%_title (optional)
echo.
pause