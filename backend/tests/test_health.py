from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_process_is_up() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_unhandled_error_hides_internals() -> None:
    def boom() -> None:
        raise RuntimeError("mysql+pymysql://secret:secret@localhost/hidden")

    app.add_api_route("/api/_test_error", boom, methods=["GET"])
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/_test_error")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "secret" not in response.text
    assert "Traceback" not in response.text
