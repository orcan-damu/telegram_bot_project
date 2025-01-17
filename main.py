from bot.bot import start, handle_voice, handle_button_click, handle_text
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv  # Import load_dotenv
import os  # Import os to access environment variables

# Load environment variables from .env file
load_dotenv()

def main():
    # Get the bot token from the environment variable
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("No BOT_TOKEN found in .env file.")

    # Build the application
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(CallbackQueryHandler(handle_button_click))  # Handle button clicks
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  # Handle text messages

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()