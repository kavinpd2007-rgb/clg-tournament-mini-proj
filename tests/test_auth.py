from __future__ import annotations

from services.auth import AuthenticationError, AuthService, hash_password, verify_password


class FakeUsers:
    def __init__(self, row):
        self.row = row

    def get_by_username(self, username: str):
        if self.row and self.row["username"] == username:
            return self.row
        return None


def test_hash_format_and_verification() -> None:
    encoded = hash_password("correct horse battery staple")
    algorithm, rounds, salt, digest = encoded.split("$")
    assert algorithm == "pbkdf2_sha256"
    assert int(rounds) >= 200_000
    assert len(salt) >= 32
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong", encoded)


def test_hash_refuses_less_than_required_rounds() -> None:
    import pytest
    with pytest.raises(ValueError):
        hash_password("secret", iterations=199_999)


def test_authentication_accepts_active_admin_and_viewer() -> None:
    for role in ("Admin", "Viewer"):
        row = {"user_id": 7, "username": "captain", "role": role, "is_active": 1, "password_hash": hash_password("a password")}
        session = AuthService(FakeUsers(row)).authenticate("captain", "a password")
        assert session.role == role
        assert session.can_write is (role == "Admin")


def test_authentication_rejects_inactive_unknown_and_wrong_password_generically() -> None:
    encoded = hash_password("correct")
    inactive = {"user_id": 1, "username": "captain", "role": "Admin", "is_active": 0, "password_hash": encoded}
    cases = (
        (FakeUsers(inactive), "captain", "correct"),
        (FakeUsers(inactive), "missing", "wrong"),
        (FakeUsers({**inactive, "is_active": 1}), "captain", "wrong"),
    )
    for repo, username, password in cases:
        try:
            AuthService(repo).authenticate(username, password)
        except AuthenticationError as exc:
            assert str(exc) == "Username or password is incorrect."
        else:
            raise AssertionError("Expected generic authentication failure")
