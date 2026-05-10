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
    root.configure(background="#101114")

    width = 156
    height = 42
    canvas = tk.Canvas(root, width=width, height=height, background="#101114", highlightthickness=0, bd=0)
    canvas.pack()
    rounded_rect(canvas, 1, 1, width - 1, height - 1, radius=20, fill="#202124", outline="#35363a")
    canvas.create_oval(18, 17, 26, 25, fill="#8ab4f8", outline="")
    canvas.create_text(88, 21, text="Dictating...", fill="#f1f3f4", font=("Sans", 11), anchor="center")

    root.update_idletasks()
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


def rounded_rect(canvas: object, x1: int, y1: int, x2: int, y2: int, *, radius: int, **kwargs: object) -> None:
    diameter = radius * 2
    canvas.create_arc(x1, y1, x1 + diameter, y1 + diameter, start=90, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - diameter, y1, x2, y1 + diameter, start=0, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - diameter, y2 - diameter, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2 - diameter, x1 + diameter, y2, start=180, extent=90, style="pieslice", **kwargs)
    canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
    canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)
    canvas.create_rectangle(x1 + radius, y1 + radius, x2 - radius, y2 - radius, **kwargs)


if __name__ == "__main__":
    main()
