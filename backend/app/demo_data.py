from datetime import datetime, timedelta

import numpy as np
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app import models


def generate_synthetic_fleet(db: Session) -> dict[str, object]:
    """Create deterministic synthetic telemetry for an interview demo."""
    _clear_demo_tables(db)

    rng = np.random.default_rng(42)
    start_time = datetime(2026, 6, 1, 0, 0, 0)
    regions = ["California", "Texas", "Arizona", "Florida", "Nevada"]

    overtemperature_batteries = {"BAT-004", "BAT-007", "BAT-009"}
    soh_degradation_batteries = {"BAT-013", "BAT-014", "BAT-015"}
    firmware_incident_batteries = {"BAT-024", "BAT-025", "BAT-026", "BAT-027", "BAT-028"}

    batteries: list[models.Battery] = []
    telemetry_records: list[models.TelemetryRecord] = []

    for index in range(1, 31):
        battery_id = f"BAT-{index:03d}"
        firmware = _firmware_for_index(index)
        region = regions[(index - 1) % len(regions)]
        battery = models.Battery(
            battery_id=battery_id,
            site_region=region,
            installation_date=datetime(2025, 1, 15) + timedelta(days=index),
            model="ResidentialPack-A",
            firmware_version=firmware,
            status="active",
        )
        batteries.append(battery)

        base_soh = 98.5 - (index % 5) * 0.25
        for hour in range(72):
            timestamp = start_time + timedelta(hours=hour)
            day_cycle = np.sin((hour % 24) / 24 * 2 * np.pi)
            soc = np.clip(62 + 24 * day_cycle + rng.normal(0, 1.8), 15, 98)
            voltage = 382 + soc * 0.45 + rng.normal(0, 1.2)
            current = 9 * np.cos((hour % 24) / 24 * 2 * np.pi) + rng.normal(0, 1.0)
            temperature = 27 + 5 * max(day_cycle, 0) + rng.normal(0, 0.8)
            soh = base_soh - hour * 0.006 + rng.normal(0, 0.03)
            error_code = None

            if battery_id in overtemperature_batteries and 34 <= hour <= 48:
                temperature += 18 + rng.normal(0, 1.0)
                if hour % 5 == 0:
                    error_code = "TEMP_HIGH"

            if battery_id in soh_degradation_batteries:
                soh = base_soh - hour * 0.11 + rng.normal(0, 0.04)

            if battery_id in firmware_incident_batteries and hour >= 44 and hour % 6 == 0:
                error_code = "FW-210"
                current += rng.normal(4.0, 0.8)

            telemetry_records.append(
                models.TelemetryRecord(
                    battery_id=battery_id,
                    timestamp=timestamp,
                    voltage=round(float(voltage), 2),
                    current=round(float(current), 2),
                    temperature=round(float(temperature), 2),
                    state_of_charge=round(float(soc), 2),
                    state_of_health=round(float(soh), 2),
                    firmware_version=firmware,
                    error_code=error_code,
                    operating_mode="charging" if current > 0 else "discharging",
                    site_region=region,
                )
            )

    db.add_all(
        [
            models.FirmwareVersion(
                version="1.0.0",
                release_date=datetime(2025, 9, 1),
                description="Baseline stable firmware for demo fleet.",
                known_issues=None,
            ),
            models.FirmwareVersion(
                version="1.1.0",
                release_date=datetime(2026, 1, 20),
                description="Minor efficiency update.",
                known_issues=None,
            ),
            models.FirmwareVersion(
                version="2.1.0",
                release_date=datetime(2026, 5, 10),
                description="Demo firmware with injected incident-rate increase.",
                known_issues="Synthetic FW-210 incident pattern for portfolio demo.",
            ),
        ]
    )
    db.add_all(batteries)
    db.add_all(telemetry_records)
    db.commit()

    return {
        "message": "Synthetic demo data generated.",
        "battery_count": len(batteries),
        "telemetry_record_count": len(telemetry_records),
        "visible_scenarios": [
            "Overtemperature affecting selected batteries",
            "Abnormal state-of-health degradation",
            "Increased failure rate associated with firmware 2.1.0",
        ],
        "synthetic_data": True,
    }


def _clear_demo_tables(db: Session) -> None:
    for table in [
        models.CorrectiveActionEffectiveness,
        models.CorrectiveAction,
        models.DiagnosticResult,
        models.DiagnosticRule,
        models.TelemetryRecord,
        models.Battery,
        models.FirmwareVersion,
        models.ReliabilityKpiSnapshot,
    ]:
        db.execute(delete(table))
    db.commit()


def _firmware_for_index(index: int) -> str:
    if index <= 10:
        return "1.0.0"
    if index <= 20:
        return "1.1.0"
    return "2.1.0"
