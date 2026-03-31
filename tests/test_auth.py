import pytest


def _make_fake_db():
    users = {}
    lockouts = {}
    verification_codes = {}

    def initialize_users_tables():
        return None

    def create_user(username, display_name, password_hash, email=None):
        users[username.lower()] = {
            "username": username.lower(),
            "display_name": display_name,
            "password": password_hash,
            "email": email,
            "email_verified": False,
        }
        return True

    def get_user(username):
        return users.get(username.lower())

    def get_user_by_email(email):
        for u in users.values():
            if u.get("email") and u["email"].lower() == email.lower():
                return u
        return None

    def set_email_verified(username, verified=True):
        u = users.get(username.lower())
        if not u:
            return False
        u["email_verified"] = True if verified else False
        return True

    def initialize_user_lockout(username):
        if username.lower() not in lockouts:
            lockouts[username.lower()] = {"failed_attempts": 0, "lockout_until": None}

    def get_lockout(username):
        return lockouts.get(username.lower())

    def increment_failed_attempt(username, lockout_until=None):
        initialize_user_lockout(username)
        r = lockouts[username.lower()]
        r["failed_attempts"] += 1
        if lockout_until is not None:
            r["lockout_until"] = lockout_until

    def reset_lockout(username):
        initialize_user_lockout(username)
        r = lockouts[username.lower()]
        r["failed_attempts"] = 0
        r["lockout_until"] = None

    def upsert_verification_code(username, code, expiry):
        verification_codes[username.lower()] = {"username": username.lower(), "code": code, "expiry": expiry, "attempts": 0}
        return True

    def get_verification_code(username):
        return verification_codes.get(username.lower())

    def increment_code_attempts(username):
        rec = verification_codes.get(username.lower())
        if not rec:
            return None
        rec["attempts"] += 1
        return rec["attempts"]

    def delete_verification_code(username):
        verification_codes.pop(username.lower(), None)

    return {
        "initialize_users_tables": initialize_users_tables,
        "create_user": create_user,
        "get_user": get_user,
        "get_user_by_email": get_user_by_email,
        "set_email_verified": set_email_verified,
        "initialize_user_lockout": initialize_user_lockout,
        "get_lockout": get_lockout,
        "increment_failed_attempt": increment_failed_attempt,
        "reset_lockout": reset_lockout,
        "upsert_verification_code": upsert_verification_code,
        "get_verification_code": get_verification_code,
        "increment_code_attempts": increment_code_attempts,
        "delete_verification_code": delete_verification_code,
    }


class FakeEmailService:
    def __init__(self):
        self.sent = []

    def send_verification_code(self, recipient_email, verification_code):
        self.sent.append((recipient_email, verification_code))
        return True, "Verification code sent to email"


def _patch_db_functions(monkeypatch, fake_db):
    import database.db as db

    for name, fn in fake_db.items():
        monkeypatch.setattr(db, name, fn)


def test_register_and_login(monkeypatch):
    fake_db = _make_fake_db()
    _patch_db_functions(monkeypatch, fake_db)

    from registration.auth_system import RegistrationSystem

    auth = RegistrationSystem()

    # register a new user (no email)
    ok, msg = auth.register("Alice", "Password1", None)
    assert ok, msg
    assert auth.is_logged_in()
    assert auth.get_current_user() == "Alice"

    # logout then login with correct password
    auth.logout()
    ok, msg = auth.login("Alice", "Password1")
    assert ok, msg
    assert auth.get_current_user() == "Alice"

    # login with wrong password
    auth.logout()
    ok, msg = auth.login("Alice", "WrongPass")
    assert not ok
    assert "Incorrect password" in msg or "attempts" in msg


def test_login_requires_2fa(monkeypatch):
    fake_db = _make_fake_db()
    _patch_db_functions(monkeypatch, fake_db)

    from registration.auth_system import RegistrationSystem

    # register with email
    email = "bob@example.com"
    auth = RegistrationSystem(email_service=FakeEmailService())
    ok, msg = auth.register("Bob", "Password1", email)
    assert ok

    # mark email verified in fake DB
    import database.db as db
    db.set_email_verified("Bob", True)

    # now login should require 2FA because email_service is configured
    auth.logout()
    ok, msg = auth.login("Bob", "Password1")
    assert not ok
    assert msg == "2FA_REQUIRED"
