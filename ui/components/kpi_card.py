"""Premium KPI card with compact, dark-themed sparkline."""

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui.components.modern_card import ModernCard
from ui.theme import BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY


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
        super().__init__(master, width=230, height=132, radius=16, shadow=True)
        body = self.body
        tk.Label(
            body,
            text=title,
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
            anchor="w",
        ).place(x=0, y=2, relwidth=0.96)
        tk.Label(
            body,
            text=value,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=(font_family, 21, "bold"),
            anchor="w",
        ).place(x=0, y=29, relwidth=0.98)
        tk.Label(
            body,
            text=change,
            bg=BG_SURFACE,
            fg=color,
            font=(font_family, 8, "bold"),
            anchor="w",
        ).place(x=0, y=72, relwidth=1)

        figure = Figure(figsize=(1.35, 0.62), dpi=90, facecolor=BG_SURFACE)
        axis = figure.add_subplot(111)
        axis.set_facecolor(BG_SURFACE)
        points = list(data)
        if points:
            low, high = min(points), max(points)
            span = max(high - low, abs(high) * 0.08, 1)
            axis.plot(points, color=color, linewidth=1.8)
            axis.fill_between(
                range(len(points)), points, low - span * 0.12, color=color, alpha=0.14
            )
            axis.set_ylim(low - span * 0.15, high + span * 0.15)
        axis.set_axis_off()
        figure.subplots_adjust(0, 0, 1, 1)
        self._chart = FigureCanvasTkAgg(figure, master=body)
        self._chart.get_tk_widget().configure(bg=BG_SURFACE, highlightthickness=0)
        self._chart.get_tk_widget().place(relx=1.0, y=27, anchor="ne", width=98, height=54)
