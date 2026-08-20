"""Income management module."""

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

INCOME_FILE = DATA_DIR / "income.json"


class IncomeService:
    """Manage income entries for the current user."""

    def __init__(self, username: str, storage_file: Path | None = None) -> None:
        self.username = username
        self.storage_file = storage_file or INCOME_FILE
        self.records = ensure_file(self.storage_file, [])

    def _user_records(self) -> List[Dict[str, Any]]:
        user_id = get_user_id_by_username(self.username)
        return [
            record for record in self.records
            if record.get("username") == self.username or record.get("user_id") == user_id
        ]

    def add_income(self, source: str, amount: float, date: str, description: str = "") -> Dict[str, Any]:
        source = validate_text(source, "Source")
        amount = validate_amount(amount)
        normalized_date = parse_date(date)
        description = validate_text(description, "Description", minimum_length=0) if description else ""
        user_id = get_user_id_by_username(self.username)
        record = {
            "id": self._generate_id(),
            "user_id": user_id,
            "username": self.username,
            "source": source,
            "amount": round(amount, 2),
            "date": normalized_date,
            "category": "Other",
            "description": description,
            "notes": "",
            "created_at": get_timestamp(),
        }
        self.records.append(record)
        write_json(self.storage_file, self.records)
        return record

    def view_income(self) -> List[Dict[str, Any]]:
        records = self._user_records()
        records.sort(key=lambda item: item.get("date", ""), reverse=True)
        return records

    def update_income(self, income_id: int, source: Optional[str] = None, amount: Optional[float] = None, date: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        for record in self.records:
            if record.get("id") == income_id and record.get("username") == self.username:
                if source is not None:
                    record["source"] = validate_text(source, "Source")
                if amount is not None:
                    record["amount"] = validate_amount(amount)
                if date is not None:
                    record["date"] = parse_date(date)
                if description is not None:
                    record["description"] = validate_text(description, "Description", minimum_length=0) if description else ""
                record["updated_at"] = get_timestamp()
                write_json(self.storage_file, self.records)
                return record
        raise ValueError("Income record not found.")

    def delete_income(self, income_id: int) -> None:
        original_length = len(self.records)
        user_id = get_user_id_by_username(self.username)
        self.records = [
            record for record in self.records
            if not (record.get("id") == income_id and (record.get("username") == self.username or record.get("user_id") == user_id))
        ]
        if len(self.records) == original_length:
            raise ValueError("Income record not found.")
        write_json(self.storage_file, self.records)

    def search_income(self, query: str) -> List[Dict[str, Any]]:
        needle = query.lower()
        return [record for record in self.view_income() if needle in record.get("source", "").lower() or needle in record.get("description", "").lower()]

    def filter_income(self, month: str) -> List[Dict[str, Any]]:
        month_prefix = month[:7]
        return [record for record in self.view_income() if record.get("date", "").startswith(month_prefix)]

    def total_income(self) -> float:
        return round(sum(item.get("amount", 0.0) for item in self.view_income()), 2)

    def display_income(self) -> None:
        rows = self.view_income()
        if not rows:
            print_info("No income records found.")
            return
        table_rows = [[entry["id"], entry["source"], format_currency(entry["amount"]), entry["date"], entry["description"]] for entry in rows]
        print_table(["ID", "Source", "Amount", "Date", "Description"], table_rows)

    def _generate_id(self) -> int:
        user_entries = [record for record in self.records if record.get("username") == self.username]
        if not user_entries:
            return 1
        return max(record.get("id", 0) for record in user_entries) + 1


def display_income_menu() -> None:
    print_info("\nIncome Management")
    print_info("1. Add Income")
    print_info("2. View Income")
    print_info("3. Update Income")
    print_info("4. Delete Income")
    print_info("5. Search Income")
    print_info("6. Filter Income")
    print_info("7. Back")


def run_income_flow(service: IncomeService) -> None:
    display_income_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        try:
            source = input("Source: ").strip()
            amount = input("Amount: ").strip()
            date = input("Date (YYYY-MM-DD): ").strip() or get_current_date()
            description = input("Description: ").strip()
            record = service.add_income(source, amount, date, description)
            print_success(f"Income added successfully with ID {record['id']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "2":
        service.display_income()
    elif choice == "3":
        try:
            income_id = int(input("Income ID: ").strip())
            source = input("New source (leave blank to keep): ").strip() or None
            amount_text = input("New amount (leave blank to keep): ").strip()
            amount = float(amount_text) if amount_text else None
            date = input("New date (YYYY-MM-DD, leave blank to keep): ").strip() or None
            description = input("New description (leave blank to keep): ").strip() or None
            record = service.update_income(income_id, source, amount, date, description)
            print_success(f"Income updated: {record['source']}")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "4":
        try:
            income_id = int(input("Income ID: ").strip())
            service.delete_income(income_id)
            print_success("Income deleted")
        except ValueError as exc:
            print_error(str(exc))
    elif choice == "5":
        query = input("Search query: ").strip()
        results = service.search_income(query)
        if results:
            for record in results:
                print_info(f"{record['id']} | {record['source']} | {format_currency(record['amount'])} | {record['date']}")
        else:
            print_info("No matching income records found.")
    elif choice == "6":
        month = input("Enter month (YYYY-MM): ").strip()
        results = service.filter_income(month)
        if results:
            for record in results:
                print_info(f"{record['id']} | {record['source']} | {format_currency(record['amount'])} | {record['date']}")
        else:
            print_info("No income records in that month.")
    elif choice == "7":
        return
    else:
        print_error("Invalid option.")
