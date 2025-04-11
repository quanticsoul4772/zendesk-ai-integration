@echo off
REM Multi-View Reports Launcher
REM This script activates the virtual environment and runs the multi-view report generator.

SET SCRIPT_DIR=%~dp0
CD /D "%SCRIPT_DIR%"

IF EXIST "venv\Scripts\activate.bat" (
    CALL venv\Scripts\activate.bat
) ELSE (
    ECHO Virtual environment not found. Attempting to run with system Python.
)

ECHO Starting Multi-View Report Generator...
python multi_view_reports.py %*

IF ERRORLEVEL 1 (
    ECHO An error occurred. See the log for details.
    PAUSE
)
