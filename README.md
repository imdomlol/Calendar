# Calendar

Calendar website for 362.

## If You Are New to Python Projects

This project uses a **virtual environment** (`.venv`).

Think of `.venv` as a private Python box for this project only. It keeps this project's packages separate from other projects on your computer.

## What You Need First

- Python 3.12 or newer

## First-Time Setup (Everyone)

Open a terminal in the project folder, then run:

```bash
python -m venv .venv
```

If `python` does not work on your machine, try `python3` (Linux/macOS) or `py` (Windows).

## Activate the Virtual Environment

### Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
source .venv/bin/activate
```

When activated, your terminal usually shows `(.venv)` at the beginning.

## Install Dependencies

With the virtual environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Set Required Environment Variables

This API needs:

- `SUPABASE_URL`
- `SUPABASE_KEY`

### macOS / Linux

```bash
export SUPABASE_URL="https://OUR_LINK.supabase.co"
export SUPABASE_KEY="OUR_SUPABASE_KEY"
```

### Windows (PowerShell)

```powershell
$env:SUPABASE_URL="https://OUR_PROJECT.supabase.co"
$env:SUPABASE_KEY="OUR_SUPABASE_KEY"
```

## Run the API File

```bash
python api/index.py
```

## Every Time You Come Back to the Project

1. Open terminal in this project folder.
2. Activate `.venv` (using the command for your OS above).
3. Run your commands (`python ...`, `pip ...`, etc.).

## Why Not Install Packages Globally

Global installs can cause version conflicts between projects.
Using `.venv` avoids that and makes setup consistent for everyone.

## Quick Troubleshooting

- **`ModuleNotFoundError`**: your `.venv` is probably not active, or dependencies were not installed yet.
