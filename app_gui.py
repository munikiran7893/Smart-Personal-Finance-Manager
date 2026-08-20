"""Tkinter-based desktop application for the Smart Personal Finance Manager."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Meter

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from fpdf import FPDF

from backend.auth import Authentication
from backend.finance import FinanceService
from backend.reports import ReportService
from backend.storage import StorageManager
from backend.utils import Utilities, Validation


class FinancePDF(FPDF):
    """Custom PDF generator matching corporate standards."""
    def header(self) -> None:
        self.set_font("helvetica", "B", 15)
        self.set_text_color(15, 23, 42) # Slate 900
        self.cell(0, 10, "Smart Personal Finance Manager", border=False, align="C")
        self.ln(12)
        
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139) # Slate 500
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", border=False, align="C")


class FinanceApp:
    """A professional desktop GUI for personal finance management using ttkbootstrap."""

    def __init__(self) -> None:
        self.root = tb.Window(themename="flatly")
        self.root.title("Smart Personal Finance Manager")
        self.root.geometry("1280x820")
        self.root.minsize(1120, 740)
        
        self.storage = StorageManager()
        self.auth_service = Authentication(self.storage)
        self.finance_service = FinanceService(self.storage)
        self.report_service = ReportService(self.storage)
        
        self.current_user: Optional[Dict[str, Any]] = None
        self.settings: Dict[str, Any] = {
            "theme": "flatly",
            "currency": "₹",
            "date_format": "YYYY-MM-DD"
        }
        
        # Navigation State
        self.current_frame: Optional[tb.Frame] = None
        self.sidebar_frame: Optional[tb.Frame] = None
        self.content_frame: Optional[tb.Frame] = None
        self.nav_buttons: Dict[str, tb.Button] = {}
        
        # Forms / Input Variables
        self.login_user_var = tk.StringVar()
        self.login_pass_var = tk.StringVar()
        self.reg_user_var = tk.StringVar()
        self.reg_disp_var = tk.StringVar()
        self.reg_pass_var = tk.StringVar()
        self.reg_confirm_var = tk.StringVar()
        
        # Monthly selection for views
        self.selected_month_var = tk.StringVar(value=Utilities.current_month())
        
        # Income variables
        self.income_id_var = tk.StringVar() # For edit tracking
        self.income_source_var = tk.StringVar()
        self.income_amount_var = tk.StringVar()
        self.income_date_var = tk.StringVar(value=Utilities.today())
        self.income_category_var = tk.StringVar(value="Salary")
        self.income_desc_var = tk.StringVar()
        self.income_notes_var = tk.StringVar()
        
        # Expense variables
        self.expense_id_var = tk.StringVar() # For edit tracking
        self.expense_name_var = tk.StringVar()
        self.expense_category_var = tk.StringVar(value="Food")
        self.expense_amount_var = tk.StringVar()
        self.expense_date_var = tk.StringVar(value=Utilities.today())
        self.expense_pm_var = tk.StringVar(value="Cash")
        self.expense_desc_var = tk.StringVar()
        self.expense_notes_var = tk.StringVar()
        
        self.show_login_screen()

    def apply_user_settings(self) -> None:
        """Loads and applies the logged-in user's settings."""
        if not self.current_user:
            return
        self.settings = self.auth_service.get_settings(self.current_user["id"])
        theme = self.settings.get("theme", "flatly")
        try:
            self.root.style.theme_use(theme)
        except Exception:
            pass

    def format_money(self, val: float) -> str:
        """Helper to format money using user's preferred currency symbol."""
        sym = self.settings.get("currency", "₹")
        return Utilities.format_currency(val, symbol=sym)

    def show_login_screen(self) -> None:
        """Draws the clean, modern login and registration tabbed interface."""
        self._clear_window()
        self.root.configure(bg="#f8fafc")
        
        main_container = tb.Frame(self.root, style="Card.TFrame")
        main_container.place(relx=0.5, rely=0.5, anchor="center", width=780, height=480)
        
        # Left Banner
        left_banner = tb.Frame(main_container, bootstyle="dark", width=340)
        left_banner.pack(side="left", fill="both")
        left_banner.pack_propagate(False)
        
        tb.Label(
            left_banner, 
            text="Smart Finance", 
            bootstyle="inverse-dark", 
            font=("Inter", 24, "bold")
        ).pack(anchor="w", padx=30, pady=(60, 5))
        
        tb.Label(
            left_banner, 
            text="Desktop Finance Assistant", 
            bootstyle="inverse-dark", 
            font=("Inter", 11)
        ).pack(anchor="w", padx=30, pady=(0, 20))
        
        desc = (
            "• Dynamic budget calculations\n"
            "• Matplotlib analytics and trends\n"
            "• Permanent report generation\n"
            "• CSV and PDF record exports\n"
            "• Custom UI themes and settings"
        )
        tb.Label(
            left_banner, 
            text=desc, 
            bootstyle="inverse-dark", 
            font=("Inter", 10), 
            justify="left"
        ).pack(anchor="w", padx=30, pady=30)
        
        # Right Form Area with Notebook for Login / Register tabs
        right_area = tb.Frame(main_container, padding=20)
        right_area.pack(side="left", fill="both", expand=True)
        
        notebook = tb.Notebook(right_area, bootstyle="primary")
        notebook.pack(fill="both", expand=True)
        
        # Login Frame
        login_frame = tb.Frame(notebook, padding=15)
        notebook.add(login_frame, text="  Login  ")
        
        tb.Label(login_frame, text="Sign in to your account", font=("Inter", 14, "bold")).pack(anchor="w", pady=(10, 20))
        
        tb.Label(login_frame, text="Username", font=("Inter", 9, "bold")).pack(anchor="w", pady=(5, 2))
        tb.Entry(login_frame, textvariable=self.login_user_var, bootstyle="secondary").pack(fill="x", pady=(0, 10))
        
        tb.Label(login_frame, text="Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=(5, 2))
        tb.Entry(login_frame, textvariable=self.login_pass_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 20))
        
        tb.Button(
            login_frame, 
            text="Sign In", 
            bootstyle="primary", 
            command=self.handle_login,
            cursor="hand2"
        ).pack(fill="x", pady=10)
        
        # Register Frame
        register_frame = tb.Frame(notebook, padding=15)
        notebook.add(register_frame, text="  Register  ")
        
        tb.Label(register_frame, text="Create a new account", font=("Inter", 14, "bold")).pack(anchor="w", pady=(5, 10))
        
        tb.Label(register_frame, text="Username", font=("Inter", 9, "bold")).pack(anchor="w", pady=(2, 1))
        tb.Entry(register_frame, textvariable=self.reg_user_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(register_frame, text="Display Name (Optional)", font=("Inter", 9, "bold")).pack(anchor="w", pady=(2, 1))
        tb.Entry(register_frame, textvariable=self.reg_disp_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(register_frame, text="Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=(2, 1))
        tb.Entry(register_frame, textvariable=self.reg_pass_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(register_frame, text="Confirm Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=(2, 1))
        tb.Entry(register_frame, textvariable=self.reg_confirm_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 12))
        
        tb.Button(
            register_frame, 
            text="Create Account", 
            bootstyle="success", 
            command=self.handle_register,
            cursor="hand2"
        ).pack(fill="x", pady=5)

    def handle_login(self) -> None:
        user = self.login_user_var.get().strip()
        pwd = self.login_pass_var.get()
        if not user or not pwd:
            messagebox.showerror("Error", "Please fill in all credentials.")
            return
        
        result = self.auth_service.login(user, pwd)
        if result:
            self.current_user = result
            self.apply_user_settings()
            self.show_main_app()
        else:
            messagebox.showerror("Authentication Failed", "Invalid username or password.")

    def handle_register(self) -> None:
        user = self.reg_user_var.get().strip()
        disp = self.reg_disp_var.get().strip()
        pwd = self.reg_pass_var.get()
        confirm = self.reg_confirm_var.get()
        
        if not user or not pwd:
            messagebox.showerror("Error", "Username and Password are required.")
            return
        
        if pwd != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
            
        try:
            self.auth_service.register(user, pwd, disp)
            messagebox.showinfo("Success", "Account created successfully! Please log in.")
            # Clear register inputs
            self.reg_user_var.set("")
            self.reg_disp_var.set("")
            self.reg_pass_var.set("")
            self.reg_confirm_var.set("")
        except ValueError as ex:
            messagebox.showerror("Registration Failed", str(ex))

    def handle_logout(self) -> None:
        self.current_user = None
        self.login_user_var.set("")
        self.login_pass_var.set("")
        try:
            self.root.style.theme_use("flatly") # Reset to default style
        except Exception:
            pass
        self.show_login_screen()

    def show_main_app(self) -> None:
        """Lays out the sidebar navigation and content frames."""
        self._clear_window()
        self.root.configure(bg="#f1f5f9")
        
        # Sidebar Frame
        self.sidebar_frame = tb.Frame(self.root, bootstyle="dark", width=220)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # User details banner
        disp_name = self.current_user.get("display_name", self.current_user["username"])
        tb.Label(
            self.sidebar_frame, 
            text=disp_name, 
            font=("Inter", 13, "bold"), 
            bootstyle="inverse-dark",
            anchor="center"
        ).pack(fill="x", padx=10, pady=(25, 2))
        
        tb.Label(
            self.sidebar_frame, 
            text=f"@{self.current_user['username']}", 
            font=("Inter", 9), 
            bootstyle="inverse-dark",
            foreground="#94a3b8",
            anchor="center"
        ).pack(fill="x", padx=10, pady=(0, 25))
        
        # Navigation Buttons list
        navs = [
            ("Dashboard", self.load_dashboard_tab),
            ("Income", self.load_income_tab),
            ("Expenses", self.load_expense_tab),
            ("Budget", self.load_budget_tab),
            ("Reports", self.load_reports_tab),
            ("Analytics", self.load_analytics_tab),
            ("Profile", self.load_profile_tab),
            ("Settings", self.load_settings_tab),
            ("Logout", self.handle_logout)
        ]
        
        for name, callback in navs:
            btn = tb.Button(
                self.sidebar_frame, 
                text=name, 
                bootstyle="dark-link", 
                padding=(15, 12), 
                command=callback,
                cursor="hand2"
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.nav_buttons[name.lower()] = btn

        # Main content area
        self.content_frame = tb.Frame(self.root, padding=20)
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        # Default load Dashboard
        self.load_dashboard_tab()

    def set_active_nav(self, nav_name: str) -> None:
        """Styles the active sidebar button."""
        for name, btn in self.nav_buttons.items():
            if name == nav_name.lower():
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="dark-link")

    def _clear_content(self) -> None:
        if self.current_frame:
            self.current_frame.destroy()

    def _clear_window(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    # ========================================================
    # 1. DASHBOARD TAB
    # ========================================================
    def load_dashboard_tab(self) -> None:
        self.set_active_nav("dashboard")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header Row
        header_row = tb.Frame(self.current_frame)
        header_row.pack(fill="x", pady=(0, 15))
        
        tb.Label(header_row, text="Financial Dashboard", font=("Inter", 20, "bold")).pack(side="left")
        
        # Quick month navigation
        month_nav = tb.Frame(header_row)
        month_nav.pack(side="right")
        tb.Label(month_nav, text="Month: ", font=("Inter", 10, "bold")).pack(side="left", padx=5)
        
        # Collect distinct months from transactions for selection
        months = sorted(list(set(
            [i["date"][:7] for i in self.finance_service.get_incomes(self.current_user["id"])] +
            [e["date"][:7] for e in self.finance_service.get_expenses(self.current_user["id"])] +
            [Utilities.current_month()]
        )), reverse=True)
        
        month_cb = tb.Combobox(
            month_nav, 
            textvariable=self.selected_month_var, 
            values=months, 
            width=9, 
            state="readonly"
        )
        month_cb.pack(side="left")
        month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_dashboard_tab())

        # Calculations snapshot
        calc = self.finance_service.get_financial_calculations(
            self.current_user["id"], 
            self.selected_month_var.get()
        )
        
        # Row 1: KPI Summary Cards
        cards_frame = tb.Frame(self.current_frame)
        cards_frame.pack(fill="x", pady=(0, 20))
        
        card_data = [
            ("Total Income", self.format_money(calc["total_income"]), "success"),
            ("Total Expenses", self.format_money(calc["total_expenses"]), "danger"),
            ("Current Savings", self.format_money(calc["net_savings"]), "info"),
            ("Remaining Budget", self.format_money(calc["remaining_budget"]), "warning" if not calc["current_month_summary"]["exceeded"] else "danger")
        ]
        
        for i, (title, value, color) in enumerate(card_data):
            card = tb.Frame(cards_frame, style="Card.TFrame")
            card.grid(row=0, column=i, sticky="nsew", padx=(0, 15) if i < 3 else 0)
            cards_frame.columnconfigure(i, weight=1)
            
            # Left accent bar
            accent = tb.Frame(card, bootstyle=color, width=5)
            accent.pack(side="left", fill="y")
            
            inner = tb.Frame(card, padding=15)
            inner.pack(fill="both", expand=True)
            tb.Label(inner, text=title, font=("Inter", 9, "bold"), foreground="#64748b").pack(anchor="w")
            tb.Label(inner, text=value, font=("Inter", 16, "bold"), bootstyle=color if "Remaining Budget" in title and calc["current_month_summary"]["exceeded"] else "").pack(anchor="w", pady=(6, 0))

        # Row 2: Budget Progress Bar
        budget_summary = calc["current_month_summary"]
        prog_frame = tb.Frame(self.current_frame, padding=15, style="Card.TFrame")
        prog_frame.pack(fill="x", pady=(0, 20))
        
        tb.Label(prog_frame, text="Budget Progress", font=("Inter", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        if budget_summary["exceeded"]:
            alert_text = f"⚠️ Budget Exceeded! Remaining Budget: {self.format_money(budget_summary['remaining'])}"
            tb.Label(prog_frame, text=alert_text, font=("Inter", 11, "bold"), bootstyle="danger").pack(anchor="w", pady=(0, 10))
        else:
            prog_text = f"Budget Used: {budget_summary['used_pct']}% of {self.format_money(budget_summary['budget'])} (Remaining: {self.format_money(budget_summary['remaining'])})"
            tb.Label(prog_frame, text=prog_text, font=("Inter", 10), foreground="#475569").pack(anchor="w", pady=(0, 10))
            
        tb.Progressbar(
            prog_frame, 
            value=min(budget_summary["used_pct"], 100), 
            bootstyle="danger" if budget_summary["exceeded"] else "success",
            maximum=100
        ).pack(fill="x")

        # Row 3: Grid split into Recent Transactions and Quick Statistics
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        # Left Panel - Recent Transactions
        recent_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame")
        recent_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        tb.Label(recent_panel, text="Recent Transactions", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Treeview
        tree_cols = ("date", "type", "category", "amount", "desc")
        tree = ttk.Treeview(recent_panel, columns=tree_cols, show="headings", height=8)
        tree.heading("date", text="Date", anchor="w")
        tree.heading("type", text="Type", anchor="w")
        tree.heading("category", text="Category", anchor="w")
        tree.heading("amount", text="Amount", anchor="e")
        tree.heading("desc", text="Description", anchor="w")
        
        tree.column("date", width=90, minwidth=80)
        tree.column("type", width=80, minwidth=70)
        tree.column("category", width=100, minwidth=80)
        tree.column("amount", width=110, anchor="e")
        tree.column("desc", width=160, minwidth=120)
        
        tree.pack(fill="both", expand=True)
        
        activity = self.finance_service.get_recent_activity(self.current_user["id"], limit=8)
        for act in activity:
            type_label = "Income" if act["type"] == "income" else "Expense"
            amt = self.format_money(act["amount"])
            if act["type"] == "expense":
                amt = f"- {amt}"
            tree.insert("", "end", values=(act["date"], type_label, act["category"], amt, act["description"]))

        # Right Panel - Quick Statistics
        stats_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame", width=340)
        stats_panel.pack(side="right", fill="both")
        stats_panel.pack_propagate(False)
        
        tb.Label(stats_panel, text="Quick Statistics", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 15))
        
        stats = [
            ("Top Expense Category", calc["top_expense_category"]),
            ("Monthly Expenses Total", self.format_money(calc["monthly_spending"])),
            ("Yearly Expenses Total", self.format_money(calc["yearly_spending"])),
            ("Monthly Incomes Total", self.format_money(budget_summary["income"])),
        ]
        
        for title, val in stats:
            box = tb.Frame(stats_panel)
            box.pack(fill="x", pady=8)
            tb.Label(box, text=title, font=("Inter", 9, "bold"), foreground="#64748b").pack(anchor="w")
            tb.Label(box, text=val, font=("Inter", 12, "bold")).pack(anchor="w", pady=(2, 0))

    # ========================================================
    # 2. INCOME TAB
    # ========================================================
    def load_income_tab(self) -> None:
        self.set_active_nav("income")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header
        header = tb.Frame(self.current_frame)
        header.pack(fill="x", pady=(0, 15))
        tb.Label(header, text="Income Records Manager", font=("Inter", 20, "bold")).pack(side="left")
        
        # Grid splits: Left has Form, Right has Table
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        # Left Side Form
        form_frame = tb.Frame(split_frame, padding=15, style="Card.TFrame", width=340)
        form_frame.pack(side="left", fill="both", padx=(0, 15))
        form_frame.pack_propagate(False)
        
        form_title = tb.Label(form_frame, text="Add Income Record", font=("Inter", 12, "bold"))
        form_title.pack(anchor="w", pady=(0, 15))
        
        tb.Label(form_frame, text="Income Source", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.income_source_var, bootstyle="secondary").pack(fill="x", pady=(0, 8))
        
        tb.Label(form_frame, text="Amount", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.income_amount_var, bootstyle="secondary").pack(fill="x", pady=(0, 8))
        
        tb.Label(form_frame, text="Date (YYYY-MM-DD)", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.income_date_var, bootstyle="secondary").pack(fill="x", pady=(0, 8))
        
        tb.Label(form_frame, text="Category", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        inc_categories = ["Salary", "Business", "Freelancing", "Investments", "Bonus", "Gift", "Other"]
        tb.Combobox(form_frame, textvariable=self.income_category_var, values=inc_categories, state="readonly").pack(fill="x", pady=(0, 8))
        
        tb.Label(form_frame, text="Description", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.income_desc_var, bootstyle="secondary").pack(fill="x", pady=(0, 8))
        
        tb.Label(form_frame, text="Notes (Optional)", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.income_notes_var, bootstyle="secondary").pack(fill="x", pady=(0, 15))
        
        btn_box = tb.Frame(form_frame)
        btn_box.pack(fill="x", pady=5)
        
        btn_save = tb.Button(
            btn_box, 
            text="Save Record", 
            bootstyle="primary", 
            command=self.save_income_record,
            cursor="hand2"
        )
        btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_clear = tb.Button(
            btn_box, 
            text="Clear", 
            bootstyle="secondary", 
            command=self.clear_income_form,
            cursor="hand2"
        )
        btn_clear.pack(side="left")
        
        # Right Side Table & Filter
        table_frame = tb.Frame(split_frame, padding=15, style="Card.TFrame")
        table_frame.pack(side="left", fill="both", expand=True)
        
        # Filter panel
        filter_bar = tb.Frame(table_frame)
        filter_bar.pack(fill="x", pady=(0, 15))
        
        tb.Label(filter_bar, text="Search: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tb.Entry(filter_bar, textvariable=search_var, width=15, bootstyle="secondary")
        search_entry.pack(side="left", padx=(0, 15))
        
        tb.Label(filter_bar, text="Category: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        filter_cat_var = tk.StringVar(value="All")
        filter_cat = tb.Combobox(filter_bar, textvariable=filter_cat_var, values=["All"] + inc_categories, width=10, state="readonly")
        filter_cat.pack(side="left", padx=(0, 15))
        
        tb.Label(filter_bar, text="Month: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        filter_month_var = tk.StringVar(value="All")
        months = sorted(list(set([i["date"][:7] for i in self.finance_service.get_incomes(self.current_user["id"])] + ["All"])), reverse=True)
        filter_month = tb.Combobox(filter_bar, textvariable=filter_month_var, values=months, width=9, state="readonly")
        filter_month.pack(side="left", padx=(0, 15))
        
        # Apply button
        def apply_income_filters() -> None:
            q = search_var.get()
            cat = filter_cat_var.get()
            m = filter_month_var.get()
            
            # Base filtering
            records = self.finance_service.get_incomes(self.current_user["id"])
            if q.strip():
                records = self.finance_service.search_incomes(self.current_user["id"], q)
            
            if cat != "All":
                records = [r for r in records if r.get("category", "") == cat]
            if m != "All":
                records = [r for r in records if r.get("date", "").startswith(m)]
                
            load_tree_data(records)
            
        tb.Button(filter_bar, text="Apply", bootstyle="primary-outline", padding=(10, 4), command=apply_income_filters, cursor="hand2").pack(side="left")
        
        # Treeview
        tree_cols = ("id", "date", "source", "category", "amount", "desc", "notes")
        tree = ttk.Treeview(table_frame, columns=tree_cols, show="headings")
        tree.heading("id", text="ID", anchor="center")
        tree.heading("date", text="Date", anchor="w")
        tree.heading("source", text="Source", anchor="w")
        tree.heading("category", text="Category", anchor="w")
        tree.heading("amount", text="Amount", anchor="e")
        tree.heading("desc", text="Description", anchor="w")
        tree.heading("notes", text="Notes", anchor="w")
        
        tree.column("id", width=40, anchor="center")
        tree.column("date", width=90)
        tree.column("source", width=120)
        tree.column("category", width=90)
        tree.column("amount", width=100, anchor="e")
        tree.column("desc", width=140)
        tree.column("notes", width=120)
        
        tree.pack(fill="both", expand=True)
        
        def load_tree_data(data_list: List[Dict[str, Any]]) -> None:
            for item in tree.get_children():
                tree.delete(item)
            for r in data_list:
                notes = r.get("notes", "")
                tree.insert(
                    "", 
                    "end", 
                    values=(
                        r["id"], 
                        r["date"], 
                        r.get("source", r.get("category", "General")), 
                        r.get("category", "Other"), 
                        self.format_money(r["amount"]), 
                        r["description"], 
                        notes
                    )
                )
                
        # Load initial
        initial_records = self.finance_service.get_incomes(self.current_user["id"])
        load_tree_data(initial_records)
        
        # Row selection behavior
        def on_tree_select(event: Any) -> None:
            selected = tree.selection()
            if not selected:
                return
            values = tree.item(selected[0])["values"]
            
            # Fetch actual record
            record_id = int(values[0])
            for r in self.finance_service.get_incomes(self.current_user["id"]):
                if r["id"] == record_id:
                    self.income_id_var.set(str(r["id"]))
                    self.income_source_var.set(r.get("source", ""))
                    self.income_amount_var.set(str(r["amount"]))
                    self.income_date_var.set(r["date"])
                    self.income_category_var.set(r.get("category", "Other"))
                    self.income_desc_var.set(r["description"])
                    self.income_notes_var.set(r.get("notes", ""))
                    form_title.configure(text="Edit Income Record")
                    break
                    
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        # Action Buttons row below table
        action_row = tb.Frame(table_frame)
        action_row.pack(fill="x", pady=(10, 0))
        
        def delete_selected_income() -> None:
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a record from the table to delete.")
                return
            record_id = int(tree.item(selected[0])["values"][0])
            confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this income record?")
            if confirm:
                try:
                    self.finance_service.delete_income(self.current_user["id"], record_id)
                    messagebox.showinfo("Success", "Income record deleted.")
                    self.clear_income_form()
                    self.load_income_tab()
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
                    
        tb.Button(action_row, text="Delete Selected", bootstyle="danger", command=delete_selected_income, cursor="hand2").pack(side="left")

    def save_income_record(self) -> None:
        source = self.income_source_var.get().strip()
        amt = self.income_amount_var.get().strip()
        dt = self.income_date_var.get().strip()
        cat = self.income_category_var.get()
        desc = self.income_desc_var.get().strip()
        notes = self.income_notes_var.get().strip()
        
        if not source or not amt or not dt:
            messagebox.showerror("Error", "Source, Amount, and Date fields are required.")
            return
            
        # Parse / Edit ID
        edit_id = self.income_id_var.get()
        
        try:
            if edit_id:
                # Update mode
                self.finance_service.update_income(
                    user_id=self.current_user["id"],
                    income_id=int(edit_id),
                    amount=amt,
                    category=cat,
                    description=desc,
                    date=dt,
                    source=source,
                    notes=notes
                )
                messagebox.showinfo("Success", "Income record updated successfully.")
            else:
                # Add mode
                self.finance_service.add_income(
                    user_id=self.current_user["id"],
                    amount=amt,
                    category=cat,
                    description=desc,
                    date=dt,
                    source=source,
                    notes=notes
                )
                messagebox.showinfo("Success", "Income record added successfully.")
                
            self.clear_income_form()
            self.load_income_tab()
        except ValueError as ex:
            messagebox.showerror("Invalid Input", str(ex))

    def clear_income_form(self) -> None:
        self.income_id_var.set("")
        self.income_source_var.set("")
        self.income_amount_var.set("")
        self.income_date_var.set(Utilities.today())
        self.income_category_var.set("Salary")
        self.income_desc_var.set("")
        self.income_notes_var.set("")
        # Reset form title
        if hasattr(self, "current_frame") and self.current_frame:
            for widget in self.current_frame.winfo_children():
                # find form label
                for child in widget.winfo_children():
                    if child.winfo_class() == "TLabel" and child.cget("text") == "Edit Income Record":
                        child.configure(text="Add Income Record")

    # ========================================================
    # 3. EXPENSES TAB
    # ========================================================
    def load_expense_tab(self) -> None:
        self.set_active_nav("expenses")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header
        header = tb.Frame(self.current_frame)
        header.pack(fill="x", pady=(0, 15))
        tb.Label(header, text="Expense Records Manager", font=("Inter", 20, "bold")).pack(side="left")
        
        # Grid splits: Left has Form, Right has Table
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        # Left Side Form
        form_frame = tb.Frame(split_frame, padding=15, style="Card.TFrame", width=340)
        form_frame.pack(side="left", fill="both", padx=(0, 15))
        form_frame.pack_propagate(False)
        
        form_title = tb.Label(form_frame, text="Add Expense Record", font=("Inter", 12, "bold"))
        form_title.pack(anchor="w", pady=(0, 12))
        
        tb.Label(form_frame, text="Expense Name", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.expense_name_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Amount", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.expense_amount_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Date (YYYY-MM-DD)", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.expense_date_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Category", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        exp_categories = ["Food", "Shopping", "Bills", "Travel", "Medical", "Education", "Entertainment", "Transport", "Utilities", "Other"]
        tb.Combobox(form_frame, textvariable=self.expense_category_var, values=exp_categories, state="readonly").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Payment Method", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        pm_methods = ["Cash", "Credit Card", "Debit Card", "Net Banking", "UPI", "Other"]
        tb.Combobox(form_frame, textvariable=self.expense_pm_var, values=pm_methods, state="readonly").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Description", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.expense_desc_var, bootstyle="secondary").pack(fill="x", pady=(0, 6))
        
        tb.Label(form_frame, text="Notes (Optional)", font=("Inter", 9, "bold")).pack(anchor="w", pady=(4, 1))
        tb.Entry(form_frame, textvariable=self.expense_notes_var, bootstyle="secondary").pack(fill="x", pady=(0, 12))
        
        btn_box = tb.Frame(form_frame)
        btn_box.pack(fill="x", pady=5)
        
        btn_save = tb.Button(
            btn_box, 
            text="Save Record", 
            bootstyle="primary", 
            command=self.save_expense_record,
            cursor="hand2"
        )
        btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_clear = tb.Button(
            btn_box, 
            text="Clear", 
            bootstyle="secondary", 
            command=self.clear_expense_form,
            cursor="hand2"
        )
        btn_clear.pack(side="left")
        
        # Right Side Table & Filter
        table_frame = tb.Frame(split_frame, padding=15, style="Card.TFrame")
        table_frame.pack(side="left", fill="both", expand=True)
        
        # Filter panel
        filter_bar = tb.Frame(table_frame)
        filter_bar.pack(fill="x", pady=(0, 15))
        
        tb.Label(filter_bar, text="Search: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tb.Entry(filter_bar, textvariable=search_var, width=12, bootstyle="secondary")
        search_entry.pack(side="left", padx=(0, 10))
        
        tb.Label(filter_bar, text="Category: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        filter_cat_var = tk.StringVar(value="All")
        filter_cat = tb.Combobox(filter_bar, textvariable=filter_cat_var, values=["All"] + exp_categories, width=9, state="readonly")
        filter_cat.pack(side="left", padx=(0, 10))
        
        tb.Label(filter_bar, text="Method: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        filter_pm_var = tk.StringVar(value="All")
        filter_pm = tb.Combobox(filter_bar, textvariable=filter_pm_var, values=["All"] + pm_methods, width=9, state="readonly")
        filter_pm.pack(side="left", padx=(0, 10))
        
        tb.Label(filter_bar, text="Month: ", font=("Inter", 9, "bold")).pack(side="left", padx=(0, 5))
        filter_month_var = tk.StringVar(value="All")
        months = sorted(list(set([e["date"][:7] for e in self.finance_service.get_expenses(self.current_user["id"])] + ["All"])), reverse=True)
        filter_month = tb.Combobox(filter_bar, textvariable=filter_month_var, values=months, width=9, state="readonly")
        filter_month.pack(side="left", padx=(0, 10))
        
        # Apply button
        def apply_expense_filters() -> None:
            q = search_var.get()
            cat = filter_cat_var.get()
            pm = filter_pm_var.get()
            m = filter_month_var.get()
            
            records = self.finance_service.get_expenses(self.current_user["id"])
            if q.strip():
                records = self.finance_service.search_expenses(self.current_user["id"], q)
            
            if cat != "All":
                records = [r for r in records if r.get("category", "") == cat]
            if pm != "All":
                records = [r for r in records if r.get("payment_method", "") == pm]
            if m != "All":
                records = [r for r in records if r.get("date", "").startswith(m)]
                
            load_tree_data(records)
            
        tb.Button(filter_bar, text="Apply", bootstyle="primary-outline", padding=(10, 4), command=apply_expense_filters, cursor="hand2").pack(side="left")
        
        # Treeview
        tree_cols = ("id", "date", "name", "category", "pm", "amount", "desc", "notes")
        tree = ttk.Treeview(table_frame, columns=tree_cols, show="headings")
        tree.heading("id", text="ID", anchor="center")
        tree.heading("date", text="Date", anchor="w")
        tree.heading("name", text="Name", anchor="w")
        tree.heading("category", text="Category", anchor="w")
        tree.heading("pm", text="Method", anchor="w")
        tree.heading("amount", text="Amount", anchor="e")
        tree.heading("desc", text="Description", anchor="w")
        tree.heading("notes", text="Notes", anchor="w")
        
        tree.column("id", width=40, anchor="center")
        tree.column("date", width=90)
        tree.column("name", width=110)
        tree.column("category", width=90)
        tree.column("pm", width=90)
        tree.column("amount", width=100, anchor="e")
        tree.column("desc", width=120)
        tree.column("notes", width=100)
        
        tree.pack(fill="both", expand=True)
        
        def load_tree_data(data_list: List[Dict[str, Any]]) -> None:
            for item in tree.get_children():
                tree.delete(item)
            for r in data_list:
                notes = r.get("notes", "")
                name = r.get("name", r.get("category", "General"))
                pm = r.get("payment_method", "Cash")
                tree.insert(
                    "", 
                    "end", 
                    values=(
                        r["id"], 
                        r["date"], 
                        name, 
                        r.get("category", "Other"), 
                        pm, 
                        self.format_money(r["amount"]), 
                        r["description"], 
                        notes
                    )
                )
                
        # Load initial
        initial_records = self.finance_service.get_expenses(self.current_user["id"])
        load_tree_data(initial_records)
        
        # Row selection behavior
        def on_tree_select(event: Any) -> None:
            selected = tree.selection()
            if not selected:
                return
            values = tree.item(selected[0])["values"]
            
            # Fetch actual record
            record_id = int(values[0])
            for r in self.finance_service.get_expenses(self.current_user["id"]):
                if r["id"] == record_id:
                    self.expense_id_var.set(str(r["id"]))
                    self.expense_name_var.set(r.get("name", ""))
                    self.expense_amount_var.set(str(r["amount"]))
                    self.expense_date_var.set(r["date"])
                    self.expense_category_var.set(r.get("category", "Other"))
                    self.expense_pm_var.set(r.get("payment_method", "Cash"))
                    self.expense_desc_var.set(r["description"])
                    self.expense_notes_var.set(r.get("notes", ""))
                    form_title.configure(text="Edit Expense Record")
                    break
                    
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        # Action Buttons row below table
        action_row = tb.Frame(table_frame)
        action_row.pack(fill="x", pady=(10, 0))
        
        def delete_selected_expense() -> None:
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a record from the table to delete.")
                return
            record_id = int(tree.item(selected[0])["values"][0])
            confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this expense record?")
            if confirm:
                try:
                    self.finance_service.delete_expense(self.current_user["id"], record_id)
                    messagebox.showinfo("Success", "Expense record deleted.")
                    self.clear_expense_form()
                    self.load_expense_tab()
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
                    
        tb.Button(action_row, text="Delete Selected", bootstyle="danger", command=delete_selected_expense, cursor="hand2").pack(side="left")

    def save_expense_record(self) -> None:
        name = self.expense_name_var.get().strip()
        amt = self.expense_amount_var.get().strip()
        dt = self.expense_date_var.get().strip()
        cat = self.expense_category_var.get()
        pm = self.expense_pm_var.get()
        desc = self.expense_desc_var.get().strip()
        notes = self.expense_notes_var.get().strip()
        
        if not name or not amt or not dt:
            messagebox.showerror("Error", "Name, Amount, and Date fields are required.")
            return
            
        edit_id = self.expense_id_var.get()
        
        try:
            if edit_id:
                # Update mode
                self.finance_service.update_expense(
                    user_id=self.current_user["id"],
                    expense_id=int(edit_id),
                    amount=amt,
                    category=cat,
                    description=desc,
                    date=dt,
                    name=name,
                    payment_method=pm,
                    notes=notes
                )
                messagebox.showinfo("Success", "Expense record updated successfully.")
            else:
                # Add mode
                self.finance_service.add_expense(
                    user_id=self.current_user["id"],
                    amount=amt,
                    category=cat,
                    description=desc,
                    date=dt,
                    name=name,
                    payment_method=pm,
                    notes=notes
                )
                messagebox.showinfo("Success", "Expense record added successfully.")
                
            self.clear_expense_form()
            self.load_expense_tab()
        except ValueError as ex:
            messagebox.showerror("Invalid Input", str(ex))

    def clear_expense_form(self) -> None:
        self.expense_id_var.set("")
        self.expense_name_var.set("")
        self.expense_amount_var.set("")
        self.expense_date_var.set(Utilities.today())
        self.expense_category_var.set("Food")
        self.expense_pm_var.set("Cash")
        self.expense_desc_var.set("")
        self.expense_notes_var.set("")
        # Reset form title
        if hasattr(self, "current_frame") and self.current_frame:
            for widget in self.current_frame.winfo_children():
                for child in widget.winfo_children():
                    if child.winfo_class() == "TLabel" and child.cget("text") == "Edit Expense Record":
                        child.configure(text="Add Expense Record")

    # ========================================================
    # 4. BUDGET TAB
    # ========================================================
    def load_budget_tab(self) -> None:
        self.set_active_nav("budget")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header Row
        header_row = tb.Frame(self.current_frame)
        header_row.pack(fill="x", pady=(0, 15))
        
        tb.Label(header_row, text="Monthly Budget Tracker", font=("Inter", 20, "bold")).pack(side="left")
        
        # Month navigation dropdown
        month_nav = tb.Frame(header_row)
        month_nav.pack(side="right")
        tb.Label(month_nav, text="Select Month: ", font=("Inter", 10, "bold")).pack(side="left", padx=5)
        
        months = sorted(list(set(
            [i["date"][:7] for i in self.finance_service.get_incomes(self.current_user["id"])] +
            [e["date"][:7] for e in self.finance_service.get_expenses(self.current_user["id"])] +
            [Utilities.current_month()]
        )), reverse=True)
        
        month_cb = tb.Combobox(month_nav, textvariable=self.selected_month_var, values=months, width=9, state="readonly")
        month_cb.pack(side="left")
        month_cb.bind("<<ComboboxSelected>>", lambda e: self.load_budget_tab())

        # Calculations
        calc = self.finance_service.get_financial_calculations(
            self.current_user["id"], 
            self.selected_month_var.get()
        )
        summary = calc["current_month_summary"]
        
        # If budget exceeded, show the massive RED Alert
        if summary["exceeded"]:
            alert_frame = tb.Frame(self.current_frame, bootstyle="danger", padding=15)
            alert_frame.pack(fill="x", pady=(0, 20))
            alert_text = f"⚠️ Budget Exceeded! Remaining Budget: {self.format_money(summary['remaining'])}"
            tb.Label(alert_frame, text=alert_text, font=("Inter", 14, "bold"), bootstyle="inverse-danger").pack(anchor="center")
            
        # Layout metrics row
        metrics_frame = tb.Frame(self.current_frame)
        metrics_frame.pack(fill="x", pady=(0, 20))
        
        budget_cards = [
            ("Total Budget (from Income)", self.format_money(summary["budget"]), "success"),
            ("Budget Used (Expenses)", self.format_money(summary["expense"]), "danger"),
            ("Remaining Budget", self.format_money(summary["remaining"]), "warning" if not summary["exceeded"] else "danger"),
            ("Monthly Savings", self.format_money(summary["savings"]), "info"),
            ("Budget Used %", f"{summary['used_pct']}%", "primary"),
            ("Budget Remaining %", f"{summary['remaining_pct']}%", "success" if not summary["exceeded"] else "danger")
        ]
        
        # Grid layout for cards (3 columns, 2 rows)
        for idx, (title, value, color) in enumerate(budget_cards):
            r = idx // 3
            c = idx % 3
            card = tb.Frame(metrics_frame, style="Card.TFrame")
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
            metrics_frame.columnconfigure(c, weight=1)
            
            accent = tb.Frame(card, bootstyle=color, width=4)
            accent.pack(side="left", fill="y")
            
            inner = tb.Frame(card, padding=12)
            inner.pack(fill="both", expand=True)
            tb.Label(inner, text=title, font=("Inter", 9, "bold"), foreground="#64748b").pack(anchor="w")
            tb.Label(inner, text=value, font=("Inter", 14, "bold"), bootstyle=color if "Remaining Budget" in title and summary["exceeded"] else "").pack(anchor="w", pady=(4, 0))

        # Bottom graphic display (Gauge meter style)
        meter_frame = tb.Frame(self.current_frame, padding=20, style="Card.TFrame")
        meter_frame.pack(fill="both", expand=True)
        
        tb.Label(meter_frame, text="Budget Usage Meter", font=("Inter", 12, "bold")).pack(anchor="center", pady=(0, 10))
        
        # Use Meter widget if safe, or a nice formatted canvas.
        meter = Meter(
            meter_frame,
            metersize=180,
            padding=5,
            amountused=int(min(summary["used_pct"], 100)),
            amounttotal=100,
            subtext="Used %",
            textright="%",
            bootstyle="danger" if summary["exceeded"] else "success",
            stripethickness=10,
        )
        meter.pack(anchor="center")

    # ========================================================
    # 5. REPORTS TAB
    # ========================================================
    def load_reports_tab(self) -> None:
        self.set_active_nav("reports")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header
        header = tb.Frame(self.current_frame)
        header.pack(fill="x", pady=(0, 15))
        tb.Label(header, text="Permanent Reports Center", font=("Inter", 20, "bold")).pack(side="left")
        
        # Grid splits: Left: Saved Reports tree, Right: Details Viewer & Generator
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        # Left Panel: Saved list
        list_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame", width=380)
        list_panel.pack(side="left", fill="both", padx=(0, 15))
        list_panel.pack_propagate(False)
        
        tb.Label(list_panel, text="Saved Reports", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        tree = ttk.Treeview(list_panel, columns=("title", "type", "period"), show="headings", height=15)
        tree.heading("title", text="Report Title", anchor="w")
        tree.heading("type", text="Type", anchor="w")
        tree.heading("period", text="Period", anchor="center")
        
        tree.column("title", width=180)
        tree.column("type", width=80)
        tree.column("period", width=70, anchor="center")
        tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Load reports list
        def reload_reports_tree() -> None:
            for item in tree.get_children():
                tree.delete(item)
            monthly = self.report_service.get_saved_reports(self.current_user["id"], "monthly")
            yearly = self.report_service.get_saved_reports(self.current_user["id"], "yearly")
            all_reports = monthly + yearly
            # Sort by generated_at
            all_reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
            for r in all_reports:
                tree.insert("", "end", values=(r["title"], r["type"], r["period"]), tags=(str(r["id"]), r["type"]))
                
        reload_reports_tree()
        
        # Right Panel: Viewer & Generator
        viewer_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame")
        viewer_panel.pack(side="right", fill="both", expand=True)
        
        # Tabs for "Viewer" vs "Generator"
        notebook = tb.Notebook(viewer_panel, bootstyle="secondary")
        notebook.pack(fill="both", expand=True)
        
        view_tab = tb.Frame(notebook, padding=15)
        notebook.add(view_tab, text="  View Report  ")
        
        gen_tab = tb.Frame(notebook, padding=15)
        notebook.add(gen_tab, text="  Generate New Report  ")
        
        # --- VIEW TAB LAYOUT ---
        viewer_scroll = tb.Canvas(view_tab, borderwidth=0, highlightthickness=0)
        v_scroll = tb.Scrollbar(view_tab, orient="vertical", command=viewer_scroll.yview)
        viewer_content = tb.Frame(viewer_scroll)
        
        viewer_scroll.create_window((0, 0), window=viewer_content, anchor="nw")
        viewer_scroll.configure(yscrollcommand=v_scroll.set)
        
        viewer_scroll.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        
        def update_scrollregion(e: Any = None) -> None:
            viewer_scroll.update_idletasks()
            viewer_scroll.configure(scrollregion=viewer_scroll.bbox("all"))
        viewer_content.bind("<Configure>", update_scrollregion)
        
        # Selected report state
        current_report: Dict[str, Any] = {}
        
        def show_report_details(report: Dict[str, Any]) -> None:
            nonlocal current_report
            current_report = report
            
            # Clear previous details
            for child in viewer_content.winfo_children():
                child.destroy()
                
            # Draw header
            tb.Label(viewer_content, text=report["title"], font=("Inter", 16, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 5))
            tb.Label(viewer_content, text=f"Generated on: {report['generated_at']}", font=("Inter", 9), foreground="#64748b").pack(anchor="w", pady=(0, 15))
            
            # KPI Cards
            cards = tb.Frame(viewer_content)
            cards.pack(fill="x", pady=(0, 15))
            
            sum_idx = 0
            for label, value in report["summary"].items():
                title = label.replace("_", " ").title()
                val_str = self.format_money(value) if isinstance(value, (int, float)) and "count" not in label.lower() else str(value)
                
                c = tb.Frame(cards, style="Card.TFrame")
                c.grid(row=0, column=sum_idx, sticky="nsew", padx=(0, 10))
                cards.columnconfigure(sum_idx, weight=1)
                
                tb.Label(c, text=title, font=("Inter", 8, "bold"), foreground="#64748b").pack(anchor="w", padx=10, pady=(10, 2))
                tb.Label(c, text=val_str, font=("Inter", 12, "bold")).pack(anchor="w", padx=10, pady=(0, 10))
                sum_idx += 1
                
            # Details listing based on type
            tb.Label(viewer_content, text="Detailed Items", font=("Inter", 11, "bold")).pack(anchor="w", pady=(10, 5))
            
            det_frame = tb.Frame(viewer_content)
            det_frame.pack(fill="both", expand=True)
            
            rep_type = report["type"]
            details = report["details"]
            
            if rep_type in ("Monthly", "Income", "Expense"):
                headers = ["ID", "Name/Source", "Category", "Amount", "Date"]
                rows = []
                if "incomes" in details:
                    for i in details["incomes"]:
                        rows.append([i["id"], i["source"], i["category"], self.format_money(i["amount"]), i["date"]])
                if "expenses" in details:
                    for e in details["expenses"]:
                        rows.append([e["id"], e["name"], e["category"], self.format_money(e["amount"]), e["date"]])
                if "expenses" not in details and "incomes" not in details: # singular reports
                    items = details.get("expenses", details.get("incomes", []))
                    for item in items:
                        rows.append([item["id"], item.get("source", item.get("name")), item["category"], self.format_money(item["amount"]), item["date"]])
                
                # Render clean table inside det_frame
                for col_idx, h in enumerate(headers):
                    tb.Label(det_frame, text=h, font=("Inter", 9, "bold"), anchor="w").grid(row=0, column=col_idx, sticky="w", padx=10, pady=5)
                for r_idx, row in enumerate(rows):
                    for col_idx, val in enumerate(row):
                        tb.Label(det_frame, text=str(val), font=("Inter", 9)).grid(row=r_idx+1, column=col_idx, sticky="w", padx=10, pady=4)
                        
            elif rep_type == "Yearly":
                headers = ["Month", "Income", "Expenses", "Savings"]
                breakdown = details.get("monthly_breakdown", {})
                for col_idx, h in enumerate(headers):
                    tb.Label(det_frame, text=h, font=("Inter", 9, "bold")).grid(row=0, column=col_idx, sticky="w", padx=10, pady=5)
                for r_idx, (m_str, val_dict) in enumerate(sorted(breakdown.items())):
                    tb.Label(det_frame, text=m_str).grid(row=r_idx+1, column=0, sticky="w", padx=10, pady=4)
                    tb.Label(det_frame, text=self.format_money(val_dict["income"])).grid(row=r_idx+1, column=1, sticky="w", padx=10, pady=4)
                    tb.Label(det_frame, text=self.format_money(val_dict["expense"])).grid(row=r_idx+1, column=2, sticky="w", padx=10, pady=4)
                    tb.Label(det_frame, text=self.format_money(val_dict["savings"])).grid(row=r_idx+1, column=3, sticky="w", padx=10, pady=4)
                    
            elif rep_type == "Savings":
                tb.Label(det_frame, text=f"Total Income: {self.format_money(report['summary']['total_income'])}").pack(anchor="w", pady=2)
                tb.Label(det_frame, text=f"Total Expense: {self.format_money(report['summary']['total_expense'])}").pack(anchor="w", pady=2)
                tb.Label(det_frame, text=f"Net Savings: {self.format_money(report['summary']['net_savings'])}").pack(anchor="w", pady=2)
                tb.Label(det_frame, text=f"Savings Percentage: {report['summary']['savings_percentage']}%").pack(anchor="w", pady=2)
                
            elif rep_type == "Category":
                amounts = details.get("category_amounts", {})
                counts = details.get("category_counts", {})
                headers = ["Category", "Amount Spent", "Transactions Count"]
                for col_idx, h in enumerate(headers):
                    tb.Label(det_frame, text=h, font=("Inter", 9, "bold")).grid(row=0, column=col_idx, sticky="w", padx=15, pady=5)
                for r_idx, (cat, val) in enumerate(amounts.items()):
                    tb.Label(det_frame, text=cat).grid(row=r_idx+1, column=0, sticky="w", padx=15, pady=4)
                    tb.Label(det_frame, text=self.format_money(val)).grid(row=r_idx+1, column=1, sticky="w", padx=15, pady=4)
                    tb.Label(det_frame, text=str(counts.get(cat, 0))).grid(row=r_idx+1, column=2, sticky="w", padx=15, pady=4)
                    
            # Add Export Buttons
            export_box = tb.Frame(viewer_content, padding=(0, 20))
            export_box.pack(fill="x")
            
            tb.Button(
                export_box, 
                text="Export to CSV", 
                bootstyle="success-outline", 
                command=lambda: export_active_report("csv"),
                cursor="hand2"
            ).pack(side="left", padx=5)
            
            tb.Button(
                export_box, 
                text="Export to PDF", 
                bootstyle="danger-outline", 
                command=lambda: export_active_report("pdf"),
                cursor="hand2"
            ).pack(side="left", padx=5)
            
            notebook.select(0)
            update_scrollregion()
            
        def export_active_report(format_type: str) -> None:
            if not current_report:
                messagebox.showerror("Error", "No report loaded to export.")
                return
                
            export_dir = self.storage.exports_dir
            export_dir.mkdir(parents=True, exist_ok=True)
            
            rep_title = current_report["title"]
            rep_type = current_report["type"]
            period = current_report["period"]
            
            safe_title = rep_title.lower().replace(" ", "_").replace("-", "_")
            
            if format_type == "csv":
                filepath = export_dir / f"{safe_title}.csv"
                with filepath.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Report Title", rep_title])
                    writer.writerow(["Generated At", current_report["generated_at"]])
                    writer.writerow([])
                    
                    # Summary
                    writer.writerow(["SUMMARY METRICS"])
                    for key, val in current_report["summary"].items():
                        writer.writerow([key.replace("_", " ").title(), val])
                    writer.writerow([])
                    
                    # Details
                    writer.writerow(["DETAILED RECORDS"])
                    details = current_report["details"]
                    if rep_type in ("Monthly", "Income", "Expense"):
                        writer.writerow(["ID", "Name/Source", "Category", "Amount", "Date"])
                        items = []
                        if "incomes" in details:
                            items += details["incomes"]
                        if "expenses" in details:
                            items += details["expenses"]
                        for i in items:
                            writer.writerow([i["id"], i.get("source", i.get("name")), i["category"], i["amount"], i["date"]])
                    elif rep_type == "Yearly":
                        writer.writerow(["Month", "Income", "Expenses", "Savings"])
                        for m_str, val in sorted(details.get("monthly_breakdown", {}).items()):
                            writer.writerow([m_str, val["income"], val["expense"], val["savings"]])
                    elif rep_type == "Category":
                        writer.writerow(["Category", "Amount Spent"])
                        for cat, amt in details.get("category_amounts", {}).items():
                            writer.writerow([cat, amt])
                            
                messagebox.showinfo("Export Successful", f"Report saved as CSV in:\n{filepath}")
                
            elif format_type == "pdf":
                filepath = export_dir / f"{safe_title}.pdf"
                pdf = FinancePDF()
                pdf.alias_nb_pages()
                pdf.add_page()
                
                pdf.set_font("helvetica", "B", 13)
                pdf.set_text_color(37, 99, 235) # Blue 600
                pdf.cell(0, 10, rep_title, new_x="LMARGIN", new_y="NEXT", align="L")
                pdf.ln(5)
                
                # Summary Section
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 8, "Summary Metrics", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 10)
                for key, val in current_report["summary"].items():
                    pdf.cell(60, 6, f"{key.replace('_', ' ').title()}:", border=0)
                    pdf.cell(0, 6, f"{val}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(8)
                
                # Details Table
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(0, 8, "Detailed Records", new_x="LMARGIN", new_y="NEXT")
                
                details = current_report["details"]
                if rep_type in ("Monthly", "Income", "Expense"):
                    headers = ["ID", "Name/Source", "Category", "Amount", "Date"]
                    col_width = 190 / len(headers)
                    pdf.set_font("helvetica", "B", 9)
                    for h in headers:
                        pdf.cell(col_width, 8, h, border=1, align="C")
                    pdf.ln()
                    
                    pdf.set_font("helvetica", "", 9)
                    items = []
                    if "incomes" in details:
                        items += details["incomes"]
                    if "expenses" in details:
                        items += details["expenses"]
                    fill = False
                    for i in items:
                        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                        pdf.cell(col_width, 7, str(i["id"]), border=1, fill=True)
                        pdf.cell(col_width, 7, str(i.get("source", i.get("name"))), border=1, fill=True)
                        pdf.cell(col_width, 7, str(i["category"]), border=1, fill=True)
                        pdf.cell(col_width, 7, self.format_money(i["amount"]), border=1, fill=True)
                        pdf.cell(col_width, 7, str(i["date"]), border=1, fill=True)
                        pdf.ln()
                        fill = not fill
                        
                elif rep_type == "Yearly":
                    headers = ["Month", "Income", "Expenses", "Savings"]
                    col_width = 190 / len(headers)
                    pdf.set_font("helvetica", "B", 9)
                    for h in headers:
                        pdf.cell(col_width, 8, h, border=1, align="C")
                    pdf.ln()
                    
                    pdf.set_font("helvetica", "", 9)
                    fill = False
                    for m_str, val in sorted(details.get("monthly_breakdown", {}).items()):
                        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                        pdf.cell(col_width, 7, m_str, border=1, fill=True)
                        pdf.cell(col_width, 7, self.format_money(val["income"]), border=1, fill=True)
                        pdf.cell(col_width, 7, self.format_money(val["expense"]), border=1, fill=True)
                        pdf.cell(col_width, 7, self.format_money(val["savings"]), border=1, fill=True)
                        pdf.ln()
                        fill = not fill
                        
                elif rep_type == "Category":
                    headers = ["Category", "Amount Spent"]
                    col_width = 190 / len(headers)
                    pdf.set_font("helvetica", "B", 9)
                    for h in headers:
                        pdf.cell(col_width, 8, h, border=1, align="C")
                    pdf.ln()
                    
                    pdf.set_font("helvetica", "", 9)
                    fill = False
                    for cat, amt in details.get("category_amounts", {}).items():
                        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                        pdf.cell(col_width, 7, cat, border=1, fill=True)
                        pdf.cell(col_width, 7, self.format_money(amt), border=1, fill=True)
                        pdf.ln()
                        fill = not fill
                else:
                    pdf.set_font("helvetica", "", 10)
                    pdf.cell(0, 10, "Savings Trend analysis metrics printed above.", new_x="LMARGIN", new_y="NEXT")
                    
                pdf.output(filepath)
                messagebox.showinfo("Export Successful", f"Report saved as PDF in:\n{filepath}")

        # Bind select to load details
        def on_saved_select(e: Any) -> None:
            sel = tree.selection()
            if not sel:
                return
            tags = tree.item(sel[0])["tags"]
            rep_id = int(tags[0])
            rep_type = tags[1]
            
            # Fetch report details
            report_class = "yearly" if rep_type == "Yearly" else "monthly"
            reports_list = self.report_service.get_saved_reports(self.current_user["id"], report_class)
            rep = next((r for r in reports_list if r["id"] == rep_id), None)
            if rep:
                show_report_details(rep)
                
        tree.bind("<<TreeviewSelect>>", on_saved_select)

        # Delete report command
        def delete_report() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select a report from the table to delete.")
                return
            tags = tree.item(sel[0])["tags"]
            rep_id = int(tags[0])
            rep_type = tags[1]
            confirm = messagebox.askyesno("Confirm Delete", "Permanently delete this saved report?")
            if confirm:
                try:
                    report_class = "yearly" if rep_type == "Yearly" else "monthly"
                    self.report_service.delete_saved_report(self.current_user["id"], rep_id, report_class)
                    messagebox.showinfo("Success", "Report deleted.")
                    reload_reports_tree()
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
                    
        tb.Button(list_panel, text="Delete Selected", bootstyle="danger", command=delete_report, cursor="hand2").pack(fill="x")
        
        # --- GENERATOR TAB LAYOUT ---
        tb.Label(gen_tab, text="Generate Financial Report", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 15))
        
        tb.Label(gen_tab, text="Report Type", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        rep_types = ["Monthly Report", "Yearly Report", "Income Report", "Expense Report", "Savings Report", "Category Report"]
        type_var = tk.StringVar(value="Monthly Report")
        type_cb = tb.Combobox(gen_tab, textvariable=type_var, values=rep_types, state="readonly")
        type_cb.pack(fill="x", pady=(0, 10))
        
        tb.Label(gen_tab, text="Period (Month as YYYY-MM or Year as YYYY)", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        period_var = tk.StringVar(value=Utilities.current_month())
        tb.Entry(gen_tab, textvariable=period_var, bootstyle="secondary").pack(fill="x", pady=(0, 20))
        
        def run_report_generation() -> None:
            rt = type_var.get()
            period = period_var.get().strip()
            if not period:
                messagebox.showerror("Error", "Please specify a period.")
                return
                
            try:
                # Validate length of period based on type
                if rt == "Yearly Report":
                    if len(period) != 4:
                        raise ValueError("Yearly report period must be YYYY format.")
                elif rt == "Monthly Report":
                    if len(period) != 7:
                        raise ValueError("Monthly report period must be YYYY-MM format.")
                
                # Generate
                if rt == "Monthly Report":
                    rep = self.report_service.generate_monthly_report(self.current_user["id"], period)
                elif rt == "Yearly Report":
                    rep = self.report_service.generate_yearly_report(self.current_user["id"], period)
                elif rt == "Income Report":
                    rep = self.report_service.generate_income_report(self.current_user["id"], period)
                elif rt == "Expense Report":
                    rep = self.report_service.generate_expense_report(self.current_user["id"], period)
                elif rt == "Savings Report":
                    rep = self.report_service.generate_savings_report(self.current_user["id"], period)
                else:
                    rep = self.report_service.generate_category_report(self.current_user["id"], period)
                    
                messagebox.showinfo("Success", f"{rt} generated and saved permanently!")
                reload_reports_tree()
                show_report_details(rep)
            except ValueError as ex:
                messagebox.showerror("Invalid Input", str(ex))
                
        tb.Button(gen_tab, text="Generate & Save", bootstyle="primary", command=run_report_generation, cursor="hand2").pack(fill="x", pady=10)

    # ========================================================
    # 6. ANALYTICS TAB
    # ========================================================
    def load_analytics_tab(self) -> None:
        self.set_active_nav("analytics")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header Row
        header_row = tb.Frame(self.current_frame)
        header_row.pack(fill="x", pady=(0, 15))
        
        tb.Label(header_row, text="Matplotlib Financial Analytics", font=("Inter", 20, "bold")).pack(side="left")
        
        # Grid splits: Left sidebar to choose chart, Right area to draw
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        opts_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame", width=300)
        opts_panel.pack(side="left", fill="both", padx=(0, 15))
        opts_panel.pack_propagate(False)
        
        tb.Label(opts_panel, text="Select Analytics Chart", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 15))
        
        charts = [
            ("Expense Pie Chart", "pie"),
            ("Income vs Expense Bar Chart", "bar"),
            ("Monthly Expense Line Graph", "line"),
            ("Budget Usage Doughnut Chart", "doughnut"),
            ("Monthly Comparison Graph", "monthly_comp"),
            ("Yearly Expense Comparison Graph", "yearly_exp"),
            ("Yearly Income Comparison Graph", "yearly_inc"),
            ("Savings Trend Graph", "savings_trend")
        ]
        
        chart_var = tk.StringVar(value="pie")
        
        # Content frame for chart rendering
        chart_panel = tb.Frame(split_frame, padding=15, style="Card.TFrame")
        chart_panel.pack(side="left", fill="both", expand=True)
        
        def render_selected_chart() -> None:
            # Clear previous canvas
            for child in chart_panel.winfo_children():
                child.destroy()
                
            ctype = chart_var.get()
            
            incomes = self.finance_service.get_incomes(self.current_user["id"])
            expenses = self.finance_service.get_expenses(self.current_user["id"])
            
            fig = Figure(figsize=(7.5, 5), dpi=100)
            fig.patch.set_facecolor('#ffffff')
            ax = fig.add_subplot(111)
            
            # Palette matching
            colors_pie = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#64748b"]
            
            if ctype == "pie":
                # Expense Breakdown
                cat_amounts: Dict[str, float] = {}
                for e in expenses:
                    cat = e.get("category", "Other")
                    cat_amounts[cat] = cat_amounts.get(cat, 0.0) + e["amount"]
                
                if cat_amounts:
                    labels = list(cat_amounts.keys())
                    values = list(cat_amounts.values())
                    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors_pie[:len(labels)])
                    ax.set_title("Expense Categories Distribution")
                else:
                    ax.text(0.5, 0.5, "No Expense Records Available", ha="center", va="center")
                    
            elif ctype == "bar":
                # Income vs Expense Bar Chart
                inc_total = sum(i["amount"] for i in incomes)
                exp_total = sum(e["amount"] for e in expenses)
                labels = ["Income", "Expenses"]
                values = [inc_total, exp_total]
                
                ax.bar(labels, values, color=["#10b981", "#ef4444"], width=0.4)
                ax.set_ylabel("Amount")
                ax.set_title("Total Income vs Total Expenses")
                for index, val in enumerate(values):
                    ax.text(index, val + (val * 0.02 or 1.0), self.format_money(val), ha="center")
                    
            elif ctype == "line":
                # Monthly Expense Line
                monthly_exp: Dict[str, float] = {}
                for e in expenses:
                    m = e["date"][:7]
                    monthly_exp[m] = monthly_exp.get(m, 0.0) + e["amount"]
                
                if monthly_exp:
                    sorted_months = sorted(monthly_exp.keys())
                    values = [monthly_exp[m] for m in sorted_months]
                    ax.plot(sorted_months, values, marker="o", color="#ef4444", linewidth=2)
                    ax.set_ylabel("Spent Amount")
                    ax.set_title("Monthly Expense Spending Trend")
                    ax.grid(True, linestyle="--", alpha=0.5)
                else:
                    ax.text(0.5, 0.5, "No Expense Data Available", ha="center", va="center")
                    
            elif ctype == "doughnut":
                # Budget Doughnut
                calc = self.finance_service.get_financial_calculations(self.current_user["id"])
                summary = calc["current_month_summary"]
                used = summary["expense"]
                rem = max(summary["remaining"], 0)
                
                if used > 0 or rem > 0:
                    labels = ["Used", "Remaining"]
                    values = [used, rem]
                    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=["#ef4444", "#10b981"], wedgeprops=dict(width=0.4))
                    ax.set_title(f"Budget Utilization Doughnut - {summary['month']}")
                else:
                    ax.text(0.5, 0.5, "No Budget Data Available for Current Month", ha="center", va="center")
                    
            elif ctype == "monthly_comp":
                # Monthly Comparison (Income vs Expense bar chart per month)
                comp: Dict[str, Dict[str, float]] = {}
                for i in incomes:
                    m = i["date"][:7]
                    if m not in comp: comp[m] = {"inc": 0.0, "exp": 0.0}
                    comp[m]["inc"] += i["amount"]
                for e in expenses:
                    m = e["date"][:7]
                    if m not in comp: comp[m] = {"inc": 0.0, "exp": 0.0}
                    comp[m]["exp"] += e["amount"]
                
                if comp:
                    sorted_months = sorted(comp.keys())[-6:] # Latest 6 months
                    x = range(len(sorted_months))
                    inc_vals = [comp[m]["inc"] for m in sorted_months]
                    exp_vals = [comp[m]["exp"] for m in sorted_months]
                    
                    ax.bar([i - 0.2 for i in x], inc_vals, width=0.4, label="Income", color="#10b981")
                    ax.bar([i + 0.2 for i in x], exp_vals, width=0.4, label="Expense", color="#ef4444")
                    ax.set_xticks(x)
                    ax.set_xticklabels(sorted_months)
                    ax.set_title("Monthly Income vs Expense Comparison")
                    ax.legend()
                else:
                    ax.text(0.5, 0.5, "No Comparison Data Available", ha="center", va="center")
                    
            elif ctype == "yearly_exp":
                # Yearly Expense Comparison Graph
                yearly_exp: Dict[str, float] = {}
                for e in expenses:
                    y = e["date"][:4]
                    yearly_exp[y] = yearly_exp.get(y, 0.0) + e["amount"]
                
                if yearly_exp:
                    sorted_years = sorted(yearly_exp.keys())
                    values = [yearly_exp[y] for y in sorted_years]
                    ax.bar(sorted_years, values, color="#f59e0b", width=0.4)
                    ax.set_ylabel("Expenses Total")
                    ax.set_title("Yearly Expense Comparisons")
                else:
                    ax.text(0.5, 0.5, "No Yearly Data Available", ha="center", va="center")
                    
            elif ctype == "yearly_inc":
                # Yearly Income Comparison Graph
                yearly_inc: Dict[str, float] = {}
                for i in incomes:
                    y = i["date"][:4]
                    yearly_inc[y] = yearly_inc.get(y, 0.0) + i["amount"]
                
                if yearly_inc:
                    sorted_years = sorted(yearly_inc.keys())
                    values = [yearly_inc[y] for y in sorted_years]
                    ax.bar(sorted_years, values, color="#3b82f6", width=0.4)
                    ax.set_ylabel("Income Total")
                    ax.set_title("Yearly Income Comparisons")
                else:
                    ax.text(0.5, 0.5, "No Yearly Income Data Available", ha="center", va="center")
                    
            else:
                # Savings Trend Graph
                monthly_savings: Dict[str, float] = {}
                months_list = list(set([i["date"][:7] for i in incomes] + [e["date"][:7] for e in expenses]))
                for m in months_list:
                    inc_m = sum(i["amount"] for i in incomes if i["date"].startswith(m))
                    exp_m = sum(e["amount"] for e in expenses if e["date"].startswith(m))
                    monthly_savings[m] = round(inc_m - exp_m, 2)
                    
                if monthly_savings:
                    sorted_months = sorted(monthly_savings.keys())
                    values = [monthly_savings[m] for m in sorted_months]
                    ax.plot(sorted_months, values, marker="o", color="#3b82f6", linewidth=2)
                    ax.set_ylabel("Net Savings")
                    ax.set_title("Monthly Net Savings Trend")
                    ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)
                    ax.grid(True, linestyle="--", alpha=0.5)
                else:
                    ax.text(0.5, 0.5, "No Savings Trend Data Available", ha="center", va="center")
                    
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=chart_panel)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        for label, val in charts:
            tb.Radiobutton(
                opts_panel, 
                text=label, 
                variable=chart_var, 
                value=val, 
                command=render_selected_chart,
                bootstyle="primary",
                cursor="hand2"
            ).pack(anchor="w", pady=10)
            
        render_selected_chart()

    # ========================================================
    # 7. PROFILE TAB
    # ========================================================
    def load_profile_tab(self) -> None:
        self.set_active_nav("profile")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header Row
        header_row = tb.Frame(self.current_frame)
        header_row.pack(fill="x", pady=(0, 15))
        tb.Label(header_row, text="User Profile Manager", font=("Inter", 20, "bold")).pack(side="left")
        
        # Grid layout
        split_frame = tb.Frame(self.current_frame)
        split_frame.pack(fill="both", expand=True)
        
        # Left Info card
        info_panel = tb.Frame(split_frame, padding=20, style="Card.TFrame", width=420)
        info_panel.pack(side="left", fill="both", padx=(0, 15))
        info_panel.pack_propagate(False)
        
        tb.Label(info_panel, text="Account Details", font=("Inter", 14, "bold")).pack(anchor="w", pady=(0, 15))
        
        disp_name = self.current_user.get("display_name", self.current_user["username"])
        details = [
            ("Username", self.current_user["username"]),
            ("Display Name", disp_name),
            ("Registration Date", self.current_user.get("created_at", "N/A")),
            ("Theme Preference", self.settings.get("theme", "flatly").title())
        ]
        
        for k, v in details:
            box = tb.Frame(info_panel)
            box.pack(fill="x", pady=6)
            tb.Label(box, text=k, font=("Inter", 9, "bold"), foreground="#64748b").pack(anchor="w")
            tb.Label(box, text=v, font=("Inter", 11, "bold")).pack(anchor="w", pady=(2, 0))
            
        # Snapshot metrics
        snapshot = self.finance_service.get_user_financial_snapshot(self.current_user["id"])
        tb.Label(info_panel, text="Financial Snapshot", font=("Inter", 12, "bold")).pack(anchor="w", pady=(20, 10))
        
        snap_details = [
            ("Total Income Record Count", str(len(snapshot["income_records"]))),
            ("Total Expense Record Count", str(len(snapshot["expense_records"]))),
            ("Current Wallet Balance / Net Savings", self.format_money(snapshot["net_savings"]))
        ]
        for k, v in snap_details:
            box = tb.Frame(info_panel)
            box.pack(fill="x", pady=5)
            tb.Label(box, text=k, font=("Inter", 9), foreground="#64748b").pack(anchor="w")
            tb.Label(box, text=v, font=("Inter", 11, "bold")).pack(anchor="w", pady=(2, 0))

        # Right Edit panel
        edit_panel = tb.Frame(split_frame, padding=20, style="Card.TFrame")
        edit_panel.pack(side="left", fill="both", expand=True)
        
        tb.Label(edit_panel, text="Edit Profile Information", font=("Inter", 14, "bold")).pack(anchor="w", pady=(0, 15))
        
        tb.Label(edit_panel, text="New Display Name", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        disp_name_var = tk.StringVar(value=disp_name)
        tb.Entry(edit_panel, textvariable=disp_name_var, bootstyle="secondary").pack(fill="x", pady=(0, 15))
        
        def save_display_name() -> None:
            new_disp = disp_name_var.get().strip()
            try:
                updated_user = self.auth_service.update_profile(self.current_user["id"], new_disp)
                self.current_user = updated_user
                messagebox.showinfo("Success", "Display name updated successfully.")
                self.load_profile_tab()
                # Update sidebar too
                self.show_main_app()
            except ValueError as ex:
                messagebox.showerror("Error", str(ex))
                
        tb.Button(edit_panel, text="Update Display Name", bootstyle="primary", command=save_display_name, cursor="hand2").pack(anchor="w", pady=(0, 30))
        
        tb.Label(edit_panel, text="Change Password", font=("Inter", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        tb.Label(edit_panel, text="Current Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=2)
        old_pass_var = tk.StringVar()
        tb.Entry(edit_panel, textvariable=old_pass_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 10))
        
        tb.Label(edit_panel, text="New Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=2)
        new_pass_var = tk.StringVar()
        tb.Entry(edit_panel, textvariable=new_pass_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 10))
        
        tb.Label(edit_panel, text="Confirm Password", font=("Inter", 9, "bold")).pack(anchor="w", pady=2)
        confirm_pass_var = tk.StringVar()
        tb.Entry(edit_panel, textvariable=confirm_pass_var, show="*", bootstyle="secondary").pack(fill="x", pady=(0, 15))
        
        def save_new_password() -> None:
            old_p = old_pass_var.get()
            new_p = new_pass_var.get()
            conf_p = confirm_pass_var.get()
            
            if new_p != conf_p:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            try:
                self.auth_service.change_password(self.current_user["id"], old_p, new_p)
                messagebox.showinfo("Success", "Password changed successfully.")
                old_pass_var.set("")
                new_pass_var.set("")
                confirm_pass_var.set("")
            except ValueError as ex:
                messagebox.showerror("Error", str(ex))
                
        tb.Button(edit_panel, text="Update Password", bootstyle="success", command=save_new_password, cursor="hand2").pack(anchor="w")

    # ========================================================
    # 8. SETTINGS TAB
    # ========================================================
    def load_settings_tab(self) -> None:
        self.set_active_nav("settings")
        self._clear_content()
        
        self.current_frame = tb.Frame(self.content_frame)
        self.current_frame.pack(fill="both", expand=True)
        
        # Header Row
        header_row = tb.Frame(self.current_frame)
        header_row.pack(fill="x", pady=(0, 15))
        tb.Label(header_row, text="Application Settings", font=("Inter", 20, "bold")).pack(side="left")
        
        box = tb.Frame(self.current_frame, padding=25, style="Card.TFrame", width=500)
        box.pack(anchor="nw")
        
        tb.Label(box, text="Preferences", font=("Inter", 14, "bold")).pack(anchor="w", pady=(0, 20))
        
        # Theme dropdown
        tb.Label(box, text="Theme Color Selection", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        themes = ["flatly", "cosmo", "minty", "sandstone", "darkly", "cyborg", "superhero"]
        theme_var = tk.StringVar(value=self.settings.get("theme", "flatly"))
        theme_cb = tb.Combobox(box, textvariable=theme_var, values=themes, state="readonly")
        theme_cb.pack(fill="x", pady=(0, 15))
        
        # Currency symbol dropdown
        tb.Label(box, text="Default Currency Symbol", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        currencies = ["₹", "$", "€", "£", "¥", "Custom"]
        curr_var = tk.StringVar(value=self.settings.get("currency", "₹"))
        curr_cb = tb.Combobox(box, textvariable=curr_var, values=currencies, state="readonly")
        curr_cb.pack(fill="x", pady=(0, 15))
        
        # Date format dropdown
        tb.Label(box, text="Default Date Format", font=("Inter", 9, "bold")).pack(anchor="w", pady=4)
        formats = ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]
        format_var = tk.StringVar(value=self.settings.get("date_format", "YYYY-MM-DD"))
        format_cb = tb.Combobox(box, textvariable=format_var, values=formats, state="readonly")
        format_cb.pack(fill="x", pady=(0, 20))
        
        def save_user_settings() -> None:
            t = theme_var.get()
            c = curr_var.get()
            f = format_var.get()
            
            try:
                self.settings = self.auth_service.update_settings(
                    user_id=self.current_user["id"],
                    theme=t,
                    currency=c,
                    date_format=f
                )
                messagebox.showinfo("Success", "Settings saved successfully.")
                self.apply_user_settings()
                self.load_settings_tab()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                
        tb.Button(box, text="Save Settings Preferences", bootstyle="primary", command=save_user_settings, cursor="hand2").pack(fill="x")

    def run(self) -> None:
        self.root.mainloop()


def launch_app() -> None:
    app = FinanceApp()
    app.run()


if __name__ == "__main__":
    launch_app()
