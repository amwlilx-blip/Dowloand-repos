import os
import sys
import json
import fnmatch
import threading
import requests
import customtkinter as ctk
from tkinter import filedialog

GITHUB_API = "https://api.github.com"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_default_color_theme(resource_path("ds.json"))
        ctk.set_appearance_mode("dark")

        self.title("Driver Loader")

        # --- Окно: больше по размеру и по центру экрана ---
        win_w, win_h = 720, 800
        self.minsize(640, 680)
        self.attributes("-alpha", 0.97)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - win_w) // 2
        y = (sh - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

        icon = resource_path("my_icon.ico")
        if os.path.exists(icon):
            self.after(200, lambda: self.iconbitmap(icon))

        BG_CARD = "#241640"
        ACCENT = "#8b5cf6"
        ACCENT_HOVER = "#a78bfa"
        TEXT_MAIN = "#ede9fe"
        TEXT_SUB = "#a78bfa"

        self.BG_CARD = BG_CARD
        self.ACCENT = ACCENT
        self.ACCENT_HOVER = ACCENT_HOVER
        self.TEXT_MAIN = TEXT_MAIN
        self.TEXT_SUB = TEXT_SUB

        self.token = os.environ.get("GITHUB_TOKEN", "")
        self.username_var = ctk.StringVar(value="")
        self.repo_checkboxes = {}

        # ===== Верхняя карточка =====
        top = ctk.CTkFrame(self, corner_radius=16, fg_color=BG_CARD,
                           border_width=1, border_color="#4a2f80")
        top.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkLabel(top, text="GitHub username",
                     font=("Segoe UI", 12), text_color=TEXT_SUB
                     ).grid(row=0, column=0, padx=(16, 8), pady=(12, 4), sticky="w")

        self.username_entry = ctk.CTkEntry(
            top, textvariable=self.username_var, width=260,
            placeholder_text="например, amwli",
            fg_color="#1a0f2e", border_color=ACCENT, text_color=TEXT_MAIN
        )
        self.username_entry.grid(row=0, column=1, padx=(0, 8), pady=(12, 4), sticky="w")

        self.load_btn = ctk.CTkButton(
            top, text="Загрузить с GitHub", width=160,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.load_repos_thread
        )
        self.load_btn.grid(row=0, column=2, padx=(0, 16), pady=(12, 4))

        ctk.CTkLabel(top, text="Шаблон файла",
                     font=("Segoe UI", 12), text_color=TEXT_SUB
                     ).grid(row=1, column=0, padx=(16, 8), pady=(4, 6), sticky="w")

        self.pattern_entry = ctk.CTkEntry(
            top, width=260, fg_color="#1a0f2e",
            border_color=ACCENT, text_color=TEXT_MAIN
        )
        self.pattern_entry.insert(0, "*.exe")
        self.pattern_entry.grid(row=1, column=1, padx=(0, 8), pady=(4, 6), sticky="w")

        self.load_json_btn = ctk.CTkButton(
            top, text="Загрузить projects.json", width=160,
            fg_color="transparent", hover_color="#3b2a66",
            text_color=TEXT_SUB, border_width=1, border_color=ACCENT,
            command=self.load_projects_json
        )
        self.load_json_btn.grid(row=1, column=2, padx=(0, 16), pady=(4, 6))

        # ===== Список проектов =====
        mid = ctk.CTkFrame(self, corner_radius=16, fg_color=BG_CARD,
                           border_width=1, border_color="#4a2f80")
        mid.pack(fill="both", expand=True, padx=14, pady=8)

        header = ctk.CTkFrame(mid, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(header, text="Проекты",
                     font=("Segoe UI Black", 16), text_color=TEXT_MAIN
                     ).pack(side="left")

        ctk.CTkButton(
            header, text="Выбрать все", width=110, height=26,
            fg_color="transparent", hover_color="#3b2a66",
            text_color=TEXT_SUB, command=self.toggle_all
        ).pack(side="right")

        self.repo_scroll = ctk.CTkScrollableFrame(
            mid, fg_color="#1a0f2e", corner_radius=12
        )
        self.repo_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        # ===== Папка и кнопка скачивания =====
        bottom = ctk.CTkFrame(self, corner_radius=16, fg_color=BG_CARD,
                              border_width=1, border_color="#4a2f80")
        bottom.pack(fill="x", padx=14, pady=(8, 14))

        self.download_dir_var = ctk.StringVar(value=os.path.abspath("downloads"))

        ctk.CTkLabel(bottom, text="Куда скачивать",
                     font=("Segoe UI", 12), text_color=TEXT_SUB
                     ).grid(row=0, column=0, padx=(16, 8), pady=(12, 4), sticky="w")

        self.dir_entry = ctk.CTkEntry(
            bottom, textvariable=self.download_dir_var, width=460,
            fg_color="#1a0f2e", border_color=ACCENT, text_color=TEXT_MAIN
        )
        self.dir_entry.grid(row=0, column=1, padx=(0, 8), pady=(12, 4), sticky="w")

        ctk.CTkButton(
            bottom, text="…", width=44,
            fg_color="transparent", hover_color="#3b2a66",
            text_color=TEXT_MAIN, command=self.pick_dir
        ).grid(row=0, column=2, padx=(0, 16), pady=(12, 4))

        self.download_btn = ctk.CTkButton(
            bottom, text="⬇ Скачать выбранное", height=44,
            font=("Segoe UI", 15, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.download_thread
        )
        self.download_btn.grid(row=1, column=0, columnspan=3,
                               padx=16, pady=(4, 8), sticky="ew")

        # Лог стал ниже, чтобы всё влезло в окно
        self.log_box = ctk.CTkTextbox(
            bottom, height=90, corner_radius=10,
            fg_color="#1a0f2e", text_color=TEXT_MAIN,
            font=("Consolas", 11)
        )
        self.log_box.grid(row=2, column=0, columnspan=3,
                          padx=16, pady=(0, 14), sticky="ew")
        self.log_box.configure(state="disabled")

        if self.token:
            self.log("✅ Токен GitHub найден — лимит 5000 запросов/час")
        else:
            self.log("⚠️ GITHUB_TOKEN не задан — лимит 60 запросов/час")

        if os.path.exists("projects.json"):
            self.after(300, self.load_projects_json)

    # ---------- Утилиты ----------
    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def headers(self):
        h = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def pick_dir(self):
        path = filedialog.askdirectory(initialdir=self.download_dir_var.get())
        if path:
            self.download_dir_var.set(path)

    def toggle_all(self):
        if not self.repo_checkboxes:
            return
        states = [v[0].get() for v in self.repo_checkboxes.values()]
        target = not all(states)
        for v in self.repo_checkboxes.values():
            v[0].set(target)

    # ---------- projects.json ----------
    def load_projects_json(self):
        path = "projects.json"
        if not os.path.exists(path):
            self.log("❌ projects.json не найден в папке программы")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                projects = json.load(f)
        except Exception as e:
            self.log(f"❌ Ошибка чтения projects.json: {e}")
            return

        if not isinstance(projects, list):
            self.log("❌ projects.json должен быть массивом [...]")
            return

        added = 0
        for p in projects:
            if isinstance(p, dict):
                owner = p.get("owner") or self.username_var.get().strip()
                repo = p.get("repo")
                pattern = p.get("asset_pattern", "")
            elif isinstance(p, str):
                if "/" in p:
                    owner, repo = p.split("/", 1)
                else:
                    owner = self.username_var.get().strip()
                    repo = p
                pattern = ""
            else:
                continue

            if not owner or not repo:
                self.log(f"⚠️ Пропущен проект без owner/repo: {p}")
                continue

            self._add_repo_checkbox(repo, owner, pattern)
            added += 1

        self.log(f"📄 Из projects.json добавлено проектов: {added}")

    # ---------- GitHub username ----------
    def load_repos_thread(self):
        username = self.username_var.get().strip()
        if not username:
            self.log("❌ Введите GitHub username")
            return
        self.load_btn.configure(state="disabled", text="Загрузка...")
        threading.Thread(target=self._load_repos, args=(username,), daemon=True).start()

    def _load_repos(self, username):
        try:
            repos = []
            page = 1
            while True:
                url = f"{GITHUB_API}/users/{username}/repos?per_page=100&page={page}"
                r = requests.get(url, headers=self.headers(), timeout=15)
                if r.status_code == 404:
                    self.after(0, lambda: self.log(f"❌ Пользователь '{username}' не найден"))
                    return
                r.raise_for_status()
                data = r.json()
                if not data:
                    break
                repos.extend(data)
                page += 1

            self.after(0, lambda: self._populate_repos(username, repos))
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Ошибка загрузки списка: {e}"))
        finally:
            self.after(0, lambda: self.load_btn.configure(
                state="normal", text="Загрузить с GitHub"))

    def _populate_repos(self, owner, repos):
        if not repos:
            self.log("ℹ️ У пользователя нет публичных репозиториев")
            return
        added = 0
        for repo in repos:
            name = repo["name"]
            if name in self.repo_checkboxes:
                continue
            self._add_repo_checkbox(name, owner, "")
            added += 1
        self.log(f"✅ С GitHub добавлено репозиториев: {added}")

    # ---------- Чекбокс ----------
    def _add_repo_checkbox(self, name, owner, default_pattern=""):
        if name in self.repo_checkboxes:
            return
        var = ctk.BooleanVar(value=False)
        cb = ctk.CTkCheckBox(
            self.repo_scroll, text=f"{owner}/{name}", variable=var,
            font=("Segoe UI", 12),
            text_color=self.TEXT_MAIN,
            text_color_disabled="#8a7fa8",
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            border_color=self.ACCENT
        )
        cb.pack(anchor="w", padx=8, pady=4)
        self.repo_checkboxes[name] = (var, owner, default_pattern)

    # ---------- Скачивание ----------
    def download_thread(self):
        selected = [(name, data[1], data[2])
                    for name, data in self.repo_checkboxes.items() if data[0].get()]
        if not selected:
            self.log("❌ Ничего не выбрано")
            return
        global_pattern = self.pattern_entry.get().strip() or "*"
        out_dir = self.download_dir_var.get().strip()

        self.download_btn.configure(state="disabled", text="Скачивание...")
        threading.Thread(
            target=self._download_all,
            args=(selected, global_pattern, out_dir),
            daemon=True
        ).start()

    def _download_all(self, selected, global_pattern, out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Не удалось создать папку: {e}"))
            self.after(0, lambda: self.download_btn.configure(
                state="normal", text="⬇ Скачать выбранное"))
            return

        for name, owner, default_pattern in selected:
            pattern = default_pattern or global_pattern
            self._process_repo(owner, name, pattern, out_dir)

        self.after(0, lambda: self.log("\n🏁 Готово"))
        self.after(0, lambda: self.download_btn.configure(
            state="normal", text="⬇ Скачать выбранное"))

    # ---------- Обработка одного репозитория ----------
    def _process_repo(self, owner, repo, pattern, out_dir):
        self.after(0, lambda: self.log(f"\n📦 {owner}/{repo}"))
        try:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest"
            r = requests.get(url, headers=self.headers(), timeout=15)
            if r.status_code == 404:
                self.after(0, lambda: self.log("  — релизов нет, пропускаем"))
                return
            r.raise_for_status()
            release = r.json()
        except Exception as e:
            self.after(0, lambda: self.log(f"  ❌ Ошибка получения релиза: {e}"))
            return

        tag = release.get("tag_name", "?")
        assets = release.get("assets", [])
        if not assets:
            self.after(0, lambda: self.log(f"  — в релизе {tag} нет файлов"))
            return

        targets = [a for a in assets if fnmatch.fnmatch(a["name"], pattern)]
        if not targets:
            self.after(0, lambda: self.log(f"  — нет файлов под шаблон '{pattern}'"))
            return

        repo_dir = os.path.join(out_dir, repo)
        os.makedirs(repo_dir, exist_ok=True)

        for asset in targets:
            dest = os.path.join(repo_dir, asset["name"])
            self.after(0, lambda n=asset["name"], s=asset["size"]:
                       self.log(f"  ⬇ {n} ({s} байт)"))
            try:
                with requests.get(asset["browser_download_url"],
                                  headers=self.headers(), stream=True, timeout=60) as resp:
                    resp.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                self.after(0, lambda d=dest: self.log(f"  ✅ {d}"))
            except Exception as e:
                self.after(0, lambda e=e: self.log(f"  ❌ Ошибка скачивания: {e}"))


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()