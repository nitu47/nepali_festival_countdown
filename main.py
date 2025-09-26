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
        root.title("Nepali Festival Countdown (BS)")
        root.geometry("520x300")
        self.festivals = load_festivals()

        # Top frame: dropdown + add/remove buttons
        top = ttk.Frame(root, padding=12)
        top.pack(fill="x")

        self.combo = ttk.Combobox(top, state="readonly")
        self.refresh_combo_values()
        if self.festivals:
            self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.update_display())

        add_btn = ttk.Button(top, text="Add Festival", command=self.show_add_window)
        add_btn.pack(side="left", padx=6)

        rem_btn = ttk.Button(top, text="Remove Selected", command=self.remove_selected)
        rem_btn.pack(side="left")

        # Countdown display
        body = ttk.Frame(root, padding=12)
        body.pack(fill="both", expand=True)

        self.info_label = ttk.Label(body, text="", font=(None, 14))
        self.info_label.pack(pady=12)

        self.count_label = ttk.Label(body, text="", font=("Consolas", 28))
        self.count_label.pack()

        note = "BS support only. Make sure 'nepali-datetime' is installed."
        self.note_label = ttk.Label(root, text=note, font=(None, 9), foreground="gray")
        self.note_label.pack(side="bottom", pady=6)

        self._target_dt = None
        self.update_display()
        self._ticker()

    def refresh_combo_values(self):
        names = [f.get("name", "Unnamed") for f in self.festivals]
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
            self.info_label.config(text=f"{fest['name']} — on {upcoming_ad.strftime('%Y-%m-%d')} (AD)")
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
