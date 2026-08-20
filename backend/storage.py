"""JSON-based storage manager for the finance application."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class StorageManager:
    """Manage JSON persistence for users, finances, and settings."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"
        self.backups_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.charts_dir = self.base_dir / "charts"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def read_json(self, filename: str, default: Any = None) -> Any:
        path = self.data_dir / filename
        if not path.exists():
            self.write_json(filename, default if default is not None else [])
            return default if default is not None else []
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return default if default is not None else []

    def write_json(self, filename: str, payload: Any) -> None:
        path = self.data_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    def backup_data(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backups_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        for filename in [
            "users.json", "income.json", "expenses.json", "budgets.json",
            "monthly_reports.json", "yearly_reports.json", "settings.json"
        ]:
            source = self.data_dir / filename
            if source.exists():
                shutil.copy2(source, backup_path / filename)
        return backup_path

    def restore_backup(self, backup_path: Path) -> None:
        if not backup_path.exists():
            raise FileNotFoundError("Backup directory not found.")
        for filename in [
            "users.json", "income.json", "expenses.json", "budgets.json",
            "monthly_reports.json", "yearly_reports.json", "settings.json"
        ]:
            source = backup_path / filename
            if source.exists():
                shutil.copy2(source, self.data_dir / filename)
