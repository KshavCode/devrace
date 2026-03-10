import sqlite3 
import bcrypt

class DevRace:
    def __init__(self):
        db_location = "server/drdb.db" # Make sure to run setup.py first!
        self.db = sqlite3.connect(db_location)
        self.db.row_factory = sqlite3.Row  
        
        self.THRESHOLDS = [
            (0, "novice", 3), (500, "novice", 2), (1000, "novice", 1),
            (2000, "apprentice", 3), (3000, "apprentice", 2), (4000, "apprentice", 1),
            (6000, "skilled", 4), (8000, "skilled", 3), (10000, "skilled", 2), (12000, "skilled", 1),
            (16000, "pro", 4), (20000, "pro", 3), (24000, "pro", 2), (28000, "pro", 1),
            (38000, "legend", 1)
        ]

    def retrieve_user(self, username):
        return self.db.execute("SELECT * FROM users WHERE username=?;", (username.lower(),)).fetchone()

    def verify_login(self, username, plain_password):
        user = self.retrieve_user(username)
        if not user:
            return False
        password_bytes = plain_password[:72].encode('utf-8')
        stored_hash_bytes = user['password_hash'].encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)

    def register_user(self, username, password, first_name, last_name, age, country):
        if self.retrieve_user(username):
            return False
        try:
            password_bytes = password[:72].encode('utf-8')
            hashed_pw = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            
            self.db.execute("""
                INSERT INTO users (username, password_hash, first_name, last_name, age, country, current_xp, legacy_xp, tier, division)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'novice', 3);
            """, (username.lower(), hashed_pw, first_name.lower(), last_name.lower(), int(age), country.lower()))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Registration Error: {e}")
            return False

    def get_rank_info(self, xp):
        if xp >= 38000:
            return "legend", ((xp - 38000) // 10000) + 1
            
        current_tier, current_div = "novice", 3
        for threshold, tier, div in self.THRESHOLDS:
            if xp >= threshold:
                current_tier, current_div = tier, div
            else:
                break
        return current_tier, current_div

    def update_xp(self, username, gained_xp):
        user = self.db.execute("SELECT current_xp, legacy_xp FROM users WHERE username=?;", (username.lower(),)).fetchone()
        if not user: return None

        new_xp = user['current_xp'] + gained_xp
        new_legacy = user['legacy_xp'] + gained_xp
        new_tier, new_div = self.get_rank_info(new_xp)

        self.db.execute("""
            UPDATE users SET current_xp = ?, legacy_xp = ?, tier = ?, division = ? WHERE username = ?;
        """, (new_xp, new_legacy, new_tier, new_div, username.lower()))
        self.db.commit()
        return {"xp": new_xp, "tier": new_tier, "division": new_div}
    
    def generate_question(self, username):
        user_info = self.retrieve_user(username)
        rank = user_info["tier"]
        topic_names = self.get_user_topics(username)

        if not topic_names:
            question = self.db.execute("""
                SELECT * FROM questions 
                WHERE difficulty_tier = ? AND question_id NOT IN (SELECT question_id FROM user_answers WHERE username = ?)
                ORDER BY RANDOM() LIMIT 1
            """, (rank, username.lower())).fetchone()
        else:
            placeholders = ', '.join(['?'] * len(topic_names))
            query = f"""
                SELECT * FROM questions 
                WHERE category IN ({placeholders}) AND difficulty_tier = ? AND question_id NOT IN (SELECT question_id FROM user_answers WHERE username = ?)
                ORDER BY RANDOM() LIMIT 1
            """
            question = self.db.execute(query, (*topic_names, rank, username.lower())).fetchone()
        return question
    
    def log_answer(self, username, question_id, is_correct):
        self.db.execute("INSERT INTO user_answers (username, question_id, is_correct) VALUES (?, ?, ?)", (username.lower(), question_id, is_correct))
        self.db.commit()
    
    def edit_user(self, username, first_name, last_name, age, country):
        try:
            self.db.execute("""
                UPDATE users SET first_name = ?, last_name = ?, age = ?, country = ? WHERE username = ?;
            """, (first_name.lower(), last_name.lower(), int(age), country.lower(), username.lower()))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            return False

    # --- NEW TOPIC MANAGEMENT METHODS ---
    def get_all_topics(self):
        return [row['topic_name'] for row in self.db.execute("SELECT topic_name FROM topics").fetchall()]

    def get_user_topics(self, username):
        cursor = self.db.execute("""
            SELECT t.topic_name FROM topics t
            JOIN users_topics ut ON t.topic_id = ut.topic_id
            WHERE ut.username = ?
        """, (username.lower(),))
        return [row[0] for row in cursor.fetchall()]

    def update_user_topics(self, username, selected_topics):
        """Wipes old topics and inserts the newly selected ones."""
        self.db.execute("DELETE FROM users_topics WHERE username = ?", (username.lower(),))
        for t_name in selected_topics:
            t_id = self.db.execute("SELECT topic_id FROM topics WHERE topic_name=?", (t_name,)).fetchone()['topic_id']
            self.db.execute("INSERT INTO users_topics (username, topic_id) VALUES (?, ?)", (username.lower(), t_id))
        self.db.commit()

    def close_connection(self):
        try:
            self.db.close()
            return True
        except:
            return False