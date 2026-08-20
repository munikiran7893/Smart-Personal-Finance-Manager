"""Reporting service layer for permanent report generation and tracking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.storage import StorageManager
from backend.utils import Utilities


class ReportService:
    """Generate, save, and retrieve permanent reports for a user."""

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def _get_filename(self, report_class: str) -> str:
        if report_class.lower() == "yearly":
            return "yearly_reports.json"
        return "monthly_reports.json"

    def get_saved_reports(self, user_id: int, report_class: str = "monthly") -> List[Dict[str, Any]]:
        filename = self._get_filename(report_class)
        reports = self.storage.read_json(filename, [])
        user_reports = [r for r in reports if r.get("user_id") == user_id]
        user_reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return user_reports

    def delete_saved_report(self, user_id: int, report_id: int, report_class: str = "monthly") -> None:
        filename = self._get_filename(report_class)
        reports = self.storage.read_json(filename, [])
        original_len = len(reports)
        reports = [
            r for r in reports
            if not (r.get("id") == report_id and r.get("user_id") == user_id)
        ]
        if len(reports) == original_len:
            raise ValueError("Report not found.")
        self.storage.write_json(filename, reports)

    def save_report(self, user_id: int, report_type: str, period: str, title: str, summary: Dict[str, Any], details: Any, report_class: str = "monthly") -> Dict[str, Any]:
        filename = self._get_filename(report_class)
        reports = self.storage.read_json(filename, [])
        
        # Check if identical report exists to prevent duplicates
        existing = next(
            (r for r in reports if r.get("user_id") == user_id and r.get("type") == report_type and r.get("period") == period),
            None
        )
        
        report_id = existing["id"] if existing else (max([r.get("id", 0) for r in reports] + [0]) + 1)
        
        report_record = {
            "id": report_id,
            "user_id": user_id,
            "type": report_type,
            "period": period,
            "title": title,
            "summary": summary,
            "details": details,
            "generated_at": Utilities.timestamp(),
        }

        if existing:
            # Update existing
            for idx, r in enumerate(reports):
                if r["id"] == report_id:
                    reports[idx] = report_record
                    break
        else:
            reports.append(report_record)
            
        self.storage.write_json(filename, reports)
        return report_record

    def generate_monthly_report(self, user_id: int, month: str) -> Dict[str, Any]:
        """Generates and permanently saves a monthly report."""
        month_prefix = month[:7]
        incomes = self.storage.read_json("income.json", [])
        expenses = self.storage.read_json("expenses.json", [])
        
        user_incomes = [
            r for r in incomes
            if r.get("user_id") == user_id and r.get("date", "").startswith(month_prefix)
        ]
        user_expenses = [
            r for r in expenses
            if r.get("user_id") == user_id and r.get("date", "").startswith(month_prefix)
        ]
        
        total_income = round(sum(r.get("amount", 0.0) for r in user_incomes), 2)
        total_expense = round(sum(r.get("amount", 0.0) for r in user_expenses), 2)
        net_savings = round(total_income - total_expense, 2)
        
        # Calculate categories
        cat_breakdown: Dict[str, float] = {}
        for r in user_expenses:
            cat = r.get("category", "Other")
            cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + r.get("amount", 0.0), 2)
            
        summary = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "income_count": len(user_incomes),
            "expense_count": len(user_expenses),
        }
        
        details = {
            "incomes": [
                {"id": r["id"], "source": r.get("source", r.get("category", "General")), "amount": r["amount"], "date": r["date"], "category": r.get("category", "Other")}
                for r in user_incomes
            ],
            "expenses": [
                {"id": r["id"], "name": r.get("name", r.get("category", "General")), "category": r.get("category", "Other"), "amount": r["amount"], "date": r["date"], "payment_method": r.get("payment_method", "Cash")}
                for r in user_expenses
            ],
            "category_breakdown": cat_breakdown
        }
        
        title = f"Monthly Financial Report - {month_prefix}"
        return self.save_report(user_id, "Monthly", month_prefix, title, summary, details, "monthly")

    def generate_yearly_report(self, user_id: int, year: str) -> Dict[str, Any]:
        """Generates and permanently saves a yearly report."""
        year_prefix = year[:4]
        incomes = self.storage.read_json("income.json", [])
        expenses = self.storage.read_json("expenses.json", [])
        
        user_incomes = [
            r for r in incomes
            if r.get("user_id") == user_id and r.get("date", "").startswith(year_prefix)
        ]
        user_expenses = [
            r for r in expenses
            if r.get("user_id") == user_id and r.get("date", "").startswith(year_prefix)
        ]
        
        total_income = round(sum(r.get("amount", 0.0) for r in user_incomes), 2)
        total_expense = round(sum(r.get("amount", 0.0) for r in user_expenses), 2)
        net_savings = round(total_income - total_expense, 2)
        
        # Monthly breakdown
        monthly_breakdown: Dict[str, Dict[str, float]] = {}
        for m in range(1, 13):
            month_str = f"{year_prefix}-{m:02d}"
            monthly_breakdown[month_str] = {"income": 0.0, "expense": 0.0, "savings": 0.0}
            
        for r in user_incomes:
            m_str = r.get("date", "")[:7]
            if m_str in monthly_breakdown:
                monthly_breakdown[m_str]["income"] += r["amount"]
                
        for r in user_expenses:
            m_str = r.get("date", "")[:7]
            if m_str in monthly_breakdown:
                monthly_breakdown[m_str]["expense"] += r["amount"]
                
        for m_str in monthly_breakdown:
            inc = monthly_breakdown[m_str]["income"]
            exp = monthly_breakdown[m_str]["expense"]
            monthly_breakdown[m_str]["savings"] = round(inc - exp, 2)
            monthly_breakdown[m_str]["income"] = round(inc, 2)
            monthly_breakdown[m_str]["expense"] = round(exp, 2)
            
        summary = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "income_count": len(user_incomes),
            "expense_count": len(user_expenses),
        }
        
        details = {
            "monthly_breakdown": monthly_breakdown
        }
        
        title = f"Yearly Financial Report - {year_prefix}"
        return self.save_report(user_id, "Yearly", year_prefix, title, summary, details, "yearly")

    def generate_income_report(self, user_id: int, period: str = "All-Time") -> Dict[str, Any]:
        """Generates and permanently saves an Income Report."""
        incomes = self.storage.read_json("income.json", [])
        user_incomes = [r for r in incomes if r.get("user_id") == user_id]
        
        if period != "All-Time":
            user_incomes = [r for r in user_incomes if r.get("date", "").startswith(period)]
            
        total_income = round(sum(r.get("amount", 0.0) for r in user_incomes), 2)
        
        cat_breakdown: Dict[str, float] = {}
        for r in user_incomes:
            cat = r.get("category", "Other")
            cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + r.get("amount", 0.0), 2)
            
        summary = {
            "total_income": total_income,
            "income_count": len(user_incomes),
        }
        
        details = {
            "incomes": [
                {"id": r["id"], "source": r.get("source", r.get("category", "General")), "amount": r["amount"], "date": r["date"], "category": r.get("category", "Other")}
                for r in user_incomes
            ],
            "category_breakdown": cat_breakdown
        }
        
        title = f"Income Report - {period}"
        report_class = "monthly" if len(period) == 7 else "yearly"
        return self.save_report(user_id, "Income", period, title, summary, details, report_class)

    def generate_expense_report(self, user_id: int, period: str = "All-Time") -> Dict[str, Any]:
        """Generates and permanently saves an Expense Report."""
        expenses = self.storage.read_json("expenses.json", [])
        user_expenses = [r for r in expenses if r.get("user_id") == user_id]
        
        if period != "All-Time":
            user_expenses = [r for r in user_expenses if r.get("date", "").startswith(period)]
            
        total_expense = round(sum(r.get("amount", 0.0) for r in user_expenses), 2)
        
        cat_breakdown: Dict[str, float] = {}
        pm_breakdown: Dict[str, float] = {}
        for r in user_expenses:
            cat = r.get("category", "Other")
            cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + r.get("amount", 0.0), 2)
            
            pm = r.get("payment_method", "Cash")
            pm_breakdown[pm] = round(pm_breakdown.get(pm, 0.0) + r.get("amount", 0.0), 2)
            
        summary = {
            "total_expense": total_expense,
            "expense_count": len(user_expenses),
        }
        
        details = {
            "expenses": [
                {"id": r["id"], "name": r.get("name", r.get("category", "General")), "category": r.get("category", "Other"), "amount": r["amount"], "date": r["date"], "payment_method": r.get("payment_method", "Cash")}
                for r in user_expenses
            ],
            "category_breakdown": cat_breakdown,
            "payment_method_breakdown": pm_breakdown
        }
        
        title = f"Expense Report - {period}"
        report_class = "monthly" if len(period) == 7 else "yearly"
        return self.save_report(user_id, "Expense", period, title, summary, details, report_class)

    def generate_savings_report(self, user_id: int, period: str = "All-Time") -> Dict[str, Any]:
        """Generates and permanently saves a Savings Report."""
        incomes = self.storage.read_json("income.json", [])
        expenses = self.storage.read_json("expenses.json", [])
        
        user_incomes = [r for r in incomes if r.get("user_id") == user_id]
        user_expenses = [r for r in expenses if r.get("user_id") == user_id]
        
        if period != "All-Time":
            user_incomes = [r for r in user_incomes if r.get("date", "").startswith(period)]
            user_expenses = [r for r in user_expenses if r.get("date", "").startswith(period)]
            
        total_income = round(sum(r.get("amount", 0.0) for r in user_incomes), 2)
        total_expense = round(sum(r.get("amount", 0.0) for r in user_expenses), 2)
        net_savings = round(total_income - total_expense, 2)
        savings_pct = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0
        
        summary = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_percentage": savings_pct
        }
        
        details = {
            "income_count": len(user_incomes),
            "expense_count": len(user_expenses),
        }
        
        title = f"Savings Report - {period}"
        report_class = "monthly" if len(period) == 7 else "yearly"
        return self.save_report(user_id, "Savings", period, title, summary, details, report_class)

    def generate_category_report(self, user_id: int, period: str = "All-Time") -> Dict[str, Any]:
        """Generates and permanently saves a Category (Spending Breakdown) Report."""
        expenses = self.storage.read_json("expenses.json", [])
        user_expenses = [r for r in expenses if r.get("user_id") == user_id]
        
        if period != "All-Time":
            user_expenses = [r for r in user_expenses if r.get("date", "").startswith(period)]
            
        total_expense = round(sum(r.get("amount", 0.0) for r in user_expenses), 2)
        
        cat_breakdown: Dict[str, float] = {}
        cat_counts: Dict[str, int] = {}
        for r in user_expenses:
            cat = r.get("category", "Other")
            cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + r.get("amount", 0.0), 2)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
        summary = {
            "total_expense": total_expense,
            "unique_categories": len(cat_breakdown),
        }
        
        details = {
            "category_amounts": cat_breakdown,
            "category_counts": cat_counts
        }
        
        title = f"Category Expense Report - {period}"
        report_class = "monthly" if len(period) == 7 else "yearly"
        return self.save_report(user_id, "Category", period, title, summary, details, report_class)

    def generate_summary(self, user_id: int) -> Dict[str, Any]:
        """Generates a transient summary for backward compatibility."""
        income_records = [record for record in self.storage.read_json("income.json", []) if record.get("user_id") == user_id]
        expense_records = [record for record in self.storage.read_json("expenses.json", []) if record.get("user_id") == user_id]
        total_income = round(sum(item.get("amount", 0) for item in income_records), 2)
        total_expense = round(sum(item.get("amount", 0) for item in expense_records), 2)
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": round(total_income - total_expense, 2),
            "income_count": len(income_records),
            "expense_count": len(expense_records),
            "generated_at": Utilities.timestamp(),
        }

    def category_breakdown(self, user_id: int) -> Dict[str, float]:
        """Generates transient category breakdown for backward compatibility."""
        expense_records = [record for record in self.storage.read_json("expenses.json", []) if record.get("user_id") == user_id]
        breakdown: Dict[str, float] = {}
        for record in expense_records:
            category = record.get("category", "General")
            breakdown[category] = breakdown.get(category, 0.0) + float(record.get("amount", 0))
        return {key: round(value, 2) for key, value in sorted(breakdown.items())}
