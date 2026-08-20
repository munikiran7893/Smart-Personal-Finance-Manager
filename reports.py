"""Reporting module for financial summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from income import IncomeService
from expense import ExpenseService
from budget import BudgetService
from utils import format_currency, print_info, print_table


class ReportService:
    """Generate reports for income, expenses, budgets, and savings."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.income_service = IncomeService(username)
        self.expense_service = ExpenseService(username)
        self.budget_service = BudgetService(username)

    def monthly_report(self, month: str) -> List[List[Any]]:
        income_rows = self.income_service.filter_income(month)
        expense_rows = self.expense_service.view_expenses()
        expense_rows = [record for record in expense_rows if record.get("date", "").startswith(month[:7])]
        total_income = sum(item.get("amount", 0.0) for item in income_rows)
        total_expense = sum(item.get("amount", 0.0) for item in expense_rows)
        return [[month, format_currency(total_income), format_currency(total_expense), format_currency(total_income - total_expense)]]

    def income_report(self) -> List[List[Any]]:
        rows = self.income_service.view_income()
        return [[entry["id"], entry["source"], format_currency(entry["amount"]), entry["date"]] for entry in rows]

    def expense_report(self) -> List[List[Any]]:
        rows = self.expense_service.view_expenses()
        return [[entry["id"], entry["category"], format_currency(entry["amount"]), entry["date"]] for entry in rows]

    def savings_report(self) -> List[List[Any]]:
        total_income = self.income_service.total_income()
        total_expense = self.expense_service.total_expenses()
        savings = total_income - total_expense
        return [["Total Income", format_currency(total_income)], ["Total Expense", format_currency(total_expense)], ["Savings", format_currency(savings)]]

    def category_report(self) -> List[List[Any]]:
        grouped: Dict[str, float] = defaultdict(float)
        for entry in self.expense_service.view_expenses():
            grouped[entry.get("category", "Uncategorized")] += entry.get("amount", 0.0)
        return [[category, format_currency(amount)] for category, amount in sorted(grouped.items())]

    def display_monthly_report(self, month: str) -> None:
        print_table(["Month", "Income", "Expense", "Net"], self.monthly_report(month))

    def display_income_report(self) -> None:
        print_table(["ID", "Source", "Amount", "Date"], self.income_report())

    def display_expense_report(self) -> None:
        print_table(["ID", "Category", "Amount", "Date"], self.expense_report())

    def display_savings_report(self) -> None:
        print_table(["Metric", "Value"], self.savings_report())

    def display_category_report(self) -> None:
        print_table(["Category", "Amount"], self.category_report())


def display_reports_menu() -> None:
    print_info("\nReports")
    print_info("1. Monthly Report")
    print_info("2. Income Report")
    print_info("3. Expense Report")
    print_info("4. Savings Report")
    print_info("5. Category Report")
    print_info("6. Back")


def run_reports_flow(service: ReportService) -> None:
    display_reports_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        month = input("Month (YYYY-MM): ").strip()
        service.display_monthly_report(month)
    elif choice == "2":
        service.display_income_report()
    elif choice == "3":
        service.display_expense_report()
    elif choice == "4":
        service.display_savings_report()
    elif choice == "5":
        service.display_category_report()
    elif choice == "6":
        return
    else:
        print_info("Invalid option.")
