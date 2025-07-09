@echo off
setlocal enabledelayedexpansion

:: Script to update all yt-player instances from main
:: Version: 2.0.1 - Fixed nested if statement error

echo ==========================================
echo YouTube Player Instance Updater v2.0.1
echo ==========================================
echo.

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

:: Search in parent directory
echo Searching in parent directory...
for /d %%D in (..\yt-player-*) do (
    set /a instance_count+=1
    set "instances[!instance_count!]=%%D"
    echo Found: %%D
)

:: Ask if user wants to search additional locations
echo.
set /p "SEARCH_MORE=Search additional locations? (y/n): "
if /i "%SEARCH_MORE%"=="y" (
    set /p "CUSTOM_PATH=Enter path to search: "
    echo Searching in !CUSTOM_PATH!...
    for /d %%D in ("!CUSTOM_PATH!\yt-player-*") do (
        set /a instance_count+=1
        set "instances[!instance_count!]=%%D"
        echo Found: %%D
    )
)

if %instance_count%==0 (
    echo.
    echo No instances found to update.
    echo.
    echo Tip: Instances should be named yt-player-*
    echo Examples: yt-player-worship, yt-player-kids
    pause
    exit /b 0
)

echo.
echo Found %instance_count% instance(s) to update
echo.

:: Step 4: Confirm update
echo [3/4] Ready to update instances
echo ----------------------------------------
echo This will update all instances from the template.
echo Cache and configuration will be preserved.
echo.
set /p "CONFIRM=Continue with update? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Update cancelled.
    pause
    exit /b 0
)

:: Step 5: Update each instance
echo.
echo [4/4] Updating instances from template...
echo ========================================

set "updated_count=0"
set "error_count=0"

for /L %%i in (1,1,%instance_count%) do (
    set "instance_path=!instances[%%i]!"
    echo.
    echo Updating: !instance_path!
    echo ------------------------
    
    :: Find the main script name by looking for .py files
    set "script_name="
    for %%F in ("!instance_path!\*.py") do (
        set "filename=%%~nF"
        :: Skip files starting with __ or test_
        set "first_chars=!filename:~0,2!"
        set "test_prefix=!filename:~0,5!"
        if not "!first_chars!"=="__" if not "!test_prefix!"=="test_" (
            set "script_name=!filename!"
        )
    )
    
    if defined script_name (
        echo Instance script: !script_name!.py
        
        :: Update modules directory
        if exist "!instance_path!\!script_name!_modules" (
            echo Updating modules...
            
            :: Copy all module files from template
            for %%M in ("%TEMPLATE_DIR%\ytplay_modules\*.py") do (
                echo   - Copying %%~nxM
                copy /Y "%%M" "!instance_path!\!script_name!_modules\" >nul 2>&1
                if errorlevel 1 (
                    echo     WARNING: Failed to copy %%~nxM
                    set /a error_count+=1
                )
            )
            
            :: Copy __init__.py if it exists
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
        
        :: Update README if it exists in template
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
    ) else (
        echo ERROR: No Python script found in !instance_path!
        set /a error_count+=1
    )
)

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

:: Important notes
echo.
echo IMPORTANT NOTES:
echo ----------------
echo 1. Each instance's cache and configuration are preserved
echo 2. You may need to restart OBS or reload scripts
echo 3. Test each instance after update to ensure it works
echo 4. Instances can be located anywhere on your system
echo.
echo TIP: To prevent Git from deleting instances, keep them
echo      outside the repository or in a separate folder.

echo.
pause