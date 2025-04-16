# Zendesk AI Integration

An intelligent support system that enhances Zendesk support using AI analysis to improve ticket categorization, prioritization, and reporting.

![Zendesk AI Integration Banner](docs/images/zendesk_ai_banner.png)

## Quick Start

Getting started with Zendesk AI Integration is now easier than ever:

1. **Check the [Installation Checklist](docs/INSTALLATION_CHECKLIST.md)** to ensure you have everything needed
2. **Run our easy installer**:
   ```bash
   # Clone the repository
   git clone https://github.com/quanticsoul4772/zendesk-ai-integration.git
   cd zendesk-ai-integration
   
   # Run the easy installer
   # On Windows:
   easy_install.bat
   # On macOS/Linux:
   ./easy_install.sh
   # Alternative for any platform:
   python easy_install.py
   ```
3. **Verify your installation**:
   ```bash
   # On Windows
   run_zendesk_ai.bat --mode listviews
   
   # On macOS/Linux
   ./run_zendesk_ai.sh --mode listviews
   ```

Need help? Check our [Installation Index](docs/INSTALLATION_INDEX.md) for all documentation resources!

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

## Installation

### Simplified Installation

We've made installation easier with:

- [Installation Checklist](docs/INSTALLATION_CHECKLIST.md): Everything you need before starting
- [Simplified Terms Guide](docs/SIMPLIFIED_TERMS.md): Technical terms explained simply
- [Copy-Paste Command Sheet](docs/COPY_PASTE_COMMANDS.md): Ready-to-use commands

For complete installation instructions, see the [Installation Guide](INSTALLATION.md).

### Prerequisites

- Python 3.9 or higher
- MongoDB 4.4 or higher (or use our Docker-based setup option)
- Zendesk account with API access

### Quick Installation Steps

1. Clone the repository and run the easy installer:
   ```bash
   # Clone the repository
   git clone https://github.com/quanticsoul4772/zendesk-ai-integration.git
   cd zendesk-ai-integration
   
   # Run the easy installer (choose one based on your platform)
   easy_install.bat            # Windows
   ./easy_install.sh           # macOS/Linux
   python easy_install.py      # Any platform
   ```

2. Follow the on-screen prompts to configure your installation

3. After installation, verify with:
   ```bash
   run_zendesk_ai.bat --mode listviews  # Windows
   ./run_zendesk_ai.sh --mode listviews  # macOS/Linux
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
python -m src.main analyzeticket 12345

# Analyze all tickets in a view
python -m src.main analyzeticket --view-id 67890 --limit 10
```

#### Generating Reports

```bash
# Generate a standard sentiment report
python -m src.main generatereport --type sentiment --days 7

# Generate an enhanced sentiment report
python -m src.main generatereport --type enhanced-sentiment --days 7

# Generate a hardware component report
python -m src.main generatereport --type hardware --view-id 12345

# Generate a multi-view comparative report
python -m src.main generatereport --type multi-view --view-ids 12345,67890
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

## Development

### Project Structure

```
zendesk-ai-integration/
├── docs/                 # Documentation
├── reports/              # Generated reports
├── src/                  # Source code
│   ├── domain/           # Domain layer
│   ├── application/      # Application layer
│   ├── infrastructure/   # Infrastructure layer
│   └── presentation/     # Presentation layer
└── tests/                # Tests
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

### User Guides
- [Installation Guide](INSTALLATION.md): Complete installation instructions
- [Command Reference](COMMAND_REFERENCE.md): Detailed CLI command documentation
- [Copy-Paste Command Sheet](docs/COPY_PASTE_COMMANDS.md): Ready-to-use commands

### Feature Documentation
- [Reporting Features](REPORTING.md): Overview of all reporting capabilities
- [Enhanced Reports](ENHANCED_REPORTS.md): Details on enhanced reporting features
- [Multi-View Reporting](MULTI_VIEW_REPORTING.md): Information on multi-view reports

### Technical Documentation
- [Architecture Documentation](src/ARCHITECTURE.md): Detailed architecture overview
- [Testing Guide](docs/TESTING_GUIDE.md): Testing approach and examples
- [Simplified Terms Guide](docs/SIMPLIFIED_TERMS.md): Technical terms explained simply

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Anthropic for Claude API
- OpenAI for GPT API
- Zendesk for their API
