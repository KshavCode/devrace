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

    def check_user(self, username):
        user_info = self.db.execute("SELECT * FROM users WHERE username=?;", (username.lower(),)).fetchone()
        return bool(user_info)

    def register_user(self, username, first_name, last_name, age, location):
        if self.check_user(username):
            print("User already exists!")
            return False
        try:
            self.db.execute("""
                INSERT INTO users (username, first_name, last_name, age, location, current_xp, tier, division)
                VALUES (?, ?, ?, ?, ?, 0, 'bronze', 3);
            """, (username.lower(), first_name, last_name, age, location))
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
            
        current_tier, current_div = "bronze", 3
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
    
    def close_connection(self):
        try:
            self.db.close()
            return True
        except:
            return False

if __name__ == "__main__":
    a = DevRace()
    a.global_season_reset()
    status = a.update_xp("test", 10)
    print(f"Update: {status}")