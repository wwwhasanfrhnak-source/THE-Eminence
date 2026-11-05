# ui/views/dashboard_view.py
"""Three-row management dashboard with KPI, finance and schedule cards."""

import tkinter as tk
from datetime import date

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config.theme import (
    BG_CARD,
    BG_MAIN,
    BORDER,
    PRIMARY,
    PURPLE,
    SECONDARY,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from core.repository import Repository
from ui.components.kpi_card import KPICard
from ui.components.modern_card import ModernCard
from utils.formatters import format_currency


class DashboardView(tk.Frame):
    def __init__(self, master, font_family, repository=None):
        super().__init__(master, bg=BG_MAIN)
        self.font_family = font_family
        self.repository = repository or Repository()
        self._photos = []
        self._build()

    def _title(self, parent, text, x=0, y=0, size=12):
        return tk.Label(
            parent, text=text, bg=BG_CARD, fg=TEXT_PRIMARY, font=(self.font_family, size, "bold")
        ).place(x=x, y=y)

    def _build(self):
        width = 1100
        tk.Label(
            self,
            text="Good morning, welcome back 👋",
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 21, "bold"),
        ).place(x=0, y=0)
        tk.Label(
            self,
            text=f"Here is your business overview · {date.today():%A, %B %d, %Y}",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 9),
        ).place(x=2, y=39)
        stats = self.repository.dashboard_stats()
        kpis = (
            (
                "Total Customers",
                f"{stats['customers']:,}",
                "+12.8% this month",
                PRIMARY,
                [2, 4, 3, 5, 4, 7, 8],
            ),
            (
                "Active Projects",
                f"{stats['projects']:,}",
                "+8.2% this month",
                SECONDARY,
                [3, 2, 4, 4, 6, 5, 7],
            ),
            (
                "Total Revenue",
                format_currency(float(stats["revenue"])),
                "+14.3% this month",
                SUCCESS,
                [2, 3, 3, 5, 6, 5, 8],
            ),
            (
                "Team Members",
                f"{stats['users']:,}",
                "Across your workspace",
                PURPLE,
                [3, 3, 4, 3, 5, 5, 6],
            ),
        )
        self.kpi_cards = []
        for index, (title, value, change, color, series) in enumerate(kpis):
            card = KPICard(self, title, value, change, color, series, self.font_family)
            card.place(x=index * 270, y=70)
            self.kpi_cards.append(card)

        chart_width = 560
        side_width = width - chart_width - 70
        chart = ModernCard(self, chart_width, 306, shadow=True)
        chart.place(x=0, y=220)
        self._title(chart.body, "Booking vs Revenue", y=0)
        tk.Label(
            chart.body,
            text="Monthly performance",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
        ).place(x=0, y=24)
        self._line_chart(chart.body, chart_width - 32, 180)

        donut = ModernCard(self, side_width, 306, shadow=True)
        donut.place(x=chart_width + 20, y=220)
        self._title(donut.body, "Device by User", y=0)
        tk.Label(
            donut.body,
            text="Active users by device",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
        ).place(x=0, y=24)
        self._donut_chart(donut.body, side_width - 40, 165)

        meeting = ModernCard(self, chart_width, 195, shadow=True)
        meeting.place(x=0, y=490)
        self._title(meeting.body, "Next Meeting", y=0)
        tk.Label(
            meeting.body,
            text="Today's schedule",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
        ).place(x=0, y=23)
        self._meeting_slot(
            meeting.body, "10:30 AM", "Project kickoff · Skyline Tower", "👩🏻‍💼", PRIMARY, 55
        )
        self._meeting_slot(
            meeting.body, "02:00 PM", "Electrical review · North District", "👨🏽‍💼", SECONDARY, 112
        )

        events = ModernCard(self, side_width, 195, shadow=True)
        events.place(x=chart_width + 20, y=490)
        self._title(events.body, "Your Upcoming Event", y=0)
        tk.Label(
            events.body,
            text="Mark your calendar",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
        ).place(x=0, y=23)
        self._event_item(
            events.body, "Electrical Safety Inspection", "NOV 08 · 09:00 AM", PRIMARY, 49
        )
        self._event_item(
            events.body, "Project Milestone Review", "NOV 12 · 02:30 PM", SECONDARY, 96
        )
        self._event_item(events.body, "Monthly Team Sync", "NOV 18 · 10:00 AM", PURPLE, 143)

    def _line_chart(self, parent, width, height):
        figure = Figure(figsize=(max(4.0, width / 100), 2.15), dpi=90, facecolor=BG_CARD)
        axis = figure.add_subplot(111)
        axis.set_facecolor(BG_CARD)
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug")
        booking = [18, 25, 22, 32, 29, 41, 37, 49]
        revenue = [14, 18, 27, 24, 35, 32, 45, 54]
        axis.plot(months, booking, color=PRIMARY, linewidth=2.2, marker="o", markersize=3)
        axis.plot(months, revenue, color=SECONDARY, linewidth=2.2, marker="o", markersize=3)
        axis.fill_between(range(len(months)), booking, color=PRIMARY, alpha=0.07)
        axis.fill_between(range(len(months)), revenue, color=SECONDARY, alpha=0.07)
        axis.grid(axis="y", color=BORDER, linewidth=0.7)
        axis.tick_params(colors=TEXT_MUTED, labelsize=8, length=0)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.set_ylim(0, 65)
        figure.tight_layout(pad=1)
        chart = FigureCanvasTkAgg(figure, master=parent)
        chart.get_tk_widget().place(x=0, y=49, width=width, height=height)
        self._photos.append(chart)

    def _donut_chart(self, parent, width, height):
        figure = Figure(figsize=(2.0, 1.8), dpi=90, facecolor=BG_CARD)
        axis = figure.add_subplot(111)
        axis.set_facecolor(BG_CARD)
        axis.pie(
            [38, 27, 20, 15],
            startangle=90,
            counterclock=False,
            colors=(PRIMARY, SECONDARY, PURPLE, SUCCESS),
            wedgeprops={"width": 0.28, "edgecolor": BG_CARD, "linewidth": 2},
        )
        axis.text(
            0,
            0,
            "Users",
            color=TEXT_PRIMARY,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
        axis.set_axis_off()
        figure.tight_layout(pad=0)
        chart = FigureCanvasTkAgg(figure, master=parent)
        chart.get_tk_widget().place(x=0, y=48, width=min(width, 210), height=height)
        self._photos.append(chart)
        legend = tk.Frame(parent, bg=BG_CARD)
        legend.place(x=min(width, 216), y=68)
        for label, count, color in (
            ("Desktop", "38%", PRIMARY),
            ("Mobile", "27%", SECONDARY),
            ("Tablet", "20%", PURPLE),
            ("Other", "15%", SUCCESS),
        ):
            row = tk.Frame(legend, bg=BG_CARD)
            row.pack(anchor="w", pady=6)
            tk.Label(row, text="●", bg=BG_CARD, fg=color, font=(self.font_family, 10)).pack(
                side="left"
            )
            tk.Label(
                row, text=f"  {label}", bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 8)
            ).pack(side="left")
            tk.Label(
                row, text=count, bg=BG_CARD, fg=TEXT_PRIMARY, font=(self.font_family, 8, "bold")
            ).pack(side="left", padx=(8, 0))

    def _meeting_slot(self, parent, time, title, avatar, color, y):
        tk.Label(parent, text=avatar, bg=BG_CARD, fg=color, font=(self.font_family, 17)).place(
            x=2, y=y
        )
        tk.Label(parent, text=time, bg=BG_CARD, fg=color, font=(self.font_family, 9, "bold")).place(
            x=50, y=y + 1
        )
        tk.Label(parent, text=title, bg=BG_CARD, fg=TEXT_PRIMARY, font=(self.font_family, 9)).place(
            x=138, y=y + 1
        )

    def _event_item(self, parent, title, when, color, y):
        tk.Label(parent, text="●", bg=BG_CARD, fg=color, font=(self.font_family, 12)).place(
            x=2, y=y
        )
        tk.Label(
            parent, text=title, bg=BG_CARD, fg=TEXT_PRIMARY, font=(self.font_family, 9, "bold")
        ).place(x=24, y=y)
        tk.Label(parent, text=when, bg=BG_CARD, fg=TEXT_MUTED, font=(self.font_family, 8)).place(
            x=24, y=y + 22
        )
