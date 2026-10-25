"""Password hashing and compact HS256 access tokens."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from uuid import UUID

from app.config.settings import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.urlsafe_b64decode(salt), 310_000
        )
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: UUID, role: str) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user_id), "role": role, "exp": int(time.time()) + settings.access_token_expire_minutes * 60}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}"
    signature = _b64(hmac.new(settings.auth_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> UUID | None:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}"
        expected = _b64(hmac.new(settings.auth_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        token_header = json.loads(base64.urlsafe_b64decode(header + "=" * (-len(header) % 4)))
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if token_header.get("alg") != "HS256" or int(claims["exp"]) <= int(time.time()):
            return None
        return UUID(claims["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
