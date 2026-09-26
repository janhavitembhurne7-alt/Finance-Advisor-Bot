"""
AI-powered financial recommendation service.

Uses Google Gemini when GEMINI_API_KEY is configured. Falls back to a
rule-based recommendation engine when no key is present, or if the API
call fails for any reason, so the app always returns something useful.
"""
import os


def _rule_based_recommendation(income, expenses, savings, category_totals):
    tips = []

    if income <= 0:
        return "Add your income first so I can generate personalized budgeting advice."

    savings_rate = (savings / income) * 100 if income else 0

    if savings_rate < 10:
        tips.append(
            "Your savings rate is below 10% of income. Try to save at least "
            "10-20% each month, even if it's a small fixed amount."
        )
    elif savings_rate >= 20:
        tips.append(
            f"Great job — you're saving about {savings_rate:.0f}% of your income. "
            "Consider directing part of this toward an emergency fund or long-term goals."
        )
    else:
        tips.append(f"You're saving around {savings_rate:.0f}% of your income. A 20% target is a solid next step.")

    if category_totals:
        top_category, top_amount = max(category_totals.items(), key=lambda kv: kv[1])
        share = (top_amount / expenses * 100) if expenses else 0
        if share > 30:
            tips.append(
                f"{top_category} makes up about {share:.0f}% of your spending. "
                f"Setting a monthly cap on {top_category.lower()} could free up extra savings."
            )

    if expenses > income:
        tips.append(
            "Your expenses currently exceed your income. Review non-essential categories "
            "first and look for quick wins before cutting essentials."
        )

    tips.append("Keep 3-6 months of expenses in an emergency fund if you don't have one yet.")

    return " ".join(tips)


def _gemini_recommendation(api_key, income, expenses, savings, category_totals):
    import requests

    breakdown = ", ".join(f"{cat}: ₹{amt:.0f}" for cat, amt in category_totals.items()) or "No expenses recorded yet"

    prompt = (
        "You are a personal finance assistant. Based on this user's monthly financial data, "
        "give 3-4 short, practical budgeting and saving suggestions in plain language. "
        "Do not give investment or tax advice, and note this is general educational guidance only.\n\n"
        f"Monthly income: ₹{income:.0f}\n"
        f"Monthly expenses: ₹{expenses:.0f}\n"
        f"Monthly savings: ₹{savings:.0f}\n"
        f"Expense breakdown: {breakdown}\n"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def get_recommendation(income, expenses, savings, category_totals):
    """
    Returns an AI-generated (or rule-based fallback) financial recommendation string.
    category_totals: dict of {category_name: total_amount}
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if api_key:
        try:
            return _gemini_recommendation(api_key, income, expenses, savings, category_totals)
        except Exception:
            # Fall back silently so the dashboard always shows something useful.
            pass

    return _rule_based_recommendation(income, expenses, savings, category_totals)
