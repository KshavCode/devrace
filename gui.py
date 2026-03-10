import json
import tkinter as tk
from tkinter import ttk, messagebox
from devrace import DevRace

class AnimatedCheckbox(tk.Canvas):
    """A custom Tkinter checkbox with a smooth scaling animation and custom font."""
    def __init__(self, parent, text, variable, *args, **kwargs):
        # Set background to match your app theme, cursor to hand for better UX
        super().__init__(parent, height=30, width=140, bg="#f5f6fa", highlightthickness=0, cursor="hand2", *args, **kwargs)
        self.variable = variable
        self.text = text
        self.is_animating = False

        # Draw outer box (Outline)
        self.box = self.create_rectangle(2, 6, 20, 24, outline="#7f8fa6", width=2, fill="#ffffff")
        
        # Draw inner box (The "Checked" fill - hidden initially in the center)
        self.inner_box = self.create_rectangle(11, 15, 11, 15, fill="#273c75", outline="")
        
        # Draw the stylized text
        self.create_text(30, 15, text=self.text, anchor="w", fill="#2f3640", font=('Helvetica', 11, 'bold'))

        # Bind clicks on the entire canvas to trigger the toggle
        self.bind("<Button-1>", self.toggle)
        
        # Check initial state and set drawing immediately without animation
        if self.variable.get():
            self.coords(self.inner_box, 6, 10, 16, 20)

    def toggle(self, event=None):
        if self.is_animating: return
        new_state = not self.variable.get()
        self.variable.set(new_state)
        self.animate(new_state)

    def animate(self, state, step=0):
        self.is_animating = True
        max_steps = 8 # Number of animation frames
        
        if step <= max_steps:
            if state: # Expanding (Checking)
                pad = 9 - int((step/max_steps) * 5) # Interpolate padding from 9 down to 4
                self.coords(self.inner_box, 2+pad, 6+pad, 20-pad, 24-pad)
            else: # Shrinking (Unchecking)
                pad = 4 + int((step/max_steps) * 5) # Interpolate padding from 4 up to 9
                self.coords(self.inner_box, 2+pad, 6+pad, 20-pad, 24-pad)
            
            # Call next frame in 15 milliseconds
            self.after(15, self.animate, state, step+1)
        else:
            self.is_animating = False

# ==========================================
# 2. THE GUI CONTROLLER (Tkinter Application)
# ==========================================
class DevRaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DevRace")
        self.geometry("600x650") # Increased height slightly for registration form
        self.configure(bg="#f5f6fa")
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f5f6fa')
        self.style.configure('TLabel', background='#f5f6fa', font=('Helvetica', 14), foreground="#2f3640")
        self.style.configure('Header.TLabel', font=('Helvetica', 18, 'bold'), foreground="#273c75")
        self.style.configure('Timer.TLabel', font=('Helvetica', 18, 'bold'), foreground="#e84118")
        self.style.configure('TButton', font=('Helvetica', 11, 'bold'), padding=6)
        
        self.backend = DevRace()
        self.current_user = None
        
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        # Included RegisterFrame in the loop
        for F in (AuthFrame, RegisterFrame, DashboardFrame, QuizFrame, LeaderboardFrame, EditProfileFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame("AuthFrame")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def logout(self):
        self.current_user = None
        self.show_frame("AuthFrame")

    def on_closing(self):
        self.backend.close_connection()
        self.destroy()


# ==========================================
# 3. APPLICATION SCREENS (Frames)
# ==========================================
class AuthFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.columnconfigure(0, weight=1)
        
        ttk.Label(self, text="Welcome to DevRace", style="Header.TLabel").grid(row=0, column=0, pady=(40, 20))

        login_frame = ttk.LabelFrame(self, text="Login", padding=(20, 10))
        login_frame.grid(row=1, column=0, padx=40, pady=10, sticky="ew")
        
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_log_user = ttk.Entry(login_frame, width=30)
        self.ent_log_user.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_log_pass = ttk.Entry(login_frame, show="*", width=30)
        self.ent_log_pass.grid(row=1, column=1, pady=5, padx=5)

        ttk.Button(login_frame, text="Login", command=self.do_login).grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Separator(self, orient='horizontal').grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        
        ttk.Label(self, text="Don't have an account?").grid(row=3, column=0)
        ttk.Button(self, text="Register New User", command=lambda: controller.show_frame("RegisterFrame")).grid(row=4, column=0, pady=10)

    def do_login(self):
        u, p = self.ent_log_user.get().strip(), self.ent_log_pass.get()
        if self.controller.backend.verify_login(u, p):
            self.controller.current_user = u
            self.ent_log_pass.delete(0, 'end') 
            self.controller.show_frame("DashboardFrame")
        else:
            messagebox.showerror("Error", "Invalid username or password.")


class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Create Account", style="Header.TLabel").pack(pady=(20, 10))

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=5)

        self.vars = {
            "username": tk.StringVar(), "password": tk.StringVar(),
            "fn": tk.StringVar(), "ln": tk.StringVar(),
            "age": tk.StringVar(), "country": tk.StringVar()
        }

        # Form Inputs
        fields = [("Username:", "username", False), ("Password:", "password", True),
                  ("First Name:", "fn", False), ("Last Name:", "ln", False),
                  ("Age:", "age", False), ("Country:", "country", False)]
        
        for i, (label, key, is_pw) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="w", pady=5, padx=5)
            ttk.Entry(form_frame, textvariable=self.vars[key], show="*" if is_pw else "").grid(row=i, column=1, pady=5, padx=5)

        # Topic Selection
        ttk.Label(self, text="Select Your Interests:").pack(pady=(10, 0))
        self.topics_frame = ttk.Frame(self)
        self.topics_frame.pack(pady=5)
        self.topic_vars = {}

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Register", command=self.do_register).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Back to Login", command=lambda: controller.show_frame("AuthFrame")).grid(row=0, column=1, padx=10)

    def on_show(self):
        # Clear fields
        for v in self.vars.values(): v.set("")
        
        # Load topics dynamically
        for widget in self.topics_frame.winfo_children(): widget.destroy()
        self.topic_vars.clear()
        all_topics = self.controller.backend.get_all_topics()
        for i, t in enumerate(all_topics):
            var = tk.BooleanVar(value=False)
            self.topic_vars[t] = var
            AnimatedCheckbox(self.topics_frame, text=t.title(), variable=var).grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)

    def do_register(self):
        u = self.vars["username"].get().strip()
        p = self.vars["password"].get()
        a = self.vars["age"].get()
        
        if not all([u, p, a, self.vars["fn"].get(), self.vars["ln"].get(), self.vars["country"].get()]):
            messagebox.showerror("Error", "Please fill out all fields.")
            return
        if not a.isdigit():
            messagebox.showerror("Error", "Age must be a valid number.")
            return

        success = self.controller.backend.register_user(u, p, self.vars["fn"].get(), self.vars["ln"].get(), a, self.vars["country"].get())
        
        if success:
            selected_topics = [t for t, var in self.topic_vars.items() if var.get()]
            if selected_topics:
                self.controller.backend.update_user_topics(u, selected_topics)
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
            self.controller.show_frame("AuthFrame")
        else:
            messagebox.showerror("Error", "Username already exists or database error.")


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.lbl_welcome = ttk.Label(self, style="Header.TLabel")
        self.lbl_welcome.pack(pady=(30, 10))

        self.card_frame = ttk.Frame(self, relief="solid", borderwidth=1)
        self.card_frame.pack(pady=10, padx=40, fill="x")
        
        self.lbl_rank = ttk.Label(self.card_frame, font=('Helvetica', 12, 'bold'))
        self.lbl_rank.pack(pady=(15, 5))
        self.lbl_xp = ttk.Label(self.card_frame, font=('Helvetica', 11))
        self.lbl_xp.pack(pady=(0, 15))

        menu_frame = ttk.Frame(self)
        menu_frame.pack(pady=20)

        ttk.Button(menu_frame, text="Start Quiz", command=lambda: controller.show_frame("QuizFrame"), width=20).grid(row=0, column=0, pady=5)
        ttk.Button(menu_frame, text="Leaderboard", command=lambda: controller.show_frame("LeaderboardFrame"), width=20).grid(row=1, column=0, pady=5)
        ttk.Button(menu_frame, text="Edit Profile", command=lambda: controller.show_frame("EditProfileFrame"), width=20).grid(row=2, column=0, pady=5)
        ttk.Button(menu_frame, text="Logout", command=controller.logout, width=20).grid(row=3, column=0, pady=25)

    def on_show(self):
        u_name = self.controller.current_user
        if not u_name: return
        user_data = self.controller.backend.retrieve_user(u_name)
        self.lbl_welcome.config(text=f"Welcome back, {user_data['first_name'].title()}!")
        self.lbl_rank.config(text=f"Rank: {user_data['tier'].title()} {user_data['division']}")
        self.lbl_xp.config(text=f"Current XP: {user_data['current_xp']} | Legacy XP: {user_data['legacy_xp']}")


class QuizFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_q = None
        self.selected_ans = tk.StringVar()
        
        # Timer variables
        self.time_left = 15
        self.timer_id = None

        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", pady=10, padx=20)

        self.lbl_topic = ttk.Label(top_bar, font=('Helvetica', 11, 'italic'))
        self.lbl_topic.pack(side="left")
        
        self.lbl_timer = ttk.Label(top_bar, text="Time: 15s", style="Timer.TLabel")
        self.lbl_timer.pack(side="right")

        self.lbl_question = ttk.Label(self, font=('Helvetica', 14, 'bold'), wraplength=500, justify="center")
        self.lbl_question.pack(pady=20, padx=20)

        self.options_frame = ttk.Frame(self)
        self.options_frame.pack(pady=10, fill="x", padx=100)

        self.btn_submit = ttk.Button(self, text="Submit Answer", command=self.check_answer)
        self.btn_submit.pack(pady=20)

        ttk.Button(self, text="Exit Quiz", command=self.exit_quiz).pack(pady=10)

    def on_show(self):
        self.load_question()

    def update_timer(self):
        self.time_left -= 1
        self.lbl_timer.config(text=f"Time: {self.time_left}s")
        
        if self.time_left <= 0:
            # Time's up logic
            self.cancel_timer()
            messagebox.showinfo("Time's Up!", "You ran out of time! Moving to the next question.")
            self.controller.backend.log_answer(self.controller.current_user, self.current_q['question_id'], False)
            self.load_question()
        else:
            self.timer_id = self.after(1000, self.update_timer)

    def cancel_timer(self):
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def load_question(self):
        self.cancel_timer()
        for widget in self.options_frame.winfo_children(): widget.destroy()
        
        self.current_q = self.controller.backend.generate_question(self.controller.current_user)
        
        if not self.current_q:
            self.lbl_question.config(text="No questions available right now.\nPlease check your topics or try again later.")
            self.lbl_topic.config(text="")
            self.lbl_timer.config(text="")
            self.btn_submit.state(['disabled'])
            return

        self.btn_submit.state(['!disabled'])
        self.selected_ans.set("") 
        self.lbl_topic.config(text=f"Topic: {self.current_q['category'].title()} | +{self.current_q['xp_reward']} XP")
        self.lbl_question.config(text=self.current_q['question_text'])

        options = json.loads(self.current_q['options'])
        for opt in options:
            ttk.Radiobutton(self.options_frame, text=opt, variable=self.selected_ans, value=opt).pack(anchor="w", pady=5)

        # Start timer for new question
        self.time_left = 15
        self.lbl_timer.config(text=f"Time: {self.time_left}s")
        self.timer_id = self.after(1000, self.update_timer)

    def check_answer(self):
        ans = self.selected_ans.get()
        if not ans:
            messagebox.showwarning("Warning", "Please select an answer!")
            return

        self.cancel_timer() # Stop the clock while they read the popup!
        u_name = self.controller.current_user
        
        if ans == self.current_q['correct_answer']:
            xp = self.current_q['xp_reward']
            self.controller.backend.update_xp(u_name, xp)
            self.controller.backend.log_answer(u_name, self.current_q['question_id'], True)
            messagebox.showinfo("Correct!", f"Superb! You earned {xp} XP.")
        else:
            self.controller.backend.log_answer(u_name, self.current_q['question_id'], False)
            messagebox.showerror("Wrong!", f"Aiyo, incorrect. The right answer was:\n{self.current_q['correct_answer']}")
        
        self.load_question()

    def exit_quiz(self):
        self.cancel_timer()
        self.controller.show_frame("DashboardFrame")


class LeaderboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Global Leaderboard", style="Header.TLabel").pack(pady=(20, 10))
        columns = ('rank', 'dev', 'tier', 'xp')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=8)
        self.tree.heading('rank', text='#')
        self.tree.heading('dev', text='Developer')
        self.tree.heading('tier', text='Tier')
        self.tree.heading('xp', text='XP')
        self.tree.column('rank', width=40, anchor='center')
        self.tree.column('dev', width=150, anchor='center')
        self.tree.column('tier', width=120, anchor='center')
        self.tree.column('xp', width=80, anchor='center')
        self.tree.pack(pady=10, padx=20, fill="x")
        ttk.Button(self, text="Back", command=lambda: controller.show_frame("DashboardFrame")).pack(pady=20)

    def on_show(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        top_users = self.controller.backend.db.execute("SELECT username, tier, division, current_xp FROM users ORDER BY current_xp DESC LIMIT 10").fetchall()
        for i, row in enumerate(top_users, 1):
            self.tree.insert('', 'end', values=(i, row['username'], f"{row['tier'].title()} {row['division']}", row['current_xp']))


class EditProfileFrame(ttk.Frame):
    # ... [Remains unchanged from previous version] ...
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Edit Profile", style="Header.TLabel").pack(pady=(20, 10))
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)
        self.var_fn, self.var_ln, self.var_age, self.var_country = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(form_frame, text="First Name:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.var_fn).grid(row=0, column=1, pady=5)
        ttk.Label(form_frame, text="Last Name:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.var_ln).grid(row=1, column=1, pady=5)
        ttk.Label(form_frame, text="Age:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.var_age).grid(row=2, column=1, pady=5)
        ttk.Label(form_frame, text="Country:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.var_country).grid(row=3, column=1, pady=5)
        ttk.Label(self, text="Your Topics:").pack(pady=(10, 0))
        self.topics_frame = ttk.Frame(self)
        self.topics_frame.pack(pady=5)
        self.topic_vars = {}
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Save Changes", command=self.save_changes).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=lambda: controller.show_frame("DashboardFrame")).grid(row=0, column=1, padx=10)

    def on_show(self):
        u_name = self.controller.current_user
        user = self.controller.backend.retrieve_user(u_name)
        self.var_fn.set(user['first_name'].title())
        self.var_ln.set(user['last_name'].title())
        self.var_age.set(user['age'])
        self.var_country.set(user['country'].title())
        for widget in self.topics_frame.winfo_children(): widget.destroy()
        self.topic_vars.clear()
        all_topics = self.controller.backend.get_all_topics()
        user_topics = self.controller.backend.get_user_topics(u_name)
        for i, t in enumerate(all_topics):
            var = tk.BooleanVar(value=(t in user_topics))
            self.topic_vars[t] = var
            AnimatedCheckbox(self.topics_frame, text=t.title(), variable=var).grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)

    def save_changes(self):
        u_name = self.controller.current_user
        if not self.var_age.get().isdigit():
            messagebox.showerror("Error", "Age must be a number.")
            return
        success = self.controller.backend.edit_user(u_name, self.var_fn.get(), self.var_ln.get(), self.var_age.get(), self.var_country.get())
        selected_topics = [t for t, var in self.topic_vars.items() if var.get()]
        self.controller.backend.update_user_topics(u_name, selected_topics)
        if success:
            messagebox.showinfo("Success", "Profile and topics updated!")
            self.controller.show_frame("DashboardFrame")
        else:
            messagebox.showerror("Error", "Database error occurred.")

# ==========================================
# 4. RUN THE APP
# ==========================================
if __name__ == "__main__":
    app = DevRaceApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()