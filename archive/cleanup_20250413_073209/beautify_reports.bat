@echo off
echo Zendesk AI Integration - HTML Report Beautifier
echo =============================================
echo.

rem Check if Python is available
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not available in the PATH
    exit /b 1
)

rem Check if an argument is provided
if "%~1"=="" (
    echo Usage: beautify_reports.bat [report_file.html]
    echo.
    echo If no specific file is provided, this script will beautify all HTML reports
    echo in the current directory.
    
    set /p process_all=Do you want to beautify all HTML reports in the current directory? (y/n): 
    
    if /i "%process_all%"=="y" (
        echo Processing all HTML reports...
        for %%f in (*.html) do (
            echo Processing: %%f
            python improve_html_report.py "%%f"
        )
        echo Done!
    ) else (
        echo Operation cancelled.
    )
) else (
    rem Process the specified file
    if not exist "%~1" (
        echo Error: File "%~1" not found.
        exit /b 1
    )
    
    echo Processing: %~1
    python improve_html_report.py "%~1"
    echo Done!
)

echo.
echo All reports have been beautified with modern styling and improved formatting.
echo The reports should now be much more readable and visually appealing.
