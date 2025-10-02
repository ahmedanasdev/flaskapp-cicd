import os
import pytest
from app import create_app

@pytest.fixture
def client():
    os.environ["USE_MEMORY_DB"] = "1"
    app = create_app()
    with app.test_client() as c:
        yield c

def test_post_and_get(client):
    rv = client.post("/data", json={"value":"x"})
    assert rv.status_code == 201
    data = client.get("/data").get_json()
    assert data == [{"value":"x"}]
