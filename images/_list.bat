@echo off
:: ============================================================
:: list_files.bat
:: Lists every file in a directory to a plain text file
:: for easy cut and paste.
:: ============================================================

set TARGET_DIR=%~1

:: If no argument passed, use the current directory
if "%TARGET_DIR%"=="" set TARGET_DIR=%CD%

set OUTPUT_FILE=%~dp0file_list.txt

echo Listing files in: %TARGET_DIR%
echo.

:: Write the list to a text file (one file path per line)
dir "%TARGET_DIR%" /b /s /a:-d > "%OUTPUT_FILE%"

echo Done! File list saved to:
echo %OUTPUT_FILE%
echo.
echo --- PREVIEW (first 20 lines) ---
more /e +0 "%OUTPUT_FILE%" | findstr /n "." | findstr "^[1-9]:\|^1[0-9]:\|^20:"
echo.
pause