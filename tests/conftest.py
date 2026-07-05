import os

import httpx
import pytest

BASE_URL = os.environ.get("PAYFLOW_BASE_URL", "http://127.0.0.1:8000")


def _is_healthy():
    try:
        return httpx.get(f"{BASE_URL}/api/health", timeout=2).status_code == 200
    except httpx.TransportError:
        return False


@pytest.fixture(scope="session")
def live_server():
    if not _is_healthy():
        pytest.exit(
            f"PayFlow API is not reachable at {BASE_URL}. "
            "Start the service in the target environment, or point "
            "PAYFLOW_BASE_URL at a running instance.",
            returncode=1,
        )
    return BASE_URL


@pytest.fixture
def api_client(live_server):
    with httpx.Client(base_url=live_server) as client:
        yield client


@pytest.fixture(autouse=True)
def _reset_state(live_server):
    httpx.post(f"{live_server}/api/admin/reset")
    yield
