"""Expense management module."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils import (
    DATA_DIR,
    ensure_file,
    format_currency,
    get_current_date,
    get_timestamp,
    get_user_id_by_username,
    parse_date,
    print_error,
    print_info,
    print_success,
    print_table,
    validate_amount,
    validate_text,
    write_json,
)

EXPENSES_FILE = DATA_DIR / "expenses.json"


class ExpenseService:
    """Manage expense entries for the current user."""

    def __init__(self, username: str, storage_file: Path | None = None) -> None:
        self.username = username
        self.storage_file = storage_file or EXPENSES_FILE
        self.records = ensure_file(self.storage_file, [])

    def _user_records(self) -> List[Dict[str, Any]]:
        user_id = get_user_id_by_username(self.username)
        return [
            record for record in self.records
            if record.get("username") == self.username or record.get("user_id") == user_id
        ]

    def add_expense(self, category: str, amount: float, date: str, description: str = "") -> Dict[str, Any]:
        category = validate_text(category, "Category")
        amount = validate_amount(amount)
        normalized_date = parse_date(date)
        description = validate_text(description, "Description", minimum_length=0) if description else ""
        user_id = get_user_id_by_username(self.username)
        record = {
            "id": self._generate_id(),
            "user_id": user_id,
            "username": self.username,
            "name": category,
            "category": category,
            "amount": round(amount, 2),
            "date": normalized_date,
            "payment_method": "Cash",
            "description": description,
            "notes": "",
            "created_at": get_timestamp(),
        }
        self.records.append(record)
        write_json(self.storage_file, self.records)
        return record

    def view_expenses(self) -> List[Dict[str, Any]]:
        records = self._user_records()
        records.sort(key=lambda item: item.get("date", ""), reverse=True)
        return records

    def update_expense(self, expense_id: int, category: Optional[str] = None, amount: Optional[float] = None, date: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        user_id = get_user_id_by_username(self.username)
        for record in self.records:
            if record.get("id") == expense_id and (record.get("username") == self.username or record.get("user_id") == user_id):
                if category is not None:
                    record["category"] = validate_text(category, "Category")
                    record["name"] = record["category"]
                if amount is not None:
                    record["amount"] = validate_amount(amount)
                if date is not None:
                    record["date"] = parse_date(date)
                if description is not None:
                    record["description"] = validate_text(description, "Description", minimum_length=0) if description else ""
                record["updated_at"] = get_timestamp()
                write_json(self.storage_file, self.records)
                return record
        raise ValueError("Expense record not found.")

    def delete_expense(self, expense_id: int) -> None:
        original_length = len(self.records)
        user_id = get_user_id_by_username(self.username)
        self.records = [
            record for record in self.records
            if not (record.get("id") == expense_id and (record.get("username") == self.username or record.get("user_id") == user_id))
        ]
        if len(self.records) == original_length:
            raise ValueError("Expense record not found.")
        write_json(self.storage_file, self.records)

    def search_expenses(self, query: str) -> List[Dict[str, Any]]:
        needle = query.lower()
        return [record for record in self.view_expenses() if needle in record.get("category", "").lower() or needle in record.get("description", "").lower()]

    def filter_by_category(self, category: str) -> List[Dict[str, Any]]:
        needle = category.lower()
        return [record for record in self.view_expenses() if needle in record.get("category", "").lower()]

    def total_expenses(self) -> float:
        return round(sum(item.get("amount", 0.0) for item in self.view_expenses()), 2)

    def display_expenses(self) -> None:
        rows = self.view_expenses()
        if not rows:
            print_info("No expense records found.")
            return
        table_rows = [[entry["id"], entry["category"], format_currency(entry["amount"]), entry["date"], entry["description"]] for entry in rows]
        print_table(["ID", "Category", "Amount", "Date", "Description"], table_rows)

    def _generate_id(self) -> int:
        user_entries = [record for record in self.records if record.get("username") == self.username]
        if not user_entries:
            return 1
        return max(record.get("id", 0) for record in user_entries) + 1


def display_expense_menu() -> None:
    print_info("\nExpense Management")
    print_info("1. Add Expense")
    print_info("2. View Expenses")
    print_info("3. Update Expense")
    print_info("4. Delete Expense")
    print_info("5. Search Expenses")
    print_info("6. Filter by Category")
    print_info("7. Back")


def run_expense_flow(service: ExpenseService) -> None:
    display_expense_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        try:
            category = input("Category: ").strip()
            amount = input("Amount: ").strip()
            date = input("Date (YYYY-MM-DD): ").strip() or get_current_date()
            description = input("Description: ").strip()
            record = service.add_expense(category, amount, date, description)
            print_success(f"Expense added successfully with ID {record['id']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "2":
        service.display_expenses()
    elif choice == "3":
        try:
            expense_id = int(input("Expense ID: ").strip())
            category = input("New category (leave blank to keep): ").strip() or None
            amount_text = input("New amount (leave blank to keep): ").strip()
            amount = float(amount_text) if amount_text else None
            date = input("New date (YYYY-MM-DD, leave blank to keep): ").strip() or None
            description = input("New description (leave blank to keep): ").strip() or None
            record = service.update_expense(expense_id, category, amount, date, description)
            print_success(f"Expense updated: {record['category']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "4":
        try:
            expense_id = int(input("Expense ID: ").strip())
            service.delete_expense(expense_id)
            print_success("Expense deleted")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "5":
        query = input("Search query: ").strip()
        results = service.search_expenses(query)
        if results:
            for record in results:
                print_info(f"{record['id']} | {record['category']} | {format_currency(record['amount'])} | {record['date']}")
        else:
            print_info("No matching expenses found.")
    elif choice == "6":
        category = input("Category: ").strip()
        results = service.filter_by_category(category)
        if results:
            for record in results:
                print_info(f"{record['id']} | {record['category']} | {format_currency(record['amount'])} | {record['date']}")
        else:
            print_info("No expenses found for that category.")
    elif choice == "7":
        return
    else:
        print_error("Invalid option.")
