@echo off
REM Launcher batch file for Zendesk AI Integration interactive menu

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Running with system Python.
)

REM Run the menu launcher
python zendesk_menu.py

REM If in virtual environment, deactivate
if defined VIRTUAL_ENV (
    call deactivate
)
