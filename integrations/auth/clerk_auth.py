import os
import time
from typing import Optional, Tuple
from urllib.request import urlopen
from jose import jwk, jwt
from jose.utils import base64url_decode
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_AUDIENCE  = os.getenv("CLERK_AUDIENCE", "")
CLERK_ISSUER    = os.getenv("CLERK_ISSUER", "")
_JWKS_CACHE = {"ts": 0, "jwks": None}
def _get_jwks():
    if _JWKS_CACHE["jwks"] and (time.time() - _JWKS_CACHE["ts"] < 3600):
        return _JWKS_CACHE["jwks"]
    with urlopen(CLERK_JWKS_URL, timeout=10) as r:
        import json as _json
        _JWKS_CACHE["jwks"] = _json.loads(r.read())
        _JWKS_CACHE["ts"] = time.time()
    return _JWKS_CACHE["jwks"]
def _verify_jwt(token: str) -> dict:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    jwks = _get_jwks()
    key = next((k for k in jwks.get("keys",[]) if k.get("kid")==kid), None)
    if not key:
        raise exceptions.AuthenticationFailed("JWKS kid not found")
    public_key = jwk.construct(key)
    message, encoded_sig = token.rsplit(".", 1)
    decoded_sig = base64url_decode(encoded_sig.encode())
    if not public_key.verify(message.encode(), decoded_sig):
        raise exceptions.AuthenticationFailed("Invalid signature")
    claims = jwt.get_unverified_claims(token)
    if CLERK_AUDIENCE and claims.get("aud") not in [CLERK_AUDIENCE] + str(CLERK_AUDIENCE).split(","):
        raise exceptions.AuthenticationFailed("Invalid audience")
    if CLERK_ISSUER and claims.get("iss") != CLERK_ISSUER:
        raise exceptions.AuthenticationFailed("Invalid issuer")
    return claims
class ClerkJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"
    def authenticate(self, request) -> Optional[Tuple[object, None]]:
        if os.getenv("DJANGO_ENV") == "test" or os.getenv("USE_CLERK_AUTH") == "0":
            return None  # fall back to Session/Basic in REST_FRAMEWORK during tests
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[len("Bearer "):].strip()
        if not token:
            raise exceptions.AuthenticationFailed("Missing token")
        claims = _verify_jwt(token)
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        user.id = claims.get("sub")
        user.email = claims.get("email")
        return (user, None)
