import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# ── Database ─────────────────────────────────────────────────────────────────
DB_FILE = "expenses.db"

# ── Design Tokens ─────────────────────────────────────────────────────────────
BG          = "#0F1117"   # page background
CARD        = "#181E29"   # card background
CARD2       = "#1F2736"   # input field background
BORDER      = "#2A3447"   # border / divider
HOVER       = "#242D3E"   # row hover / subtle highlight
ROW_ALT     = "#161C28"   # alternating table row

PURPLE      = "#7C5CFC"   # primary accent
PURPLE_H    = "#9576FF"   # primary hover
PURPLE_D    = "#5A3FD4"   # primary pressed
GREEN       = "#22C55E"   # success / positive
AMBER       = "#F59E0B"   # warning / average
RED         = "#EF4444"   # danger / delete

TEXT        = "#E2E8F5"   # primary text
TEXT_SUB    = "#8896B0"   # secondary text
TEXT_MUTED  = "#3D4F6A"   # very dim text

FONT        = "Segoe UI"

CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Housing & Rent",
    "Health & Medical",
    "Entertainment",
    "Education",
    "Shopping",
    "Utilities & Bills",
    "Travel",
    "Work & Business",
    "Gifts & Donations",
    "Other",
]


# ── Database Layer ────────────────────────────────────────────────────────────
class ExpenseDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cur  = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                description TEXT,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add(self, amount, category, description=""):
        self.cur.execute(
            "INSERT INTO expenses (amount, category, description) VALUES (?,?,?)",
            (amount, category, description)
        )
        self.conn.commit()
        return self.cur.lastrowid

    def all(self):
        self.cur.execute(
            "SELECT id, amount, category, description, timestamp "
            "FROM expenses ORDER BY timestamp DESC"
        )
        return self.cur.fetchall()

    def delete(self, row_id):
        self.cur.execute("DELETE FROM expenses WHERE id=?", (row_id,))
        self.conn.commit()

    def total(self):
        self.cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses")
        return self.cur.fetchone()[0]

    def count(self):
        self.cur.execute("SELECT COUNT(*) FROM expenses")
        return self.cur.fetchone()[0]

    def close(self):
        self.conn.close()


# ── Custom Widgets ────────────────────────────────────────────────────────────
class RoundedBtn(tk.Canvas):
    """Canvas-drawn pill button with hover / press animation."""

    def __init__(self, parent, text, command=None,
                 fill=PURPLE, fill_h=PURPLE_H, fill_p=PURPLE_D,
                 fg=TEXT, btn_w=220, btn_h=42, r=10,
                 font_size=10, bold=True, **kw):
        parent_bg = parent.cget("bg") if hasattr(parent, "cget") else BG
        super().__init__(parent, width=btn_w, height=btn_h,
                         bg=parent_bg, highlightthickness=0, **kw)
        self._cmd    = command
        self._fill   = fill
        self._fill_h = fill_h
        self._fill_p = fill_p
        self._fg     = fg
        self._text   = text
        self._r      = r
        self._bw, self._bh = btn_w, btn_h
        self._font   = (FONT, font_size, "bold" if bold else "normal")
        self._draw(fill)
        self.bind("<Enter>",    lambda _: self._draw(self._fill_h))
        self.bind("<Leave>",    lambda _: self._draw(self._fill))
        self.bind("<Button-1>", lambda _: self._press())

    def _draw(self, color):
        self.delete("all")
        r, w, h = self._r, self._bw, self._bh
        pts = [r, 0, w-r, 0, w, r, w, h-r, w-r, h, r, h, 0, h-r, 0, r]
        self.create_polygon(pts, fill=color, smooth=True, outline="")
        self.create_text(w//2, h//2, text=self._text,
                         fill=self._fg, font=self._font)

    def _press(self):
        self._draw(self._fill_p)
        self.after(120, lambda: self._draw(self._fill))
        if self._cmd:
            self._cmd()


class StatCard(tk.Frame):
    """Mini KPI card with an accent left stripe."""

    def __init__(self, parent, title, color, **kw):
        super().__init__(parent, bg=CARD, padx=0, pady=0, **kw)
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")
        body = tk.Frame(self, bg=CARD, padx=18, pady=14)
        body.pack(side="left", fill="both", expand=True)
        tk.Label(body, text=title, bg=CARD, fg=TEXT_SUB,
                 font=(FONT, 8)).pack(anchor="w")
        self._val = tk.Label(body, text="—", bg=CARD, fg=TEXT,
                             font=(FONT, 17, "bold"))
        self._val.pack(anchor="w", pady=(2, 0))

    def set(self, text):
        self._val.config(text=text)


class FancyEntry(tk.Frame):
    """Styled entry widget with a focus border highlight."""

    def __init__(self, parent, textvariable=None, prefix="",
                 width=20, font_size=11, **kw):
        super().__init__(parent, bg=CARD2,
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=PURPLE, **kw)
        if prefix:
            tk.Label(self, text=prefix, bg=CARD2, fg=PURPLE,
                     font=(FONT, font_size, "bold")).pack(side="left", padx=(10, 4))
        self.entry = tk.Entry(self, textvariable=textvariable, bg=CARD2,
                              fg=TEXT, insertbackground=TEXT, relief="flat",
                              font=(FONT, font_size), bd=0, width=width)
        self.entry.pack(side="left",
                        padx=(4 if not prefix else 0, 8), pady=9)
        self.entry.bind("<FocusIn>",
                        lambda _: self.config(highlightbackground=PURPLE))
        self.entry.bind("<FocusOut>",
                        lambda _: self.config(highlightbackground=BORDER))

    def bind(self, seq, func, add=None):
        self.entry.bind(seq, func, add)

    def focus(self):
        self.entry.focus()


# ── Main Application ──────────────────────────────────────────────────────────
class ExpenseTracker:
    def __init__(self, root: tk.Tk):
        self.root    = root
        self.root.title("ExpenseIQ  —  Smart Expense Tracker")
        self.root.configure(bg=BG)
        self.root.geometry("980x680")
        self.root.minsize(820, 580)

        self.db      = ExpenseDB()
        self._id_map = {}   # treeview iid -> db row id

        self._styles()
        self._build()
        self._load_all()

    # ── ttk styles ──────────────────────────────────────────────
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("Tree.Treeview",
            background=CARD, fieldbackground=CARD, foreground=TEXT,
            rowheight=40, font=(FONT, 10), borderwidth=0, relief="flat")
        s.configure("Tree.Treeview.Heading",
            background=CARD2, foreground=TEXT_SUB,
            font=(FONT, 9, "bold"), borderwidth=0, relief="flat",
            padding=(12, 8))
        s.map("Tree.Treeview",
            background=[("selected", PURPLE)],
            foreground=[("selected", TEXT)])
        s.map("Tree.Treeview.Heading",
            background=[("active", CARD2)])

        s.configure("Vertical.TScrollbar",
            troughcolor=CARD, background=BORDER,
            borderwidth=0, relief="flat", arrowcolor=TEXT_MUTED)
        s.map("Vertical.TScrollbar",
            background=[('active', TEXT_SUB), ('!active', BORDER)])

        s.configure("TCombobox",
            background=CARD2, foreground=TEXT,
            fieldbackground=CARD2, selectbackground=PURPLE,
            selectforeground=TEXT,
            font=(FONT, 10), borderwidth=0, relief="flat",
            arrowcolor=TEXT_SUB, padding=(10, 8))
        s.map("TCombobox",
            fieldbackground=[("readonly", CARD2), ("disabled", CARD2)],
            foreground=[("readonly", TEXT), ("disabled", TEXT_SUB)],
            background=[("readonly", CARD2), ("active", CARD2)],
            selectbackground=[("readonly", PURPLE)],
            selectforeground=[("readonly", TEXT)])
        self.root.option_add("*TCombobox*Listbox.background", CARD2)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", PURPLE)
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
        self.root.option_add("*TCombobox*Listbox.font", f"{FONT} 10")

    # ── UI construction ─────────────────────────────────────────
    def _build(self):
        # ── HEADER ───────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(22, 0))

        brand = tk.Frame(hdr, bg=BG)
        brand.pack(side="left")

        dot = tk.Canvas(brand, width=12, height=12, bg=BG, highlightthickness=0)
        dot.create_oval(1, 1, 11, 11, fill=PURPLE, outline="")
        dot.pack(side="left", padx=(0, 9), pady=5)

        tk.Label(brand, text="ExpenseIQ", bg=BG, fg=TEXT,
                 font=(FONT, 19, "bold")).pack(side="left")
        tk.Label(brand, text="  Smart Tracker", bg=BG, fg=TEXT_SUB,
                 font=(FONT, 10)).pack(side="left", pady=3)

        tk.Label(hdr, text=datetime.now().strftime("%A, %B %d  %Y"),
                 bg=BG, fg=TEXT_MUTED, font=(FONT, 9)).pack(side="right", pady=4)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(12, 0))

        # ── STAT CARDS ───────────────────────────────────────────
        stats = tk.Frame(self.root, bg=BG)
        stats.pack(fill="x", padx=28, pady=18)

        self.card_total = StatCard(stats, "Total Spent",    PURPLE)
        self.card_count = StatCard(stats, "Transactions",   GREEN)
        self.card_avg   = StatCard(stats, "Avg per Entry",  AMBER)
        for card in (self.card_total, self.card_count, self.card_avg):
            card.pack(side="left", padx=(0, 12), ipadx=4)

        # ── CONTENT ROW ──────────────────────────────────────────
        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # ── LEFT: form panel ─────────────────────────────────────
        left = tk.Frame(content, bg=CARD, padx=22, pady=22)
        left.pack(side="left", fill="y", padx=(0, 14))

        def flabel(parent, text, size=9, color=TEXT_SUB):
            tk.Label(parent, text=text, bg=parent.cget("bg"),
                     fg=color, font=(FONT, size)).pack(anchor="w")

        flabel(left, "Add Expense",  size=13, color=TEXT)
        flabel(left, "Track every rupee effortlessly", size=9, color=TEXT_MUTED)
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=(10, 18))

        # Amount
        flabel(left, "AMOUNT")
        self.amount_var = tk.StringVar()
        self.amt_entry  = FancyEntry(left, textvariable=self.amount_var,
                                     prefix="Rs", width=16, font_size=12)
        self.amt_entry.pack(fill="x", pady=(4, 14))

        # Category
        flabel(left, "CATEGORY")
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.cat_combo = ttk.Combobox(left, textvariable=self.category_var,
                                       values=CATEGORIES,
                                       state="readonly", width=24)
        self.cat_combo.pack(fill="x", pady=(4, 14))

        # Description
        flabel(left, "DESCRIPTION  (optional)")
        self.desc_var  = tk.StringVar()
        self.desc_entry = FancyEntry(left, textvariable=self.desc_var, width=23)
        self.desc_entry.pack(fill="x", pady=(4, 22))

        # Add button
        self._add_btn = RoundedBtn(left, "+  Add Expense",
                                   command=self._add_expense,
                                   fill=PURPLE, fill_h=PURPLE_H, fill_p=PURPLE_D,
                                   btn_w=226, btn_h=44, font_size=10)
        self._add_btn.pack(pady=(0, 10))

        # Delete button
        self._del_btn = RoundedBtn(left, "Delete Selected",
                                   command=self._delete_selected,
                                   fill=CARD2, fill_h="#2B1F2A", fill_p="#3A1F2A",
                                   fg=RED, btn_w=226, btn_h=38, font_size=9, bold=False)
        self._del_btn.pack()

        # Tab order / keyboard flow
        self.amt_entry.bind("<Return>",  lambda _: self.cat_combo.focus())
        self.cat_combo.bind("<Return>",  lambda _: self.desc_entry.focus())
        self.desc_entry.bind("<Return>", lambda _: self._add_expense())

        # ── RIGHT: table panel ───────────────────────────────────
        right = tk.Frame(content, bg=CARD)
        right.pack(side="left", fill="both", expand=True)

        th = tk.Frame(right, bg=CARD, padx=16, pady=14)
        th.pack(fill="x")
        tk.Label(th, text="Recent Transactions", bg=CARD, fg=TEXT,
                 font=(FONT, 12, "bold")).pack(side="left")
        self._count_lbl = tk.Label(th, text="0 entries", bg=CARD,
                                   fg=TEXT_MUTED, font=(FONT, 9))
        self._count_lbl.pack(side="right", pady=2)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x")

        tree_wrap = tk.Frame(right, bg=CARD)
        tree_wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_wrap,
            columns=("Amount", "Category", "Description", "Date"),
            show="headings", style="Tree.Treeview", selectmode="browse"
        )
        for col, anchor, w in [
            ("Amount",      "center", 105),
            ("Category",    "w",      165),
            ("Description", "w",      225),
            ("Date",        "center", 115),
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=anchor, width=w, minwidth=80)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=CARD)
        self.tree.tag_configure("even", background=ROW_ALT)

        # ── STATUS BAR ───────────────────────────────────────────
        bar = tk.Frame(self.root, bg=CARD2, pady=6)
        bar.pack(fill="x")
        tk.Label(bar,
                 text="  ExpenseIQ v2.0  |  SQLite — data stored locally on your device",
                 bg=CARD2, fg=TEXT_MUTED, font=(FONT, 8)).pack(side="left")

    # ── Actions ─────────────────────────────────────────────────
    def _add_expense(self):
        raw  = self.amount_var.get().strip()
        cat  = self.category_var.get().strip()
        desc = self.desc_var.get().strip()

        if not raw:
            messagebox.showwarning("Missing Field", "Please enter an amount.")
            return
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Amount",
                                   "Amount must be a positive number.")
            return

        row_id   = self.db.add(amount, cat, desc)
        date_str = datetime.now().strftime("%b %d, %Y")
        n        = len(self.tree.get_children())
        tag      = "odd" if n % 2 == 0 else "even"

        iid = self.tree.insert("", 0,
              values=(f"Rs {amount:,.2f}", cat, desc or "—", date_str),
              tags=(tag,))
        self._id_map[iid] = row_id

        self.amount_var.set("")
        self.desc_var.set("")
        self.category_var.set(CATEGORIES[0])
        self.amt_entry.focus()
        self._update_stats()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing Selected",
                                "Click a row first to select it.")
            return
        iid = sel[0]
        if iid in self._id_map:
            self.db.delete(self._id_map.pop(iid))
        self.tree.delete(iid)
        self._restripe()
        self._update_stats()

    def _load_all(self):
        for row in self.db.all():
            rid, amount, cat, desc, ts = row
            try:
                dt       = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%b %d, %Y")
            except Exception:
                date_str = str(ts)[:10]
            n   = len(self.tree.get_children())
            tag = "odd" if n % 2 == 0 else "even"
            iid = self.tree.insert("", "end",
                      values=(f"Rs {amount:,.2f}", cat, desc or "—", date_str),
                      tags=(tag,))
            self._id_map[iid] = rid
        self._update_stats()

    def _restripe(self):
        for i, iid in enumerate(self.tree.get_children()):
            self.tree.item(iid, tags=("odd" if i % 2 == 0 else "even",))

    def _update_stats(self):
        total = self.db.total()
        count = self.db.count()
        avg   = total / count if count else 0
        self.card_total.set(f"Rs {total:,.2f}")
        self.card_count.set(str(count))
        self.card_avg.set(f"Rs {avg:,.2f}")
        self._count_lbl.config(
            text=f"{count} {'entry' if count == 1 else 'entries'}")

    def __del__(self):
        self.db.close()


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = ExpenseTracker(root)
    root.mainloop()
