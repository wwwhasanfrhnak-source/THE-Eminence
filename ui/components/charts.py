"""Dark-themed, reusable matplotlib charts embedded in Tk."""

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui.theme import (
    BG_SURFACE,
    BORDER,
    PRIMARY,
    PURPLE,
    SECONDARY,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

_DEFAULT_COLORS = (PRIMARY, SECONDARY, SUCCESS, PURPLE)


class ChartContainer(tk.Frame):
    """Responsive chart surface supporting line, bar, and donut visualizations."""

    def __init__(
        self,
        master,
        font_family: str,
        *,
        kind: str = "line",
        height: int = 220,
        labels=None,
        values=None,
        series=None,
        colors=None,
        center_text: str = "",
    ):
        super().__init__(master, bg=BG_SURFACE, height=height, highlightthickness=0)
        if kind not in {"line", "bar", "donut"}:
            raise ValueError(f"Unsupported chart kind: {kind}")
        self.pack_propagate(False)
        self.kind = kind
        self.font_family = font_family
        self.labels = tuple(labels or ())
        self.values = tuple(values or ())
        self.series = series or {}
        self.colors = tuple(colors or _DEFAULT_COLORS)
        self.center_text = center_text
        self.figure = Figure(figsize=(5.4, max(1.6, height / 100)), dpi=90, facecolor=BG_SURFACE)
        self.axis = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg=BG_SURFACE, highlightthickness=0)
        self.canvas_widget.pack(fill="both", expand=True)
        self.loading = tk.Label(
            self,
            text="Loading chart…",
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
        )
        self.loading.place(relwidth=1, relheight=1)
        self.after(30, self._render)

    def set_data(self, *, labels=None, values=None, series=None):
        if labels is not None:
            self.labels = tuple(labels)
        if values is not None:
            self.values = tuple(values)
        if series is not None:
            self.series = series
        self.loading.place(relwidth=1, relheight=1)
        self.after_idle(self._render)

    def _render(self):
        self.axis.clear()
        self.axis.set_facecolor(BG_SURFACE)
        if self.kind == "line":
            self._draw_line()
        elif self.kind == "bar":
            self._draw_bar()
        else:
            self._draw_donut()
        self.figure.tight_layout(pad=1.2)
        self.canvas.draw_idle()
        self.loading.place_forget()

    def _draw_line(self):
        if not self.series and self.values:
            self.series = {"Series": self.values}
        if not self.series:
            self._draw_empty()
            return
        count = max(len(points) for points in self.series.values())
        labels = self.labels or tuple(str(index + 1) for index in range(count))
        for index, (name, points) in enumerate(self.series.items()):
            points = tuple(points)
            color = self.colors[index % len(self.colors)]
            self.axis.plot(
                range(len(points)),
                points,
                label=name,
                color=color,
                linewidth=2.2,
                marker="o",
                markersize=3,
            )
            self.axis.fill_between(range(len(points)), points, color=color, alpha=0.07)
        tick_labels = labels[:count]
        self.axis.set_xticks(range(len(tick_labels)), tick_labels)
        self.axis.grid(axis="y", color=BORDER, linewidth=0.7)
        self.axis.tick_params(colors=TEXT_MUTED, labelsize=8, length=0)
        if len(self.series) > 1:
            legend = self.axis.legend(
                frameon=False, labelcolor=TEXT_SECONDARY, fontsize=8, loc="upper left"
            )
            for text in legend.get_texts():
                text.set_fontfamily(self.font_family)
        self._hide_spines()

    def _draw_bar(self):
        if not self.values:
            self._draw_empty()
            return
        labels = self.labels or tuple(str(index + 1) for index in range(len(self.values)))
        self.axis.bar(
            range(len(self.values)),
            self.values,
            color=[self.colors[index % len(self.colors)] for index in range(len(self.values))],
            width=0.64,
        )
        tick_labels = labels[: len(self.values)]
        self.axis.set_xticks(range(len(tick_labels)), tick_labels)
        self.axis.grid(axis="y", color=BORDER, linewidth=0.7)
        self.axis.tick_params(colors=TEXT_MUTED, labelsize=8, length=0)
        self._hide_spines()

    def _draw_donut(self):
        if not self.values:
            self._draw_empty()
            return
        labels = self.labels or tuple(f"Item {i + 1}" for i in range(len(self.values)))
        self.axis.pie(
            self.values,
            startangle=90,
            counterclock=False,
            colors=[self.colors[index % len(self.colors)] for index in range(len(self.values))],
            wedgeprops={"width": 0.3, "edgecolor": BG_SURFACE, "linewidth": 2},
        )
        if self.center_text:
            self.axis.text(
                0,
                0,
                self.center_text,
                color=TEXT_PRIMARY,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                fontfamily=self.font_family,
            )
        self.axis.legend(
            labels,
            frameon=False,
            labelcolor=TEXT_SECONDARY,
            fontsize=8,
            loc="center left",
            bbox_to_anchor=(1, 0.5),
        )
        self.axis.set_aspect("equal")

    def _draw_empty(self):
        self.axis.text(
            0.5,
            0.5,
            "No data available",
            color=TEXT_MUTED,
            ha="center",
            va="center",
            transform=self.axis.transAxes,
            fontsize=9,
            fontfamily=self.font_family,
        )
        self.axis.set_axis_off()

    def _hide_spines(self):
        for spine in self.axis.spines.values():
            spine.set_visible(False)


class LineChart(ChartContainer):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, font_family, kind="line", **kwargs)


class BarChart(ChartContainer):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, font_family, kind="bar", **kwargs)


class DonutChart(ChartContainer):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, font_family, kind="donut", **kwargs)
