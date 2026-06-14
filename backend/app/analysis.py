from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models


TEMP_LIMIT_C = 45.0
SOH_DROP_LIMIT = 4.0
FIRMWARE_INCIDENT_RATE_LIMIT = 0.25


def telemetry_dataframe(db: Session) -> pd.DataFrame:
    records = db.scalars(select(models.TelemetryRecord)).all()
    rows = [
        {
            "battery_id": record.battery_id,
            "timestamp": record.timestamp,
            "voltage": record.voltage,
            "current": record.current,
            "temperature": record.temperature,
            "state_of_charge": record.state_of_charge,
            "state_of_health": record.state_of_health,
            "firmware_version": record.firmware_version,
            "error_code": record.error_code,
            "operating_mode": record.operating_mode,
            "site_region": record.site_region,
        }
        for record in records
    ]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["battery_id", "timestamp"])


def build_diagnostics(db: Session) -> list[dict[str, object]]:
    df = telemetry_dataframe(db)
    if df.empty:
        return []

    diagnostics: list[dict[str, object]] = []
    latest = df.sort_values("timestamp").groupby("battery_id").tail(1)
    latest_lookup = latest.set_index("battery_id")

    grouped = df.groupby("battery_id")
    for battery_id, group in grouped:
        context = latest_lookup.loc[battery_id]
        max_temp = float(group["temperature"].max())
        soh_start = float(group["state_of_health"].iloc[0])
        soh_end = float(group["state_of_health"].iloc[-1])
        soh_drop = round(soh_start - soh_end, 2)

        if max_temp > TEMP_LIMIT_C:
            diagnostics.append(
                _diagnostic_row(
                    battery_id=battery_id,
                    context=context,
                    issue_type="Overtemperature",
                    severity="Critical" if max_temp >= 50 else "Warning",
                    observed_value=round(max_temp, 2),
                    expected_range="<= 45.0 C",
                    likely_cause="Hypothesis: thermal management restriction or high ambient temperature",
                    recommended_action="Inspect airflow path, installation environment, and temperature sensor calibration.",
                )
            )

        if soh_drop > SOH_DROP_LIMIT or soh_end < 90:
            diagnostics.append(
                _diagnostic_row(
                    battery_id=battery_id,
                    context=context,
                    issue_type="Abnormal SOH degradation",
                    severity="Critical" if soh_end < 88 else "Warning",
                    observed_value=round(soh_drop, 2),
                    expected_range="<= 4.0 percentage-point drop during demo window",
                    likely_cause="Hypothesis: cell degradation, high cycle stress, or sensor drift",
                    recommended_action="Review charge/discharge history and schedule pack health inspection.",
                )
            )

    firmware_rates = _firmware_incident_rates(df)
    high_risk_firmware = firmware_rates[
        firmware_rates["incident_rate"] > FIRMWARE_INCIDENT_RATE_LIMIT
    ]
    for _, firmware_row in high_risk_firmware.iterrows():
        firmware = str(firmware_row["firmware_version"])
        affected = df[
            (df["firmware_version"] == firmware)
            & (df["error_code"].fillna("").str.startswith("FW-"))
        ]
        for battery_id in sorted(affected["battery_id"].unique()):
            context = latest_lookup.loc[battery_id]
            diagnostics.append(
                _diagnostic_row(
                    battery_id=battery_id,
                    context=context,
                    issue_type="Firmware-associated incident increase",
                    severity="Warning",
                    observed_value=round(float(firmware_row["incident_rate"]) * 100, 1),
                    expected_range="<= 25.0% of batteries on same firmware reporting incidents",
                    likely_cause="Hypothesis: firmware regression",
                    recommended_action="Compare against previous firmware and consider staged rollback or hotfix validation.",
                )
            )

    return diagnostics


def build_dashboard_summary(db: Session) -> dict[str, object]:
    df = telemetry_dataframe(db)
    if df.empty:
        return {
            "fleet_size": 0,
            "healthy_battery_count": 0,
            "batteries_with_active_issues": 0,
            "incident_rate": 0.0,
            "average_temperature": 0.0,
            "average_state_of_health": 0.0,
            "affected_batteries": [],
            "main_observed_trend": "No telemetry has been generated yet.",
            "population_affected": "0 of 0 batteries",
            "risk_level": "Normal",
            "recommended_next_step": "Generate synthetic demo data.",
            "synthetic_data": True,
        }

    diagnostics = build_diagnostics(db)
    affected = sorted({str(item["battery_id"]) for item in diagnostics})
    fleet_size = int(df["battery_id"].nunique())
    latest = df.sort_values("timestamp").groupby("battery_id").tail(1)
    average_soh = float(latest["state_of_health"].mean())
    incident_rate = len(affected) / fleet_size if fleet_size else 0.0
    issue_types = pd.Series([item["issue_type"] for item in diagnostics])
    main_trend = (
        str(issue_types.value_counts().idxmax())
        if not issue_types.empty
        else "Fleet telemetry is inside expected operating limits."
    )

    return {
        "fleet_size": fleet_size,
        "healthy_battery_count": fleet_size - len(affected),
        "batteries_with_active_issues": len(affected),
        "incident_rate": round(incident_rate, 3),
        "average_temperature": round(float(df["temperature"].mean()), 2),
        "average_state_of_health": round(average_soh, 2),
        "affected_batteries": affected,
        "main_observed_trend": main_trend,
        "population_affected": f"{len(affected)} of {fleet_size} batteries",
        "risk_level": _risk_level(diagnostics),
        "recommended_next_step": _recommended_next_step(diagnostics),
        "synthetic_data": True,
    }


def build_firmware_incidents(db: Session) -> list[dict[str, object]]:
    df = telemetry_dataframe(db)
    if df.empty:
        return []
    rates = _firmware_incident_rates(df)
    return [
        {
            "firmware_version": str(row["firmware_version"]),
            "battery_count": int(row["battery_count"]),
            "incident_battery_count": int(row["incident_battery_count"]),
            "incident_rate": round(float(row["incident_rate"]), 3),
        }
        for _, row in rates.iterrows()
    ]


def build_battery_health(db: Session) -> dict[str, object]:
    df = telemetry_dataframe(db)
    if df.empty:
        return {"distribution": [], "soh_by_battery": [], "temperature_by_battery": []}

    latest = df.sort_values("timestamp").groupby("battery_id").tail(1)
    latest = latest.sort_values("battery_id")
    bins = [0, 85, 90, 95, 100]
    labels = ["<85", "85-90", "90-95", "95-100"]
    latest = latest.copy()
    latest["soh_band"] = pd.cut(latest["state_of_health"], bins=bins, labels=labels)
    distribution = latest["soh_band"].value_counts().reindex(labels, fill_value=0)
    temp_by_battery = df.groupby("battery_id")["temperature"].max().reset_index()

    return {
        "distribution": [
            {"range": str(index), "count": int(value)}
            for index, value in distribution.items()
        ],
        "soh_by_battery": [
            {
                "battery_id": str(row["battery_id"]),
                "state_of_health": round(float(row["state_of_health"]), 2),
            }
            for _, row in latest.iterrows()
        ],
        "temperature_by_battery": [
            {
                "battery_id": str(row["battery_id"]),
                "temperature": round(float(row["temperature"]), 2),
            }
            for _, row in temp_by_battery.iterrows()
        ],
    }


def build_battery_detail(db: Session, battery_id: str) -> Optional[dict[str, object]]:
    battery = db.scalar(select(models.Battery).where(models.Battery.battery_id == battery_id))
    if battery is None:
        return None

    telemetry = db.scalars(
        select(models.TelemetryRecord)
        .where(models.TelemetryRecord.battery_id == battery_id)
        .order_by(models.TelemetryRecord.timestamp)
    ).all()
    diagnostics = [
        item for item in build_diagnostics(db) if item["battery_id"] == battery_id
    ]

    return {
        "battery": {
            "battery_id": battery.battery_id,
            "site_region": battery.site_region,
            "firmware_version": battery.firmware_version,
            "status": battery.status,
            "model": battery.model,
        },
        "recent_telemetry": [
            {
                "timestamp": record.timestamp.isoformat(),
                "voltage": record.voltage,
                "current": record.current,
                "temperature": record.temperature,
                "state_of_charge": record.state_of_charge,
                "state_of_health": record.state_of_health,
                "error_code": record.error_code,
                "operating_mode": record.operating_mode,
            }
            for record in telemetry[-24:]
        ],
        "diagnostics": diagnostics,
        "synthetic_data": True,
    }


def _diagnostic_row(
    battery_id: str,
    context: pd.Series,
    issue_type: str,
    severity: str,
    observed_value: float,
    expected_range: str,
    likely_cause: str,
    recommended_action: str,
) -> dict[str, object]:
    return {
        "battery_id": battery_id,
        "region": str(context["site_region"]),
        "firmware_version": str(context["firmware_version"]),
        "issue_type": issue_type,
        "severity": severity,
        "observed_value": observed_value,
        "expected_range": expected_range,
        "likely_cause": likely_cause,
        "recommended_action": recommended_action,
    }


def _firmware_incident_rates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["firmware_error"] = df["error_code"].fillna("").str.startswith("FW-")
    per_battery = (
        df.groupby(["firmware_version", "battery_id"])["firmware_error"]
        .apply(lambda values: bool(values.any()))
        .reset_index(name="has_incident")
    )
    rates = (
        per_battery.groupby("firmware_version")
        .agg(
            battery_count=("battery_id", "nunique"),
            incident_battery_count=("has_incident", "sum"),
        )
        .reset_index()
    )
    rates["incident_rate"] = np.where(
        rates["battery_count"] > 0,
        rates["incident_battery_count"] / rates["battery_count"],
        0.0,
    )
    return rates.sort_values("firmware_version")


def _risk_level(diagnostics: list[dict[str, object]]) -> str:
    severities = {str(item["severity"]) for item in diagnostics}
    if "Critical" in severities:
        return "Critical"
    if "Warning" in severities:
        return "Warning"
    return "Normal"


def _recommended_next_step(diagnostics: list[dict[str, object]]) -> str:
    issue_types = {str(item["issue_type"]) for item in diagnostics}
    if "Overtemperature" in issue_types:
        return "Prioritize thermal inspection for affected units, then review firmware cohort trends."
    if "Firmware-associated incident increase" in issue_types:
        return "Compare incident rates against previous firmware and prepare rollback validation."
    if "Abnormal SOH degradation" in issue_types:
        return "Review cycle stress and schedule battery health inspection."
    return "Continue monitoring fleet telemetry."
