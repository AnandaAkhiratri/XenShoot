"""
Authentication manager for KShot desktop.
Handles session persistence and API login/verification.
"""

import json
import requests
from pathlib import Path


class AuthManager:
    _SESSION_FILE  = Path.home() / ".KShot" / "session.json"
    _PENDING_FILE  = Path.home() / ".KShot" / "pending_credentials.json"

    def __init__(self, config):
        self._config = config
        self._session: dict = self._load()

    # ── Session persistence ───────────────────────────────────────────────────

    def _load(self) -> dict:
        try:
            if self._SESSION_FILE.exists():
                with open(self._SESSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[AUTH] Could not load session: {e}")
        return {}

    def _save(self) -> None:
        try:
            self._SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self._SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(self._session, f, indent=2)
        except Exception as e:
            print(f"[AUTH] Could not save session: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        return bool(self._session.get("user_id") and self._session.get("username"))

    @property
    def user_id(self) -> int | None:
        return self._session.get("user_id")

    @property
    def username(self) -> str:
        return self._session.get("username", "")

    @property
    def name(self) -> str:
        return self._session.get("name", "")

    def login_with_credentials(self, username: str, password: str) -> tuple[bool, str]:
        """
        Calls POST /api/auth/login on the Laravel server.
        Returns (success: bool, message: str).
        On success the session is persisted to disk automatically.
        """
        api_url = self._config.get("laravel_api_url", "https://kshot.cloud")
        try:
            resp = requests.post(
                f"{api_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            data = resp.json()
        except requests.exceptions.ConnectionError:
            return False, "Tidak bisa terhubung ke server. Periksa koneksi internet."
        except requests.exceptions.Timeout:
            return False, "Server tidak merespons (timeout). Coba lagi."
        except Exception as e:
            return False, f"Error: {e}"

        if resp.status_code == 200 and data.get("success"):
            user = data["user"]
            self._session = {
                "user_id":  user["id"],
                "username": user["username"],
                "name":     user["name"],
            }
            self._save()
            return True, data.get("message", "Login berhasil.")

        return False, data.get("message", "Login gagal.")

    def verify_session(self) -> bool:
        """
        Verify the stored session is still valid against the server.
        Returns True if valid, False otherwise (caller should re-show login).
        Silently succeeds if the server is unreachable (offline-friendly).
        """
        if not self.is_logged_in():
            return False

        api_url = self._config.get("laravel_api_url", "https://kshot.cloud")
        try:
            resp = requests.post(
                f"{api_url}/api/auth/verify",
                json={"username": self.username, "user_id": self.user_id},
                timeout=6,
            )
            if resp.status_code == 401:
                return False
            return True
        except Exception:
            # Network error → keep existing session (offline mode)
            return True

    def consume_pending_credentials(self) -> tuple[bool, str]:
        """
        If the installer wrote a pending_credentials.json, try to log in with it.
        On success: saves session, deletes the pending file, returns (True, "").
        On failure: keeps pending file for inspection, returns (False, error_msg).
        If no pending file: returns (False, "").
        """
        if not self._PENDING_FILE.exists():
            return False, ""

        try:
            with open(self._PENDING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            username = data.get("username", "")
            password = data.get("password", "")
        except Exception as e:
            print(f"[AUTH] Could not read pending credentials: {e}")
            return False, ""

        if not username or not password:
            return False, ""

        print(f"[AUTH] Found pending credentials for '{username}', attempting auto-login…")
        ok, msg = self.login_with_credentials(username, password)

        # Always delete the pending file — whether login succeeded or failed.
        # On failure the user will log in manually via wizard.
        try:
            self._PENDING_FILE.unlink()
        except Exception:
            pass

        if ok:
            print("[AUTH] Auto-login from installer succeeded.")
        else:
            print(f"[AUTH] Auto-login failed: {msg}")

        return ok, msg

    def logout(self) -> None:
        self._session = {}
        try:
            if self._SESSION_FILE.exists():
                self._SESSION_FILE.unlink()
        except Exception as e:
            print(f"[AUTH] Could not delete session file: {e}")
        print("[AUTH] Logged out.")
