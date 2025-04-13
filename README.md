# Zendesk AI Integration

An intelligent support system that enhances Zendesk support using AI analysis to improve ticket categorization, prioritization, and reporting.

## Overview

The Zendesk AI Integration tool uses artificial intelligence to analyze support tickets in Zendesk, providing:

- **Sentiment Analysis**: Detect customer sentiment (positive, neutral, negative)
- **Ticket Categorization**: Automatically categorize tickets by issue type
- **Priority Scoring**: Generate priority scores based on sentiment, urgency, and business impact
- **Hardware Component Detection**: Identify hardware components mentioned in tickets
- **Advanced Reporting**: Generate comprehensive reports with actionable insights
- **Real-time Processing**: Process tickets as they arrive using webhooks
- **Scheduled Analysis**: Run batch analyses on a regular schedule

## Features

### AI-Powered Analysis

- Uses Claude and OpenAI models for accurate analysis
- Detects customer sentiment with nuanced categorization
- Identifies priority based on several factors
- Recognizes hardware components mentioned in tickets
- Detects business impact indicators

### Comprehensive Reporting

- Standard and enhanced sentiment reports
- Hardware component reports
- Pending ticket reports
- Multi-view comparative reports
- Time-based trend analysis
- Executive summaries with actionable insights

### Integration Capabilities

- Webhook server for real-time ticket processing
- Scheduled tasks for regular reporting
- Comments and tags to enhance Zendesk workflow
- Multi-view support for organizational needs

### User-Friendly Interfaces

- Command-line interface for all operations
- Interactive menu system for easy navigation
- Hierarchical view organization
- Text, JSON, HTML, CSV export options

## Clean Architecture

The application is built using Clean Architecture principles, organized into the following layers:

### Domain Layer (`src/domain`)

- **Entities**: Core business objects (`Ticket`, `TicketAnalysis`)
- **Value Objects**: Immutable objects (`SentimentPolarity`, `TicketCategory`, `HardwareComponent`)
- **Interfaces**: Abstract definitions for services and repositories
- **Exceptions**: Domain-specific exceptions

### Application Layer (`src/application`)

- **Use Cases**: Orchestration of business operations
- **Services**: Implementation of complex business logic
- **DTOs**: Data transfer objects for communication between layers

### Infrastructure Layer (`src/infrastructure`)

- **Repositories**: Data access implementations for MongoDB and Zendesk
- **External Services**: Integrations with Claude and OpenAI
- **Utils**: Technical utilities like configuration and dependency injection

### Presentation Layer (`src/presentation`)

- **CLI**: Command-line interface and commands
- **Webhook**: Webhook handling for real-time events
- **Reporters**: Formatting and presentation of reports

### Benefits of Clean Architecture

- **Separation of Concerns**: Domain logic is isolated from infrastructure
- **Testability**: Components can be tested independently
- **Flexibility**: Easy to change infrastructure without affecting business logic
- **Maintainability**: Well-organized code with clear responsibilities

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Zendesk account with API access

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/zendesk-ai-integration.git
   cd zendesk-ai-integration
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Zendesk API credentials and other settings
   ```

5. Set up MongoDB:
   ```bash
   python install_mongodb.py
   ```

## Usage

### Command-Line Interface

The command-line interface provides access to all features:

```bash
python -m src.main [COMMAND] [OPTIONS]
```

See [Command Reference](COMMAND_REFERENCE.md) for detailed usage information.

### Basic Operations

#### Analyzing Tickets

```bash
# Analyze a specific ticket
python -m src.main analyze --ticket-id 12345

# Analyze all tickets in a view
python -m src.main analyze --view-id 67890
```

#### Generating Reports

```bash
# Generate a standard sentiment report
python -m src.main report --type sentiment --days 7

# Generate an enhanced sentiment report
python -m src.main report --type enhanced-sentiment --days 7

# Generate a hardware component report
python -m src.main report --type hardware --view-id 12345

# Generate a multi-view comparative report
python -m src.main report --type multi-view --view-ids 12345,67890
```

#### Using the Interactive Menu

```bash
python -m src.main interactive
```

#### Running the Webhook Server

```bash
python -m src.main webhook --start --host 0.0.0.0 --port 8000
```

#### Setting Up Scheduled Tasks

```bash
python -m src.main schedule --add --type analyze --view-id 12345 --interval 60
```

## Configuration

The application uses environment variables for configuration:

- `ZENDESK_EMAIL`: Your Zendesk email address
- `ZENDESK_API_TOKEN`: Your Zendesk API token
- `ZENDESK_SUBDOMAIN`: Your Zendesk subdomain
- `MONGODB_URI`: MongoDB connection string
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_API_KEY`: Anthropic Claude API key

## Development

### Project Structure

```
zendesk-ai-integration/
├── docs/                 # Documentation
├── reports/              # Generated reports
├── src/                  # Source code
│   ├── domain/           # Domain layer
│   │   ├── entities/     # Domain entities
│   │   ├── interfaces/   # Interfaces for repositories and services
│   │   └── value_objects/# Value objects
│   ├── application/      # Application layer
│   │   ├── dtos/         # Data Transfer Objects
│   │   ├── services/     # Application services
│   │   └── use_cases/    # Use cases
│   ├── infrastructure/   # Infrastructure layer
│   │   ├── external_services/ # External APIs
│   │   ├── repositories/ # Repository implementations
│   │   └── utils/        # Utility functions
│   └── presentation/     # Presentation layer
│       ├── cli/          # Command-line interface
│       │   ├── commands/ # Command implementations
│       │   └── command_handler.py # Command handling
│       ├── reporters/    # Report formatters
│       └── webhook/      # Webhook server
└── tests/                # Tests
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── functional/       # Functional tests
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific tests
python -m unittest tests/unit/test_module.py

# Run tests with enhanced reports
python run_enhanced_tests.py
```

### Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

See [Contributing Guide](CONTRIBUTING.md) for more details.

## Documentation

- [Command Reference](COMMAND_REFERENCE.md): Detailed CLI command documentation
- [Reporting Features](REPORTING.md): Overview of all reporting capabilities
- [Enhanced Reports](ENHANCED_REPORTS.md): Details on enhanced reporting features
- [Multi-View Reporting](MULTI_VIEW_REPORTING.md): Information on multi-view comparative reports
- [Architecture Documentation](src/ARCHITECTURE.md): Detailed architecture overview
- [Testing Guide](docs/TESTING_GUIDE.md): Testing approach and examples

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Anthropic for Claude API
- OpenAI for GPT API
- Zendesk for their API
