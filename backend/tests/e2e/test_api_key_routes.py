from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from price_driven_switch.__main__ import app
from price_driven_switch.services.tibber_connection import TibberConnection

client = TestClient(app)


@pytest.mark.e2e
def test_set_api_key():
    """Test setting API key with automatic restoration"""
    # Store original API key
    original_response = client.get("/api/settings/api-key")
    original_api_key = original_response.json()["api_key"]
    test_key = "test-api-key-123"

    try:
        # Test setting new API key
        response = client.post("/api/settings/api-key", json={"api_key": test_key})
        assert response.status_code == 200
        assert response.json() == {"message": "API key updated successfully"}
        # Verify the key was set
        verify_response = client.get("/api/settings/api-key")
        assert verify_response.json()["api_key"] == test_key

    finally:
        # Restore original API key
        restore_response = client.post(
            "/api/settings/api-key", json={"api_key": original_api_key}
        )
        assert restore_response.status_code == 200, "Failed to restore original API key"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_api_key_status_valid(tibber_test_token):
    """Test with a valid API key"""
    with patch(
        "price_driven_switch.services.tibber_connection.load_tibber_token",
        tibber_test_token,
    ):
        response = client.get("/api/settings/api-key-status")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "API key is valid"}


# @pytest.mark.e2e
# @pytest.mark.asyncio
# async def test_api_key_status_invalid():
#     """Test with an invalid API key"""
#     original_response = client.get("/api/settings/api-key")
#     original_api_key = original_response.json()["api_key"]
#     try:
#         response = client.post(
#             "/api/settings/api-key", json={"api_key": "invalid-token"}
#         )
#         response = client.get("/api/settings/api-key-status")
#         assert response.status_code == 200
#         assert response.json() == {
#             "status": "unauthorized",
#             "message": "API key is invalid or unauthorized",
#         }
#     finally:
#         restore_response = client.post(
#             "/api/settings/api-key", json={"api_key": original_api_key}
#         )
#         assert restore_response.status_code == 200, "Failed to restore original API key"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_api_key_status_server_error():
    """Test server error handling"""
    with patch.object(
        TibberConnection, "check_token_validity", side_effect=Exception("Test error")
    ):
        response = client.get("/api/settings/api-key-status")
        assert response.status_code == 500
        assert "Error checking API key status" in response.json()["detail"]
