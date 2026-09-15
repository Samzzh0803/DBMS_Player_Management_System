from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import (
    Base,
    Contract,
    MatchTeam,
    Performance,
    Player,
    PlayerLogin,
    PlayerOffer,
    Team,
    TeamLogin,
)


def create_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False), engine


def seed_if_empty(session: Session):
    if session.query(Player).count() > 0:
        return

    lions = Team(name="Lions FC", founding_year=1986, stadium="North Arena")
    falcons = Team(name="Falcons United", founding_year=1992, stadium="City Dome")
    sharks = Team(name="Sharks City", founding_year=2001, stadium="West Field")

    p1 = Player(name="Ali Raza", nationality="Pakistan", position="Forward", dob=date(1999, 3, 14))
    p2 = Player(name="Mason Lee", nationality="England", position="Midfielder", dob=date(2000, 7, 8))
    p3 = Player(name="Noah Silva", nationality="Brazil", position="Defender", dob=date(2002, 1, 19))

    session.add_all([lions, falcons, sharks, p1, p2, p3])
    session.flush()

    session.add_all(
        [
            TeamLogin(team_id=lions.id, username="T_lions"),
            TeamLogin(team_id=falcons.id, username="T_falcons"),
            TeamLogin(team_id=sharks.id, username="T_sharks"),
            PlayerLogin(player_id=p1.id, username="P_ali"),
            PlayerLogin(player_id=p2.id, username="P_mason"),
            PlayerLogin(player_id=p3.id, username="P_noah"),
        ]
    )

    session.add_all(
        [
            Contract(player_id=p1.id, team_id=lions.id, salary=150000, start_date=date(2024, 7, 1), end_date=date(2026, 10, 15)),
            Contract(player_id=p2.id, team_id=falcons.id, salary=120000, start_date=date(2023, 7, 1), end_date=date(2027, 6, 30)),
            Contract(player_id=p3.id, team_id=sharks.id, salary=100000, start_date=date(2025, 7, 1), end_date=date(2026, 11, 10)),
        ]
    )

    session.add_all(
        [
            Performance(player_id=p1.id, season="2024", matches_played=29, goals=12, assists=6),
            Performance(player_id=p1.id, season="2025", matches_played=30, goals=14, assists=7),
            Performance(player_id=p2.id, season="2024", matches_played=28, goals=5, assists=9),
            Performance(player_id=p2.id, season="2025", matches_played=31, goals=6, assists=11),
            Performance(player_id=p3.id, season="2025", matches_played=26, goals=2, assists=3),
        ]
    )

    session.add_all(
        [
            PlayerOffer(player_id=p1.id, team_id=falcons.id, amount_offered=175000),
            PlayerOffer(player_id=p1.id, team_id=sharks.id, amount_offered=180000),
            PlayerOffer(player_id=p3.id, team_id=lions.id, amount_offered=130000),
        ]
    )

    session.add_all(
        [
            MatchTeam(season=2024, home_team_id=lions.id, away_team_id=falcons.id, home_team_score=2, away_team_score=1, result="HOME"),
            MatchTeam(season=2024, home_team_id=sharks.id, away_team_id=lions.id, home_team_score=0, away_team_score=0, result="DRAW"),
            MatchTeam(season=2025, home_team_id=falcons.id, away_team_id=sharks.id, home_team_score=1, away_team_score=3, result="AWAY"),
            MatchTeam(season=2025, home_team_id=lions.id, away_team_id=sharks.id, home_team_score=2, away_team_score=2, result="DRAW"),
        ]
    )

    session.commit()
