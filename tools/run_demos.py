#!/usr/bin/env python3
"""
Demo Utilities for Zendesk AI Integration

This script provides command-line demos for various components of the Zendesk AI Integration.
These were extracted from the test scripts to maintain the useful demonstration functionality
while properly organizing the test code in the tests/ directory.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zendesk_demos")

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)

def demo_ai_service():
    """Run a demonstration of the AI service."""
    try:
        from src.ai_service import analyze_ticket_content
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        print("AI Service Demo - Ticket Analysis")
        print("=================================")
        
        # Sample ticket
        sample_ticket = """
        Hello support team,
        
        I've been trying to use your product for the past week and I'm really impressed with the features.
        However, I'm having trouble with the export functionality. When I try to export my data to CSV,
        the application crashes. Could you please help me resolve this issue?
        
        Thanks,
        John
        """
        
        # Check if API key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY environment variable is not set.")
            print("The analysis will fail unless you set this environment variable.")
            print("For testing purposes only, you can set it temporarily:")
            print("  - Windows (PowerShell): $env:OPENAI_API_KEY = 'your-api-key'")
            print("  - Windows (CMD): set OPENAI_API_KEY=your-api-key")
            print("  - Linux/macOS: export OPENAI_API_KEY=your-api-key")
            return
        
        print("\nSample Ticket:")
        print(sample_ticket)
        
        print("\nAnalyzing ticket...")
        result = analyze_ticket_content(sample_ticket)
        
        print("\nAnalysis Result:")
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    {subkey}: {subvalue}")
            else:
                print(f"  {key}: {value}")
                
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you're running this script from the project root directory.")
        
def demo_sentiment_analysis():
    """Run a demonstration of the enhanced sentiment analysis."""
    try:
        from src.enhanced_sentiment import enhanced_analyze_ticket_content
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Sample tickets with varying sentiment characteristics
        SAMPLE_TICKETS = [
            {
                "title": "Low urgency order status",
                "content": """
                Hello, I placed an order for a new workstation last week (Order #12345).
                I was just wondering if you could provide me with an estimated delivery date?
                Thank you for your help!
                """
            },
            {
                "title": "Medium urgency technical issue",
                "content": """
                Hi support team,
                
                I'm having an issue with one of our development systems. The system keeps freezing
                when running our compute workloads. I've tried rebooting and checking temperatures
                but it still happens. This is slowing down our development process and we need
                to get it resolved in the next few days if possible.
                
                System details:
                - Model: Traverse Pro X8
                - CPU: Intel i9-13900K
                - GPU: 2x RTX 4090
                
                Thanks,
                Dave
                """
            },
            {
                "title": "High urgency production issue",
                "content": """
                URGENT HELP NEEDED! Our main production render server has completely crashed
                and we have a client deliverable due tomorrow morning! This is the third system
                failure this month and it's severely impacting our business. We have a team of
                15 artists sitting idle and we're losing thousands of dollars per hour!
                
                The system was running fine last night but now it won't POST and all diagnostic
                LEDs are red. We've already tried reseating components and testing the power supply.
                
                We need someone to call us IMMEDIATELY to help troubleshoot this.
                Our business literally depends on getting this fixed TODAY.
                
                Jason Miller
                Chief Technical Officer
                """
            }
        ]
        
        def display_analysis_results(title, analysis):
            """Display the analysis results in a readable format."""
            print(f"\n{'='*80}")
            print(f"ANALYSIS RESULTS: {title}")
            print(f"{'='*80}")
            
            # Extract sentiment data
            sentiment = analysis.get("sentiment", {})
            
            # Print sentiment metrics
            print(f"Sentiment Polarity: {sentiment.get('polarity', 'unknown')}")
            print(f"Urgency Level: {sentiment.get('urgency_level', 'unknown')}/5")
            print(f"Frustration Level: {sentiment.get('frustration_level', 'unknown')}/5")
            print(f"Technical Expertise: {sentiment.get('technical_expertise', 'unknown')}/5")
            
            # Print business impact
            business_impact = sentiment.get("business_impact", {})
            if business_impact and business_impact.get("detected", False):
                print(f"Business Impact: DETECTED - {business_impact.get('description', '')}")
            else:
                print("Business Impact: None detected")
            
            # Print emotions
            emotions = sentiment.get("emotions", [])
            if emotions:
                print(f"Emotions: {', '.join(emotions)}")
            
            # Print category and component
            print(f"Category: {analysis.get('category', 'unknown')}")
            print(f"Component: {analysis.get('component', 'none')}")
            print(f"Priority Score: {analysis.get('priority_score', 'unknown')}/10")
            print(f"Confidence: {analysis.get('confidence', 'unknown')}")
            
            # Print key phrases
            key_phrases = sentiment.get("key_phrases", [])
            if key_phrases:
                print("Key Phrases:")
                for phrase in key_phrases:
                    print(f"  - {phrase}")
            
            print(f"{'='*80}\n")
        
        print("\nEnhanced Sentiment Analysis Demo")
        print("===============================")
        
        # Check if API key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY environment variable is not set.")
            print("The analysis will fail unless you set this environment variable.")
            return
        
        for i, sample in enumerate(SAMPLE_TICKETS, 1):
            title = sample["title"]
            content = sample["content"]
            
            print(f"Processing sample {i}/{len(SAMPLE_TICKETS)}: {title}")
            analysis = enhanced_analyze_ticket_content(content)
            display_analysis_results(title, analysis)
        
        print("Sentiment analysis demo complete!")
        
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you're running this script from the project root directory.")

def demo_cache_invalidation():
    """Run a demonstration of cache invalidation functionality."""
    try:
        from src.modules.zendesk_client import ZendeskClient
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        print("\nCache Invalidation Demo")
        print("======================")
        
        # Create a Zendesk client (which initializes the cache)
        client = ZendeskClient()
        
        # First fetch will be a cache miss
        print("First fetch (cache miss)...")
        start_time = time.time()
        views_first = client.list_all_views()
        first_duration = time.time() - start_time
        print(f"First fetch took {first_duration:.2f} seconds")
        
        # Second fetch should be a cache hit
        print("Second fetch (should be cache hit)...")
        start_time = time.time()
        views_second = client.list_all_views()
        second_duration = time.time() - start_time
        print(f"Second fetch took {second_duration:.2f} seconds")
        
        # Now invalidate the views cache
        print("Invalidating the views cache...")
        client.cache.invalidate_views()
        
        # Get cache stats to confirm views cache is empty
        stats_before = client.cache.get_stats()
        print(f"Cache statistics after invalidation: {stats_before}")
        
        # Third fetch should be a cache miss again
        print("Third fetch after invalidation (should be cache miss)...")
        start_time = time.time()
        views_third = client.list_all_views()
        third_duration = time.time() - start_time
        print(f"Third fetch took {third_duration:.2f} seconds")
        
        # Get cache stats to confirm views cache is populated again
        stats_after = client.cache.get_stats()
        print(f"Cache statistics after re-fetch: {stats_after}")
        
        # Verify expected behavior
        success = True
        
        # Check that second fetch was from cache (fast)
        if second_duration > 0.1:  # Generous threshold for cache hit
            print(f"WARNING: Second fetch took {second_duration:.2f} seconds - cache hit should be faster")
            success = False
        
        # Check that third fetch was slow (cache miss after invalidation)
        if third_duration < 0.1:  # Very unlikely to be this fast for real API call
            print(f"WARNING: Third fetch too fast after cache invalidation: {third_duration:.2f} seconds")
            success = False
        
        # Check that views cache was empty after invalidation
        if stats_before['views_cache']['size'] != 0:
            print(f"WARNING: Views cache not empty after invalidation: {stats_before['views_cache']['size']} items")
            success = False
        
        # Check that views cache was populated after third fetch
        if stats_after['views_cache']['size'] == 0:
            print("WARNING: Views cache still empty after third fetch")
            success = False
        
        if success:
            print("Cache invalidation demo PASSED ✅")
        else:
            print("Cache invalidation demo had issues ❌")
            
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you're running this script from the project root directory.")

def demo_performance():
    """Run a demonstration of the performance optimizations."""
    try:
        from src.modules.zendesk_client import ZendeskClient
        from src.modules.ai_analyzer import AIAnalyzer
        from src.modules.batch_processor import BatchProcessor
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        print("\nPerformance Optimization Demo")
        print("===========================")
        
        # Create clients
        zendesk_client = ZendeskClient()
        
        # Create an analyzer with custom batch settings for testing
        ai_analyzer = AIAnalyzer()
        ai_analyzer.batch_processor = BatchProcessor(
            max_workers=3,
            batch_size=5,
            show_progress=True
        )
        
        # Fetch some test tickets by status
        print("Fetching tickets with status 'open' for testing")
        tickets = zendesk_client.fetch_tickets(status="open", limit=5)
        
        if not tickets:
            print("No open tickets found, trying 'pending' status")
            tickets = zendesk_client.fetch_tickets(status="pending", limit=5)
        
        if not tickets:
            print("No pending tickets found, trying 'all' status")
            tickets = zendesk_client.fetch_tickets(status="all", limit=5)
        
        print(f"Fetched {len(tickets)} tickets for testing")
        
        if not tickets:
            print("No tickets found for testing")
            return
        
        # Sequential processing
        print("Testing sequential processing...")
        start_time = time.time()
        sequential_results = []
        for ticket in tickets:
            analysis = ai_analyzer.analyze_ticket(
                ticket_id=ticket.id,
                subject=ticket.subject or "",
                description=ticket.description or "",
                use_claude=True
            )
            sequential_results.append(analysis)
        sequential_duration = time.time() - start_time
        print(f"Sequential processing took {sequential_duration:.2f} seconds for {len(tickets)} tickets")
        
        # Batch processing
        print(f"Testing batch processing with 3 workers and batch size 5...")
        start_time = time.time()
        batch_results = ai_analyzer.analyze_tickets_batch(tickets, use_claude=True)
        batch_duration = time.time() - start_time
        print(f"Batch processing took {batch_duration:.2f} seconds for {len(tickets)} tickets")
        
        # Calculate the improvement
        if sequential_duration > 0 and batch_duration > 0:
            improvement = (sequential_duration - batch_duration) / sequential_duration * 100
            speedup = sequential_duration / batch_duration
            print(f"Batch processing improved performance by {improvement:.2f}% (speedup factor: {speedup:.2f}x)")
        
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you're running this script from the project root directory.")

def demo_workflow():
    """Run a demonstration of the complete workflow with caching."""
    try:
        from src.modules.zendesk_client import ZendeskClient
        from src.modules.ai_analyzer import AIAnalyzer
        from src.modules.batch_processor import BatchProcessor
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        print("\nWorkflow Integration Demo")
        print("=======================")
        
        # Create components
        client = ZendeskClient()
        ai_analyzer = AIAnalyzer()
        
        # Set up test parameters
        status = "open"  # Fetch open tickets
        limit = 3  # Limit to 3 tickets (to keep the demo reasonable)
        
        # Create an output file to log test results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_file = f"workflow_demo_{timestamp}.txt"
        
        with open(output_file, "w") as f:
            f.write(f"WORKFLOW INTEGRATION DEMO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            
            # Workflow #1: First Run (Cold Cache)
            print("WORKFLOW #1: COLD CACHE")
            f.write("WORKFLOW #1: COLD CACHE\n")
            f.write("-"*20 + "\n\n")
            
            # Record start time
            start_time = time.time()
            
            # Step 1: Fetch tickets (should be cache miss)
            print("Step 1: Fetching Tickets")
            f.write("Step 1: Fetching Tickets\n")
            step_start = time.time()
            tickets = client.fetch_tickets(status=status, limit=limit)
            step_duration = time.time() - step_start
            print(f"- Fetched {len(tickets)} tickets in {step_duration:.2f} seconds")
            f.write(f"- Fetched {len(tickets)} tickets in {step_duration:.2f} seconds\n")
            
            # Step 2: Analyze tickets using batch processing
            print("Step 2: Analyzing Tickets with Batch Processing")
            f.write("\nStep 2: Analyzing Tickets with Batch Processing\n")
            step_start = time.time()
            analyses = ai_analyzer.analyze_tickets_batch(tickets, use_claude=True)
            step_duration = time.time() - step_start
            print(f"- Analyzed {len(analyses)} tickets in {step_duration:.2f} seconds")
            f.write(f"- Analyzed {len(analyses)} tickets in {step_duration:.2f} seconds\n")
            
            # Record total time for first workflow
            total_duration_first = time.time() - start_time
            print(f"Total Workflow #1 Duration: {total_duration_first:.2f} seconds")
            f.write(f"\nTotal Workflow #1 Duration: {total_duration_first:.2f} seconds\n\n")
            
            # Workflow #2: Second Run (Warm Cache)
            print("\nWORKFLOW #2: WARM CACHE")
            f.write("WORKFLOW #2: WARM CACHE\n")
            f.write("-"*20 + "\n\n")
            
            # Record start time
            start_time = time.time()
            
            # Step 1: Fetch tickets again (should be cache hit)
            print("Step 1: Fetching Tickets Again")
            f.write("Step 1: Fetching Tickets Again\n")
            step_start = time.time()
            tickets_again = client.fetch_tickets(status=status, limit=limit)
            step_duration = time.time() - step_start
            print(f"- Fetched {len(tickets_again)} tickets in {step_duration:.2f} seconds")
            f.write(f"- Fetched {len(tickets_again)} tickets in {step_duration:.2f} seconds\n")
            
            # Step 2: Analyze tickets using batch processing
            print("Step 2: Analyzing Tickets with Batch Processing")
            f.write("\nStep 2: Analyzing Tickets with Batch Processing\n")
            step_start = time.time()
            analyses_again = ai_analyzer.analyze_tickets_batch(tickets_again, use_claude=True)
            step_duration = time.time() - step_start
            print(f"- Analyzed {len(analyses_again)} tickets in {step_duration:.2f} seconds")
            f.write(f"- Analyzed {len(analyses_again)} tickets in {step_duration:.2f} seconds\n")
            
            # Record total time for second workflow
            total_duration_second = time.time() - start_time
            print(f"Total Workflow #2 Duration: {total_duration_second:.2f} seconds")
            f.write(f"\nTotal Workflow #2 Duration: {total_duration_second:.2f} seconds\n\n")
            
            # Performance Comparison
            print("\nPERFORMANCE COMPARISON")
            f.write("PERFORMANCE COMPARISON\n")
            f.write("-"*20 + "\n\n")
            
            # Check cache hit metrics
            cache_stats = client.cache.get_stats()
            print(f"Cache Statistics: {cache_stats}")
            f.write(f"Cache Statistics: {cache_stats}\n\n")
            
            # Compare ticket fetch times
            if step_duration < 0.1:
                print("SUCCESS: Ticket fetch time improved significantly with cache")
                f.write("SUCCESS: Ticket fetch time improved significantly with cache\n")
            else:
                print("ISSUE: Ticket fetch not benefiting from cache as expected")
                f.write("ISSUE: Ticket fetch not benefiting from cache as expected\n")
            
            # Compare overall workflow times
            if total_duration_second < total_duration_first:
                improvement = ((total_duration_first - total_duration_second) / total_duration_first) * 100
                print(f"SUCCESS: Overall workflow improved by {improvement:.2f}%")
                f.write(f"SUCCESS: Overall workflow improved by {improvement:.2f}%\n")
            else:
                print("ISSUE: No overall workflow improvement detected")
                f.write("ISSUE: No overall workflow improvement detected\n")
        
        print(f"Workflow integration demo completed. Results saved to {output_file}")
        
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you're running this script from the project root directory.")

def main():
    """Main function to run the demos."""
    parser = argparse.ArgumentParser(description="Run Zendesk AI Integration demos")
    parser.add_argument(
        "--demo", 
        choices=["ai", "sentiment", "cache", "performance", "workflow", "all"], 
        default="all",
        help="Which demo to run (ai, sentiment, cache, performance, workflow, or all)"
    )
    
    args = parser.parse_args()
    
    if args.demo in ["ai", "all"]:
        demo_ai_service()
        
    if args.demo in ["sentiment", "all"]:
        demo_sentiment_analysis()
        
    if args.demo in ["cache", "all"]:
        demo_cache_invalidation()
        
    if args.demo in ["performance", "all"]:
        demo_performance()
        
    if args.demo in ["workflow", "all"]:
        demo_workflow()
    
    print("\nAll demos completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
