"""تب انبار — مدیریت کالا، ورود و خروج، هشدار کمبود."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from pathlib import Path
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import warehouse as wh
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


class WarehouseTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def _is_admin(self):
        return (self.app.current_user
                and self.app.current_user["role"] == "admin")

    def build_ui(self):
        parent = self.inner

        # عنوان
        ttk.Label(parent, text="🏭  انبار",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent,
                  text="مدیریت موجودی، ورود و خروج کالا",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # آمار (کارت)
        self.stats_frame = tk.Frame(parent, bg=C.COLOR_BG)
        self.stats_frame.pack(fill="x", pady=(0, 15))

        # دکمه‌ها
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 12))

        ttk.Button(bar, text="+ کالای جدید",
                   command=self._new_item).pack(side="left")
        ttk.Button(bar, text="✏️ ویرایش",
                   command=self._edit_item).pack(side="left", padx=5)
        ttk.Button(bar, text="📥 ورود کالا",
                   command=lambda: self._transaction("in")).pack(side="left")
        ttk.Button(bar, text="📤 خروج کالا",
                   command=lambda: self._transaction("out")).pack(side="left", padx=5)
        ttk.Button(bar, text="📋 تراکنش‌ها",
                   command=self._show_transactions).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete_item).pack(side="left", padx=5)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=5)

        # فیلترها
        filter_box = ttk.LabelFrame(parent, text="🔍 فیلتر", padding=10)
        filter_box.pack(fill="x", pady=(0, 12))

        row1 = ttk.Frame(filter_box)
        row1.pack(fill="x")

        ttk.Label(row1, text="جستجو:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))
        self.search_var = StringVar()
        e = ttk.Entry(row1, textvariable=self.search_var, width=20)
        e.pack(side="right", padx=(0, 15))
        e.bind("<KeyRelease>", lambda ev: self.refresh())

        ttk.Label(row1, text="دسته:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))
        self.category_var = StringVar(value="همه")
        cat_combo = ttk.Combobox(row1, textvariable=self.category_var,
                                   values=["همه"] + wh.CATEGORIES,
                                   state="readonly", width=18)
        cat_combo.pack(side="right", padx=(0, 15))
        cat_combo.bind("<<ComboboxSelected>>", lambda ev: self.refresh())

        self.low_stock_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1, text="فقط کمبود موجودی",
                       variable=self.low_stock_var,
                       bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                       activebackground=C.COLOR_BG,
                       font=C.FONT_BODY,
                       command=self.refresh).pack(side="right", padx=(0, 15))

        # جدول
        cols = ("id", "name", "category", "quantity", "unit",
                "min_qty", "purchase", "sale", "supplier", "value")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)

        headers = {
            "id": "ID", "name": "نام کالا", "category": "دسته",
            "quantity": "موجودی", "unit": "واحد",
            "min_qty": "حداقل", "purchase": "خرید",
            "sale": "فروش", "supplier": "تأمین‌کننده", "value": "ارزش",
        }
        widths = {
            "id": 40, "name": 180, "category": 130,
            "quantity": 80, "unit": 60, "min_qty": 70,
            "purchase": 90, "sale": 90, "supplier": 130, "value": 100,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="w" if c in ("name", "category", "supplier")
                              else "center")

        self.tree.pack(fill="both", expand=True)

        # رنگ‌بندی هشدار
        self.tree.tag_configure("low", background="#fff3cd")
        self.tree.tag_configure("out", background="#f8d7da")

        # دابل کلیک
        self.tree.bind("<Double-1>", lambda e: self._edit_item())

    # ========================================================
    def refresh(self):
        # آمار
        for w in self.stats_frame.winfo_children():
            w.destroy()

        stats = wh.get_stats()

        cards = [
            ("📦", "کالاها", stats["total_items"], C.COLOR_HEADER_BG),
            ("💰", "ارزش انبار",
             f"{stats['total_value']:,.0f}", C.COLOR_SUCCESS),
            ("⚠️", "کمبود", stats["low_stock"],
             C.COLOR_ACCENT if stats["low_stock"] else C.COLOR_MUTED),
            ("❌", "تمام‌شده", stats["out_of_stock"],
             C.COLOR_DANGER if stats["out_of_stock"] else C.COLOR_MUTED),
        ]

        for icon, title, value, color in cards:
            card = tk.Frame(self.stats_frame, bg=C.COLOR_TAB_BG,
                             highlightbackground=color, highlightthickness=2)
            card.pack(side="right", fill="both", expand=True, padx=4)

            tk.Label(card, text=icon, font=("Segoe UI Emoji", 18),
                     bg=C.COLOR_TAB_BG, fg=color).pack(pady=(10, 2))
            tk.Label(card, text=str(value), font=("Segoe UI", 14, "bold"),
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_TEXT).pack()
            tk.Label(card, text=title, font=C.FONT_SMALL,
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_MUTED).pack(pady=(0, 10))

        # جدول
        for i in self.tree.get_children():
            self.tree.delete(i)

        search = self.search_var.get().strip()
        category = None if self.category_var.get() == "همه" else self.category_var.get()

        items = wh.list_items(search, category,
                                low_stock_only=self.low_stock_var.get())

        for item in items:
            qty = item["quantity"] or 0
            min_qty = item["min_quantity"] or 0
            purchase = item["purchase_price"] or 0
            value = qty * purchase

            # tag بر اساس موجودی
            tags = ()
            if qty <= 0:
                tags = ("out",)
            elif min_qty > 0 and qty <= min_qty:
                tags = ("low",)

            self.tree.insert("", "end", iid=str(item["id"]),
                              values=(item["id"], item["name"],
                                       item["category"] or "-",
                                       f"{qty:,.2f}",
                                       item["unit"] or "-",
                                       f"{min_qty:,.2f}",
                                       f"{purchase:,.0f}",
                                       f"{item['sale_price'] or 0:,.0f}",
                                       item["supplier"] or "-",
                                       f"{value:,.0f}"),
                              tags=tags)

    # ========================================================
    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "اول یک کالا انتخاب کن.")
            return None
        return int(s[0])

    def _new_item(self):
        ItemDialog(self.winfo_toplevel(), on_done=self.refresh)

    def _edit_item(self):
        item_id = self._selected_id()
        if not item_id:
            return
        ItemDialog(self.winfo_toplevel(), on_done=self.refresh,
                    item_id=item_id)

    def _delete_item(self):
        item_id = self._selected_id()
        if not item_id:
            return
        if not messagebox.askyesno("تأیید",
                                     "این کالا و همه تراکنش‌هاش حذف شوند؟"):
            return
        wh.delete_item(item_id)
        self.refresh()

    def _transaction(self, trans_type):
        item_id = self._selected_id()
        if not item_id:
            return
        item = wh.get_item(item_id)
        if not item:
            return
        TransactionDialog(self.winfo_toplevel(), item, trans_type,
                           on_done=self.refresh,
                           user=(self.app.current_user["username"]
                                 if self.app.current_user else ""))

    def _show_transactions(self):
        item_id = self._selected_id()
        if not item_id:
            return
        item = wh.get_item(item_id)
        if not item:
            return
        TransactionsListDialog(self.winfo_toplevel(), item,
                                on_done=self.refresh)


# ========================================================
class ItemDialog:
    """پنجره کالای جدید/ویرایش."""

    def __init__(self, parent, on_done=None, item_id=None):
        self.on_done = on_done
        self.item_id = item_id
        self.win = tk.Toplevel(parent)
        self.win.title("کالای جدید" if not item_id else "ویرایش کالا")
        self.win.geometry("500x620")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()
        if item_id:
            self._load()

    def _build_ui(self):
        tk.Label(self.win,
                 text="➕ کالای جدید" if not self.item_id else "✏️ ویرایش کالا",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        self.vars = {}
        # نام
        self.vars["name"] = StringVar()
        # دسته
        self.vars["category"] = StringVar(value="کابل و سیم")
        # واحد
        self.vars["unit"] = StringVar(value="عدد")
        # موجودی
        self.vars["quantity"] = StringVar(value="0")
        # حداقل
        self.vars["min_quantity"] = StringVar(value="0")
        # قیمت خرید
        self.vars["purchase_price"] = StringVar(value="0")
        # قیمت فروش
        self.vars["sale_price"] = StringVar(value="0")
        # تأمین‌کننده
        self.vars["supplier"] = StringVar()
        # محل
        self.vars["location"] = StringVar()
        # توضیحات
        self.vars["description"] = StringVar()

        row = 0

        # نام
        tk.Label(f, text="نام کالا *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.vars["name"], width=30).grid(
            row=row, column=1, sticky="ew", pady=5)
        row += 1

        # دسته
        tk.Label(f, text="دسته:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(f, textvariable=self.vars["category"],
                      values=wh.CATEGORIES, width=28).grid(
            row=row, column=1, sticky="ew", pady=5)
        row += 1

        # واحد
        tk.Label(f, text="واحد:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(f, textvariable=self.vars["unit"],
                      values=["عدد", "متر", "کیلوگرم", "بسته",
                              "حلقه", "لیتر", "متر مربع"],
                      width=28).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # موجودی + حداقل — کنار هم
        row_frame = tk.Frame(f, bg=C.COLOR_BG)
        row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(row_frame, text="موجودی:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(row_frame, textvariable=self.vars["quantity"],
                  width=10).pack(side="right", padx=(0, 20))
        tk.Label(row_frame, text="حداقل موجودی:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(row_frame, textvariable=self.vars["min_quantity"],
                  width=10).pack(side="right")
        row += 1

        # قیمت خرید + فروش
        row_frame2 = tk.Frame(f, bg=C.COLOR_BG)
        row_frame2.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(row_frame2, text="قیمت خرید:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(row_frame2, textvariable=self.vars["purchase_price"],
                  width=12).pack(side="right", padx=(0, 20))
        tk.Label(row_frame2, text="قیمت فروش:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(row_frame2, textvariable=self.vars["sale_price"],
                  width=12).pack(side="right")
        row += 1

        # تأمین‌کننده
        tk.Label(f, text="تأمین‌کننده:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.vars["supplier"], width=30).grid(
            row=row, column=1, sticky="ew", pady=5)
        row += 1

        # محل نگهداری
        tk.Label(f, text="محل نگهداری:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.vars["location"], width=30).grid(
            row=row, column=1, sticky="ew", pady=5)
        row += 1

        # توضیحات
        tk.Label(f, text="توضیحات:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(f, width=30, height=4, font=C.FONT_BODY)
        self.desc_text.grid(row=row, column=1, sticky="ew", pady=5)

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="💾 ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _load(self):
        item = wh.get_item(self.item_id)
        if not item:
            return
        for k in ["name", "category", "unit", "supplier", "location"]:
            self.vars[k].set(item[k] or "")

        self.vars["quantity"].set(str(item["quantity"] or 0))
        self.vars["min_quantity"].set(str(item["min_quantity"] or 0))
        self.vars["purchase_price"].set(str(item["purchase_price"] or 0))
        self.vars["sale_price"].set(str(item["sale_price"] or 0))
        self.desc_text.insert("1.0", item["description"] or "")

    def _save(self):
        try:
            def to_float(s):
                return float(str(s).replace(",", "").strip() or "0")

            desc = self.desc_text.get("1.0", "end").strip()

            data = dict(
                name=self.vars["name"].get(),
                category=self.vars["category"].get(),
                unit=self.vars["unit"].get(),
                quantity=to_float(self.vars["quantity"].get()),
                min_quantity=to_float(self.vars["min_quantity"].get()),
                purchase_price=to_float(self.vars["purchase_price"].get()),
                sale_price=to_float(self.vars["sale_price"].get()),
                supplier=self.vars["supplier"].get(),
                location=self.vars["location"].get(),
                description=desc,
            )

            if self.item_id:
                wh.update_item(self.item_id, **data)
            else:
                wh.create_item(**data)

            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)


# ========================================================
class TransactionDialog:
    """پنجره ورود/خروج کالا."""

    def __init__(self, parent, item, trans_type, on_done=None, user=""):
        self.item = item
        self.trans_type = trans_type
        self.on_done = on_done
        self.user = user

        self.win = tk.Toplevel(parent)
        title = "📥 ورود کالا" if trans_type == "in" else "📤 خروج کالا"
        self.win.title(title)
        self.win.geometry("480x520")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        icon = "📥" if self.trans_type == "in" else "📤"
        title = "ورود کالا" if self.trans_type == "in" else "خروج کالا"

        tk.Label(self.win, text=f"{icon}  {title}",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 5))

        tk.Label(self.win, text=self.item["name"],
                 font=("Segoe UI", 12, "bold"),
                 bg=C.COLOR_BG, fg=C.COLOR_ACCENT).pack()

        tk.Label(self.win,
                 text=f"موجودی فعلی: {self.item['quantity']:,.2f} {self.item['unit']}",
                 font=C.FONT_BODY, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).pack(pady=(0, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="x")

        self.quantity_var = StringVar()
        self.unit_price_var = StringVar(
            value=str(self.item["purchase_price"] or 0))
        self.project_var = StringVar()
        self.supplier_var = StringVar(value=self.item["supplier"] or "")
        self.note_var = StringVar()

        row = 0
        tk.Label(f, text="تعداد *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.quantity_var, width=25).grid(
            row=row, column=1, sticky="ew", pady=6)
        row += 1

        if self.trans_type == "in":
            tk.Label(f, text="قیمت واحد:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(f, textvariable=self.unit_price_var, width=25).grid(
                row=row, column=1, sticky="ew", pady=6)
            row += 1

            tk.Label(f, text="تأمین‌کننده:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(f, textvariable=self.supplier_var, width=25).grid(
                row=row, column=1, sticky="ew", pady=6)
            row += 1
        else:
            # خروج → پروژه
            tk.Label(f, text="پروژه:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=6)
            projects = proj.list_projects()
            self.project_map = {"(بدون پروژه)": None}
            for p in projects:
                d = f"{p['id']} - {p['name']}"
                self.project_map[d] = p["id"]

            combo = ttk.Combobox(f, textvariable=self.project_var,
                                   values=list(self.project_map.keys()),
                                   state="readonly", width=23)
            combo.grid(row=row, column=1, sticky="ew", pady=6)
            combo.current(0)
            row += 1

        tk.Label(f, text="توضیحات:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.note_var, width=25).grid(
            row=row, column=1, sticky="ew", pady=6)

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="✅ ثبت", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _save(self):
        try:
            qty_text = self.quantity_var.get().strip()
            if not qty_text:
                raise ValueError("تعداد الزامی است.")
            qty = float(qty_text.replace(",", ""))

            if qty <= 0:
                raise ValueError("تعداد باید بزرگ‌تر از صفر باشد.")

            # اگه خروج
            if self.trans_type == "out":
                current = self.item["quantity"] or 0
                if qty > current:
                    messagebox.showerror("خطا",
                        f"موجودی کافی نیست.\nموجودی فعلی: {current}",
                        parent=self.win)
                    return

            unit_price = 0
            if self.trans_type == "in":
                try:
                    unit_price = float(self.unit_price_var.get().replace(",", "") or 0)
                except Exception:
                    unit_price = 0

            project_id = None
            if self.trans_type == "out":
                project_id = self.project_map.get(self.project_var.get())

            wh.add_transaction(
                item_id=self.item["id"],
                trans_type=self.trans_type,
                quantity=qty,
                unit_price=unit_price,
                project_id=project_id,
                supplier=self.supplier_var.get(),
                note=self.note_var.get(),
                created_by=self.user,
            )

            # اگه بعد از خروج، موجودی کم شد → هشدار
            if self.trans_type == "out":
                updated = wh.get_item(self.item["id"])
                if updated and updated["min_quantity"] > 0:
                    if updated["quantity"] <= updated["min_quantity"]:
                        try:
                            from electrocalc.core import notifications as notif
                            notif.notify_admins(
                                title=f"⚠️ کمبود انبار: {updated['name']}",
                                message=f"موجودی الان: {updated['quantity']} {updated['unit']}",
                                category="warning",
                            )
                        except Exception:
                            pass

            self.win.destroy()
            if self.on_done:
                self.on_done()

        except ValueError as e:
            messagebox.showerror("خطا", str(e), parent=self.win)
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)


# ========================================================
class TransactionsListDialog:
    """پنجره لیست تراکنش‌های یک کالا."""

    def __init__(self, parent, item, on_done=None):
        self.item = item
        self.on_done = on_done

        self.win = tk.Toplevel(parent)
        self.win.title(f"تراکنش‌های {item['name']}")
        self.win.geometry("800x500")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.win, text=f"📋  تراکنش‌های {self.item['name']}",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 10))

        cols = ("id", "date", "type", "qty", "price", "total",
                "project", "supplier", "note")
        tree = ttk.Treeview(self.win, columns=cols, show="headings", height=15)

        headers = {
            "id": "ID", "date": "تاریخ", "type": "نوع",
            "qty": "تعداد", "price": "قیمت", "total": "جمع",
            "project": "پروژه", "supplier": "تأمین‌کننده", "note": "توضیح",
        }
        widths = {
            "id": 40, "date": 90, "type": 70, "qty": 70,
            "price": 90, "total": 100, "project": 130,
            "supplier": 110, "note": 150,
        }

        for c in cols:
            tree.heading(c, text=headers[c])
            tree.column(c, width=widths[c],
                         anchor="w" if c in ("project", "supplier", "note")
                         else "center")

        tree.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        tree.tag_configure("in", foreground=C.COLOR_SUCCESS)
        tree.tag_configure("out", foreground=C.COLOR_DANGER)

        transactions = wh.list_transactions(item_id=self.item["id"])

        for t in transactions:
            t_type = "📥 ورود" if t["type"] == "in" else "📤 خروج"
            tree.insert("", "end", values=(
                t["id"], t["trans_date"] or "-",
                t_type,
                f"{t['quantity']:,.2f}",
                f"{t['unit_price'] or 0:,.0f}",
                f"{t['total_price'] or 0:,.0f}",
                t["project_name"] or "-",
                t["supplier"] or "-",
                t["note"] or "-",
            ), tags=(t["type"],))

        ttk.Button(self.win, text="بستن",
                   command=self.win.destroy).pack(pady=10, ipadx=20)