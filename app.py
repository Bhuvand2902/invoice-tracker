from pathlib import Path
import sqlite3

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DATABASE = Path(__file__).with_name("invoices.db")


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


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

        # Add this column to the database you already created.
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
    if request.method == "POST":
        customer = request.form["customer"].strip()
        amount = request.form["amount"]
        due_date = request.form["due_date"]

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

    return render_template("index.html", invoices=invoices)


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