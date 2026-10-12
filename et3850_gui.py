"""Retro LAN console for an already-modified ET-3850."""

from __future__ import annotations

import math
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from et3850_client import probe
from mod_shell import connect


BG = "#070b1c"
PANEL = "#101a32"
CYAN = "#55f4ef"
PINK = "#fa5ecc"
LIME = "#baff88"
TEXT = "#e9f8ff"
MUTED = "#91a9c5"
FONT = "Consolas"


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("ET-3850 // MOD LAB")
        root.geometry("980x700")
        root.minsize(760, 580)
        root.configure(bg=BG)
        self.host = tk.StringVar(value="192.168.0.12")
        self.password = tk.StringVar()
        self.command = tk.StringVar(value="id")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.busy = False
        self._build()
        root.after(100, self._drain)

    def _build(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(22, 10))
        tk.Label(header, text="◆ ET-3850 // MOD LAB", bg=BG, fg=CYAN,
                 font=(FONT, 22, "bold")).pack(side="left")
        tk.Label(header, text="OWNER CONSOLE  //  LINUX 4.4", bg=BG, fg=PINK,
                 font=(FONT, 10, "bold")).pack(side="right")

        wave = tk.Canvas(self.root, height=145, bg="#0b177a", highlightthickness=0)
        wave.pack(fill="x")
        wave.bind("<Configure>", lambda _event: self._wave(wave))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)
        left = tk.Frame(body, bg=BG, width=310)
        left.pack(side="left", fill="y", padx=(0, 18))
        left.pack_propagate(False)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        card = self._card(left, "01 / PRINTER LINK")
        self._field(card, "HOST / IP", self.host)
        self._button(card, "PROBE PORTS", self._probe, CYAN)
        tk.Label(card, text="Checks 22 / 23 / 2323 only", bg=PANEL, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", pady=(8, 0))

        card = self._card(left, "02 / PRIVATE LOGIN")
        self._field(card, "PASSWORD FILE", self.password)
        self._button(card, "CHOOSE FILE", self._choose, CYAN)
        self._button(card, "READ LIVE STATUS", self._status, PINK)
        tk.Label(card, text="No password is stored in this app or repository.",
                 bg=PANEL, fg=MUTED, font=(FONT, 9), wraplength=265,
                 justify="left").pack(anchor="w", pady=(10, 0))

        card = self._card(right, "03 / ROOT CONSOLE")
        tk.Label(card, text="Run a command on your already-modded printer",
                 bg=PANEL, fg=MUTED, font=(FONT, 10)).pack(anchor="w")
        self._field(card, "COMMAND", self.command)
        self._button(card, "RUN COMMAND", self._run_command, LIME)

        log_card = self._card(right, "SESSION OUTPUT")
        self.log = tk.Text(log_card, bg="#080e22", fg=LIME, insertbackground=CYAN,
                           relief="flat", font=(FONT, 10), padx=12, pady=12,
                           wrap="word")
        self.log.pack(fill="both", expand=True)
        self._write("ET3850MOD companion ready. This client does not install firmware.\n")
        self.status_line = tk.Label(self.root, text="● READY", bg="#111a31", fg=LIME,
                                    anchor="w", padx=24, pady=8, font=(FONT, 10, "bold"))
        self.status_line.pack(fill="x")

    def _wave(self, canvas: tk.Canvas) -> None:
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        colors = ("#083ea6", "#075ac5", "#047cdb", "#00a0ed", "#43d9fb")
        for layer, color in enumerate(colors):
            points = []
            for x in range(0, width + 8, 8):
                y = 55 + layer * 12 + 15 * math.sin(x / 100 + layer * 0.3)
                points.extend((x, y))
            canvas.create_line(*points, fill=color, width=7 + layer * 2, smooth=True)
        canvas.create_text(24, 121, anchor="w", text="NO STOCK SIGNING KEY // LIVE ROOT VERIFIED",
                           fill="#d4faff", font=(FONT, 10, "bold"))

    def _card(self, parent: tk.Frame, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg="#2b4b70", padx=1, pady=1)
        outer.pack(fill="both", expand=parent is not None and title == "SESSION OUTPUT",
                   pady=(0, 14))
        inner = tk.Frame(outer, bg=PANEL, padx=16, pady=14)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title, bg=PANEL, fg=CYAN,
                 font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))
        return inner

    def _field(self, parent: tk.Frame, label: str, value: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg=PANEL, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", pady=(7, 2))
        tk.Entry(parent, textvariable=value, bg="#080e22", fg=TEXT,
                 insertbackground=CYAN, relief="flat", font=(FONT, 10)).pack(fill="x", ipady=6)

    def _button(self, parent: tk.Frame, text: str, action, color: str) -> None:
        tk.Button(parent, text=text, command=action, bg="#15213d", fg=color,
                  activebackground=color, activeforeground=BG, relief="flat",
                  bd=0, padx=12, pady=8, font=(FONT, 10, "bold"),
                  cursor="hand2").pack(anchor="w", pady=(9, 0))

    def _write(self, text: str) -> None:
        self.log.insert("end", text + ("\n" if not text.endswith("\n") else ""))
        self.log.see("end")

    def _choose(self) -> None:
        selected = filedialog.askopenfilename(title="Choose your ET3850MOD password file")
        if selected:
            self.password.set(selected)

    def _start(self, label: str, task) -> None:
        if self.busy:
            return
        self.busy = True
        self.status_line.configure(text="● " + label.upper(), fg=PINK)

        def worker() -> None:
            try:
                self.events.put((label, task()))
            except Exception as error:
                self.events.put((label, error))

        threading.Thread(target=worker, daemon=True).start()

    def _drain(self) -> None:
        try:
            while True:
                label, result = self.events.get_nowait()
                self.busy = False
                self.status_line.configure(text="● READY", fg=LIME)
                self._write(f"[{label}]")
                self._write(str(result))
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _host(self) -> str:
        host = self.host.get().strip()
        if not host:
            raise ValueError("Enter the printer's IP address or hostname")
        return host

    def _secret_file(self) -> Path:
        path = Path(self.password.get().strip())
        if not path.is_file():
            raise ValueError("Choose your private password file")
        return path

    def _probe(self) -> None:
        self._start("port probe", lambda: probe(self._host()))

    def _status(self) -> None:
        command = ("id; uname -a; "
                   "printf 'Wi-Fi power: '; cat /sys/module/8723du/parameters/rtw_power_mgnt; "
                   "printf 'USB suspend: '; cat /sys/module/8723du/parameters/rtw_enusbss")
        self._start("live status", lambda: connect(self._host(), self._secret_file(), command))

    def _run_command(self) -> None:
        command = self.command.get().strip()
        if not command:
            messagebox.showinfo("Command needed", "Enter a shell command.")
            return
        self._start("root command", lambda: connect(self._host(), self._secret_file(), command))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
