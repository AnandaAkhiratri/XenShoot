"""
Dev launcher with auto-restart on file change.
Usage: python dev.py
"""

import sys
import os
import time
import subprocess
import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR  = Path(__file__).parent / "src"
ENTRY      = Path(__file__).parent / "run.py"
EXTENSIONS = {".py", ".json", ".svg", ".css"}
DEBOUNCE   = 1.2   # seconds — wait before restarting after last change


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_fn):
        self._restart = restart_fn
        self._timer   = None

    def on_modified(self, event):
        if not event.is_directory and Path(event.src_path).suffix in EXTENSIONS:
            self._schedule()

    def on_created(self, event):
        if not event.is_directory and Path(event.src_path).suffix in EXTENSIONS:
            self._schedule()

    def _schedule(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(DEBOUNCE, self._restart)
        self._timer.daemon = True
        self._timer.start()


class DevRunner:
    def __init__(self):
        self._proc = None

    def start(self):
        self._kill()
        print("\n" + "─" * 50)
        print("▶  Starting XenShoot…")
        print("─" * 50)
        self._proc = subprocess.Popen(
            [sys.executable, str(ENTRY)],
            stdout=None, stderr=None,
        )

    def restart(self):
        print("\n🔄  File changed — restarting…")
        self.start()

    def _kill(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def run(self):
        self.start()

        handler  = _ChangeHandler(restart_fn=self.restart)
        observer = Observer()
        observer.schedule(handler, str(WATCH_DIR), recursive=True)
        observer.start()

        print(f"\n👁  Watching  {WATCH_DIR.relative_to(Path.cwd())}  for changes…")
        print("   Press Ctrl+C to stop.\n")

        try:
            while True:
                time.sleep(0.5)
                # Auto-restart if the process crashes
                if self._proc and self._proc.poll() is not None:
                    code = self._proc.returncode
                    if code != 0:
                        print(f"⚠  Process exited (code {code}) — restarting in 1s…")
                        time.sleep(1)
                        self.start()
        except KeyboardInterrupt:
            print("\n\nStopping…")
        finally:
            observer.stop()
            observer.join()
            self._kill()
            print("Done.")


if __name__ == "__main__":
    DevRunner().run()
