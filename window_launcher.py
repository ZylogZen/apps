"""
Window Launcher — Apri più cartelle contemporaneamente
Applicazione Python con GUI tkinter dark mode.
Le impostazioni vengono salvate in config.json.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys

# ── Paths ────────────────────────────────────────────────────────────────────
APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# ── Colors (dark mode palette) ───────────────────────────────────────────────
BG_DARK      = "#1a1a2e"
BG_CARD      = "#16213e"
BG_INPUT     = "#0f3460"
FG_TEXT       = "#e0e0e0"
FG_SECONDARY  = "#a0a0b0"
ACCENT        = "#e94560"
ACCENT_HOVER  = "#ff6b81"
SUCCESS       = "#00d2d3"
SUCCESS_HOVER = "#48dbfb"
BORDER        = "#2a2a4a"
HIGHLIGHT_BG  = "#0f3460"

# ── Fonts ────────────────────────────────────────────────────────────────────
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_NORMAL   = ("Segoe UI", 11)
FONT_BUTTON   = ("Segoe UI", 11, "bold")
FONT_SMALL    = ("Segoe UI", 9)


class WindowLauncher(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("🗂  Window Launcher V.0.5 by d.a.")
        self.configure(bg=BG_DARK)
        self.minsize(560, 520)
        self.geometry("600x600")
        self.resizable(True, True)

        # Internal folder list: list of dicts {name, path}
        self.folders: list[dict] = []

        self._build_ui()
        self._load_config()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x", padx=24, pady=(20, 4))

        tk.Label(
            header, text="🗂  Window Launcher", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_TEXT
        ).pack(anchor="w")
        tk.Label(
            header, text="Configura le cartelle da aprire contemporaneamente",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)

        # ── Listbox card ─────────────────────────────────────────────────────
        card = tk.Frame(self, bg=BG_CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        # Listbox + scrollbar
        list_frame = tk.Frame(card, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True, padx=12, pady=12)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            bg=BG_INPUT, fg=FG_TEXT,
            selectbackground=ACCENT,
            selectforeground="#ffffff",
            font=FONT_NORMAL,
            bd=0,
            highlightthickness=0,
            relief="flat",
            activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        scrollbar.config(command=self.listbox.yview)

        # Empty-state label (shown when list is empty)
        self.empty_label = tk.Label(
            list_frame,
            text="Nessuna cartella configurata.\nClicca  ➕ Aggiungi Cartella  per iniziare.",
            font=FONT_SMALL, bg=BG_INPUT, fg=FG_SECONDARY,
            justify="center"
        )

        # ── Side buttons (add / remove) ──────────────────────────────────────
        btn_side = tk.Frame(card, bg=BG_CARD)
        btn_side.pack(fill="x", padx=12, pady=(0, 12))

        self._make_button(btn_side, "➕  Aggiungi Cartella", self._add_folder,
                          SUCCESS, SUCCESS_HOVER).pack(side="left", padx=(0, 8))
        self._make_button(btn_side, "🗑  Rimuovi Selezionata", self._remove_folder,
                          ACCENT, ACCENT_HOVER).pack(side="left")

        # ── Bottom action bar ────────────────────────────────────────────────
        action_bar = tk.Frame(self, bg=BG_DARK)
        action_bar.pack(fill="x", padx=24, pady=(8, 20))

        self._make_button(action_bar, "💾  Salva Impostazioni", self._save_config,
                          SUCCESS, SUCCESS_HOVER, width=20).pack(side="left")
        self._make_button(action_bar, "🚀  Lancia Tutto!", self._launch_all,
                          ACCENT, ACCENT_HOVER, width=20).pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        tk.Label(
            self, textvariable=self.status_var, font=FONT_SMALL,
            bg=BG_DARK, fg=FG_SECONDARY, anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

    # ── Button helper ────────────────────────────────────────────────────────

    @staticmethod
    def _make_button(parent, text, command, bg, hover_bg, width=None):
        btn = tk.Button(
            parent, text=text, command=command,
            font=FONT_BUTTON, bg=bg, fg="#ffffff",
            activebackground=hover_bg, activeforeground="#ffffff",
            bd=0, relief="flat", cursor="hand2",
            padx=14, pady=6,
        )
        if width:
            btn.config(width=width)

        def on_enter(_):
            btn.config(bg=hover_bg)

        def on_leave(_):
            btn.config(bg=bg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ── Listbox helpers ──────────────────────────────────────────────────────

    def _refresh_listbox(self):
        self.listbox.delete(0, "end")
        for i, f in enumerate(self.folders):
            display = f"  {i+1}.  {f['name']}    —    {f['path']}"
            self.listbox.insert("end", display)

        # Show / hide empty-state label
        if not self.folders:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_double_click(self, event):
        """Apre la cartella corrispondente alla riga su cui si è fatto doppio click."""
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.folders):
            path = self.folders[idx]["path"]
            if os.path.isdir(path):
                os.startfile(path)
                self.status_var.set(f"Aperta: {self.folders[idx]['name']}")
            else:
                messagebox.showwarning(
                    "Cartella non trovata",
                    f"La cartella non esiste:\n{path}"
                )


    def _add_folder(self):
        path = filedialog.askdirectory(title="Scegli una cartella")
        if not path:
            return
        name = os.path.basename(path) or path
        self.folders.append({"name": name, "path": path})
        self._refresh_listbox()
        self.status_var.set(f"Aggiunta: {name}")

    def _remove_folder(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona una cartella dalla lista.")
            return
        idx = sel[0]
        removed = self.folders.pop(idx)
        self._refresh_listbox()
        self.status_var.set(f"Rimossa: {removed['name']}")

    def _launch_all(self):
        if not self.folders:
            messagebox.showinfo("Info", "Nessuna cartella da aprire.\nAggiungi almeno una cartella.")
            return

        opened = 0
        for f in self.folders:
            path = f["path"]
            if os.path.isdir(path):
                os.startfile(path)
                opened += 1
            else:
                messagebox.showwarning(
                    "Cartella non trovata",
                    f"La cartella non esiste:\n{path}"
                )
        self.status_var.set(f"Aperte {opened} cartelle ✔")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as fp:
                json.dump({"folders": self.folders}, fp, indent=2, ensure_ascii=False)
            self.status_var.set(f"Impostazioni salvate in {CONFIG_FILE} ✔")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare:\n{e}")

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self._refresh_listbox()
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            self.folders = data.get("folders", [])
        except Exception:
            self.folders = []
        self._refresh_listbox()
        if self.folders:
            self.status_var.set(f"Caricate {len(self.folders)} cartelle dalla configurazione")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = WindowLauncher()
    app.mainloop()
