@echo off
setlocal enabledelayedexpansion

:: Script to update all yt-player instances from main
:: Version: 1.0.0

echo ========================================
echo YouTube Player Instance Updater v1.0.0
echo ========================================
echo.

:: Step 1: Update main repository with git
echo [1/3] Updating main repository from GitHub...
echo ----------------------------------------
git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to update from GitHub!
    echo Please check your internet connection and git configuration.
    pause
    exit /b 1
)
echo ✓ Main repository updated successfully
echo.

:: Step 2: Check if template exists
set "TEMPLATE_DIR=yt-player-main"
if not exist "%TEMPLATE_DIR%" (
    echo ERROR: Template directory "%TEMPLATE_DIR%" not found!
    echo Please ensure you have the template instance set up.
    pause
    exit /b 1
)

:: Step 3: Find all instance directories
echo [2/3] Finding all instance directories...
echo ----------------------------------------
set "instance_count=0"
for /d %%D in (yt-player-*) do (
    set /a instance_count+=1
    set "instances[!instance_count!]=%%D"
    echo Found: %%D
)

if %instance_count%==1 (
    echo.
    echo Only found the template directory. No instances to update.
    pause
    exit /b 0
)

echo.
echo Found %instance_count% directories (including template)
echo.

:: Step 4: Update each instance
echo [3/3] Updating instances from template...
echo ========================================

set "updated_count=0"
set "skipped_count=0"
set "error_count=0"

for /d %%D in (yt-player-*) do (
    :: Skip the template directory itself
    if /i "%%D"=="%TEMPLATE_DIR%" (
        echo.
        echo Skipping template directory: %%D
        set /a skipped_count+=1
    ) else (
        echo.
        echo Updating instance: %%D
        echo ------------------------
        
        :: Find the main script name
        set "script_name="
        for %%F in ("%%D\*.py") do (
            set "filename=%%~nF"
            if not "!filename:~0,2!"=="__" (
                set "script_name=!filename!"
            )
        )
        
        if defined script_name (
            echo Instance script: !script_name!.py
            
            :: Update modules directory
            if exist "%%D\!script_name!_modules" (
                echo Updating modules...
                
                :: Copy all module files from template
                for %%M in ("%TEMPLATE_DIR%\ytplay_modules\*.py") do (
                    echo   - Copying %%~nxM
                    copy /Y "%%M" "%%D\!script_name!_modules\" >nul 2>&1
                    if errorlevel 1 (
                        echo     WARNING: Failed to copy %%~nxM
                        set /a error_count+=1
                    )
                )
                
                :: Copy __init__.py if it exists
                if exist "%TEMPLATE_DIR%\ytplay_modules\__init__.py" (
                    copy /Y "%TEMPLATE_DIR%\ytplay_modules\__init__.py" "%%D\!script_name!_modules\" >nul 2>&1
                )
                
                echo ✓ Modules updated
            ) else (
                echo ERROR: Module directory !script_name!_modules not found!
                set /a error_count+=1
            )
            
            :: Update main script
            echo Updating main script...
            copy /Y "%TEMPLATE_DIR%\ytplay.py" "%%D\!script_name!.py" >nul 2>&1
            if errorlevel 1 (
                echo ERROR: Failed to update main script!
                set /a error_count+=1
            ) else (
                echo ✓ Main script updated
            )
            
            :: Update README if it exists in template
            if exist "%TEMPLATE_DIR%\README.md" (
                copy /Y "%TEMPLATE_DIR%\README.md" "%%D\" >nul 2>&1
            )
            
            echo ✓ Instance %%D updated successfully
            set /a updated_count+=1
        ) else (
            echo ERROR: No Python script found in %%D!
            set /a error_count+=1
        )
    )
)

:: Summary
echo.
echo ========================================
echo Update Summary
echo ========================================
echo ✓ Updated:  %updated_count% instances
echo - Skipped:  %skipped_count% (template)
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
echo 3. Check each instance after update to ensure it works
echo 4. If you have v4.0.x instances, update OBS source names:
echo    - Old: video, title
echo    - New: [instance]_video, [instance]_title

echo.
pause