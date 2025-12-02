# AI-Powered Excel Analysis Telegram Bot

An intelligent Telegram bot that uses AI to analyze any Excel file and provide comprehensive categorized reports. Supports dispatcher earnings, driver payments, broker performance, and automatically detects other analysis categories.

## Features

### 🤖 AI-Powered Analysis
- Automatically detects analysis categories in your Excel files
- Intelligent column and data type detection
- AI-suggested calculation methods
- Works with any Excel file structure

### 📊 Supported Analyses
- **Dispatcher Earnings**: Calculate earnings by dispatcher with percentage-based rates
- **Driver Payments**: Analyze driver payments and earnings
- **Broker Performance**: Revenue breakdown by broker/customer
- **Auto-Detection**: AI discovers additional categories automatically

### 🎯 Smart Features
- Interactive category selection
- Multi-category configuration
- Weekly and overall breakdowns
- Flexible calculation methods (percentage, flat rate, sum-only)
- AI-assisted configuration suggestions

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

#### Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token you receive

#### OpenAI API Key (for AI features)
1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### 3. Configure Environment

Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

Then edit `.env` and add your tokens:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Important:** Never commit the `.env` file to git. It's already included in `.gitignore` for your security.

### 4. Run the Bot

```bash
python bot.py
```

You should see:
```
🤖 AI-Powered Bot is running...
📊 Features: Smart Excel Analysis, Multi-Category Reports
```

## Usage

### Quick Start

1. **Start the bot**
   - Send `/start` to your bot on Telegram

2. **Upload an Excel file**
   - Send any .xlsx or .xls file

3. **Review detected categories**
   - Bot shows what analyses it can perform
   - Example:
     ```
     📊 Analysis Options Detected:

     1️⃣ 📋 Dispatcher Earnings
        Calculate earnings for each dispatcher

     2️⃣ 🚗 Driver Payments
        Analyze driver payments

     3️⃣ 🏢 Broker Performance
        Revenue by broker
     ```

4. **Select analyses**
   - `/analyze 1` - Run dispatcher analysis
   - `/analyze 1 2` - Run multiple analyses
   - `/analyze all` - Run all detected analyses

5. **Configure (if needed)**
   - Bot will ask for configuration when needed
   - AI suggests best calculation method
   - Accept AI suggestion or provide custom config

6. **Get reports**
   - Receive detailed weekly breakdowns
   - Overall summary with totals
   - Earnings calculations

### Commands

- `/start` or `/help` - Show welcome message and instructions
- `/analyze <numbers>` - Run specific analyses (e.g., `/analyze 1 2`)
- `/analyze all` - Run all detected analyses
- `/categories` - View configured categories
- `/cancel` - Cancel current operation

### Excel File Format

Your Excel file can have any structure! The bot intelligently detects columns. Common patterns:

**Example 1: Logistics/Dispatch**
| Broker | Dispatch | Driver | Amount | Week |
|--------|----------|--------|--------|------|
| ABC Co | Java     | John   | 1500$  | Week 4 |
| XYZ Ltd| Baxa     | Sarah  | 2000$  | Week 4 |

**Example 2: Sales**
| Customer | Salesperson | Region | Revenue | Date |
|----------|-------------|--------|---------|------|
| Client A | Alice       | East   | $5,000  | 1/1  |
| Client B | Bob         | West   | $3,500  | 1/2  |

The bot will detect appropriate columns and suggest analyses!

### Configuration Examples

**Dispatcher Earnings (Percentage-based):**
```
Java: 1.5
Baxa: 1.3
Jasur: 1.3
Sharif: 1.5
```

**Driver Payments (Percentage-based):**
```
John: 70
Sarah: 65
Mike: 70
```

**Broker Analysis:**
No configuration needed - shows totals only!

## File Structure

```
ali-bot/
├── bot.py                      # Main bot application (AI-powered)
├── bot_legacy.py               # Original bot (backup)
├── ai_analyzer.py              # AI Excel analysis with OpenAI
├── config_manager.py           # Multi-category configuration
├── universal_processor.py      # Generic Excel processing
├── report_generator.py         # Report formatting
├── excel_processor.py          # Legacy processor (deprecated)
├── categories/                 # Analysis category definitions
│   ├── __init__.py
│   ├── base.py                # Base category class
│   ├── dispatcher.py          # Dispatcher analysis
│   ├── driver.py              # Driver analysis
│   └── broker.py              # Broker analysis
├── requirements.txt            # Python dependencies
├── .env                        # Your API keys (DO NOT COMMIT)
├── .env.example                # Template for .env
├── .gitignore                  # Git ignore rules
├── analysis_config.json        # Auto-generated configs
├── README.md                   # This file
└── May.xlsx, June.xlsx         # Your Excel files
```

## How It Works

### AI Analysis Pipeline

1. **Upload**: User sends Excel file
2. **Structure Analysis**: AI examines columns, data types, patterns
3. **Category Detection**: AI identifies possible analyses
4. **User Selection**: User chooses which analyses to run
5. **Configuration**: AI suggests calculation methods
6. **Processing**: Universal processor runs analyses
7. **Reporting**: Formatted reports sent to user

### Architecture

```
Excel File → AI Analyzer → Category Detection
                ↓
         User Selection
                ↓
    Configuration Manager ← AI Suggestions
                ↓
    Universal Processor (processes any category)
                ↓
    Report Generator (formats results)
                ↓
         Telegram Bot (sends reports)
```

## Advanced Features

### AI-Assisted Configuration

When configuring a new category, the bot can:
- Suggest percentage vs. flat rate based on data patterns
- Recommend reasonable percentage ranges
- Explain reasoning for suggestions

### Backward Compatibility

Your existing dispatcher configuration is automatically migrated to the new system. The bot still works with your old `/setconfig` setup!

### Multi-File Support

Process multiple files:
- Each file analyzed independently
- Configurations saved for reuse
- Consistent analysis across files

## Troubleshooting

**Bot doesn't detect categories:**
- Ensure column names are descriptive (e.g., "Dispatch", "Driver", "Amount")
- Check that data rows exist (not just headers)
- Try renaming columns to be more explicit

**AI features not working:**
- Verify `OPENAI_API_KEY` is set in `.env`
- Check OpenAI account has credits
- Bot falls back to rule-based detection if AI fails

**Configuration errors:**
- Use format: `EntityName: Value`
- Ensure values are numbers
- Percentages should be 0-100
- One entity per line

**Excel file errors:**
- File must be .xlsx or .xls
- Remove completely empty rows
- Ensure amount columns contain numbers

## Cost Management

### OpenAI API Usage
- Structure analysis: ~500 tokens per file
- Category detection: ~1,000 tokens per file
- Config suggestions: ~800 tokens per category
- Uses GPT-3.5-turbo (cost-effective)

**Estimated costs**: ~$0.002-0.005 per file analysis

**Tips to save costs:**
- Configurations are cached (one-time cost per category)
- Bot falls back to free rule-based detection if API key missing
- Only category detection uses AI (processing is local)

## Development

### Adding New Categories

1. Create new category class in `categories/`:
```python
from .base import AnalysisCategory, CalculationMethod

class CustomAnalysis(AnalysisCategory):
    def __init__(self, entity_column, amount_columns):
        super().__init__(
            name="Custom Analysis",
            entity_column=entity_column,
            amount_columns=amount_columns,
            calculation_method=CalculationMethod.PERCENTAGE
        )
```

2. Add to `categories/__init__.py`

3. Update `bot.py` to recognize new category type

### Running Tests

```bash
# Test AI analyzer
python -c "from ai_analyzer import AIExcelAnalyzer; import pandas as pd; df = pd.read_excel('May.xlsx'); a = AIExcelAnalyzer(); print(a.detect_categories(a.analyze_excel_structure(df)))"

# Test universal processor
python -c "from universal_processor import UniversalExcelProcessor; from categories import DispatcherAnalysis; import pandas as pd; df = pd.read_excel('May.xlsx'); cat = DispatcherAnalysis('Dispatch', ['Amount']); print(UniversalExcelProcessor.process_category(df, cat))"
```

## Legacy Version

The original dispatcher-only bot is saved as `bot_legacy.py`. To use it:

```bash
python bot_legacy.py
```

## Future Enhancements

- [ ] PDF export of reports
- [ ] Historical trend analysis
- [ ] Automated anomaly detection
- [ ] Custom calculation formulas
- [ ] Multi-file batch processing
- [ ] Chart/graph generation
- [ ] Email report delivery

## License

MIT License - feel free to use and modify!

## Support

- File issues on GitHub
- Check `/help` in bot for quick reference
- Review logs for detailed error messages

## Credits

Built with:
- Python 3.11+
- python-telegram-bot
- OpenAI GPT-3.5
- pandas & openpyxl
