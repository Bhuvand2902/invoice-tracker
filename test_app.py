import tempfile
import unittest
from pathlib import Path

import app as invoice_app


class InvoiceTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database = invoice_app.DATABASE

        invoice_app.DATABASE = Path(self.temp_dir.name) / "test_invoices.db"
        invoice_app.create_table()

        self.client = invoice_app.app.test_client()

    def tearDown(self):
        invoice_app.DATABASE = self.original_database
        self.temp_dir.cleanup()

    def test_home_page_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invoice Tracker", response.data)

    def test_add_invoice(self):
        response = self.client.post(
            "/",
            data={
                "customer": "Sample Customer",
                "amount": "100",
                "due_date": "2026-10-28",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sample Customer", response.data)
        self.assertIn(b"Unpaid total: 100.00", response.data)

    def test_mark_invoice_paid(self):
        self.client.post(
            "/",
            data={
                "customer": "Sample Customer",
                "amount": "100",
                "due_date": "2026-10-28",
            },
        )

        response = self.client.post(
            "/mark-paid/1",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Paid total: 100.00", response.data)


if __name__ == "__main__":
    unittest.main()