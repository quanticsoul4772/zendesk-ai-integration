#!/bin/bash
echo "Setting up Zendesk AI Integration from github.com/quanticsoul4772/zendesk-ai-integration"

# Set environment variables
export ZENDESK_AI_ORG=quanticsoul4772
export ZENDESK_AI_REPO=zendesk-ai-integration
export SKIP_CHECKSUM_VERIFY=true

# Run the installer
python3 install.py

echo
echo "If installation was successful, you can run the application with:"
echo "./run_zendesk_ai.sh --mode listviews"
