# Calendar

Calendar website for 362.

## 1) What You Need

- Git installed
- Python 3.12+
d
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

### Core Git concepts (quick guide)

- Branch: an isolated line of work (for one feature, bug fix, or task).
- Commit: a saved snapshot of your staged changes with a message explaining why the change was made.
- Pull: gets remote commits into your local branch.
- Pull Request (PR): a GitHub review/merge workflow for moving one branch into another (usually into `main`).

### Pulling from `main` vs using Pull Requests

- `git pull origin main` updates your local `main` branch with the latest commits from the remote repository.
- A Pull Request does not update your local branch by itself. A PR is a review conversation plus a merge action on GitHub.
- Typical flow:
1. You pull latest `main` locally.
2. You create a feature branch and commit work there.
3. You push that branch and open a PR.
4. After review/approval, the PR is merged into `main`.
5. Everyone pulls `main` again locally to get merged changes.

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

Branch naming tips:

- Use prefixes like `feature/`, `fix/`, `docs/`, `refactor/`.
- Keep names short and specific, for example: `feature/event-edit-script`.

### Save your changes

What a commit is:

- A commit is a checkpoint in project history.
- Good commits are small, focused, and have clear messages.
- Commit only related changes together (do not mix unrelated edits).

```bash
git add .
git commit -m "Short clear message about what changed"
```

Commit message examples:

- `Add Event.remove integration test script`
- `Update README with VS Code Git workflow`
- `Fix event edit script to target first Supabase row`

If you use VS Code UI instead of terminal:

- Open Source Control (`Ctrl+Shift+G`).
- Stage files with `+`.
- Enter a commit message.
- Click `Commit`.

### Push your branch

```bash
git push -u origin feature/short-description
```

Then open GitHub and create a Pull Request (PR).

If you use VS Code with `github.vscode-pull-request-github`:

- Open the GitHub Pull Requests view.
- Click `Create Pull Request`.
- Set base branch to `main` and compare branch to your feature branch.
- Add title/description and submit.

### Keep your branch updated while PR is open

```bash
git checkout main
git pull origin main
git checkout feature/short-description
git merge main
```

If there are merge conflicts, resolve them, then commit and push again.

### Branch workflow in VS Code (no terminal)

1. Click the branch name in the bottom-left status bar.
2. Choose `Create new branch...` from `main`.
3. Make changes, then open Source Control and commit.
4. Click `Publish Branch`.
5. Create PR from the Pull Requests view.
6. After PR merge, switch to `main` and click `Sync Changes` (or pull).

## 9) Important Notes

- Do not upload `.venv` to GitHub (ignored by `.gitignore`).
- Do not commit secrets or API keys.
- Keep commits small and focused so we can review easily.