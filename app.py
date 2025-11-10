from __future__ import annotations

import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk
from tkinter import font as tkfont

LOG_DIRECTORY = Path("logs")
LOG_DIRECTORY.mkdir(exist_ok=True)

SEVERITY_LEVELS = [
    ("Normal", "#0052CC"),
    ("Alert", "#FFAB00"),
    ("Critical", "#DE350B"),
]

SYSTEMS = [
    "Uçuş Kontrol", "Seviyelendirme", "Yakıt Yönetimi", "Haberleşme", "Navigasyon",
    "Radar", "Uçuş Veri Kaydedici", "Motor Kontrol", "Aviyonik Yazılım",
]


class LogStorage:
    """Manage per-day log storage under LOG_DIRECTORY."""

    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory

    def _path_for_date(self, date: datetime) -> Path:
        return self.root_directory / f"{date:%Y-%m-%d}.jsonl"

    def append_entry(self, date: datetime, payload: dict) -> None:
        path = self._path_for_date(date)
        with path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load_entries(self, date: datetime) -> list[dict]:
        path = self._path_for_date(date)
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as fp:
            return [json.loads(line) for line in fp if line.strip()]

    def available_dates(self) -> list[str]:
        dates = []
        for path in sorted(self.root_directory.glob("*.jsonl"), reverse=True):
            dates.append(path.stem)
        if not dates:
            dates.append(datetime.now().strftime("%Y-%m-%d"))
        return dates


class ScheduleCanvas(ttk.Frame):
    """A Jira-inspired daily schedule canvas that places log entries on a timeline."""

    def __init__(self, master: tk.Widget, font_family: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._font_family = font_family
        self._fonts = {
            "header": tkfont.Font(family=font_family, size=12, weight="bold"),
            "time": tkfont.Font(family=font_family, size=9, weight="bold"),
            "card_title": tkfont.Font(family=font_family, size=10, weight="bold"),
            "card_body": tkfont.Font(family=font_family, size=9),
        }
        self.canvas = tk.Canvas(
            self,
            width=620,
            height=420,
            bg="#FFFFFF",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._start_hour = 7
        self._end_hour = 21
        self._row_height = 44
        self._left_margin = 72
        self._top_margin = 48
        self._current_date = ""
        self._entries: list[dict] = []
        self.canvas.bind("<Configure>", self._on_resize)

    def render(self, date_label: str, entries: list[dict]) -> None:
        self._current_date = date_label
        self._entries = list(entries)
        self._redraw()

    def _on_resize(self, _event: tk.Event | None = None) -> None:
        if self._current_date:
            self._redraw()

    def _redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        self._draw_base_grid()
        sorted_entries = sorted(self._entries, key=lambda item: item.get("time", ""))
        for entry in sorted_entries:
            self._draw_entry_card(entry)

    def _draw_base_grid(self) -> None:
        c = self.canvas
        width = int(c.winfo_width()) or 620
        height = int(c.winfo_height()) or 420
        c.create_rectangle(0, 0, width, height, fill="#FFFFFF", outline="")
        c.create_text(
            self._left_margin,
            20,
            text=f"{self._current_date} • Günlük Plan",
            anchor="w",
            fill="#172B4D",
            font=self._fonts["header"],
        )
        c.create_line(0, self._top_margin - 16, width, self._top_margin - 16, fill="#DFE1E6")
        for hour in range(self._start_hour, self._end_hour + 1):
            y = self._top_margin + (hour - self._start_hour) * self._row_height
            c.create_text(
                self._left_margin - 16,
                y,
                text=f"{hour:02d}:00",
                fill="#5E6C84",
                anchor="e",
                font=self._fonts["time"],
            )
            c.create_line(self._left_margin, y, width - 32, y, fill="#EBECF0")

    def _draw_entry_card(self, entry: dict) -> None:
        c = self.canvas
        time_str = entry.get("time", "00:00")
        try:
            hour, minute, *_ = [int(part) for part in time_str.split(":")]
        except (ValueError, TypeError):
            hour, minute = self._start_hour, 0
        row_offset = (hour + minute / 60) - self._start_hour
        row_offset = max(0, min(row_offset, self._end_hour - self._start_hour))
        y = self._top_margin + row_offset * self._row_height
        card_height = 54
        top = y - card_height / 2
        bottom = top + card_height
        left = self._left_margin + 12
        canvas_width = int(c.winfo_width()) or 620
        available_width = max(320, canvas_width - left - 32)
        right = left + available_width
        severity = entry.get("severity", "Normal")
        color = next((color for level, color in SEVERITY_LEVELS if level == severity), "#0052CC")
        c.create_rectangle(left, top, right, bottom, fill="#FFFFFF", outline="#C1C7D0", width=1)
        c.create_rectangle(left, top, left + 6, bottom, fill=color, outline="")
        c.create_text(
            left + 18,
            top + 16,
            text=f"{entry.get('system', '')}",
            anchor="w",
            fill="#172B4D",
            font=self._fonts["card_title"],
        )
        c.create_text(
            right - 12,
            top + 16,
            text=time_str,
            anchor="e",
            fill="#5E6C84",
            font=self._fonts["card_body"],
        )
        c.create_text(
            left + 18,
            top + 34,
            text=entry.get("message", ""),
            anchor="w",
            fill="#42526E",
            font=self._fonts["card_body"],
            width=right - left - 36,
        )


class LogApp(ttk.Frame):
    def __init__(self, master: tk.Tk, storage: LogStorage):
        super().__init__(master, padding=20)
        self.master = master
        self.storage = storage
        self.pack(fill="both", expand=True)
        self._selected_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self._current_entries: list[dict] = []
        self._font_family = self._resolve_font_family()
        self._setup_style()
        self._build_layout()
        self._populate_dates()
        self._load_selected_date()
        self._update_clock()

    def _resolve_font_family(self) -> str:
        preferred = "Segoe UI"
        available = {name.lower(): name for name in tkfont.families(self.master)}
        if preferred.lower() in available:
            return available[preferred.lower()]
        default_font = tkfont.nametofont("TkDefaultFont")
        fallback_family = default_font.cget("family")
        if fallback_family:
            return fallback_family
        if available:
            return next(iter(available.values()))
        return "TkDefaultFont"

    def _setup_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        base_bg = "#F4F5F7"
        surface = "#FFFFFF"
        accent = "#0052CC"
        base_font = tkfont.nametofont("TkDefaultFont")
        base_font.configure(family=self._font_family, size=10)
        self.fonts = {
            "base": base_font,
            "header": tkfont.Font(family=self._font_family, size=20, weight="bold"),
            "subheader": tkfont.Font(family=self._font_family, size=11),
            "button": tkfont.Font(family=self._font_family, size=10, weight="bold"),
            "tree_heading": tkfont.Font(family=self._font_family, size=10, weight="bold"),
            "card_title": tkfont.Font(family=self._font_family, size=12, weight="bold"),
        }
        style.configure("TFrame", background=base_bg)
        style.configure("Toolbar.TFrame", background=surface)
        style.configure("Card.TFrame", background=surface)
        style.configure("TLabel", background=base_bg, foreground="#172B4D", font=self.fonts["base"])
        style.configure("Header.TLabel", font=self.fonts["header"], foreground="#FFFFFF", background="#0747A6")
        style.configure("SubHeader.TLabel", font=self.fonts["subheader"], foreground="#172B4D", background=surface)
        style.configure("CardTitle.TLabel", font=self.fonts["card_title"], foreground="#172B4D", background=surface)
        style.configure("Accent.TButton", background=accent, foreground="#FFFFFF", font=self.fonts["button"], borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#2684FF")])
        style.configure(
            "Treeview",
            background=surface,
            fieldbackground=surface,
            foreground="#172B4D",
            rowheight=32,
            bordercolor="#DFE1E6",
            borderwidth=0,
        )
        style.configure("Treeview.Heading", font=self.fonts["tree_heading"], foreground="#172B4D", background="#F4F5F7")
        style.map("Treeview", background=[("selected", "#DEEBFF")], foreground=[("selected", "#091E42")])
        style.configure("Vertical.TScrollbar", gripcount=0, background=surface, troughcolor="#DFE1E6", bordercolor=surface)

    def _build_layout(self) -> None:
        self.configure(style="TFrame")
        header_frame = tk.Frame(self, bg="#0747A6", padx=24, pady=20)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        title = tk.Label(
            header_frame,
            text="Günlük İzleme • Jira Stil Panel",
            font=self.fonts["header"],
            fg="#FFFFFF",
            bg="#0747A6",
        )
        title.grid(row=0, column=0, sticky="w")
        self.clock_label = tk.Label(
            header_frame,
            text="",
            font=self.fonts["subheader"],
            fg="#DEEBFF",
            bg="#0747A6",
        )
        self.clock_label.grid(row=0, column=1, sticky="e")

        toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=(24, 16))
        toolbar.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        ttk.Label(toolbar, text="Günlük Tarihi", style="SubHeader.TLabel").pack(side="left")
        self.date_combo = ttk.Combobox(toolbar, textvariable=self._selected_date, state="readonly", width=16)
        self.date_combo.pack(side="left", padx=(12, 0))
        self.date_combo.bind("<<ComboboxSelected>>", lambda e: self._load_selected_date())
        ttk.Button(toolbar, text="Bugüne Git", style="Accent.TButton", command=self._goto_today).pack(side="left", padx=(16, 0))

        main_frame = ttk.Frame(self, padding=24)
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        left_column = ttk.Frame(main_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left_column.rowconfigure(0, weight=3)
        left_column.rowconfigure(1, weight=2)

        self._build_schedule_panel(left_column)
        self._build_log_view(left_column)
        self._build_entry_form(main_frame)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _build_schedule_panel(self, parent: ttk.Frame) -> None:
        schedule_card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        schedule_card.grid(row=0, column=0, sticky="nsew", pady=(0, 16))
        ttk.Label(schedule_card, text="Günlük Zaman Çizelgesi", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))
        self.schedule_canvas = ScheduleCanvas(schedule_card, self._font_family)
        self.schedule_canvas.pack(fill="both", expand=True)

    def _build_log_view(self, parent: ttk.Frame) -> None:
        view_card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        view_card.grid(row=1, column=0, sticky="nsew")
        ttk.Label(view_card, text="Log Tablosu", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))
        columns = ("time", "system", "severity", "message")
        self.tree = ttk.Treeview(view_card, columns=columns, show="headings")
        self.tree.heading("time", text="Saat")
        self.tree.heading("system", text="Sistem")
        self.tree.heading("severity", text="Durum")
        self.tree.heading("message", text="Açıklama")
        self.tree.column("time", width=80, anchor="center")
        self.tree.column("system", width=140)
        self.tree.column("severity", width=100, anchor="center")
        self.tree.column("message", width=360)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(view_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _build_entry_form(self, parent: ttk.Frame) -> None:
        form_card = ttk.Frame(parent, style="Card.TFrame", padding=24)
        form_card.grid(row=0, column=1, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        ttk.Label(form_card, text="Yeni Log Girişi", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(form_card, text="Sistem", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", pady=(16, 4))
        self.system_combo = ttk.Combobox(form_card, values=SYSTEMS, state="readonly")
        self.system_combo.grid(row=2, column=0, sticky="ew")
        self.system_combo.set(SYSTEMS[0])

        ttk.Label(form_card, text="Durum Seviyesi", style="SubHeader.TLabel").grid(row=3, column=0, sticky="w", pady=(16, 4))
        self.severity_combo = ttk.Combobox(form_card, values=[level for level, _ in SEVERITY_LEVELS], state="readonly")
        self.severity_combo.grid(row=4, column=0, sticky="ew")
        self.severity_combo.set(SEVERITY_LEVELS[0][0])

        ttk.Label(form_card, text="Log Açıklaması", style="SubHeader.TLabel").grid(row=5, column=0, sticky="w", pady=(16, 4))
        self.message_text = tk.Text(
            form_card,
            height=10,
            wrap="word",
            background="#FFFFFF",
            foreground="#172B4D",
            insertbackground="#172B4D",
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            font=self.fonts["base"],
        )
        self.message_text.grid(row=6, column=0, sticky="nsew")

        form_card.columnconfigure(0, weight=1)
        form_card.rowconfigure(6, weight=1)

        ttk.Button(form_card, text="Kaydı Ekle", style="Accent.TButton", command=self._save_entry).grid(
            row=7, column=0, sticky="ew", pady=(20, 0))

    def _populate_dates(self) -> None:
        dates = self.storage.available_dates()
        self.date_combo["values"] = dates
        if self._selected_date.get() not in dates:
            self._selected_date.set(dates[0])

    def _load_selected_date(self) -> None:
        date_str = self._selected_date.get()
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Hatalı Tarih", "Geçerli bir tarih seçin.")
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        entries = self.storage.load_entries(date)
        self._current_entries = entries.copy()
        for entry in entries:
            self._insert_tree_item(entry)
        human_date = date.strftime("%d %B %Y")
        self.schedule_canvas.render(human_date, self._current_entries)

    def _insert_tree_item(self, entry: dict) -> None:
        severity = entry.get("severity", "")
        color = next((color for level, color in SEVERITY_LEVELS if level == severity), "#0052CC")
        values = (entry.get("time"), entry.get("system"), severity, entry.get("message"))
        item_id = self.tree.insert("", "end", values=values)
        self.tree.tag_configure(severity, foreground=color)
        self.tree.item(item_id, tags=(severity,))

    def _save_entry(self) -> None:
        message = self.message_text.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("Eksik Bilgi", "Log açıklaması girin.")
            return
        system = self.system_combo.get()
        severity = self.severity_combo.get()
        now = datetime.now()
        entry = {
            "time": now.strftime("%H:%M:%S"),
            "system": system,
            "severity": severity,
            "message": message,
        }
        self.storage.append_entry(now, entry)
        if self._selected_date.get() == now.strftime("%Y-%m-%d"):
            self._insert_tree_item(entry)
            self._current_entries.append(entry)
            self.schedule_canvas.render(now.strftime("%d %B %Y"), self._current_entries)
        self.message_text.delete("1.0", "end")
        self._populate_dates()
        self._selected_date.set(now.strftime("%Y-%m-%d"))
        self.date_combo.event_generate("<<ComboboxSelected>>")

    def _goto_today(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        self._selected_date.set(today)
        self._populate_dates()
        self._load_selected_date()

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%d %B %Y • %H:%M:%S")
        self.clock_label.configure(text=now)
        self.after(1000, self._update_clock)


def main() -> None:
    root = tk.Tk()
    root.title("Jira Esintili Günlük İzleme")
    root.geometry("1100x640")
    root.configure(bg="#F4F5F7")
    storage = LogStorage(LOG_DIRECTORY)
    LogApp(root, storage)
    root.mainloop()


if __name__ == "__main__":
    main()
