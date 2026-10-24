"""Database error types and user-facing translations."""

from __future__ import annotations

from mysql.connector import Error as MySQLError


class DatabaseOperationError(RuntimeError):
    """A database failure with a safe, human-readable message."""

    def __init__(self, message: str, *, errno: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.errno = errno
        self.retryable = retryable


def translate_mysql_error(error: MySQLError) -> DatabaseOperationError:
    """Map common MySQL failures to actionable messages."""
    code = getattr(error, "errno", None)
    messages = {
        1062: "That value already exists. Choose a unique value and try again.",
        1451: "This record is still referenced by other records and cannot be deleted.",
        1452: "A selected related record no longer exists. Refresh the list and try again.",
        3819: "The value violates a database rule. Check the entered values and try again.",
        1045: "MySQL rejected the login. Check MYSQL_USER and MYSQL_PASSWORD in .env.",
        1049: "The configured database does not exist. Create the database before opening the app.",
    }
    if code in messages:
        return DatabaseOperationError(messages[code], errno=code)
    if code in {2002, 2003, 2006, 2013, 2055}:
        return DatabaseOperationError(
            "The MySQL connection was lost. Check the server and retry the operation.",
            errno=code,
            retryable=True,
        )
    return DatabaseOperationError("The database operation failed. Check the application log.", errno=code)
