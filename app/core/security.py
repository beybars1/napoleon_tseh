"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token settings
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: The JWT token to verify
        
    Returns:
        dict: The decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode an access token and return the username
    
    Args:
        token: The JWT access token
        
    Returns:
        str: The username if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass


class InvalidTokenError(SecurityError):
    """Exception raised when token is invalid"""
    pass


class ExpiredTokenError(SecurityError):
    """Exception raised when token has expired"""
    pass


def validate_token_payload(payload: dict) -> dict:
    """
    Validate JWT token payload
    
    Args:
        payload: The decoded JWT payload
        
    Returns:
        dict: The validated payload
        
    Raises:
        InvalidTokenError: If payload is invalid
        ExpiredTokenError: If token has expired
    """
    if not payload:
        raise InvalidTokenError("Invalid token payload")
    
    # Check expiration
    exp = payload.get("exp")
    if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
        raise ExpiredTokenError("Token has expired")
    
    # Check required fields
    if not payload.get("sub"):
        raise InvalidTokenError("Token missing subject")
    
    return payload


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token
    
    Args:
        email: The user's email address
        
    Returns:
        str: The password reset token
    """
    expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
    to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return the email
    
    Args:
        token: The password reset token
        
    Returns:
        str: The email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's a password reset token
        if payload.get("type") != "password_reset":
            return None
            
        email: str = payload.get("sub")
        return email
    except JWTError:
        return None 