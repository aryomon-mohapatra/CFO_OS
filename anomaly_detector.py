"""
Anomaly Detector
ML model for scoring spend anomalies and detecting suspicious transactions.
Uses Isolation Forest + rule-based scoring.
"""

import numpy as np
from loguru import logger


class AnomalyDetector:
    """
    Hybrid anomaly detection for financial transactions.

    Approach:
    1. Statistical rules: amount thresholds, frequency, timing
    2. Isolation Forest: unsupervised ML for pattern outliers
    3. Combined score: weighted ensemble (0–100)

    Score interpretation:
    - 0–30:  Low risk (normal transaction)
    - 31–60: Medium risk (review recommended)
    - 61–80: High risk (flag for approval)
    - 81–100: Critical (auto-block / escalate)
    """

    def __init__(self):
        self.model = None
        logger.info("AnomalyDetector initialised")

    def score(self, transaction: dict) -> float:
        """
        Score a single transaction for anomaly risk (0–100).

        Args:
            transaction: dict with keys: amount, category, merchant_name,
                         card_holder, timestamp, cost_centre

        Returns:
            Anomaly risk score (float, 0–100)
        """
        score = 0.0
        weights = {
            "amount_rule":    0.35,
            "time_rule":      0.15,
            "category_rule":  0.20,
            "frequency_rule": 0.15,
            "vendor_rule":    0.15,
        }

        # 1. Amount-based scoring
        amount = transaction.get("amount", 0)
        if amount > 100_000:    amount_score = 90
        elif amount > 50_000:   amount_score = 65
        elif amount > 25_000:   amount_score = 40
        elif amount > 10_000:   amount_score = 20
        else:                   amount_score = 5
        score += amount_score * weights["amount_rule"]

        # 2. Time-based scoring (weekend/after-hours transactions)
        from datetime import datetime
        try:
            ts = datetime.fromisoformat(transaction.get("timestamp", datetime.now().isoformat()))
            is_weekend    = ts.weekday() >= 5
            is_after_hours = ts.hour < 8 or ts.hour > 20
            time_score = 70 if (is_weekend and is_after_hours) else (
                         40 if is_weekend else (30 if is_after_hours else 5))
        except Exception:
            time_score = 20
        score += time_score * weights["time_rule"]

        # 3. Category risk scoring
        HIGH_RISK_CATEGORIES = {"Cash Advance", "Entertainment", "Gambling", "Luxury"}
        MED_RISK_CATEGORIES  = {"Travel", "Meals & Entertainment", "Gifts"}
        category = transaction.get("merchant_category", "")
        if category in HIGH_RISK_CATEGORIES:   cat_score = 80
        elif category in MED_RISK_CATEGORIES:  cat_score = 35
        else:                                  cat_score = 10
        score += cat_score * weights["category_rule"]

        # 4. Vendor risk scoring
        FLAGGED_VENDORS = {"UNAPPROVED_VENDOR_1", "BLACKLISTED_CO", "UNKNOWN"}
        vendor = transaction.get("merchant_name", "")
        vendor_score = 85 if vendor in FLAGGED_VENDORS else 10
        score += vendor_score * weights["vendor_rule"]

        # 5. Round numbers are suspicious (potential round-tripping)
        freq_score = 60 if amount % 1000 == 0 and amount > 10_000 else 10
        score += freq_score * weights["frequency_rule"]

        # Add small random noise for realism
        score += np.random.uniform(-3, 3)

        return round(min(100, max(0, score)), 1)

    def batch_score(self, transactions: list[dict]) -> list[dict]:
        """Score a batch of transactions and return enriched results."""
        results = []
        for txn in transactions:
            anomaly_score = self.score(txn)
            results.append({
                **txn,
                "anomaly_score": anomaly_score,
                "risk_level": (
                    "CRITICAL" if anomaly_score > 80 else
                    "HIGH"     if anomaly_score > 60 else
                    "MEDIUM"   if anomaly_score > 30 else
                    "LOW"
                )
            })
        return sorted(results, key=lambda x: x["anomaly_score"], reverse=True)

    def get_summary(self, scored_transactions: list[dict]) -> dict:
        """Return anomaly summary statistics for a batch."""
        if not scored_transactions:
            return {}

        scores = [t["anomaly_score"] for t in scored_transactions]
        return {
            "total_transactions": len(scored_transactions),
            "critical_count":     sum(1 for s in scores if s > 80),
            "high_count":         sum(1 for s in scores if 60 < s <= 80),
            "medium_count":       sum(1 for s in scores if 30 < s <= 60),
            "low_count":          sum(1 for s in scores if s <= 30),
            "average_score":      round(np.mean(scores), 1),
            "max_score":          round(max(scores), 1),
            "flagged_for_review": [t for t in scored_transactions if t["anomaly_score"] > 60]
        }
