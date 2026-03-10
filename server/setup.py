import sqlite3
import json
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with open("questions.json") as f:
    questions_data = json.load(f)
with open("topics.json") as f:
    topics_data = json.load(f)

def setup_and_seed():
    # 1. Connect to SQLite
    conn = sqlite3.connect('drdb.db')
    cursor = conn.cursor()

    # Enforce Foreign Key constraints (SQLite disables this by default!)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. Create the tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,       -- MANDATORY: For JWT Mobile Auth
            first_name TEXT,
            last_name TEXT,
            age INTEGER,
            country TEXT,
            legacy_xp INTEGER DEFAULT 0,       -- MANDATORY: All-time career XP
            current_xp INTEGER DEFAULT 0,      -- Seasonal XP (resets)
            tier TEXT DEFAULT 'novice',
            division INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            season_name TEXT,
            rank_name TEXT,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT UNIQUE
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_topics (
            username TEXT NOT NULL,
            topic_id INTEGER,
            PRIMARY KEY (username, topic_id),
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            subcategory TEXT,
            difficulty_tier TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,          
            correct_answer TEXT NOT NULL,
            xp_reward INTEGER DEFAULT 50,
            is_active BOOLEAN DEFAULT 1        -- Allows 'soft deleting' bad questions
        )
    ''')

    # MANDATORY: Tracks answered questions so users don't get duplicates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
        )
    ''')

    # 3. Clear existing data for a clean slate
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM topics")

    # 4. Insert Topics FIRST (Crucial for Foreign Keys)
    for item in topics_data:
        cursor.execute('''
            INSERT OR IGNORE INTO topics (topic_name) VALUES (?)
        ''', (item['name'].lower(),))

    # 5. Insert Questions
    for item in questions_data:
        options_string = json.dumps(item['options'])
        cursor.execute('''
            INSERT INTO questions (
                category, subcategory, difficulty_tier, 
                question_text, options, correct_answer
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item['category'].lower(), 
            item['subcategory'].lower(), 
            item['difficulty'].lower(), 
            item['question'], 
            options_string, 
            item['answer']
        ))

    # 6. Insert Test User (Now requires a dummy password hash)
    # Using 'pbkdf2:sha256...' as a placeholder for a hashed "password123"
    dummy_hash = "pbkdf2:sha256:290000$dummyhash$placeholder"
    cursor.execute('''
        INSERT OR IGNORE INTO users (
            username, password_hash, first_name, last_name, 
            age, country, tier, division) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("test", dummy_hash, "abc", "xyz", 18, "india", "novice", 3)
    )
    
    # 7. Insert User Topics (Ensure these IDs actually exist in topics.json!)
    interests = [1, 2, 3] 
    for interest in interests:
        cursor.execute('''
            INSERT OR IGNORE INTO users_topics (username, topic_id) 
            VALUES (?, ?)
            ''', ("test", interest)
        )

    # 8. Commit and close
    conn.commit()
    conn.close()
    print("Database optimised and seeded successfully for mobile infrastructure!")

if __name__ == "__main__":
    setup_and_seed()