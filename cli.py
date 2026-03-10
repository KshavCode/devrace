import sqlite3
import json
import time
import bcrypt
import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import os

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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    console = Console()
    obj = DevRace()

    def main_loop(username):
        while True:
            clear_screen()
            user = obj.retrieve_user(username)
            
            profile_text = f"[bold cyan]Rank:[/] {user['tier'].title()} {user['division']}  |  [bold green]XP:[/] {user['current_xp']}"
            console.print(Panel(profile_text, title=f"Welcome, {user['first_name'].title()}", subtitle="DevRace Terminal v1.0", border_style="blue"))

            choice = questionary.select(
                "Main Menu:",
                choices=["Start Quiz", "Leaderboard", "Edit Details", "Profile Info", "Logout"]
            ).ask()

            if not choice or choice == "Logout":
                break

            if choice == "Start Quiz":
                q = obj.generate_question(username)
                if not q:
                    console.print("[yellow]You have answered all available questions for your rank and topics! Waiting for new content...[/]")
                    time.sleep(2)
                    continue

                options = json.loads(q['options'])
                answer = questionary.select(f"\n{q['question_text']}", choices=options).ask()

                if answer == q['correct_answer']:
                    console.print(f"[bold green]Correct! +{q['xp_reward']} XP[/]")
                    obj.update_xp(username, q['xp_reward'])
                    obj.log_answer(username, q['question_id'], True)
                else:
                    console.print(f"[bold red]Wrong![/] The correct answer was: {q['correct_answer']}")
                    obj.log_answer(username, q['question_id'], False)
                time.sleep(1.5)

            elif choice == "Leaderboard":
                top_users = obj.db.execute("SELECT username, tier, division, current_xp FROM users ORDER BY current_xp DESC LIMIT 5").fetchall()
                table = Table(title="Global Leaderboard", border_style="magenta")
                table.add_column("Rank", justify="right", style="cyan")
                table.add_column("Dev", style="magenta")
                table.add_column("Tier")
                table.add_column("XP", justify="right", style="green")

                for i, row in enumerate(top_users, 1):
                    table.add_row(str(i), row['username'], f"{row['tier'].title()} {row['division']}", str(row['current_xp']))
                console.print(table)
                questionary.press_any_key_to_continue().ask()

            elif choice == "Edit Details":
                sub_choice = questionary.select(
                    "What would you like to edit?",
                    choices=["Change Topics", "Change Personal Details", "Back"]
                ).ask()
                
                if sub_choice == "Change Topics":
                    all_topics = obj.get_all_topics()
                    current_topics = obj.get_user_topics(username)
                    
                    # Create Choice objects so previously selected topics are pre-checked!
                    topic_choices = [Choice(title=t, checked=(t in current_topics)) for t in all_topics]
                    
                    if topic_choices:
                        selected = questionary.checkbox("Update your interests (Space to select, Enter to confirm):", choices=topic_choices).ask()
                        if selected is not None:
                            obj.update_user_topics(username, selected)
                            console.print("[green]Topics updated successfully![/green]")
                            time.sleep(1)

                elif sub_choice == "Change Personal Details":
                    console.print("\n[bold yellow]--- Edit Your Profile ---[/]")
                    console.print("[cyan]Press Enter to keep your current details.[/cyan]")
                    
                    # Age validation logic
                    def validate_age(text):
                        return True if text.isdigit() and int(text) > 0 else "Please enter a valid age (numbers only)."

                    new_fn = questionary.text("First Name:", default=str(user['first_name']).title()).ask()
                    new_ln = questionary.text("Last Name:", default=str(user['last_name']).title()).ask()
                    new_age = questionary.text("Age:", default=str(user['age']), validate=validate_age).ask()
                    new_country = questionary.text("Country:", default=str(user['country']).title()).ask()
                    
                    if obj.edit_user(username, new_fn, new_ln, new_age, new_country):
                        console.print("[bold green]Profile updated pakka! Superb.[/bold green]\n")
                    else:
                        console.print("[bold red]Aiyo, something went wrong saving your details.[/bold red]\n")
                    time.sleep(1)

            elif choice == "Profile Info":
                user_topics = obj.get_user_topics(username)
                topics_str = ", ".join(user_topics).title() if user_topics else "None selected"
                
                profile_info_text = (
                    f"[bold cyan]Username:[/] {user['username']}\n"
                    f"[bold cyan]Name:[/] {user['first_name'].title()} {user['last_name'].title()}\n"
                    f"[bold cyan]Age:[/] {user['age']}\n"
                    f"[bold cyan]Country:[/] {user['country'].title()}\n"
                    f"[bold cyan]Topics:[/] {topics_str}"
                )
                console.print(Panel(profile_info_text, title="Profile Information", border_style="cyan"))
                questionary.press_any_key_to_continue().ask()

    # --- Initial Entry ---
    clear_screen()
    step = questionary.select("Welcome to DevRace:", choices=["Login", "Register", "Exit"]).ask()

    if step == "Register":
        username = questionary.text("Enter username:").ask()
        if obj.retrieve_user(username):
            console.print("[red]Username already exists![/red]")
        else:
            password = questionary.password("Enter password:").ask()
            fn = questionary.text("First Name:").ask()
            ln = questionary.text("Last Name:").ask()
            age = questionary.text("Age:", validate=lambda text: True if text.isdigit() and int(text) > 0 else "Enter a valid number").ask()
            country = questionary.text("Country:").ask()
            
            if obj.register_user(username, password, fn, ln, age, country):
                console.print("[green]Registration successful![/green]")
                all_topics = obj.get_all_topics()
                if all_topics:
                    selected = questionary.checkbox("Select your interests:", choices=all_topics).ask()
                    if selected:
                        obj.update_user_topics(username, selected)
                main_loop(username)

    elif step == "Login":
        username = questionary.text("Username:").ask()
        password = questionary.password("Password:").ask()
        
        if obj.verify_login(username, password):
            main_loop(username)
        else:
            console.print("[red]Invalid username or password.[/red]")

    obj.close_connection()