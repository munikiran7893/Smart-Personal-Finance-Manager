import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from budget import BudgetService
from expense import ExpenseService
from income import IncomeService
from login import AuthenticationService


def test_registration_and_login():
    temp_file = Path(tempfile.mkdtemp()) / "users.json"
    auth_service = AuthenticationService(storage_file=temp_file)
    user = auth_service.register("tester", "Test1234")
    assert user["username"] == "tester"
    logged_in = auth_service.login("tester", "Test1234")
    assert logged_in is not None

    # Username matching should be case-insensitive
    logged_in_case = auth_service.login("Tester", "Test1234")
    assert logged_in_case is not None
    assert logged_in_case["username"] == "tester"


def test_income_flow():
    temp_file = Path(tempfile.mkdtemp()) / "income.json"
    service = IncomeService("tester", storage_file=temp_file)
    record = service.add_income("Consulting", 300.0, "2026-07-20", "Project fee")
    assert record["amount"] == 300.0
    assert service.total_income() == 300.0


def test_expense_flow():
    temp_file = Path(tempfile.mkdtemp()) / "expenses.json"
    service = ExpenseService("tester", storage_file=temp_file)
    record = service.add_expense("Travel", 60.0, "2026-07-21", "Taxi")
    assert record["category"] == "Travel"
    assert service.total_expenses() == 60.0


def test_budget_flow():
    temp_file = Path(tempfile.mkdtemp()) / "budgets.json"
    service = BudgetService("tester", storage_file=temp_file)
    record = service.set_budget("2026-07", 2000.0)
    assert record["budget_amount"] == 2000.0
    remaining = service.remaining_budget("2026-07", 1500.0)
    assert remaining == 500.0


def test_currency_formatting():
    from utils import format_currency as format_root
    from backend.utils import Utilities

    assert format_root(1234.56) == "₹1,234.56"
    assert Utilities.format_currency(1234.56) == "₹1,234.56"

