"""
ERP Connector
Integrates with ERP/GL systems (SAP, Oracle, Tally, Zoho Books)
to pull actuals, budgets, journal entries, and AP/AR data.
"""

import os
import httpx
from loguru import logger


class ERPConnector:
    """
    Generic ERP connector that supports REST-based ERP APIs.
    Provides standardised data access regardless of underlying ERP system.

    Supported: SAP S/4HANA · Oracle Fusion · Zoho Books · Tally Prime
    """

    BASE_URL = os.getenv("ERP_API_BASE_URL", "https://demo-erp.cfoos.local/api")

    def __init__(self):
        self.api_key      = os.getenv("ERP_API_KEY", "demo_key")
        self.company_code = os.getenv("ERP_COMPANY_CODE", "COMP001")
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "X-Company-Code": self.company_code,
            "Content-Type": "application/json"
        }
        logger.info(f"ERPConnector initialised for company {self.company_code}")

    def get_actuals(self, period: str, gl_accounts: list[str] = None) -> dict:
        """
        Fetch actual financial data from the GL for a given period.
        period: '2024-Q1' | '2024-03' | 'YTD'
        """
        try:
            params = {"period": period, "company_code": self.company_code}
            if gl_accounts:
                params["gl_accounts"] = ",".join(gl_accounts)

            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/gl/actuals",
                    headers=self.headers, params=params
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"ERP actuals API error ({e}). Using demo data.")
            return self._demo_actuals(period)

    def get_budget(self, period: str) -> dict:
        """Fetch approved budget from ERP for the given period."""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/budget",
                    headers=self.headers,
                    params={"period": period}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"ERP budget API error ({e}). Using demo data.")
            return self._demo_budget(period)

    def get_gl_entries(self, from_date: str, to_date: str) -> list[dict]:
        """Fetch journal entries from GL for reconciliation."""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/gl/journal-entries",
                    headers=self.headers,
                    params={"from_date": from_date, "to_date": to_date, "page_size": 500}
                )
                resp.raise_for_status()
                return resp.json().get("entries", [])
        except Exception as e:
            logger.warning(f"GL entries API error ({e}). Returning empty list.")
            return self._demo_gl_entries()

    def get_accounts_payable(self, aging_bucket: str = "all") -> list[dict]:
        """Fetch accounts payable with aging buckets."""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/ap/aging",
                    headers=self.headers,
                    params={"bucket": aging_bucket}
                )
                resp.raise_for_status()
                return resp.json().get("payables", [])
        except Exception:
            return self._demo_ap()

    def get_accounts_receivable(self) -> list[dict]:
        """Fetch accounts receivable with collection status."""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(f"{self.BASE_URL}/ar/outstanding", headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("receivables", [])
        except Exception:
            return []

    # ── Demo Data ─────────────────────────────────────────────────────────

    def _demo_actuals(self, period: str) -> dict:
        return {
            "period": period,
            "currency": "INR",
            "revenue":             45_200_000,
            "cost_of_goods_sold":  18_100_000,
            "gross_profit":        27_100_000,
            "salaries":            12_400_000,
            "marketing":            3_800_000,
            "travel":               2_100_000,
            "software_saas":        1_560_000,
            "rent_utilities":       2_200_000,
            "miscellaneous":          980_000,
            "ebitda":               4_060_000,
        }

    def _demo_budget(self, period: str) -> dict:
        return {
            "period": period,
            "currency": "INR",
            "revenue":             50_000_000,
            "cost_of_goods_sold":  19_000_000,
            "gross_profit":        31_000_000,
            "salaries":            12_000_000,
            "marketing":            3_500_000,
            "travel":               1_800_000,
            "software_saas":        1_400_000,
            "rent_utilities":       2_200_000,
            "miscellaneous":          800_000,
            "ebitda":               9_300_000,
        }

    def _demo_gl_entries(self) -> list[dict]:
        import random
        entries = []
        for i in range(150):
            entries.append({
                "entry_id": f"JE{10000 + i}",
                "debit_account": f"AC{random.randint(1000, 9999)}",
                "credit_account": f"AC{random.randint(1000, 9999)}",
                "amount": round(random.uniform(1000, 500000), 2),
                "narration": f"Journal entry {i}",
                "date": "2024-03-31",
                "posted": True
            })
        return entries

    def _demo_ap(self) -> list[dict]:
        return [
            {"vendor": "Supplier A", "amount": 245000, "due_date": "2024-04-15", "days_overdue": 0},
            {"vendor": "Supplier B", "amount": 178000, "due_date": "2024-03-30", "days_overdue": 5},
            {"vendor": "Supplier C", "amount": 520000, "due_date": "2024-04-30", "days_overdue": 0},
        ]
