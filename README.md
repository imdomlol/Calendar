# Calendar

Calendar website for 362.

## 1) What You Need

- Git installed
- Python 3.12+

## 2) Get the Project on Your Computer

### Option A: You have write access to this repository

```bash
git clone https://github.com/imdomlol/Calendar.git
cd Calendar
```

### Option B: You do NOT have write access

1. Fork this repository in GitHub (top-right "Fork" button).
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/Calendar.git
cd Calendar
```

3. Add the original repository as `upstream`:

```bash
git remote add upstream https://github.com/imdomlol/Calendar.git
```

## 3) Create and Activate a Virtual Environment

Run this from the project root.

### Create

```bash
python3 -m venv .venv
```

If your machine uses `python` instead of `python3`, use `python -m venv .venv`.

### Activate

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows (Command Prompt):

```bat
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

You should now see `(.venv)` at the beginning of your terminal prompt.

## 4) Install Dependencies

With `.venv` activated:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## 5) Set Environment Variables (Required)

This project expects:

- `SUPABASE_URL`
- `SUPABASE_KEY`

macOS/Linux:

```bash
export SUPABASE_URL="https://brdvyxxaclhceucmcioq.supabase.co"
export SUPABASE_KEY="SUPABASE_API_KEY"
```

Windows (PowerShell):

```powershell
$env:SUPABASE_URL="https://brdvyxxaclhceucmcioq.supabase.co"
$env:SUPABASE_KEY="SUPABASE_API_KEY"
```

## 6) Quick Local Check

Confirm your environment variables and package setup are working:

```bash
python api/index.py
```

If successful, you should see:

```text
Supabase client initialized successfully
```

## 7) Daily Workflow (Every Time You Come Back)

```bash
cd Calendar
source .venv/bin/activate
```

Then run your normal commands (`python ...`, `pip ...`, `git ...`).

## 8) Team Git Workflow

### Start new work

1. Make sure you are on `main`:

```bash
git checkout main
```

2. Pull latest changes:

```bash
git pull origin main
```

3. Create a new branch for your task:

```bash
git checkout -b feature/short-description
```

### Save your changes

```bash
git add .
git commit -m "Short clear message about what changed"
```

### Push your branch

```bash
git push -u origin feature/short-description
```

Then open GitHub and create a Pull Request (PR).

### Keep your branch updated while PR is open

```bash
git checkout main
git pull origin main
git checkout feature/short-description
git merge main
```

If there are merge conflicts, resolve them, then commit and push again.

## 9) Important Notes

- Do not upload `.venv` to GitHub (ignored by `.gitignore`).
- Do not commit secrets or API keys.
- Keep commits small and focused so we can review easily.