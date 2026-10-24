"""Password hashing and AppUser login rules."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Protocol

PBKDF2_ITERATIONS = 260_000
_SALT_BYTES = 16


class UserLookup(Protocol):
    def get_by_username(self, username: str) -> dict[str, object] | None: ...


class AuthenticationError(ValueError):
    """Generic login failure that does not reveal whether a user exists."""


@dataclass(frozen=True, slots=True)
class UserSession:
    user_id: int
    username: str
    role: str

    @property
    def can_write(self) -> bool:
        return self.role == "Admin"


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> str:
    if iterations < 200_000:
        raise ValueError("Password hashing must use at least 200000 iterations.")
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded.split("$", 3)
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (AttributeError, TypeError, ValueError):
        return False
    if algorithm != "pbkdf2_sha256" or iterations < 200_000 or len(salt) < 16:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


class AuthService:
    def __init__(self, users: UserLookup):
        self._users = users

    def authenticate(self, username: str, password: str) -> UserSession:
        if not username.strip() or not password:
            raise AuthenticationError("Username or password is incorrect.")
        row = self._users.get_by_username(username.strip())
        if row is None or not bool(row.get("is_active")) or not verify_password(password, str(row.get("password_hash", ""))):
            raise AuthenticationError("Username or password is incorrect.")
        role = str(row.get("role", ""))
        if role not in {"Admin", "Viewer"}:
            raise AuthenticationError("Username or password is incorrect.")
        return UserSession(int(row["user_id"]), str(row["username"]), role)
