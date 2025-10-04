import json
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox

# Nepali datetime library is required
try:
    from nepali_datetime import date as nep_date
    HAS_NEPALI = True
except ImportError:
    HAS_NEPALI = False

FESTIVAL_FILE = "festivals.json"

# --- Festival Data Handling --------------------------------------------

def load_festivals():
    try:
        with open(FESTIVAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_festivals(festivals):
    with open(FESTIVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(festivals, f, indent=2, ensure_ascii=False)

def next_occurrence(festival: dict) -> date:
    """Return next occurrence date in AD for a BS festival."""
    if not HAS_NEPALI:
        raise ValueError("Nepali date support requires 'nepali-datetime' library.")

    bs_month, bs_day = festival["month"], festival["day"]
    current_bs_year = nep_date.today().year
    candidate_ad = nep_date(current_bs_year, bs_month, bs_day).to_datetime_date()
    if candidate_ad < date.today():
        candidate_ad = nep_date(current_bs_year + 1, bs_month, bs_day).to_datetime_date()
    return candidate_ad

# --- Countdown Utility -------------------------------------------------

def get_time_delta_str(target_dt: datetime) -> str:
    now = datetime.now()
    delta = target_dt - now
    if delta.total_seconds() < 0:
        return "Already passed"
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}d {hours:02}h {minutes:02}m {seconds:02}s"

# --- GUI ----------------------------------------------------------------

class App:
    def __init__(self, root):
        self.root = root
        root.title("🎊 Nepali Festival Countdown (BS)")
        root.geometry("540x380")

        # 🌸 Main background color
        root.configure(bg="#fff3e6")  # warm cream color

        # 🎨 Style setup
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#fff3e6")
        style.configure("TLabel", background="#fff3e6", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.map("TButton",
                  background=[("active", "#ff5722")],
                  foreground=[("active", "white")])

        style.configure("TCombobox", padding=4)

        self.festivals = load_festivals()

        # --- Gradient Banner ---
        banner_height = 70
        banner = tk.Canvas(root, height=banner_height, highlightthickness=0, bd=0)
        banner.pack(fill="x")

        self._draw_gradient(banner, "#ff9800", "#e53935")  # orange to red
        banner.create_text(270, banner_height // 2, text="🎉 Nepali Festivals 🎉",
                           font=("Segoe UI", 18, "bold"), fill="white")

        # --- Top frame ---
        top = ttk.Frame(root, padding=12, style="TFrame")
        top.pack(fill="x")

        self.combo = ttk.Combobox(top, state="readonly", style="TCombobox")
        self.refresh_combo_values()
        if self.festivals:
            self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.update_display())

        add_btn = ttk.Button(top, text="➕ Add", command=self.show_add_window, style="TButton")
        add_btn.pack(side="left", padx=6)

        rem_btn = ttk.Button(top, text="🗑 Remove", command=self.remove_selected, style="TButton")
        rem_btn.pack(side="left")

        # --- Body frame ---
        body = ttk.Frame(root, padding=12, style="TFrame")
        body.pack(fill="both", expand=True)

        # Label with icon + festival name
        self.info_label = ttk.Label(body, text="", font=("Segoe UI", 14, "bold"), foreground="#333")
        self.info_label.pack(pady=12)

        # Countdown
        self.count_label = ttk.Label(body, text="", font=("Consolas", 30, "bold"), foreground="#e53935")
        self.count_label.pack()

        note = "BS support only. Make sure 'nepali-datetime' is installed."
        self.note_label = ttk.Label(root, text=note, font=("Segoe UI", 9),
                                    foreground="gray", background="#fff3e6")
        self.note_label.pack(side="bottom", pady=6)

        self._target_dt = None
        self.update_display()
        self._ticker()

    # --- Draw gradient banner ---
    def _draw_gradient(self, canvas, color1, color2):
        """Draw vertical gradient on canvas."""
        width = 540
        height = int(canvas["height"])
        limit = height
        (r1, g1, b1) = self.root.winfo_rgb(color1)
        (r2, g2, b2) = self.root.winfo_rgb(color2)

        r_ratio = (r2 - r1) / limit
        g_ratio = (g2 - g1) / limit
        b_ratio = (b2 - b1) / limit

        for i in range(limit):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f"#{nr//256:02x}{ng//256:02x}{nb//256:02x}"
            canvas.create_line(0, i, width, i, fill=color)

    def refresh_combo_values(self):
        # Add emoji icons next to festival names 🌸🪔
        names = [f"🌸 {f.get('name', 'Unnamed')}" for f in self.festivals]
        if not names:
            names = ["(no festivals)"]
        self.combo["values"] = names

    def update_display(self):
        idx = self.combo.current()
        if idx < 0 or idx >= len(self.festivals):
            self.info_label.config(text="No festival selected")
            self.count_label.config(text="---")
            self._target_dt = None
            return
        fest = self.festivals[idx]
        try:
            upcoming_ad = next_occurrence(fest)
            # Show icon 🪔 for main label
            self.info_label.config(
                text=f"🪔 {fest['name']} — {upcoming_ad.strftime('%Y-%m-%d')} (AD)"
            )
            self._target_dt = datetime.combine(upcoming_ad, datetime.min.time())
        except Exception as e:
            self.info_label.config(text=f"Error: {e}")
            self.count_label.config(text="---")
            self._target_dt = None

    def _ticker(self):
        if self._target_dt:
            self.count_label.config(text=get_time_delta_str(self._target_dt))
        self.root.after(1000, self._ticker)

    def show_add_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add BS Festival")
        win.configure(bg="#fff3e6")

        ttk.Label(win, text="Name:").grid(row=0, column=0, sticky="e")
        name_entry = ttk.Entry(win)
        name_entry.grid(row=0, column=1)

        ttk.Label(win, text="Month (1-12):").grid(row=1, column=0, sticky="e")
        month_entry = ttk.Entry(win)
        month_entry.grid(row=1, column=1)

        ttk.Label(win, text="Day (1-31):").grid(row=2, column=0, sticky="e")
        day_entry = ttk.Entry(win)
        day_entry.grid(row=2, column=1)

        def save_new():
            try:
                fest = {
                    "name": name_entry.get().strip() or "Unnamed",
                    "month": int(month_entry.get()),
                    "day": int(day_entry.get())
                }
                self.festivals.append(fest)
                save_festivals(self.festivals)
                self.refresh_combo_values()
                self.combo.current(len(self.festivals) - 1)
                self.update_display()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(win, text="Save", command=save_new).grid(row=3, column=0, columnspan=2, pady=6)

    def remove_selected(self):
        idx = self.combo.current()
        if 0 <= idx < len(self.festivals):
            del self.festivals[idx]
            save_festivals(self.festivals)
            self.refresh_combo_values()
            if self.festivals:
                self.combo.current(0)
            self.update_display()

# --- Run ----------------------------------------------------------------

if __name__ == "__main__":
    if not HAS_NEPALI:
        print("Error: 'nepali-datetime' library is required for BS support.")
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
