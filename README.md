# Personal Finance Advisor Bot

An AI-powered personal finance web app built with Flask. Users track income
and expenses, get an automatic 50/20/20/10 budget split, see spending
analytics, and receive AI-generated (or rule-based fallback) budgeting
recommendations.

## Features

- Registration / login / logout with hashed passwords (Flask-Login)
- Per-user income and expense tracking with categories
- Auto-calculated budget (needs / wants / savings / emergency fund)
- Spending-by-category chart on the dashboard
- AI recommendations via Google Gemini, with a built-in rule-based
  fallback so the app always works, even without an API key
- Printable monthly financial report

## Project structure

```
finance-bot/
├── app.py              # Routes and app factory
├── config.py           # Config from environment variables
├── models.py           # SQLAlchemy models: User, Income, Expense
├── ai_service.py        # Gemini call + rule-based fallback
├── requirements.txt
├── .env.example
├── templates/           # Jinja2 templates
├── static/css/style.css
├── static/js/script.js
└── database/             # SQLite file created at first run
```

## Setup

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set a `SECRET_KEY`. Add a `GEMINI_API_KEY` if you want
   live AI recommendations — get one free at https://aistudio.google.com/apikey.
   Leaving it blank still works: the app falls back to rule-based advice.

4. **Run the app**
   ```bash
   python app.py
   ```
   The database (`database/finance.db`) is created automatically on first
   run. Visit http://127.0.0.1:5000, register an account, and start adding
   income and expenses.

## Optional: public demo link with ngrok

```bash
# in a second terminal, while app.py is running
ngrok http 5000
```
Ngrok prints a public URL that forwards to your local Flask app — useful for
demoing the project to someone else without deploying it.

## Testing checklist

- [ ] Register, log in, log out
- [ ] Wrong password is rejected
- [ ] `/dashboard`, `/income`, `/expense`, `/budget`, `/report` require login
- [ ] Income and expense entries save, appear in tables, and can be deleted
- [ ] Dashboard totals and chart update after adding entries
- [ ] AI recommendation text changes based on income/expenses
- [ ] Report page prints cleanly (`window.print()` button)

## Notes

- SQLite is used by default; set `DATABASE_URL` in `.env` to point at
  PostgreSQL for a deployment-oriented setup.
- AI recommendations are general educational guidance, not a substitute
  for a licensed financial adviser — this is stated in the UI as well.
