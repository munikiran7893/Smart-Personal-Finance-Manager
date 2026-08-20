"""Budget management module."""

from __future__ import annotations

from typing import Any, Dict, List

from utils import (
    DATA_DIR,
    ensure_file,
    format_currency,
    get_current_date,
    get_timestamp,
    get_user_id_by_username,
    print_error,
    print_info,
    print_success,
    print_table,
    validate_amount,
    write_json,
)

BUDGETS_FILE = DATA_DIR / "budgets.json"


class BudgetService:
    """Manage monthly budgets for the current user."""

    def __init__(self, username: str, storage_file: Path | None = None) -> None:
        self.username = username
        self.storage_file = storage_file or BUDGETS_FILE
        self.records = ensure_file(self.storage_file, [])

    def _user_records(self) -> List[Dict[str, Any]]:
        user_id = get_user_id_by_username(self.username)
        return [
            record for record in self.records
            if record.get("username") == self.username or record.get("user_id") == user_id
        ]

    def set_budget(self, month: str, amount: float) -> Dict[str, Any]:
        amount = validate_amount(amount)
        budget_key = month[:7]
        existing = next((record for record in self._user_records() if record.get("month") == budget_key), None)
        if existing:
            raise ValueError("Budget already exists for that month.")
        user_id = get_user_id_by_username(self.username)
        record = {
            "id": self._generate_id(),
            "user_id": user_id,
            "username": self.username,
            "month": budget_key,
            "budget_amount": round(amount, 2),
            "created_at": get_timestamp(),
        }
        self.records.append(record)
        write_json(self.storage_file, self.records)
        return record

    def update_budget(self, month: str, amount: float) -> Dict[str, Any]:
        amount = validate_amount(amount)
        budget_key = month[:7]
        user_id = get_user_id_by_username(self.username)
        for record in self.records:
            if (record.get("username") == self.username or record.get("user_id") == user_id) and record.get("month") == budget_key:
                record["budget_amount"] = round(amount, 2)
                record["updated_at"] = get_timestamp()
                write_json(self.storage_file, self.records)
                return record
        raise ValueError("Budget for that month not found.")

    def view_budget(self, month: str | None = None) -> List[Dict[str, Any]]:
        records = self._user_records()
        if month:
            budget_key = month[:7]
            return [record for record in records if record.get("month") == budget_key]
        return records

    def remaining_budget(self, month: str, expenses_total: float) -> float:
        budgets = self.view_budget(month)
        if not budgets:
            return 0.0
        budget_amount = budgets[0].get("budget_amount", 0.0)
        return round(budget_amount - expenses_total, 2)

    def alert(self, month: str, expenses_total: float) -> str:
        remaining = self.remaining_budget(month, expenses_total)
        if remaining < 0:
            return "Budget exceeded"
        if remaining <= 100:
            return "Budget is close to the limit"
        return "Budget is healthy"

    def display_budget(self, month: str | None = None) -> None:
        rows = self.view_budget(month)
        if not rows:
            print_info("No budget records found.")
            return
        table_rows = [[entry["month"], format_currency(entry["budget_amount"])] for entry in rows]
        print_table(["Month", "Budget"], table_rows)

    def _generate_id(self) -> int:
        user_entries = [record for record in self.records if record.get("username") == self.username]
        if not user_entries:
            return 1
        return max(record.get("id", 0) for record in user_entries) + 1


def display_budget_menu() -> None:
    print_info("\nBudget Management")
    print_info("1. Set Monthly Budget")
    print_info("2. Update Budget")
    print_info("3. View Budget")
    print_info("4. Back")


def run_budget_flow(service: BudgetService, expenses_total: float) -> None:
    display_budget_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        try:
            month = input("Month (YYYY-MM): ").strip()
            amount = input("Budget amount: ").strip()
            record = service.set_budget(month, amount)
            print_success(f"Budget set for {record['month']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "2":
        try:
            month = input("Month (YYYY-MM): ").strip()
            amount = input("New budget amount: ").strip()
            record = service.update_budget(month, amount)
            print_success(f"Budget updated for {record['month']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "3":
        month = input("Month (YYYY-MM, leave blank for all): ").strip() or None
        service.display_budget(month)
        if month:
            print_info(f"Remaining budget: {format_currency(service.remaining_budget(month, expenses_total))}")
            print_info(service.alert(month, expenses_total))
    elif choice == "4":
        return
    else:
        print_error("Invalid option.")
