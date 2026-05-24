import httpx
import time
from typing import Optional, Any, Dict
from jose import jwt, jwk
from jose.utils import base64url_decode
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Security scheme for FastAPI
# We set auto_error=False to manually handle missing credentials with a 401 error
# instead of FastAPI's default 403.
security = HTTPBearer(auto_error=False)

# Cache for JWKS
_jwks_cache: Dict[str, Any] = {}
_jwks_last_fetch: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def get_clerk_jwks() -> Dict[str, Any]:
    """Fetch and cache Clerk's JWKS endpoint."""
    global _jwks_cache, _jwks_last_fetch

    now = time.time()
    if _jwks_cache and (now - _jwks_last_fetch < JWKS_CACHE_TTL):
        return _jwks_cache

    # In a real app, this URL would be derived from settings or environment
    # Clerk JWKS URL pattern: https://<your-domain>/.well-known/jwks.json
    # We'll use a placeholder or derive it if possible.
    # For now, we'll try to get it from settings if we added it, otherwise we'll need it.

    # NOTE: Since we don't have the exact domain, we assume it's provided in settings
    # or we construct it if we had the clerk domain.
    # For this implementation, we'll look for CLERK_JWKS_URL in settings.
    jwks_url = getattr(settings, "clerk_jwks_url", None)
    if not jwks_url:
        # Fallback/Default for development if not provided
        # This is often needed in .env
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL not configured")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_last_fetch = now
            return _jwks_cache
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch JWKS from Clerk: {str(e)}"
            )


async def verify_clerk_token(token: str) -> Dict[str, Any]:
    """Verify the Clerk JWT token signature and expiry."""
    jwks = await get_clerk_jwks()

    try:
        # Get the unverified header to find the kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Missing kid in token header")

        # Find the correct public key
        key_data = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            raise HTTPException(status_code=401, detail="Public key not found in JWKS")

        # Verify the token
        public_key = jwk.construct(key_data)
        message, encoded_sig = token.rsplit(".", 1)
        decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))

        if not public_key.verify(message.encode("utf-8"), decoded_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")

        # Decode and check claims (expiry is checked by jwt.decode)
        # Note: In production, you'd also check 'aud' and 'iss'
        payload = jwt.decode(
            token,
            key_data,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Adjust based on your setup
        )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_current_user_id(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    FastAPI dependency to get the current authenticated user's Clerk ID.
    Usage: user_id: str = Depends(get_current_user_id)
    """
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth.credentials
    payload = await verify_clerk_token(token)

    # Extract 'sub' claim as user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject claim")

    return user_id


async def get_current_user_from_query(token: str = None) -> str:
    """
    Get user ID from token passed as query parameter (for SSE streaming).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )
    
    try:
        payload = await verify_clerk_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing subject claim")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
