"""
Local App Launcher
A lightweight Windows utility to launch locally-hosted applications with one click.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import customtkinter as ctk


# ── Config helpers ─────────────────────────────────────────────────────────────

def get_config_path() -> Path:
    """Return path to apps.json, next to the executable or script."""
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    return base / "apps.json"


def load_apps() -> list[dict]:
    config_path = get_config_path()
    if not config_path.exists():
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_apps(apps: list[dict]) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2)


# ── Terminal spawning ──────────────────────────────────────────────────────────

def _find_git_dir() -> Path | None:
    """Return the Git for Windows root directory."""
    candidates = [
        Path(r"C:\Program Files\Git"),
        Path(r"C:\Program Files (x86)\Git"),
    ]
    git_exe = shutil.which("git")
    if git_exe:
        candidates.insert(0, Path(git_exe).parent.parent)
    for c in candidates:
        if (c / "git-bash.exe").exists():
            return c
    return None


def _win_to_posix(win_path: str) -> str:
    """Convert C:\\foo\\bar to /c/foo/bar for use inside bash."""
    p = str(Path(win_path))
    if len(p) >= 2 and p[1] == ':':
        return '/' + p[0].lower() + p[2:].replace('\\', '/')
    return p.replace('\\', '/')


def spawn_terminal(path: str, command: str) -> None:
    """Open a new Git Bash window, cd to path, and pre-fill the command without running it."""
    git_dir = _find_git_dir()
    if not git_dir:
        raise OSError("Git for Windows not found. Please install it from https://gitforwindows.org")

    mintty = git_dir / "usr" / "bin" / "mintty.exe"
    bash   = git_dir / "bin" / "bash.exe"
    if not mintty.exists() or not bash.exists():
        raise OSError(f"Could not find mintty or bash under {git_dir}.")

    # Escape for a readline macro string (only backslash and double-quote are special)
    safe_macro = command.replace('\\', '\\\\').replace('"', '\\"')

    rc_lines = ['source ~/.bashrc 2>/dev/null']
    if path:
        bash_path = _win_to_posix(path).replace("'", "\\'")
        rc_lines.append(f"cd '{bash_path}'")

    # Bind terminal-status-response (ESC[0n) to a readline MACRO that inserts the
    # command text verbatim.  PROMPT_COMMAND sends the status query (ESC[5n) once,
    # just before readline starts reading; the terminal replies with ESC[0n and
    # readline immediately inserts the macro text into the buffer.
    rc_lines.append("bind '\"\\e[0n\": \"" + safe_macro + "\"'")
    rc_lines.append("PROMPT_COMMAND='printf \"\\e[5n\"; unset PROMPT_COMMAND'")

    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.bashrc', delete=False, encoding='utf-8'
    )
    tmp.write('\n'.join(rc_lines) + '\n')
    tmp.close()

    subprocess.Popen(
        [str(mintty), str(bash), '--rcfile', _win_to_posix(tmp.name), '-i'],
        shell=False,
    )

# ── App Editor Dialog ──────────────────────────────────────────────────────────

class AppEditorDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing an app entry."""

    def __init__(self, parent: ctk.CTk, app: dict | None = None, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.app = app or {}
        self.title("Edit App" if app else "Add App")
        self.geometry("500x380")
        self.resizable(False, False)
        self.grab_set()  # modal
        self.lift()
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": (0, 2)}

        ctk.CTkLabel(self, text="Name *", anchor="w").pack(fill="x", padx=24, pady=(18, 2))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Stable Diffusion")
        self.name_entry.insert(0, self.app.get("name", ""))
        self.name_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Working Directory (path)", anchor="w").pack(fill="x", padx=24, pady=(10, 2))
        self.path_entry = ctk.CTkEntry(self, placeholder_text=r"e.g. C:\AI\stable-diffusion")
        self.path_entry.insert(0, self.app.get("path", ""))
        self.path_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Start Command *", anchor="w").pack(fill="x", padx=24, pady=(10, 2))
        self.command_entry = ctk.CTkEntry(self, placeholder_text="e.g. webui-user.bat  or  npm start")
        self.command_entry.insert(0, self.app.get("command", ""))
        self.command_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="URL", anchor="w").pack(fill="x", padx=24, pady=(10, 2))
        self.url_entry = ctk.CTkEntry(self, placeholder_text="e.g. http://127.0.0.1:7860")
        self.url_entry.insert(0, self.app.get("url", ""))
        self.url_entry.pack(fill="x", **pad)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#FF6B6B", anchor="w")
        self.error_label.pack(fill="x", padx=24, pady=(6, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(10, 18))
        ctk.CTkButton(btn_frame, text="Cancel", width=100,
                      fg_color="gray40", hover_color="gray30",
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=100,
                      command=self._save).pack(side="right")

    def _save(self):
        name = self.name_entry.get().strip()
        command = self.command_entry.get().strip()

        if not name:
            self.error_label.configure(text="Name is required.")
            return
        if not command:
            self.error_label.configure(text="Start Command is required.")
            return

        result = {
            "id": self.app.get("id") or str(uuid.uuid4()),
            "name": name,
            "path": self.path_entry.get().strip(),
            "command": command,
            "url": self.url_entry.get().strip(),
        }
        if self.on_save:
            self.on_save(result)
        self.destroy()


# ── Main Application ───────────────────────────────────────────────────────────

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Local App Launcher")
        self.geometry("660x540")
        self.minsize(500, 320)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.apps: list[dict] = load_apps()
        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 6))

        ctk.CTkLabel(
            header, text="Local App Launcher",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Add App", width=110,
            command=self._add_app,
        ).pack(side="right")

        # Scrollable app list
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Applications")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(4, 0))

        self._render_app_list()

        # Notification bar at bottom
        self.notification = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), height=30,
        )
        self.notification.pack(pady=(4, 14))

    def _render_app_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.apps:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No apps configured yet.  Click '+ Add App' to get started.",
                text_color="gray60",
                font=ctk.CTkFont(size=13),
            ).pack(pady=40)
            return

        for app in self.apps:
            self._add_app_card(app)

    def _add_app_card(self, app: dict):
        card = ctk.CTkFrame(self.scroll_frame)
        card.pack(fill="x", pady=4, padx=2)

        # Info column
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info,
            text=app.get("name", "Unnamed"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(anchor="w")

        url_text = app.get("url") or "no URL configured"
        ctk.CTkLabel(
            info,
            text=url_text,
            text_color="gray60",
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame, text="Launch", width=84,
            command=lambda a=app: self._launch(a),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="Edit", width=64,
            fg_color="gray40", hover_color="gray30",
            command=lambda a=app: self._edit_app(a),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="✕", width=36,
            fg_color="#7A1C1C", hover_color="#5C1010",
            command=lambda a=app: self._delete_app(a),
        ).pack(side="left")

    # ── Actions ────────────────────────────────────────────────────────────────

    def _launch(self, app: dict):
        path = app.get("path", "")
        command = app.get("command", "")
        url = app.get("url", "")

        if not command:
            self._notify("No command configured for this app.", error=True)
            return

        if path and not Path(path).exists():
            self._notify(f"Path not found: {path}", error=True)
            return

        try:
            spawn_terminal(path, command)
        except OSError as exc:
            self._notify(f"Failed to launch terminal: {exc}", error=True)
            return

        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self._notify(f"Launched  ·  URL copied to clipboard: {url}")
        else:
            self._notify(f"Launched '{app.get('name', '')}' (no URL configured).")

    def _add_app(self):
        AppEditorDialog(self, on_save=self._on_app_saved)

    def _edit_app(self, app: dict):
        AppEditorDialog(self, app=app, on_save=self._on_app_saved)

    def _delete_app(self, app: dict):
        self.apps = [a for a in self.apps if a.get("id") != app.get("id")]
        save_apps(self.apps)
        self._render_app_list()

    def _on_app_saved(self, updated: dict):
        ids = [a.get("id") for a in self.apps]
        if updated["id"] in ids:
            self.apps = [updated if a.get("id") == updated["id"] else a for a in self.apps]
        else:
            self.apps.append(updated)
        save_apps(self.apps)
        self._render_app_list()

    # ── Notification helper ────────────────────────────────────────────────────

    def _notify(self, message: str, error: bool = False):
        color = "#FF6B6B" if error else "#6BCB77"
        self.notification.configure(text=message, text_color=color)
        self.after(4000, lambda: self.notification.configure(text=""))


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
