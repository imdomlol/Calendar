# Calendar
## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth, Flask sessions |
| External Calendars | Google Calendar API, Microsoft Graph (MSAL) |
| Templates | Jinja2 |
| Deployment | Vercel (serverless Python) |

## System Requirements

- Python 3.12 or later
- Git

## Testing

Since we have developed a web app, installing and running on your own device is not recommended, as you would need access to all the necessary environmental variables.

Here is the link to the web app: https://calendar-dominic-dionnes-projects-772c74d2.vercel.app/

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/imdomlol/Calendar.git
cd Calendar
```

**2. Create and activate a virtual environment**

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**4. Set environment variables**

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `SUPABASE_SECRET_API_KEY` | Service role key (used by logger to bypass RLS) |
| `FLASK_SECRET_KEY` | Session signing key |
| `APP_BASE_URL` | Full base URL for OAuth redirects (e.g. `http://localhost:5000`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Required for Google Calendar OAuth |
| `MS_CLIENT_ID` / `MS_CLIENT_SECRET` | Required for Outlook integration |
| `CRON_SECRET` | Bearer secret for the Vercel subscription renewal cron |
| `RESEND_API_KEY` | Resend transactional email API key |

**5. Run the development server**

```bash
flask --app api/index.py run
```

The app will be available at `http://localhost:5000`.

## Team Members

- Charlize Manuel
- Dominic Dionne
- Hector Banda
- Nathan Flandez
- Owen Polaschek
- Eric Kiyamu
