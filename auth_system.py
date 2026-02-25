import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Tuple

class RegistrationSystem:
    """User registration and authentication system with file-based storage."""
    
    def __init__(self, credentials_file: str = "credentials.json"):
        """
        Initialize the registration system.
        
        Args:
            credentials_file: Path to store user credentials (JSON format)
        """
        self.credentials_file = credentials_file
        self.current_user = None
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load existing credentials from file."""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.users = {}
        else:
            self.users = {}
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        with open(self.credentials_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
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
        return username.lower() in self.users
    
    def _validate_username(self, username: str) -> Tuple[bool, str]:
        """
        Validate username requirements.
        
        Returns:
            Tuple of (is_valid, error_message)
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
        self.users[username.lower()] = {
            "username": username,
            "password": self._hash_password(password)
        }
        
        self._save_credentials()
        self.current_user = username
        
        return True, f"Successfully registered and logged in as {username}"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate and login a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, message)
        """
        if not self._username_exists(username):
            return False, "Username not found"
        
        stored_hash = self.users[username.lower()]["password"]
        provided_hash = self._hash_password(password)
        
        if stored_hash != provided_hash:
            return False, "Incorrect password"
        
        self.current_user = username
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


class UserInterface:
    """Command-line interface for the registration system."""
    
    def __init__(self):
        self.auth = RegistrationSystem("credentials.json")
    
    def display_menu(self) -> None:
        """Display main menu options."""
        print("\n" + "=" * 50)
        print("Welcome to Omnium - Trading Software")
        print("=" * 50)
        
        if self.auth.is_logged_in():
            print(f"Logged in as: {self.auth.get_current_user()}")
            print("1. Logout")
            print("2. Access Trading Platform")
            print("3. Exit")
        else:
            print("1. Register")
            print("2. Login")
            print("3. Exit")
        
        print("=" * 50)
    
    def handle_registration(self) -> None:
        """Handle user registration."""
        print("\n--- Registration ---")
        username = input("Enter desired username: ").strip()
        password = input("Enter desired password: ").strip()
        
        success, message = self.auth.register(username, password)
        print(f"\n{'✓' if success else '✗'} {message}")
    
    def handle_login(self) -> None:
        """Handle user login."""
        print("\n--- Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        success, message = self.auth.login(username, password)
        print(f"\n{'✓' if success else '✗'} {message}")
    
    def run(self) -> None:
        """Run the main application loop."""
        while True:
            self.display_menu()
            choice = input("Select an option (1-3): ").strip()
            
            if not self.auth.is_logged_in():
                if choice == "1":
                    self.handle_registration()
                elif choice == "2":
                    self.handle_login()
                elif choice == "3":
                    print("\nGoodbye!")
                    break
                else:
                    print("Invalid option. Please try again.")
            else:
                if choice == "1":
                    self.auth.logout()
                    print("Logged out successfully")
                elif choice == "2":
                    print("\n✓ Access Granted - Launching Trading Platform...")
                    # Add your trading platform code here
                elif choice == "3":
                    self.auth.logout()
                    print("Goodbye!")
                    break
                else:
                    print("Invalid option. Please try again.")


if __name__ == "__main__":
    app = UserInterface()
    app.run()
