@echo off
setlocal enabledelayedexpansion

:: Script to update all yt-player instances from main - Simplified
:: Version: 2.2.0 - No prompts, auto-search current + parent directories

echo ==========================================
echo YouTube Player Instance Updater v2.2.0
echo ==========================================
echo.

:: Parse command line options
set "SKIP_PARENT=0"
set "CUSTOM_PATH="
set "ASK_CONFIRM=0"

:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="/noparent" (
    set "SKIP_PARENT=1"
) else if /i "%~1"=="/confirm" (
    set "ASK_CONFIRM=1"
) else if /i "%~1"=="/path" (
    echo ERROR: /path requires a directory. Use /path:C:\your\directory
    pause
    exit /b 1
) else (
    set "param=%~1"
    set "prefix=!param:~0,6!"
    if /i "!prefix!"=="/path:" (
        set "CUSTOM_PATH=!param:~6!"
    )
)
shift
goto parse_args
:end_parse

:: Step 1: Update main repository with git
echo [1/4] Updating main repository from GitHub...
echo ----------------------------------------
git pull origin main
if errorlevel 1 (
    echo WARNING: Git pull failed. Continuing with local version...
    echo.
)

:: Step 2: Check if template exists
set "TEMPLATE_DIR=yt-player-main"
if not exist "%TEMPLATE_DIR%" (
    echo ERROR: Template directory "%TEMPLATE_DIR%" not found!
    echo Please ensure you have the template instance set up.
    pause
    exit /b 1
)

:: Step 3: Find instances in multiple locations
echo [2/4] Searching for instances...
echo ----------------------------------------
set "instance_count=0"

:: Search in current directory
echo Searching in current directory...
for /d %%D in (yt-player-*) do (
    if /i not "%%D"=="%TEMPLATE_DIR%" (
        set /a instance_count+=1
        set "instances[!instance_count!]=%%D"
        echo Found: %%D
    )
)

:: Search in parent directory (unless disabled)
if "%SKIP_PARENT%"=="0" (
    echo Searching in parent directory...
    for /d %%D in (..\yt-player-*) do (
        set /a instance_count+=1
        set "instances[!instance_count!]=%%D"
        echo Found: %%D
    )
)

:: Search custom path if provided
if not "%CUSTOM_PATH%"=="" (
    echo Searching in %CUSTOM_PATH%...
    for /d %%D in ("%CUSTOM_PATH%\yt-player-*") do (
        set /a instance_count+=1
        set "instances[!instance_count!]=%%D"
        echo Found: %%D
    )
)

if %instance_count%==0 (
    echo.
    echo No instances found to update.
    echo.
    echo Tip: Use /path:C:\custom\path to search additional locations
    echo Examples: update_all_instances.bat /path:D:\OBS\Instances
    pause
    exit /b 0
)

echo.
echo Found %instance_count% instance(s) to update

:: Step 4: Confirm update (only if /confirm was used)
if "%ASK_CONFIRM%"=="1" (
    echo.
    echo [3/4] Confirmation required
    echo ----------------------------------------
    echo This will update all instances from the template.
    echo Cache and configuration will be preserved.
    echo.
    set /p "CONFIRM=Continue with update? (y/n): "
    if /i not "!CONFIRM!"=="y" (
        echo Update cancelled.
        pause
        exit /b 0
    )
) else (
    echo.
    echo [3/4] Starting automatic update...
    echo ----------------------------------------
)

:: Step 5: Update each instance
echo.
echo [4/4] Updating instances from template...
echo ========================================

set "updated_count=0"
set "error_count=0"

:: Process each instance using a simpler approach
for /L %%i in (1,1,%instance_count%) do call :process_instance %%i

:: Summary
echo.
echo ========================================
echo Update Summary
echo ========================================
echo ✓ Updated:  %updated_count% instances
if %error_count% gtr 0 (
    echo ✗ Errors:   %error_count%
)
echo ========================================

:: Quick notes
echo.
echo Update complete! Remember to:
echo - Restart OBS or reload scripts
echo - Test each instance after update
echo.
pause
exit /b 0

:: Function to process a single instance
:process_instance
set "idx=%1"
set "instance_path=!instances[%idx%]!"
echo.
echo Updating: !instance_path!
echo ------------------------

:: Find the main script name
set "script_name="
for %%F in ("!instance_path!\*.py") do (
    set "filename=%%~nF"
    :: Skip files starting with __ or test_
    set "first_two=!filename:~0,2!"
    set "first_five=!filename:~0,5!"
    if not "!first_two!"=="__" if not "!first_five!"=="test_" (
        set "script_name=!filename!"
    )
)

if not defined script_name (
    echo ERROR: No Python script found in !instance_path!
    set /a error_count+=1
    exit /b 1
)

echo Instance script: !script_name!.py

:: Update modules directory
if exist "!instance_path!\!script_name!_modules" (
    echo Updating modules...
    
    :: Copy module files
    for %%M in ("%TEMPLATE_DIR%\ytplay_modules\*.py") do (
        echo   - Copying %%~nxM
        copy /Y "%%M" "!instance_path!\!script_name!_modules\" >nul 2>&1
        if errorlevel 1 (
            echo     WARNING: Failed to copy %%~nxM
            set /a error_count+=1
        )
    )
    
    :: Copy __init__.py
    if exist "%TEMPLATE_DIR%\ytplay_modules\__init__.py" (
        copy /Y "%TEMPLATE_DIR%\ytplay_modules\__init__.py" "!instance_path!\!script_name!_modules\" >nul 2>&1
    )
    
    echo ✓ Modules updated
) else (
    echo ERROR: Module directory !script_name!_modules not found!
    set /a error_count+=1
)

:: Update main script
echo Updating main script...
copy /Y "%TEMPLATE_DIR%\ytplay.py" "!instance_path!\!script_name!.py" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to update main script!
    set /a error_count+=1
) else (
    echo ✓ Main script updated
)

:: Update README
if exist "%TEMPLATE_DIR%\README.md" (
    copy /Y "%TEMPLATE_DIR%\README.md" "!instance_path!\" >nul 2>&1
)

:: Update instance info
(
    echo Instance: !script_name!
    echo Updated: %DATE% %TIME%
    echo Script: !script_name!.py
    echo Modules: !script_name!_modules
    echo.
    echo Last updated from template version in: %TEMPLATE_DIR%
) > "!instance_path!\INSTANCE_INFO.txt"

echo ✓ Instance updated successfully
set /a updated_count+=1
exit /b 0