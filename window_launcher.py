"""
Window Launcher — Apri cartelle e URL contemporaneamente
Applicazione Python con GUI tkinter dark mode.
Le impostazioni vengono salvate in config.json (default);
è possibile salvare e aprire configurazioni personalizzate tramite il menu File.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import os
import sys
import webbrowser

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False
    DND_FILES = None

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


_BaseApp = TkinterDnD.Tk if _DND_AVAILABLE else tk.Tk


class WindowLauncher(_BaseApp):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.configure(bg=BG_DARK)
        self.minsize(560, 520)
        self.geometry("620x660")
        self.resizable(True, True)

        # Percorso del file di configurazione attualmente aperto
        self._current_config: str = CONFIG_FILE

        # Internal items list: list of dicts {name, path, type}
        # type can be: "folder", "url"
        self.items: list[dict] = []

        self._build_menu()
        self._build_ui()
        self._setup_dnd()
        self._load_config(self._current_config)
        self._set_current_config(self._current_config)  # aggiorna titolo e label header

    # ── Title helper ─────────────────────────────────────────────────────────

    def _update_title(self):
        name = os.path.basename(self._current_config)
        self.title(f"🗂  Window Launcher V.0.7.1  —  {name}")

    # ── Drag & Drop ──────────────────────────────────────────────────────────

    def _setup_dnd(self):
        """Registra la finestra come drop target (richiede tkinterdnd2)."""
        if not _DND_AVAILABLE:
            return
        # Registra sia la finestra principale che il listbox come target
        for widget in (self, self.listbox):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        """Chiamato quando un file viene trascinato nella finestra."""
        raw = event.data.strip()
        # tkinterdnd2 su Windows racchiude path con spazi in {}, gestiamo entrambi i casi
        if raw.startswith("{") and raw.endswith("}"):
            path = raw[1:-1]
        else:
            # Prende solo il primo file se ne vengono droppati più di uno
            path = raw.split("} {")[0].lstrip("{").rstrip("}")

        path = os.path.normpath(path)

        if not path.lower().endswith(".json"):
            messagebox.showwarning(
                "Formato non supportato",
                f"Trascina solo file .json di configurazione.\n\nFile ricevuto:\n{path}"
            )
            return

        self._load_config(path)
        self._set_current_config(path)

    # ── Menu bar ─────────────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self, bg=BG_CARD, fg=FG_TEXT,
                          activebackground=ACCENT, activeforeground="#ffffff",
                          relief="flat", bd=0)

        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=BG_CARD, fg=FG_TEXT,
                            activebackground=ACCENT, activeforeground="#ffffff",
                            relief="flat")

        file_menu.add_command(label="📂  Nuova configurazione",
                              command=self._new_config,
                              accelerator="Ctrl+N")
        file_menu.add_command(label="📁  Apri configurazione…",
                              command=self._open_config,
                              accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="💾  Salva",
                              command=self._save_config_current,
                              accelerator="Ctrl+S")
        file_menu.add_command(label="💾  Salva con nome…",
                              command=self._save_config_as,
                              accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="❌  Esci", command=self.destroy)

        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Keyboard shortcuts
        self.bind_all("<Control-n>", lambda e: self._new_config())
        self.bind_all("<Control-o>", lambda e: self._open_config())
        self.bind_all("<Control-s>", lambda e: self._save_config_current())
        self.bind_all("<Control-S>", lambda e: self._save_config_as())

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
            header, text="Configura cartelle e URL da aprire contemporaneamente",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # Current config label
        self.config_label_var = tk.StringVar()
        tk.Label(
            header, textvariable=self.config_label_var,
            font=FONT_SMALL, bg=BG_DARK, fg=ACCENT, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

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
            text="Nessun elemento configurato.\nUsa i pulsanti ➕ per aggiungere cartelle o URL.",
            font=FONT_SMALL, bg=BG_INPUT, fg=FG_SECONDARY,
            justify="center"
        )

        # ── Side buttons (add / remove) ──────────────────────────────────────
        btn_side = tk.Frame(card, bg=BG_CARD)
        btn_side.pack(fill="x", padx=12, pady=(0, 12))

        self._make_button(btn_side, "📁 Cartella", self._add_folder,
                          SUCCESS, SUCCESS_HOVER).pack(side="left", padx=(0, 6))
        self._make_button(btn_side, "🌐 URL", self._add_url,
                          SUCCESS, SUCCESS_HOVER).pack(side="left", padx=(0, 6))
        self._make_button(btn_side, "🗑 Rimuovi", self._remove_item,
                          ACCENT, ACCENT_HOVER).pack(side="right")

        # ── Bottom action bar ────────────────────────────────────────────────
        action_bar = tk.Frame(self, bg=BG_DARK)
        action_bar.pack(fill="x", padx=24, pady=(8, 20))

        self._make_button(action_bar, "🧹  Pulisci Tutto", self._clear_all,
                          "#ff9f43", "#feca57", width=16).pack(side="left")
        self._make_button(action_bar, "🚀  Lancia Tutto!", self._launch_all,
                          ACCENT, ACCENT_HOVER, width=16).pack(side="right")

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

    _TYPE_ICONS = {"folder": "📁", "url": "🌐"}

    def _refresh_listbox(self):
        self.listbox.delete(0, "end")
        for i, item in enumerate(self.items):
            icon = self._TYPE_ICONS.get(item.get("type", "folder"), "📁")
            display = f"  {icon}  {i+1}.  {item['name']}    —    {item['path']}"
            self.listbox.insert("end", display)

        # Show / hide empty-state label
        if not self.items:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    def _set_current_config(self, path: str):
        """Aggiorna il file di configurazione corrente e le label collegate."""
        self._current_config = path
        self._update_title()
        self.config_label_var.set(f"📄  {path}")

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_double_click(self, event):
        """Apre l'elemento corrispondente alla riga su cui si è fatto doppio click."""
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.items):
            self._launch_item(self.items[idx])

    # ── Add helpers ──────────────────────────────────────────────────────────

    def _add_folder(self):
        path = filedialog.askdirectory(title="Scegli una cartella")
        if not path:
            return
        name = os.path.basename(path) or path
        self.items.append({"name": name, "path": path, "type": "folder"})
        self._refresh_listbox()
        self._save_config_current()
        self.status_var.set(f"Aggiunta cartella: {name}")

    def _add_url(self):
        url = simpledialog.askstring(
            "Aggiungi URL",
            "Inserisci l'URL da aprire:",
            parent=self,
        )
        if not url:
            return
        # Assicura che l'URL abbia un protocollo
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        # Usa il dominio come nome
        name = url.replace("https://", "").replace("http://", "").split("/")[0]
        self.items.append({"name": name, "path": url, "type": "url"})
        self._refresh_listbox()
        self._save_config_current()
        self.status_var.set(f"Aggiunto URL: {name}")

    def _remove_item(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona un elemento dalla lista.")
            return
        idx = sel[0]
        removed = self.items.pop(idx)
        self._refresh_listbox()
        self._save_config_current()
        self.status_var.set(f"Rimosso: {removed['name']}")

    def _clear_all(self):
        if not self.items:
            messagebox.showinfo("Info", "La lista è già vuota.")
            return
        if messagebox.askyesno("Conferma", "Vuoi rimuovere tutti gli elementi dalla lista?"):
            self.items.clear()
            self._refresh_listbox()
            self.status_var.set("Lista svuotata (il file non è stato modificato) ✔")

    # ── Launch logic ─────────────────────────────────────────────────────────

    def _launch_item(self, item):
        """Lancia un singolo elemento in base al tipo."""
        item_type = item.get("type", "folder")
        path = item["path"]
        name = item["name"]

        try:
            if item_type == "url":
                webbrowser.open(path)
                self.status_var.set(f"Aperto URL: {name}")
            else:  # folder
                if os.path.isdir(path):
                    os.startfile(path)
                    self.status_var.set(f"Aperta: {name}")
                else:
                    messagebox.showwarning("Cartella non trovata", f"La cartella non esiste:\n{path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire {name}:\n{e}")

    def _launch_all(self):
        if not self.items:
            messagebox.showinfo("Info", "Nessun elemento da aprire.\nAggiungi almeno un elemento.")
            return

        opened = 0
        for item in self.items:
            self._launch_item(item)
            opened += 1
        self.status_var.set(f"Lanciati {opened} elementi ✔")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_config_current(self):
        """Salva nel file di configurazione attualmente attivo."""
        self._write_config(self._current_config)

    def _save_config_as(self):
        """Chiede un nuovo percorso e salva lì la configurazione corrente."""
        path = filedialog.asksaveasfilename(
            title="Salva configurazione con nome",
            defaultextension=".json",
            filetypes=[("File di configurazione JSON", "*.json"), ("Tutti i file", "*.*")],
            initialdir=APP_DIR,
        )
        if not path:
            return
        path = os.path.normpath(path)  # normalizza slash su Windows
        self._write_config(path)
        self._set_current_config(path)
        self.status_var.set(f"Configurazione salvata come: {os.path.basename(path)}")

    def _open_config(self):
        """Apre un file di configurazione esistente."""
        path = filedialog.askopenfilename(
            title="Apri configurazione",
            defaultextension=".json",
            filetypes=[("File di configurazione JSON", "*.json"), ("Tutti i file", "*.*")],
            initialdir=APP_DIR,
        )
        if not path:
            return
        path = os.path.normpath(path)  # normalizza slash su Windows
        self._load_config(path)
        self._set_current_config(path)

    def _new_config(self):
        """Riparte con una lista vuota senza toccare il file corrente."""
        if self.items:
            if not messagebox.askyesno(
                "Nuova configurazione",
                "Vuoi creare una nuova configurazione vuota?\n"
                "Le modifiche non salvate andranno perse."
            ):
                return
        self.items = []
        self._refresh_listbox()
        self._set_current_config(CONFIG_FILE)
        self.status_var.set("Nuova configurazione creata")

    def _write_config(self, path: str):
        """Scrive self.items nel file indicato."""
        try:
            with open(path, "w", encoding="utf-8") as fp:
                json.dump({"items": self.items}, fp, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare:\n{e}")

    def _load_config(self, path: str):
        path = os.path.normpath(path)  # normalizza slash su Windows
        if not os.path.exists(path):
            self.items = []
            self._refresh_listbox()
            self._set_status(f"File non trovato: {os.path.basename(path)}")
            return
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            # Retrocompatibilità: supporta sia "items" che il vecchio "folders"
            raw = data.get("items", data.get("folders", []))
            # Assicura che ogni elemento abbia il campo 'type'
            for item in raw:
                if "type" not in item:
                    item["type"] = "folder"
            self.items = raw
        except Exception as e:
            messagebox.showerror(
                "Errore lettura configurazione",
                f"Impossibile leggere il file:\n{path}\n\nDettaglio: {e}"
            )
            self.items = []
        self._refresh_listbox()
        self.update_idletasks()  # forza aggiornamento UI
        if self.items:
            self._set_status(f"Caricati {len(self.items)} elementi da {os.path.basename(path)}")
        else:
            self._set_status(f"Configurazione aperta (vuota): {os.path.basename(path)}")

    def _set_status(self, msg: str):
        """Imposta la barra di stato in modo sicuro (può essere chiamato prima di _build_ui)."""
        if hasattr(self, "status_var"):
            self.status_var.set(msg)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = WindowLauncher()
    app.mainloop()
