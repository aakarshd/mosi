def test_health_returns_200(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200


def test_health_response_shape(client):
    data = client.get("/api/v1/health/").json()
    assert data["status"] == "healthy"
    assert data["service"] == "mosi-api"
    assert "version" in data
