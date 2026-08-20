from pathlib import Path

from backend.finance import FinanceService
from backend.storage import StorageManager


def test_recent_activity_lists_latest_transactions(tmp_path: Path) -> None:
    storage = StorageManager(base_dir=tmp_path)
    service = FinanceService(storage)

    service.add_income(1, 1200, "Salary", "Monthly salary", "2024-01-10")
    service.add_expense(1, 120, "Groceries", "Weekly groceries", "2024-01-11")

    activity = service.get_recent_activity(1, limit=5)

    assert len(activity) == 2
    assert activity[0]["type"] == "expense"
    assert activity[0]["amount"] == 120.0
    assert activity[1]["type"] == "income"
