from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
MANCHESTER = {"X-Dev-Officer-ID": "101"}
CLARENDON = {"X-Dev-Officer-ID": "202"}


def test_authentication_is_required():
    response = client.get("/incidents")
    assert response.status_code == 401


def test_officer_only_sees_assigned_parish():
    response = client.get("/incidents?days=20", headers=MANCHESTER)
    assert response.status_code == 200
    assert response.json()
    assert all(row["parish"] == "Manchester" for row in response.json())


def test_client_cannot_select_another_parish():
    # Extra query parameters do not override the identity's parish.
    response = client.get("/incidents?days=20&parish=Clarendon", headers=MANCHESTER)
    assert response.status_code == 200
    assert all(row["parish"] == "Manchester" for row in response.json())


def test_cross_parish_incident_id_is_denied_without_disclosing_existence():
    response = client.get("/incidents/1003", headers=MANCHESTER)
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_cross_parish_photo_id_is_denied():
    response = client.get("/media/5003", headers=MANCHESTER)
    assert response.status_code == 404


def test_photo_for_authorized_incident_is_available():
    response = client.get("/media/5001", headers=MANCHESTER)
    assert response.status_code == 200
    assert response.json()["incident_id"] == 1001


def test_rag_never_returns_other_parish_records():
    response = client.post(
        "/rag/query",
        headers=MANCHESTER,
        json={"question": "rain incidents and DUI", "days": 20},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parish_scope"] == "Manchester"
    assert all(row["parish"] == "Manchester" for row in body["incidents"])
    assert set(body["evidence_incident_ids"]).issubset(
        {row["incident_id"] for row in body["incidents"]}
    )


def test_date_window_excludes_old_records():
    response = client.get("/incidents?days=20", headers=MANCHESTER)
    ids = {row["incident_id"] for row in response.json()}
    assert 1005 not in ids


def test_query_schema_rejects_invalid_day_range():
    response = client.post(
        "/rag/query",
        headers=MANCHESTER,
        json={"question": "rain incidents", "days": 9999},
    )
    assert response.status_code == 422
