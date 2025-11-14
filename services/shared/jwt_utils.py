"""
Shared JWT utilities for all services.
Provides token validation, creation, and payload extraction.
"""
import os
from datetime import timedelta
import jwt
from functools import wraps
from rest_framework.exceptions import AuthenticationFailed


class JWTConfig:
    """Centralized JWT configuration."""
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    EXPIRATION_DELTA = timedelta(hours=2)


def decode_jwt_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string (without 'Bearer ' prefix)
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        AuthenticationFailed: If token is invalid or expired
    """
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = jwt.decode(
            token,
            JWTConfig.SECRET_KEY,
            algorithms=[JWTConfig.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")


def create_jwt_token(user_data: dict) -> str:
    """
    Create a JWT token from user data.
    
    Args:
        user_data: Dictionary with user info (must include 'id', 'email', 'user_id')
    
    Returns:
        JWT token string
    """
    payload = {
        **user_data,
        'exp': jwt.datetime.datetime.utcnow() + JWTConfig.EXPIRATION_DELTA
    }
    token = jwt.encode(
        payload,
        JWTConfig.SECRET_KEY,
        algorithm=JWTConfig.ALGORITHM
    )
    return token


def validate_auth_header(auth_header: str) -> dict:
    """
    Validate and extract user info from Authorization header.
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        Decoded token payload
    
    Raises:
        AuthenticationFailed: If header or token is invalid
    """
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthenticationFailed("Missing or invalid Authorization header")
    
    token = auth_header[7:]
    return decode_jwt_token(token)
