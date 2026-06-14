from fastapi.testclient import TestClient


def test_synthetic_data_generation_creates_expected_fleet(client: TestClient) -> None:
    response = client.post("/demo/generate")

    assert response.status_code == 200
    data = response.json()
    assert data["battery_count"] == 30
    assert data["telemetry_record_count"] == 2160
    assert len(data["visible_scenarios"]) == 3


def test_overtemperature_detection(client: TestClient) -> None:
    client.post("/demo/generate")

    response = client.get("/diagnostics")

    assert response.status_code == 200
    diagnostics = response.json()
    overtemperature = [
        item for item in diagnostics if item["issue_type"] == "Overtemperature"
    ]
    assert overtemperature
    assert {"BAT-004", "BAT-007", "BAT-009"}.issubset(
        {item["battery_id"] for item in overtemperature}
    )


def test_critical_overtemperature_detection(client: TestClient) -> None:
    client.post("/demo/generate")

    response = client.get("/diagnostics")

    assert response.status_code == 200
    diagnostics = response.json()
    critical = [
        item
        for item in diagnostics
        if item["battery_id"] == "BAT-009" and item["severity"] == "Critical"
    ]
    assert critical
    assert critical[0]["issue_type"] == "Overtemperature"


def test_soh_degradation_detection(client: TestClient) -> None:
    client.post("/demo/generate")

    response = client.get("/diagnostics")

    assert response.status_code == 200
    diagnostics = response.json()
    soh_issues = [
        item for item in diagnostics if item["issue_type"] == "Abnormal SOH degradation"
    ]
    assert soh_issues
    assert {"BAT-013", "BAT-014", "BAT-015"}.issubset(
        {item["battery_id"] for item in soh_issues}
    )


def test_firmware_incident_aggregation(client: TestClient) -> None:
    client.post("/demo/generate")

    response = client.get("/dashboard/firmware-incidents")

    assert response.status_code == 200
    rows = response.json()
    firmware_210 = next(row for row in rows if row["firmware_version"] == "2.1.0")
    assert firmware_210["battery_count"] == 10
    assert firmware_210["incident_battery_count"] == 5
    assert firmware_210["incident_rate"] == 0.5
