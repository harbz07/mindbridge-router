def test_models_requires_auth(client):
    response = client.get("/v1/models")
    assert response.status_code == 403


def test_models_rejects_bad_key(client):
    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


def test_models_accepts_valid_key(client, auth_headers):
    response = client.get("/v1/models", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)


def test_providers_requires_auth(client):
    response = client.get("/providers")
    assert response.status_code == 403


def test_completions_requires_auth(client):
    response = client.post("/v1/chat/completions", json={"model": "test", "messages": []})
    assert response.status_code == 403
