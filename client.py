import sqlite3 

class DevRace:
    def __init__(self):
        db_location = "server/drdb.db"
        self.db = sqlite3.connect(db_location)
    def check_user(self, username):
        user_info = self.db.execute("SELECT * FROM users WHERE username=?;", (username,)).fetchone()
        return False if not user_info else True
    def register_user(self, username, first_name, last_name, dob, country):
        user_info = self.db.execute("SELECT * FROM users WHERE username=?;", (username,)).fetchone()
        return False if not user_info else True
    
    def close_connection(self):
        try:
            self.db.close()
            return True
        except:
            return False

if __name__ == "__main__":
    a = DevRace()
    print(a.check_user("test"))
    