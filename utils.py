"""Shared helpers and configuration for the Smart Personal Finance Manager."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"
EXPORTS_DIR = BASE_DIR / "exports"

for directory in (DATA_DIR, CHARTS_DIR, EXPORTS_DIR):
    directory.mkdir(exist_ok=True)


def ensure_file(path: Path, default: Any) -> Any:
    """Create a file with a default payload if it does not exist."""
    if not path.exists():
        write_json(path, default)
    return read_json(path, default)


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON data from disk with graceful fallback."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    """Persist JSON data to disk."""
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def get_timestamp() -> str:
    """Return a readable timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_date() -> str:
    """Return the current date in ISO format."""
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(value: str) -> str:
    """Normalize a date string to YYYY-MM-DD."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")


def format_currency(amount: float) -> str:
    """Represent money values as a currency string."""
    return f"₹{amount:,.2f}"


def validate_amount(value: Any) -> float:
    """Validate and convert user-provided amount values."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a valid number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_text(value: Any, field_name: str, minimum_length: int = 1) -> str:
    """Validate a user-entered text field."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    cleaned = value.strip()
    if len(cleaned) < minimum_length:
        raise ValueError(f"{field_name} must be at least {minimum_length} characters long.")
    return cleaned


def validate_choice(value: str, valid_choices: List[str]) -> str:
    """Ensure a user-entered choice matches a known set."""
    normalized = value.strip().lower()
    if normalized not in valid_choices:
        raise ValueError(f"Choice must be one of: {', '.join(valid_choices)}")
    return normalized


def print_table(headers: List[str], rows: List[List[Any]]) -> None:
    """Render a simple table to the console."""
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_success(message: str) -> None:
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(exist_ok=True)


def write_csv(path: Path, headers: List[str], rows: List[List[Any]]) -> None:
    """Write a CSV file from a list of rows."""
    ensure_parent_dir(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def get_user_id_by_username(username: str) -> int:
    """Resolve a username to a user_id by reading users.json."""
    users = read_json(DATA_DIR / "users.json", [])
    for u in users:
        if u.get("username") == username:
            return u.get("id")
    return 1001


def main_menu() -> str:
    """Display the main menu and return the user's choice."""
    print("\n=== Smart Personal Finance Manager ===")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    choice = input("Choose an option: ").strip()
    return choice


def main():
    """Main function to run the Smart Personal Finance Manager."""
    print("Welcome to the Smart Personal Finance Manager!")
    main_menu()


if __name__ == "__main__":
    main()
