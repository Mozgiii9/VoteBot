from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from db_handler import DatabaseHandler
import logging
import pytz

# Константы состояний для ConversationHandler
SELECTING_ACTION, VOTING, CONFIRM_VOTE, ADMIN_AUTH, CREATING_VOTE, ADDING_CANDIDATE = range(6)

class BotHandler:
    def __init__(self, token, db_file):
        self.updater = Updater(token, use_context=True)
        self.dp = self.updater.dispatcher
        self.db = DatabaseHandler(db_file)
        self.init_handlers()
        self.admin_password = "ADMIN111!"

    def init_handlers(self):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('voting', self.voting),
                          CommandHandler('admin', self.admin)],
            states={
                SELECTING_ACTION: [MessageHandler(Filters.text & ~Filters.command, self.select_vote)],
                VOTING: [MessageHandler(Filters.text & ~Filters.command, self.vote)],
                CONFIRM_VOTE: [MessageHandler(Filters.text & ~Filters.command, self.confirm_vote)],
                ADMIN_AUTH: [MessageHandler(Filters.text & ~Filters.command, self.check_admin)],
                CREATING_VOTE: [MessageHandler(Filters.text & ~Filters.command, self.create_vote)],
                ADDING_CANDIDATE: [MessageHandler(Filters.text & ~Filters.command, self.add_candidate)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        self.dp.add_handler(conv_handler)
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("menu", self.menu))
        self.dp.add_handler(CommandHandler("description", self.description))

    def start(self, update, context):
        user = update.message.from_user
        username = user.username
        if not self.db.get_user(username):
            self.db.add_user(username, "wallet_of_" + username, "user")
            update.message.reply_text(f"Добро пожаловать, {username}! Ваш аккаунт создан.")
        else:
            update.message.reply_text(f"Доброго времени суток, {username}! Вот список команд для взаимодействия с ботом:")
        self.menu(update, context)

    def menu(self, update, context):
        update.message.reply_text("Список команд:\n/voting - Принять участие в голосовании\n/admin - Админ-панель\n/description - Описание бота")

    def description(self, update, context):
        update.message.reply_text("Этот бот предназначен для проведения открытых голосований с использованием технологии блокчейн.")

    def admin(self, update, context):
        update.message.reply_text("Введите кодовое слово, чтобы зайти под видом админа:")
        return ADMIN_AUTH

    def check_admin(self, update, context):
        text = update.message.text
        if text == self.admin_password:
            update.message.reply_text("Вы вошли как администратор. Введите название нового голосования:")
            return CREATING_VOTE
        else:
            update.message.reply_text("Неправильное кодовое слово.")
            return ConversationHandler.END

    def create_vote(self, update, context):
        vote_name = update.message.text
        context.user_data['vote_name'] = vote_name
        update.message.reply_text(f"Голосование '{vote_name}' создано. Введите имя первого кандидата:")
        return ADDING_CANDIDATE

    def add_candidate(self, update, context):
        candidate = update.message.text
        if 'candidates' not in context.user_data:
            context.user_data['candidates'] = []
        context.user_data['candidates'].append(candidate)
        if len(context.user_data['candidates']) == 2:  # Предположим, что в голосовании 2 кандидата
            self.db.create_vote(context.user_data['vote_name'], context.user_data['candidates'])
            update.message.reply_text(f"Кандидаты добавлены. Голосование создано.")
            return ConversationHandler.END
        else:
            update.message.reply_text("Введите имя следующего кандидата:")
            return ADDING_CANDIDATE

    def voting(self, update, context):
        active_votes = self.db.get_active_votes()
        reply_text = "Активные голосования:\n"
        for vote in active_votes:
            reply_text += f"{vote[0]}. {vote[1]} (до {vote[4]})\n"
        reply_text += "\nВыберите номер голосования для участия."
        update.message.reply_text(reply_text)
        return SELECTING_ACTION

    def select_vote(self, update, context):
        vote_id = update.message.text
        vote = self.db.get_vote(vote_id)
        if vote:
            context.user_data['vote_id'] = vote_id
            update.message.reply_text(f"Вы выбрали голосование '{vote[1]}'. Введите имя кандидата для голосования:")
            return VOTING
        else:
            update.message.reply_text("Неверный номер голосования. Попробуйте еще раз:")
            return SELECTING_ACTION

    def vote(self, update, context):
        candidate = update.message.text
        context.user_data['candidate'] = candidate
        update.message.reply_text(f"Вы хотите проголосовать за {candidate}. Подтвердите ваш выбор (да/нет):")
        return CONFIRM_VOTE

    def confirm_vote(self, update, context):
        confirmation = update.message.text.lower()
        if confirmation == 'да':
            vote_id = context.user_data['vote_id']
            candidate = context.user_data['candidate']
            username = update.message.from_user.username
            self.db.add_transaction(username, candidate, vote_id)
            update.message.reply_text(f"Вы успешно проголосовали за {candidate}!")
            return ConversationHandler.END
        else:
            update.message.reply_text("Голосование отменено.")
            return ConversationHandler.END

    def cancel(self, update, context):
        update.message.reply_text('Действие отменено.')
        return ConversationHandler.END

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    token = 'TELEGRAM_BOT_TOKEN'
    db_file = 'database.db'
    bot = BotHandler(token, db_file)
    bot.run()
