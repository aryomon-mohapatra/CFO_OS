"""
CFO-OS Demo: Spend Intelligence Pipeline
=========================================
Run this script to see the CFO-OS spend intelligence module in action.
No API keys required — uses realistic synthetic data.

Usage:
    python demo/demo_spend_intelligence.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.zaggle_api import ZaggleAPIClient
from src.integrations.erp_connector import ERPConnector
from src.models.anomaly_detector import AnomalyDetector
from src.models.cash_flow_forecast import CashFlowForecaster


def divider(title: str):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)


def demo_spend_intelligence():
    divider("MODULE 1: REAL-TIME SPEND INTELLIGENCE")

    zaggle   = ZaggleAPIClient()
    detector = AnomalyDetector()

    print("\n📡 Fetching last 7 days of Zaggle transactions...")
    transactions = zaggle.get_transactions(days=7)
    print(f"   ✅ Fetched {len(transactions)} transactions")

    print("\n🤖 Running anomaly scoring on all transactions...")
    scored = detector.batch_score(transactions)
    summary = detector.get_summary(scored)

    print(f"\n   📊 ANOMALY SUMMARY")
    print(f"   ─────────────────────────────────────────")
    print(f"   Total transactions:   {summary['total_transactions']}")
    print(f"   🔴 Critical (>80):    {summary['critical_count']}")
    print(f"   🟠 High (60–80):      {summary['high_count']}")
    print(f"   🟡 Medium (30–60):    {summary['medium_count']}")
    print(f"   🟢 Low (<30):         {summary['low_count']}")
    print(f"   Average risk score:   {summary['average_score']}")

    print(f"\n   🚨 TOP 3 FLAGGED TRANSACTIONS")
    print(f"   ─────────────────────────────────────────")
    for txn in scored[:3]:
        print(f"   [{txn['risk_level']:8s}] Score: {txn['anomaly_score']:5.1f} | "
              f"₹{txn['amount']:>10,.0f} | {txn['merchant_name']:20s} | "
              f"{txn['merchant_category']}")

    spend_summary = zaggle.get_spend_summary()
    print(f"\n   💸 SPEND SUMMARY (Current Month)")
    print(f"   ─────────────────────────────────────────")
    print(f"   Total spend:          ₹{spend_summary['total_spend']:>12,.0f}")
    print(f"   Budget:               ₹{spend_summary['budget']:>12,.0f}")
    print(f"   Variance:             {spend_summary['variance_pct']:+.1f}%")
    print(f"   Policy violations:    {spend_summary['policy_violations']}")
    print(f"   High anomaly flags:   {spend_summary['high_anomaly_txns']}")

    print(f"\n   📂 TOP CATEGORIES")
    for cat, amt in list(spend_summary['by_category'].items())[:4]:
        print(f"      {cat:30s}  ₹{amt:>10,.0f}")


def demo_cash_flow_forecast():
    divider("MODULE 2: CASH FLOW FORECASTING (13-WEEK ROLLING)")

    forecaster = CashFlowForecaster()
    print("\n🔮 Generating 13-week rolling cash flow forecast...")
    forecast = forecaster.predict(periods=13)
    risk     = forecaster.get_risk_summary(forecast)

    print(f"\n   STATUS: {'🔴 ' if risk['overall_status'] == 'CRITICAL' else '🟠 ' if risk['overall_status'] == 'HIGH' else '🟢 '}{risk['overall_status']}")
    print(f"   Liquidity risk weeks: {risk['risk_weeks']} / {risk['total_weeks']}")
    print(f"   Recommendation: {risk['recommendation']}")

    print(f"\n   WEEK-BY-WEEK FORECAST")
    print(f"   {'Week':8s} {'Date':12s} {'Cash In':>14s} {'Cash Out':>14s} {'Net Position':>14s} {'Risk':6s}")
    print(f"   {'─'*8} {'─'*12} {'─'*14} {'─'*14} {'─'*14} {'─'*6}")
    for w in forecast:
        risk_flag = "⚠️" if w['liquidity_risk'] else "  "
        print(f"   {w['week']:8s} {w['week_start']:12s} "
              f"₹{w['cash_in']:>12,.0f} "
              f"₹{w['cash_out']:>12,.0f} "
              f"₹{w['net_cash']:>12,.0f} {risk_flag}")


def demo_variance_analysis():
    divider("MODULE 3: FP&A VARIANCE ANALYSIS")

    erp = ERPConnector()
    print("\n📥 Fetching actuals and budget from ERP...")

    actuals = erp.get_actuals("2024-Q1")
    budget  = erp.get_budget("2024-Q1")

    print(f"\n   BUDGET VS ACTUAL — Q1 2024")
    print(f"   {'Line Item':30s} {'Budget':>14s} {'Actual':>14s} {'Variance':>14s} {'%':>7s}")
    print(f"   {'─'*30} {'─'*14} {'─'*14} {'─'*14} {'─'*7}")

    for key in budget:
        if key in actuals and isinstance(budget[key], (int, float)) and isinstance(actuals[key], (int, float)):
            delta = actuals[key] - budget[key]
            pct   = (delta / budget[key] * 100) if budget[key] else 0
            flag  = "🔴" if delta > budget[key] * 0.1 else "🟢" if delta < 0 else "  "
            print(f"   {flag} {key:28s} ₹{budget[key]:>12,.0f} ₹{actuals[key]:>12,.0f} "
                  f"₹{delta:>+12,.0f} {pct:>+6.1f}%")


def demo_compliance():
    divider("MODULE 4: COMPLIANCE STATUS")
    print("\n   REGULATORY COMPLIANCE DASHBOARD — March 2024")
    print("   ─────────────────────────────────────────────")
    items = [
        ("GST / GSTR-3B",      "✅ COMPLIANT",   "Filed 18-Mar"),
        ("TDS Q4",             "✅ COMPLIANT",   "Deposited on time"),
        ("ROC / MCA Filing",   "✅ COMPLIANT",   "Up to date"),
        ("FEMA / RBI",         "✅ COMPLIANT",   "No violations"),
        ("Labour Compliance",  "✅ COMPLIANT",   "PF/ESI current"),
    ]
    for item, status, detail in items:
        print(f"   {status}  {item:25s}  {detail}")

    print("\n   📅 UPCOMING DEADLINES")
    deadlines = [
        ("GSTR-3B (Apr)", "20 Apr 2024"),
        ("TDS Q4 Return", "31 May 2024"),
        ("AGM Filing",    "30 Sep 2024"),
    ]
    for filing, due in deadlines:
        print(f"      {filing:25s}  Due: {due}")


def demo_cfo_chat():
    divider("MODULE 5: CFO CHAT — Natural Language Q&A")
    questions = [
        "What is our current cash runway?",
        "Where are we overspending vs budget?",
        "What is the Q2 revenue forecast?",
    ]
    answers = [
        "Cash runway: ~5.1 months at ₹14.2Cr balance and ₹2.8Cr/month burn. Recommend accelerating Q2 collections.",
        "Marketing 18.3% over (Google Ads spike). Travel 16.7% over (3 unapproved bookings flagged by Spend Sentinel).",
        "Q2 revenue forecast: ₹4.8Cr (4% below target). Risk: 2 enterprise deals slipped. Upside: SMB tracking 12% above plan."
    ]
    for q, a in zip(questions, answers):
        print(f"\n   👤 CFO: {q}")
        print(f"   🤖 CFO-OS: {a}")


if __name__ == "__main__":
    print("\n" + "🧠 " * 20)
    print("   CFO-OS: AI-Native CFO Operating System")
    print("   Zaggle × COMET'26 | IIT Roorkee")
    print("🧠 " * 20)

    demo_spend_intelligence()
    demo_cash_flow_forecast()
    demo_variance_analysis()
    demo_compliance()
    demo_cfo_chat()

    divider("DEMO COMPLETE")
    print("\n   🚀 Run `uvicorn src.api.main:app --reload` for the full API")
    print("   📖 Visit http://localhost:8000/docs for Swagger UI\n")
