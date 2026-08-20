"""Export utilities for reports and financial data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from expense import ExpenseService
from income import IncomeService
from reports import ReportService
from utils import EXPORTS_DIR, print_info, print_success, write_csv


class ExportService:
    """Export income, expenses, and reports to CSV files."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.income_service = IncomeService(username)
        self.expense_service = ExpenseService(username)
        self.report_service = ReportService(username)

    def export_income_data(self) -> Path:
        rows = self.income_service.view_income()
        export_path = EXPORTS_DIR / f"{self.username}_income.csv"
        write_csv(
            export_path,
            ["id", "source", "amount", "date", "description"],
            [[entry["id"], entry["source"], entry["amount"], entry["date"], entry["description"]] for entry in rows],
        )
        return export_path

    def export_expense_data(self) -> Path:
        rows = self.expense_service.view_expenses()
        export_path = EXPORTS_DIR / f"{self.username}_expenses.csv"
        write_csv(
            export_path,
            ["id", "category", "amount", "date", "description"],
            [[entry["id"], entry["category"], entry["amount"], entry["date"], entry["description"]] for entry in rows],
        )
        return export_path

    def export_report(self, report_type: str) -> Path:
        export_path = EXPORTS_DIR / f"{self.username}_{report_type}.csv"
        if report_type == "income":
            rows = self.report_service.income_report()
            headers = ["id", "source", "amount", "date"]
        elif report_type == "expense":
            rows = self.report_service.expense_report()
            headers = ["id", "category", "amount", "date"]
        elif report_type == "savings":
            rows = self.report_service.savings_report()
            headers = ["metric", "value"]
        elif report_type == "category":
            rows = self.report_service.category_report()
            headers = ["category", "amount"]
        else:
            raise ValueError("Unsupported report type.")
        write_csv(export_path, headers, rows)
        return export_path


def display_export_menu() -> None:
    print_info("\nExport")
    print_info("1. Export Income Data")
    print_info("2. Export Expense Data")
    print_info("3. Export Report")
    print_info("4. Back")


def run_export_flow(service: ExportService) -> None:
    display_export_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        path = service.export_income_data()
        print_success(f"Income data exported to {path}")
    elif choice == "2":
        path = service.export_expense_data()
        print_success(f"Expense data exported to {path}")
    elif choice == "3":
        report_type = input("Report type (income/expense/savings/category): ").strip().lower()
        try:
            path = service.export_report(report_type)
            print_success(f"Report exported to {path}")
        except ValueError as exc:
            print_info(str(exc))
    elif choice == "4":
        return
    else:
        print_info("Invalid option.")
