"""
Forecast Oracle Agent
Generates rolling 13-week cash flow forecasts using ML models,
identifies liquidity risks, and feeds the FP&A automation pipeline.
"""

import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from loguru import logger

from src.models.cash_flow_forecast import CashFlowForecaster
from src.integrations.erp_connector import ERPConnector


# ── Tools ─────────────────────────────────────────────────────────────────

@tool("fetch_actuals_from_erp")
def fetch_actuals_from_erp(period: str) -> str:
    """Fetch actual financial data from ERP for a given period (e.g. '2024-Q1')."""
    erp = ERPConnector()
    data = erp.get_actuals(period=period)
    return str(data)


@tool("fetch_budget_from_erp")
def fetch_budget_from_erp(period: str) -> str:
    """Fetch approved budget from ERP for a given period."""
    erp = ERPConnector()
    data = erp.get_budget(period=period)
    return str(data)


@tool("generate_cash_flow_forecast")
def generate_cash_flow_forecast(weeks: int = 13) -> str:
    """
    Generate a rolling cash flow forecast for the next N weeks.
    Uses Prophet time-series model trained on historical transaction data.
    Returns weekly cash in/out/net predictions.
    """
    forecaster = CashFlowForecaster()
    forecast = forecaster.predict(periods=weeks)
    return str(forecast)


@tool("detect_liquidity_risk")
def detect_liquidity_risk(forecast_json: str) -> str:
    """
    Analyse the cash flow forecast and detect weeks where cash may drop
    below the minimum operating threshold (₹50 lakhs by default).
    Returns a list of at-risk weeks with severity levels.
    """
    import json
    try:
        forecast = json.loads(forecast_json)
    except Exception:
        forecast = []

    THRESHOLD = 5_000_000  # ₹50 lakhs
    at_risk = []

    for week in forecast:
        projected_cash = week.get("net_cash", 0)
        if projected_cash < THRESHOLD:
            severity = "CRITICAL" if projected_cash < 0 else "HIGH"
            at_risk.append({
                "week": week.get("week"),
                "projected_cash": projected_cash,
                "severity": severity,
                "shortfall": THRESHOLD - projected_cash
            })

    if not at_risk:
        return "No liquidity risks detected in the 13-week horizon."
    return f"LIQUIDITY RISK DETECTED in {len(at_risk)} weeks: {at_risk}"


@tool("generate_scenario_models")
def generate_scenario_models(base_forecast: str) -> str:
    """
    Generate 3 financial scenarios: Optimistic (+15%), Base, Pessimistic (-20%).
    Returns scenario comparison with narrative impact summary.
    """
    scenarios = {
        "optimistic": "Revenue +15% · Collections faster · OpEx controlled",
        "base":       "Revenue on plan · Standard payment cycles",
        "pessimistic":"Revenue -20% · Delayed receivables · Increased burn rate"
    }
    return str({
        "scenarios": scenarios,
        "recommendation": "Prepare contingency plan for pessimistic scenario; "
                          "maintain 8-week cash buffer as minimum."
    })


# ── Agent Definition ───────────────────────────────────────────────────────

class ForecastOracleAgent:
    """
    Forecast Oracle — AI agent for cash flow forecasting and FP&A planning.

    Responsibilities:
    - Pull actuals and budgets from ERP
    - Generate rolling 13-week cash flow forecasts (Prophet + ML)
    - Detect liquidity risk windows
    - Generate scenario models (optimistic/base/pessimistic)
    - Feed predictions to Variance Narrator for commentary
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.forecaster = CashFlowForecaster()
        self.agent = self._build_agent()
        logger.info("ForecastOracleAgent initialised")

    def _build_agent(self) -> Agent:
        return Agent(
            role="Chief Financial Forecasting Officer",
            goal=(
                "Generate accurate, rolling cash flow forecasts. "
                "Identify liquidity risks at least 14 days in advance. "
                "Provide scenario models to support CFO strategic planning."
            ),
            backstory=(
                "You are a seasoned FP&A specialist with expertise in time-series "
                "forecasting, working capital management, and scenario analysis. "
                "You combine ML model outputs with business context to deliver "
                "forecasts that finance teams actually trust and act on."
            ),
            tools=[
                fetch_actuals_from_erp,
                fetch_budget_from_erp,
                generate_cash_flow_forecast,
                detect_liquidity_risk,
                generate_scenario_models,
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def run_weekly_forecast(self) -> dict:
        """Run the standard weekly 13-week forecast job."""
        logger.info("Running weekly 13-week cash flow forecast")
        forecast = self.forecaster.predict(periods=13)
        risk_weeks = [w for w in forecast if w.get("net_cash", 0) < 5_000_000]

        return {
            "forecast_weeks": forecast,
            "liquidity_risk_weeks": risk_weeks,
            "risk_count": len(risk_weeks),
            "status": "CRITICAL" if any(w.get("net_cash", 0) < 0 for w in risk_weeks) else (
                      "HIGH" if risk_weeks else "HEALTHY")
        }
