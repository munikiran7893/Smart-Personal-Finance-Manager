"""Dashboard and main menu navigation for the finance manager."""

from __future__ import annotations

from analytics import AnalyticsService, run_analytics_flow
from budget import BudgetService, run_budget_flow
from expense import ExpenseService, run_expense_flow
from export import ExportService, run_export_flow
from income import IncomeService, run_income_flow
from reports import ReportService, run_reports_flow
from utils import clear_screen, format_currency, print_error, print_info, print_success


class Dashboard:
    """Main application dashboard for the logged-in user."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.income_service = IncomeService(username)
        self.expense_service = ExpenseService(username)
        self.budget_service = BudgetService(username)
        self.report_service = ReportService(username)
        self.analytics_service = AnalyticsService(username)
        self.export_service = ExportService(username)

    def show_welcome(self) -> None:
        print_info(f"\nWelcome, {self.username}!")
        print_info("Smart Personal Finance Manager")
        print_info("Manage income, expenses, budgets, reports, and analytics from one place.")

    def show_main_menu(self) -> None:
        print_info("\nMain Menu")
        print_info("1. Income Management")
        print_info("2. Expense Management")
        print_info("3. Budget Management")
        print_info("4. Reports")
        print_info("5. Analytics")
        print_info("6. Export")
        print_info("7. Logout")

    def run(self) -> None:
        self.show_welcome()
        while True:
            self.show_main_menu()
            choice = input("Choose an option: ").strip()
            if choice == "1":
                run_income_flow(self.income_service)
            elif choice == "2":
                run_expense_flow(self.expense_service)
            elif choice == "3":
                expenses_total = self.expense_service.total_expenses()
                run_budget_flow(self.budget_service, expenses_total)
            elif choice == "4":
                run_reports_flow(self.report_service)
            elif choice == "5":
                run_analytics_flow(self.analytics_service)
            elif choice == "6":
                run_export_flow(self.export_service)
            elif choice == "7":
                print_success("You have been logged out.")
                break
            else:
                print_error("Invalid option.")
