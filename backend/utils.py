"""Shared utilities for the finance application."""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class Validation:
    """Validate common user and finance inputs."""

    @staticmethod
    def username(value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username is required.")
        if len(cleaned) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return cleaned

    @staticmethod
    def password(value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        return value

    @staticmethod
    def amount(value: Any) -> float:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            raise ValueError("Amount must be a valid number.")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return round(amount, 2)

    @staticmethod
    def date(value: str) -> str:
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")

    @staticmethod
    def income_category(value: str) -> str:
        categories = ["Salary", "Business", "Freelancing", "Investments", "Bonus", "Gift", "Other"]
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Income category is required.")
        match = next((c for c in categories if c.lower() == cleaned.lower()), None)
        if not match:
            raise ValueError(f"Invalid income category. Must be one of: {', '.join(categories)}")
        return match

    @staticmethod
    def expense_category(value: str) -> str:
        categories = ["Food", "Shopping", "Bills", "Travel", "Medical", "Education", "Entertainment", "Transport", "Utilities", "Other"]
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Expense category is required.")
        match = next((c for c in categories if c.lower() == cleaned.lower()), None)
        if not match:
            raise ValueError(f"Invalid expense category. Must be one of: {', '.join(categories)}")
        return match

    @staticmethod
    def payment_method(value: str) -> str:
        methods = ["Cash", "Credit Card", "Debit Card", "Net Banking", "UPI", "Other"]
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Payment method is required.")
        match = next((m for m in methods if m.lower() == cleaned.lower()), None)
        if not match:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(methods)}")
        return match


class Utilities:
    """Helpers for formatting and hashing."""

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def format_currency(value: float, symbol: str = "₹") -> str:
        return f"{symbol}{value:,.2f}"

    @staticmethod
    def today() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def current_month() -> str:
        return datetime.now().strftime("%Y-%m")

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
