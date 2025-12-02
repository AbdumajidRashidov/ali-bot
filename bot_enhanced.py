import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
import pandas as pd
from typing import Dict
from dotenv import load_dotenv

# Import new modules
from ai_analyzer import AIExcelAnalyzer
from config_manager import ConfigManager
from universal_processor import UniversalExcelProcessor
from report_generator import ReportGenerator
from categories import DispatcherAnalysis, DriverAnalysis, BrokerAnalysis

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class IntelligentDispatchBot:
    """Enhanced bot with AI-powered analysis"""

    def __init__(self):
        self.config_manager = ConfigManager()

        # Migrate legacy config if it exists
        self.config_manager.migrate_legacy_config()

        # Initialize AI analyzer (will be created when needed to handle API key)
        self.ai_analyzer = None

    def get_ai_analyzer(self):
        """Lazy initialization of AI analyzer"""
        if self.ai_analyzer is None:
            try:
                self.ai_analyzer = AIExcelAnalyzer()
            except ValueError as e:
                logger.warning(f"AI Analyzer not available: {e}")
        return self.ai_analyzer

bot_instance = IntelligentDispatchBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_message = """
🤖 **Welcome to AI-Powered Excel Analysis Bot!**

I can intelligently analyze any Excel file and provide comprehensive reports.

**How it works:**
1️⃣ Upload an Excel file (.xlsx)
2️⃣ I'll detect what can be analyzed
3️⃣ Choose which analyses to run
4️⃣ Get detailed reports!

**Supported Analyses:**
📋 Dispatcher Earnings
🚗 Driver Payments
🏢 Broker Performance
...and more (AI auto-detects!)

**Commands:**
/setconfig - Pre-configure categories before uploading files
/categories - View configured categories
/help - Show this message

**Let's get started!**
Just send me an Excel file 📊
Or use /setconfig to set up your configurations first!
"""
    await update.message.reply_text(welcome_message)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all configured categories"""
    categories = bot_instance.config_manager.get_all_categories()

    if not categories:
        await update.message.reply_text(
            "No categories configured yet.\n"
            "Upload an Excel file to get started!"
        )
        return

    message = "📊 **Configured Categories:**\n\n"
    for cat_id in categories:
        message += f"• {cat_id.replace('_', ' ').title()}\n"

    await update.message.reply_text(message)

async def setconfig_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setconfig command to pre-configure categories"""
    # Clear any previous setconfig state
    if 'setconfig_mode' in context.user_data:
        del context.user_data['setconfig_mode']
    if 'setconfig_category' in context.user_data:
        del context.user_data['setconfig_category']

    # Show category selection menu
    menu = """
🔧 **Pre-Configure Analysis Categories**

Choose which category to configure:

**1️⃣ Dispatcher Earnings**
Calculate earnings for dispatchers based on percentages
Example: Java: 1.5%, Baxa: 1.3%

**2️⃣ Driver Payments**
Calculate payments for drivers based on percentages
Example: Driver1: 70%, Driver2: 65%

**3️⃣ Broker Performance**
Analyze broker revenue (sum only, no calculation)

**How to use:**
Reply with the number (1, 2, or 3) to configure that category.

Or use `/cancel` to exit configuration mode.
"""
    await update.message.reply_text(menu)

    # Set flag that we're in setconfig mode
    context.user_data['setconfig_mode'] = 'awaiting_category_selection'

async def handle_setconfig_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle the setconfig conversation flow"""
    mode = context.user_data.get('setconfig_mode')

    if mode == 'awaiting_category_selection':
        # User is selecting which category to configure
        category_map = {
            '1': ('dispatcher_earnings', DispatcherAnalysis),
            '2': ('driver_payments', DriverAnalysis),
            '3': ('broker_analysis', BrokerAnalysis)
        }

        if text not in category_map:
            await update.message.reply_text(
                "❌ Invalid selection. Please reply with 1, 2, or 3.\n"
                "Or use `/cancel` to exit."
            )
            return

        cat_id, cat_class = category_map[text]

        # Create a category instance with placeholder values
        # We'll ask user for entity names first
        category = cat_class(
            entity_column='placeholder',
            amount_columns=['placeholder']
        )

        # Store category info
        context.user_data['setconfig_category_id'] = cat_id
        context.user_data['setconfig_category'] = category
        context.user_data['setconfig_mode'] = 'awaiting_entity_list'

        # Ask for entity names
        entity_type = category.name.split()[0]  # e.g., "Dispatcher" from "Dispatcher Earnings"

        await update.message.reply_text(
            f"📝 **Configure {category.name}**\n\n"
            f"Please provide the list of {entity_type.lower()}s, one per line.\n\n"
            f"**Example:**\n"
            f"Java\n"
            f"Baxa\n"
            f"Jasur\n"
            f"Sherali\n\n"
            f"Send your list now:"
        )

    elif mode == 'awaiting_entity_list':
        # User sent entity names
        category = context.user_data['setconfig_category']

        # Parse entity names (one per line)
        entities = [line.strip() for line in text.split('\n') if line.strip()]

        if not entities:
            await update.message.reply_text(
                "❌ No entities found. Please send entity names, one per line."
            )
            return

        # Store entities
        context.user_data['setconfig_entities'] = entities
        context.user_data['setconfig_mode'] = 'awaiting_values'

        # Ask for configuration values
        await update.message.reply_text(
            category.get_config_prompt(entities)
        )

    elif mode == 'awaiting_values':
        # User sent configuration values
        category = context.user_data['setconfig_category']
        entities = context.user_data['setconfig_entities']

        # Parse config from text
        config = bot_instance.config_manager.parse_config_from_text(
            text,
            category
        )

        if not config:
            await update.message.reply_text(
                "❌ Could not parse configuration.\n"
                "Please use format: `EntityName: Value`\n\n"
                + category.get_config_prompt(entities)
            )
            return

        # Validate and save
        if bot_instance.config_manager.validate_and_save(category, config):
            await update.message.reply_text(
                f"✅ Configuration saved for {category.name}!\n\n"
                + bot_instance.config_manager.format_config_for_display(category)
                + "\n\n📊 You can now upload Excel files, and this configuration will be used automatically.\n\n"
                + "💡 To configure another category, use `/setconfig` again."
            )

            # Clear setconfig state
            del context.user_data['setconfig_mode']
            del context.user_data['setconfig_category']
            del context.user_data['setconfig_entities']
            del context.user_data['setconfig_category_id']
        else:
            await update.message.reply_text(
                "❌ Invalid configuration. Please try again.\n\n"
                + category.get_config_prompt(entities)
            )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Excel file uploads with AI analysis"""
    document = update.message.document

    # Check if it's an Excel file
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Please send an Excel file (.xlsx or .xls)")
        return

    # Clear any previous state when new file is uploaded
    context.user_data.clear()

    try:
        await update.message.reply_text("📥 Analyzing your file...")

        # Download the file
        file = await document.get_file()
        file_path = f"temp_{document.file_name}"
        await file.download_to_drive(file_path)

        # Read Excel file
        df = pd.read_excel(file_path)

        # Analyze with AI
        analyzer = bot_instance.get_ai_analyzer()

        if analyzer:
            # AI-powered analysis
            structure = analyzer.analyze_excel_structure(df)
            detected_categories = analyzer.detect_categories(structure)
        else:
            # Fallback: Use rule-based detection
            logger.info("Using fallback detection (no AI)")
            from ai_analyzer import AIExcelAnalyzer
            temp_analyzer = AIExcelAnalyzer.__new__(AIExcelAnalyzer)
            structure = temp_analyzer.analyze_excel_structure(df)
            detected_categories = temp_analyzer._fallback_detection(structure)

        if not detected_categories:
            await update.message.reply_text(
                "❌ Could not detect any analysis categories.\n"
                "Please ensure your Excel file has clear column names like:\n"
                "• Dispatch, Driver, Broker\n"
                "• Amount, Total, Revenue"
            )
            os.remove(file_path)
            return

        # Store detected categories and file info in context
        context.user_data['pending_file'] = file_path
        context.user_data['file_name'] = document.file_name
        context.user_data['detected_categories'] = detected_categories
        context.user_data['df'] = df

        # Show category selection menu
        menu = ReportGenerator.generate_category_selection_menu(detected_categories)
        await update.message.reply_text(menu)

    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        error_msg = ReportGenerator.generate_error_message(e)
        await update.message.reply_text(error_msg)

        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze command"""
    if 'detected_categories' not in context.user_data:
        await update.message.reply_text(
            "❌ Please upload an Excel file first!"
        )
        return

    # Parse arguments
    args = context.args
    if not args:
        await update.message.reply_text(
            "Please specify which analyses to run:\n"
            "• `/analyze 1 2` - Run specific analyses\n"
            "• `/analyze all` - Run all analyses"
        )
        return

    detected_categories = context.user_data['detected_categories']

    # Determine which categories to analyze
    if args[0].lower() == 'all':
        selected_indices = list(range(len(detected_categories)))
    else:
        try:
            selected_indices = [int(arg) - 1 for arg in args]
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid selection. Use numbers like `/analyze 1 2`"
            )
            return

    # Validate indices
    selected_categories = []
    for idx in selected_indices:
        if 0 <= idx < len(detected_categories):
            selected_categories.append(detected_categories[idx])
        else:
            await update.message.reply_text(
                f"❌ Invalid selection: {idx + 1}. "
                f"Please choose from 1 to {len(detected_categories)}"
            )
            return

    # Store selected categories for processing
    context.user_data['selected_categories'] = selected_categories
    context.user_data['current_category_index'] = 0

    # Start processing first category
    await process_next_category(update, context)

async def process_next_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the next category in the queue"""
    selected_categories = context.user_data.get('selected_categories', [])
    current_index = context.user_data.get('current_category_index', 0)

    if current_index >= len(selected_categories):
        # All done!
        await finish_analysis(update, context)
        return

    cat_data = selected_categories[current_index]

    # Create category object based on type
    category = create_category_from_dict(cat_data)

    # Check if config is needed
    if category.config_needed and not bot_instance.config_manager.has_category_config(category):
        # Need to configure this category
        await request_category_config(update, context, category, cat_data)
    else:
        # Config exists or not needed, run analysis
        await run_category_analysis(update, context, category)

async def request_category_config(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category,
    cat_data: Dict
):
    """Request configuration for a category"""
    df = context.user_data['df']

    # Get unique entities
    entities = df[category.entity_column].dropna().unique().tolist()
    entities = [str(e).strip() for e in entities if str(e).strip() != 'nan']

    # Get AI suggestion for calculation method
    analyzer = bot_instance.get_ai_analyzer()
    ai_suggestion = None

    if analyzer:
        try:
            structure = analyzer.analyze_excel_structure(df)
            ai_suggestion = analyzer.suggest_calculation_method(cat_data, structure)
        except Exception as e:
            logger.warning(f"Could not get AI suggestion: {e}")

    # Store info for later
    context.user_data['awaiting_config_category'] = category
    context.user_data['config_entities'] = entities
    context.user_data['ai_suggestion'] = ai_suggestion

    # Send config request message
    config_msg = ReportGenerator.generate_config_needed_message(
        category, entities, ai_suggestion
    )
    await update.message.reply_text(config_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    # Skip if message has no text (e.g., file uploads)
    if not update.message.text:
        return

    text = update.message.text.strip()

    # Check if in setconfig mode
    if 'setconfig_mode' in context.user_data:
        await handle_setconfig_flow(update, context, text)
        return

    # Lower case for other checks
    text_lower = text.lower()

    # Check if awaiting config
    if 'awaiting_config_category' in context.user_data:
        category = context.user_data['awaiting_config_category']
        entities = context.user_data['config_entities']
        ai_suggestion = context.user_data.get('ai_suggestion')

        # Check if user accepted AI suggestion
        if ai_suggestion and text_lower in ['yes', 'y', 'accept']:
            # User accepted AI suggestion - ask for actual values
            # Clear AI suggestion so next message will be parsed as config
            del context.user_data['ai_suggestion']
            await update.message.reply_text(
                category.get_config_prompt(entities)
            )
            return
        elif ai_suggestion and text_lower in ['custom', 'no', 'n']:
            # User wants custom config - ask for values
            # Clear AI suggestion so next message will be parsed as config
            del context.user_data['ai_suggestion']
            await update.message.reply_text(
                category.get_config_prompt(entities)
            )
            return

        # Parse config from text (use original text, not lowercased)
        config = bot_instance.config_manager.parse_config_from_text(
            text,
            category
        )

        if not config:
            await update.message.reply_text(
                "❌ Could not parse configuration.\n"
                "Please use format: `EntityName: Value`"
            )
            return

        # Validate and save
        if bot_instance.config_manager.validate_and_save(category, config):
            await update.message.reply_text(
                f"✅ Configuration saved for {category.name}!\n\n"
                + bot_instance.config_manager.format_config_for_display(category)
            )

            # Clear awaiting state
            del context.user_data['awaiting_config_category']
            del context.user_data['config_entities']
            if 'ai_suggestion' in context.user_data:
                del context.user_data['ai_suggestion']

            # Continue with analysis
            await run_category_analysis(update, context, category)
        else:
            await update.message.reply_text(
                "❌ Invalid configuration. Please try again."
            )

    else:
        await update.message.reply_text(
            "Send /start to see available commands."
        )

async def run_category_analysis(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category
):
    """Run analysis for a category"""
    try:
        df = context.user_data['df']
        file_name = context.user_data['file_name']
        chat_id = update.effective_chat.id

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔄 Running {category.name} analysis..."
        )

        # Get config
        config = bot_instance.config_manager.get_category_config(category)

        # Process with universal processor
        results = UniversalExcelProcessor.process_category(df, category, config)

        # Generate reports
        reports = ReportGenerator.generate_analysis_report(
            category, results, file_name
        )

        # Send all report messages
        for report in reports:
            await context.bot.send_message(chat_id=chat_id, text=report)

        # Move to next category
        context.user_data['current_category_index'] += 1
        await process_next_category(update, context)

    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=ReportGenerator.generate_error_message(e)
        )

async def finish_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish analysis and clean up"""
    selected_categories = context.user_data.get('selected_categories', [])
    chat_id = update.effective_chat.id

    # Send summary
    summary = ReportGenerator.generate_analysis_summary(
        selected_categories,
        len(selected_categories)  # Simplified count
    )
    await context.bot.send_message(chat_id=chat_id, text=summary)

    # Clean up temp file
    file_path = context.user_data.get('pending_file')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Clear context
    context.user_data.clear()

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    # Clean up temp file
    file_path = context.user_data.get('pending_file')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    context.user_data.clear()
    await update.message.reply_text("✅ Operation cancelled.")

def create_category_from_dict(cat_data: Dict):
    """Create category object from dictionary"""
    name = cat_data.get('name', '').lower()

    if 'dispatch' in name:
        return DispatcherAnalysis(
            entity_column=cat_data['entity_column'],
            amount_columns=cat_data['amount_columns'],
            confidence=cat_data.get('confidence', 1.0)
        )
    elif 'driver' in name:
        return DriverAnalysis(
            entity_column=cat_data['entity_column'],
            amount_columns=cat_data['amount_columns'],
            confidence=cat_data.get('confidence', 1.0)
        )
    elif 'broker' in name:
        return BrokerAnalysis(
            entity_column=cat_data['entity_column'],
            amount_columns=cat_data['amount_columns'],
            confidence=cat_data.get('confidence', 1.0)
        )
    else:
        # Generic category
        return DispatcherAnalysis(
            entity_column=cat_data['entity_column'],
            amount_columns=cat_data['amount_columns'],
            confidence=cat_data.get('confidence', 1.0)
        )

def main():
    """Start the bot"""
    # Get token from .env file
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not TOKEN:
        print("⚠️  Error: TELEGRAM_BOT_TOKEN not found!")
        print("Please create a .env file with your bot token:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return

    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("categories", show_categories))
    application.add_handler(CommandHandler("setconfig", setconfig_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Start the Bot
    print("🤖 AI-Powered Bot is running...")
    print("📊 Features: Smart Excel Analysis, Multi-Category Reports")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
