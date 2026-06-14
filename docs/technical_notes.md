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
5. The frontend renders KPIs, charts, diagnostic tables, and battery details.

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
