# Vocal Grid Snap

Hard vocal timing for FL Studio: detect acoustic attacks, cut an isolated vocal into syllable-like slices and align them to a chosen rhythm grid. Optional section placement keeps phrase starts on regular bar boundaries.

## Run from source (Windows)

Install Python 3.13 with Tkinter and the Windows Python launcher, then run in this folder:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe vocal_grid_snap.py
```

After setup, `Start.bat` uses the local `.venv`. See [USER_GUIDE.md](USER_GUIDE.md) for controls and workflow.

Install the external audio tools described in [tools/INSTALL.md](tools/INSTALL.md). This is a small source checkout; no model weights, audio files or Python runtime are included.

## Source and distribution

This repository contains editable application source. Generated exports, private settings, API keys, user audio, bundled runtimes and packaged executables are excluded. Original local releases remain separate. No new license is granted for original application code in this publication; dependency notices retain their own terms.
