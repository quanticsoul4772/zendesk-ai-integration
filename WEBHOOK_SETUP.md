# Zendesk Webhook Configuration Guide

This guide explains how to configure Zendesk to send webhook notifications to your integration server.

## Prerequisites

1. Zendesk administrator access
2. Your integration server running in webhook mode
3. A publicly accessible URL for your webhook server
4. The webhook secret key from your `.env` file

## Step 1: Access Zendesk Admin Center

1. Log in to your Zendesk account
2. Click on the Admin icon (gear) in the sidebar
3. Under "Settings", click on "Extensions"

## Step 2: Create a Webhook

1. In the Extensions page, click on "Webhooks"
2. Click "Add Webhook"
3. Fill in the following details:
   - **Webhook Name**: `Zendesk AI Integration`
   - **Endpoint URL**: `https://your-server.com/webhook` (replace with your actual server URL)
   - **Request method**: `POST`
   - **Request format**: `JSON`
   - **Authentication**: `Basic Auth` (if your server requires it)
   - **Security setting**: `Shared secret`
   - **Shared secret value**: Enter the `WEBHOOK_SECRET_KEY` value from your `.env` file

4. Click "Test webhook" to ensure connectivity
5. Click "Create" to save the webhook

## Step 3: Create a Trigger

Webhooks need triggers to determine when they should be called.

1. Go to Admin → Settings → Business Rules → Triggers
2. Click "Add Trigger"
3. Set up the trigger conditions:
   - **Name**: `AI Analysis for New Tickets`
   - **Category**: Optional (e.g., "Notifications")
   - **Description**: "Sends new tickets to AI analysis service"

4. Set the conditions:
   - Meet ALL of the following conditions:
     - `Ticket: Is Created` - `Is` - `True`

5. Set the actions:
   - `Notify webhook` - `Zendesk AI Integration`

6. Click "Create Trigger"

## Step 4: Create Additional Triggers (Optional)

You may want to create additional triggers for other events:

### For Ticket Updates

1. Create a new trigger named "AI Analysis for Updated Tickets"
2. Conditions:
   - `Ticket: Is Updated` - `Is` - `True`
   - `Ticket: Status` - `Changed`
3. Actions:
   - `Notify webhook` - `Zendesk AI Integration`

### For Comments

1. Create a new trigger named "AI Analysis for New Comments"
2. Conditions:
   - `Ticket: Comment` - `Is` - `Present`
   - `Ticket: Comment is Public` - `Is` - `True`
3. Actions:
   - `Notify webhook` - `Zendesk AI Integration`

## Step 5: Test the Configuration

1. Create a test ticket in Zendesk
2. Check your webhook server logs to confirm it received the webhook
3. Verify that the ticket was analyzed and updated with tags

## Troubleshooting

### Webhook Not Firing

- Check that the trigger is active
- Ensure conditions are set correctly
- Verify webhook status in Admin → Extensions → Webhooks

### Authentication Failures

- Confirm the shared secret in Zendesk matches your `.env` file
- Check server logs for detailed error messages

### Connection Issues

- Verify your server is publicly accessible
- Check firewall settings and network rules
- Ensure your server is handling POST requests properly

## Security Considerations

- Always use HTTPS for your webhook endpoint
- Regularly rotate your webhook secret key
- Use IP whitelisting if your Zendesk instance has fixed IP addresses
- Monitor webhook activity for unauthorized access attempts