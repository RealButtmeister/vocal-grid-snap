"""Small desktop front end for Vocal Grid Snap. Run with Python 3.13."""

from __future__ import annotations

import math
import os
from pathlib import Path
import queue
import json
import sys
import threading
import traceback
from dataclasses import asdict, is_dataclass
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


BG = "#10151f"
PANEL = "#192231"
INK = "#edf3fd"
MUTED = "#a8b7cb"
ACCENT = "#79c8ff"
APP_DIR = Path(__file__).resolve().parent


def save_error_report(stage, exc, *, input_path="", output_path="", config=None, trace_text=None):
    """Persist a failure without allowing a logging error to hide the original."""
    try:
        settings = asdict(config) if is_dataclass(config) and not isinstance(config, type) else config
        details = (
            "VOCAL GRID SNAP — LAST ERROR\n"
            f"Time: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"Stage: {stage}\n"
            f"Python: {sys.executable}\n"
            f"Input: {input_path}\n"
            f"Output folder: {output_path}\n"
            f"Settings: {json.dumps(settings, ensure_ascii=False, default=str, sort_keys=True)}\n\n"
            + (trace_text or "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        )
        locations = [APP_DIR / "Last error.txt"]
        local_data = os.environ.get("LOCALAPPDATA")
        if local_data:
            locations.append(Path(local_data) / "Vocal Grid Snap" / "Last error.txt")
        for path in locations:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(details, encoding="utf-8")
                return path
            except OSError:
                continue
    except Exception:
        # Diagnostics must never replace the processing exception.
        pass
    return None


def error_message(exc, report_path):
    message = f"{type(exc).__name__}: {exc}"
    if report_path is not None:
        return f"{message}\n\nError details saved to:\n{report_path}\n\nYou can open Last error.txt and copy its contents for troubleshooting."
    return f"{message}\n\nThe error report could not be saved. Copy this message for troubleshooting."


def show_native_error(message):
    """Make startup errors visible even when pythonw has no console or Tk fails."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Vocal Grid Snap — error", 0x10)
    except (AttributeError, OSError):
        if sys.stderr is not None:
            print(message, file=sys.stderr)


class VocalGridSnapApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Vocal Grid Snap")
        self.root.geometry("940x880")
        self.root.minsize(860, 800)
        self.root.configure(bg=BG)
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.running = False
        self.result = None
        self.last_default_output = ""
        self.editable = []
        self.section_widgets = []

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.bpm_var = tk.StringVar(value="140")
        self.grid_var = tk.StringVar(value="1/16")
        self.sensitivity_var = tk.DoubleVar(value=60)
        self.sensitivity_label = tk.StringVar(value="60%")
        self.slice_var = tk.StringVar(value="80")
        self.offset_var = tk.StringVar(value="0")
        self.source_bpm_var = tk.StringVar()
        self.slices_var = tk.BooleanVar(value=False)
        self.section_mode_var = tk.BooleanVar(value=True)
        self.section_block_var = tk.StringVar(value="2 bars")
        self.section_gap_var = tk.StringVar(value="2")
        self.start_bar_var = tk.StringVar(value="2")
        self.section_summary_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready — choose an isolated vocal stem.")
        self._make_styles()
        self._build()
        self.root.report_callback_exception = self._callback_error
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(100, self._poll)

    def _make_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=INK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 23))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Badge.TLabel", foreground=ACCENT, font=("Segoe UI Semibold", 10))
        style.configure("Panel.TLabel", background=PANEL)
        style.configure("PanelMuted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Section.TLabel", background=PANEL, font=("Segoe UI Semibold", 11))
        style.configure("TEntry", fieldbackground="#0d1420", foreground=INK, insertcolor=INK, padding=7)
        style.configure("TCombobox", fieldbackground="#0d1420", background=PANEL, foreground=INK, padding=6, arrowsize=14)
        style.map("TCombobox", fieldbackground=[("readonly", "#0d1420")], foreground=[("readonly", INK)])
        style.configure("TButton", background="#2b3a50", foreground=INK, font=("Segoe UI", 10), padding=(14, 8))
        style.map("TButton", background=[("active", "#3a4f6d"), ("disabled", "#222c3c")], foreground=[("disabled", "#67748a")])
        style.configure("Primary.TButton", background="#66b8f0", foreground="#071523", font=("Segoe UI Semibold", 11))
        style.map("Primary.TButton", background=[("active", "#97d6ff"), ("disabled", "#2b3a50")], foreground=[("disabled", "#8191a7")])
        style.configure("TCheckbutton", background=PANEL, foreground=INK, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", PANEL)], foreground=[("disabled", "#68768c")])
        style.configure("Horizontal.TScale", background=PANEL, troughcolor="#0d1420")
        style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=PANEL, borderwidth=0)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#253247", foreground=MUTED, font=("Segoe UI Semibold", 10), padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", PANEL), ("active", "#354a65")], foreground=[("selected", INK)])
        self.root.option_add("*TCombobox*Listbox.background", "#192231")
        self.root.option_add("*TCombobox*Listbox.foreground", INK)
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#385f83")

    def _build(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(5, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 11))
        ttk.Label(header, text="VOCAL GRID SNAP", style="Badge.TLabel").pack(anchor="w")
        ttk.Label(header, text="Make the rhythm land.", style="Title.TLabel").pack(anchor="w", pady=(2, 3))
        ttk.Label(header, text="Hard word / syllable timing for FL Studio  ·  100% snap to your chosen grid", style="Muted.TLabel").pack(anchor="w")

        files = ttk.Frame(outer, style="Panel.TFrame", padding=16)
        files.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        files.columnconfigure(1, weight=1)
        ttk.Label(files, text="Vocal file", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 14))
        input_entry = ttk.Entry(files, textvariable=self.input_var)
        input_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        input_entry.bind("<FocusOut>", lambda _e: self._update_output_default())
        input_button = ttk.Button(files, text="Choose file…", command=self._choose_input)
        input_button.grid(row=0, column=2, sticky="ew")
        ttk.Label(files, text="Save exports", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 14), pady=(10, 0))
        output_entry = ttk.Entry(files, textvariable=self.output_var)
        output_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(10, 0))
        output_button = ttk.Button(files, text="Choose folder…", command=self._choose_output)
        output_button.grid(row=1, column=2, sticky="ew", pady=(10, 0))
        ttk.Label(files, text="Use an isolated vocal. Each run gets its own folder; your input stays unchanged.", style="PanelMuted.TLabel").grid(row=2, column=1, columnspan=2, sticky="w", pady=(10, 0))
        self.editable.extend([input_entry, input_button, output_entry, output_button])

        notebook = ttk.Notebook(outer)
        notebook.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        settings = ttk.Frame(notebook, style="Panel.TFrame", padding=16)
        notebook.add(settings, text="Timing & cuts")
        for col in (1, 3):
            settings.columnconfigure(col, weight=1)
        ttk.Label(settings, text="Timing", style="Section.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self._field(settings, 1, 0, "Target BPM", self.bpm_var)
        ttk.Label(settings, text="Snap grid", style="Panel.TLabel").grid(row=1, column=2, sticky="w", padx=(22, 12))
        grid_combo = ttk.Combobox(settings, textvariable=self.grid_var, values=("1/8", "1/16", "1/32", "1/8T", "1/16T"), width=17, state="readonly")
        grid_combo.grid(row=1, column=3, sticky="ew")
        self.editable.append(grid_combo)
        self.grid_combo = grid_combo
        self._field(settings, 2, 0, "Beat offset (ms)", self.offset_var)
        self._field(settings, 2, 2, "Source BPM (optional)", self.source_bpm_var)
        ttk.Label(settings, text="Grid controls spacing: 1/8 = coarser, 1/32 = finer; T = triplets. Blank source BPM keeps the original overall tempo.", style="PanelMuted.TLabel", wraplength=810).grid(row=3, column=0, columnspan=4, sticky="w", pady=(9, 13))
        ttk.Label(settings, text="Cut detection", style="Section.TLabel").grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 8))
        ttk.Label(settings, text="Sensitivity", style="Panel.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 12))
        sensitivity_frame = ttk.Frame(settings, style="Panel.TFrame")
        sensitivity_frame.grid(row=5, column=1, sticky="ew")
        sensitivity_frame.columnconfigure(0, weight=1)
        scale = ttk.Scale(sensitivity_frame, from_=1, to=100, variable=self.sensitivity_var, command=lambda v: self.sensitivity_label.set(f"{float(v):.0f}%"))
        scale.grid(row=0, column=0, sticky="ew")
        ttk.Label(sensitivity_frame, textvariable=self.sensitivity_label, style="Panel.TLabel", width=5, anchor="e").grid(row=0, column=1, padx=(8, 0))
        self.editable.append(scale)
        self._field(settings, 5, 2, "Minimum slice (ms)", self.slice_var)
        ttk.Label(settings, text="Higher sensitivity finds more attacks. Detection follows sound, so cuts may be syllables rather than complete words.", style="PanelMuted.TLabel", wraplength=810).grid(row=6, column=0, columnspan=4, sticky="w", pady=(9, 8))
        slices_check = ttk.Checkbutton(settings, text="Also export individual slices", variable=self.slices_var)
        slices_check.grid(row=7, column=0, columnspan=4, sticky="w")
        self.editable.append(slices_check)

        sections = ttk.Frame(notebook, style="Panel.TFrame", padding=16)
        notebook.add(sections, text="Section placement")
        sections.columnconfigure(1, weight=1)
        section_check = ttk.Checkbutton(sections, text="Arrange vocal sections on bar blocks", variable=self.section_mode_var)
        section_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self.editable.append(section_check)
        ttk.Label(sections, text="Block size", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 16))
        section_combo = ttk.Combobox(sections, textvariable=self.section_block_var, values=("1 bar", "2 bars", "4 bars"), width=17, state="readonly")
        section_combo.grid(row=1, column=1, sticky="ew")
        self.section_widgets.append(section_combo)
        self.editable.append(section_combo)
        self.section_widgets.append(self._field(sections, 2, 0, "New section after silence (beats)", self.section_gap_var))
        first_bar_entry = self._field(sections, 3, 0, "First section bar (earliest)", self.start_bar_var)
        first_bar_entry.grid_configure(pady=(8, 0))
        self.section_widgets.append(first_bar_entry)
        ttk.Label(sections, text="Uses 4/4 bars. With 2-bar blocks, a 3-bar section reserves 4 bars; starting at FL bar 2 puts the next section at bar 6. A 4-bar section also puts the next at bar 6.", style="PanelMuted.TLabel", wraplength=810).grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 8))
        ttk.Label(sections, text="Earliest bar 2 keeps section anchors on even bar numbers. Vocal pickups stay attached; the first anchor may move later by whole blocks so none are cut. Blocks add silence, not stretching.", style="PanelMuted.TLabel", wraplength=810).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(sections, text="Quiet gaps define sections; verse and chorus names are not detected. Turn this off to keep section positions on the original timeline.", style="PanelMuted.TLabel", wraplength=810).grid(row=6, column=0, columnspan=2, sticky="w")
        for variable in (self.section_mode_var, self.section_block_var, self.section_gap_var, self.start_bar_var):
            variable.trace_add("write", self._section_settings_changed)
        self._section_settings_changed()

        ttk.Label(outer, textvariable=self.section_summary_var, style="Muted.TLabel", wraplength=850).grid(row=3, column=0, sticky="w", pady=(0, 10))
        ttk.Label(outer, textvariable=self.status_var, style="Badge.TLabel", wraplength=850).grid(row=4, column=0, sticky="w", pady=(0, 7))

        log_frame = ttk.Frame(outer)
        log_frame.grid(row=5, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=4, wrap="word", bg="#0b111b", fg=MUTED, font=("Segoe UI", 9), relief="flat", borderwidth=0, padx=12, pady=10, state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)
        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.progress.grid(row=6, column=0, sticky="ew", pady=(9, 12))

        footer = ttk.Frame(outer)
        footer.grid(row=7, column=0, sticky="ew")
        footer.columnconfigure(2, weight=1)
        self.open_button = ttk.Button(footer, text="Open exports", command=self._open_output, state="disabled")
        self.open_button.grid(row=0, column=0, padx=(0, 8))
        self.play_button = ttk.Button(footer, text="Play snapped + click", command=self._play_comparison, state="disabled")
        self.play_button.grid(row=0, column=1)
        self.cancel_button = ttk.Button(footer, text="Cancel", command=self._cancel, state="disabled")
        self.cancel_button.grid(row=0, column=3, padx=(12, 8))
        self.start_button = ttk.Button(footer, text="Snap vocal", style="Primary.TButton", command=self._start)
        self.start_button.grid(row=0, column=4)
        self._log("The snap strength is always 100%. BPM sets the tempo; the grid sets where each detected attack can land.")

    def _field(self, parent, row, col, label, variable):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=col, sticky="w", padx=(22 if col else 0, 12), pady=(8 if row == 2 else 0, 0))
        entry = ttk.Entry(parent, textvariable=variable, width=18)
        entry.grid(row=row, column=col + 1, sticky="ew", pady=(8 if row == 2 else 0, 0))
        self.editable.append(entry)
        return entry

    def _section_settings_changed(self, *_args):
        enabled = self.section_mode_var.get()
        for widget in self.section_widgets:
            widget.configure(state="disabled" if self.running or not enabled else ("readonly" if isinstance(widget, ttk.Combobox) else "normal"))
        if enabled:
            self.section_summary_var.set(f"Section placement ON · {self.section_block_var.get()} per block · earliest first FL bar {self.start_bar_var.get() or '?'} · silence threshold {self.section_gap_var.get() or '?'} beats")
        else:
            self.section_summary_var.set("Section placement OFF · keep the original section positions and snap individual attacks.")

    def _choose_input(self):
        path = filedialog.askopenfilename(title="Choose an isolated vocal stem", filetypes=[("Audio files", "*.wav *.flac *.aif *.aiff *.ogg *.mp3 *.m4a"), ("All files", "*.*")])
        if path:
            self.input_var.set(path)
            self._update_output_default()

    def _update_output_default(self):
        raw = self.input_var.get().strip().strip('"')
        if raw and (not self.output_var.get().strip() or self.output_var.get() == self.last_default_output):
            self.last_default_output = str(Path(raw).expanduser().resolve().parent / "Vocal Grid Snap Exports")
            self.output_var.set(self.last_default_output)

    def _choose_output(self):
        current = self.output_var.get().strip()
        folder = filedialog.askdirectory(title="Choose the parent folder for exports", initialdir=current if Path(current).is_dir() else None)
        if folder:
            self.output_var.set(folder)

    @staticmethod
    def _number(raw, label, positive=False):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"Enter a number for {label}.") from None
        if not math.isfinite(value) or (positive and value <= 0):
            raise ValueError(f"{label} must be a {'positive ' if positive else ''}finite number.")
        return value

    def _whole_number(self, raw, label):
        value = self._number(raw, label, positive=True)
        if not value.is_integer():
            raise ValueError(f"{label} must be a whole number.")
        return int(value)

    def _diagnostic_settings(self):
        settings = {}
        for name in ("bpm", "grid", "sensitivity", "slice", "offset", "source_bpm", "slices", "section_mode", "section_block", "section_gap", "start_bar"):
            try:
                settings[name] = getattr(self, f"{name}_var").get()
            except Exception:
                settings[name] = "<unavailable>"
        return settings

    def _callback_error(self, exc_type, exc, tb):
        report = save_error_report(
            "Interface callback", exc,
            input_path=self.input_var.get(), output_path=self.output_var.get(),
            config=self._diagnostic_settings(),
            trace_text="".join(traceback.format_exception(exc_type, exc, tb)),
        )
        message = error_message(exc, report)
        try:
            self._log(message)
            messagebox.showerror("Vocal Grid Snap", message, parent=self.root)
        except Exception:
            show_native_error(message)

    def _start(self):
        if self.running:
            return
        try:
            from vocal_engine import SnapConfig
            raw_input = self.input_var.get().strip().strip('"')
            if not raw_input:
                raise ValueError("Choose an isolated vocal file first.")
            input_path = Path(raw_input).expanduser().resolve()
            if not input_path.is_file():
                raise ValueError("The selected vocal file could not be found.")
            self._update_output_default()
            output_raw = self.output_var.get().strip().strip('"')
            if not output_raw:
                raise ValueError("Choose a folder for the exports.")
            output_path = Path(output_raw).expanduser().resolve()
            if output_path.exists() and not output_path.is_dir():
                raise ValueError("The export destination must be a folder.")
            source = self.source_bpm_var.get().strip()
            config = SnapConfig(
                bpm=self._number(self.bpm_var.get(), "Target BPM", positive=True),
                grid=self.grid_var.get(),
                sensitivity=self.sensitivity_var.get() / 100.0,
                min_slice_ms=self._number(self.slice_var.get(), "Minimum slice", positive=True),
                offset_ms=self._number(self.offset_var.get(), "Beat offset"),
                source_bpm=self._number(source, "Source BPM", positive=True) if source else None,
                export_slices=self.slices_var.get(),
                section_mode="blocks" if self.section_mode_var.get() else "off",
                section_gap_beats=self._number(self.section_gap_var.get(), "Silence between sections", positive=True) if self.section_mode_var.get() else 2.0,
                section_block_bars={"1 bar": 1, "2 bars": 2, "4 bars": 4}[self.section_block_var.get()],
                start_bar=self._whole_number(self.start_bar_var.get(), "First section bar") if self.section_mode_var.get() else 1,
            )
            config.validate()
        except Exception as exc:
            report = save_error_report(
                "Validate settings / prepare run", exc,
                input_path=self.input_var.get(), output_path=self.output_var.get(),
                config=self._diagnostic_settings(),
            )
            message = error_message(exc, report)
            self._log(message)
            messagebox.showerror("Check the settings", message, parent=self.root)
            return
        self.cancel_event = threading.Event()
        self.result = None
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._log(f"Input: {input_path.name}")
        self._log(f"Target: {config.bpm:g} BPM • {config.grid} grid • 100% snap")
        self._log(self.section_summary_var.get())
        self.status_var.set("Working — finding vocal attacks and moving them onto the grid…")
        self._set_running(True)
        threading.Thread(target=self._worker, args=(input_path, output_path, config), daemon=True).start()

    def _worker(self, input_path, output_path, config):
        try:
            from vocal_engine import process
            result = process(str(input_path), str(output_path), config, progress=lambda message: self.events.put(("progress", str(message))), cancel_event=self.cancel_event)
            self.events.put(("done", result))
        except Exception as exc:
            if self.cancel_event.is_set() and isinstance(exc, RuntimeError) and str(exc) == "Cancelled":
                self.events.put(("cancelled", str(exc)))
            else:
                report = save_error_report("Process vocal", exc, input_path=input_path, output_path=output_path, config=config)
                self.events.put(("error", error_message(exc, report)))

    def _set_running(self, running):
        self.running = running
        for widget in self.editable:
            widget.configure(state="disabled" if running else ("readonly" if isinstance(widget, ttk.Combobox) else "normal"))
        self._section_settings_changed()
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")
        self.open_button.configure(state="normal" if self.result and not running else "disabled")
        self.play_button.configure(state="normal" if self.result and not running else "disabled")
        if running:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _poll(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    self._log(payload)
                elif kind == "done":
                    self.result = payload
                    self._set_running(False)
                    slices = payload.get("slices", "?")
                    if isinstance(slices, (list, tuple)):
                        slices = len(slices)
                    shift = payload.get("max_shift_ms")
                    suffix = f" • largest syllable move {shift:.0f} ms" if isinstance(shift, (int, float)) else ""
                    section_count = payload.get("sections", 0)
                    section_text = f" · {section_count} sections placed" if section_count else ""
                    self.status_var.set(f"Done — {slices} slices snapped{section_text}{suffix}.")
                    self._log(f"Saved to: {payload['output_dir']}")
                    for warning in payload.get("warnings", []):
                        self._log(f"Note: {warning}")
                    self._log("Play snapped + click to check the rhythm. In FL Studio, set the target BPM and place the snapped vocal at the project start.")
                elif kind == "cancelled":
                    self._set_running(False)
                    self.status_var.set("Cancelled — ready for another run.")
                    self._log("Processing cancelled.")
                elif kind == "error":
                    self._set_running(False)
                    self.status_var.set("Could not finish — see the message below.")
                    self._log(payload)
                    messagebox.showerror("Vocal Grid Snap", payload, parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", str(message) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _cancel(self):
        if self.running:
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self.status_var.set("Cancelling — finishing the current step…")

    def _open(self, path):
        try:
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror("Could not open the export", str(exc), parent=self.root)

    def _open_output(self):
        if self.result:
            self._open(self.result["output_dir"])

    def _play_comparison(self):
        if self.result:
            self._open(self.result["comparison_path"])

    def _close(self):
        if self.running:
            if not messagebox.askyesno("Stop processing?", "A vocal is still processing. Stop this run and close?", parent=self.root):
                return
            self.cancel_event.set()
        self.root.destroy()


def main():
    # Keep Windows display scaling crisp; failure just uses Tk's default scaling.
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    VocalGridSnapApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report = save_error_report("Start application", exc)
        show_native_error(error_message(exc, report))
        raise SystemExit(1) from exc
