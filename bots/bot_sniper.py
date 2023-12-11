import time
import logging
from datetime import datetime
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
        self.last_check_time = int(time.time())
        self.setup_jobs()
        self.notify_startup()

    def setup_jobs(self):
        self.scheduler.add_job(self.check_new_votes, 'interval', seconds=60)
        self.scheduler.add_job(self.check_voting_results, 'interval', minutes=5)
        self.scheduler.start()

    def notify_startup(self):
        # Отправка сообщения о запуске бота
        startup_message = "Бот для отслеживания голосований запущен и работает."
        try:
            self.updater.bot.send_message(chat_id=self.channel_name, text=startup_message)
            logger.info("Startup message sent to channel.")
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")

    def check_new_votes(self):
        new_votes = self.db.get_new_votes(self.last_check_time)
        for vote in new_votes:
            sender = vote['sender']
            recipient = vote['recipient']
            vote_id = vote['vote_id']
            vote_info = self.db.get_vote(vote_id)
            message = f"@{sender} успешно отправил голос на кошелек кандидата @{recipient} в голосовании '{vote_info['name']}'"
            try:
                self.updater.bot.send_message(chat_id=self.channel_name, text=message)
                logger.info(f"Message sent to channel: {message}")
            except Exception as e:
                logger.error(f"Error sending message: {e}")
        self.last_check_time = int(time.time())

    def check_voting_results(self):
        completed_votes = self.db.get_completed_votes()
        for vote in completed_votes:
            vote_id = vote['id']
            winner = self.db.get_vote_winner(vote_id)
            if winner:
                message = f"В голосовании '{vote['name']}' победу одержал кандидат @{winner}"
                try:
                    self.updater.bot.send_message(chat_id=self.channel_name, text=message)
                    logger.info(f"Results announced for vote: {vote['name']}")
                except Exception as e:
                    logger.error(f"Error sending vote result: {e}")
                self.db.mark_vote_as_announced(vote_id)

    def run(self):
        logger.info("Бот для отслеживания голосований запущен и работает...")
        while True:
            time.sleep(10)

if __name__ == '__main__':
    token = 'TELEGRAM_BOT_TOKEN'
    db_file = 'database.db'
    channel_name = 'CHANNEL_ID'
    second_bot = SecondBot(token, db_file, channel_name)
    second_bot.run()


