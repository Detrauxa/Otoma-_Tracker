# main.py (version corrigée pour .json en .py et en .exe)
import customtkinter as ctk
import json
import os
import sys
from pathlib import Path

# ----------------- CONFIG -----------------
APP_NAME = "Otomaï Tracker"
SAVE_DIR = Path(os.path.expanduser("~")) / ".otomai_tracker"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SAVE_FILE = SAVE_DIR / "progress.json"
SETTINGS_FILE = SAVE_DIR / "settings.json"

# ----------------- resource helper -----------------
def resource_path(relative_path: str) -> Path:
    """
    Retourne le Path vers `relative_path` selon l'environnement :
    - si l'application est "frozen" (PyInstaller) : 
        * cherche d'abord un fichier externe à côté de l'exécutable (pratique pour éditer monsters.json)
        * sinon, si le fichier est bundlé dans l'EXE, retourne le chemin dans _MEIPASS
    - sinon (mode .py) : retourne le fichier à côté du script
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        external = exe_dir / relative_path
        if external.exists():
            return external
        try:
            meipass_dir = Path(sys._MEIPASS)
            candidate = meipass_dir / relative_path
            return candidate
        except Exception:
            return external
    else:
        return Path(__file__).parent / relative_path

# monsters.json should live next to main.py or next to the exe
MONSTERS_JSON = resource_path("monsters.json")

# Colors
GREEN_HEX = "#2ecc71"
TRANSPARENT = "transparent"

# ----------------- Helpers: load/save -----------------
def load_json_file(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_json_file(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------- Load settings / progress / monsters -----------------
def load_settings():
    s = load_json_file(SETTINGS_FILE)
    if not isinstance(s, dict):
        s = {}
    # defaults
    s.setdefault("theme", "dark")
    s.setdefault("categories_open", {})
    return s

def load_progress(all_names):
    p = load_json_file(SAVE_FILE)
    if not isinstance(p, dict):
        p = {}
    for name in all_names:
        p.setdefault(name, False)
    return p

def load_monsters():
    data = load_json_file(MONSTERS_JSON)
    if not isinstance(data, dict):
        return {"Monstres": [], "Boss": [], "Archimonstres": []}
    for k in ["Monstres", "Boss", "Archimonstres"]:
        data.setdefault(k, [])
    return data

# ----------------- UI App -----------------
class OtomaiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("780x900")

        # load data
        self.monsters = load_monsters()
        all_names = [n for cat in self.monsters.values() for n in cat]
        self.settings = load_settings()
        self.progress = load_progress(all_names)

        # theme
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        # container for dynamic widgets
        self.category_frames = {}

        # top UI
        self._build_top()

        # scrollable content
        self.content_frame = ctk.CTkScrollableFrame(self, width=740, height=720)
        self.content_frame.pack(padx=20, pady=(5,20), fill="both", expand=True)

        # build categories
        self._build_categories()

        # apply initial state of categories
        self._restore_categories_state()

    # ---------- top bar ----------
    def _build_top(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,0))

        title = ctk.CTkLabel(top, text="📘 Suivi des Captures Otomaï", font=("Segoe UI", 22, "bold"))
        title.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(top, text="", command=self._toggle_theme)
        self.theme_switch.pack(side="right", padx=(10,0))
        self.theme_label = ctk.CTkLabel(top, text="🌙", width=30)
        self.theme_label.pack(side="right")

        if self.settings.get("theme") == "dark":
            self.theme_switch.select()
            self.theme_label.configure(text="🌙")
        else:
            self.theme_switch.deselect()
            self.theme_label.configure(text="☀️")

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(10,5))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=420, placeholder_text="🔎 Rechercher…")
        self.search_entry.pack(side="left", padx=(0,10))
        self.search_var.trace_add("write", self._on_search_change)

        clear_btn = ctk.CTkButton(search_frame, text="❌", width=40, command=self._clear_search)
        clear_btn.pack(side="left")

        self.progress_label = ctk.CTkLabel(search_frame, text=self._progress_text())
        self.progress_label.pack(side="right")

    # ---------- category builder ----------
    def _build_categories(self):
        for cat_name, monster_list in self.monsters.items():
            self._build_category_card(cat_name, monster_list)

    def _build_category_card(self, cat_name, monster_list):
        card = ctk.CTkFrame(self.content_frame, corner_radius=12)
        card.pack(fill="x", padx=10, pady=10)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(6,6))

        arrow = ctk.CTkLabel(header, text="▼", width=20, anchor="w", font=("Segoe UI", 18))
        arrow.pack(side="left")

        title_btn = ctk.CTkButton(header, text=f" {cat_name}", fg_color="transparent",
                                  hover_color="#2a2a2a", command=lambda c=cat_name: self._toggle_category(c),
                                  anchor="w")
        title_btn.pack(side="left", padx=(6,10))

        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.pack(side="right")
        ctk.CTkButton(btns, text="✔ Tout cocher", width=140,
                      command=lambda lst=monster_list: self._check_all(lst)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="✖ Tout décocher", width=140,
                      command=lambda lst=monster_list: self._uncheck_all(lst)).pack(side="left", padx=6)

        rows_container = ctk.CTkFrame(card, fg_color="transparent")
        rows_container.pack(fill="x", padx=10, pady=(0,8))

        rows = []
        for name in monster_list:
            row = ctk.CTkFrame(rows_container, corner_radius=8)
            row.pack(fill="x", pady=3)

            label = ctk.CTkLabel(row, text=name, anchor="w")
            label.pack(side="left", padx=8, pady=6, fill="x", expand=True)

            if self.progress.get(name):
                label.configure(fg_color=GREEN_HEX)
            else:
                label.configure(fg_color=TRANSPARENT)

            btn = ctk.CTkButton(row, text="Capturé ✔", width=110,
                                command=lambda n=name, l=label: self._toggle_captured(n, l))
            btn.pack(side="right", padx=8)

            rows.append((name, row, label))

        self.category_frames[cat_name] = {
            "card": card,
            "header": header,
            "arrow": arrow,
            "rows_container": rows_container,
            "rows": rows,
            "open": True
        }

    # ---------- toggle category ----------
    def _toggle_category(self, cat_name):
        info = self.category_frames[cat_name]
        is_open = info["open"]

        if is_open:
            info["rows_container"].pack_forget()
            info["arrow"].configure(text="►")
            info["open"] = False
        else:
            info["rows_container"].pack(fill="x", padx=10, pady=(0, 8))
            info["arrow"].configure(text="▼")
            info["open"] = True

        self.settings.setdefault("categories_open", {})[cat_name] = info["open"]
        save_json_file(SETTINGS_FILE, self.settings)

    def _restore_categories_state(self):
        saved = self.settings.get("categories_open", {})
        for cat_name, info in self.category_frames.items():
            should_open = saved.get(cat_name, True)
            if not should_open:
                info["rows_container"].pack_forget()
                info["arrow"].configure(text="►")
                info["open"] = False
            else:
                info["rows_container"].pack(fill="x", padx=10, pady=(0, 8))
                info["arrow"].configure(text="▼")
                info["open"] = True

    # ---------- check / uncheck ----------
    def _check_all(self, names):
        for name in names:
            self.progress[name] = True
            row_info = self._find_row(name)
            if row_info:
                _, _, label = row_info
                label.configure(fg_color=GREEN_HEX)
        save_json_file(SAVE_FILE, self.progress)
        self._update_progress_label()

    def _uncheck_all(self, names):
        for name in names:
            self.progress[name] = False
            row_info = self._find_row(name)
            if row_info:
                _, _, label = row_info
                label.configure(fg_color=TRANSPARENT)
        save_json_file(SAVE_FILE, self.progress)
        self._update_progress_label()

    def _toggle_captured(self, name, label_widget):
        self.progress[name] = not self.progress.get(name, False)
        if self.progress[name]:
            label_widget.configure(fg_color=GREEN_HEX)
        else:
            label_widget.configure(fg_color=TRANSPARENT)
        save_json_file(SAVE_FILE, self.progress)
        self._update_progress_label()

    def _find_row(self, name):
        for cat, info in self.category_frames.items():
            for n, row, label in info["rows"]:
                if n == name:
                    return (n, row, label)
        return None

    # ---------- search ----------
    def _on_search_change(self, *args):
        query = self.search_var.get().strip().lower()
        for cat, info in self.category_frames.items():
            match_in_cat = False
            for name, row, label in info["rows"]:
                if query == "" or query in name.lower():
                    row.pack(fill="x", pady=3)
                    match_in_cat = True
                else:
                    row.pack_forget()
            if query != "":
                if match_in_cat:
                    info["arrow"].configure(text="▼")
                    info["open"] = True
                else:
                    info["arrow"].configure(text="►")
                    info["open"] = False
            else:
                saved_open = self.settings.get("categories_open", {}).get(cat, True)
                if saved_open:
                    for name, row, label in info["rows"]:
                        row.pack(fill="x", pady=3)
                    info["arrow"].configure(text="▼")
                    info["open"] = True
                else:
                    for name, row, label in info["rows"]:
                        row.pack_forget()
                    info["arrow"].configure(text="►")
                    info["open"] = False

    def _clear_search(self):
        self.search_var.set("")
        self._on_search_change()

    # ---------- theme toggle ----------
    def _toggle_theme(self):
        new = "dark" if self.theme_switch.get() == 1 else "light"
        self.settings["theme"] = new
        save_json_file(SETTINGS_FILE, self.settings)
        ctk.set_appearance_mode(new)
        self.theme_label.configure(text="🌙" if new=="dark" else "☀️")

    # ---------- progress text ----------
    def _progress_text(self):
        total = sum(len(lst) for lst in self.monsters.values())
        done = sum(1 for v in self.progress.values() if v)
        return f"{done}/{total} capturés"

    def _update_progress_label(self):
        self.progress_label.configure(text=self._progress_text())

# ---------- run ----------
def main():
    if not MONSTERS_JSON.exists():
        template = {
            "Monstres": ["Arakne", "Arakne malade", "Boufton blanc", "Moskito", "Piou bleu", "Tofu"],
            "Boss": ["Blop Coco Royal", "Bouftou Royal", "Dragon Cochon"],
            "Archimonstres": ["Sourizoto le Collant", "Mosketère le Dévoué", "Kralamoure Géant"]
        }
        MONSTERS_JSON.parent.mkdir(parents=True, exist_ok=True)
        save_json_file(MONSTERS_JSON, template)
        print(f"Création d'un fichier modèle : {MONSTERS_JSON}. Édite-le pour ajouter tes listes complètes.")
    app = OtomaiApp()
    app.mainloop()

if __name__ == "__main__":
    main()
