import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page_renders_and_shows_the_live_message(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.content_type
    assert "hello from smartcd-test" in resp.get_data(as_text=True)


def test_api_hello_returns_the_expected_json(client):
    resp = client.get("/api/hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "hello from smartcd-test"}


def test_healthz_returns_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_arbitrary_path_falls_back_to_the_index_page(client):
    """The platform's ALB forwards the full, unstripped path prefix it
    assigns a project (e.g. /api/v1/cicd-test) straight to the container —
    it never rewrites it back to "/". A genuinely unknown path must still
    render something real, not a bare 404, since it may just be this
    project's own live-URL prefix."""
    resp = client.get("/api/v1/cicd-test")
    assert resp.status_code == 200
    assert "hello from smartcd-test" in resp.get_data(as_text=True)


def test_prefixed_healthz_path_still_returns_the_real_health_check(client):
    resp = client.get("/api/v1/cicd-test/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_prefixed_hello_path_still_returns_the_real_json(client):
    resp = client.get("/api/v1/cicd-test/api/hello")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "hello from smartcd-test"}
