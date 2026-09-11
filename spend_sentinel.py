"""
Spend Sentinel Agent
Monitors every transaction in real-time, flags policy violations,
scores anomalies, and triggers alerts via the CFO-OS platform.
"""

import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from loguru import logger

from src.integrations.zaggle_api import ZaggleAPIClient
from src.models.anomaly_detector import AnomalyDetector


# ── Tools available to the Spend Sentinel ─────────────────────────────────

@tool("fetch_recent_transactions")
def fetch_recent_transactions(days: int = 7) -> str:
    """Fetch recent transactions from the Zaggle API for the last N days."""
    client = ZaggleAPIClient()
    txns = client.get_transactions(days=days)
    return str(txns[:20])  # return sample


@tool("check_spend_policy")
def check_spend_policy(transaction_json: str) -> str:
    """
    Check a transaction against the company spend policy.
    Returns policy status: COMPLIANT, WARNING, or VIOLATION with reason.
    """
    import json
    try:
        txn = json.loads(transaction_json)
    except Exception:
        txn = {"amount": 0, "category": "unknown", "vendor": "unknown"}

    # Policy rules (demo logic — real version reads from policy DB)
    violations = []
    amount = txn.get("amount", 0)
    category = txn.get("category", "").lower()

    if amount > 50000 and "travel" in category:
        violations.append("Travel spend exceeds ₹50,000 limit — requires CFO approval")
    if amount > 100000:
        violations.append("Transaction exceeds ₹1,00,000 — dual approval required")
    if txn.get("vendor") in ["UNAPPROVED_VENDOR_1", "BLACKLISTED_CO"]:
        violations.append("Vendor is on the blacklist")

    if violations:
        return f"VIOLATION: {'; '.join(violations)}"
    elif amount > 25000:
        return "WARNING: High-value transaction — recommend review"
    return "COMPLIANT"


@tool("score_anomaly")
def score_anomaly(transaction_json: str) -> str:
    """Score the anomaly risk of a transaction (0–100). Higher = more suspicious."""
    import json
    try:
        txn = json.loads(transaction_json)
    except Exception:
        return "50"  # neutral score on parse failure

    detector = AnomalyDetector()
    score = detector.score(txn)
    return str(score)


@tool("generate_spend_alert")
def generate_spend_alert(summary: str) -> str:
    """Generate a natural language spend alert for the CFO dashboard."""
    return f"""
    🚨 SPEND ALERT — CFO-OS Notification
    {summary}
    Recommended action: Review flagged transactions in the Spend Intelligence dashboard.
    """


# ── Agent Definition ───────────────────────────────────────────────────────

class SpendSentinelAgent:
    """
    Spend Sentinel — autonomous agent that monitors all spend in real-time.

    Responsibilities:
    - Ingest Zaggle transaction feed
    - Classify by category, cost centre, and vendor
    - Score anomaly risk using ML model
    - Check against spend policy
    - Generate narrative alerts for violations
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.agent = self._build_agent()
        logger.info("SpendSentinelAgent initialised")

    def _build_agent(self) -> Agent:
        return Agent(
            role="Chief Spend Intelligence Officer",
            goal=(
                "Monitor every financial transaction in real-time. "
                "Detect policy violations, anomalies, and spend inefficiencies. "
                "Generate clear, actionable alerts for the CFO."
            ),
            backstory=(
                "You are an expert in enterprise spend management with deep knowledge "
                "of procurement policies, vendor risk, and financial controls. "
                "You process hundreds of transactions per minute and never miss a policy breach. "
                "You communicate findings clearly and concisely to finance leadership."
            ),
            tools=[
                fetch_recent_transactions,
                check_spend_policy,
                score_anomaly,
                generate_spend_alert,
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def analyse_transactions(self, transactions: list[dict]) -> dict:
        """Analyse a batch of transactions and return classified results."""
        results = {"compliant": [], "warnings": [], "violations": [], "high_anomaly": []}

        detector = AnomalyDetector()

        for txn in transactions:
            import json
            txn_str = json.dumps(txn)

            # Anomaly score
            score = detector.score(txn)
            txn["anomaly_score"] = score

            # Policy check
            policy_result = check_spend_policy.run(txn_str)

            if "VIOLATION" in policy_result:
                results["violations"].append({**txn, "policy_status": policy_result})
            elif "WARNING" in policy_result:
                results["warnings"].append({**txn, "policy_status": policy_result})
            else:
                results["compliant"].append({**txn, "policy_status": "COMPLIANT"})

            if score > 75:
                results["high_anomaly"].append({**txn, "anomaly_score": score})

        logger.info(
            f"Spend analysis complete — "
            f"{len(results['violations'])} violations, "
            f"{len(results['warnings'])} warnings, "
            f"{len(results['high_anomaly'])} high anomaly"
        )
        return results
