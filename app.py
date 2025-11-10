from __future__ import annotations

import json
import math
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk
from tkinter import font as tkfont

LOG_DIRECTORY = Path("logs")
LOG_DIRECTORY.mkdir(exist_ok=True)

SEVERITY_LEVELS = [
    ("Normal", "#19D3FF"),
    ("Alert", "#FFC857"),
    ("Critical", "#FF6B6B"),
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


class AvionicsCanvas(ttk.Frame):
    """Animated avionics-style canvas with radar sweep and widgets."""

    def __init__(self, master: tk.Widget, font_family: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.canvas = tk.Canvas(self, width=320, height=320, bg="#0B172A", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._radar_angle = 0
        self._font_family = font_family
        self._fonts = {
            "title": tkfont.Font(family=font_family, size=12, weight="bold"),
            "subtitle": tkfont.Font(family=font_family, size=10),
            "label": tkfont.Font(family=font_family, size=10),
        }
        self._draw_static_elements()
        self._animate()

    def _draw_static_elements(self) -> None:
        c = self.canvas
        c.create_oval(40, 40, 280, 280, outline="#19D3FF", width=3)
        for r in range(60, 140, 20):
            c.create_oval(160 - r, 160 - r, 160 + r, 160 + r, outline="#12304D", dash=(2, 4))
        c.create_text(160, 24, text="AVİYONİK GÖSTERGE", fill="#FFFFFF", font=self._fonts["title"])
        c.create_text(160, 296, text="Radyo Navigasyon", fill="#19D3FF", font=self._fonts["subtitle"])
        # HUD horizon
        c.create_rectangle(60, 150, 260, 170, outline="", fill="#1F2A44")
        c.create_line(60, 160, 260, 160, fill="#19D3FF", width=2)
        c.create_text(70, 140, text="IAS", fill="#98FAEC", anchor="w", font=self._fonts["label"])
        c.create_text(250, 140, text="ALT", fill="#FFC857", anchor="e", font=self._fonts["label"])

    def _animate(self) -> None:
        c = self.canvas
        c.delete("radar")
        length = 120
        angle_rad = math.radians(self._radar_angle)
        x = 160 + length * math.sin(angle_rad)
        y = 160 - length * math.cos(angle_rad)
        c.create_line(160, 160, x, y, fill="#19D3FF", width=2, tags="radar")
        self._radar_angle = (self._radar_angle + 3) % 360
        self.after(60, self._animate)


class LogApp(ttk.Frame):
    def __init__(self, master: tk.Tk, storage: LogStorage):
        super().__init__(master, padding=20)
        self.master = master
        self.storage = storage
        self.pack(fill="both", expand=True)
        self._selected_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
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
        base_bg = "#081426"
        accent = "#19D3FF"
        base_font = tkfont.nametofont("TkDefaultFont")
        base_font.configure(family=self._font_family, size=10)
        self.fonts = {
            "base": base_font,
            "header": tkfont.Font(family=self._font_family, size=18, weight="bold"),
            "subheader": tkfont.Font(family=self._font_family, size=11),
            "button": tkfont.Font(family=self._font_family, size=10, weight="bold"),
            "tree_heading": tkfont.Font(family=self._font_family, size=10, weight="bold"),
        }
        style.configure("TFrame", background=base_bg)
        style.configure("TLabel", background=base_bg, foreground="#E1ECF7", font=self.fonts["base"])
        style.configure("Header.TLabel", font=self.fonts["header"], foreground=accent)
        style.configure("SubHeader.TLabel", font=self.fonts["subheader"])
        style.configure("Accent.TButton", background=accent, foreground="#081426", font=self.fonts["button"])
        style.map("Accent.TButton", background=[("active", "#42E6FF")])
        style.configure("Treeview", background="#0F1F38", fieldbackground="#0F1F38", foreground="#E8F1FF", rowheight=28)
        style.configure("Treeview.Heading", font=self.fonts["tree_heading"], foreground=accent)
        style.map("Treeview", background=[("selected", "#1F3B64")])

    def _build_layout(self) -> None:
        header = ttk.Label(self, text="Aviyonik Günlük İzleme Paneli", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w")

        self.clock_label = ttk.Label(self, text="", style="SubHeader.TLabel")
        self.clock_label.grid(row=0, column=1, sticky="e")

        top_frame = ttk.Frame(self)
        top_frame.grid(row=1, column=0, columnspan=2, pady=(12, 18), sticky="nsew")
        top_frame.columnconfigure(0, weight=3)
        top_frame.columnconfigure(1, weight=2)

        self._build_log_view(top_frame)
        self._build_entry_form(top_frame)
        self._build_avionics_panel(top_frame)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _build_log_view(self, parent: ttk.Frame) -> None:
        view_frame = ttk.Frame(parent)
        view_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 16))
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=2)

        selector_frame = ttk.Frame(view_frame)
        selector_frame.pack(fill="x", pady=(0, 12))
        ttk.Label(selector_frame, text="Günlük Tarihi").pack(side="left")
        self.date_combo = ttk.Combobox(selector_frame, textvariable=self._selected_date, state="readonly")
        self.date_combo.pack(side="left", padx=(8, 0))
        self.date_combo.bind("<<ComboboxSelected>>", lambda e: self._load_selected_date())

        columns = ("time", "system", "severity", "message")
        self.tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        self.tree.heading("time", text="Saat")
        self.tree.heading("system", text="Sistem")
        self.tree.heading("severity", text="Durum")
        self.tree.heading("message", text="Açıklama")
        self.tree.column("time", width=90, anchor="center")
        self.tree.column("system", width=140)
        self.tree.column("severity", width=100, anchor="center")
        self.tree.column("message", width=380)
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(view_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _build_entry_form(self, parent: ttk.Frame) -> None:
        form_frame = ttk.Frame(parent)
        form_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 12))

        ttk.Label(form_frame, text="Sistem").grid(row=0, column=0, sticky="w")
        self.system_combo = ttk.Combobox(form_frame, values=SYSTEMS, state="readonly")
        self.system_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.system_combo.set(SYSTEMS[0])

        ttk.Label(form_frame, text="Durum Seviyesi").grid(row=2, column=0, sticky="w")
        self.severity_combo = ttk.Combobox(form_frame, values=[level for level, _ in SEVERITY_LEVELS], state="readonly")
        self.severity_combo.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.severity_combo.set(SEVERITY_LEVELS[0][0])

        ttk.Label(form_frame, text="Log Açıklaması").grid(row=4, column=0, sticky="w")
        self.message_text = tk.Text(form_frame, height=6, wrap="word", background="#0F1F38", foreground="#E1ECF7",
                                    insertbackground="#E1ECF7", relief="flat", font=self.fonts["base"])
        self.message_text.grid(row=5, column=0, sticky="nsew", pady=(0, 12))

        form_frame.columnconfigure(0, weight=1)
        form_frame.rowconfigure(5, weight=1)

        ttk.Button(form_frame, text="Kaydı Ekle", style="Accent.TButton", command=self._save_entry).grid(
            row=6, column=0, sticky="ew")

    def _build_avionics_panel(self, parent: ttk.Frame) -> None:
        avionics_frame = ttk.Frame(parent)
        avionics_frame.grid(row=1, column=1, sticky="nsew")
        ttk.Label(avionics_frame, text="Aviyonik Durum Görselleştirmesi", style="SubHeader.TLabel").pack(anchor="w")
        AvionicsCanvas(avionics_frame, self._font_family).pack(fill="both", expand=True, pady=(8, 0))

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
        for entry in entries:
            self._insert_tree_item(entry)

    def _insert_tree_item(self, entry: dict) -> None:
        severity = entry.get("severity", "")
        color = next((color for level, color in SEVERITY_LEVELS if level == severity), "#19D3FF")
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
        self.message_text.delete("1.0", "end")
        self._populate_dates()
        self._selected_date.set(now.strftime("%Y-%m-%d"))
        self.date_combo.event_generate("<<ComboboxSelected>>")

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%d %B %Y • %H:%M:%S")
        self.clock_label.configure(text=now)
        self.after(1000, self._update_clock)


def main() -> None:
    root = tk.Tk()
    root.title("Aviyonik Günlük İzleme")
    root.geometry("1100x640")
    root.configure(bg="#081426")
    storage = LogStorage(LOG_DIRECTORY)
    LogApp(root, storage)
    root.mainloop()


if __name__ == "__main__":
    main()
