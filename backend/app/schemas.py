from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BatteryCreate(BaseModel):
    battery_id: str
    site_region: str
    installation_date: Optional[datetime] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    status: str = "active"


class BatteryRead(BatteryCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TelemetryRecordCreate(BaseModel):
    battery_id: str
    timestamp: datetime
    voltage: float
    current: float
    temperature: float
    state_of_charge: float
    state_of_health: float
    firmware_version: str
    error_code: Optional[str] = None
    operating_mode: str
    site_region: str


class TelemetryRecordRead(TelemetryRecordCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
