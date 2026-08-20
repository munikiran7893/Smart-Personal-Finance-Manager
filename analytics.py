"""Analytics and chart generation module."""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Dict, List

import matplotlib.pyplot as plt

from expense import ExpenseService
from income import IncomeService
from utils import CHARTS_DIR, format_currency, print_error, print_info


class AnalyticsService:
    """Create charts and summarize spending patterns."""

    def __init__(self, username: str) -> None:
        self.username = username
        self.income_service = IncomeService(username)
        self.expense_service = ExpenseService(username)

    def income_vs_expense_chart(self) -> str:
        income_total = self.income_service.total_income()
        expense_total = self.expense_service.total_expenses()
        labels = ["Income", "Expenses"]
        values = [income_total, expense_total]
        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color=["#4CAF50", "#F44336"])
        plt.ylabel("Amount")
        plt.title("Income vs Expenses")
        for index, value in enumerate(values):
            plt.text(index, value + 0.5, format_currency(value), ha="center")
        save_path = CHARTS_DIR / "income_vs_expense.png"
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        return str(save_path)

    def expense_category_pie_chart(self) -> str:
        grouped: Dict[str, float] = defaultdict(float)
        for entry in self.expense_service.view_expenses():
            grouped[entry.get("category", "Uncategorized")] += entry.get("amount", 0.0)
        labels = list(grouped.keys())
        values = list(grouped.values())
        plt.figure(figsize=(6, 6))
        plt.pie(values, labels=labels, autopct="%1.1f%%")
        plt.title("Expense Categories")
        save_path = CHARTS_DIR / "expense_categories.png"
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        return str(save_path)

    def monthly_expense_trend(self) -> List[List[Any]]:
        grouped: Dict[str, float] = defaultdict(float)
        for entry in self.expense_service.view_expenses():
            month = entry.get("date", "")[:7]
            grouped[month] += entry.get("amount", 0.0)
        return [[month, format_currency(amount)] for month, amount in sorted(grouped.items())]

    def savings_analysis(self) -> List[List[Any]]:
        income_total = self.income_service.total_income()
        expense_total = self.expense_service.total_expenses()
        savings = income_total - expense_total
        return [["Total Income", format_currency(income_total)], ["Total Expense", format_currency(expense_total)], ["Savings", format_currency(savings)]]


def display_analytics_menu() -> None:
    print_info("\nAnalytics")
    print_info("1. Income vs Expense Chart")
    print_info("2. Expense Category Pie Chart")
    print_info("3. Monthly Expense Trend")
    print_info("4. Savings Analysis")
    print_info("5. Back")


def run_analytics_flow(service: AnalyticsService) -> None:
    display_analytics_menu()
    choice = input("Choose an option: ").strip()
    if choice == "1":
        path = service.income_vs_expense_chart()
        print_info(f"Chart saved to {path}")
    elif choice == "2":
        path = service.expense_category_pie_chart()
        print_info(f"Chart saved to {path}")
    elif choice == "3":
        rows = service.monthly_expense_trend()
        print_info("Monthly expense trend")
        for month, amount in rows:
            print_info(f"{month}: {amount}")
    elif choice == "4":
        rows = service.savings_analysis()
        for metric, value in rows:
            print_info(f"{metric}: {value}")
    elif choice == "5":
        return
    else:
        print_error("Invalid option.")
