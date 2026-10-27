from contextlib import contextmanager
from datetime import date, datetime
import math
from pathlib import Path
import sqlite3

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DATABASE = Path(__file__).with_name("invoices.db")


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                amount REAL NOT NULL,
                due_date TEXT NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 0
            )
        """)

        columns = connection.execute(
            "PRAGMA table_info(invoices)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        if "is_paid" not in column_names:
            connection.execute("""
                ALTER TABLE invoices
                ADD COLUMN is_paid INTEGER NOT NULL DEFAULT 0
            """)


@app.route("/", methods=["GET", "POST"])
def home():
    errors = []

    if request.method == "POST":
        customer = request.form.get("customer", "").strip()
        amount_text = request.form.get("amount", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not customer:
            errors.append("Enter a customer name.")

        try:
            amount = float(amount_text)
            if not math.isfinite(amount) or amount <= 0:
                errors.append("Amount must be a valid number greater than zero.")
        except ValueError:
            amount = 0
            errors.append("Enter a valid amount.")

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Enter a valid due date.")

        if not errors:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO invoices (customer, amount, due_date)
                    VALUES (?, ?, ?)
                    """,
                    (customer, amount, due_date)
                )

            return redirect(url_for("home"))

    with get_connection() as connection:
        invoices = connection.execute(
            "SELECT * FROM invoices ORDER BY id DESC"
        ).fetchall()

    today = date.today().isoformat()

    paid_total = sum(
        float(invoice["amount"])
        for invoice in invoices
        if invoice["is_paid"]
    )

    unpaid_total = sum(
        float(invoice["amount"])
        for invoice in invoices
        if not invoice["is_paid"] and invoice["due_date"] >= today
    )

    overdue_total = sum(
        float(invoice["amount"])
        for invoice in invoices
        if not invoice["is_paid"] and invoice["due_date"] < today
    )

    return render_template(
        "index.html",
        invoices=invoices,
        today=today,
        paid_total=paid_total,
        unpaid_total=unpaid_total,
        overdue_total=overdue_total,
        errors=errors
    )


@app.route("/mark-paid/<int:invoice_id>", methods=["POST"])
def mark_paid(invoice_id):
    with get_connection() as connection:
        connection.execute(
            "UPDATE invoices SET is_paid = 1 WHERE id = ?",
            (invoice_id,)
        )

    return redirect(url_for("home"))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)