import sqlite3
import time

class DatabaseHandler:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            wallet TEXT,
            role TEXT
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            candidates TEXT,
            start_time INTEGER,
            end_time INTEGER,
            results_announced INTEGER DEFAULT 0
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            vote_id INTEGER,
            timestamp INTEGER,
            FOREIGN KEY (vote_id) REFERENCES votes(id)
        )''')
        self.conn.commit()

    def add_user(self, username, wallet, role):
        try:
            self.cursor.execute('INSERT INTO users (username, wallet, role) VALUES (?, ?, ?)',
                                (username, wallet, role))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Пользователь с таким именем уже существует")

    def get_user(self, username):
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return self.cursor.fetchone()

    def create_vote(self, name, candidates):
        start_time = int(time.time())
        end_time = start_time + 86400  # 24 часа
        self.cursor.execute('INSERT INTO votes (name, candidates, start_time, end_time) VALUES (?, ?, ?, ?)', 
                            (name, ','.join(candidates), start_time, end_time))
        self.conn.commit()

    def get_vote(self, vote_id):
        self.cursor.execute('SELECT * FROM votes WHERE id = ?', (vote_id,))
        return self.cursor.fetchone()

    def get_active_votes(self):
        current_time = int(time.time())
        self.cursor.execute('SELECT * FROM votes WHERE end_time > ?', (current_time,))
        return self.cursor.fetchall()

    def add_transaction(self, sender, recipient, vote_id):
        timestamp = int(time.time())
        self.cursor.execute('INSERT INTO transactions (sender, recipient, vote_id, timestamp) VALUES (?, ?, ?, ?)', 
                            (sender, recipient, vote_id, timestamp))
        self.conn.commit()

    def get_transactions_for_vote(self, vote_id):
        self.cursor.execute('SELECT * FROM transactions WHERE vote_id = ?', (vote_id,))
        return self.cursor.fetchall()

    def get_new_votes(self, last_check_time):
        self.cursor.execute('SELECT * FROM transactions WHERE timestamp > ?', (last_check_time,))
        return self.cursor.fetchall()

    def get_completed_votes(self):
        current_time = int(time.time())
        self.cursor.execute('SELECT * FROM votes WHERE end_time <= ? AND results_announced = 0', (current_time,))
        return self.cursor.fetchall()

    def get_vote_winner(self, vote_id):
        self.cursor.execute('''SELECT recipient, COUNT(*) as vote_count FROM transactions 
                               WHERE vote_id = ? GROUP BY recipient ORDER BY vote_count DESC LIMIT 1''', (vote_id,))
        winner = self.cursor.fetchone()
        return winner[0] if winner else None

    def mark_vote_as_announced(self, vote_id):
        self.cursor.execute('UPDATE votes SET results_announced = 1 WHERE id = ?', (vote_id,))
        self.conn.commit()

    def has_user_voted(self, username, vote_id):
        self.cursor.execute('SELECT * FROM transactions WHERE sender = ? AND vote_id = ?', (username, vote_id))
        return self.cursor.fetchone() is not None
    
    def get_last_transaction(self):
        self.cursor.execute('SELECT * FROM transactions ORDER BY id DESC LIMIT 1')
        return self.cursor.fetchone()

    def get_new_transactions_since(self, last_id):
        self.cursor.execute('SELECT * FROM transactions WHERE id > ?', (last_id,))
        return self.cursor.fetchall()
    
    def get_votes_for_candidate(self, vote_id, candidate):
        self.cursor.execute('SELECT COUNT(*) FROM transactions WHERE vote_id = ? AND recipient = ?', (vote_id, candidate))
        result = self.cursor.fetchone()
        return result[0] if result else 0


