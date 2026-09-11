"""
CFO-OS Multi-Agent Orchestrator
Coordinates all finance agents using CrewAI
"""

from crewai import Crew, Task, Process
from loguru import logger

from .spend_sentinel import SpendSentinelAgent
from .forecast_oracle import ForecastOracleAgent
from .variance_narrator import VarianceNarratorAgent
from .close_accelerator import CloseAcceleratorAgent
from .compliance_guardian import ComplianceGuardianAgent


class CFOOrchestrator:
    """
    Central orchestrator that routes tasks to the appropriate finance agents.
    Supports both sequential and hierarchical multi-agent workflows.
    """

    def __init__(self):
        self.spend_agent     = SpendSentinelAgent()
        self.forecast_agent  = ForecastOracleAgent()
        self.narrator_agent  = VarianceNarratorAgent()
        self.close_agent     = CloseAcceleratorAgent()
        self.compliance_agent= ComplianceGuardianAgent()
        logger.info("CFO Orchestrator initialised with 5 agents")

    # ── Spend Intelligence Pipeline ───────────────────────────────────────
    def run_spend_intelligence(self, transactions: list[dict]) -> dict:
        """
        Full spend intelligence pipeline:
        1. Classify transactions
        2. Detect anomalies / policy violations
        3. Generate narrative alert
        """
        logger.info(f"Running spend intelligence on {len(transactions)} transactions")

        task_classify = Task(
            description=f"""
                Analyse the following transactions and:
                1. Classify each by category, cost centre, and vendor
                2. Flag any policy violations (amount limits, unapproved vendors)
                3. Score anomaly risk (0–100) for each transaction
                Transactions: {transactions[:10]}  # sample for demo
            """,
            agent=self.spend_agent.agent,
            expected_output="JSON with classified transactions, anomaly scores, and policy flags"
        )

        task_narrate = Task(
            description="""
                Based on the spend classification results, generate a CFO-ready
                narrative alert. Include: top overspend categories, anomaly summary,
                recommended actions. Format: executive brief (max 150 words).
            """,
            agent=self.narrator_agent.agent,
            expected_output="Executive spend alert narrative in plain English"
        )

        crew = Crew(
            agents=[self.spend_agent.agent, self.narrator_agent.agent],
            tasks=[task_classify, task_narrate],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return {"pipeline": "spend_intelligence", "output": str(result)}

    # ── FP&A Automation Pipeline ──────────────────────────────────────────
    def run_fpa_automation(self, actuals: dict, budget: dict, period: str) -> dict:
        """
        FP&A pipeline: forecast → variance analysis → narrative
        """
        logger.info(f"Running FP&A automation for period: {period}")

        task_forecast = Task(
            description=f"""
                Using the actuals data, generate a 13-week rolling cash flow forecast.
                Actuals: {actuals}
                Identify liquidity risks and flag periods where cash drops below threshold.
            """,
            agent=self.forecast_agent.agent,
            expected_output="13-week cash flow forecast with liquidity risk flags"
        )

        task_variance = Task(
            description=f"""
                Analyse variance between budget and actuals for period {period}.
                Budget: {budget}
                Actuals: {actuals}
                Identify top 5 variance drivers and root causes.
            """,
            agent=self.narrator_agent.agent,
            expected_output="Variance analysis with root cause explanation and CFO commentary"
        )

        crew = Crew(
            agents=[self.forecast_agent.agent, self.narrator_agent.agent],
            tasks=[task_forecast, task_variance],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return {"pipeline": "fpa_automation", "period": period, "output": str(result)}

    # ── Month-End Close Pipeline ──────────────────────────────────────────
    def run_month_end_close(self, gl_entries: list, bank_statements: list) -> dict:
        """
        Autonomous month-end close: reconcile → flag exceptions → compliance check
        """
        logger.info("Starting month-end close pipeline")

        task_reconcile = Task(
            description=f"""
                Perform bank reconciliation between GL entries and bank statements.
                GL entries count: {len(gl_entries)}
                Bank statement count: {len(bank_statements)}
                Identify matched entries, unmatched items, and exceptions.
            """,
            agent=self.close_agent.agent,
            expected_output="Reconciliation report with matched/unmatched items and exception queue"
        )

        task_compliance = Task(
            description="""
                Review the reconciliation output for:
                1. GST liability calculations
                2. TDS deduction compliance
                3. Any regulatory red flags
                Generate compliance sign-off checklist.
            """,
            agent=self.compliance_agent.agent,
            expected_output="Compliance checklist with pass/fail status for each regulatory item"
        )

        crew = Crew(
            agents=[self.close_agent.agent, self.compliance_agent.agent],
            tasks=[task_reconcile, task_compliance],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return {"pipeline": "month_end_close", "output": str(result)}

    # ── Natural Language CFO Query ────────────────────────────────────────
    def ask_cfo(self, question: str, context: dict) -> str:
        """
        CFO Chat interface — natural language financial Q&A
        Example: "What's our cash runway?" / "Where are we overspending?"
        """
        logger.info(f"CFO query: {question}")

        task = Task(
            description=f"""
                Answer this CFO question accurately and concisely using the context provided.
                Question: {question}
                Financial Context: {context}
                Respond in ≤3 sentences with specific numbers. Be direct and actionable.
            """,
            agent=self.narrator_agent.agent,
            expected_output="Concise, data-backed answer to the CFO question"
        )

        crew = Crew(
            agents=[self.narrator_agent.agent],
            tasks=[task],
            process=Process.sequential
        )

        return str(crew.kickoff())
