"""Read-only report and dashboard data composition."""
from __future__ import annotations
from db.repositories.reports import ReportRepository
from db.repositories.tournaments import TournamentRepository
from db.repositories.teams import TeamRepository


class ReportService:
    def __init__(self, reports=None, tournaments=None, teams=None):
        self.reports = reports or ReportRepository()
        self.tournaments = tournaments or TournamentRepository()
        self.teams = teams or TeamRepository()

    def filters(self):
        return {"tournaments": self.tournaments.list_all(), "teams": self.teams.list_all()}

    def run(self, report: str, filter_id: int | None = None):
        if report == "Standings":
            return self.reports.standings(filter_id)
        if report == "Team Matches":
            if filter_id is None:
                return []
            return self.reports.team_matches(filter_id)
        if report == "Wins per team":
            return self.reports.wins_per_team()
        if report == "Matches played":
            return self.reports.matches_played()
        if report == "Total score per team":
            return self.reports.total_score_per_team()
        if report == "Upcoming matches":
            return self.reports.upcoming_matches()
        raise ValueError("Select a valid report.")

    def dashboard(self):
        counts = self.reports.dashboard_counts()
        upcoming = self.reports.upcoming_matches()[:6]
        standings = self.reports.standings()
        top = sorted(standings, key=lambda row: (row.get("points", 0), row.get("wins", 0)), reverse=True)[:5]
        return {"counts": counts, "upcoming": upcoming, "top": top}
