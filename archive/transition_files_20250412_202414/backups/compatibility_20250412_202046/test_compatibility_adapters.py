"""
Tests for the compatibility adapters.

This module tests that the compatibility adapters correctly implement
the interfaces of the legacy components while using the new implementations.
"""

import unittest
from unittest.mock import MagicMock, patch

# from src.infrastructure.compatibility import (
    ZendeskClient,
    AIAnalyzer,
    DBRepository,
    WebhookServer,
    Scheduler,
    SentimentReporter,
    HardwareReporter,
    PendingReporter,
    ServiceProvider,
    generate_summary_report,
    generate_enhanced_summary_report,
    generate_hardware_report,
    generate_pending_report
)


class TestZendeskClientAdapter(unittest.TestCase):
    """Tests for the ZendeskClientAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_repository = MagicMock()
        self.adapter = ZendeskClient(repository=self.mock_repository)
    
    def test_fetch_tickets(self):
        """Test fetch_tickets method."""
        # Arrange
        self.mock_repository.get_tickets.return_value = ["ticket1", "ticket2"]
        
        # Act
        result = self.adapter.get_tickets(status="open", limit=10)
        
        # Assert
        self.assertEqual(result, ["ticket1", "ticket2"])
        self.mock_repository.get_tickets.assert_called_once_with("open", 10)
    
    def test_fetch_tickets_with_id_filter(self):
        """Test fetch_tickets method with ID filter."""
        # Arrange
        self.mock_repository.get_ticket.return_value = "ticket1"
        
        # Act
        result = self.adapter.get_tickets(filter_by={"id": 123})
        
        # Assert
        self.assertEqual(result, ["ticket1"])
        self.mock_repository.get_ticket.assert_called_once_with(123)
    
    def test_fetch_tickets_from_view(self):
        """Test fetch_tickets_from_view method."""
        # Arrange
        self.mock_repository.get_tickets_from_view.return_value = ["ticket1", "ticket2"]
        
        # Act
        result = self.adapter.get_tickets_from_view(view_id=456, limit=10)
        
        # Assert
        self.assertEqual(result, ["ticket1", "ticket2"])
        self.mock_repository.get_tickets_from_view.assert_called_once_with(456, 10)


class TestAIAnalyzerAdapter(unittest.TestCase):
    """Tests for the AIAnalyzerAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_ticket_analysis_service = MagicMock()
        self.mock_claude_service = MagicMock()
        self.mock_openai_service = MagicMock()
        
        self.adapter = AIAnalyzer(
            ticket_analysis_service=self.mock_ticket_analysis_service,
            claude_service=self.mock_claude_service,
            openai_service=self.mock_openai_service
        )
    
    def test_analyze_ticket_with_openai(self):
        """Test analyze_ticket method with OpenAI."""
        # Arrange
        mock_ticket = MagicMock()
        self.mock_ticket_analysis_service.analyze_ticket.return_value = "analysis_result"
        
        # Act
        result = self.adapter.analyze_ticket(mock_ticket, use_claude=False)
        
        # Assert
        self.assertEqual(result, "analysis_result")
        self.mock_ticket_analysis_service.analyze_ticket.assert_called_once_with(mock_ticket)
        self.assertEqual(self.mock_ticket_analysis_service.ai_service, self.mock_openai_service)
    
    def test_analyze_ticket_with_claude(self):
        """Test analyze_ticket method with Claude."""
        # Arrange
        mock_ticket = MagicMock()
        self.mock_ticket_analysis_service.analyze_ticket.return_value = "analysis_result"
        
        # Act
        result = self.adapter.analyze_ticket(mock_ticket, use_claude=True)
        
        # Assert
        self.assertEqual(result, "analysis_result")
        self.mock_ticket_analysis_service.analyze_ticket.assert_called_once_with(mock_ticket)
        self.assertEqual(self.mock_ticket_analysis_service.ai_service, self.mock_claude_service)
    
    def test_analyze_tickets_batch(self):
        """Test analyze_tickets_batch method."""
        # Arrange
        mock_tickets = [MagicMock(), MagicMock()]
        self.mock_ticket_analysis_service.analyze_tickets_batch.return_value = ["result1", "result2"]
        
        # Act
        result = self.adapter.analyze_tickets_batch(mock_tickets, use_claude=True)
        
        # Assert
        self.assertEqual(result, ["result1", "result2"])
        self.mock_ticket_analysis_service.analyze_tickets_batch.assert_called_once_with(mock_tickets)
        self.assertEqual(self.mock_ticket_analysis_service.ai_service, self.mock_claude_service)


class TestDBRepositoryAdapter(unittest.TestCase):
    """Tests for the DBRepositoryAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_repository = MagicMock()
        self.adapter = DBRepository(repository=self.mock_repository)
    
    def test_save_analysis(self):
        """Test save_analysis method."""
        # Arrange
        mock_analysis = {"ticket_id": 123, "sentiment": "positive"}
        self.mock_repository.save_analysis.return_value = "doc_id"
        
        # Act
        result = self.adapter.save_analysis(mock_analysis)
        
        # Assert
        self.assertEqual(result, "doc_id")
        self.mock_repository.save_analysis.assert_called_once_with(mock_analysis, 3)
    
    def test_get_analysis_by_ticket_id(self):
        """Test get_analysis_by_ticket_id method."""
        # Arrange
        self.mock_repository.get_analysis_by_ticket_id.return_value = {"ticket_id": 123, "sentiment": "positive"}
        
        # Act
        result = self.adapter.get_analysis_by_ticket_id(123)
        
        # Assert
        self.assertEqual(result, {"ticket_id": 123, "sentiment": "positive"})
        self.mock_repository.get_analysis_by_ticket_id.assert_called_once_with(123)
    
    def test_find_analyses_since(self):
        """Test find_analyses_since method."""
        # Arrange
        mock_date = MagicMock()
        self.mock_repository.find_analyses_since.return_value = ["analysis1", "analysis2"]
        
        # Act
        result = self.adapter.find_analyses_since(mock_date)
        
        # Assert
        self.assertEqual(result, ["analysis1", "analysis2"])
        self.mock_repository.find_analyses_since.assert_called_once_with(mock_date)


class TestServiceProviderAdapter(unittest.TestCase):
    """Tests for the ServiceProviderAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_container = MagicMock()
        self.adapter = ServiceProvider(service_container=self.mock_container)
    
    def test_get_zendesk_client(self):
        """Test get_zendesk_client method."""
        # Arrange
        self.mock_container.resolve.return_value = MagicMock()
        
        # Act
        result = self.adapter.get(ZendeskRepository))
        
        # Assert
        self.assertIsInstance(result, ZendeskClient)
        self.mock_container.resolve.assert_called()  # Just verify a call was made, not the exact arguments
    
    def test_get_ai_analyzer(self):
        """Test get_ai_analyzer method."""
        # Arrange
        self.mock_container.resolve.side_effect = lambda name: MagicMock()
        
        # Act
        result = self.adapter.get(TicketAnalysisService))
        
        # Assert
        self.assertIsInstance(result, AIAnalyzer)
    
    def test_get_analyze_ticket_use_case(self):
        """Test get_analyze_ticket_use_case method."""
        # Arrange
        mock_use_case = MagicMock()
        self.mock_container.resolve.return_value = mock_use_case
        
        # Act
        result = self.adapter.get_analyze_ticket_use_case()
        
        # Assert
        self.assertEqual(result, mock_use_case)
        self.mock_container.resolve.assert_called_with('analyze_ticket_use_case')


class TestReportGeneratorAdapter(unittest.TestCase):
    """Tests for the report generator adapter functions."""
    
    @patch('src.infrastructure.compatibility.report_generator_adapter.SentimentReporterAdapter')
    def test_generate_report_use_case.execute(self, mock_reporter_class):
        """Test generate_summary_report function."""
        # Arrange
        mock_reporter = mock_reporter_class.return_value
        mock_reporter.generate_report.return_value = "report_content"
        
        mock_zendesk = MagicMock()
        mock_ai = MagicMock()
        mock_db = MagicMock()
        
        # Act
        result = generate_report_use_case.execute(
            mock_zendesk, mock_ai, mock_db, 
            view_id=123, days=30, format_type="text"
        )
        
        # Assert
        self.assertEqual(result, "report_content")
        mock_reporter.set_services.assert_called_once_with(mock_zendesk, mock_ai, mock_db)
        mock_reporter.generate_report.assert_called_once_with(
            view=123, days=30, enhanced=False, format_type="text"
        )


class TestWebhookServerAdapter(unittest.TestCase):
    """Tests for the WebhookServerAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_webhook_service = MagicMock()
        self.mock_webhook_handler = MagicMock()
        
        self.adapter = WebhookServer(
            webhook_service=self.mock_webhook_service,
            webhook_handler=self.mock_webhook_handler
        )
    
    def test_start(self):
        """Test start method."""
        # Act
        with patch('threading.Thread') as mock_thread:
            result = self.adapter.start(host='127.0.0.1', port=8080, endpoint='/hook')
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(self.adapter._running)
        mock_thread.assert_called()
    
    def test_stop(self):
        """Test stop method."""
        # Arrange
        self.adapter._running = True
        
        # Act
        result = self.adapter.stop()
        
        # Assert
        self.assertTrue(result)
        self.assertFalse(self.adapter._running)
        self.mock_webhook_handler.stop.assert_called_once()


class TestSchedulerAdapter(unittest.TestCase):
    """Tests for the SchedulerAdapter."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_scheduler_service = MagicMock()
        self.adapter = Scheduler(scheduler_service=self.mock_scheduler_service)
    
    def test_add_daily_task(self):
        """Test add_daily_task method."""
        # Arrange
        mock_task = MagicMock()
        self.mock_scheduler_service.schedule_daily_task.return_value = "task_id"
        
        # Act
        result = self.adapter.add_daily_task(mock_task, time_str="12:30")
        
        # Assert
        self.assertEqual(result, "task_id")
        self.mock_scheduler_service.schedule_daily_task.assert_called_once_with(
            mock_task, hour=12, minute=30
        )
    
    def test_run_blocking(self):
        """Test run method with blocking=True."""
        # Act
        self.adapter.run(blocking=True)
        
        # Assert
        self.mock_scheduler_service.start.assert_called_once()
    
    def test_run_non_blocking(self):
        """Test run method with blocking=False."""
        # Act
        with patch('threading.Thread') as mock_thread:
            self.adapter.run(blocking=False)
        
        # Assert
        mock_thread.assert_called()
        mock_thread.return_value.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
