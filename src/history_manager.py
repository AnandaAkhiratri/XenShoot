"""
History manager — stores last 30 screenshot entries in ~/.KShot/history.json

Each entry JSON:
  id, timestamp, type, url, filename, thumbnail (base64 small JPEG), image_path (full PNG on disk)

Full-resolution screenshots are stored in ~/.KShot/history/images/<id>.png
Thumbnails are kept as base64 JPEG inside the JSON for fast grid rendering.
"""

import json
import base64
import uuid
from datetime import datetime
from pathlib import Path


MAX_ENTRIES  = 30
THUMB_W, THUMB_H = 280, 180   # grid thumbnail size


class HistoryManager:
    def __init__(self):
        self.history_dir   = Path.home() / ".KShot"
        self.images_dir    = self.history_dir / "history" / "images"
        self.history_file  = self.history_dir / "history.json"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    # ── Load / Save ──────────────────────────────────────────────────────

    def load(self):
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self, entries):
        self.history_file.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ── Public API ───────────────────────────────────────────────────────

    def add(self, pixmap, entry_type="upload", url="", filename=""):
        """
        Add a new history entry.
          pixmap     : QPixmap of the screenshot (full resolution)
          entry_type : 'upload' | 'clipboard' | 'local'
          url        : public URL (empty for clipboard/local)
          filename   : filename used when saving
        """
        entry_id   = str(uuid.uuid4())
        image_path = str(self.images_dir / f"{entry_id}.png")

        # Save full-resolution PNG for crisp preview
        self._save_full(pixmap, image_path)

        # Build small thumbnail base64 for grid display
        thumb_b64 = self._pixmap_to_b64(pixmap)

        entry = {
            "id":         entry_id,
            "timestamp":  datetime.now().isoformat(timespec="seconds"),
            "type":       entry_type,
            "url":        url,
            "filename":   filename,
            "thumbnail":  thumb_b64,
            "image_path": image_path,
        }

        entries = self.load()
        entries.insert(0, entry)

        # Prune old entries and delete their image files
        if len(entries) > MAX_ENTRIES:
            for old in entries[MAX_ENTRIES:]:
                self._delete_image_file(old.get("image_path", ""))
            entries = entries[:MAX_ENTRIES]

        self._save(entries)
        return entry

    def delete(self, entry_id):
        entries = self.load()
        for e in entries:
            if e.get("id") == entry_id:
                self._delete_image_file(e.get("image_path", ""))
                break
        self._save([e for e in entries if e.get("id") != entry_id])

    def clear(self):
        for e in self.load():
            self._delete_image_file(e.get("image_path", ""))
        self._save([])

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _save_full(pixmap, path):
        """Save QPixmap as full-resolution PNG to disk."""
        try:
            pixmap.save(path, "PNG")
        except Exception as ex:
            print(f"[HISTORY] full image save error: {ex}")

    @staticmethod
    def _delete_image_file(path):
        try:
            if path:
                p = Path(path)
                if p.exists():
                    p.unlink()
        except Exception:
            pass

    @staticmethod
    def _pixmap_to_b64(pixmap):
        """QPixmap → scaled JPEG → base64 string (for grid thumbnail)."""
        try:
            from PyQt5.QtCore import QBuffer, QIODevice, Qt

            scaled = pixmap.scaled(
                THUMB_W, THUMB_H,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            scaled.save(buf, "JPEG", 85)
            return base64.b64encode(buf.data().data()).decode()
        except Exception as e:
            print(f"[HISTORY] thumbnail error: {e}")
            return ""

    @staticmethod
    def b64_to_pixmap(b64_str):
        """base64 string → QPixmap."""
        try:
            from PyQt5.QtGui import QPixmap
            from PyQt5.QtCore import QByteArray
            data = base64.b64decode(b64_str)
            px   = QPixmap()
            px.loadFromData(QByteArray(data), "JPEG")
            return px
        except Exception:
            return None

    @staticmethod
    def load_full_pixmap(entry):
        """Load the full-resolution PNG from disk for preview."""
        try:
            from PyQt5.QtGui import QPixmap
            path = entry.get("image_path", "")
            if path and Path(path).exists():
                px = QPixmap()
                px.load(path)
                if not px.isNull():
                    return px
        except Exception as e:
            print(f"[HISTORY] load full image error: {e}")
        # Fallback: decode thumbnail
        return HistoryManager.b64_to_pixmap(entry.get("thumbnail", ""))
