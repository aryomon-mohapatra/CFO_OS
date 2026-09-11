# CFO-OS API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info & status |
| GET | `/health` | Health check |

---

## Spend Intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/spend/transactions?days=7&cost_centre=Sales` | Fetch & score recent Zaggle transactions |
| GET | `/spend/summary?period=monthly` | Aggregated spend by category |
| POST | `/spend/validate-policy` | Validate a single transaction against policy |

**Example — validate policy:**
```bash
curl -X POST http://localhost:8000/spend/validate-policy \
  -H "Content-Type: application/json" \
  -d '{"amount": 95000, "merchant_category": "Travel", "merchant_name": "MakeMyTrip"}'
```

---

## FP&A & Forecasting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fpa/cash-forecast?weeks=13` | Generate rolling 13-week cash forecast |
| GET | `/fpa/actuals?period=2024-Q1` | Fetch actuals from ERP |
| POST | `/fpa/variance-analysis` | Budget vs actual variance breakdown |

**Example — variance analysis:**
```bash
curl -X POST http://localhost:8000/fpa/variance-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "period": "2024-Q1",
    "actuals": {"revenue": 45200000, "marketing": 3800000},
    "budget":  {"revenue": 50000000, "marketing": 3500000}
  }'
```

---

## Compliance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/compliance/status?period=2024-03` | Full compliance dashboard |

---

## Close Acceleration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/close/reconcile` | Run automated bank reconciliation |
| GET | `/close/checklist` | Month-end close checklist status |

**Example — reconcile:**
```bash
curl -X POST http://localhost:8000/close/reconcile \
  -H "Content-Type: application/json" \
  -d '{"from_date": "2024-03-01", "to_date": "2024-03-31"}'
```

---

## CFO Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cfo/ask` | Natural language financial Q&A |

**Example questions:**
```bash
curl -X POST http://localhost:8000/cfo/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our current cash runway?"}'

curl -X POST http://localhost:8000/cfo/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Where are we overspending vs budget?"}'
```

---

## Response Format

All endpoints return JSON. Error responses follow:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```
