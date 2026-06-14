# Interview Talking Points

## 30-Second Summary

This project is a compact full-stack diagnostic dashboard for a synthetic fleet of residential batteries. It simulates the kind of work a Systems Engineer would do when monitoring fleet telemetry, identifying abnormal behavior, forming root-cause hypotheses, and communicating reliability risk.

The demo uses FastAPI, SQLAlchemy, SQLite, Pandas, NumPy, Next.js, TypeScript, Tailwind CSS, and Recharts.

## 2-Minute Walkthrough

1. The backend generates synthetic telemetry for 30 residential batteries.
2. The data includes voltage, current, temperature, SOC, SOH, firmware, region, operating mode, and error codes.
3. Three failure patterns are injected:
   - overtemperature on selected batteries,
   - abnormal SOH degradation,
   - increased firmware-related incidents on firmware `2.1.0`.
4. The backend stores telemetry in SQL and analyzes it with Pandas and NumPy.
5. The dashboard presents fleet KPIs, firmware incident rates, health distribution, temperature comparison, SOH comparison, diagnostic findings, and battery-level detail.
6. Root causes are intentionally shown as hypotheses, not proven conclusions.

## Engineering Framing

This is not intended to be a production enterprise platform. It is an interview-ready demo showing how raw telemetry can become actionable engineering insight.

The project demonstrates:

- SQL data modeling and telemetry storage
- Python API development with FastAPI
- SQLAlchemy ORM usage with SQLite locally and PostgreSQL readiness
- Pandas and NumPy analysis
- transparent rule-based diagnostics
- reliability KPI monitoring
- firmware cohort comparison
- technical communication through dashboard design

## Diagnostic Logic

The diagnostic engine uses explainable thresholds:

- overtemperature if max temperature exceeds `45 C`
- abnormal SOH degradation if SOH drop exceeds `4 percentage points`
- firmware-associated issue if a firmware cohort has more than `25%` of batteries with `FW-*` errors

No machine learning is used. That is intentional because the portfolio goal is explainability.

## How To Explain The Results

The current synthetic dataset produces:

- 30 total batteries
- 19 healthy batteries
- 11 batteries with issues
- 3 overtemperature batteries
- 3 abnormal SOH degradation batteries
- 5 firmware-related incident batteries on firmware `2.1.0`

The key engineering interpretation is:

> The fleet has localized thermal and SOH issues, plus a cohort-level reliability signal associated with firmware `2.1.0`. The next engineering step would be to inspect thermal environments, review degradation history, and compare firmware incident rates against previous firmware releases before recommending rollback or hotfix validation.

## Good Interview Questions And Answers

**Why use synthetic data?**

Real fleet telemetry is private and proprietary. Synthetic data lets the project demonstrate realistic engineering workflows without exposing customer or company data.

**Why not machine learning?**

For this demo, explainability matters more than model sophistication. A Systems Engineer needs to defend why a diagnostic was triggered. Transparent rules are easier to validate and communicate.

**How would this change in production?**

I would add authentication, background ingestion jobs, database migrations, PostgreSQL, cloud-hosted storage, richer telemetry validation, alerting, audit history, and integration with service or corrective-action workflows.

**How does this show reliability engineering?**

It compares incident rates across firmware cohorts, tracks affected population, identifies repeated failure patterns, and presents risk level and recommended next steps.

**How does this support root-cause analysis?**

It does not claim root cause is proven. It turns telemetry symptoms into likely hypotheses that an engineer would validate with service history, environment data, firmware history, and additional testing.

## Suggested Live Demo Flow

1. Open the dashboard.
2. Point to the KPI cards and summarize fleet health.
3. Show firmware incident chart and explain why `2.1.0` stands out.
4. Show temperature and SOH charts and explain unit-level anomalies.
5. Use diagnostic filters: Thermal, SOH, Firmware.
6. Open a battery detail and show recent telemetry plus diagnostics.
7. End with what you would add next for production.
