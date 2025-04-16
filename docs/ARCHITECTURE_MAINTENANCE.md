# Clean Architecture Maintenance Guide

This document provides guidelines for maintaining the clean architecture of the Zendesk AI Integration application and adding new features in a way that preserves architectural integrity.

## Architecture Principles to Preserve

1. **Dependency Rule**: Dependencies must only point inward, never outward
2. **Independent Domain Layer**: The domain layer must not depend on any external frameworks or libraries
3. **Interface Segregation**: Keep interfaces focused on specific responsibilities
4. **Explicit Dependencies**: Components should declare their dependencies explicitly
5. **Testability**: All components should be testable in isolation

## Adding New Features

When adding new features to the application, follow these steps to maintain architectural integrity:

### Step 1: Define Domain Concepts

1. Start by defining any new domain concepts as entities or value objects in the domain layer
2. Define interfaces for any new repository or service requirements
3. Ensure the domain layer remains completely independent of external frameworks

Example:
```python
# Domain entity
class CustomReport:
    def __init__(self, id, name, criteria, created_at):
        self.id = id
        self.name = name
        self.criteria = criteria
        self.created_at = created_at
    
    def is_valid(self):
        # Domain logic
        return bool(self.name and self.criteria)
    
    def applies_to_ticket(self, ticket):
        # Domain logic
        # ...

# Domain interface
class CustomReportRepository:
    @abstractmethod
    def save(self, report):
        pass
    
    @abstractmethod
    def get_by_id(self, report_id):
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria):
        pass
```

### Step 2: Implement Use Cases

1. Define use cases in the application layer that orchestrate the domain logic
2. Use DTOs to communicate between layers
3. Keep use cases focused on a single responsibility

Example:
```python
class GenerateCustomReportUseCase:
    def __init__(self, ticket_repository, report_repository, report_formatter):
        self.ticket_repository = ticket_repository
        self.report_repository = report_repository
        self.report_formatter = report_formatter
    
    def execute(self, report_criteria, output_format):
        # Use case logic
        tickets = self.ticket_repository.find_by_criteria(report_criteria)
        report = CustomReport(
            id=str(uuid.uuid4()),
            name=report_criteria.get('name', 'Unnamed Report'),
            criteria=report_criteria,
            created_at=datetime.utcnow()
        )
        
        if not report.is_valid():
            return {"success": False, "error": "Invalid report criteria"}
        
        self.report_repository.save(report)
        
        # Format the report
        formatted_report = self.report_formatter.format(
            tickets, report, output_format
        )
        
        return {
            "success": True,
            "report_id": report.id,
            "report": formatted_report
        }
```

### Step 3: Implement Infrastructure

1. Create concrete implementations of the domain interfaces in the infrastructure layer
2. Inject external dependencies (frameworks, libraries) only in the infrastructure layer
3. Handle technical concerns like database connections, API calls, caching, etc.

Example:
```python
class MongoDBCustomReportRepository(CustomReportRepository):
    def __init__(self, mongodb_client):
        self.client = mongodb_client
        self.db = self.client.get_database("zendesk_analytics")
        self.collection = self.db.get_collection("custom_reports")
    
    def save(self, report):
        report_dict = {
            "id": report.id,
            "name": report.name,
            "criteria": report.criteria,
            "created_at": report.created_at
        }
        self.collection.replace_one(
            {"id": report.id}, report_dict, upsert=True
        )
        return report.id
    
    def get_by_id(self, report_id):
        result = self.collection.find_one({"id": report_id})
        if not result:
            return None
        
        return CustomReport(
            id=result["id"],
            name=result["name"],
            criteria=result["criteria"],
            created_at=result["created_at"]
        )
    
    def find_by_criteria(self, criteria):
        # Implementation details...
```

### Step 4: Implement Presentation

1. Add presentation components (CLI commands, API endpoints, etc.) that use the application use cases
2. Keep presentation logic thin, delegating business logic to use cases
3. Format responses appropriately for the presentation context

Example:
```python
class GenerateCustomReportCommand(Command):
    name = "generate-custom-report"
    description = "Generate a custom report based on criteria"
    
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--name", help="Report name")
        parser.add_argument("--format", choices=["text", "json", "html"], default="text")
        parser.add_argument("--days", type=int, help="Days to include")
        # Other arguments...
    
    def __init__(self, args, service_provider):
        self.args = args
        self.use_case = service_provider.get(GenerateCustomReportUseCase)
    
    def execute(self):
        # Convert command line args to criteria
        criteria = {
            "name": self.args.get("name"),
            "days": self.args.get("days"),
            # Other criteria...
        }
        
        # Execute the use case
        result = self.use_case.execute(
            report_criteria=criteria,
            output_format=self.args.get("format", "text")
        )
        
        # Handle the result
        if result["success"]:
            if self.args.get("output"):
                # Save to file
                with open(self.args.get("output"), "w") as f:
                    f.write(result["report"])
                return {
                    "success": True,
                    "message": f"Report saved to {self.args.get('output')}"
                }
            else:
                # Return for display
                return {
                    "success": True,
                    "report": result["report"]
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }
```

## Common Architecture Violations to Avoid

### 1. Bypassing Layer Boundaries

❌ **Bad**: Directly accessing repository implementation from presentation layer
```python
# In a CLI command
def execute(self):
    mongodb_repo = MongoDBRepository()  # Direct dependency on implementation
    tickets = mongodb_repo.find_all()
```

✅ **Good**: Inject dependencies and respect layer boundaries
```python
# In a CLI command
def __init__(self, args, service_provider):
    self.args = args
    self.use_case = service_provider.get(AnalyzeTicketsUseCase)  # Get via DI
    
def execute(self):
    result = self.use_case.execute(self.args)  # Use application layer
```

### 2. Domain Logic in Infrastructure Layer

❌ **Bad**: Business rules in repository implementation
```python
class ZendeskTicketRepository:
    def get_high_priority_tickets(self):
        tickets = self.client.tickets()
        # Business logic shouldn't be here
        return [t for t in tickets if t.urgency_level > 3 or "urgent" in t.tags]
```

✅ **Good**: Keep domain logic in domain entities/services
```python
# In domain layer
class Ticket:
    def is_high_priority(self):
        return self.urgency_level > 3 or "urgent" in self.tags

# In repository implementation
class ZendeskTicketRepository:
    def get_tickets(self, status=None):
        # Only data access logic here
        return [self._to_entity(t) for t in self.client.tickets(status=status)]
```

### 3. Multiple Responsibilities in Use Cases

❌ **Bad**: Use case that does too many things
```python
class TicketProcessingUseCase:
    def execute(self, ticket_id):
        # Fetching data
        ticket = self.repository.get_ticket(ticket_id)
        
        # Analysis logic
        sentiment = self.ai_service.analyze_sentiment(ticket.content)
        
        # Database updates
        self.repository.update_ticket(ticket_id, {"sentiment": sentiment})
        
        # Email notifications
        self.email_service.send_notification(ticket)
        
        # Report generation
        report = self.report_generator.generate(ticket)
        
        # File operations
        with open(f"report_{ticket_id}.txt", "w") as f:
            f.write(report)
```

✅ **Good**: Split into focused use cases
```python
class AnalyzeTicketUseCase:
    def execute(self, ticket_id):
        ticket = self.repository.get_ticket(ticket_id)
        sentiment = self.ai_service.analyze_sentiment(ticket.content)
        self.repository.update_ticket(ticket_id, {"sentiment": sentiment})
        return {"ticket_id": ticket_id, "sentiment": sentiment}

class NotifyAboutTicketUseCase:
    def execute(self, ticket_id):
        ticket = self.repository.get_ticket(ticket_id)
        self.notification_service.send_notification(ticket)
        return {"ticket_id": ticket_id, "notified": True}
```

### 4. External Dependencies in Domain Layer

❌ **Bad**: Using external libraries in domain entities
```python
# In domain entity
from mongoengine import Document, StringField

class Ticket(Document):  # Directly using MongoDB ORM
    id = StringField(primary_key=True)
    subject = StringField()
    description = StringField()
```

✅ **Good**: Keep domain entities independent
```python
# In domain entity
class Ticket:  # Pure Python with no external dependencies
    def __init__(self, id, subject, description):
        self.id = id
        self.subject = subject
        self.description = description
```

## How to Add a New Feature: Complete Example

Here's a complete example of adding a new feature while maintaining clean architecture:

### 1. New Feature: Custom Alert System

Let's build a feature that allows users to define custom alerts based on ticket characteristics.

#### Step 1: Define Domain Concepts

```python
# domain/entities/alert_rule.py
class AlertRule:
    def __init__(self, id, name, conditions, action, created_by=None, created_at=None):
        self.id = id
        self.name = name
        self.conditions = conditions
        self.action = action
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()
    
    def matches_ticket(self, ticket):
        """Check if the ticket matches this alert rule's conditions"""
        for condition in self.conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field == "subject":
                ticket_value = ticket.subject
            elif field == "priority":
                ticket_value = ticket.priority
            elif field == "sentiment":
                ticket_value = ticket.sentiment.polarity if ticket.sentiment else None
            else:
                continue
            
            if operator == "equals" and ticket_value != value:
                return False
            elif operator == "contains" and value not in ticket_value:
                return False
            elif operator == "greater_than" and not (ticket_value and ticket_value > value):
                return False
            # other operators...
        
        return True

# domain/interfaces/repository_interfaces.py
class AlertRuleRepository(ABC):
    @abstractmethod
    def save(self, alert_rule):
        pass
    
    @abstractmethod
    def get_by_id(self, rule_id):
        pass
    
    @abstractmethod
    def get_all(self):
        pass
    
    @abstractmethod
    def delete(self, rule_id):
        pass
```

#### Step 2: Implement Use Cases

```python
# application/use_cases/create_alert_rule_use_case.py
class CreateAlertRuleUseCase:
    def __init__(self, alert_rule_repository):
        self.repository = alert_rule_repository
    
    def execute(self, name, conditions, action, created_by=None):
        # Validate input
        if not name or not conditions or not action:
            return {"success": False, "error": "Missing required fields"}
        
        # Create the rule
        rule = AlertRule(
            id=str(uuid.uuid4()),
            name=name,
            conditions=conditions,
            action=action,
            created_by=created_by
        )
        
        # Save the rule
        rule_id = self.repository.save(rule)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": f"Alert rule '{name}' created successfully"
        }

# application/use_cases/check_ticket_alerts_use_case.py
class CheckTicketAlertsUseCase:
    def __init__(self, ticket_repository, alert_rule_repository, notification_service):
        self.ticket_repository = ticket_repository
        self.alert_rule_repository = alert_rule_repository
        self.notification_service = notification_service
    
    def execute(self, ticket_id):
        # Get the ticket
        ticket = self.ticket_repository.get_ticket(ticket_id)
        if not ticket:
            return {"success": False, "error": f"Ticket {ticket_id} not found"}
        
        # Get all alert rules
        rules = self.alert_rule_repository.get_all()
        
        # Check which rules match
        matching_rules = []
        for rule in rules:
            if rule.matches_ticket(ticket):
                matching_rules.append(rule)
                
                # Execute the action
                if rule.action["type"] == "notification":
                    self.notification_service.send_notification(
                        recipient=rule.action["recipient"],
                        subject=f"Alert: {rule.name}",
                        body=f"Ticket {ticket_id} matches alert rule '{rule.name}'"
                    )
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "matching_rules": [r.id for r in matching_rules],
            "actions_executed": len(matching_rules)
        }
```

#### Step 3: Implement Infrastructure

```python
# infrastructure/repositories/mongodb_alert_repository.py
class MongoDBAlertRuleRepository(AlertRuleRepository):
    def __init__(self, mongodb_client):
        self.client = mongodb_client
        self.db = self.client.get_database("zendesk_analytics")
        self.collection = self.db.get_collection("alert_rules")
    
    def save(self, alert_rule):
        rule_dict = {
            "id": alert_rule.id,
            "name": alert_rule.name,
            "conditions": alert_rule.conditions,
            "action": alert_rule.action,
            "created_by": alert_rule.created_by,
            "created_at": alert_rule.created_at
        }
        
        self.collection.replace_one(
            {"id": alert_rule.id}, rule_dict, upsert=True
        )
        
        return alert_rule.id
    
    def get_by_id(self, rule_id):
        result = self.collection.find_one({"id": rule_id})
        if not result:
            return None
        
        return AlertRule(
            id=result["id"],
            name=result["name"],
            conditions=result["conditions"],
            action=result["action"],
            created_by=result["created_by"],
            created_at=result["created_at"]
        )
    
    def get_all(self):
        results = self.collection.find()
        rules = []
        
        for result in results:
            rules.append(AlertRule(
                id=result["id"],
                name=result["name"],
                conditions=result["conditions"],
                action=result["action"],
                created_by=result["created_by"],
                created_at=result["created_at"]
            ))
        
        return rules
    
    def delete(self, rule_id):
        result = self.collection.delete_one({"id": rule_id})
        return result.deleted_count > 0

# infrastructure/services/email_notification_service.py
class EmailNotificationService:
    def __init__(self, smtp_config):
        self.smtp_host = smtp_config.get("host", "localhost")
        self.smtp_port = smtp_config.get("port", 25)
        self.sender = smtp_config.get("sender", "noreply@example.com")
    
    def send_notification(self, recipient, subject, body):
        import smtplib
        from email.message import EmailMessage
        
        message = EmailMessage()
        message.set_content(body)
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = recipient
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.send_message(message)
            
        return True
```

#### Step 4: Implement Presentation

```python
# presentation/cli/commands/create_alert_command.py
class CreateAlertCommand(Command):
    name = "create-alert"
    description = "Create a new alert rule"
    
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--name", required=True, help="Alert name")
        parser.add_argument("--field", required=True, help="Field to check")
        parser.add_argument("--operator", required=True, 
                           choices=["equals", "contains", "greater_than"], 
                           help="Comparison operator")
        parser.add_argument("--value", required=True, help="Value to compare against")
        parser.add_argument("--notify", help="Email to notify")
    
    def __init__(self, args, service_provider):
        self.args = args
        self.use_case = service_provider.get(CreateAlertRuleUseCase)
    
    def execute(self):
        # Convert arguments to conditions and action
        conditions = [{
            "field": self.args.get("field"),
            "operator": self.args.get("operator"),
            "value": self.args.get("value")
        }]
        
        action = {
            "type": "notification",
            "recipient": self.args.get("notify")
        }
        
        # Execute use case
        result = self.use_case.execute(
            name=self.args.get("name"),
            conditions=conditions,
            action=action
        )
        
        return result
```

#### Step 5: Register Dependencies

```python
# infrastructure/service_provider.py
class ServiceProvider:
    def __init__(self, config_file=None):
        self.container = DependencyContainer()
        self._register_dependencies(config_file)
    
    def _register_dependencies(self, config_file):
        # Existing registrations...
        
        # Configure MongoDB client
        mongodb_client = self._create_mongodb_client()
        
        # Register repositories
        self.container.register_instance(
            MongoDBRepository, MongoDBRepository(mongodb_client)
        )
        self.container.register_instance(
            AlertRuleRepository, 
            MongoDBAlertRuleRepository(mongodb_client)
        )
        
        # Register services
        smtp_config = self._get_smtp_config()
        self.container.register_instance(
            NotificationService,
            EmailNotificationService(smtp_config)
        )
        
        # Register use cases
        self.container.register_class(
            CreateAlertRuleUseCase,
            CreateAlertRuleUseCase
        )
        self.container.register_class(
            CheckTicketAlertsUseCase,
            CheckTicketAlertsUseCase
        )
    
    def get(self, interface_class):
        return self.container.resolve(interface_class)
```

## Common Refactoring Techniques

When refactoring existing code to comply with clean architecture, use these techniques:

### 1. Extract Domain Model

Separate pure domain logic from infrastructure concerns:

```python
# Before: Mixed business and data access logic
class TicketManager:
    def __init__(self, zendesk_client):
        self.client = zendesk_client
    
    def get_high_priority_tickets(self):
        tickets = self.client.tickets()
        return [t for t in tickets if t.priority_score > 7]
```

```python
# After: Separated domain and infrastructure concerns

# Domain layer
class Ticket:
    def __init__(self, id, subject, priority_score):
        self.id = id
        self.subject = subject
        self.priority_score = priority_score
    
    def is_high_priority(self):
        return self.priority_score > 7

# Infrastructure layer
class ZendeskTicketRepository:
    def __init__(self, zendesk_client):
        self.client = zendesk_client
    
    def get_tickets(self):
        zendesk_tickets = self.client.tickets()
        return [
            Ticket(
                id=t.id,
                subject=t.subject,
                priority_score=t.priority_score
            ) 
            for t in zendesk_tickets
        ]
        
# Application layer
class TicketService:
    def __init__(self, ticket_repository):
        self.repository = ticket_repository
    
    def get_high_priority_tickets(self):
        tickets = self.repository.get_tickets()
        return [t for t in tickets if t.is_high_priority()]
```

### 2. Introduce Interfaces

Add interfaces before implementations to enforce the dependency rule:

```python
# Before: Direct dependency on implementation
class TicketAnalyzer:
    def __init__(self):
        self.repository = MongoDBRepository()  # Direct dependency
    
    def analyze(self, ticket_id):
        ticket = self.repository.get_ticket(ticket_id)
        # Analysis logic...
```

```python
# After: Using interfaces

# Domain layer
class TicketRepository(ABC):
    @abstractmethod
    def get_ticket(self, ticket_id):
        pass

# Infrastructure layer
class MongoDBTicketRepository(TicketRepository):
    def get_ticket(self, ticket_id):
        # Implementation...

# Application layer
class TicketAnalyzer:
    def __init__(self, ticket_repository: TicketRepository):
        self.repository = ticket_repository  # Dependency on interface
    
    def analyze(self, ticket_id):
        ticket = self.repository.get_ticket(ticket_id)
        # Analysis logic...
```

### 3. Use Command Pattern for CLI

Refactor CLI code to use the command pattern:

```python
# Before: Monolithic CLI handling
def main():
    args = parse_args()
    
    if args.command == "analyze":
        # Analyze ticket logic...
    elif args.command == "report":
        # Generate report logic...
    elif args.command == "webhook":
        # Start webhook server...
    # More commands...
```

```python
# After: Command pattern

# Base command
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

# Specific commands
class AnalyzeCommand(Command):
    def __init__(self, args, service_provider):
        self.args = args
        self.use_case = service_provider.get(AnalyzeTicketUseCase)
    
    def execute(self):
        return self.use_case.execute(self.args.ticket_id)

class ReportCommand(Command):
    # Implementation...

# Command handler
class CommandHandler:
    def __init__(self, service_provider):
        self.service_provider = service_provider
        self.commands = {}
    
    def register_command(self, name, command_class):
        self.commands[name] = command_class
    
    def execute(self, args):
        command_class = self.commands.get(args.command)
        if not command_class:
            return {"success": False, "error": "Unknown command"}
        
        command = command_class(args, self.service_provider)
        return command.execute()

# Main
def main():
    args = parse_args()
    service_provider = ServiceProvider()
    
    handler = CommandHandler(service_provider)
    handler.register_command("analyze", AnalyzeCommand)
    handler.register_command("report", ReportCommand)
    # Register more commands...
    
    result = handler.execute(args)
    # Handle result...
```

## Conclusion

Maintaining a clean architecture requires discipline and consistent application of these principles. When implemented correctly, clean architecture provides significant benefits:

1. **Maintainability**: Changes are isolated to specific layers
2. **Testability**: Components can be tested in isolation
3. **Flexibility**: Implementations can be swapped without affecting business logic
4. **Independence**: Business logic is independent of frameworks and external systems

By following the guidelines in this document, you'll ensure that the Zendesk AI Integration application remains maintainable, testable, and extensible as it evolves.
