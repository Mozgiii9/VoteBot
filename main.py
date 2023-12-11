from bots.bot_handler import BotHandler

def main():
    
    token = 'TELEGRAM_BOT_TOKEN'

    db_file = 'database.db'

    bot = BotHandler(token, db_file)
    bot.run()

if __name__ == "__main__":
    main()
