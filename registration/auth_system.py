# auth_system.py

import hashlib
import random
import database.db as db
import search as search
from typing import Tuple
from datetime import datetime, timedelta
from email_service import EmailService


class RegistrationSystem:
    """User registration and authentication system with MySQL storage."""

    def __init__(self, email_service: EmailService = None):
        """Initialize the registration system."""
        self.current_user = None
        self.max_attempts = 3
        self.lockout_duration = 60  # seconds
        self.email_service = email_service
        db.initialize_users_tables()

    # lockout helpers -------------------------------------------------------

    def _initialize_user_lockout(self, username: str) -> None:
        """Initialize lockout tracking for a user."""
        db.initialize_user_lockout(username)

    def _is_user_locked_out(self, username: str) -> Tuple[bool, int]:
        """
        Check if user is currently locked out.

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
            db.reset_lockout(username)
            return False, 0

    def _record_failed_attempt(self, username: str) -> None:
        """Record a failed login attempt and apply lockout if necessary."""
        self._initialize_user_lockout(username)
        lockout_info = db.get_lockout(username)
        new_attempts = lockout_info["failed_attempts"] + 1

        if new_attempts >= self.max_attempts:
            lockout_until = datetime.now() + timedelta(seconds=self.lockout_duration)
            db.increment_failed_attempt(username, lockout_until)
        else:
            db.increment_failed_attempt(username)

    def _reset_failed_attempts(self, username: str) -> None:
        """Reset failed attempts counter after successful login."""
        db.reset_lockout(username)

    def _get_remaining_attempts(self, username: str) -> int:
        """Get remaining login attempts for a user."""
        lockout_info = db.get_lockout(username)
        if not lockout_info:
            return self.max_attempts
        return max(0, self.max_attempts - lockout_info["failed_attempts"])

    # password helpers -------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    # validation helpers -----------------------------------------------------

    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return db.get_user(username) is not None

    def _validate_username(self, username: str) -> Tuple[bool, str]:
        """Validate username requirements."""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        if not all(c.isalnum() or c == '_' for c in username):
            return False, "Username can only contain letters, numbers, and underscores"

        if self._username_exists(username):
            return False, "Username already exists"

        return True, ""

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password requirements."""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"

        return True, ""

    def _validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email format and uniqueness."""
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Invalid email format"

        if db.get_user_by_email(email) is not None:
            return False, "Email already registered"

        return True, ""

    # verification code helpers ----------------------------------------------

    @staticmethod
    def _generate_verification_code() -> str:
        """Generate a random 5-digit verification code."""
        return ''.join([str(random.randint(0, 9)) for _ in range(5)])

    def _send_verification_code(self, username: str, email: str) -> Tuple[bool, str]:
        """
        Generate a code, store it in the DB, and email it to the user.

        Returns:
            Tuple of (success, message)
        """
        if not self.email_service:
            return False, "Email service not configured"

        code = self._generate_verification_code()
        expiry = datetime.now() + timedelta(minutes=10)

        if not db.upsert_verification_code(username, code, expiry):
            return False, "Failed to store verification code"

        return self.email_service.send_verification_code(email, code)

    def _check_verification_code(self, username: str, code: str,
                                  max_attempts: int = 3) -> Tuple[bool, str]:
        """
        Validate a submitted verification code against the stored record.

        Deletes the record on success or when attempts are exhausted.

        Returns:
            Tuple of (success, message)
        """
        record = db.get_verification_code(username)

        if not record:
            return False, "No verification code found. Request a new one."

        if datetime.now() > record["expiry"]:
            db.delete_verification_code(username)
            return False, "Verification code expired. Request a new one."

        new_attempts = db.increment_code_attempts(username)

        if new_attempts is None:
            return False, "Internal error checking verification code."

        if code == record["code"]:
            db.delete_verification_code(username)
            return True, "Code verified"

        if new_attempts >= max_attempts:
            db.delete_verification_code(username)
            return False, "Too many incorrect attempts. Request a new code."

        remaining = max_attempts - new_attempts
        return False, f"Incorrect code. {remaining} attempt{'s' if remaining != 1 else ''} remaining."

    # public API -------------------------------------------------------------

    def register(self, username: str, password: str,
                 email: str = None) -> Tuple[bool, str]:
        """
        Register a new user.

        Args:
            username: Desired username
            password: Desired password
            email:    Optional email address for verification / 2FA

        Returns:
            Tuple of (success, message)
        """
        is_valid, error = self._validate_username(username)
        if not is_valid:
            return False, f"Username validation failed: {error}"

        is_valid, error = self._validate_password(password)
        if not is_valid:
            return False, f"Password validation failed: {error}"

        if email:
            is_valid, error = self._validate_email(email)
            if not is_valid:
                return False, f"Email validation failed: {error}"

        db.create_user(username, username, self._hash_password(password), email)
        self._initialize_user_lockout(username)
        self.current_user = username

        return True, f"Successfully registered and logged in as {username}"

    def verify_email_registration(self, username: str) -> Tuple[bool, str]:
        """
        Send a verification code to the email address stored for this user.
        Call this after register() when the user provided an email.

        Returns:
            Tuple of (success, message)
        """
        user = db.get_user(username)
        if not user:
            return False, "User not found"

        if not user.get("email"):
            return False, "No email associated with this account"

        return self._send_verification_code(username, user["email"])

    def verify_code_registration(self, username: str, code: str) -> Tuple[bool, str]:
        """
        Verify the code submitted during registration.
        Marks email_verified = True on success.

        Returns:
            Tuple of (success, message)
        """
        success, message = self._check_verification_code(username, code)

        if success:
            db.set_email_verified(username)
            return True, "Email verified successfully"

        return False, message

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate a user.

        If the user has a verified email and an email_service is configured,
        this returns (False, "2FA_REQUIRED") — the caller must then call
        send_login_2fa() and verify_code_login() to complete sign-in.

        Returns:
            Tuple of (success, message)
        """
        self._initialize_user_lockout(username)

        is_locked, seconds_remaining = self._is_user_locked_out(username)
        if is_locked:
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            return False, f"Account locked. Try again in {minutes}m {seconds}s"

        if not self._username_exists(username):
            self._record_failed_attempt(username)
            remaining = self._get_remaining_attempts(username)
            return False, f"Username not found. {remaining} attempts remaining."

        user = db.get_user(username)
        if self._hash_password(password) != user["password"]:
            self._record_failed_attempt(username)
            remaining = self._get_remaining_attempts(username)
            if remaining == 0:
                return False, "Incorrect password. Account locked for 1 minute."
            return False, f"Incorrect password. {remaining} attempts remaining."

        # Password correct — check whether 2FA is needed.
        if self.email_service and user.get("email") and user.get("email_verified"):
            return False, "2FA_REQUIRED"

        # No 2FA — complete login now.
        self._reset_failed_attempts(username)
        self.current_user = user["display_name"]
        return True, f"Successfully logged in as {username}"

    def send_login_2fa(self, username: str) -> Tuple[bool, str]:
        """
        Send a 2FA code to the verified email on record.
        Call this when login() returns "2FA_REQUIRED".

        Returns:
            Tuple of (success, message)
        """
        user = db.get_user(username)
        if not user or not user.get("email"):
            return False, "No email on record for this account"

        return self._send_verification_code(username, user["email"])

    def verify_code_login(self, username: str, code: str) -> Tuple[bool, str]:
        """
        Verify the 2FA code submitted during login.
        Completes the login on success.

        Returns:
            Tuple of (success, message)
        """
        success, message = self._check_verification_code(username, code)

        if success:
            self._reset_failed_attempts(username)
            user = db.get_user(username)
            self.current_user = user["display_name"]
            return True, f"Successfully logged in as {username}"

        # Count a failed 2FA attempt against the lockout counter too.
        self._record_failed_attempt(username)
        return False, message

    def logout(self) -> None:
        """Logout the current user."""
        self.current_user = None

    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in."""
        return self.current_user is not None

    def get_current_user(self) -> str:
        """Get the currently logged-in user."""
        return self.current_user if self.current_user else "None"


# this is a temporary terminal-based interface.
# use for dev and testing.
class UserInterface:
    """Command-line interface for the registration system."""

    def __init__(self, email_service: EmailService = None):
        self.auth = RegistrationSystem(email_service)
        self.email_service = email_service

    def display_menu(self) -> None:
        """Display main menu options."""
        print("\n" + "=" * 50)
        print("Welcome to Omnium - Trading Software")
        print("=" * 50)

        if self.auth.is_logged_in():
            print(f"Logged in as: {self.auth.get_current_user()}")
            print("1. Logout")
            print("2. Access Trading Platform")
            print("3. Search Securities")
            print("4. Get Security Details")
            print("5. Execute Trade")
            print("6. Update Trading Algorithm")
            print("7. View Status")
            print("0. Exit")
        else:
            print("1. Register")
            print("2. Login")
            print("0. Exit")

        print("=" * 50)

    def run(self) -> None:
        """Run the main application loop."""
        while True:
            self.display_menu()
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
                    print("Logged out successfully")

                elif choice == "2":
                    from stub import stubby_stub
                    print("\nAccess Granted - Launching Trading Platform...")
                    stubby_stub()

                elif choice == "3":
                    from search import search_securities
                    query = input("Enter search term: ").strip()
                    results = search_securities(query)
                    if results:
                        for r in results:
                            print(f"  {r['symbol']:<8} {r['name']}")
                    else:
                        print("No results.")

                elif choice == "4":
                    from search import get_security_details
                    symbol = input("Type exact symbol here: ").strip()
                    print(get_security_details(symbol))

                elif choice == "5":
                    print("beep boop this will call run_tick")
                    from trading_logic.orchestrator import run_tick
                    print(run_tick(1, 1))

                elif choice == "6":
                    print("beep boop this will call update_algorithm")

                elif choice == "7":
                    print("beep boop this will call get_status")

                elif choice == "0":
                    self.auth.logout()
                    print("Goodbye!")
                    break

                else:
                    print("Invalid option. Please try again.")

    # registration -----------------------------------------------------------

    def handle_registration(self) -> None:
        """Handle user registration, including optional email verification."""
        print("\n--- Registration ---")
        username = input("Enter desired username: ").strip()
        password = input("Enter desired password: ").strip()
        email    = input("Enter email address (optional, press Enter to skip): ").strip() or None

        success, message = self.auth.register(username, password, email)
        print(f"\n{'✓' if success else '✗'} {message}")

        if not success:
            return

        # If email was given and email service is configured, send a code.
        if email and self.email_service:
            ok, msg = self.auth.verify_email_registration(username)
            if ok:
                print(f"A verification code has been sent to {email}.")
                self._prompt_verification_code(
                    username,
                    self.auth.verify_code_registration,
                    "Registration verification"
                )
            else:
                print(f"Could not send verification email: {msg}")

    # login ------------------------------------------------------------------

    def handle_login(self) -> None:
        """Handle user login, including 2FA if the account requires it."""
        print("\n--- Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()

        success, message = self.auth.login(username, password)

        if message == "2FA_REQUIRED":
            print("This account has two-factor authentication enabled.")
            ok, msg = self.auth.send_login_2fa(username)
            if not ok:
                print(f"✗ Could not send 2FA code: {msg}")
                return

            user = db.get_user(username)
            print(f"A verification code has been sent to {user['email']}.")
            self._prompt_verification_code(
                username,
                self.auth.verify_code_login,
                "Login verification"
            )
            return

        print(f"\n{'✓' if success else '✗'} {message}")

    # shared helper ----------------------------------------------------------

    def _prompt_verification_code(self, username: str, verify_fn, label: str) -> None:
        """
        Prompt the user to enter a verification code and call verify_fn.

        Args:
            username:  The username being verified
            verify_fn: A callable(username, code) -> Tuple[bool, str]
            label:     Display label shown before the prompt
        """
        for _ in range(3):
            code = input(f"{label} — enter code: ").strip()
            ok, msg = verify_fn(username, code)
            print(f"{'✓' if ok else '✗'} {msg}")
            if ok:
                return
        print("Too many failed attempts.")


# to test: run py -m registration.auth_system in terminal
if __name__ == "__main__":
    email_service = EmailService()
    app = UserInterface(email_service)
    app.run()