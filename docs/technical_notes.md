# Technical Notes

## Architecture

```text
Next.js Dashboard
        |
NEXT_PUBLIC_API_URL
        |
FastAPI Backend
        |
SQLAlchemy ORM
        |
SQLite locally / PostgreSQL via DATABASE_URL
        |
Pandas + NumPy Analysis
```

## Main Data Flow

1. `POST /demo/generate` creates synthetic batteries and telemetry records.
2. Telemetry is persisted through SQLAlchemy models.
3. Dashboard endpoints load records from SQL.
4. Pandas DataFrames calculate fleet summaries and diagnostic findings.
5. Reliability helpers build the FMEA register, failure tree, and corrective-action validation view.
6. The frontend renders KPIs, charts, diagnostic tables, reliability artifacts, and battery details.

## Key Backend Files

- `backend/app/main.py`: FastAPI app and routes
- `backend/app/database.py`: SQLAlchemy engine/session setup
- `backend/app/models.py`: database entities
- `backend/app/schemas.py`: Pydantic schemas
- `backend/app/demo_data.py`: synthetic fleet generation
- `backend/app/analysis.py`: Pandas/NumPy diagnostic logic

## Key Frontend Files

- `frontend/app/page.tsx`: dashboard route
- `frontend/components/Dashboard.tsx`: main dashboard UI
- `frontend/lib/api.ts`: typed API client
- `frontend/app/globals.css`: Tailwind base styles

## Diagnostic Thresholds

| Scenario | Rule |
| --- | --- |
| Overtemperature | max temperature > `45 C` |
| Critical overtemperature | max temperature >= `50 C` |
| SOH degradation | SOH drop > `4 percentage points` |
| Firmware incident increase | firmware cohort incident rate > `25%` using `FW-*` error codes |

## Reliability Engineering Artifacts

| View | Purpose |
| --- | --- |
| FMEA register | Prioritizes failure modes using Severity, Occurrence, Detection, and RPN |
| Failure tree | Frames likely contributors to the `BAT-009` critical overtemperature event |
| Corrective action validation | Compares thermal issue count before and after a thermal-path corrective action |

The FMEA register is intentionally compact. It is designed to show engineering reasoning, not to replace a full production DFMEA process.

Current FMEA examples:

| Failure mode | S | O | D | RPN | Priority |
| --- | ---: | ---: | ---: | ---: | --- |
| Overtemperature | 8 | 4 | 3 | 96 | High |
| Abnormal SOH degradation | 7 | 3 | 4 | 84 | Medium |
| Firmware-associated incident increase | 6 | 5 | 3 | 90 | High |

Corrective-action validation currently models a thermal path inspection and airflow correction:

```text
Before: 3 batteries above 45 C
After:  1 battery above 45 C
Result: Partially effective
```

## Local Ports

The demo currently runs cleanly with:

```text
Frontend: http://127.0.0.1:3000
Backend:  http://127.0.0.1:8001
```

The frontend local env file should contain:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

## Vercel Serverless Notes

When deployed without `DATABASE_URL`, the backend uses SQLite in `/tmp`. That storage is ephemeral in serverless environments, so the dashboard endpoints auto-seed synthetic data when no batteries exist.

For the first portfolio deployment, use:

```text
NEXT_PUBLIC_API_URL=/api
```

For a more production-like deployment, add PostgreSQL and set:

```text
DATABASE_URL=<postgresql connection string>
FRONTEND_URL=<vercel app URL>
```

## Verification Commands

Backend tests:

```bash
source .venv/bin/activate
pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

Generate demo data:

```bash
curl -X POST http://127.0.0.1:8001/demo/generate
```

Check dashboard summary:

```bash
curl http://127.0.0.1:8001/dashboard/summary
```

Check reliability endpoints:

```bash
curl http://127.0.0.1:8001/reliability/fmea
curl http://127.0.0.1:8001/reliability/failure-tree
curl http://127.0.0.1:8001/reliability/corrective-action-validation
```
