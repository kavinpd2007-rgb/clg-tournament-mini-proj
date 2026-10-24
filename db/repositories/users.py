"""AppUser authentication and user provisioning repository."""
from typing import Any
from db.connection import connection_scope, transaction

class AppUserRepository:
    def get_by_username(self, username: str) -> dict[str, Any] | None:
        with connection_scope() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT `user_id`, `username`, `password_hash`, `role`, `is_active` "
                "FROM `AppUser` WHERE `username` = %s",
                (username,),
            )
            return cursor.fetchone()

    def upsert_user(self, username: str, password_hash: str, role: str = "Admin") -> int:
        if role not in {"Admin", "Viewer"}:
            raise ValueError("Role must be Admin or Viewer.")
        with transaction() as connection, connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT `user_id` FROM `AppUser` WHERE `username` = %s FOR UPDATE", (username,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE `AppUser` SET `password_hash` = %s, `role` = %s, `is_active` = TRUE "
                    "WHERE `user_id` = %s",
                    (password_hash, role, row["user_id"]),
                )
                return int(row["user_id"])
            cursor.execute(
                "INSERT INTO `AppUser` (`username`, `password_hash`, `role`, `is_active`) "
                "VALUES (%s, %s, %s, TRUE)",
                (username, password_hash, role),
            )
            return int(cursor.lastrowid)
