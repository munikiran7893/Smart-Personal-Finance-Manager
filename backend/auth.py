"""Authentication and user management backend."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.storage import StorageManager
from backend.utils import Validation, Utilities


class Authentication:
    """Handle registration, login, and session state."""

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage
        self.users = self.storage.read_json("users.json", [])

    @staticmethod
    def _normalize_username(username: str) -> str:
        return Validation.username(username).lower()

    def register(self, username: str, password: str, display_name: str = "") -> Dict[str, Any]:
        username = self._normalize_username(username)
        Validation.password(password)
        if any(user.get("username", "").lower() == username for user in self.users):
            raise ValueError("Username already exists.")
        if not display_name.strip():
            display_name = username
        user_record = {
            "id": self._next_id(),
            "username": username,
            "display_name": display_name.strip(),
            "password": Utilities.hash_password(password),
            "created_at": Utilities.timestamp(),
            "last_login": None,
        }
        self.users.append(user_record)
        self.storage.write_json("users.json", self.users)

        # Initialize default settings for user
        settings = self.storage.read_json("settings.json", [])
        if not any(s.get("user_id") == user_record["id"] for s in settings):
            settings.append({
                "user_id": user_record["id"],
                "theme": "flatly",
                "currency": "₹",
                "date_format": "YYYY-MM-DD"
            })
            self.storage.write_json("settings.json", settings)

        return user_record

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        username = self._normalize_username(username)
        for user in self.users:
            if user.get("username", "").lower() == username and user.get("password") == Utilities.hash_password(password):
                user["last_login"] = Utilities.timestamp()
                # Ensure display_name exists for older records
                if "display_name" not in user:
                    user["display_name"] = user["username"]
                self.storage.write_json("users.json", self.users)
                return user
        return None

    def get_settings(self, user_id: int) -> Dict[str, Any]:
        settings = self.storage.read_json("settings.json", [])
        user_settings = next((s for s in settings if s.get("user_id") == user_id), None)
        if not user_settings:
            user_settings = {
                "user_id": user_id,
                "theme": "flatly",
                "currency": "₹",
                "date_format": "YYYY-MM-DD"
            }
            settings.append(user_settings)
            self.storage.write_json("settings.json", settings)
        return user_settings

    def update_settings(self, user_id: int, theme: str, currency: str, date_format: str) -> Dict[str, Any]:
        settings = self.storage.read_json("settings.json", [])
        user_settings = next((s for s in settings if s.get("user_id") == user_id), None)
        if not user_settings:
            user_settings = {"user_id": user_id}
            settings.append(user_settings)
        user_settings["theme"] = theme
        user_settings["currency"] = currency
        user_settings["date_format"] = date_format
        self.storage.write_json("settings.json", settings)
        return user_settings

    def update_profile(self, user_id: int, display_name: str) -> Dict[str, Any]:
        if not display_name.strip():
            raise ValueError("Display name cannot be empty.")
        for user in self.users:
            if user.get("id") == user_id:
                user["display_name"] = display_name.strip()
                self.storage.write_json("users.json", self.users)
                return user
        raise ValueError("User not found.")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        Validation.password(new_password)
        for user in self.users:
            if user.get("id") == user_id:
                if user.get("password") != Utilities.hash_password(old_password):
                    raise ValueError("Incorrect current password.")
                user["password"] = Utilities.hash_password(new_password)
                self.storage.write_json("users.json", self.users)
                return
        raise ValueError("User not found.")

    def _next_id(self) -> int:
        if not self.users:
            return 1
        return max(int(user.get("id", 0)) for user in self.users) + 1
