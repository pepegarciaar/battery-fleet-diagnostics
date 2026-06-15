from collections.abc import Sequence
from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.analysis import (
    build_battery_detail,
    build_battery_health,
    build_corrective_action_validation,
    build_dashboard_summary,
    build_diagnostics,
    build_failure_tree,
    build_fmea_register,
    build_firmware_incidents,
)
from backend.app.database import get_db, init_db
from backend.app.demo_data import generate_synthetic_fleet
from backend.app.schemas import (
    BatteryCreate,
    BatteryRead,
    TelemetryRecordCreate,
    TelemetryRecordRead,
)


def ensure_demo_data(db: Session) -> None:
    """Seed synthetic demo data when a dashboard endpoint has no records yet."""
    battery_count = db.scalar(select(func.count(models.Battery.id)))
    if battery_count == 0:
        generate_synthetic_fleet(db)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Create database tables when the API starts."""
    init_db()
    yield


app = FastAPI(
    title="Battery Fleet Diagnostic & Reliability Analyzer",
    version="0.1.0",
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    """Allow Vercel rewrites to call the same API under /api."""
    if request.scope["path"].startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:]
    return await call_next(request)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/batteries",
    response_model=BatteryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_battery(
    battery: BatteryCreate,
    db: Session = Depends(get_db),
) -> models.Battery:
    db_battery = models.Battery(**battery.model_dump())
    db.add(db_battery)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Battery already exists.",
        ) from exc

    db.refresh(db_battery)
    return db_battery


@app.get("/batteries", response_model=list[BatteryRead])
def list_batteries(db: Session = Depends(get_db)) -> Sequence[models.Battery]:
    ensure_demo_data(db)
    result = db.scalars(select(models.Battery).order_by(models.Battery.battery_id))
    return result.all()


@app.get("/batteries/{battery_id}")
def get_battery_detail(
    battery_id: str,
    db: Session = Depends(get_db),
) -> dict:
    ensure_demo_data(db)
    detail = build_battery_detail(db, battery_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battery not found.",
        )
    return detail


@app.post(
    "/telemetry",
    response_model=TelemetryRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_telemetry_record(
    telemetry: TelemetryRecordCreate,
    db: Session = Depends(get_db),
) -> models.TelemetryRecord:
    battery_exists = db.scalar(
        select(models.Battery).where(models.Battery.battery_id == telemetry.battery_id)
    )
    if battery_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battery not found.",
        )

    db_telemetry = models.TelemetryRecord(**telemetry.model_dump())
    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)
    return db_telemetry


@app.get("/telemetry", response_model=list[TelemetryRecordRead])
def list_telemetry_records(
    db: Session = Depends(get_db),
) -> Sequence[models.TelemetryRecord]:
    ensure_demo_data(db)
    result = db.scalars(
        select(models.TelemetryRecord).order_by(models.TelemetryRecord.timestamp)
    )
    return result.all()


@app.get("/batteries/{battery_id}/telemetry", response_model=list[TelemetryRecordRead])
def list_battery_telemetry(
    battery_id: str,
    db: Session = Depends(get_db),
) -> Sequence[models.TelemetryRecord]:
    ensure_demo_data(db)
    result = db.scalars(
        select(models.TelemetryRecord)
        .where(models.TelemetryRecord.battery_id == battery_id)
        .order_by(models.TelemetryRecord.timestamp)
    )
    return result.all()


@app.post("/demo/generate")
def generate_demo_data(db: Session = Depends(get_db)) -> dict[str, object]:
    return generate_synthetic_fleet(db)


@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_data(db)
    return build_dashboard_summary(db)


@app.get("/dashboard/firmware-incidents")
def dashboard_firmware_incidents(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    ensure_demo_data(db)
    return build_firmware_incidents(db)


@app.get("/dashboard/battery-health")
def dashboard_battery_health(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_data(db)
    return build_battery_health(db)


@app.get("/diagnostics")
def diagnostics(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    ensure_demo_data(db)
    return build_diagnostics(db)


@app.get("/reliability/fmea")
def fmea_register() -> list[dict[str, object]]:
    return build_fmea_register()


@app.get("/reliability/failure-tree")
def failure_tree() -> dict[str, object]:
    return build_failure_tree()


@app.get("/reliability/corrective-action-validation")
def corrective_action_validation(db: Session = Depends(get_db)) -> dict[str, object]:
    ensure_demo_data(db)
    return build_corrective_action_validation(db)
