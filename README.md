# College Sports Tournament Manager

A Python 3.11+ Windows desktop application for managing college sports, teams, tournaments, match schedules, results, and reports. The UI uses ttkbootstrap 2.2.3 and MySQL 8.

## Setup (PowerShell)

```powershell
cd "C:\path\to\sports_app"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` in `.env`. Set `DB_TEST_NAME` to a separate database name ending in `_test`; the default is `CollegeSportsDB_test`. `MYSQL_DATABASE` is the application database. Never point `DB_TEST_NAME` at it.

## Create the database

Install/start MySQL 8 and create the application database and a MySQL account with the needed privileges. The reference SQL file is `reference/College_tournament.sql`. It contains demo CRUD statements and ends with a deliberately failing insert: **do not execute that file in one run**. In MySQL Workbench, execute the DDL, intended sample inserts, `TournamentStandings` view, `GetTeamMatches` procedure and `ValidateMatchResult` trigger statements only. Skip the demo UPDATE/INSERT/DELETE block and the final failing insert. The existing project reference file is retained unchanged.

For a test database, use the guarded builder below; it creates the schema directly from `sql/test_schema.sql`, including its test data and database objects. It drops and recreates only the configured `_test` database.

## Create an administrator

After the app database and `AppUser` table exist and `.env` is configured:

```powershell
python scripts\create_admin.py
```

Enter the username, role (Admin or Viewer), and password when prompted. Password input is hidden. Running the script again with the same username updates the password and role and reactivates the account.

## Run the app

```powershell
python -W default main.py
```

The app logs to `logs/app.log` and remembers window size in `.app_state/window.json`. The first sign-in requires an AppUser created with `scripts/create_admin.py`.

## Run tests

```powershell
python -m pytest -q
```

The DB integration tests are skipped unless `MYSQL_USER` is set. Configure the MySQL account with permission to create/drop databases, then explicitly rebuild the isolated test database with:

```powershell
python -m db.test_database --reset
```

The builder validates that `DB_TEST_NAME` is a simple identifier ending in `_test` before dropping or creating anything. The integration fixture also redirects repository connections to `DB_TEST_NAME`, not `MYSQL_DATABASE`.

## Features and rules

- Admin can create, view, update, and delete; Viewer is read-only.
- Teams must match the tournament sport, cannot play themselves, and must be scheduled inside tournament dates.
- Matches with a result cannot change teams/tournament; deleting them requires confirmation. Completed is set by saving a result. Results can be entered only for Scheduled/Ongoing matches without one; edits use Edit. Draws are displayed.
- Result scores are non-negative and the winner must agree with the score. Saving a result and setting Completed are atomic. Confirmed result deletion returns the match to Scheduled.
- There is no requirement that result-entry match dates be in the past.
- Standings come directly from the existing `TournamentStandings` view; Team Matches calls the existing `GetTeamMatches` procedure. The view, procedure and trigger are not redefined by the app.

## Troubleshooting

- **MySQL connection refused:** Start the MySQL service; verify `MYSQL_HOST` and `MYSQL_PORT`.
- **Access denied:** Check the MySQL username/password and that the account has access to the selected databases. The test builder additionally needs database create/drop privileges.
- **Unknown database:** Create the application database using the DDL workflow above. Confirm `MYSQL_DATABASE` matches it.
- **PowerShell blocks Activate.ps1:** You can run the venv interpreter directly without changing execution policy: `.\.venv\Scripts\python.exe main.py`.
- **Integration tests are skipped:** Set `MYSQL_USER` in `.env` and ensure the configured MySQL server is reachable. The tests use only `DB_TEST_NAME`.
- **Login fails:** Create or reset an AppUser with `python scripts\create_admin.py`; verify `AppUser.is_active` and the database connection.
- **Operation error:** Read `logs/app.log`; messages avoid logging password values.

## Known boundaries

The schema installation and DB integration checks require a configured MySQL 8 server. The application and service tests can be exercised without MySQL, but database-side view/procedure/trigger behavior and the full CRUD checklist require a reachable MySQL instance. A GUI walkthrough should be done after installing the schema and creating an Admin user.

