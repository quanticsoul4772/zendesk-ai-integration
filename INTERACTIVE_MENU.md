# Interactive Menu for Zendesk AI Integration

The interactive menu provides a user-friendly interface for navigating Zendesk views and executing actions on them, eliminating the need to remember view IDs or specific command-line arguments.

## Launching the Interactive Menu

### Using the Command Line

```bash
# Windows
python -m src.zendesk_ai_app --mode interactive

# macOS/Linux
python -m src.zendesk_ai_app --mode interactive
```

### Using Convenience Scripts

**Windows**:
```
zendesk_menu.bat
```

**macOS/Linux**:
```
./zendesk_menu.sh
```

## Menu Navigation

The interactive menu system is organized hierarchically, making it easy to navigate through your Zendesk views:

1. **Main Menu**
   - Categories based on view name prefixes (e.g., "Support", "Production")
   - Recently used views for quick access
   - Exit option

2. **Category/Subcategory Menu**
   - Displays subcategories and views within the selected category
   - Options to go back or return to the main menu

3. **View Actions Menu**
   - Available actions for the selected view
   - Option to go back

### Breadcrumb Navigation

The menu displays your current location in the hierarchy as breadcrumbs at the top of each menu (e.g., "Home > Support > Pending").

### Recently Used Views

The main menu includes a section with your recently used views for quick access.

## Keyboard Navigation

- **↑/↓**: Move between options
- **Enter**: Select highlighted option
- **Esc**: Go back to previous menu
- **/** (forward slash): Activate search
- **First letter**: Jump to matching option

## Available Actions

When you select a view, you can perform the following actions:

1. **Run Sentiment Analysis**
   - Analyzes tickets in the view using AI
   - Detects sentiment, urgency, and business impact
   - Saves results to the database

2. **Generate Pending Report**
   - Creates a report of pending tickets
   - Saves the report to a file

3. **Generate Enhanced Report**
   - Creates a detailed sentiment analysis report
   - Includes metrics like sentiment distribution, urgency levels, etc.
   - Saves the report to a file

4. **View Tickets in Browser**
   - Opens the selected view in your web browser

## Search Functionality

You can search for views or categories by pressing the `/` key and typing your search term. This is especially useful when you have many views to navigate through.

## Cross-Platform Support

The interactive menu works on:
- Windows (using prompt_toolkit with a simplified UI)
- macOS (using simple-term-menu)
- Linux (using simple-term-menu)

## Testing the Menu System

To run tests specifically for the interactive menu:

```bash
python run_menu_tests.py
```

To run tests with coverage report:

```bash
python run_menu_tests.py --coverage
```

To run tests with increased verbosity:

```bash
python run_menu_tests.py -v
```

The test suite includes:
- Tests for different view structures (empty, flat, nested, deeply nested)
- Tests with large numbers of views (500+)
- Tests for search functionality
- Tests for keyboard shortcuts
- Tests for navigation between menu levels
- Tests for action execution

## Examples

### Example 1: Run Sentiment Analysis on Support Tickets

1. Launch the interactive menu
2. Select "Support" category
3. Select "Open Tickets" view
4. Choose "Run Sentiment Analysis"
5. Wait for the analysis to complete

### Example 2: Generate a Report for Multiple Views

1. Launch the interactive menu
2. Select a view from the "Recently Used Views" section
3. Choose "Generate Enhanced Report"
4. View the generated report

## Troubleshooting

### Menu Display Issues

If you encounter display issues:
- Try increasing your terminal window size
- The UI uses a simplified style for better compatibility

### Windows-Specific Issues

If you encounter issues on Windows:
- Ensure windows-curses and prompt_toolkit are installed
- Try using Windows Terminal instead of the standard command prompt

### Navigation Problems

If navigation becomes difficult:
- Use the search functionality (press `/`) to quickly find views
- Use the "Recently Used Views" section for frequently accessed views
