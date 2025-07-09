@echo off
:: Cleanup old ytfast_modules directory
:: This script removes the old modules folder after migration to ytplay

echo.
echo Cleanup Script - Remove old ytfast_modules
echo ==========================================
echo.

set TARGET_DIR=yt-player-main\ytfast_modules

if exist "%TARGET_DIR%" (
    echo Found old modules directory: %TARGET_DIR%
    echo.
    set /p CONFIRM="Do you want to delete it? (Y/N): "
    if /i "!CONFIRM!"=="Y" (
        echo.
        echo Deleting %TARGET_DIR%...
        rmdir /s /q "%TARGET_DIR%"
        echo [OK] Directory removed
    ) else (
        echo Operation cancelled.
    )
) else (
    echo Directory %TARGET_DIR% not found - already cleaned up!
)

echo.
echo Cleanup complete.
pause
