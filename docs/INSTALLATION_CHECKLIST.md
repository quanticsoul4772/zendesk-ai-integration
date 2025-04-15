# Zendesk AI Integration - Installation Checklist

Use this checklist to ensure you have everything ready before starting the installation process.

## Prerequisites Checklist

- [ ] **System Requirements**
  - [ ] Python 3.9 or higher installed 
  - [ ] Administrator/sudo access on your machine
  - [ ] At least 500MB of free disk space
  - [ ] Stable internet connection

- [ ] **Required Credentials**
  - [ ] Zendesk email address
  - [ ] Zendesk API token (Get this from Zendesk Admin → Settings → API)
  - [ ] Zendesk subdomain (the 'example' part of example.zendesk.com)
  - [ ] At least one of the following:
    - [ ] OpenAI API key, OR
    - [ ] Anthropic API key (Claude)

- [ ] **Database Options (Choose One)**
  - [ ] MongoDB Atlas account details (for cloud database)
  - [ ] Docker installed (for containerized MongoDB)
  - [ ] Local MongoDB installation
  - [ ] Using existing MongoDB instance

- [ ] **Time Required**
  - [ ] 15-30 minutes for basic installation
  - [ ] Additional 15 minutes for database setup (if using MongoDB Atlas)

## Setup Process Summary

1. Download the installer
2. Run the installer script
3. Answer the configuration questions
4. Verify installation with a test command

## Post-Installation Verification

- [ ] Successfully run the test command
- [ ] Connect to your Zendesk account
- [ ] Test AI analysis on a sample ticket

## Need Help?

If you encounter any issues during installation, please check:
- The troubleshooting section in the documentation
- Ask in the #zendesk-integration Slack channel
- Contact the development team at dev-support@example.com
