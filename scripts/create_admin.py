"""Create or rotate an AppUser password without exposing it in a command argument."""
from __future__ import annotations

import getpass
import logging

from config import configure_logging
from db.repositories.users import AppUserRepository
from services.auth import hash_password


def main() -> None:
    configure_logging()
    username = input("Username: ").strip()
    if not username:
        raise SystemExit("Username is required.")
    role = input("Role [Admin/Viewer, default Admin]: ").strip().title() or "Admin"
    if role not in {"Admin", "Viewer"}:
        raise SystemExit("Role must be Admin or Viewer.")
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match.")
    try:
        encoded = hash_password(password)
        user_id = AppUserRepository().upsert_user(username, encoded, role)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    logging.getLogger(__name__).info("Created or updated AppUser id=%s role=%s", user_id, role)
    print(f"User '{username}' is ready with role {role}.")


if __name__ == "__main__":
    main()
