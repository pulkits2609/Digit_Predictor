# Live integration verification

Start the trained backend on `127.0.0.1:8000` and the Vite frontend on `127.0.0.1:5173` first. From the repository root in PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r qa/requirements.txt
.\backend\.venv\Scripts\python.exe qa/verify_live.py backend/models/samples/digit-7.png
.\backend\.venv\Scripts\python.exe qa/browser_smoke.py
```

The browser test uses an installed Microsoft Edge browser through Playwright. It tests actual mouse drawing, undo/redo/clear, upload, real CNN responses, all ten scores, processed preview, simulated network failure and recovery, offline bundled model artifacts, responsive widths, browser exceptions, and emulated Chromium touch drawing. It does not replace testing on physical iOS/Android hardware or Firefox/Safari. The digit itself is deliberately not asserted for arbitrary drawn strokes; displayed output must match the genuine API response.

`verify_live.py` needs only Python's standard library and accepts another input PNG and `--base-url`.
