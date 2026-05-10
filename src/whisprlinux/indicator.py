from __future__ import annotations

import signal
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class RecordingIndicator:
    enabled: bool = True
    process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        if not self.enabled or self.process is not None:
            return
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-m", "whisprlinux.indicator"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            self.process = None

    def stop(self) -> None:
        if self.process is None:
            return
        process = self.process
        self.process = None
        if process.returncode is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception:
            pass


def main() -> None:
    try:
        import tkinter as tk
    except Exception:
        return

    try:
        root = tk.Tk()
    except Exception:
        return
    root.withdraw()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.78)
    except tk.TclError:
        pass
    try:
        root.attributes("-type", "notification")
    except tk.TclError:
        pass
    root.configure(background="#202124")

    frame = tk.Frame(root, background="#202124", padx=18, pady=8)
    frame.pack()
    label = tk.Label(
        frame,
        text="Dictating...",
        background="#202124",
        foreground="#f1f3f4",
        font=("Sans", 11),
    )
    label.pack()

    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max(screen_height - height - 90, 0)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.deiconify()

    def close(_signum: int, _frame: object) -> None:
        root.after(0, root.destroy)

    signal.signal(signal.SIGTERM, close)
    signal.signal(signal.SIGINT, close)
    root.mainloop()


if __name__ == "__main__":
    main()
