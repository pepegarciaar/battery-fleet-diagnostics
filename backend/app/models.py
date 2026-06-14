from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Battery(Base):
    __tablename__ = "batteries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    battery_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    site_region: Mapped[str] = mapped_column(String(64), index=True)
    installation_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")

    telemetry_records: Mapped[list["TelemetryRecord"]] = relationship(
        back_populates="battery",
        cascade="all, delete-orphan",
    )
    diagnostic_results: Mapped[list["DiagnosticResult"]] = relationship(
        back_populates="battery",
    )
    corrective_actions: Mapped[list["CorrectiveAction"]] = relationship(
        back_populates="battery",
    )


class FirmwareVersion(Base):
    __tablename__ = "firmware_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_issues: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    battery_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("batteries.battery_id"),
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    voltage: Mapped[float] = mapped_column(Float)
    current: Mapped[float] = mapped_column(Float)
    temperature: Mapped[float] = mapped_column(Float)
    state_of_charge: Mapped[float] = mapped_column(Float)
    state_of_health: Mapped[float] = mapped_column(Float)
    firmware_version: Mapped[str] = mapped_column(String(32), index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    operating_mode: Mapped[str] = mapped_column(String(32), index=True)
    site_region: Mapped[str] = mapped_column(String(64), index=True)

    battery: Mapped["Battery"] = relationship(back_populates="telemetry_records")


class DiagnosticRule(Base):
    __tablename__ = "diagnostic_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[int] = mapped_column(Integer, default=1)

    diagnostic_results: Mapped[list["DiagnosticResult"]] = relationship(
        back_populates="rule",
    )


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    battery_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("batteries.battery_id"),
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    rule_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("diagnostic_rules.id"),
        nullable=True,
    )
    diagnostic_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    observed_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    root_cause_hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")

    battery: Mapped["Battery"] = relationship(back_populates="diagnostic_results")
    rule: Mapped[Optional["DiagnosticRule"]] = relationship(back_populates="diagnostic_results")


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    battery_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("batteries.battery_id"),
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    implemented_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    implemented_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    related_diagnostic_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("diagnostic_results.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="planned")

    battery: Mapped["Battery"] = relationship(back_populates="corrective_actions")
    effectiveness_records: Mapped[list["CorrectiveActionEffectiveness"]] = relationship(
        back_populates="corrective_action",
        cascade="all, delete-orphan",
    )


class CorrectiveActionEffectiveness(Base):
    __tablename__ = "corrective_action_effectiveness"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    corrective_action_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("corrective_actions.id"),
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    before_value: Mapped[float] = mapped_column(Float)
    after_value: Mapped[float] = mapped_column(Float)
    improvement_percent: Mapped[float] = mapped_column(Float)
    evaluation_window_days: Mapped[int] = mapped_column(Integer)
    effective: Mapped[int] = mapped_column(Integer, default=0)

    corrective_action: Mapped["CorrectiveAction"] = relationship(
        back_populates="effectiveness_records",
    )


class ReliabilityKpiSnapshot(Base):
    __tablename__ = "reliability_kpi_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    fleet_size: Mapped[int] = mapped_column(Integer)
    failure_rate: Mapped[float] = mapped_column(Float)
    mtbf_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_incident_rate: Mapped[float] = mapped_column(Float)
    voltage_deviation_rate: Mapped[float] = mapped_column(Float)
    soh_degradation_rate: Mapped[float] = mapped_column(Float)
    firmware_failure_rate: Mapped[float] = mapped_column(Float)
    repeated_error_code_count: Mapped[int] = mapped_column(Integer)
