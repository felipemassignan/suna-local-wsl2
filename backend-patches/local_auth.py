"""
Local authentication system
Sistema de autenticação local para substituir o Supabase Auth
"""

import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from utils.logger import logger
from utils.config import config, is_local_mode
from .local_database import local_db


class LocalAuthService:
    """Local authentication service"""
    
    def __init__(self):
        self.secret_key = "local-suna-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.token_expiry_hours = 24
    
    def generate_token(self, user_id: str, email: str = None) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user_id,
            "email": email or "local@example.com",
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow(),
            "iss": "suna-local"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    async def create_local_session(self, user_id: str = None) -> Dict[str, Any]:
        """Create a local session for the user"""
        user_id = user_id or config.LOCAL_USER_ID
        
        # Get or create user
        user = await local_db.get_user(user_id)
        if not user:
            user = await local_db.create_user("local@example.com", user_id)
        
        # Create session
        session = await local_db.create_session(user_id)
        
        return {
            "user": user,
            "session": session,
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"]
        }
    
    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token"""
        
        if not is_local_mode():
            return None
        
        # For local mode, accept any token and return default user
        if token and (token.startswith("local_token_") or token == "mock-token"):
            user = await local_db.get_user(config.LOCAL_USER_ID)
            return user
        
        # Try to verify JWT token
        payload = self.verify_token(token)
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                return await local_db.get_user(user_id)
        
        return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        
        if not is_local_mode():
            return None
        
        # In local mode, always allow refresh
        if refresh_token and refresh_token.startswith("local_refresh_"):
            return await self.create_local_session()
        
        return None


# Global auth service instance
local_auth = LocalAuthService()


async def verify_user_token(token: str) -> str:
    """
    Verify user token and return user ID
    Compatible with the original verify_user_token function
    """
    
    if not is_local_mode():
        # In non-local mode, would use original Supabase verification
        raise NotImplementedError("Non-local mode not implemented in this version")
    
    if not token:
        logger.warning("No token provided")
        return config.LOCAL_USER_ID  # Return default user in local mode
    
    # Remove Bearer prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    user = await local_auth.get_user_from_token(token)
    if user:
        return user["id"]
    
    # In local mode, always return default user as fallback
    logger.info("Token verification failed, using default local user")
    return config.LOCAL_USER_ID


async def get_account_id_from_thread(thread_id: str) -> str:
    """
    Get account ID from thread ID
    Compatible with the original function
    """
    
    if not is_local_mode():
        raise NotImplementedError("Non-local mode not implemented in this version")
    
    # In local mode, always return default project ID
    return config.LOCAL_PROJECT_ID


class LocalAuthMiddleware:
    """Middleware for local authentication"""
    
    def __init__(self):
        self.auth_service = local_auth
    
    async def authenticate_request(self, request) -> Optional[Dict[str, Any]]:
        """Authenticate request and return user info"""
        
        if not is_local_mode():
            return None
        
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # In local mode, create default session
            session = await self.auth_service.create_local_session()
            return session["user"]
        
        token = auth_header.replace("Bearer ", "")
        user = await self.auth_service.get_user_from_token(token)
        
        if not user:
            # In local mode, create default session as fallback
            session = await self.auth_service.create_local_session()
            return session["user"]
        
        return user
    
    def create_auth_response(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Create authentication response"""
        
        token = self.auth_service.generate_token(user["id"], user["email"])
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.auth_service.token_expiry_hours * 3600,
            "user": user
        }


# Global middleware instance
local_auth_middleware = LocalAuthMiddleware()

