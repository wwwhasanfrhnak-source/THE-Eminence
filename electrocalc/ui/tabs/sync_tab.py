"""Secure local-network synchronization interface."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from electrocalc.core.lan_sync import LanSyncService
from electrocalc.ui.design_system import TOKENS
from electrocalc.ui.scrollable_frame import ScrollableFrame

try:
    from electrocalc.ui.components.modern_card import ModernCard
except ImportError:
    ModernCard = None


class _Card(tk.Frame):
    """Dark themed section surface, used if ModernCard is unavailable."""

    def __init__(self, parent, palette):
        super().__init__(
            parent,
            bg=palette["card"],
            highlightbackground=palette["border"],
            highlightthickness=1,
        )


class SyncTab(tk.Frame):
    """Discover, pair with, and synchronize another app instance on the LAN."""

    PALETTE = {
        "bg": "#0B1220",
        "card": "#142137",
        "text": "#EAF1FC",
        "muted": "#93A4BE",
        "border": "#243550",
        "accent": "#4E8BFF",
        "success": "#46C79A",
        "danger": "#F06B78",
        "entry": "#0B1220",
    }

    def __init__(self, parent, app):
        super().__init__(parent, bg=self.PALETTE["bg"])
        self.app = app
        self.palette = self.PALETTE
        self._events = queue.Queue()
        self._destroyed = False
        self._busy = False
        self._peers = {}
        self._paired_peer = None
        self._pair_token = None
        self._selected_peer_id = None
        self._poll_job = None
        self._service = LanSyncService()

        self._build_ui()
        self._poll_job = self.after(100, self._poll_events)
        self._start_service()

    def _build_ui(self):
        p = self.palette
        self.scroll = ScrollableFrame(self, padding=22, bg=p["bg"])
        self.scroll.pack(fill="both", expand=True)
        body = self.scroll.inner

        header = tk.Frame(body, bg=p["bg"])
        header.pack(fill="x", pady=(0, 15))
        tk.Label(
            header, text="⇄", bg=p["bg"], fg=p["accent"],
            font=("Segoe UI Symbol", 22, "bold"),
        ).pack(side="right", padx=(0, 10))
        tk.Label(
            header, text="همگام‌سازی شبکه محلی", bg=p["bg"], fg=p["text"],
            font=(TOKENS["font_family"], TOKENS["font_title"], "bold"),
            anchor="e",
        ).pack(side="right")

        local_body = self._make_card(body, "اطلاعات این دستگاه", "◉")
        self.device_label = tk.Label(
            local_body, text="شناسه دستگاه: در حال آماده‌سازی...",
            bg=p["card"], fg=p["muted"], font=(TOKENS["font_family"], 9),
            anchor="e",
        )
        self.device_label.pack(fill="x", pady=(0, 5))
        local_row = tk.Frame(local_body, bg=p["card"])
        local_row.pack(fill="x")
        self.ip_label = tk.Label(
            local_row, text="IP محلی: —", bg=p["card"], fg=p["text"],
            font=(TOKENS["font_family"], 10), anchor="e",
        )
        self.ip_label.pack(side="right", fill="x", expand=True)
        tk.Label(
            local_row, text="PIN:", bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9, "bold"),
        ).pack(side="right", padx=(14, 5))
        self.pin_label = tk.Label(
            local_row, text="------", bg=p["card"], fg=p["accent"],
            font=(TOKENS["font_mono"], 15, "bold"),
        )
        self.pin_label.pack(side="right", padx=(0, 12))
        self.new_pin_button = self._button(
            local_row, "تولید PIN جدید", self._generate_pin, p["border"],
        )
        self.new_pin_button.pack(side="left")

        discovery_body = self._make_card(body, "دستگاه‌های شبکه", "⌕")
        discovery_top = tk.Frame(discovery_body, bg=p["card"])
        discovery_top.pack(fill="x", pady=(0, 8))
        self.scan_button = self._button(
            discovery_top, "اسکن شبکه", self._scan_network, p["accent"],
        )
        self.scan_button.pack(side="right")
        tk.Label(
            discovery_top, text="IP  ·  نام دستگاه  ·  شناسه",
            bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e",
        ).pack(side="left", padx=8)

        style = ttk.Style(self)
        style.configure(
            "LanSync.Treeview",
            background=p["bg"], foreground=p["text"],
            fieldbackground=p["bg"], rowheight=30,
            bordercolor=p["border"], font=(TOKENS["font_family"], 9),
        )
        style.configure(
            "LanSync.Treeview.Heading",
            background=p["card"], foreground=p["muted"],
            font=(TOKENS["font_family"], 9, "bold"),
        )
        style.map(
            "LanSync.Treeview",
            background=[("selected", p["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )
        tree_frame = tk.Frame(discovery_body, bg=p["border"], padx=1, pady=1)
        tree_frame.pack(fill="x")
        self.peer_tree = ttk.Treeview(
            tree_frame,
            columns=("ip", "hostname", "device_id"),
            show="headings",
            height=5,
            selectmode="browse",
            style="LanSync.Treeview",
        )
        self.peer_tree.heading("ip", text="IP")
        self.peer_tree.heading("hostname", text="نام دستگاه")
        self.peer_tree.heading("device_id", text="شناسه دستگاه")
        self.peer_tree.column("ip", width=140, anchor="center")
        self.peer_tree.column("hostname", width=190, anchor="center")
        self.peer_tree.column("device_id", width=260, anchor="center")
        tree_scroll = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.peer_tree.yview,
        )
        self.peer_tree.configure(yscrollcommand=tree_scroll.set)
        self.peer_tree.pack(side="right", fill="x", expand=True)
        tree_scroll.pack(side="left", fill="y")
        self.peer_tree.bind("<<TreeviewSelect>>", self._select_peer)

        connection_body = self._make_card(body, "اتصال امن", "◇")
        connect_row = tk.Frame(connection_body, bg=p["card"])
        connect_row.pack(fill="x")
        self.connect_button = self._button(
            connect_row, "اتصال", self._connect_peer, p["accent"],
        )
        self.connect_button.pack(side="right")
        tk.Label(
            connect_row, text="PIN دستگاه انتخاب‌شده:",
            bg=p["card"], fg=p["text"],
            font=(TOKENS["font_family"], 9),
        ).pack(side="right", padx=(0, 10))
        self.peer_pin_var = tk.StringVar()
        self.peer_pin_entry = tk.Entry(
            connect_row, textvariable=self.peer_pin_var, width=12,
            justify="center", show="•", bg=p["entry"], fg=p["text"],
            insertbackground=p["text"], relief="flat",
            highlightthickness=1, highlightbackground=p["border"],
            highlightcolor=p["accent"], font=(TOKENS["font_mono"], 12),
        )
        self.peer_pin_entry.pack(side="right", padx=6, ipady=5)
        self.connection_status = tk.Label(
            connection_body, text="دستگاهی انتخاب نشده است",
            bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e",
        )
        self.connection_status.pack(fill="x", pady=(8, 0))

        sync_body = self._make_card(body, "تبادل اطلاعات", "⇅")
        sync_row = tk.Frame(sync_body, bg=p["card"])
        sync_row.pack(fill="x", pady=(0, 9))
        self.sync_button = self._button(
            sync_row, "تبادل اطلاعات", self._sync_peer, p["success"],
            state="disabled",
        )
        self.sync_button.pack(side="right")
        tk.Label(
            sync_row, text="جداول پروژه‌ها، گزارش‌ها و ساعات کار همگام می‌شوند.",
            bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e",
        ).pack(side="right", padx=10)

        log_frame = tk.Frame(
            sync_body, bg=p["border"], highlightthickness=1,
            highlightbackground=p["border"],
        )
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame, height=8, wrap="word", state="disabled",
            bg=p["bg"], fg=p["text"], insertbackground=p["text"],
            selectbackground=p["accent"], relief="flat", padx=10, pady=8,
            font=(TOKENS["font_mono"], 9),
        )
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview,
        )
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="right", fill="both", expand=True)
        log_scroll.pack(side="left", fill="y")

    def _make_card(self, parent, title, icon):
        p = self.palette
        card_type = ModernCard if isinstance(ModernCard, type) else _Card
        try:
            card = card_type(parent, bg=p["card"], border_color=p["border"])
        except TypeError:
            card = _Card(parent, p)
        card.pack(fill="x", pady=(0, 12))
        content = tk.Frame(card, bg=p["card"], padx=15, pady=13)
        content.pack(fill="both", expand=True)
        title_row = tk.Frame(content, bg=p["card"])
        title_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            title_row, text=title, bg=p["card"], fg=p["text"],
            font=(TOKENS["font_family"], TOKENS["font_section"], "bold"),
            anchor="e",
        ).pack(side="right")
        tk.Label(
            title_row, text=icon, bg=p["card"], fg=p["accent"],
            font=("Segoe UI Symbol", 13, "bold"),
        ).pack(side="right", padx=(0, 7))
        return content

    def _button(self, parent, text, command, color, state="normal"):
        p = self.palette
        return tk.Button(
            parent, text=text, command=command,
            bg=color, fg="#FFFFFF", activebackground=color,
            activeforeground="#FFFFFF", disabledforeground=p["muted"],
            relief="flat", cursor="hand2", padx=14, pady=7,
            font=(TOKENS["font_family"], 9, "bold"), state=state,
        )

    def _start_service(self):
        self._run_worker("service", self._service.start)

    def _generate_pin(self):
        self._run_worker("pin", self._service.rotate_pin)

    def _scan_network(self):
        self.scan_button.config(state="disabled", text="در حال اسکن...")
        self._log("در حال اسکن شبکه...")
        self._run_worker("scan", self._service.discover_peers)

    def _select_peer(self, _event=None):
        selection = self.peer_tree.selection()
        if not selection:
            return
        self._selected_peer_id = selection[0]
        peer = self._peers.get(self._selected_peer_id)
        if peer:
            self.connection_status.config(
                text=f"انتخاب‌شده: {peer['hostname']}  ({peer['ip']})",
                fg=self.palette["text"],
            )

    def _connect_peer(self):
        peer = self._peers.get(self._selected_peer_id)
        pin = self.peer_pin_var.get().strip()
        if peer is None:
            messagebox.showwarning(
                "انتخاب دستگاه", "ابتدا یک دستگاه را انتخاب کنید.", parent=self,
            )
            return
        if len(pin) != 6 or not pin.isdigit():
            messagebox.showwarning(
                "PIN نامعتبر", "PIN باید یک کد ۶ رقمی باشد.", parent=self,
            )
            return
        self._paired_peer = None
        self._pair_token = None
        self.sync_button.config(state="disabled")
        self.connect_button.config(state="disabled", text="در حال اتصال...")
        self._log(f"در حال اتصال امن به {peer['ip']}...")
        self._run_worker(
            "connect",
            lambda: self._service.pair_with_peer(peer, pin),
            peer,
        )

    def _sync_peer(self):
        if not self._paired_peer or not self._pair_token or self._busy:
            return
        self._busy = True
        self.sync_button.config(state="disabled", text="در حال تبادل...")
        self._log("در حال تبادل اطلاعات...")
        role = "engineer"
        try:
            if self.app.current_user:
                role = self.app.current_user.get("role", role)
        except (AttributeError, TypeError):
            pass
        self._run_worker(
            "sync",
            lambda: self._service.sync_with_peer(
                self._paired_peer, self._pair_token, role=role,
            ),
        )

    def _run_worker(self, event_name, function, *result_args):
        def worker():
            try:
                result = function()
                self._events.put((event_name, True, result, result_args))
            except Exception as exc:
                self._events.put((event_name, False, str(exc), result_args))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_events(self):
        if self._destroyed:
            return
        try:
            while True:
                name, ok, result, args = self._events.get_nowait()
                if name == "service":
                    if ok:
                        self._show_local_info(result)
                        self._log("سرویس همگام‌سازی آماده است.")
                    else:
                        self._log(f"راه‌اندازی سرویس ناموفق بود: {result}")
                        messagebox.showerror(
                            "خطای سرویس",
                            f"راه‌اندازی سرویس LAN ممکن نشد:\n{result}",
                            parent=self,
                        )
                elif name == "pin":
                    if ok:
                        self._show_local_info(result)
                        self._log("PIN جدید تولید شد. برای اتصال، آن را در اختیار دستگاه مقابل بگذارید.")
                    else:
                        self._show_error("تولید PIN", result)
                elif name == "scan":
                    self.scan_button.config(state="normal", text="اسکن شبکه")
                    if ok:
                        self._display_peers(result)
                    else:
                        self._log(f"اسکن شبکه ناموفق بود: {result}")
                        self._show_error("خطای اسکن", result)
                elif name == "connect":
                    self.connect_button.config(state="normal", text="اتصال")
                    peer = args[0]
                    if ok:
                        self._paired_peer = peer
                        self._pair_token = result["token"]
                        self.sync_button.config(state="normal")
                        self.connection_status.config(
                            text=f"اتصال امن برقرار شد: {peer['hostname']} ({peer['ip']})",
                            fg=self.palette["success"],
                        )
                        self.peer_pin_var.set("")
                        self._log(f"اتصال امن با {peer['ip']} برقرار شد.")
                    else:
                        self._paired_peer = None
                        self._pair_token = None
                        self.sync_button.config(state="disabled")
                        self._log(f"اتصال برقرار نشد: {result}")
                        messagebox.showerror("اتصال ناموفق", result, parent=self)
                elif name == "sync":
                    self._busy = False
                    self.sync_button.config(state="normal", text="تبادل اطلاعات")
                    if ok:
                        self._log(
                            f"تبادل اطلاعات کامل شد. دریافت: {result['received']}، "
                            f"ارسال: {result['sent']} رکورد."
                        )
                    else:
                        self._log(f"تبادل اطلاعات ناموفق بود: {result}")
                        messagebox.showerror("خطای همگام‌سازی", result, parent=self)
        except queue.Empty:
            pass
        self._poll_job = self.after(100, self._poll_events)

    def _show_local_info(self, info):
        self.device_label.config(text=f"شناسه دستگاه: {info['device_id']}")
        self.ip_label.config(text=f"IP محلی: {info['ip']}  ·  درگاه: {info['port']}")
        self.pin_label.config(text=info["pin"])

    def _display_peers(self, peers):
        self._peers = {peer["device_id"]: peer for peer in peers}
        self._selected_peer_id = None
        for item in self.peer_tree.get_children():
            self.peer_tree.delete(item)
        for peer in peers:
            self.peer_tree.insert(
                "", "end", iid=peer["device_id"],
                values=(peer["ip"], peer["hostname"], peer["device_id"]),
            )
        if peers:
            self._log(f"دستگاه پیدا شد: {len(peers)} دستگاه در شبکه موجود است.")
        else:
            self._log("دستگاهی پیدا نشد. بررسی کنید هر دو دستگاه به یک شبکه متصل باشند.")

    def _show_error(self, title, detail):
        messagebox.showerror(title, detail, parent=self)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def destroy(self):
        self._destroyed = True
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except tk.TclError:
                pass
        try:
            self._service.stop()
        except Exception:
            pass
        super().destroy()
