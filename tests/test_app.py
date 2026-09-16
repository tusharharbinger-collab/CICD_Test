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


def test_unknown_route_returns_404(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
