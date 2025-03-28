@echo off
setlocal enabledelayedexpansion

:: Check if running in PowerShell and relaunch in CMD if needed
for /f "tokens=2 delims=:" %%a in ('tasklist /fi "imagename eq powershell.exe" /v ^| find "%~nx0"') do (
    start cmd /c "%~f0"
    exit /b
)

color 0A
cls

:: ===================================================
:: MASTER PROMPT UTILITY - SELF-CONTAINED VERSION
:: ===================================================
:: This batch file contains both the Master Prompt content
:: and the menu system to select sections for AI input

:: ===================================================
:: MASTER PROMPT CONTENT DEFINITION
:: ===================================================

set "COMPLETE=# Master Prompt for File Structure and Organization

## Overview
This document provides guidelines for organizing application files into a structured folder system. Follow these principles to create a clean, maintainable project structure that separates essential application files from development and test files.

## File Organization Principles

### 1. Analyze the Application Structure
- Identify the main application file(s) (e.g., main.py, Gospel_JukeBox.py)
- Identify essential data directories (e.g., mp3_files, pictures, data/songs)
- Identify configuration files (e.g., requirements.txt)
- Identify non-essential files (test files, backups, development scripts)

### 2. Recommended Folder Structure

```
/                           # Root directory
├── main.py                 # Main application file
├── requirements.txt        # Dependencies
├── data/                   # Application data
│   └── songs/              # Song directories with mp3, txt, and image files
├── mp3_files/              # MP3 files with corresponding lyrics
├── pictures/               # Image files
├── Sandbox_Files/          # Non-essential files
│   ├── .dockerignore       # Docker ignore file
│   ├── .env                # Environment variables
│   ├── Dockerfile          # Docker configuration
│   └── Unused_Test_Files/  # Test and backup files
```

### 3. File Classification Guidelines

#### Essential Files (Keep in Root Directory)
- Main application files (e.g., main.py, Gospel_JukeBox.py)
- Configuration files (e.g., requirements.txt)
- README.md (contains setup instructions and project overview)

#### Essential Data Directories (Keep in Root Directory)
- mp3_files/
- pictures/
- data/

#### Non-Essential Files (Move to Sandbox_Files)
- Docker configuration files (place at Sandbox_Files root)
- Development and test files (place in Unused_Test_Files subfolder)
  - Backup files (*_BU*, *.bak)
  - Test files (app.py, create_folders.bat)
  - Unused code files (*.pyyy)
  - Development scripts

## Language-Specific Directory Structures

### Python Applications
```
/
├── src/                    # Source code
│   ├── __init__.py         # Makes src a package
│   ├── main.py             # Entry point
│   ├── models/             # Data models
│   ├── controllers/        # Business logic
│   ├── views/              # UI components (for web apps)
│   └── utils/              # Helper functions
├── tests/                  # Test files
├── docs/                   # Documentation
├── config/                 # Configuration files
├── requirements.txt        # Production dependencies
└── README.md
```

### JavaScript/TypeScript (React) Applications
```
/
├── src/                    # Source code
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── context/            # React context providers
│   ├── services/           # API services
│   ├── utils/              # Helper functions
│   ├── assets/             # Static assets
│   ├── App.js              # Main App component
│   └── index.js            # Entry point
├── public/                 # Public assets
└── README.md
```

### Java (Spring Boot) Applications
```
/
├── src/
│   ├── main/
│   │   ├── java/com/example/project/
│   │   │   ├── controllers/    # REST controllers
│   │   │   ├── models/         # Data models
│   │   │   ├── repositories/   # Data access
│   │   │   ├── services/       # Business logic
│   │   │   ├── config/         # Configuration
│   │   │   └── Application.java # Entry point
│   │   └── resources/
│   └── test/
├── pom.xml                # Project dependencies
└── README.md
```

## Environment Configuration Principles
- Create separate configuration files for different environments
- Never commit sensitive information to version control
- Use environment variables for configuration that changes between environments
- Document all required environment variables

## Asset Management Principles
- Use a consistent naming convention for all asset files
- Optimize assets during the build process
- Implement caching strategies for static assets
- Separate source assets from compiled/processed assets

## Database Organization Principles
- Use sequential naming for migration files
- Ensure migrations are idempotent
- Include both "up" and "down" migrations for reversibility
- Document database schema changes

## Version Control Principles
- Create a comprehensive .gitignore file
- Use semantic versioning for releases
- Implement a consistent branching strategy
- Write descriptive commit messages

## Documentation Principles
- Maintain up-to-date documentation for all major components
- Include code examples for common use cases
- Document APIs with request/response examples
- Use a consistent documentation format

## Maintenance Guidelines
- Keep the root directory clean with only essential files
- Place new test files in the Sandbox_Files/Unused_Test_Files directory
- Update .dockerignore when adding new file types to exclude
- Document any changes to the folder structure
- Regularly review and clean up unused code and assets
- Maintain consistent naming conventions across the project

## README.md Template

When setting up a new project, create a README.md file in the root directory based on the following template structure. Use this template as a reference to manually create a comprehensive README.md file for your project.

### README.md Template Structure

```markdown
# [Project Name] Application

## Overview
[Brief description of the application and its purpose]

## Project Structure

The application follows this structure:

```
[Include the project's folder structure here]
```

## Development Setup

### Prerequisites
- [List required software and versions]
- [List required dependencies]

### Installation
1. [Step-by-step installation instructions]
2. [Include code examples for installation commands]
3. [Instructions for running the application]

## Docker Setup

### Prerequisites
- Docker installed on your system

### Building the Docker Image
[Include Docker build command]

### Running the Docker Container
[Include Docker run command]

### Accessing the Application
[Instructions for accessing the application]

### Docker Management Commands
[Include common Docker management commands]

## Version Control Guidelines

### Branching Strategy
[Describe the branching strategy]

### Commit Message Format
[Describe the commit message format]

### Tagging Releases
[Include instructions for tagging releases]
```"

set "FILE_ORG=## File Organization Principles

### 1. Analyze the Application Structure
- Identify the main application file(s) (e.g., main.py, Gospel_JukeBox.py)
- Identify essential data directories (e.g., mp3_files, pictures, data/songs)
- Identify configuration files (e.g., requirements.txt)
- Identify non-essential files (test files, backups, development scripts)

### 2. Recommended Folder Structure

```
/                           # Root directory
├── main.py                 # Main application file
├── requirements.txt        # Dependencies
├── data/                   # Application data
│   └── songs/              # Song directories with mp3, txt, and image files
├── mp3_files/              # MP3 files with corresponding lyrics
├── pictures/               # Image files
├── Sandbox_Files/          # Non-essential files
│   ├── .dockerignore       # Docker ignore file
│   ├── .env                # Environment variables
│   ├── Dockerfile          # Docker configuration
│   └── Unused_Test_Files/  # Test and backup files
```

### 3. File Classification Guidelines

#### Essential Files (Keep in Root Directory)
- Main application files (e.g., main.py, Gospel_JukeBox.py)
- Configuration files (e.g., requirements.txt)
- README.md (contains setup instructions and project overview)

#### Essential Data Directories (Keep in Root Directory)
- mp3_files/
- pictures/
- data/

#### Non-Essential Files (Move to Sandbox_Files)
- Docker configuration files (place at Sandbox_Files root)
- Development and test files (place in Unused_Test_Files subfolder)
  - Backup files (*_BU*, *.bak)
  - Test files (app.py, create_folders.bat)
  - Unused code files (*.pyyy)
  - Development scripts"

set "LANG_DIR=## Language-Specific Directory Structures

### Python Applications
```
/
├── src/                    # Source code
│   ├── __init__.py         # Makes src a package
│   ├── main.py             # Entry point
│   ├── models/             # Data models
│   ├── controllers/        # Business logic
│   ├── views/              # UI components (for web apps)
│   └── utils/              # Helper functions
├── tests/                  # Test files
├── docs/                   # Documentation
├── config/                 # Configuration files
├── requirements.txt        # Production dependencies
└── README.md
```

### JavaScript/TypeScript (React) Applications
```
/
├── src/                    # Source code
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── context/            # React context providers
│   ├── services/           # API services
│   ├── utils/              # Helper functions
│   ├── assets/             # Static assets
│   ├── App.js              # Main App component
│   └── index.js            # Entry point
├── public/                 # Public assets
└── README.md
```

### Java (Spring Boot) Applications
```
/
├── src/
│   ├── main/
│   │   ├── java/com/example/project/
│   │   │   ├── controllers/    # REST controllers
│   │   │   ├── models/         # Data models
│   │   │   ├── repositories/   # Data access
│   │   │   ├── services/       # Business logic
│   │   │   ├── config/         # Configuration
│   │   │   └── Application.java # Entry point
│   │   └── resources/
│   └── test/
├── pom.xml                # Project dependencies
└── README.md
```"

set "ENV_CONFIG=## Environment Configuration Principles
- Create separate configuration files for different environments
- Never commit sensitive information to version control
- Use environment variables for configuration that changes between environments
- Document all required environment variables"

set "ASSET_MGMT=## Asset Management Principles
- Use a consistent naming convention for all asset files
- Optimize assets during the build process
- Implement caching strategies for static assets
- Separate source assets from compiled/processed assets"

set "DB_ORG=## Database Organization Principles
- Use sequential naming for migration files
- Ensure migrations are idempotent
- Include both "up" and "down" migrations for reversibility
- Document database schema changes"

set "VERSION_CTRL=## Version Control Principles
- Create a comprehensive .gitignore file
- Use semantic versioning for releases
- Implement a consistent branching strategy
- Write descriptive commit messages"

set "DOC_PRINCIPLES=## Documentation Principles
- Maintain up-to-date documentation for all major components
- Include code examples for common use cases
- Document APIs with request/response examples
- Use a consistent documentation format"

set "MAINTENANCE=## Maintenance Guidelines
- Keep the root directory clean with only essential files
- Place new test files in the Sandbox_Files/Unused_Test_Files directory
- Update .dockerignore when adding new file types to exclude
- Document any changes to the folder structure
- Regularly review and clean up unused code and assets
- Maintain consistent naming conventions across the project"

set "README_TEMPLATE=## README.md Template

When setting up a new project, create a README.md file in the root directory based on the following template structure. Use this template as a reference to manually create a comprehensive README.md file for your project.

### README.md Template Structure

```markdown
# [Project Name] Application

## Overview
[Brief description of the application and its purpose]

## Project Structure

The application follows this structure:

```
[Include the project's folder structure here]
```

## Development Setup

### Prerequisites
- [List required software and versions]
- [List required dependencies]

### Installation
1. [Step-by-step installation instructions]
2. [Include code examples for installation commands]
3. [Instructions for running the application]

## Docker Setup

### Prerequisites
- Docker installed on your system

### Building the Docker Image
[Include Docker build command]

### Running the Docker Container
[Include Docker run command]

### Accessing the Application
[Instructions for accessing the application]

### Docker Management Commands
[Include common Docker management commands]

## Version Control Guidelines

### Branching Strategy
[Describe the branching strategy]

### Commit Message Format
[Describe the commit message format]

### Tagging Releases
[Include instructions for tagging releases]
```"

:: ===================================================
:: MAIN MENU FUNCTION
:: ===================================================
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

:: ===================================================
:: SELECT INPUT METHOD
:: ===================================================
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

:: ===================================================
:: COPY TO CLIPBOARD METHOD
:: ===================================================
:COPY_TO_CLIPBOARD
cls
echo Preparing selected section for clipboard...

set "TEMP_FILE=%TEMP%\ai_prompt_section.txt"

:: Write the selected section to a temporary file
echo !%SECTION%! > "%TEMP_FILE%"

:: Copy the content to clipboard
type "%TEMP_FILE%" | clip

echo.
echo ===================================================
echo The selected section has been copied to clipboard.
echo You can now paste it into the AI interface.
echo ===================================================
echo.
echo Press any key to return to the main menu...
pause >nul
goto :MAIN_MENU

:: ===================================================
:: SIMULATE TYPING METHOD
:: ===================================================
:SIMULATE_TYPING
cls
echo Preparing selected section for typing simulation...

set "TEMP_FILE=%TEMP%\ai_prompt_section.txt"

:: Write the selected section to a temporary file
echo !%SECTION%! > "%TEMP_FILE%"

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

powershell -Command "$text = Get-Content -Path '%TEMP_FILE%' -Raw; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait($text)"

echo.
echo ===================================================
echo Done! The text should now be entered in the AI input field.
echo ===================================================
echo.
echo Press any key to return to the main menu...
pause >nul
goto :MAIN_MENU

:: ===================================================
:: EXIT FUNCTION
:: ===================================================
:EXIT
cls
echo Thank you for using the Master Prompt Selection Utility.
echo Goodbye!
echo.
timeout /t 2 >nul
exit /b 0