# CFO-OS Architecture Documentation

## System Design

CFO-OS is built on a **three-layer AI architecture**:

```
┌──────────────────────────────────────────────────────────────────┐
│                     CFO DASHBOARD / UI                           │
│              React Dashboard  ·  CFO Chat Interface              │
└──────────────────────────┬───────────────────────────────────────┘
                           │ REST API (FastAPI)
┌──────────────────────────▼───────────────────────────────────────┐
│                    AGENTIC AI LAYER (CrewAI)                      │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Spend Sentinel  │  │ Forecast Oracle │  │Variance Narrator │  │
│  │  - Policy check │  │  - 13-wk fcst   │  │  - LLM narration │  │
│  │  - Anomaly flag │  │  - Liquidity    │  │  - Commentary    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬─────────┘  │
│           │                    │                    │             │
│  ┌────────▼────────┐  ┌────────▼────────┐           │             │
│  │Close Accelerator│  │Compliance Guard │           │             │
│  │  - Recon ML     │  │  - GST/TDS/MCA  │           │             │
│  │  - Exception Q  │  │  - Auto-audit   │           │             │
│  └─────────────────┘  └─────────────────┘           │             │
│                                                      │             │
│              ORCHESTRATOR (routes & coordinates) ◄───┘             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│               GENERATIVE AI LAYER (GPT-4o / Claude)               │
│  Variance Narration · Planning Commentary · Policy Drafting        │
│  CFO Chat Q&A · Board Pack Generation · Audit Summaries           │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                INFERENCE / ML LAYER                                │
│                                                                    │
│  Cash Flow Forecast    Anomaly Detection    Reconciliation ML      │
│  (Prophet + XGBoost)   (Isolation Forest)  (Embedding Match)      │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                      DATA LAYER                                    │
│                                                                    │
│  Zaggle API   ERP/GL   Bank Feeds   GSTN   MCA   RBI APIs         │
│  (Real-time)  (Batch)  (Daily)     (API)  (API)  (Webhook)        │
└──────────────────────────────────────────────────────────────────┘
```

## Agent Communication

Agents communicate via a **shared memory store** (Redis):

1. **Orchestrator** receives a trigger (API call, scheduled job, webhook)
2. Routes to the appropriate agent(s)
3. Agents write intermediate results to shared memory
4. Downstream agents read context from memory
5. Final output returned via API / dashboard

## Data Flow: Spend Intelligence

```
Zaggle Card Txn
      │
      ▼
ZaggleAPIClient.get_transactions()
      │
      ▼
AnomalyDetector.batch_score()        ← ML anomaly scoring
      │
      ▼
SpendSentinelAgent.analyse()         ← Policy check + classification
      │
      ├─── COMPLIANT → dashboard update
      ├─── WARNING   → finance team notification
      └─── VIOLATION → CFO alert + auto-escalation
```

## Data Flow: Month-End Close

```
Trigger: End of month (cron job)
      │
      ▼
ERPConnector.get_gl_entries()
      +
Bank Statement (uploaded or API)
      │
      ▼
CloseAcceleratorAgent
      │
      ├─── ML Reconciliation Match (95% auto)
      ├─── Exception Queue → human review
      └─── Compliance check → ComplianceGuardianAgent
                │
                └─── Sign-off report → CFO dashboard
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | CrewAI 0.28 | Multi-agent orchestration |
| LLM | GPT-4o | Narration, Q&A, policy drafting |
| Forecasting | Prophet + XGBoost | Cash flow prediction |
| Anomaly Detection | Isolation Forest | Spend anomaly scoring |
| API Server | FastAPI | REST endpoints |
| Database | PostgreSQL | Persistent storage |
| Cache | Redis | Agent shared memory |
| Data Ingestion | httpx | Zaggle / ERP API calls |
| Containerisation | Docker | Deployment |
