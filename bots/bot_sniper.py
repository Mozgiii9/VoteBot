import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater
from db_handler import DatabaseHandler
import pytz

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecondBot:
    def __init__(self, token, db_file, channel_name):
        self.updater = Updater(token, use_context=True)
        self.db = DatabaseHandler(db_file)
        self.scheduler = BackgroundScheduler(timezone=pytz.utc)
        self.channel_name = channel_name
        self.last_transaction_id = self.get_last_transaction_id()
        self.setup_jobs()
        self.notify_startup()

    def get_last_transaction_id(self):
        last_transaction = self.db.get_last_transaction()
        return last_transaction[0] if last_transaction else 0

    def setup_jobs(self):
        self.scheduler.add_job(self.check_new_votes, 'interval', seconds=10)
        self.scheduler.start()

    def notify_startup(self):
        startup_message = "Бот для отслеживания голосований запущен и работает."
        try:
            self.updater.bot.send_message(chat_id=self.channel_name, text=startup_message)
            logger.info("Startup message sent to channel.")
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")

    def check_new_votes(self):
        new_transactions = self.db.get_new_transactions_since(self.last_transaction_id)
        if new_transactions:
            for transaction in new_transactions:
                sender = transaction[1]  # Индекс зависит от структуры вашей таблицы transactions
                recipient = transaction[2]  # Индекс зависит от структуры вашей таблицы transactions
                message = f"Успешная транзакция: @{sender} перевел голос -> @{recipient}"
                try:
                    self.updater.bot.send_message(chat_id=self.channel_name, text=message)
                    logger.info(f"Sent new transaction notification to channel: {message}")
                except Exception as e:
                    logger.error(f"Error sending transaction notification: {e}")
                self.last_transaction_id = transaction[0]  # Обновление ID последней транзакции
        else:
            logger.info("No new transactions found.")
        time.sleep(10)

    def run(self):
        logger.info("Бот для отслеживания голосований запущен и работает...")
        self.scheduler.start()

if __name__ == '__main__':
    token = 'TELEGRAM_BOT_TOKEN'
    db_file = 'database.db'
    channel_name = 'CHANNEL_ID'
    second_bot = SecondBot(token, db_file, channel_name)
    second_bot.run()
