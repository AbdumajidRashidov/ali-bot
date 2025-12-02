import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
from dotenv import load_dotenv
from excel_processor import process_excel_file

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File to store dispatcher percentages
CONFIG_FILE = 'dispatcher_config.json'

class DispatcherBot:
    def __init__(self):
        self.dispatcher_percentages = self.load_config()

    def load_config(self):
        """Load dispatcher percentages from config file"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self):
        """Save dispatcher percentages to config file"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.dispatcher_percentages, f, indent=2)

bot_instance = DispatcherBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = """
Welcome to the Dispatcher Earnings Bot! 🚀

Here's how to use me:

1️⃣ **Set Dispatcher Percentages:**
   Send: /setconfig
   Example:
   ```
   Ali: 10
   Sara: 15
   John: 12
   ```

2️⃣ **View Current Config:**
   Send: /viewconfig

3️⃣ **Process Excel File:**
   Simply send me an Excel file (.xlsx) with columns:
   - Dispatch (dispatcher name)
   - Amount (revenue amount)

   I'll calculate total earnings for each dispatcher!

Let's get started! 👇
"""
    await update.message.reply_text(welcome_message)

async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to send dispatcher configuration"""
    message = """
Please send the dispatcher percentages in this format:

DispatcherName: Percentage

Example:
```
Ali: 10
Sara: 15
John: 12
Mike: 8
```

Just send the list as a regular message (not as a command).
"""
    await update.message.reply_text(message)
    context.user_data['awaiting_config'] = True

async def view_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display current dispatcher configuration"""
    if not bot_instance.dispatcher_percentages:
        await update.message.reply_text("No configuration set yet. Use /setconfig to add dispatchers.")
        return

    config_text = "📊 Current Dispatcher Percentages:\n\n"
    for dispatcher, percentage in bot_instance.dispatcher_percentages.items():
        config_text += f"• {dispatcher}: {percentage}%\n"

    await update.message.reply_text(config_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for configuration input"""
    if context.user_data.get('awaiting_config'):
        try:
            # Parse the configuration
            text = update.message.text
            lines = text.strip().split('\n')

            new_config = {}
            for line in lines:
                if ':' in line:
                    parts = line.split(':')
                    dispatcher = parts[0].strip()
                    percentage = float(parts[1].strip())
                    new_config[dispatcher] = percentage

            if new_config:
                bot_instance.dispatcher_percentages = new_config
                bot_instance.save_config()

                response = "✅ Configuration saved successfully!\n\n"
                for dispatcher, percentage in new_config.items():
                    response += f"• {dispatcher}: {percentage}%\n"

                await update.message.reply_text(response)
                context.user_data['awaiting_config'] = False
            else:
                await update.message.reply_text("❌ No valid configuration found. Please try again.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error parsing configuration: {str(e)}\nPlease try again.")
    else:
        await update.message.reply_text("Send /start to see available commands.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Excel file uploads"""
    document = update.message.document

    # Check if it's an Excel file
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Please send an Excel file (.xlsx or .xls)")
        return

    # Check if configuration is set
    if not bot_instance.dispatcher_percentages:
        await update.message.reply_text("❌ Please set dispatcher percentages first using /setconfig")
        return

    try:
        await update.message.reply_text("📥 Processing your file...")

        # Download the file
        file = await document.get_file()
        file_path = f"temp_{document.file_name}"
        await file.download_to_drive(file_path)

        # Process the Excel file
        results = process_excel_file(file_path, bot_instance.dispatcher_percentages)

        # Format and send results - Weekly breakdown
        messages = []

        # Process each week
        for week, week_data in results['weeks'].items():
            response = f"📅 **Week: {week}**\n\n"

            week_total_revenue = 0
            week_total_earnings = 0

            for dispatcher, data in sorted(week_data.items()):
                total_amount = data['total_amount']
                percentage = data['percentage']
                earnings = data['earnings']

                # Only show dispatchers with non-zero revenue
                if total_amount > 0:
                    week_total_revenue += total_amount
                    week_total_earnings += earnings

                    response += f"👤 **{dispatcher}**\n"
                    response += f"   Revenue: ${total_amount:,.2f}\n"
                    response += f"   Percentage: {percentage}%\n"
                    response += f"   Earnings: ${earnings:,.2f}\n\n"

            response += f"─────────────────\n"
            response += f"Week Total: ${week_total_revenue:,.2f}\n"
            response += f"Week Earnings: ${week_total_earnings:,.2f}\n"

            messages.append(response)

        # Overall summary
        overall_response = f"📊 **Overall Summary - {document.file_name}**\n\n"

        grand_total_revenue = 0
        grand_total_earnings = 0

        for dispatcher, data in sorted(results['overall'].items()):
            total_amount = data['total_amount']
            percentage = data['percentage']
            earnings = data['earnings']

            grand_total_revenue += total_amount
            grand_total_earnings += earnings

            overall_response += f"👤 **{dispatcher}**\n"
            overall_response += f"   Total Revenue: ${total_amount:,.2f}\n"
            overall_response += f"   Percentage: {percentage}%\n"
            overall_response += f"   Total Earnings: ${earnings:,.2f}\n\n"

        overall_response += f"═══════════════════\n"
        overall_response += f"📈 Grand Total Revenue: ${grand_total_revenue:,.2f}\n"
        overall_response += f"💰 Grand Total Earnings: ${grand_total_earnings:,.2f}\n"

        messages.append(overall_response)

        # Send all messages
        for msg in messages:
            await update.message.reply_text(msg)

        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")

        # Clean up temporary file in case of error
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    """Start the bot."""
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
    application.add_handler(CommandHandler("setconfig", set_config))
    application.add_handler(CommandHandler("viewconfig", view_config))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Start the Bot
    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
