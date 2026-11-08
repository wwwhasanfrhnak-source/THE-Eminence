"""GitHub synchronization tab."""

import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, cast

from electrocalc.ui.components import modern_card
from electrocalc.ui.design_system import TOKENS, premium_palette
from electrocalc.ui.scrollable_frame import ScrollableFrame

class _FallbackModernCard(tk.Frame):
    """Theme-aware card fallback while the shared component is unavailable."""

    def __init__(self, parent, bg, border_color, **kwargs):
        super().__init__(
            parent,
            bg=bg,
            highlightbackground=border_color,
            highlightthickness=1,
            **kwargs,
        )


ModernCard = getattr(modern_card, "ModernCard", _FallbackModernCard)


class SyncTab(tk.Frame):
    """Pull and push the application's Git repository."""

    def __init__(self, parent, app):
        palette = cast(
            dict[str, Any],
            getattr(app, "palette", None) or premium_palette("dark"),
        )
        super().__init__(parent, bg=palette["bg"])
        self.app = app
        self.palette: dict[str, Any] = palette
        self._repo_root = None
        self._busy = False
        self._destroyed = False
        self._events = queue.Queue()
        self._poll_job = None
        self._auto_job = None

        self._build_ui()
        self._poll_job = self.after(100, self._poll_events)
        self._refresh_status()

    def _build_ui(self):
        p: dict[str, Any] = self.palette
        self.content = ScrollableFrame(self, padding=22, bg=p["bg"])
        self.content.pack(fill="both", expand=True)
        body = self.content.inner

        header = tk.Frame(body, bg=p["bg"])
        header.pack(fill="x", pady=(0, 16))
        tk.Label(
            header,
            text="⇄",
            bg=p["bg"],
            fg=p["accent"],
            font=("Segoe UI Symbol", 22, "bold"),
        ).pack(side="right", padx=(0, 10))
        tk.Label(
            header,
            text="همگام‌سازی با گیت‌هاب",
            bg=p["bg"],
            fg=p["text"],
            font=(TOKENS["font_family"], TOKENS["font_title"], "bold"),
            anchor="e",
        ).pack(side="right")

        _, status_body = self._make_card(body, "وضعیت اتصال", "●")
        status_row = tk.Frame(status_body, bg=p["card"])
        status_row.pack(fill="x")
        self.status_dot = tk.Label(
            status_row, text="●", bg=p["card"], fg=p["muted"],
            font=("Segoe UI", 14),
        )
        self.status_dot.pack(side="right", padx=(0, 8))
        self.status_label = tk.Label(
            status_row, text="در حال بررسی مخزن...", bg=p["card"],
            fg=p["muted"], font=(TOKENS["font_family"], 10), anchor="e",
        )
        self.status_label.pack(side="right")
        self.branch_label = tk.Label(
            status_body, text="شاخه: —", bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e",
        )
        self.branch_label.pack(fill="x", pady=(7, 0))
        self.remote_label = tk.Label(
            status_body, text="مخزن: —", bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e", justify="right",
            wraplength=900,
        )
        self.remote_label.pack(fill="x", pady=(3, 0))

        _, actions_body = self._make_card(body, "عملیات همگام‌سازی", "⇅")
        button_row = tk.Frame(actions_body, bg=p["card"])
        button_row.pack(fill="x", pady=(0, 10))
        self.pull_button = tk.Button(
            button_row,
            text="دریافت از گیت‌هاب",
            command=self._pull,
            bg=p["accent"], fg="#FFFFFF",
            activebackground=p["accent"], activeforeground="#FFFFFF",
            relief="flat", cursor="hand2", padx=16, pady=9,
            font=(TOKENS["font_family"], 10, "bold"), state="disabled",
        )
        self.pull_button.pack(side="right", padx=(0, 8))
        self.push_button = tk.Button(
            button_row,
            text="ارسال به گیت‌هاب",
            command=self._push,
            bg=p["success"], fg="#FFFFFF",
            activebackground=p["success"], activeforeground="#FFFFFF",
            relief="flat", cursor="hand2", padx=16, pady=9,
            font=(TOKENS["font_family"], 10, "bold"), state="disabled",
        )
        self.push_button.pack(side="right")

        tk.Label(
            actions_body,
            text="گزارش عملیات",
            bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9, "bold"), anchor="e",
        ).pack(fill="x", pady=(2, 5))
        log_frame = tk.Frame(
            actions_body, bg=p["border"], highlightthickness=1,
            highlightbackground=p["border"],
        )
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame, height=10, wrap="word", state="disabled",
            bg=p["bg"], fg=p["text"], insertbackground=p["text"],
            selectbackground=p["accent"], relief="flat", padx=10, pady=8,
            font=(TOKENS["font_mono"], 9),
        )
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side="right", fill="both", expand=True)
        log_scrollbar.pack(side="left", fill="y")

        _, auto_body = self._make_card(body, "همگام‌سازی خودکار", "◷")
        auto_row = tk.Frame(auto_body, bg=p["card"])
        auto_row.pack(fill="x")
        self.auto_sync_var = tk.BooleanVar(value=False)
        self.auto_sync_toggle = ttk.Checkbutton(
            auto_row,
            text="دریافت خودکار تغییرات هر ۶۰ ثانیه",
            variable=self.auto_sync_var,
            command=self._toggle_auto_sync,
        )
        self.auto_sync_toggle.pack(side="right")
        tk.Label(
            auto_row,
            text="ارسال به مخزن فقط با فشردن دکمه ارسال انجام می‌شود.",
            bg=p["card"], fg=p["muted"],
            font=(TOKENS["font_family"], 9), anchor="e",
        ).pack(side="left", padx=(8, 0))

    def _make_card(self, parent, title, icon):
        p: dict[str, Any] = self.palette
        card = ModernCard(parent, bg=p["card"], border_color=p["border"])
        card.pack(fill="x", pady=(0, 12))
        body = tk.Frame(card, bg=p["card"], padx=16, pady=13)
        body.pack(fill="both", expand=True)
        heading = tk.Frame(body, bg=p["card"])
        heading.pack(fill="x", pady=(0, 10))
        tk.Label(
            heading, text=title, bg=p["card"], fg=p["text"],
            font=(TOKENS["font_family"], TOKENS["font_section"], "bold"),
            anchor="e",
        ).pack(side="right")
        tk.Label(
            heading, text=icon, bg=p["card"], fg=p["accent"],
            font=("Segoe UI Symbol", 13, "bold"),
        ).pack(side="right", padx=(0, 7))
        return card, body

    def _find_repository(self):
        candidates = (Path.cwd(), Path(__file__).resolve().parents[3])
        seen = set()
        for candidate in candidates:
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=candidate,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip()).resolve()
        return None

    def _refresh_status(self):
        self.status_label.config(text="در حال بررسی مخزن...", fg=self.palette["muted"])
        self.status_dot.config(fg=self.palette["muted"])
        threading.Thread(target=self._inspect_repository, daemon=True).start()

    def _inspect_repository(self):
        try:
            repo = self._find_repository()
            if repo is None:
                self._events.put(("status", None, "", ""))
                return
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], cwd=repo,
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=False,
            )
            remote_result = subprocess.run(
                ["git", "remote", "get-url", "origin"], cwd=repo,
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=False,
            )
            branch = branch_result.stdout.strip() or "HEAD جداشده"
            remote = remote_result.stdout.strip() if remote_result.returncode == 0 else ""
            self._events.put(("status", str(repo), branch, remote))
        except FileNotFoundError:
            self._events.put(("status_error", "برنامه git در سیستم پیدا نشد."))
        except Exception as exc:
            self._events.put(("status_error", f"خطا در بررسی مخزن: {exc}"))

    def _poll_events(self):
        if self._destroyed:
            return
        try:
            while True:
                event = self._events.get_nowait()
                if event[0] == "log":
                    self._append_log(event[1])
                elif event[0] == "status":
                    _, repo, branch, remote = event
                    self._repo_root = Path(repo) if repo else None
                    connected = bool(repo and remote)
                    color = self.palette["success"] if connected else self.palette["danger"]
                    text = "مخزن متصل است" if connected else "مخزن گیت‌هاب تنظیم نشده است"
                    self.status_label.config(text=text, fg=color)
                    self.status_dot.config(fg=color)
                    self.branch_label.config(text=f"شاخه: {branch or '—'}")
                    self.remote_label.config(text=f"مخزن: {remote or 'origin تنظیم نشده'}")
                    self._set_action_state()
                elif event[0] == "status_error":
                    self._repo_root = None
                    self.status_label.config(text=event[1], fg=self.palette["danger"])
                    self.status_dot.config(fg=self.palette["danger"])
                    self.branch_label.config(text="شاخه: —")
                    self.remote_label.config(text="مخزن: —")
                    self._set_action_state()
                elif event[0] == "done":
                    self._busy = False
                    self._set_action_state()
                    self._refresh_status()
        except queue.Empty:
            pass
        self._poll_job = self.after(100, self._poll_events)

    def _append_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{text}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_action_state(self):
        state = "normal" if self._repo_root and not self._busy else "disabled"
        self.pull_button.config(state=state)
        self.push_button.config(state=state)

    def _pull(self, automatic=False):
        if not self._repo_root or self._busy:
            return
        label = "دریافت خودکار" if automatic else "دریافت از گیت‌هاب"
        self._start_operation(label, [("git", "pull", "--ff-only")])

    def _push(self):
        if not self._repo_root or self._busy:
            return
        confirmed = messagebox.askyesno(
            "تأیید ارسال",
            "تمام تغییرات کاری، شامل فایل‌های جدید، stage و commit می‌شوند و به origin ارسال خواهند شد. ادامه می‌دهید؟",
            parent=self,
        )
        if confirmed:
            self._start_operation("ارسال به گیت‌هاب", "push")

    def _start_operation(self, label, commands):
        if self._busy:
            return
        self._busy = True
        self._set_action_state()
        self._events.put(("log", f"\n--- {label} ---"))
        threading.Thread(
            target=self._run_operation,
            args=(commands,),
            daemon=True,
        ).start()

    def _run_operation(self, commands):
        try:
            repo = self._repo_root
            if isinstance(commands, str) and commands == "push":
                if not self._run_git(repo, ["git", "add", "-A"]):
                    return
                staged = subprocess.run(
                    ["git", "diff", "--cached", "--quiet"], cwd=repo,
                    capture_output=True, check=False,
                )
                if staged.returncode == 1:
                    if not self._run_git(
                        repo, ["git", "commit", "-m", "Sync from ElectroCalc"]
                    ):
                        return
                elif staged.returncode != 0:
                    self._events.put(("log", "خطا در بررسی تغییرات stageشده."))
                    return
                else:
                    self._events.put(("log", "تغییر جدیدی برای commit وجود ندارد."))

                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"], cwd=repo,
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", check=False,
                )
                branch = branch_result.stdout.strip()
                if not branch:
                    self._events.put(("log", "ارسال ممکن نیست: شاخه فعالی انتخاب نشده است."))
                    return
                self._run_git(repo, ["git", "push", "-u", "origin", branch])
            else:
                for command in commands:
                    if not self._run_git(repo, list(command)):
                        break
        except Exception as exc:
            self._events.put(("log", f"خطا: {exc}"))
        finally:
            self._events.put(("done",))

    def _run_git(self, repo, command):
        self._events.put(("log", f"$ {' '.join(command)}"))
        try:
            process = subprocess.Popen(
                command,
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            if process.stdout is not None:
                for line in process.stdout:
                    self._events.put(("log", line.rstrip()))
            return_code = process.wait()
        except FileNotFoundError:
            self._events.put(("log", "خطا: برنامه git در سیستم پیدا نشد."))
            return False
        if return_code:
            self._events.put(("log", f"فرمان با کد {return_code} ناموفق بود."))
            return False
        self._events.put(("log", "فرمان با موفقیت انجام شد."))
        return True

    def _toggle_auto_sync(self):
        if self.auto_sync_var.get():
            self._append_log("دریافت خودکار هر ۶۰ ثانیه فعال شد.")
            self._schedule_auto_sync()
        else:
            if self._auto_job is not None:
                self.after_cancel(self._auto_job)
                self._auto_job = None
            self._append_log("دریافت خودکار غیرفعال شد.")

    def _schedule_auto_sync(self):
        if self._destroyed or not self.auto_sync_var.get():
            return
        self._auto_job = self.after(60_000, self._auto_sync_tick)

    def _auto_sync_tick(self):
        self._auto_job = None
        if self.auto_sync_var.get():
            if self._repo_root and not self._busy:
                self._pull(automatic=True)
            else:
                self._append_log("دریافت خودکار رد شد؛ مخزن متصل نیست یا عملیات دیگری در جریان است.")
            self._schedule_auto_sync()

    def destroy(self):
        self._destroyed = True
        for job in (self._poll_job, self._auto_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        super().destroy()