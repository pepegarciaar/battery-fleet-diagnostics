from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app import models
from backend.app.database import Base


def test_database_initialization_creates_expected_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    testing_session = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "batteries",
        "telemetry_records",
        "diagnostic_rules",
        "diagnostic_results",
        "firmware_versions",
        "corrective_actions",
        "corrective_action_effectiveness",
        "reliability_kpi_snapshots",
    }

    assert expected_tables.issubset(table_names)

    # Keep a tiny session smoke test so the import is clearly exercised.
    with testing_session() as session:
        assert session.is_active
        assert models.Battery.__tablename__ == "batteries"
