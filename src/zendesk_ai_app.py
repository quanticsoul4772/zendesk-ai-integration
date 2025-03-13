import os
import time
import logging
import schedule
import requests
from datetime import datetime
import urllib.parse  # Import for URL encoding

from dotenv import load_dotenv
from flask import Flask, request, jsonify

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket
import openai

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

# OpenAI credentials
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))

# Database credentials (PostgreSQL example)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "zendesk_analytics")

# URL encode the password to handle special characters
DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#############################################################################
# 2. SETUP DATABASE (SQLALCHEMY)
#############################################################################

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class TicketAnalysis(Base):
    __tablename__ = "ticket_analysis"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, index=True)
    subject = Column(String(255))
    category = Column(String(50))
    sentiment = Column(String(50))
    confidence = Column(Float)
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

#############################################################################
# 3. AI LOGIC
#############################################################################

def call_openai_api(content: str) -> dict:
    try:
        prompt = f"""
        Analyze the following customer message and:
        1) Provide sentiment: Positive, Negative, or Neutral.
        2) Provide category label (e.g., billing issue, technical issue, general inquiry).
        Message: {content}
        Format your response as JSON with keys: sentiment, category.
        """

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        assistant_reply = response.choices[0].message.content
        
        import json
        parsed = json.loads(assistant_reply)
        return parsed
    except Exception as e:
        logger.exception("Error calling OpenAI API")
        return {"sentiment": "unknown", "category": "uncategorized"}

#############################################################################
# 4. CORE FUNCTIONS
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

def analyze_and_update_ticket(ticket: Ticket):
    session = SessionLocal()
    try:
        description = ticket.description or ""
        ai_result = call_openai_api(description)

        sentiment = ai_result.get("sentiment", "unknown").lower().replace(" ", "_")
        category = ai_result.get("category", "general_inquiry").lower().replace(" ", "_")

        if category not in ticket.tags:
            ticket.tags.append(category)
        if f"sentiment_{sentiment}" not in ticket.tags:
            ticket.tags.append(f"sentiment_{sentiment}")

        ticket.comment = {
            "body": f"AI Classification:\n- Category: {category}\n- Sentiment: {sentiment}",
            "public": False
        }

        exponential_backoff_retry(zenpy_client.tickets.update, ticket)
        logger.info(f"Updated ticket #{ticket.id} - category={category}, sentiment={sentiment}")

        db_record = TicketAnalysis(
            ticket_id=ticket.id,
            subject=ticket.subject,
            category=category,
            sentiment=sentiment,
            confidence=1.0,
            description=description
        )
        session.add(db_record)
        session.commit()
        logger.info(f"Stored analysis for ticket #{ticket.id}")
    except Exception as e:
        logger.exception(f"Error processing ticket #{ticket.id}")
        session.rollback()
    finally:
        session.close()

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
        sentiment_counts = {}
        priority_counts = {}
        
        for ticket in tickets:
            # Count by status
            status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
            
            # Count by category and sentiment (from tags)
            for tag in ticket.tags:
                if tag.startswith("sentiment_"):
                    sentiment = tag.replace("sentiment_", "")
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                elif not tag.startswith("sentiment_"):  # Assuming non-sentiment tags are categories
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
    session = SessionLocal()
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        recent_analyses = session.query(TicketAnalysis).filter(
            TicketAnalysis.timestamp >= cutoff
        ).all()

        total = len(recent_analyses)
        categories = {}
        sentiments = {}

        for record in recent_analyses:
            categories[record.category] = categories.get(record.category, 0) + 1
            sentiments[record.sentiment] = sentiments.get(record.sentiment, 0) + 1

        summary_text = f"""
========================================
DATABASE TICKET SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M')})
========================================

Total Tickets Analyzed (last {days_back} days): {total}

CATEGORY BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{category}: {count}" for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)]) + f"""

SENTIMENT BREAKDOWN:
{'-' * 20}
""" + "\n".join([f"{sentiment}: {count}" for sentiment, count in sorted(sentiments.items(), key=lambda x: x[1], reverse=True)])
        
        print(summary_text)
        return summary_text
    except Exception as e:
        logger.exception("Failed to generate summary from database")
        return f"Error generating summary: {str(e)}"
    finally:
        session.close()

def send_summary_notification(frequency="daily"):
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        if frequency == "daily":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            from datetime import timedelta
            cutoff = now - timedelta(days=7)

        recent_analyses = session.query(TicketAnalysis).filter(
            TicketAnalysis.timestamp >= cutoff
        ).all()

        total = len(recent_analyses)
        categories = {}
        sentiments = {}

        for record in recent_analyses:
            categories[record.category] = categories.get(record.category, 0) + 1
            sentiments[record.sentiment] = sentiments.get(record.sentiment, 0) + 1

        summary_text = (
            f"Zendesk {frequency.capitalize()} Summary:\n"
            f"Tickets Analyzed: {total}\n"
            f"Categories: {categories}\n"
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
        session.close()

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

#############################################################################
# 7. MAIN
#############################################################################

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Zendesk AI Integration App")
    parser.add_argument("--mode", choices=["run", "webhook", "schedule", "summary"], default="run")
    parser.add_argument("--status", default="open")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--days", type=int, default=30, help="Number of days back to include in summary")
    args = parser.parse_args()

    if args.mode == "run":
        logger.info("Fetching & processing tickets one-time...")
        tickets = fetch_tickets(status=args.status, limit=args.limit)
        for t in tickets:
            analyze_and_update_ticket(t)
        logger.info("Done processing.")
    elif args.mode == "webhook":
        logger.info("Starting Flask webhook server on port 5000...")
        app.run(port=5000, debug=True)
    elif args.mode == "schedule":
        logger.info("Starting scheduled tasks for daily/weekly summaries...")
        schedule_tasks()
    elif args.mode == "summary":
        logger.info(f"Generating summary of {args.status} tickets...")
        # Try to get summary from Zendesk directly first
        generate_summary_from_zendesk(status=args.status)
        print("\n")
        # Then show summary from database 
        generate_summary_from_db(days_back=args.days)