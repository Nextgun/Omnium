''' ==========================
auth_system.py - registration and login 
author: Brady Bottari
data created: 
date last modified: 3/6/2026
==========================
'''

import hashlib
import database.db as db
import search as search
from typing import Tuple
from datetime import datetime, timedelta

class RegistrationSystem:
    """User registration and authentication system with MySQL storage."""
    
    def __init__(self):
        """Initialize the registration system."""
        self.current_user = None
        self.max_attempts = 3
        self.lockout_duration = 60  # 1 minute in seconds
        db.initialize_users_tables()
    
    def _initialize_user_lockout(self, username: str) -> None:
        """Initialize lockout tracking for a user."""
        db.initialize_user_lockout(username)
    
    def _is_user_locked_out(self, username: str) -> Tuple[bool, int]:
        """
        Check if user is currently locked out.
        
        Args:
            username: Username to check
            
        Returns:
            Tuple of (is_locked_out, seconds_remaining)
        """
        self._initialize_user_lockout(username)

        lockout_info = db.get_lockout(username)

        if not lockout_info or lockout_info["lockout_until"] is None:
            return False, 0

        lockout_time = lockout_info["lockout_until"]
        current_time = datetime.now()

        if current_time < lockout_time:
            seconds_remaining = int((lockout_time - current_time).total_seconds())
            return True, seconds_remaining
        else:
            # Lockout period has expired, reset attempts
            db.reset_lockout(username)
            return False, 0
    
    def _record_failed_attempt(self, username: str) -> None:
        """
        Record a failed login attempt and apply lockout if necessary.
        
        Args:
            username: Username that failed to login
        """
        self._initialize_user_lockout(username)

        lockout_info = db.get_lockout(username)
        new_attempts = lockout_info["failed_attempts"] + 1

        if new_attempts >= self.max_attempts:
            # Lock the account
            lockout_until = datetime.now() + timedelta(seconds=self.lockout_duration)
            db.increment_failed_attempt(username, lockout_until)
        else:
            db.increment_failed_attempt(username)
    
    def _reset_failed_attempts(self, username: str) -> None:
        """
        Reset failed attempts counter after successful login.
        
        Args:
            username: Username that successfully logged in
        """
        db.reset_lockout(username)
    
    def _get_remaining_attempts(self, username: str) -> int:
        """
        Get remaining login attempts for a user.
        
        Args:
            username: Username to check
            
        Returns:
            Number of remaining attempts
        """
        lockout_info = db.get_lockout(username)

        if not lockout_info:
            return self.max_attempts

        return max(0, self.max_attempts - lockout_info["failed_attempts"])
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return db.get_user(username) is not None
    
    def _validate_username(self, username: str) -> Tuple[bool, str]:
        """
        Validate username requirements.
        
        Returns:
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        

        if not username.isalnum() and '_' not in username:
            return False, "Username can only contain letters, numbers, and underscores"

        
        if self._username_exists(username):

            return False, "Username already exists"
        
        return True, ""

    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password requirements.
        
        Returns:
            Tuple of (is_valid, error_message)

        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        return True, ""
    
    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Args:
            username: Desired username
            password: Desired password
            
        Returns:
            Tuple of (success, message)
        """
        # Validate username
        is_valid, error = self._validate_username(username)
        if not is_valid:
            return False, f"Username validation failed: {error}"
        
        # Validate password
        is_valid, error = self._validate_password(password)
        if not is_valid:
            return False, f"Password validation failed: {error}"
        
        # Store user credentials
        db.create_user(username, username, self._hash_password(password))
        
        # Initialize lockout tracking for new user
        self._initialize_user_lockout(username)
        
        # Automatically log in after registration
        self.current_user = username
        
        return True, f"Successfully registered and logged in as {username}"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate and login a user with attempt limiting.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, message)
        """
        # Initialize lockout tracking if not exists
        self._initialize_user_lockout(username)
        
        # Check if user is locked out
        is_locked, seconds_remaining = self._is_user_locked_out(username)
        if is_locked:
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            return False, f"Account locked. Try again in {minutes}m {seconds}s"
        
        # Check if username exists
        if not self._username_exists(username):
            self._record_failed_attempt(username)
            remaining = self._get_remaining_attempts(username)
            return False, f"Username not found. {remaining} attempts remaining."
        
        # Check password
        user = db.get_user(username)
        stored_hash = user["password"]
        provided_hash = self._hash_password(password)
        
        if stored_hash != provided_hash:
            self._record_failed_attempt(username)
            remaining = self._get_remaining_attempts(username)
            
            if remaining == 0:

                return False, f"Incorrect password. Account locked for 1 minute."

            else:

                return False, f"Incorrect password. {remaining} attempts remaining."
        
        # Successful login
        self._reset_failed_attempts(username)

        self.current_user = user["display_name"]
        return True, f"Successfully logged in as {username}"

    

    def logout(self) -> None:

        """Logout the current user."""
        self.current_user = None

    
    def is_logged_in(self) -> bool:

        """Check if a user is currently logged in."""
        return self.current_user is not None

    
    def get_current_user(self) -> str:
        """Get the currently logged-in user."""

        return self.current_user if self.current_user else "None"


# this is a temporary terminal based interface.
# use for dev and testing.
class UserInterface:
    """Command-line interface for the registration system."""
    
    def __init__(self):
        self.auth = RegistrationSystem()
    
    def display_menu(self) -> None:
        """Display main menu options."""

        print("\n" + "=" * 50)
        print("Welcome to Omnium - Trading Software")
        print("=" * 50)
        
        # options if user is logged in
        if self.auth.is_logged_in():
            # andrew's UI here            
            print(f"Logged in as: {self.auth.get_current_user()}")
            print("1. Logout")
            print("2. Access Trading Platform")
            print("3. Search Securities")
            print("4. Get Security Details")
            print("5. Execute Trade")
            print("6. Update Trading Algorithm")
            print("7. View Status")
            print("0. Exit")

        # options if user is not logged in
        else:
            print("1. Register")
            print("2. Login")
            print("0. Exit")
        
        print("=" * 50)

    def run(self) -> None:
        """Run the main application loop."""
        while True:
            self.display_menu()
            # andrew's UI here
            choice = input("Select an option: ").strip()

            if not self.auth.is_logged_in():

                if choice == "1":
                    self.handle_registration()

                elif choice == "2":
                    self.handle_login()

                elif choice == "0":
                    print("\nGoodbye!")
                    break

                else:
                    print("Invalid option. Please try again.")
        
            else:

                if choice == "1":
                    self.auth.logout()
                    # andrew's UI here
                    print("Logged out successfully")

                # this is the gateway into main menu of omnium interface
                elif choice == "2":
                    # andrew's UI here
                    from stub import stubby_stub
                    print("\nAccess Granted - Launching Trading Platform...")
                    stubby_stub()

                # search companies 
                elif choice == "3":
                    # andrew's UI here                    
                    from search import search_securities
                    search = input("Enter search term:").strip()

                    results = search_securities(search) 
                    if results:
                        for r in results:
                            print(f"  {r['symbol']:<8} {r['name']}")
                    else:
                        "no results."

                # enter exact ticker symbol -> get all details     
                elif choice == "4":
                    from search import get_security_details
                    symbol = input("Type exact symbol here:").strip()
                    results = get_security_details(symbol) 
                    print(results)
                    # andrew's UI here

                elif choice == "5":
                    # andrew's UI here                    
                    print("beep boop this will call run_tick")
                    from trading_logic.orchestrator import run_tick 
                    results = run_tick(1, 1) 
                    # account id = 1, a paper trading account
                    # asset id = 1 which is apple
                    print(results)

                elif choice == "6":
                    print("beep boop this will call update_algorithm")
                    # andrew's UI here

                elif choice == "7":
                    print("beep boop this will call get_status")
                    # andrew's UI here

                # exit
                elif choice == "0":
                    self.auth.logout()
                    print("Goodbye!")
                    # andrew's UI here

                    break

                else:
                    print("Invalid option. Please try again.")
        
    # registration stuff -------------------------------------------------------
    def handle_registration(self) -> None:
        """Handle user registration."""
        print("\n--- Registration ---")
        username = input("Enter desired username: ").strip()
        password = input("Enter desired password: ").strip()
        
        success, message = self.auth.register(username, password)
        print(f"\n{'Good' if success else 'X'} {message}")
    
    def handle_login(self) -> None:
        """Handle user login."""
        print("\n--- Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        success, message = self.auth.login(username, password)
        print(f"\n{'Good' if success else 'X'} {message}")


# to test: run py -m registration.auth_system in terminal
if __name__ == "__main__":
    app = UserInterface()
    app.run()