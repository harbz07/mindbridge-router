"""
Authentication middleware for API key validation.
"""

import os

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the API key from the Authorization header.

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        str: The validated API key

    Raises:
        HTTPException: If the API key is invalid or missing
    """
    expected_key = os.getenv("MINDBRIDGE_API_KEY")

    if not expected_key:
        raise HTTPException(status_code=500, detail="Server configuration error: MINDBRIDGE_API_KEY not set")

    if credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return credentials.credentials
