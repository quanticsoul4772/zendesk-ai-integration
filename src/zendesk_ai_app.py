import os
import time
import logging
import schedule
import requests
from datetime import datetime
from dateutil import parser

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket

# Import MongoDB helper
from mongodb_helper import get_collection, find_analyses_since, insert_ticket_analysis, close_connections

# Import security module
from security import ip_whitelist, webhook_auth

# Import AI service
from ai_service import analyze_ticket_content

#############################################################################
# 1. LOAD ENVIRONMENT VARIABLES & CONFIGURE LOGGING
#############################################################################

# Load .env file if present
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Zendesk credentials
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL", "[email protected]")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN", "YOUR_ZENDESK_API_TOKEN")
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN", "YOUR_SUBDOMAIN")

zenpy_client = Zenpy(
    email=ZENDESK_EMAIL,
    token=ZENDESK_API_TOKEN,
    subdomain=ZENDESK_SUBDOMAIN
)

# MongoDB collection is initialized through mongodb_helper module

#############################################################################
# 2. DATABASE ACCESS (MongoDB via Helper)
#############################################################################

# MongoDB connection is handled by the mongodb_helper module
# This keeps the database connection details isolated for better maintainability

#############################################################################
# 3. CORE FUNCTIONS
#############################################################################

def exponential_backoff_retry(func, *args, **kwargs):
    max_retries = 5
    backoff_factor = 2
    delay = 1

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor

    logger.error("Max retries exceeded. Aborting.")
    raise Exception("Max retries exceeded")

def fetch_tickets(status="open", limit=10):
    try:
        all_tickets = zenpy_client.tickets()
        filtered = [ticket for ticket in all_tickets if ticket.status == status]
        return filtered[:limit]
    except Exception as e:
        logger.exception("Error fetching tickets")
        return []

def fetch_tickets_from_view(view_id, limit=None):
    """
    Fetch tickets from a specific Zendesk view.
    
    Args:
        view_id: ID of the Zendesk view to fetch tickets from
        limit: Maximum number of tickets to retrieve, None means no limit
        
    Returns:
        List of Ticket objects
    """
    try:
        if limit:
            logger.info(f"Fetching up to {limit} tickets from view {view_id}")
        else:
            logger.info(f"Fetching all tickets from view {view_id}")
            
        # Zenpy API expects view_id as a positional argument
        tickets = zenpy_client.views.tickets(view_id)
        
        # Apply limit only if specified
        if limit is not None:
            return list(tickets)[:limit]
        else:
            return list(tickets)
    except Exception as e:
        logger.exception(f"Error fetching tickets from view {view_id}")
        return []
        
def list_all_views():
    """
    List all available Zendesk views with their IDs and titles.
    
    Returns:
        String containing formatted list of views
    """
    try:
        views = zenpy_client.views()
        view_list = "\nAVAILABLE ZENDESK VIEWS:\n" + "-" * 40 + "\n"
        view_list += "ID\t\tTITLE\n"
        view_list += "-" * 40 + "\n"
        
        for view in views:
            view_list += f"{view.id}\t\t{view.title}\n"
            
        return view_list
    except Exception as e:
        logger.exception("Error fetching views")
        return "Error fetching views: " + str(e)

def fetch_tickets_by_view_name(view_name, limit=None):
    """
    Fetch tickets from a specific Zendesk view by its name.
    
    Args:
        view_name: Name of the Zendesk view to fetch tickets from
        limit: Maximum number of tickets to retrieve, None means no limit
        
    Returns:
        List of Ticket objects
    """
    try:
        logger.info(f"Searching for view named '{view_name}'")
        # Get all views
        views = zenpy_client.views()
        
        # Find the view with the specified name
        target_view_id = None
        for view in views:
            if view.title == view_name:
                target_view_id = view.id
                logger.info(f"Found view '{view_name}' with ID {target_view_id}")
                break
        
        if not target_view_id:
            logger.error(f"View '{view_name}' not found")
            return []
        
        # Get tickets from the view
        if limit:
            logger.info(f"Fetching up to {limit} tickets from view '{view_name}' (ID: {target_view_id})")
        else:
            logger.info(f"Fetching all tickets from view '{view_name}' (ID: {target_view_id})")
            
        # Zenpy API expects view_id as a positional argument
        tickets = zenpy_client.views.tickets(target_view_id)
        
        # Apply limit only if specified
        if limit is not None:
            return list(tickets)[:limit]
        else:
            return list(tickets)
    except Exception as e:
        logger.exception(f"Error fetching tickets from view '{view_name}'")
        return []

def analyze_and_update_ticket(ticket: Ticket):
    try:
        description = ticket.description or ""
        
        # Use the enhanced AI service
        ai_result = analyze_ticket_content(description)

        sentiment = ai_result.get("sentiment", "unknown")
        category = ai_result.get("category", "general_inquiry")
        component = ai_result.get("component", "none")
        confidence = ai_result.get("confidence", 0.0)

        # Add category tag
        if category not in ticket.tags:
            ticket.tags.append(category)
            
        # Add sentiment tag
        if f"sentiment_{sentiment}" not in ticket.tags:
            ticket.tags.append(f"sentiment_{sentiment}")
            
        # Add component tag if not "none"
        if component != "none" and component not in ticket.tags:
            ticket.tags.append(component)

        ticket.comment = {
            "body": f"AI Classification:\n- Category: {category}\n- Component: {component}\n- Sentiment: {sentiment}\n- Confidence: {confidence:.2f}",
            "public": False
        }

        exponential_backoff_retry(zenpy_client.tickets.update, ticket)
        logger.info(f"Updated ticket #{ticket.id} - category={category}, component={component}, sentiment={sentiment}")

        # Store analysis in MongoDB
        db_record = {
            "ticket_id": ticket.id,
            "subject": ticket.subject,
            "category": category,
            "component": component,
            "sentiment": sentiment,
            "confidence": confidence,
            "description": description,
            "timestamp": datetime.utcnow()
        }
        insert_ticket_analysis(db_record)
        logger.info(f"Stored analysis for ticket #{ticket.id}")
    except Exception as e:
        logger.exception(f"Error processing ticket #{ticket.id}")

#############################################################################
# 5. SCHEDULING & SUMMARIES
#############################################################################

def generate_summary_from_zendesk(status="open"):
    """Generate a summary of tickets directly from Zendesk API"""
    try:
        tickets = zenpy_client.tickets(status=status)
        
        # Count tickets by status
        status_counts = {}
        category_counts = {}
        component_counts = {}
        sentiment_counts = {}
        priority_counts = {}
        
        for ticket in tickets:
            # Count by status
            status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
            
            # Count by category, component, and sentiment (from tags)
            for tag in ticket.tags:
                if tag.startswith("sentiment_"):
                    sentiment = tag.replace("sentiment_", "")
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                # Check for component tags
                elif tag in ["gpu", "cpu", "drive", "memory", "power_supply", "motherboard", "cooling", "display", "network"]:
                    component_counts[tag] = component_counts.get(tag, 0) + 1
                # Assuming other tags are categories
                elif not tag.startswith("sentiment_"):
                    category_counts[tag] = category_counts.get(tag, 0) + 1
            
            # Count by priority
            if hasattr(ticket, 'priority'):
                priority = ticket.priority or "none"
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Generate summary text
        total_tickets = len(list(tickets))
        
        summary_text = f"""
========================================
ZENDESK TICKET SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M')})
========================================

Total Tickets: {total_tickets}

STATUS BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{status}: {count}" for status, count in status_counts.items()]) + f"""

CATEGORY BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{category}: {count}" for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]) + f"""

COMPONENT BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{component}: {count}" for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True)]) + f"""

SENTIMENT BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{sentiment}: {count}" for sentiment, count in sorted(sentiment_counts.items(), key=lambda x: x[1], reverse=True)]) + f"""

PRIORITY BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{priority}: {count}" for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True)])
        
        print(summary_text)
        return summary_text
        
    except Exception as e:
        logger.exception("Error generating summary from Zendesk")
        return f"Error generating summary: {str(e)}"

def generate_summary_from_db(days_back=30):
    """Generate a summary of tickets from the database"""
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        # Query MongoDB for recent analyses
        recent_analyses = find_analyses_since(cutoff)
        total = len(recent_analyses)
        categories = {}
        components = {}
        sentiments = {}

        for record in recent_analyses:
            categories[record["category"]] = categories.get(record["category"], 0) + 1
            
            # Handle component data if it exists in the record
            if "component" in record and record["component"] != "none":
                components[record["component"]] = components.get(record["component"], 0) + 1
                
            sentiments[record["sentiment"]] = sentiments.get(record["sentiment"], 0) + 1

        summary_text = f"""
========================================
DATABASE TICKET SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M')})
========================================

Total Tickets Analyzed (last {days_back} days): {total}

CATEGORY BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{category}: {count}" for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)]) + f"""

COMPONENT BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{component}: {count}" for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True)]) + f"""

SENTIMENT BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{sentiment}: {count}" for sentiment, count in sorted(sentiments.items(), key=lambda x: x[1], reverse=True)])
        
        print(summary_text)
        return summary_text
    except Exception as e:
        logger.exception("Failed to generate summary from database")
        return f"Error generating summary: {str(e)}"
    finally:
        pass

def generate_pending_support_report(tickets, view_name="Pending Support"):
    """
    Generate a detailed report for tickets in the Pending Support view.
    
    Args:
        tickets: List of Zendesk Ticket objects
        view_name: Name of the view (for display purposes)
        
    Returns:
        String containing the formatted report
    """
    # Count various metrics
    status_counts = {}
    priority_counts = {}
    component_counts = {}
    age_buckets = {
        "today": 0,
        "yesterday": 0,
        "this_week": 0,
        "older": 0
    }
    customer_segments = {}
    
    # Prepare ticket details
    ticket_details = []
    today = datetime.now().date()
    
    for ticket in tickets:
        # Track status
        status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
        
        # Track priority
        priority = ticket.priority or "normal"
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Track customer segment (organization)
        org_name = "No Organization"
        if hasattr(ticket, 'organization') and ticket.organization:
            org_name = ticket.organization.name
            customer_segments[org_name] = customer_segments.get(org_name, 0) + 1
        
        # Track ticket age
        if hasattr(ticket, 'created_at'):
            created_at = ticket.created_at
            # Check if created_at is a string and convert it to datetime if needed
            if isinstance(created_at, str):
                from dateutil import parser
                try:
                    created_at = parser.parse(created_at)
                except Exception as e:
                    logger.warning(f"Could not parse date: {created_at}, error: {str(e)}")
                    created_at = None
            
            if created_at:
                try:
                    created_date = created_at.date()
                    delta = (today - created_date).days
                    if delta == 0:
                        age_buckets["today"] += 1
                    elif delta == 1:
                        age_buckets["yesterday"] += 1
                    elif delta <= 7:
                        age_buckets["this_week"] += 1
                    else:
                        age_buckets["older"] += 1
                except Exception as e:
                    logger.warning(f"Error processing date: {str(e)}")
        
        
        # Analyze ticket for hardware components
        hardware_components = []
        
        # First check for AI-generated component tags
        for tag in ticket.tags:
            if tag in ["gpu", "cpu", "drive", "memory", "power_supply", "motherboard", 
                      "cooling", "display", "network", "ipmi", "bios"]:
                hardware_components.append(tag)
                component_counts[tag] = component_counts.get(tag, 0) + 1
        
        # Also check title/subject for component keywords
        subject_lower = ticket.subject.lower() if hasattr(ticket, 'subject') else ""
        component_keywords = {
            "gpu": ["gpu", "graphics", "video card", "rtx", "nvidia", "amd", "radeon"],
            "cpu": ["cpu", "processor", "intel", "amd", "ryzen", "xeon"],
            "drive": ["drive", "ssd", "hdd", "storage", "disk", "nvme"],
            "memory": ["memory", "ram", "dimm"],
            "power_supply": ["power supply", "psu", "power"],
            "motherboard": ["motherboard", "mainboard"],
            "cooling": ["cooling", "fan", "temperature", "overheating"],
            "display": ["display", "monitor", "screen"],
            "network": ["network", "ethernet", "wifi", "wireless"],
            "boot": ["boot", "post", "startup"],
            "bios": ["bios", "uefi"],
            "ipmi": ["ipmi", "bmc", "remote management"]
        }
        
        for component, keywords in component_keywords.items():
            if any(keyword in subject_lower for keyword in keywords) and component not in hardware_components:
                hardware_components.append(component)
                component_counts[component] = component_counts.get(component, 0) + 1
        
        # Store ticket details for report
        ticket_details.append({
            "id": ticket.id,
            "subject": ticket.subject if hasattr(ticket, 'subject') else "No subject",
            "status": ticket.status,
            "priority": priority,
            "components": hardware_components,
            "requester": ticket.requester.name if hasattr(ticket, 'requester') and hasattr(ticket.requester, 'name') else "Unknown",
            "organization": org_name,
            "created_at": ticket.created_at if hasattr(ticket, 'created_at') else None,
            "updated_at": ticket.updated_at if hasattr(ticket, 'updated_at') else None
        })
    
    # Generate the report
    report = f"""
===================================================
PENDING SUPPORT TICKET REPORT ({datetime.now().strftime('%Y-%m-%d %H:%M')})
===================================================

OVERVIEW
--------
Total Tickets: {len(tickets)}
Queue Purpose: New Support tickets waiting for assignment to agent
View: {view_name}

STATUS DISTRIBUTION
------------------
"""
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"{status}: {count}\n"
    
    report += f"""
PRIORITY DISTRIBUTION
--------------------
"""
    for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"{priority}: {count}\n"
    
    report += f"""
HARDWARE COMPONENT DISTRIBUTION
-----------------------------
"""
    for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"{component}: {count}\n"
    
    report += f"""
CUSTOMER DISTRIBUTION
------------------
"""
    for org, count in sorted(customer_segments.items(), key=lambda x: x[1], reverse=True)[:5]:
        report += f"{org}: {count}\n"
    
    report += f"""
TICKET AGE
---------
Today: {age_buckets["today"]}
Yesterday: {age_buckets["yesterday"]}
This Week: {age_buckets["this_week"]}
Older: {age_buckets["older"]}

TICKET DETAILS
-------------
"""
    
    # Sort tickets by creation date, newest first
    ticket_details.sort(key=lambda x: x["created_at"] if x["created_at"] else datetime.min, reverse=True)
    
    for ticket in ticket_details:
        report += f"#{ticket['id']} - {ticket['subject']} ({ticket['status']})\n"
        report += f"Priority: {ticket['priority']}\n"
        if ticket["components"]:
            report += f"Components: {', '.join(ticket['components'])}\n"
        report += f"Requester: {ticket['requester']} | Organization: {ticket['organization']}\n"
        if ticket["created_at"]:
            # Handle datetime formatting safely
            try:
                created_at = ticket["created_at"]
                if isinstance(created_at, str):
                    from dateutil import parser
                    created_at = parser.parse(created_at)
                report += f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}\n"
            except Exception as e:
                report += f"Created: {ticket['created_at']}\n"
                
        if ticket["updated_at"]:
            # Handle datetime formatting safely
            try:
                updated_at = ticket["updated_at"]
                if isinstance(updated_at, str):
                    from dateutil import parser
                    updated_at = parser.parse(updated_at)
                report += f"Updated: {updated_at.strftime('%Y-%m-%d %H:%M')}\n"
            except Exception as e:
                report += f"Updated: {ticket['updated_at']}\n"
        report += f"{'-' * 40}\n"
    
    return report

def generate_hardware_component_report(tickets):
    """
    Generate a detailed report focused on hardware components from a list of tickets.
    
    Args:
        tickets: List of Zendesk Ticket objects
        
    Returns:
        String containing the formatted report
    """
    # Count hardware component issues
    component_counts = {}
    status_counts = {}
    customer_segments = {}
    age_buckets = {
        "today": 0,
        "yesterday": 0,
        "this_week": 0,
        "older": 0
    }
    
    # Extract hardware component information from tickets
    component_tickets = []
    today = datetime.now().date()
    
    for ticket in tickets:
        # Track status
        status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
        
        # Track customer segment (organization)
        if hasattr(ticket, 'organization') and ticket.organization:
            org_name = ticket.organization.name
            customer_segments[org_name] = customer_segments.get(org_name, 0) + 1
        
        # Track ticket age
        created_date = ticket.created_at.date() if hasattr(ticket, 'created_at') else None
        if created_date:
            delta = (today - created_date).days
            if delta == 0:
                age_buckets["today"] += 1
            elif delta == 1:
                age_buckets["yesterday"] += 1
            elif delta <= 7:
                age_buckets["this_week"] += 1
            else:
                age_buckets["older"] += 1
        
        # Analyze ticket for hardware components
        hardware_components = []
        
        # First check for AI-generated component tags
        for tag in ticket.tags:
            if tag in ["gpu", "cpu", "drive", "memory", "power_supply", "motherboard", 
                      "cooling", "display", "network", "ipmi", "bios"]:
                hardware_components.append(tag)
                component_counts[tag] = component_counts.get(tag, 0) + 1
        
        # Also check title/subject for component keywords
        subject_lower = ticket.subject.lower() if hasattr(ticket, 'subject') else ""
        component_keywords = {
            "gpu": ["gpu", "graphics", "video card", "rtx", "nvidia", "amd", "radeon"],
            "cpu": ["cpu", "processor", "intel", "amd", "ryzen", "xeon"],
            "drive": ["drive", "ssd", "hdd", "storage", "disk", "nvme"],
            "memory": ["memory", "ram", "dimm"],
            "power_supply": ["power supply", "psu", "power"],
            "motherboard": ["motherboard", "mainboard"],
            "cooling": ["cooling", "fan", "temperature", "overheating"],
            "display": ["display", "monitor", "screen"],
            "network": ["network", "ethernet", "wifi", "wireless"],
            "boot": ["boot", "post", "startup"],
            "bios": ["bios", "uefi"],
            "ipmi": ["ipmi", "bmc", "remote management"]
        }
        
        for component, keywords in component_keywords.items():
            if any(keyword in subject_lower for keyword in keywords) and component not in hardware_components:
                hardware_components.append(component)
                component_counts[component] = component_counts.get(component, 0) + 1
        
        if hardware_components:
            component_tickets.append({
                "id": ticket.id,
                "subject": ticket.subject if hasattr(ticket, 'subject') else "No subject",
                "status": ticket.status,
                "components": hardware_components,
                "requester": ticket.requester.name if hasattr(ticket, 'requester') and hasattr(ticket.requester, 'name') else "Unknown",
                "organization": ticket.organization.name if hasattr(ticket, 'organization') and ticket.organization else "No organization",
                "created_at": ticket.created_at if hasattr(ticket, 'created_at') else None
            })
    
    # Generate the report
    report = f"""
# Zendesk Hardware Support Ticket Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview
Total Tickets: {len(tickets)}
Hardware Component Issues: {len(component_tickets)}

## Status Distribution
{'-' * 40}
"""
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"{status}: {count}\n"
    
    report += f"""
## Hardware Component Distribution
{'-' * 40}
"""
    for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"{component}: {count}\n"
    
    report += f"""
## Customer Segment Distribution
{'-' * 40}
"""
    for org, count in sorted(customer_segments.items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"{org}: {count}\n"
    
    report += f"""
## Ticket Age
{'-' * 40}
Today: {age_buckets["today"]}
Yesterday: {age_buckets["yesterday"]}
This Week: {age_buckets["this_week"]}
Older: {age_buckets["older"]}

## Hardware Component Tickets
{'-' * 40}
"""
    
    # Sort component tickets by created date (newest first)
    component_tickets.sort(key=lambda x: x["created_at"] if x["created_at"] else datetime.min, reverse=True)
    
    for ticket in component_tickets:
        report += f"ID: #{ticket['id']} - {ticket['subject']}\n"
        report += f"Status: {ticket['status']} | Components: {', '.join(ticket['components'])}\n"
        report += f"Requester: {ticket['requester']} | Organization: {ticket['organization']}\n"
        if ticket["created_at"]:
            report += f"Created: {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        report += f"{'-' * 40}\n"
    
    return report

def send_summary_notification(frequency="daily"):
    try:
        now = datetime.utcnow()
        if frequency == "daily":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            from datetime import timedelta
            cutoff = now - timedelta(days=7)

        # Query MongoDB for recent analyses
        recent_analyses = find_analyses_since(cutoff)
        total = len(recent_analyses)
        categories = {}
        components = {}
        sentiments = {}

        for record in recent_analyses:
            categories[record["category"]] = categories.get(record["category"], 0) + 1
            
            # Handle component data if it exists in the record
            if "component" in record and record["component"] != "none":
                components[record["component"]] = components.get(record["component"], 0) + 1
                
            sentiments[record["sentiment"]] = sentiments.get(record["sentiment"], 0) + 1

        summary_text = (
            f"Zendesk {frequency.capitalize()} Summary:\n"
            f"Tickets Analyzed: {total}\n"
            f"Categories: {categories}\n"
            f"Components: {components}\n"
            f"Sentiments: {sentiments}\n"
        )
        logger.info(summary_text)

        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook_url and slack_webhook_url.startswith("http"):
            payload = {"text": summary_text}
            requests.post(slack_webhook_url, json=payload)
            logger.info("Slack notification sent.")
    except Exception as e:
        logger.exception("Failed to send summary notification")
    finally:
        pass

def schedule_tasks():
    schedule.every().day.at("09:00").do(send_summary_notification, frequency="daily")
    schedule.every().monday.at("09:00").do(send_summary_notification, frequency="weekly")

    while True:
        schedule.run_pending()
        time.sleep(60)

#############################################################################
# 6. WEBHOOK
#############################################################################

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
@ip_whitelist
@webhook_auth
def zendesk_webhook():
    data = request.json
    if not data or "ticket" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    ticket_id = data["ticket"]["id"]
    try:
        fetched_ticket = zenpy_client.tickets(id=ticket_id)
        if not fetched_ticket:
            return jsonify({"error": "Ticket not found"}), 404
        analyze_and_update_ticket(fetched_ticket)
        return jsonify({"status": "success", "ticket_id": ticket_id}), 200
    except Exception as e:
        logger.exception(f"Error processing ticket via webhook: {ticket_id}")
        return jsonify({"error": str(e)}), 500

# Add a health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint that doesn't require authentication"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

#############################################################################
# 7. MAIN
#############################################################################

if __name__ == "__main__":
    import argparse
    import atexit
    import os

    # Register function to close MongoDB connections on exit
    atexit.register(close_connections)

    parser = argparse.ArgumentParser(description="Zendesk AI Integration App")
    parser.add_argument("--mode", choices=["run", "webhook", "schedule", "summary", "report", "pending", "list-views"], default="run")
    parser.add_argument("--status", default="open")
    parser.add_argument("--limit", type=int, help="Optional: Maximum number of tickets to retrieve (if not specified, all tickets will be fetched)")
    parser.add_argument("--days", type=int, default=30, help="Number of days back to include in summary")
    parser.add_argument("--view", type=int, help="Zendesk view ID to analyze")
    parser.add_argument("--component-report", action="store_true", help="Generate a hardware component focused report")
    parser.add_argument("--pending-view", default="Pending Support", help="Name of the pending support view (default: 'Pending Support')")
    parser.add_argument("--output", help="Filename to save the report to (will be created in current directory)")
    args = parser.parse_args()

    try:
        if args.mode == "run":
            if args.view:
                logger.info(f"Fetching & processing tickets from view {args.view}...")
                tickets = fetch_tickets_from_view(view_id=args.view, limit=args.limit)
                if args.component_report:
                    report = generate_hardware_component_report(tickets)
                    print(report)
                    # Optionally save to file
                    report_filename = args.output if args.output else f"hardware_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                    with open(report_filename, "w") as f:
                        f.write(report)
                    logger.info(f"Hardware component report generated with {len(tickets)} tickets and saved to {report_filename}")
                else:
                    for t in tickets:
                        analyze_and_update_ticket(t)
                    logger.info("Done processing.")
            else:
                logger.info("Fetching & processing tickets one-time...")
                tickets = fetch_tickets(status=args.status, limit=args.limit)
                for t in tickets:
                    analyze_and_update_ticket(t)
                logger.info("Done processing.")
        elif args.mode == "webhook":
            logger.info("Starting Flask webhook server on port 5000...")
            logger.info("Security features enabled:")
            logger.info(f"- IP Whitelist: {'Enabled' if os.getenv('ALLOWED_IPS') else 'Disabled'}")
            logger.info(f"- Webhook Signature Verification: {'Enabled' if os.getenv('WEBHOOK_SECRET_KEY') else 'Disabled'}")
            # Flask will handle MongoDB connections during requests
            app.run(host='0.0.0.0', port=5000, debug=False)
        elif args.mode == "schedule":
            logger.info("Starting scheduled tasks for daily/weekly summaries...")
            schedule_tasks()
        elif args.mode == "report":
            if args.view:
                logger.info(f"Generating hardware component report for view {args.view}...")
                tickets = fetch_tickets_from_view(view_id=args.view, limit=args.limit)
                report = generate_hardware_component_report(tickets)
                print(report)
                # Optionally save to file
                report_filename = args.output if args.output else f"hardware_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                with open(report_filename, "w") as f:
                    f.write(report)
                logger.info(f"Hardware component report generated with {len(tickets)} tickets and saved to {report_filename}")
            else:
                logger.error("View ID is required for report mode. Use --view parameter.")
                
        elif args.mode == "list-views":
            logger.info("Listing all available Zendesk views...")
            views_list = list_all_views()
            print(views_list)
            # Optionally save to file
            if args.output:
                with open(args.output, "w") as f:
                    f.write(views_list)
                logger.info(f"Views list saved to {args.output}")
                
        elif args.mode == "pending":
            logger.info(f"Generating report for {args.pending_view} view...")
            # No default limit - fetch all tickets unless explicitly limited
            tickets = fetch_tickets_by_view_name(view_name=args.pending_view, limit=args.limit)
            if tickets:
                report = generate_pending_support_report(tickets, view_name=args.pending_view)
                print(report)
                # Optionally save to file
                report_filename = args.output if args.output else f"pending_support_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                with open(report_filename, "w") as f:
                    f.write(report)
                logger.info(f"Pending Support report generated with {len(tickets)} tickets and saved to {report_filename}")
            else:
                logger.error(f"No tickets found in '{args.pending_view}' view or view not found.")
                
        elif args.mode == "summary":
            logger.info(f"Generating summary of {args.status} tickets...")
            # Try to get summary from Zendesk directly first
            generate_summary_from_zendesk(status=args.status)
            print("\n")
            # Then show summary from database 
            generate_summary_from_db(days_back=args.days)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.exception(f"Error in main execution: {e}")
    finally:
        # Ensure connections are closed when the program exits
        close_connections()