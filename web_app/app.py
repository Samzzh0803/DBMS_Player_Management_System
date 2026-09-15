import logging
from datetime import date

from flask import Flask, jsonify, render_template
from sqlalchemy import func

from .config import Config
from .db import create_session_factory, seed_if_empty
from .models import Contract, Performance, Player, Team

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    session_factory, engine = create_session_factory(app.config["DATABASE_URL"])
    app.session_factory = session_factory
    app.db_engine = engine

    if app.config["INIT_DB_ON_START"]:
        with app.session_factory() as session:
            seed_if_empty(session)
        logger.info("Database initialized/seeded")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    @app.get("/api/players")
    def players_api():
        with app.session_factory() as session:
            latest_contract_subquery = (
                session.query(
                    Contract.player_id,
                    func.max(Contract.start_date).label("max_start"),
                )
                .group_by(Contract.player_id)
                .subquery()
            )

            rows = (
                session.query(
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

            data = [
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
            return jsonify(data)

    @app.get("/")
    def home():
        with app.session_factory() as session:
            players = players_api().get_json()
        return render_template("index.html", players=players)

    return app


def _calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
