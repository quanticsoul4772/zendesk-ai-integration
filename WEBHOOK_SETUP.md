# Zendesk Webhook Configuration Guide

This guide explains how to configure Zendesk to send webhook notifications to your integration server.

## Prerequisites

1. Zendesk administrator access
2. Your integration server running in webhook mode
3. A publicly accessible URL for your webhook server
4. The webhook secret key from your `.env` file

## Important Note: Read-Only Operation

The webhook server operates in a **completely read-only mode**, meaning:
1. It analyzes tickets using AI
2. It stores analysis results in MongoDB
3. It **never modifies tickets** in Zendesk

This design ensures the system can safely be used in production environments without risk of interfering with support workflows.

## Starting the Webhook Server

To run the webhook server using our modular architecture:

```bash
python src/zendesk_ai_app.py --mode webhook
```

This will:
1. Initialize the Zendesk client, AI analyzer, and database repository modules
2. Create a Flask server with the appropriate routes
3. Apply security features (IP whitelisting and signature verification)
4. Start listening for incoming webhooks on port 5000 (default)

You can customize the host and port:

```bash
python src/zendesk_ai_app.py --mode webhook --host 127.0.0.1 --port 8080
```

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
3. Verify that the ticket was analyzed and the results stored in MongoDB

## Webhook Server Implementation

In our modular architecture, webhooks are handled by the following components:

1. `src/modules/webhook_server.py` - Core webhook server implementation 
   - Contains the Flask server setup
   - Defines webhook routes
   - Handles incoming JSON payloads
   - Coordinates with other modules for processing

2. `src/security.py` - Security components
   - Provides IP whitelisting via a decorator
   - Verifies webhook signatures via a decorator
   - Validates incoming requests

When a webhook is received, the server:
1. Validates the request (IP and signature)
2. Extracts the ticket ID from the payload
3. Fetches the complete ticket data from Zendesk
4. Sends the ticket content to the AI analyzer
5. Stores the analysis results in the database
6. Returns a success/failure response to Zendesk

## Health Check Endpoint

The webhook server also provides a health check endpoint at `/health` that you can use to verify the server is running:

```
GET https://your-server.com/health
```

This endpoint returns a simple status response and can be used for monitoring and availability checks.

## Troubleshooting

### Webhook Not Firing

- Check that the trigger is active
- Ensure conditions are set correctly
- Verify webhook status in Admin → Extensions → Webhooks

### Authentication Failures

- Confirm the shared secret in Zendesk matches your `.env` file
- Check server logs for detailed error messages
- Ensure the `WEBHOOK_SECRET_KEY` environment variable is set correctly

### Connection Issues

- Verify your server is publicly accessible
- Check firewall settings and network rules
- Ensure your server is handling POST requests properly

### Module Import Errors

If you encounter module import errors:
1. Make sure you're running the application from the project root directory
2. Check that your virtual environment is activated
3. Verify that all required packages are installed: `pip install -r requirements.txt`

## Security Considerations

- Always use HTTPS for your webhook endpoint
- Regularly rotate your webhook secret key
- Use IP whitelisting if your Zendesk instance has fixed IP addresses
- Monitor webhook activity for unauthorized access attempts
- Consider rate limiting for protection against DoS attacks