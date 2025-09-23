import pytest
import requests

from arcadedb_python.api.sync import SyncClient


def test_sync_client_instantiation():
    client = SyncClient(
        host="localhost", port="2480", username="root", password="playwithdata"
    )
    assert client.host == "localhost"
    assert client.port == 2480
    assert client.protocol == "http"
    assert client.url == "http://localhost:2480"
    assert client.username == "root"
    assert client.password == "playwithdata"
    assert client.headers == {"Content-Type": "application/json"}
    assert str(client) == "<host=localhost port=2480 user=root>"
    assert repr(client) == str(client)


def test_sync_client_get():
    endpoint = "/api/v1/server"
    client = SyncClient(
        host="localhost", port="2480", username="root", password="playwithdata"
    )
    # Test that we can make a GET request (should return server info)
    response = client.get(endpoint)
    assert response is not None


def test_sync_client_post():
    endpoint = "/api/v1/server"
    client = SyncClient(
        host="localhost", port="2480", username="root", password="playwithdata"
    )
    # Test that we can make a POST request with a valid command
    response = client.post(endpoint, payload={"command": "list databases"})
    assert response is not None
