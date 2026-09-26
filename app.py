from datetime import datetime, date
from collections import defaultdict

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config, BASE_DIR
from models import db, User, Income, Expense, EXPENSE_CATEGORIES
import ai_service

import os

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access your dashboard."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_budget(income_total):
    """50/30/20-style split adapted to the project brief's needs/wants/savings/emergency model."""
    return {
        "needs": round(income_total * 0.50, 2),
        "wants": round(income_total * 0.20, 2),
        "savings": round(income_total * 0.20, 2),
        "emergency": round(income_total * 0.10, 2),
    }


def get_financial_summary(user_id):
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    income_total = sum(i.amount for i in incomes)
    expense_total = sum(e.amount for e in expenses)
    savings = income_total - expense_total

    category_totals = defaultdict(float)
    for e in expenses:
        category_totals[e.category] += e.amount

    return {
        "incomes": incomes,
        "expenses": expenses,
        "income_total": income_total,
        "expense_total": expense_total,
        "savings": savings,
        "category_totals": dict(category_totals),
        "max_category_total": max(category_totals.values()) if category_totals else 0,
        "budget": compute_budget(income_total),
    }


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created. Welcome!", "success")
            return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Core app routes
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    summary = get_financial_summary(current_user.id)
    recommendation = ai_service.get_recommendation(
        summary["income_total"],
        summary["expense_total"],
        summary["savings"],
        summary["category_totals"],
    )
    return render_template("dashboard.html", summary=summary, recommendation=recommendation)


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount = request.form.get("amount", "")
        entry_date = request.form.get("date") or date.today().isoformat()

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid positive amount.", "error")
            return redirect(url_for("income"))

        if not source:
            flash("Please provide an income source.", "error")
            return redirect(url_for("income"))

        db.session.add(Income(
            user_id=current_user.id,
            source=source,
            amount=amount_val,
            date=datetime.strptime(entry_date, "%Y-%m-%d").date(),
        ))
        db.session.commit()
        flash("Income added.", "success")
        return redirect(url_for("income"))

    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    total = sum(i.amount for i in incomes)
    return render_template("income.html", incomes=incomes, total=total, today=date.today().isoformat())


@app.route("/income/<int:income_id>/delete", methods=["POST"])
@login_required
def delete_income(income_id):
    entry = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Income entry removed.", "info")
    return redirect(url_for("income"))


@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        category = request.form.get("category", "")
        amount = request.form.get("amount", "")
        description = request.form.get("description", "").strip()
        entry_date = request.form.get("date") or date.today().isoformat()

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid positive amount.", "error")
            return redirect(url_for("expense"))

        if category not in EXPENSE_CATEGORIES:
            flash("Please choose a valid category.", "error")
            return redirect(url_for("expense"))

        db.session.add(Expense(
            user_id=current_user.id,
            category=category,
            amount=amount_val,
            description=description,
            date=datetime.strptime(entry_date, "%Y-%m-%d").date(),
        ))
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for("expense"))

    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)
    return render_template(
        "expense.html",
        expenses=expenses,
        total=total,
        categories=EXPENSE_CATEGORIES,
        today=date.today().isoformat(),
    )


@app.route("/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    entry = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Expense entry removed.", "info")
    return redirect(url_for("expense"))


@app.route("/budget")
@login_required
def budget():
    summary = get_financial_summary(current_user.id)
    return render_template("budget.html", summary=summary)


@app.route("/report")
@login_required
def report():
    summary = get_financial_summary(current_user.id)
    recommendation = ai_service.get_recommendation(
        summary["income_total"],
        summary["expense_total"],
        summary["savings"],
        summary["category_totals"],
    )
    return render_template(
        "report.html",
        summary=summary,
        recommendation=recommendation,
        generated_on=date.today().strftime("%d %B %Y"),
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
