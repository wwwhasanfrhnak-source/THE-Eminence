# ui/components/kpi_card.py
"""Compact KPI card with a dark matplotlib sparkline."""

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config.theme import BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY
from ui.components.modern_card import ModernCard


class KPICard(ModernCard):
    def __init__(
        self,
        master,
        title: str,
        value: str,
        change: str,
        color: str,
        data: list[float],
        font_family: str,
    ):
        super().__init__(master, width=230, height=125, radius=16, shadow=True)
        body = self.body
        tk.Label(body, text=title, bg=BG_CARD, fg=TEXT_SECONDARY, font=(font_family, 9)).place(
            x=0, y=1
        )
        tk.Label(
            body, text=value, bg=BG_CARD, fg=TEXT_PRIMARY, font=(font_family, 22, "bold")
        ).place(x=0, y=27)
        tk.Label(body, text=change, bg=BG_CARD, fg=color, font=(font_family, 8, "bold")).place(
            x=0, y=64
        )
        figure = Figure(figsize=(1.34, 0.62), dpi=80, facecolor=BG_CARD)
        axis = figure.add_subplot(111)
        axis.set_facecolor(BG_CARD)
        axis.plot(data, color=color, linewidth=1.8)
        axis.fill_between(range(len(data)), data, min(data), color=color, alpha=0.16)
        axis.set_axis_off()
        figure.subplots_adjust(0, 0, 1, 1)
        self._chart = FigureCanvasTkAgg(figure, master=body)
        self._chart.get_tk_widget().place(relx=1.0, y=22, anchor="ne", width=104, height=52)
