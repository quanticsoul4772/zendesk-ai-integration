@echo off
echo Setting up Zendesk AI Integration from github.com/quanticsoul4772/zendesk-ai-integration

:: Set environment variables
set ZENDESK_AI_ORG=quanticsoul4772
set ZENDESK_AI_REPO=zendesk-ai-integration
set SKIP_CHECKSUM_VERIFY=true

:: Run the installer
python install.py

echo.
echo If installation was successful, you can run the application with:
echo run_zendesk_ai.bat --mode listviews
