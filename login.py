"""Authentication and user management module."""

from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import (
    DATA_DIR,
    ensure_file,
    get_timestamp,
    print_error,
    print_info,
    print_success,
    read_json,
    validate_text,
    write_json,
)

USERS_FILE = DATA_DIR / "users.json"


class AuthenticationService:
    """Handle user registration, login, and session management."""

    def __init__(self, storage_file: Path | None = None) -> None:
        self.storage_file = storage_file or USERS_FILE
        self.users = ensure_file(self.storage_file, [])

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_username(username: str) -> str:
        return validate_text(username, "Username").lower()

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must include at least one digit.")

    def register(self, username: str, password: str) -> Dict[str, Any]:
        username = self._normalize_username(username)
        self._validate_password(password)
        if any(user.get("username", "").lower() == username for user in self.users):
            raise ValueError("Username already exists.")
        user_record = {
            "id": self._generate_user_id(),
            "username": username,
            "display_name": username,
            "password": self._hash_password(password),
            "created_at": get_timestamp(),
        }
        self.users.append(user_record)
        write_json(USERS_FILE, self.users)

        # Initialize default settings for user
        settings_file = DATA_DIR / "settings.json"
        settings = read_json(settings_file, [])
        if not any(s.get("user_id") == user_record["id"] for s in settings):
            settings.append({
                "user_id": user_record["id"],
                "theme": "flatly",
                "currency": "₹",
                "date_format": "YYYY-MM-DD"
            })
            write_json(settings_file, settings)

        return user_record

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        username = self._normalize_username(username)
        if not password:
            raise ValueError("Password cannot be empty.")
        for user in self.users:
            if user.get("username", "").lower() == username and user.get("password") == self._hash_password(password):
                user["last_login"] = get_timestamp()
                write_json(USERS_FILE, self.users)
                return user
        return None

    def _generate_user_id(self) -> int:
        if not self.users:
            return 1001
        return max(user.get("id", 1000) for user in self.users) + 1


class SessionManager:
    """Manage logged in user context."""

    def __init__(self) -> None:
        self.current_user: Optional[Dict[str, Any]] = None

    def login_user(self, user: Dict[str, Any]) -> None:
        self.current_user = user

    def logout(self) -> None:
        self.current_user = None

    def is_logged_in(self) -> bool:
        return self.current_user is not None


def display_auth_menu() -> None:
    print_info("\n=== Smart Personal Finance Manager ===")
    print_info("1. Register")
    print_info("2. Login")
    print_info("3. Exit")


def run_auth_flow(auth_service: AuthenticationService, session: SessionManager) -> bool:
    display_auth_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        try:
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            user = auth_service.register(username, password)
            print_success(f"User registered successfully: {user['username']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "2":
        try:
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            user = auth_service.login(username, password)
            if user:
                session.login_user(user)
                print_success(f"Welcome back, {user['username']}!")
                return True
            print_error("Invalid username or password.")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "3":
        return False
    else:
        print_error("Invalid option.")
    return False
