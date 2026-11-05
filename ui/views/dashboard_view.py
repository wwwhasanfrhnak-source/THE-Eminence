"""Responsive, data-backed dashboard for the workspace."""

import tkinter as tk
from datetime import date

from config.theme import BG_CARD, BG_MAIN, PRIMARY, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY
from core.repository import Repository
from ui.components.charts import DonutChart, LineChart
from ui.components.kpi_card import KPICard
from ui.components.modern_card import ModernCard
from ui.theme import BORDER, PURPLE, SECONDARY, SUCCESS
from utils.formatters import format_currency


class DashboardView(tk.Frame):
    def __init__(self, master, font_family, repository=None):
        super().__init__(master, bg=BG_MAIN)
        self.font_family = font_family
        self.repository = repository or Repository()
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=BG_MAIN)
        header.pack(fill="x", pady=(0, 16))
        tk.Label(
            header,
            text="Workspace overview",
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=f"Your business at a glance · {date.today():%A, %B %d, %Y}",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 9),
        ).pack(anchor="w", pady=(4, 0))

        stats = self.repository.dashboard_stats()
        cards = tk.Frame(self, bg=BG_MAIN)
        cards.pack(fill="x", pady=(0, 16))
        for column in range(4):
            cards.grid_columnconfigure(column, weight=1, uniform="kpi")
        kpis = (
            (
                "Customers",
                f"{stats['customers']:,}",
                "In your workspace",
                PRIMARY,
                [2, 4, 3, 5, 6, 8],
            ),
            (
                "Active projects",
                f"{stats['projects']:,}",
                "Across all statuses",
                SECONDARY,
                [3, 2, 4, 5, 6, 7],
            ),
            (
                "Total revenue",
                format_currency(float(stats["revenue"])),
                "Recorded income",
                SUCCESS,
                [2, 3, 3, 5, 6, 8],
            ),
            (
                "Team members",
                f"{stats['users']:,}",
                "Registered accounts",
                PURPLE,
                [3, 3, 4, 4, 5, 6],
            ),
        )
        self.kpi_cards = []
        for column, values in enumerate(kpis):
            card = KPICard(cards, *values, self.font_family)
            card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
            self.kpi_cards.append(card)

        charts = tk.Frame(self, bg=BG_MAIN)
        charts.pack(fill="both", expand=True)
        charts.grid_columnconfigure(0, weight=3, uniform="charts")
        charts.grid_columnconfigure(1, weight=2, uniform="charts")
        charts.grid_rowconfigure(0, weight=3)
        charts.grid_rowconfigure(1, weight=2)

        revenue_card = ModernCard(charts, width=650, height=330, shadow=True)
        revenue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._card_heading(revenue_card.body, "Revenue performance", "Monthly income this year")
        months, revenue = self._monthly_revenue()
        self.revenue_chart = LineChart(
            revenue_card.body,
            self.font_family,
            height=230,
            labels=months,
            series={"Income": revenue},
            colors=(PRIMARY,),
        )
        self.revenue_chart.pack(fill="both", expand=True, pady=(42, 0))

        status_card = ModernCard(charts, width=390, height=330, shadow=True)
        status_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        self._card_heading(status_card.body, "Project status", "Portfolio distribution")
        status_labels, status_values = self._project_status()
        self.status_chart = DonutChart(
            status_card.body,
            self.font_family,
            height=220,
            labels=status_labels,
            values=status_values,
            colors=(PRIMARY, SECONDARY, SUCCESS, PURPLE),
            center_text="Projects",
        )
        self.status_chart.pack(fill="both", expand=True, pady=(38, 0))

        recent_card = ModernCard(charts, width=650, height=200, shadow=True)
        recent_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self._card_heading(
            recent_card.body, "Recent projects", "Latest additions to your portfolio"
        )
        self._recent_projects(recent_card.body)

        insight_card = ModernCard(charts, width=390, height=200, shadow=True)
        insight_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        self._card_heading(insight_card.body, "Workspace health", "A quick operational snapshot")
        self._health_summary(insight_card.body, stats)

    def _card_heading(self, parent, title, subtitle):
        tk.Label(
            parent,
            text=title,
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 11, "bold"),
            anchor="w",
        ).place(x=0, y=0)
        tk.Label(
            parent,
            text=subtitle,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
            anchor="w",
        ).place(x=0, y=23)

    def _monthly_revenue(self):
        rows = self.repository.db.fetch_all(
            "SELECT strftime('%m', tx_date) AS month, SUM(amount) AS total "
            "FROM transactions WHERE type = ? AND strftime('%Y', tx_date) = strftime('%Y', 'now') "
            "GROUP BY month ORDER BY month",
            ("income",),
        )
        monthly = {int(row["month"]): float(row["total"] or 0) for row in rows if row["month"]}
        labels = (
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        )
        return labels, [monthly.get(index, 0.0) for index in range(1, 13)]

    def _project_status(self):
        rows = self.repository.db.fetch_all(
            "SELECT status, COUNT(*) AS total FROM projects GROUP BY status ORDER BY status"
        )
        labels = [str(row["status"] or "Unspecified").replace("_", " ").title() for row in rows]
        values = [int(row["total"]) for row in rows]
        if not values:
            return (), ()
        return tuple(labels), tuple(values)

    def _recent_projects(self, parent):
        rows = self.repository.db.fetch_all(
            "SELECT title, status, end_date FROM projects ORDER BY id DESC LIMIT ?", (3,)
        )
        if not rows:
            tk.Label(
                parent,
                text="No projects yet. Add a project to see it here.",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 9),
            ).place(x=0, y=58, anchor="nw")
            return
        for index, row in enumerate(rows):
            y = 55 + index * 36
            tk.Frame(parent, bg=BORDER, height=1).place(x=0, y=y + 30, relwidth=1)
            tk.Label(
                parent,
                text=str(row["title"]),
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                font=(self.font_family, 9, "bold"),
                anchor="w",
            ).place(x=0, y=y, relwidth=0.62)
            status = str(row["status"] or "pending").replace("_", " ").title()
            tk.Label(
                parent,
                text=status,
                bg=BG_CARD,
                fg=PRIMARY if status.lower() == "active" else SECONDARY,
                font=(self.font_family, 8),
                anchor="w",
            ).place(relx=0.65, y=y, relwidth=0.2)
            tk.Label(
                parent,
                text=str(row["end_date"] or "No due date"),
                bg=BG_CARD,
                fg=TEXT_MUTED,
                font=(self.font_family, 8),
                anchor="e",
            ).place(relx=0.82, y=y, relwidth=0.18)

    def _health_summary(self, parent, stats):
        items = (
            ("Active projects", str(stats["projects"]), PRIMARY),
            ("Customer records", str(stats["customers"]), SECONDARY),
            ("Team accounts", str(stats["users"]), SUCCESS),
        )
        for index, (label, value, color) in enumerate(items):
            y = 56 + index * 37
            tk.Label(parent, text="●", bg=BG_CARD, fg=color, font=(self.font_family, 10)).place(
                x=0, y=y
            )
            tk.Label(
                parent,
                text=label,
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 8),
                anchor="w",
            ).place(x=20, y=y + 1)
            tk.Label(
                parent,
                text=value,
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                font=(self.font_family, 9, "bold"),
                anchor="e",
            ).place(relx=0.82, y=y, relwidth=0.16)
