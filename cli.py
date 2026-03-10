from devrace import DevRace
import json
import time
import asyncio
import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    
console = Console()
obj = DevRace()

# --- NEW ASYNC QUIZ LOOP ---
async def quiz_loop(username):
    """Handles the infinite question generation and the 15-second timer."""
    while True:
        clear_screen()
        q = obj.generate_question(username)
        
        if not q:
            console.print("[yellow]No questions available right now! Check your topics.[/yellow]")
            time.sleep(2)
            break

        options = json.loads(q['options'])
        # Append the Exit button directly into the multiple-choice list
        options.append(Choice(title="[ ❌ Exit Quiz ]", value="EXIT"))
        
        # Display Header
        console.print(f"[bold cyan]Topic:[/] {q['category'].title()}  |  [bold red]Timer: 15 Seconds[/]")
        
        try:
            # Using wait_for to enforce the 15-second timeout on the questionary prompt!
            answer = await asyncio.wait_for(
                questionary.select(f"\n{q['question_text']}", choices=options).ask_async(),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            answer = "TIMEOUT"

        # Handle the results
        if answer == "EXIT" or answer is None: # None handles keyboard interrupts (Ctrl+C)
            break
            
        elif answer == "TIMEOUT":
            console.print("\n[bold red]⏰ Time's Up![/] You took longer than 15 seconds.")
            obj.log_answer(username, q['question_id'], False)
            time.sleep(2)
            
        elif answer == q['correct_answer']:
            console.print(f"\n[bold green]Correct! +{q['xp_reward']} XP[/]")
            obj.update_xp(username, q['xp_reward'])
            obj.log_answer(username, q['question_id'], True)
            time.sleep(1.5)
            
        else:
            console.print(f"\n[bold red]Wrong![/] The correct answer was: [green]{q['correct_answer']}[/green]")
            obj.log_answer(username, q['question_id'], False)
            time.sleep(2)


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
            # Fire up the asynchronous quiz loop
            asyncio.run(quiz_loop(username))
            
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