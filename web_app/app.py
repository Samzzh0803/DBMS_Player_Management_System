import logging
from datetime import date, timedelta

from flask import Flask, jsonify, redirect, render_template, request, session as flask_session, url_for
from sqlalchemy import func

from .config import Config
from .db import create_session_factory, seed_if_empty
from .models import Contract, MatchTeam, Performance, Player, PlayerLogin, PlayerOffer, Team, TeamLogin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]

    session_factory, engine = create_session_factory(app.config["DATABASE_URL"])
    app.session_factory = session_factory
    app.db_engine = engine

    if app.config["INIT_DB_ON_START"]:
        with app.session_factory() as db_session:
            seed_if_empty(db_session)
        logger.info("Database initialized/seeded")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    @app.get("/")
    def home():
        players = _fetch_players(app)
        return render_template("index.html", players=players)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            role = request.form.get("role", "")
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            user = _authenticate_user(app, role, username, password)
            if user is None:
                error = "Invalid credentials."
            else:
                flask_session["role"] = role
                flask_session["user_id"] = user
                if role == "team":
                    return redirect(url_for("team_portal", team_id=user))
                if role == "player":
                    return redirect(url_for("player_portal", player_id=user))
                return redirect(url_for("admin_portal"))

        return render_template("login.html", error=error)

    @app.get("/logout")
    def logout():
        flask_session.clear()
        return redirect(url_for("home"))

    @app.get("/team/<int:team_id>")
    def team_portal(team_id: int):
        summary = _fetch_team_summary(app, team_id)
        players = _fetch_team_players(app, team_id)
        if not summary:
            return "Team not found", 404
        return render_template("team_portal.html", summary=summary, players=players)

    @app.get("/player/<int:player_id>")
    def player_portal(player_id: int):
        profile = _fetch_player_profile(app, player_id)
        if not profile:
            return "Player not found", 404
        return render_template("player_portal.html", profile=profile)

    @app.get("/admin")
    def admin_portal():
        with app.session_factory() as db_session:
            stats = {
                "players": db_session.query(Player).count(),
                "teams": db_session.query(Team).count(),
                "contracts": db_session.query(Contract).count(),
                "offers": db_session.query(PlayerOffer).count(),
            }
        return render_template("admin_portal.html", stats=stats)

    @app.get("/contracts/expiring")
    def expiring_contracts_page():
        contracts = _fetch_expiring_contracts(app)
        return render_template("expiring_contracts.html", contracts=contracts)

    @app.get("/api/players")
    def players_api():
        return jsonify(_fetch_players(app))

    @app.get("/api/contracts/expiring")
    def expiring_contracts_api():
        return jsonify(_fetch_expiring_contracts(app))

    @app.get("/api/teams/<int:team_id>/summary")
    def team_summary_api(team_id: int):
        summary = _fetch_team_summary(app, team_id)
        if not summary:
            return jsonify({"error": "Team not found"}), 404
        return jsonify(summary)

    @app.get("/api/teams/<int:team_id>/players")
    def team_players_api(team_id: int):
        return jsonify(_fetch_team_players(app, team_id))

    @app.get("/api/players/<int:player_id>/summary")
    def player_summary_api(player_id: int):
        profile = _fetch_player_profile(app, player_id)
        if not profile:
            return jsonify({"error": "Player not found"}), 404
        return jsonify(profile)

    return app


def _authenticate_user(app: Flask, role: str, username: str, password: str):
    if role == "admin":
        return 0 if username == "admin" and password == "admin1" else None

    with app.session_factory() as db_session:
        if role == "team":
            row = db_session.query(TeamLogin).filter(TeamLogin.username == username).first()
            if row and row.password == password:
                return row.team_id
            return None

        if role == "player":
            row = db_session.query(PlayerLogin).filter(PlayerLogin.username == username).first()
            if row and row.password == password:
                return row.player_id
            return None

    return None


def _fetch_players(app: Flask):
    with app.session_factory() as db_session:
        latest_contract_subquery = (
            db_session.query(
                Contract.player_id,
                func.max(Contract.start_date).label("max_start"),
            )
            .group_by(Contract.player_id)
            .subquery()
        )

        rows = (
            db_session.query(
                Player.id,
                Player.name,
                Player.position,
                Player.dob,
                func.coalesce(Team.name, "No Team").label("team"),
                func.coalesce(func.sum(Performance.goals), 0).label("goals"),
                func.coalesce(func.sum(Performance.assists), 0).label("assists"),
            )
            .outerjoin(Performance, Performance.player_id == Player.id)
            .outerjoin(
                latest_contract_subquery,
                latest_contract_subquery.c.player_id == Player.id,
            )
            .outerjoin(
                Contract,
                (Contract.player_id == Player.id)
                & (Contract.start_date == latest_contract_subquery.c.max_start),
            )
            .outerjoin(Team, Team.id == Contract.team_id)
            .group_by(Player.id, Player.name, Player.position, Player.dob, Team.name)
            .order_by(Player.name)
            .all()
        )

        return [
            {
                "id": row.id,
                "name": row.name,
                "position": row.position,
                "age": _calculate_age(row.dob),
                "team": row.team,
                "goals": int(row.goals),
                "assists": int(row.assists),
            }
            for row in rows
        ]


def _fetch_expiring_contracts(app: Flask):
    today = date.today()
    upper_bound = today + timedelta(days=90)

    with app.session_factory() as db_session:
        latest_contract_subquery = (
            db_session.query(
                Contract.player_id,
                func.max(Contract.start_date).label("max_start"),
            )
            .group_by(Contract.player_id)
            .subquery()
        )

        rows = (
            db_session.query(
                Player.id.label("player_id"),
                Player.name.label("player_name"),
                Team.id.label("team_id"),
                Team.name.label("team_name"),
                Contract.end_date,
            )
            .join(latest_contract_subquery, latest_contract_subquery.c.player_id == Player.id)
            .join(
                Contract,
                (Contract.player_id == Player.id)
                & (Contract.start_date == latest_contract_subquery.c.max_start),
            )
            .join(Team, Team.id == Contract.team_id)
            .filter(Contract.end_date >= today)
            .filter(Contract.end_date <= upper_bound)
            .order_by(Contract.end_date.asc())
            .all()
        )

        return [
            {
                "player_id": row.player_id,
                "player_name": row.player_name,
                "team_id": row.team_id,
                "team_name": row.team_name,
                "contract_end_date": row.end_date.isoformat(),
            }
            for row in rows
        ]


def _fetch_team_summary(app: Flask, team_id: int):
    with app.session_factory() as db_session:
        team = db_session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None

        matches = (
            db_session.query(MatchTeam)
            .filter((MatchTeam.home_team_id == team_id) | (MatchTeam.away_team_id == team_id))
            .all()
        )

        season = 2025
        wins, draws, losses = _calculate_record(matches, team_id)
        current_matches = [m for m in matches if m.season == season]
        cw, cd, cl = _calculate_record(current_matches, team_id)

        goals_for = 0
        goals_against = 0
        for m in current_matches:
            if m.home_team_id == team_id:
                goals_for += m.home_team_score
                goals_against += m.away_team_score
            else:
                goals_for += m.away_team_score
                goals_against += m.home_team_score

        total = wins + draws + losses
        win_pct = round((wins * 100.0 / total), 2) if total else 0.0

        return {
            "team_id": team.id,
            "team_name": team.name,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_percentage": win_pct,
            "current_season": season,
            "current_wins": cw,
            "current_draws": cd,
            "current_losses": cl,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against,
        }


def _fetch_team_players(app: Flask, team_id: int):
    with app.session_factory() as db_session:
        latest_contract_subquery = (
            db_session.query(
                Contract.player_id,
                func.max(Contract.start_date).label("max_start"),
            )
            .group_by(Contract.player_id)
            .subquery()
        )

        rows = (
            db_session.query(Player.id, Player.name, Player.nationality, Player.position, Player.dob)
            .join(latest_contract_subquery, latest_contract_subquery.c.player_id == Player.id)
            .join(
                Contract,
                (Contract.player_id == Player.id)
                & (Contract.start_date == latest_contract_subquery.c.max_start),
            )
            .filter(Contract.team_id == team_id)
            .order_by(Player.name)
            .all()
        )

        return [
            {
                "player_id": r.id,
                "name": r.name,
                "nationality": r.nationality,
                "position": r.position,
                "age": _calculate_age(r.dob),
            }
            for r in rows
        ]


def _fetch_player_profile(app: Flask, player_id: int):
    with app.session_factory() as db_session:
        player = db_session.query(Player).filter(Player.id == player_id).first()
        if not player:
            return None

        latest_contract_subquery = (
            db_session.query(
                Contract.player_id,
                func.max(Contract.start_date).label("max_start"),
            )
            .group_by(Contract.player_id)
            .subquery()
        )

        team_row = (
            db_session.query(Team.name)
            .join(Contract, Contract.team_id == Team.id)
            .join(
                latest_contract_subquery,
                (latest_contract_subquery.c.player_id == Contract.player_id)
                & (latest_contract_subquery.c.max_start == Contract.start_date),
            )
            .filter(Contract.player_id == player_id)
            .first()
        )

        perf_rows = db_session.query(Performance).filter(Performance.player_id == player_id).all()

        overall = {
            "matches_played": sum(x.matches_played for x in perf_rows),
            "goals": sum(x.goals for x in perf_rows),
            "assists": sum(x.assists for x in perf_rows),
        }

        latest_season = None
        if perf_rows:
            latest = sorted(perf_rows, key=lambda x: x.season, reverse=True)[0]
            latest_season = {
                "season": latest.season,
                "matches_played": latest.matches_played,
                "goals": latest.goals,
                "assists": latest.assists,
            }

        offers = (
            db_session.query(PlayerOffer.id, Team.name, PlayerOffer.amount_offered)
            .join(Team, Team.id == PlayerOffer.team_id)
            .filter(PlayerOffer.player_id == player_id)
            .order_by(PlayerOffer.amount_offered.desc())
            .all()
        )

        return {
            "player_id": player.id,
            "player_name": player.name,
            "team_name": team_row[0] if team_row else "No Team",
            "position": player.position,
            "age": _calculate_age(player.dob),
            "overall": overall,
            "current": latest_season,
            "offers": [
                {"offer_id": x.id, "team_name": x.name, "amount_offered": float(x.amount_offered)}
                for x in offers
            ],
        }


def _calculate_record(matches: list[MatchTeam], team_id: int):
    wins, draws, losses = 0, 0, 0
    for m in matches:
        if m.result == "DRAW":
            draws += 1
        elif m.result == "HOME" and m.home_team_id == team_id:
            wins += 1
        elif m.result == "AWAY" and m.away_team_id == team_id:
            wins += 1
        else:
            losses += 1
    return wins, draws, losses


def _calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=10000)
