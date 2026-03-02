import sqlite3

class DevRace:
    def __init__(self):
        # Ensure the directory exists or just use 'drdb.db' if in the same folder
        db_location = "server/drdb.db"
        self.db = sqlite3.connect(db_location)
        self.db.row_factory = sqlite3.Row  # Allows accessing columns by name
        self.THRESHOLDS = [
            (0, "novice", 3), (500, "novice", 2), (1000, "novice", 1),
            (2000, "apperentice", 3), (3000, "apprentice", 2), (4000, "apperentice", 1),
            (6000, "skilled", 4), (8000, "skilled", 3), (10000, "skilled", 2), (12000, "skilled", 1),
            (16000, "pro", 4), (20000, "pro", 3), (24000, "pro", 2), (28000, "pro", 1),
            (38000, "legend", 1)
        ]

    def retrieve_user(self, username):
        user_info = self.db.execute("SELECT * FROM users WHERE username=?;", (username.lower(),)).fetchone()
        return user_info

    def register_user(self, username, first_name, last_name, age, country):
        if self.retrieve_user(username):
            print("User already exists!")
            return False
        try:
            self.db.execute("""
                INSERT INTO users (username, first_name, last_name, age, country, current_xp, tier, division)
                VALUES (?, ?, ?, ?, ?, 0, 'novice', 3);
            """, (username.lower(), first_name, last_name, age, country))
            self.db.commit()
            return True
        except sqlite3.Error as e:
            print(f"Registration Error: {e}")
            return False

    def get_rank_info(self, xp):
        """Helper to calculate tier/division based on XP"""
        if xp >= 38000:
            level = ((xp - 38000) // 10000) + 1
            return "legend", level
            
        current_tier, current_div = "novice", 3
        for threshold, tier, div in self.THRESHOLDS:
            if xp >= threshold:
                current_tier, current_div = tier, div
            else:
                break
        return current_tier, current_div

    def update_xp(self, username, gained_xp):
        """Adds XP and updates the Rank automatically"""
        user = self.db.execute("SELECT current_xp FROM users WHERE username=?;", (username.lower(),)).fetchone()
        if not user:
            return None

        new_xp = user['current_xp'] + gained_xp
        new_tier, new_div = self.get_rank_info(new_xp)

        self.db.execute("""
            UPDATE users 
            SET current_xp = ?, tier = ?, division = ? 
            WHERE username = ?;
        """, (new_xp, new_tier, new_div, username.lower()))
        self.db.commit()
        return {"xp": new_xp, "tier": new_tier, "division": new_div}
    
    def global_season_reset(self):
        """Resets every user in the database for the new season."""
        # 1. Fetch all users
        users = self.db.execute("SELECT username, current_xp, tier FROM users;").fetchall()

        # 2. Define the corrected rank names and bonuses
        bonuses = {
            "novice": 0, 
            "apprentice": 30, 
            "expert": 60, 
            "skilled": 90, 
            "pro": 120, 
            "legend": 150
        }

        reset_report = []

        for user in users:
            username = user['username']
            old_xp = user['current_xp']

            # Get bonus based on tier (handling potential typos with .get)
            bonus = bonuses.get(user['tier'].lower(), 0)

            # Calculate New XP (30% retention + bonus)
            new_xp = int(old_xp * 0.30) + bonus

            # Recalculate the new starting rank using your existing helper
            new_tier, new_div = self.get_rank_info(new_xp)

            # Update the specific user
            self.db.execute("""
                UPDATE users 
                SET current_xp = ?, tier = ?, division = ? 
                WHERE username = ?;
            """, (new_xp, new_tier, new_div, username))

            reset_report.append({
                "user": username,
                "from": f"{user['tier']} {old_xp}xp",
                "to": f"{new_tier} {new_div} ({new_xp}xp)"
            })

        # 3. Commit all changes at once
        self.db.commit()
        return reset_report
    
    def generate_question(self, username):
        # 1. Get user tier
        user_info = self.retrieve_user(username)
        rank = user_info["tier"]

        # 2. Get the actual names of the topics the user follows
        cursor = self.db.execute("""
            SELECT t.topic_name 
            FROM topics t
            JOIN users_topics ut ON t.topic_id = ut.topic_id
            WHERE ut.username = ?
        """, (username.lower(),))

        # Flatten the list of tuples: [('frontend',), ('backend',)] -> ['frontend', 'backend']
        topic_names = [row[0] for row in cursor.fetchall()]

        # 3. Handle the "No Topics Selected"
        if not topic_names:
            # Show them everything from their tier
            questions = self.db.execute(
                "SELECT * FROM questions WHERE difficulty_tier = ? ORDER BY RANDOM() LIMIT 1", 
                (rank,)
            ).fetchone()
        else:
            # 4. Dynamic query to handle the list of topics
            # We need to create a string like (?, ?, ?) based on the number of topics
            placeholders = ', '.join(['?'] * len(topic_names))
            query = f"""
                SELECT * FROM questions 
                WHERE category IN ({placeholders}) 
                AND difficulty_tier = ? 
                ORDER BY RANDOM() LIMIT 1
            """
            # We combine the topic list and the rank into one tuple for the execution
            question = self.db.execute(query, (*topic_names, rank)).fetchone()
        return question
    
    def close_connection(self):
        try:
            self.db.close()
            return True
        except:
            return False

if __name__ == "__main__":
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    import json
    import time

    console = Console()
    obj = DevRace()

    def main_loop(username):
        while True:
            user = obj.retrieve_user(username)
            
            # 1. Display Header with Rich
            profile_text = f"[bold cyan]Rank:[/] {user['tier'].upper()} {user['division']}  |  [bold green]XP:[/] {user['current_xp']}"
            console.print(Panel(profile_text, title=f"Welcome, {user['first_name']}", subtitle="DevRace Terminal v1.0"))

            # 2. Main Menu Options
            choice = questionary.select(
                "Menu:",
                choices=["Start Quiz", "Leaderboard", "Profile Info", "Exit"]
            ).ask()

            if choice == "Start Quiz":
                q = obj.generate_question(username)
                if not q:
                    console.print("[yellow]No questions found for your topics/rank. Add more topics![/]")
                    continue

                # Display Question
                options = json.loads(q['options'])
                answer = questionary.select(
                    f"\n[bold]{q['question_text']}[/]",
                    choices=options
                ).ask()

                if answer == q['correct_answer']:
                    console.print("[bold green]Correct! +50 XP[/]")
                    obj.update_xp(username, 50)
                else:
                    console.print(f"[bold red]Wrong![/] The correct answer was: {q['correct_answer']}")

            elif choice == "Leaderboard":
                # Simple Leaderboard Query
                top_users = obj.db.execute("SELECT username, tier, division, current_xp FROM users ORDER BY current_xp DESC LIMIT 5").fetchall()
                table = Table(title="Global Leaderboard")
                table.add_column("Rank", justify="right", style="cyan")
                table.add_column("Dev", style="magenta")
                table.add_column("Tier")
                table.add_column("XP", justify="right", style="green")

                for i, row in enumerate(top_users, 1):
                    table.add_row(str(i), row['username'], f"{row['tier']} {row['division']}", str(row['current_xp']))
                console.print(table)

            elif choice == "Profile Info":
                profile_info_text = f"[bold cyan]Username:[/] {username}\n[bold cyan]Name:[/] {user["first_name"].title()} {user["last_name"].title()}\n[bold cyan]Age:[/] {user["age"]}\n[bold cyan]Country:[/] {user["country"]}"
                console.print(Panel(profile_info_text, title="Profile Information"))
                time.sleep(1)

            elif choice == "Exit":
                break

    # --- Initial Entry ---
    step = questionary.select("Welcome to DevRace:", choices=["Login", "Register", "Exit"]).ask()

    if step == "Register":
        username = questionary.text("Enter username:").ask()
        if obj.retrieve_user(username):
            console.print("[red]Username already exists![/]")
        else:
            fn = questionary.text("First Name:").ask()
            ln = questionary.text("Last Name:").ask()
            age = questionary.text("Age:").ask()
            country = questionary.text("Country:").ask()
            
            if obj.register_user(username, fn, ln, int(age), country):
                console.print("[green]Registration successful![/]")
                # Let them pick topics immediately
                all_topics = [row[0] for row in obj.db.execute("SELECT topic_name FROM topics").fetchall()]
                if all_topics:
                    selected = questionary.checkbox("Select your interests:", choices=all_topics).ask()
                    for t_name in selected:
                        t_id = obj.db.execute("SELECT topic_id FROM topics WHERE topic_name=?", (t_name,)).fetchone()[0]
                        obj.db.execute("INSERT INTO users_topics (username, topic_id) VALUES (?, ?)", (username.lower(), t_id))
                    obj.db.commit()
                main_loop(username)

    elif step == "Login":
        username = questionary.text("Username:").ask()
        if obj.retrieve_user(username):
            main_loop(username)
        else:
            console.print("[red]User not found.[/]")

    obj.close_connection()