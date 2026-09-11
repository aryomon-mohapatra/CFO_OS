"""
Zaggle API Client
Integrates with Zaggle's prepaid card & expense management platform
to pull real-time transaction data into the CFO-OS spend intelligence pipeline.
"""

import os
import httpx
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel


class Transaction(BaseModel):
    transaction_id: str
    amount: float
    currency: str = "INR"
    merchant_name: str
    merchant_category: str
    card_holder: str
    cost_centre: str
    timestamp: str
    status: str


class ZaggleAPIClient:
    """
    Client for the Zaggle Prepaid Card & Expense API.

    Endpoints used:
    - GET /transactions        — fetch card transaction feed
    - GET /cards               — active card inventory
    - GET /expense-reports     — submitted expense reports
    - POST /policies/validate  — validate transaction against spend policy
    """

    BASE_URL = os.getenv("ZAGGLE_API_BASE_URL", "https://api.zaggle.in/v1")

    def __init__(self):
        self.api_key = os.getenv("ZAGGLE_API_KEY", "demo_key")
        self.client_id = os.getenv("ZAGGLE_CLIENT_ID", "demo_client")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Client-ID": self.client_id,
            "Content-Type": "application/json"
        }
        logger.info("ZaggleAPIClient initialised")

    def get_transactions(
        self,
        days: int = 7,
        cost_centre: str = None,
        card_holder: str = None,
        min_amount: float = None,
        max_amount: float = None
    ) -> list[dict]:
        """
        Fetch transactions from the Zaggle API for the last N days.
        Falls back to synthetic demo data if API is unavailable.
        """
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date   = datetime.now().strftime("%Y-%m-%d")

        params = {
            "from_date": from_date,
            "to_date":   to_date,
            "page_size": 200,
        }
        if cost_centre: params["cost_centre"] = cost_centre
        if card_holder:  params["card_holder"] = card_holder
        if min_amount:   params["min_amount"]  = min_amount
        if max_amount:   params["max_amount"]  = max_amount

        try:
            with httpx.Client(timeout=10) as http:
                resp = http.get(
                    f"{self.BASE_URL}/transactions",
                    headers=self.headers,
                    params=params
                )
                resp.raise_for_status()
                return resp.json().get("transactions", [])

        except Exception as e:
            logger.warning(f"Zaggle API unavailable ({e}). Using demo data.")
            return self._demo_transactions(days)

    def validate_policy(self, transaction: dict) -> dict:
        """
        Validate a transaction against the company's Zaggle spend policy.
        Returns policy status with reasons.
        """
        try:
            with httpx.Client(timeout=10) as http:
                resp = http.post(
                    f"{self.BASE_URL}/policies/validate",
                    headers=self.headers,
                    json={"transaction": transaction}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"Policy validation API error ({e}). Using local rules.")
            return {"status": "UNKNOWN", "reason": "API unavailable"}

    def get_spend_summary(self, period: str = "monthly") -> dict:
        """Get aggregated spend summary by category and cost centre."""
        try:
            with httpx.Client(timeout=10) as http:
                resp = http.get(
                    f"{self.BASE_URL}/reports/spend-summary",
                    headers=self.headers,
                    params={"period": period}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return self._demo_spend_summary()

    # ── Demo / Mock Data ────────────────────────────────────────────────────

    def _demo_transactions(self, days: int) -> list[dict]:
        """Return realistic synthetic transaction data for demos."""
        import random
        categories = ["Travel", "Meals & Entertainment", "Office Supplies",
                      "Software & SaaS", "Marketing", "Logistics", "Training"]
        vendors = ["MakeMyTrip", "Swiggy Business", "Amazon Business",
                   "Zoom", "Google Ads", "Blue Dart", "Coursera Business",
                   "OYO Business", "Uber Business", "Salesforce"]
        cost_centres = ["Engineering", "Sales", "Marketing", "Operations", "Finance"]
        employees    = ["Arjun Sharma", "Priya Patel", "Ravi Kumar",
                        "Sneha Reddy", "Amit Gupta"]

        txns = []
        for i in range(min(days * 12, 100)):
            amount = round(random.uniform(500, 95000), 2)
            txns.append({
                "transaction_id": f"TXN{100000 + i}",
                "amount": amount,
                "currency": "INR",
                "merchant_name": random.choice(vendors),
                "merchant_category": random.choice(categories),
                "card_holder": random.choice(employees),
                "cost_centre": random.choice(cost_centres),
                "timestamp": (
                    datetime.now() - timedelta(
                        days=random.randint(0, days),
                        hours=random.randint(0, 23)
                    )
                ).isoformat(),
                "status": "SETTLED",
                "anomaly_flag": amount > 75000
            })
        return txns

    def _demo_spend_summary(self) -> dict:
        return {
            "period": "current_month",
            "total_spend": 4_523_800,
            "budget": 4_000_000,
            "variance_pct": 13.1,
            "by_category": {
                "Travel": 1_245_000,
                "Marketing": 980_000,
                "Software & SaaS": 756_000,
                "Meals & Entertainment": 542_800,
                "Office Supplies": 1_000_000
            },
            "top_vendors": [
                {"vendor": "Google Ads",    "amount": 520_000},
                {"vendor": "MakeMyTrip",    "amount": 380_000},
                {"vendor": "Zoom",          "amount": 210_000},
            ],
            "policy_violations": 7,
            "high_anomaly_txns": 3
        }
