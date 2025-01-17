from bot.bot import start, handle_voice
from telegram.ext import Application, CommandHandler, MessageHandler, filters

def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("8078421446:AAHbJVqpjGyEfnwvuP3NJeUA-qVc8k48P6g").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()