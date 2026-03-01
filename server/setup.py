import sqlite3
import json

with open("questions.json") as f:
    questions_data = json.load(f)
with open("ranks.json") as f:
    ranks_data = json.load(f)

def setup_and_seed():
    # 1. Connect to SQLite (creates quiz.db if it doesn't exist)
    conn = sqlite3.connect('drdb.db')
    cursor = conn.cursor()

    # 2. Create the table based on our finalized structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ranks (
            rank_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank_name TEXT UNIQUE NOT NULL,
            xp_threshold INT NOT NULL
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            age INT,
            country TEXT,
            current_xp INT DEFAULT 0,
            rank_id INT DEFAULT 1,
            FOREIGN KEY (rank_id) REFERENCES ranks(rank_id)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            season_name TEXT,
            final_rank_id INTEGER,
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (final_rank_id) REFERENCES ranks(rank_id)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            subcategory TEXT,
            difficulty_tier TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,          -- Stored as JSON string
            correct_answer TEXT NOT NULL,
            xp_reward INTEGER DEFAULT 50
        )
    ''')

    # 3. Clear existing questions to avoid duplicates during testing
    cursor.execute("DELETE FROM questions")

    cursor.execute('''
        INSERT INTO users (
            username, first_name, last_name, 
            age, country) 
            VALUES (?, ?, ?, ?, ?)
        ''', ("test", "abc", "xyz", 18, "india")
    )

    # 4. Insert the data
    for item in questions_data:
        # Convert the options list ['a', 'b'] into a string "['a', 'b']"
        options_string = json.dumps(item['options'])
        
        cursor.execute('''
            INSERT INTO questions (
                category, subcategory, difficulty_tier, 
                question_text, options, correct_answer
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item['category'], 
            item['subcategory'], 
            item['difficulty'], 
            item['question'], 
            options_string, 
            item['answer']
        ))
        
    for item in ranks_data:
        cursor.execute('''
            INSERT INTO ranks (
                rank_name, xp_threshold
            ) VALUES (?, ?)
        ''', (
            item["rank_name"], item["xp_threshold"]
        ))

    # 5. Commit and close
    conn.commit()
    conn.close()
    print(f"Success!")

if __name__ == "__main__":
    setup_and_seed()