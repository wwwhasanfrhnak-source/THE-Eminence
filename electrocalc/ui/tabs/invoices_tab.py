"""تب فاکتور — فروش کالا و خدمات."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from electrocalc.core import invoices as inv


class InvoicesTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f8fafc")

        self.original_parent = parent
        self.app = app
        self.current_user = dict(app.current_user) if app.current_user else {}
        self.username = self.current_user.get("username", "")

        self.current_invoice_id = None
        self.items = []

        self._build_ui()
        self._refresh_list()

    # ====================================================
    # UI
    # ====================================================
    def _build_ui(self):
        # هدر
        header = tk.Frame(self, bg="#7c3aed", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🧾  فاکتورها",
            bg="#7c3aed", fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="right", padx=20, pady=15)

        # نوار ابزار
        toolbar = tk.Frame(self, bg="#f8fafc")
        toolbar.pack(fill="x", padx=15, pady=10)

        tk.Button(
            toolbar, text="➕ فاکتور جدید", bg="#10b981", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=6, cursor="hand2",
            command=self._new_invoice,
        ).pack(side="right", padx=5)

        tk.Button(
            toolbar, text="🔄 بروزرسانی", bg="#06b6d4", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=6, cursor="hand2",
            command=self._refresh_list,
        ).pack(side="right", padx=5)

        tk.Label(toolbar, text="جستجو:", bg="#f8fafc",
                 font=("Segoe UI", 10)).pack(side="right", padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._refresh_list())
        tk.Entry(toolbar, textvariable=self.search_var,
                 font=("Segoe UI", 10), width=25).pack(side="right")

        # لیست فاکتورها
        list_frame = tk.LabelFrame(
            self, text=" 📋 لیست فاکتورها ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=10, pady=10,
        )
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("number", "customer", "date", "total", "status")
        self.tree = ttk.Treeview(list_frame, columns=cols,
                                  show="headings", height=12)

        headers = {
            "number": "شماره",
            "customer": "مشتری",
            "date": "تاریخ",
            "total": "مبلغ (تومان)",
            "status": "وضعیت",
        }
        for col, txt in headers.items():
            self.tree.heading(col, text=txt)
            self.tree.column(col, anchor="center",
                              width=150 if col != "customer" else 200)

        self.tree.pack(fill="both", expand=True, side="right")

        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.bind("<Double-1>", lambda e: self._edit_invoice())

        # دکمه‌های عملیات
        ops = tk.Frame(self, bg="#f8fafc")
        ops.pack(fill="x", padx=15, pady=5)

        tk.Button(ops, text="✏️ ویرایش", bg="#f59e0b", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=15, pady=6, cursor="hand2",
                  command=self._edit_invoice).pack(side="right", padx=5)

        tk.Button(ops, text="📄 PDF", bg="#ef4444", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=15, pady=6, cursor="hand2",
                  command=self._export_pdf).pack(side="right", padx=5)

        tk.Button(ops, text="🗑️ حذف", bg="#6b7280", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=15, pady=6, cursor="hand2",
                  command=self._delete_invoice).pack(side="right", padx=5)

    # ====================================================
    # لیست
    # ====================================================
    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get().strip()
        try:
            rows = inv.list_invoices(search=search)
        except Exception as e:
            print(f"خطا در لیست فاکتورها: {e}")
            rows = []

        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["number"],
                r.get("customer_name") or "—",
                r["issue_date"],
                f"{r['total']:,.0f}",
                r["status"],
            ))

    # ====================================================
    # جدید / ویرایش
    # ====================================================
    def _new_invoice(self):
        InvoiceDialog(self.original_parent, self, invoice_id=None)

    def _edit_invoice(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "یه فاکتور انتخاب کن")
            return
        InvoiceDialog(self.original_parent, self, invoice_id=int(sel[0]))

    def _delete_invoice(self):
        sel = self.tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("حذف", "مطمئنی؟"):
            return
        inv.delete_invoice(int(sel[0]))
        self._refresh_list()

    def _export_pdf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "یه فاکتور انتخاب کن")
            return
        try:
            path = inv.build_invoice_pdf(int(sel[0]))
            messagebox.showinfo("موفق", f"PDF ساخته شد:\n{path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))


# ========================================================
# دیالوگ فاکتور
# ========================================================
class InvoiceDialog:
    def __init__(self, parent, tab, invoice_id=None):
        self.tab = tab
        self.invoice_id = invoice_id
        self.items = []
        self.customers = {}
        self.projects = {}

        self.win = tk.Toplevel(parent)
        self.win.title("فاکتور جدید" if not invoice_id else "ویرایش فاکتور")
        self.win.geometry("900x650")
        self.win.configure(bg="#f8fafc")

        self._build()

        if invoice_id:
            self._load()

    def _build(self):
        tk.Label(self.win, text="🧾  فاکتور",
                 bg="#7c3aed", fg="white",
                 font=("Segoe UI", 14, "bold"),
                 pady=10).pack(fill="x")

        form = tk.Frame(self.win, bg="#f8fafc")
        form.pack(fill="x", padx=15, pady=10)

        # ردیف ۱
        row1 = tk.Frame(form, bg="#f8fafc")
        row1.pack(fill="x", pady=5)

        tk.Label(row1, text="مشتری:", bg="#f8fafc",
                 font=("Segoe UI", 10), width=10,
                 anchor="e").pack(side="right")
        self.customer_var = tk.StringVar()
        self.customer_combo = ttk.Combobox(
            row1, textvariable=self.customer_var,
            font=("Segoe UI", 10), width=30, state="readonly")
        self.customer_combo.pack(side="right", padx=5)

        tk.Label(row1, text="پروژه:", bg="#f8fafc",
                 font=("Segoe UI", 10), width=10,
                 anchor="e").pack(side="right", padx=(20, 0))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(
            row1, textvariable=self.project_var,
            font=("Segoe UI", 10), width=30, state="readonly")
        self.project_combo.pack(side="right", padx=5)

        self._load_customers()
        self._load_projects()

        # ردیف ۲
        row2 = tk.Frame(form, bg="#f8fafc")
        row2.pack(fill="x", pady=5)

        tk.Label(row2, text="تاریخ:", bg="#f8fafc",
                 font=("Segoe UI", 10), width=10,
                 anchor="e").pack(side="right")
        self.date_entry = tk.Entry(row2, font=("Segoe UI", 10), width=15)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="right", padx=5)

        tk.Label(row2, text="وضعیت:", bg="#f8fafc",
                 font=("Segoe UI", 10), width=10,
                 anchor="e").pack(side="right", padx=(20, 0))
        self.status_var = tk.StringVar(value="پیش‌نویس")
        ttk.Combobox(row2, textvariable=self.status_var,
                     values=["پیش‌نویس", "ارسال‌شده", "پرداخت‌شده", "لغو‌شده"],
                     font=("Segoe UI", 10), width=15,
                     state="readonly").pack(side="right", padx=5)

        # آیتم‌ها
        items_frame = tk.LabelFrame(
            self.win, text=" 📦 آیتم‌ها ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=10, pady=10,
        )
        items_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("desc", "qty", "price", "total")
        self.items_tree = ttk.Treeview(items_frame, columns=cols,
                                        show="headings", height=8)
        headers = {
            "desc": "شرح",
            "qty": "تعداد",
            "price": "قیمت واحد",
            "total": "جمع",
        }
        for col, txt in headers.items():
            self.items_tree.heading(col, text=txt)
            self.items_tree.column(col, anchor="center",
                                    width=150 if col != "desc" else 300)
        self.items_tree.pack(fill="both", expand=True, side="right")

        sb = ttk.Scrollbar(items_frame, orient="vertical",
                            command=self.items_tree.yview)
        sb.pack(side="left", fill="y")
        self.items_tree.configure(yscrollcommand=sb.set)

        add_row = tk.Frame(self.win, bg="#f8fafc")
        add_row.pack(fill="x", padx=15)

        tk.Button(add_row, text="➕ افزودن آیتم",
                  bg="#06b6d4", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=15, pady=6, cursor="hand2",
                  command=self._add_item).pack(side="right", padx=5)

        tk.Button(add_row, text="➖ حذف آیتم انتخاب‌شده",
                  bg="#ef4444", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=15, pady=6, cursor="hand2",
                  command=self._remove_item).pack(side="right", padx=5)

        sums = tk.Frame(self.win, bg="#f8fafc")
        sums.pack(fill="x", padx=15, pady=10)

        tk.Label(sums, text="جمع کل:", bg="#f8fafc",
                 font=("Segoe UI", 11, "bold")).pack(side="right")
        self.subtotal_lbl = tk.Label(sums, text="0",
                                       bg="#f8fafc", fg="#7c3aed",
                                       font=("Segoe UI", 11, "bold"))
        self.subtotal_lbl.pack(side="right", padx=10)

        tk.Label(sums, text="تخفیف (%):", bg="#f8fafc",
                 font=("Segoe UI", 10)).pack(side="right", padx=(30, 5))
        self.discount_var = tk.StringVar(value="0")
        self.discount_var.trace("w", lambda *a: self._recalc())
        tk.Entry(sums, textvariable=self.discount_var,
                 font=("Segoe UI", 10), width=6).pack(side="right")

        tk.Label(sums, text="مالیات (%):", bg="#f8fafc",
                 font=("Segoe UI", 10)).pack(side="right", padx=(20, 5))
        self.tax_var = tk.StringVar(value="9")
        self.tax_var.trace("w", lambda *a: self._recalc())
        tk.Entry(sums, textvariable=self.tax_var,
                 font=("Segoe UI", 10), width=6).pack(side="right")

        tk.Label(sums, text="قابل پرداخت:", bg="#f8fafc",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
        self.total_lbl = tk.Label(sums, text="0",
                                    bg="#f8fafc", fg="#10b981",
                                    font=("Segoe UI", 12, "bold"))
        self.total_lbl.pack(side="left")

        actions = tk.Frame(self.win, bg="#f8fafc")
        actions.pack(fill="x", padx=15, pady=10)

        tk.Button(actions, text="💾 ذخیره",
                  bg="#10b981", fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat",
                  padx=25, pady=8, cursor="hand2",
                  command=self._save).pack(side="right", padx=5)

        tk.Button(actions, text="❌ انصراف",
                  bg="#6b7280", fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat",
                  padx=25, pady=8, cursor="hand2",
                  command=self.win.destroy).pack(side="right", padx=5)

    def _load_customers(self):
        try:
            from electrocalc.data.database import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM customers ORDER BY name")
            self.customers = {r["name"]: r["id"] for r in cur.fetchall()}
            conn.close()
        except Exception as e:
            print(f"خطا در لود مشتریان: {e}")
            self.customers = {}
        self.customer_combo["values"] = list(self.customers.keys())

    def _load_projects(self):
        try:
            from electrocalc.data.database import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY name")
            self.projects = {r["name"]: r["id"] for r in cur.fetchall()}
            conn.close()
        except Exception as e:
            print(f"خطا در لود پروژه‌ها: {e}")
            self.projects = {}
        self.project_combo["values"] = ["—"] + list(self.projects.keys())

    def _add_item(self):
        ItemDialog(self.win, self)

    def _remove_item(self):
        sel = self.items_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.items[idx]
        self._refresh_items()

    def _refresh_items(self):
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        for i, it in enumerate(self.items):
            self.items_tree.insert("", "end", iid=str(i), values=(
                it["description"],
                f"{it['quantity']:,.2f}",
                f"{it['unit_price']:,.0f}",
                f"{it['quantity'] * it['unit_price']:,.0f}",
            ))
        self._recalc()

    def _recalc(self):
        subtotal = sum(it["quantity"] * it["unit_price"] for it in self.items)

        try:
            disc = float(self.discount_var.get() or 0)
            tax = float(self.tax_var.get() or 0)
        except ValueError:
            disc = tax = 0

        disc_amt = subtotal * (disc / 100)
        tax_amt = (subtotal - disc_amt) * (tax / 100)
        total = subtotal - disc_amt + tax_amt

        self.subtotal_lbl.config(text=f"{subtotal:,.0f}")
        self.total_lbl.config(text=f"{total:,.0f}")

    def _load(self):
        data, items = inv.get_invoice(self.invoice_id)
        if not data:
            return

        if data.get("customer_name"):
            self.customer_var.set(data["customer_name"])
        if data.get("project_name"):
            self.project_var.set(data["project_name"])

        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, data["issue_date"])
        self.status_var.set(data["status"])
        self.discount_var.set(str(data["discount"]))
        self.tax_var.set(str(data["tax"]))

        self.items = [
            {
                "description": it["description"],
                "quantity": it["quantity"],
                "unit_price": it["unit_price"],
                "item_type": it.get("item_type", "کالا"),
            }
            for it in items
        ]
        self._refresh_items()

    def _save(self):
        if not self.items:
            messagebox.showwarning("هشدار", "حداقل یه آیتم اضافه کن")
            return

        customer_id = self.customers.get(self.customer_var.get())
        project_id = self.projects.get(self.project_var.get())

        try:
            disc = float(self.discount_var.get() or 0)
            tax = float(self.tax_var.get() or 0)
        except ValueError:
            disc = tax = 0

        try:
            if self.invoice_id:
                inv.update_invoice(
                    self.invoice_id, customer_id, project_id,
                    self.date_entry.get(), None, self.items,
                    discount=disc, tax=tax, status=self.status_var.get())
            else:
                inv.create_invoice(
                    customer_id, project_id,
                    self.date_entry.get(), None, self.items,
                    discount=disc, tax=tax,
                    created_by=self.tab.username,
                    status=self.status_var.get())

            messagebox.showinfo("موفق", "فاکتور ذخیره شد")
            self.tab._refresh_list()
            self.win.destroy()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))


# ========================================================
# دیالوگ آیتم
# ========================================================
class ItemDialog:
    def __init__(self, parent, invoice_dialog):
        self.invoice_dialog = invoice_dialog

        self.win = tk.Toplevel(parent)
        self.win.title("آیتم جدید")
        self.win.geometry("400x280")
        self.win.configure(bg="#f8fafc")

        tk.Label(self.win, text="📦  آیتم",
                 bg="#06b6d4", fg="white",
                 font=("Segoe UI", 12, "bold"),
                 pady=8).pack(fill="x")

        form = tk.Frame(self.win, bg="#f8fafc")
        form.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(form, text="شرح:", bg="#f8fafc",
                 font=("Segoe UI", 10)).grid(row=0, column=0,
                                              sticky="e", pady=5)
        self.desc_entry = tk.Entry(form, font=("Segoe UI", 10), width=30)
        self.desc_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="نوع:", bg="#f8fafc",
                 font=("Segoe UI", 10)).grid(row=1, column=0,
                                              sticky="e", pady=5)
        self.type_var = tk.StringVar(value="کالا")
        ttk.Combobox(form, textvariable=self.type_var,
                     values=["کالا", "خدمات"], width=27,
                     state="readonly").grid(row=1, column=1, pady=5)

        tk.Label(form, text="تعداد:", bg="#f8fafc",
                 font=("Segoe UI", 10)).grid(row=2, column=0,
                                              sticky="e", pady=5)
        self.qty_entry = tk.Entry(form, font=("Segoe UI", 10), width=30)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=2, column=1, pady=5)

        tk.Label(form, text="قیمت واحد:", bg="#f8fafc",
                 font=("Segoe UI", 10)).grid(row=3, column=0,
                                              sticky="e", pady=5)
        self.price_entry = tk.Entry(form, font=("Segoe UI", 10), width=30)
        self.price_entry.insert(0, "0")
        self.price_entry.grid(row=3, column=1, pady=5)

        tk.Button(self.win, text="✅ افزودن",
                  bg="#10b981", fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat",
                  padx=25, pady=8, cursor="hand2",
                  command=self._save).pack(pady=10)

    def _save(self):
        try:
            qty = float(self.qty_entry.get())
            price = float(self.price_entry.get())
        except ValueError:
            messagebox.showerror("خطا", "عدد وارد کن")
            return

        desc = self.desc_entry.get().strip()
        if not desc:
            messagebox.showwarning("هشدار", "شرح رو وارد کن")
            return

        self.invoice_dialog.items.append({
            "description": desc,
            "quantity": qty,
            "unit_price": price,
            "item_type": self.type_var.get(),
        })
        self.invoice_dialog._refresh_items()
        self.win.destroy()