from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Contract, Performance, Player, Team


def create_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False), engine


def seed_if_empty(session: Session):
    if session.query(Player).count() > 0:
        return

    team1 = Team(name="Lions FC", founding_year=1986, stadium="North Arena")
    team2 = Team(name="Falcons United", founding_year=1992, stadium="City Dome")

    p1 = Player(name="Ali Raza", nationality="Pakistan", position="Forward", dob=date(1999, 3, 14))
    p2 = Player(name="Mason Lee", nationality="England", position="Midfielder", dob=date(2000, 7, 8))

    session.add_all([team1, team2, p1, p2])
    session.flush()

    session.add_all(
        [
            Contract(player_id=p1.id, team_id=team1.id, salary=150000, start_date=date(2024, 7, 1), end_date=date(2027, 6, 30)),
            Contract(player_id=p2.id, team_id=team2.id, salary=120000, start_date=date(2023, 7, 1), end_date=date(2026, 6, 30)),
            Performance(player_id=p1.id, season="2025", matches_played=30, goals=14, assists=7),
            Performance(player_id=p2.id, season="2025", matches_played=31, goals=6, assists=11),
        ]
    )
    session.commit()
