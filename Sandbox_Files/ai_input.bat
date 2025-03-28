@echo off
setlocal enabledelayedexpansion

:: Check if running in PowerShell and relaunch in CMD if needed
for /f "tokens=2 delims=:" %%a in ('tasklist /fi "imagename eq powershell.exe" /v ^| find "%~nx0"') do (
    start cmd /c "%~f0"
    exit /b
)

color 0A
cls

set "PROMPT_FILE=%~dp0..\Master_Prompt.txt"

:MAIN_MENU
cls
echo ===================================================
echo        MASTER PROMPT SELECTION UTILITY
echo ===================================================
echo.
echo Select a section to input to AI:
echo.
echo  1. Complete Master Prompt (entire file)
echo  2. File Organization Principles
echo  3. Language-Specific Directory Structures
echo  4. Environment Configuration Principles
echo  5. Asset Management Principles
echo  6. Database Organization Principles
echo  7. Version Control Principles
echo  8. Documentation Principles
echo  9. Maintenance Guidelines
echo 10. README.md Template
echo.
echo  0. Exit
echo.
echo ===================================================
echo.

set /p CHOICE="Enter your choice (0-10): "

if "%CHOICE%"=="0" goto :EXIT
if "%CHOICE%"=="1" set "SECTION=COMPLETE" & goto :SELECT_METHOD
if "%CHOICE%"=="2" set "SECTION=FILE_ORG" & goto :SELECT_METHOD
if "%CHOICE%"=="3" set "SECTION=LANG_DIR" & goto :SELECT_METHOD
if "%CHOICE%"=="4" set "SECTION=ENV_CONFIG" & goto :SELECT_METHOD
if "%CHOICE%"=="5" set "SECTION=ASSET_MGMT" & goto :SELECT_METHOD
if "%CHOICE%"=="6" set "SECTION=DB_ORG" & goto :SELECT_METHOD
if "%CHOICE%"=="7" set "SECTION=VERSION_CTRL" & goto :SELECT_METHOD
if "%CHOICE%"=="8" set "SECTION=DOC_PRINCIPLES" & goto :SELECT_METHOD
if "%CHOICE%"=="9" set "SECTION=MAINTENANCE" & goto :SELECT_METHOD
if "%CHOICE%"=="10" set "SECTION=README_TEMPLATE" & goto :SELECT_METHOD

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto :MAIN_MENU

:SELECT_METHOD
cls
echo ===================================================
echo        INPUT METHOD SELECTION
echo ===================================================
echo.
echo How would you like to input the selected section?
echo.
echo 1. Copy to clipboard (for manual paste)
echo 2. Simulate typing directly (requires focus on AI input field)
echo.
echo 0. Back to main menu
echo.
echo ===================================================
echo.

set /p METHOD="Enter your choice (0-2): "

if "%METHOD%"=="0" goto :MAIN_MENU
if "%METHOD%"=="1" goto :COPY_TO_CLIPBOARD
if "%METHOD%"=="2" goto :SIMULATE_TYPING

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto :SELECT_METHOD

:COPY_TO_CLIPBOARD
cls
echo Extracting selected section from Master_Prompt.txt...

call :EXTRACT_SECTION

echo !EXTRACTED_TEXT! | clip

echo.
echo ===================================================
echo The selected section has been copied to clipboard.
echo You can now paste it into the AI interface.
echo ===================================================
echo.
echo Press any key to return to the main menu...
pause >nul
goto :MAIN_MENU

:SIMULATE_TYPING
cls
echo Extracting selected section from Master_Prompt.txt...

call :EXTRACT_SECTION

echo.
echo ===================================================
echo IMPORTANT: Please click in the AI input field now!
echo ===================================================
echo.
echo The text will be typed automatically in 5 seconds...
echo Press Ctrl+C to cancel if needed.
echo.

timeout /t 5

echo Simulating typing...

powershell -Command "$text = Get-Content -Path '%TEMP%\ai_prompt_section.txt' -Raw; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait($text)"

echo.
echo ===================================================
echo Done! The text should now be entered in the AI input field.
echo ===================================================
echo.
echo Press any key to return to the main menu...
pause >nul
goto :MAIN_MENU

:EXTRACT_SECTION
set "TEMP_FILE=%TEMP%\ai_prompt_section.txt"

if "%SECTION%"=="COMPLETE" (
    type "%PROMPT_FILE%" > "%TEMP_FILE%"
    set "EXTRACTED_TEXT=Complete Master Prompt file"
    goto :EOF
)

powershell -Command "$content = Get-Content -Path '%PROMPT_FILE%' -Raw; $section = ''; switch ('%SECTION%') {
    'FILE_ORG' { 
        $pattern = '(?s)## File Organization Principles.*?(?=## Language-Specific Directory Structures)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'LANG_DIR' { 
        $pattern = '(?s)## Language-Specific Directory Structures.*?(?=## Environment Configuration Principles)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'ENV_CONFIG' { 
        $pattern = '(?s)## Environment Configuration Principles.*?(?=## Asset Management Principles)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'ASSET_MGMT' { 
        $pattern = '(?s)## Asset Management Principles.*?(?=## Database Organization Principles)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'DB_ORG' { 
        $pattern = '(?s)## Database Organization Principles.*?(?=## Version Control Principles)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'VERSION_CTRL' { 
        $pattern = '(?s)## Version Control Principles.*?(?=## Documentation Principles)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'DOC_PRINCIPLES' { 
        $pattern = '(?s)## Documentation Principles.*?(?=## Maintenance Guidelines)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'MAINTENANCE' { 
        $pattern = '(?s)## Maintenance Guidelines.*?(?=## README.md Template)'
        $section = [regex]::Match($content, $pattern).Value
    }
    'README_TEMPLATE' { 
        $pattern = '(?s)## README.md Template.*$'
        $section = [regex]::Match($content, $pattern).Value
    }
}
Set-Content -Path '%TEMP_FILE%' -Value $section"

set "EXTRACTED_TEXT=Selected section"
goto :EOF

:EXIT
cls
echo Thank you for using the Master Prompt Selection Utility.
echo Goodbye!
echo.
timeout /t 2 >nul
exit /b 0