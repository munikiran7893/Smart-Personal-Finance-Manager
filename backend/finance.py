"""Finance service layer for incomes, expenses, and budgets."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.storage import StorageManager
from backend.utils import Validation, Utilities


class FinanceService:
    """Manage financial records, budget state, and calculations."""

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage
        self.incomes = self.storage.read_json("income.json", [])
        self.expenses = self.storage.read_json("expenses.json", [])
        self.budgets = self.storage.read_json("budgets.json", [])

    def _get_username(self, user_id: int) -> str:
        users = self.storage.read_json("users.json", [])
        for u in users:
            if u.get("id") == user_id:
                return u.get("username", "")
        return ""

    # --- INCOME MANAGEMENT ---

    def add_income(
        self,
        user_id: int,
        amount: Any,
        category: str,
        description: str,
        date: str,
        source: str = "",
        notes: str = "",
        username: str = ""
    ) -> Dict[str, Any]:
        amount = Validation.amount(amount)
        date = Validation.date(date)
        
        # Validate category, fallback to Other if invalid
        try:
            norm_category = Validation.income_category(category)
        except ValueError:
            norm_category = "Other"
            
        source = source.strip() or category.strip() or "General"
        username = username or self._get_username(user_id)

        entry = {
            "id": self._next_id(self.incomes),
            "user_id": user_id,
            "username": username,
            "amount": amount,
            "category": norm_category,
            "source": source,
            "description": description.strip() or "Income",
            "notes": notes.strip(),
            "date": date,
            "created_at": Utilities.timestamp(),
        }
        self.incomes.append(entry)
        self.storage.write_json("income.json", self.incomes)
        
        # Sync budget
        self.sync_budget(user_id, date[:7])
        
        return entry

    def update_income(
        self,
        user_id: int,
        income_id: int,
        amount: Optional[Any] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        date: Optional[str] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        for entry in self.incomes:
            if entry.get("id") == income_id and entry.get("user_id") == user_id:
                old_month = entry.get("date", "")[:7]
                if amount is not None:
                    entry["amount"] = Validation.amount(amount)
                if date is not None:
                    entry["date"] = Validation.date(date)
                if category is not None:
                    try:
                        entry["category"] = Validation.income_category(category)
                    except ValueError:
                        entry["category"] = "Other"
                if source is not None:
                    entry["source"] = source.strip() or entry["category"]
                if description is not None:
                    entry["description"] = description.strip()
                if notes is not None:
                    entry["notes"] = notes.strip()
                entry["updated_at"] = Utilities.timestamp()
                
                self.storage.write_json("income.json", self.incomes)
                
                # Sync budget for old and new month
                self.sync_budget(user_id, old_month)
                if date is not None:
                    self.sync_budget(user_id, date[:7])
                    
                return entry
        raise ValueError("Income record not found.")

    def delete_income(self, user_id: int, income_id: int) -> None:
        original_len = len(self.incomes)
        month_to_sync = None
        
        for entry in self.incomes:
            if entry.get("id") == income_id and entry.get("user_id") == user_id:
                month_to_sync = entry.get("date", "")[:7]
                break
                
        self.incomes = [
            e for e in self.incomes
            if not (e.get("id") == income_id and e.get("user_id") == user_id)
        ]
        
        if len(self.incomes) == original_len:
            raise ValueError("Income record not found.")
            
        self.storage.write_json("income.json", self.incomes)
        if month_to_sync:
            self.sync_budget(user_id, month_to_sync)

    def get_incomes(self, user_id: int) -> List[Dict[str, Any]]:
        records = [e for e in self.incomes if e.get("user_id") == user_id]
        records.sort(key=lambda x: x.get("date", ""), reverse=True)
        return records

    def search_incomes(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        needle = query.lower().strip()
        records = self.get_incomes(user_id)
        if not needle:
            return records
        return [
            r for r in records
            if needle in r.get("source", "").lower()
            or needle in r.get("description", "").lower()
            or needle in r.get("category", "").lower()
        ]

    def filter_incomes(self, user_id: int, month: str = "", category: str = "") -> List[Dict[str, Any]]:
        records = self.get_incomes(user_id)
        if month:
            month_prefix = month[:7]
            records = [r for r in records if r.get("date", "").startswith(month_prefix)]
        if category:
            records = [r for r in records if r.get("category", "").lower() == category.lower()]
        return records

    # --- EXPENSE MANAGEMENT ---

    def add_expense(
        self,
        user_id: int,
        amount: Any,
        category: str,
        description: str,
        date: str,
        name: str = "",
        payment_method: str = "Cash",
        notes: str = "",
        username: str = ""
    ) -> Dict[str, Any]:
        amount = Validation.amount(amount)
        date = Validation.date(date)
        
        try:
            norm_category = Validation.expense_category(category)
        except ValueError:
            norm_category = "Other"
            
        try:
            norm_pm = Validation.payment_method(payment_method)
        except ValueError:
            norm_pm = "Other"

        name = name.strip() or category.strip() or "General"
        username = username or self._get_username(user_id)

        entry = {
            "id": self._next_id(self.expenses),
            "user_id": user_id,
            "username": username,
            "name": name,
            "amount": amount,
            "category": norm_category,
            "payment_method": norm_pm,
            "description": description.strip() or "Expense",
            "notes": notes.strip(),
            "date": date,
            "created_at": Utilities.timestamp(),
        }
        self.expenses.append(entry)
        self.storage.write_json("expenses.json", self.expenses)
        return entry

    def update_expense(
        self,
        user_id: int,
        expense_id: int,
        amount: Optional[Any] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        date: Optional[str] = None,
        name: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        for entry in self.expenses:
            if entry.get("id") == expense_id and entry.get("user_id") == user_id:
                if amount is not None:
                    entry["amount"] = Validation.amount(amount)
                if date is not None:
                    entry["date"] = Validation.date(date)
                if category is not None:
                    try:
                        entry["category"] = Validation.expense_category(category)
                    except ValueError:
                        entry["category"] = "Other"
                if payment_method is not None:
                    try:
                        entry["payment_method"] = Validation.payment_method(payment_method)
                    except ValueError:
                        entry["payment_method"] = "Other"
                if name is not None:
                    entry["name"] = name.strip() or entry["category"]
                if description is not None:
                    entry["description"] = description.strip()
                if notes is not None:
                    entry["notes"] = notes.strip()
                entry["updated_at"] = Utilities.timestamp()
                
                self.storage.write_json("expenses.json", self.expenses)
                return entry
        raise ValueError("Expense record not found.")

    def delete_expense(self, user_id: int, expense_id: int) -> None:
        original_len = len(self.expenses)
        self.expenses = [
            e for e in self.expenses
            if not (e.get("id") == expense_id and e.get("user_id") == user_id)
        ]
        if len(self.expenses) == original_len:
            raise ValueError("Expense record not found.")
        self.storage.write_json("expenses.json", self.expenses)

    def get_expenses(self, user_id: int) -> List[Dict[str, Any]]:
        records = [e for e in self.expenses if e.get("user_id") == user_id]
        records.sort(key=lambda x: x.get("date", ""), reverse=True)
        return records

    def search_expenses(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        needle = query.lower().strip()
        records = self.get_expenses(user_id)
        if not needle:
            return records
        return [
            r for r in records
            if needle in r.get("name", "").lower()
            or needle in r.get("description", "").lower()
            or needle in r.get("category", "").lower()
        ]

    def filter_expenses(
        self, user_id: int, month: str = "", category: str = "", payment_method: str = ""
    ) -> List[Dict[str, Any]]:
        records = self.get_expenses(user_id)
        if month:
            month_prefix = month[:7]
            records = [r for r in records if r.get("date", "").startswith(month_prefix)]
        if category:
            records = [r for r in records if r.get("category", "").lower() == category.lower()]
        if payment_method:
            records = [r for r in records if r.get("payment_method", "").lower() == payment_method.lower()]
        return records

    # --- BUDGET & CALCULATIONS ---

    def sync_budget(self, user_id: int, month: str) -> None:
        """Calculate total income for the month and sync/write it to budgets.json."""
        month_prefix = month[:7]
        user_incomes = [
            r for r in self.incomes
            if r.get("user_id") == user_id and r.get("date", "").startswith(month_prefix)
        ]
        total_income = round(sum(r.get("amount", 0.0) for r in user_incomes), 2)
        
        # Read/Write budget record
        username = self._get_username(user_id)
        existing = next(
            (b for b in self.budgets if b.get("user_id") == user_id and b.get("month") == month_prefix),
            None
        )
        if existing:
            existing["budget_amount"] = total_income
            existing["updated_at"] = Utilities.timestamp()
        else:
            self.budgets.append({
                "id": self._next_id(self.budgets),
                "user_id": user_id,
                "username": username,
                "month": month_prefix,
                "budget_amount": total_income,
                "created_at": Utilities.timestamp()
            })
        self.storage.write_json("budgets.json", self.budgets)

    def set_budget(self, user_id: int, month: str, category: str, amount: float) -> Dict[str, Any]:
        """Allows setting an override/explicit budget for backward compatibility."""
        amount = Validation.amount(amount)
        month_prefix = month[:7]
        username = self._get_username(user_id)
        
        existing = next(
            (b for b in self.budgets if b.get("user_id") == user_id and b.get("month") == month_prefix),
            None
        )
        if existing:
            existing["budget_amount"] = amount
            existing["updated_at"] = Utilities.timestamp()
            budget_entry = existing
        else:
            budget_entry = {
                "id": self._next_id(self.budgets),
                "user_id": user_id,
                "username": username,
                "month": month_prefix,
                "category": category.strip() or "General",
                "amount": amount, # key compatibility
                "budget_amount": amount,
                "created_at": Utilities.timestamp(),
            }
            self.budgets.append(budget_entry)
            
        self.storage.write_json("budgets.json", self.budgets)
        return budget_entry

    def get_financial_calculations(self, user_id: int, month: Optional[str] = None) -> Dict[str, Any]:
        """Calculate totals, savings, budget utilization, trends, and summaries."""
        if not month:
            month = Utilities.current_month()
        month_prefix = month[:7]
        year_prefix = month[:4]

        incomes = self.get_incomes(user_id)
        expenses = self.get_expenses(user_id)

        # All-time totals
        total_income = round(sum(i.get("amount", 0.0) for i in incomes), 2)
        total_expenses = round(sum(e.get("amount", 0.0) for e in expenses), 2)
        net_savings = round(total_income - total_expenses, 2)

        # Monthly specific totals
        monthly_incomes = [i for i in incomes if i.get("date", "").startswith(month_prefix)]
        monthly_expenses = [e for e in expenses if e.get("date", "").startswith(month_prefix)]

        monthly_income_total = round(sum(i.get("amount", 0.0) for i in monthly_incomes), 2)
        monthly_expense_total = round(sum(e.get("amount", 0.0) for e in monthly_expenses), 2)
        
        # Available Monthly Budget = Sum of income in that month
        # If no income in that month, check if there is an override budget in budgets.json
        budget_record = next(
            (b for b in self.budgets if b.get("user_id") == user_id and b.get("month") == month_prefix),
            None
        )
        if budget_record:
            total_budget = budget_record.get("budget_amount", monthly_income_total)
        else:
            total_budget = monthly_income_total

        remaining_budget = round(total_budget - monthly_expense_total, 2)
        monthly_savings = round(monthly_income_total - monthly_expense_total, 2)

        # Percentages
        if total_budget > 0:
            budget_used_pct = round((monthly_expense_total / total_budget) * 100, 1)
            budget_remaining_pct = round((remaining_budget / total_budget) * 100, 1)
        else:
            budget_used_pct = 0.0
            budget_remaining_pct = 0.0

        # Spending Trends
        monthly_spending = monthly_expense_total
        yearly_spending = round(
            sum(e.get("amount", 0.0) for e in expenses if e.get("date", "").startswith(year_prefix)),
            2
        )

        # Category Breakdowns for Expenses
        category_breakdown: Dict[str, float] = {}
        for e in monthly_expenses:
            cat = e.get("category", "Other")
            category_breakdown[cat] = round(category_breakdown.get(cat, 0.0) + e.get("amount", 0.0), 2)

        top_expense_category = "None"
        if category_breakdown:
            top_expense_category = max(category_breakdown, key=category_breakdown.get)

        current_month_summary = {
            "month": month_prefix,
            "income": monthly_income_total,
            "expense": monthly_expense_total,
            "budget": total_budget,
            "remaining": remaining_budget,
            "savings": monthly_savings,
            "used_pct": budget_used_pct,
            "remaining_pct": budget_remaining_pct,
            "exceeded": remaining_budget < 0
        }

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_savings": net_savings,
            "total_budget": total_budget,
            "budget_used": monthly_expense_total,
            "remaining_budget": remaining_budget,
            "savings": net_savings, # All-time savings
            "monthly_savings": monthly_savings,
            "budget_used_pct": budget_used_pct,
            "budget_remaining_pct": budget_remaining_pct,
            "monthly_spending": monthly_spending,
            "yearly_spending": yearly_spending,
            "top_expense_category": top_expense_category,
            "category_breakdown": category_breakdown,
            "current_month_summary": current_month_summary,
        }

    def get_user_financial_snapshot(self, user_id: int) -> Dict[str, Any]:
        """Backward compatible snapshot interface."""
        incomes = self.get_incomes(user_id)
        expenses = self.get_expenses(user_id)
        total_income = round(sum(item.get("amount", 0) for item in incomes), 2)
        total_expense = round(sum(item.get("amount", 0) for item in expenses), 2)
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": round(total_income - total_expense, 2),
            "income_records": incomes,
            "expense_records": expenses,
        }

    def get_recent_activity(self, user_id: int, limit: int = 6) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for record in self.incomes:
            if record.get("user_id") == user_id:
                entries.append({
                    "type": "income",
                    "amount": float(record.get("amount", 0.0)),
                    "category": record.get("category", "Salary"),
                    "description": record.get("description", "Income"),
                    "date": record.get("date", "")
                })
        for record in self.expenses:
            if record.get("user_id") == user_id:
                entries.append({
                    "type": "expense",
                    "amount": float(record.get("amount", 0.0)),
                    "category": record.get("category", "Food"),
                    "description": record.get("description", "Expense"),
                    "date": record.get("date", "")
                })
        entries.sort(key=lambda item: item["date"], reverse=True)
        return entries[:limit]

    def _next_id(self, items: List[Dict[str, Any]]) -> int:
        if not items:
            return 1
        return max(int(item.get("id", 0)) for item in items) + 1
