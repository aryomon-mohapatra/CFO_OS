"""
GSTN API Client
Integrates with the GST Network (GSTN) API for compliance verification,
GSTR reconciliation, and ITC (Input Tax Credit) validation.
"""

import os
import httpx
from loguru import logger


class GSTNAPIClient:
    """
    Client for GSTN compliance APIs.

    Endpoints:
    - GET  /taxpayer/{gstin}        — Taxpayer profile & status
    - GET  /returns/gstr1           — GSTR-1 filed return data
    - GET  /returns/gstr3b          — GSTR-3B filed return data
    - POST /reconcile/itc           — ITC reconciliation (GSTR-2A vs books)
    - GET  /e-invoice/status        — E-invoice validation
    """

    BASE_URL = os.getenv("GSTN_API_URL", "https://api.gst.gov.in")

    def __init__(self):
        self.username = os.getenv("GSTN_USERNAME", "demo_user")
        self.app_key  = os.getenv("GSTN_APP_KEY", "demo_key")
        self.gstin    = os.getenv("COMPANY_GSTIN", "27AAPFU0939F1ZV")
        logger.info(f"GSTNAPIClient initialised for GSTIN: {self.gstin}")

    def get_taxpayer_profile(self) -> dict:
        """Fetch taxpayer registration details from GSTN."""
        try:
            with httpx.Client(timeout=10) as http:
                resp = http.get(
                    f"{self.BASE_URL}/taxpayer/{self.gstin}",
                    headers=self._headers()
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"GSTN taxpayer API error ({e}). Using demo data.")
            return self._demo_taxpayer()

    def get_gstr1(self, period: str) -> dict:
        """Fetch GSTR-1 (outward supply) return for a period. period: 'MMYYYY'"""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/returns/gstr1",
                    headers=self._headers(),
                    params={"gstin": self.gstin, "ret_period": period}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"GSTR-1 API error ({e}). Using demo data.")
            return self._demo_gstr1(period)

    def get_gstr3b(self, period: str) -> dict:
        """Fetch GSTR-3B (summary return) for a period."""
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(
                    f"{self.BASE_URL}/returns/gstr3b",
                    headers=self._headers(),
                    params={"gstin": self.gstin, "ret_period": period}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"GSTR-3B API error ({e}). Using demo data.")
            return self._demo_gstr3b(period)

    def reconcile_itc(self, books_itc: float, period: str) -> dict:
        """
        Reconcile ITC claimed in books vs GSTR-2A (auto-populated from suppliers).
        Returns mismatch amount and reconciliation status.
        """
        gstr2a_itc = books_itc * 0.96  # demo: 4% mismatch
        mismatch   = books_itc - gstr2a_itc
        return {
            "period": period,
            "books_itc": books_itc,
            "gstr2a_itc": round(gstr2a_itc, 2),
            "mismatch": round(mismatch, 2),
            "mismatch_pct": round((mismatch / books_itc * 100) if books_itc else 0, 2),
            "status": "RECONCILED" if mismatch < 1000 else "ACTION_REQUIRED",
            "action": None if mismatch < 1000 else (
                f"Follow up with suppliers for ₹{mismatch:,.0f} ITC difference"
            )
        }

    def get_compliance_calendar(self) -> list[dict]:
        """Return upcoming GST filing deadlines."""
        return [
            {"filing": "GSTR-1 (Monthly)", "due_date": "11th of next month", "frequency": "Monthly"},
            {"filing": "GSTR-3B",          "due_date": "20th of next month", "frequency": "Monthly"},
            {"filing": "GSTR-9 (Annual)",  "due_date": "31st December",      "frequency": "Annual"},
            {"filing": "GSTR-9C (Audit)",  "due_date": "31st December",      "frequency": "Annual"},
        ]

    def _headers(self) -> dict:
        return {
            "username":     self.username,
            "gstin":        self.gstin,
            "Authorization": f"Bearer {self.app_key}",
            "Content-Type": "application/json"
        }

    def _demo_taxpayer(self) -> dict:
        return {
            "gstin":          self.gstin,
            "legal_name":     "Demo Company Private Limited",
            "trade_name":     "Demo Co",
            "status":         "ACTIVE",
            "registration_dt": "01/04/2018",
            "state":          "Maharashtra",
            "tax_payer_type": "Regular"
        }

    def _demo_gstr1(self, period: str) -> dict:
        return {
            "gstin": self.gstin, "period": period,
            "status": "FILED", "filing_date": f"10/{period[2:]}/{period[:2]}",
            "total_taxable_value": 38_500_000,
            "total_igst": 2_100_000, "total_cgst": 1_750_000, "total_sgst": 1_750_000,
            "invoice_count": 248
        }

    def _demo_gstr3b(self, period: str) -> dict:
        return {
            "gstin": self.gstin, "period": period,
            "status": "FILED", "filing_date": f"18/{period[2:]}/{period[:2]}",
            "tax_liability": {"igst": 2_100_000, "cgst": 1_750_000, "sgst": 1_750_000},
            "itc_claimed":   {"igst": 1_800_000, "cgst": 1_200_000, "sgst": 1_200_000},
            "net_tax_paid":  {"igst": 300_000,   "cgst": 550_000,   "sgst": 550_000},
            "cash_paid":      1_400_000
        }
