from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    nationality: Mapped[str] = mapped_column(String(60), nullable=False)
    position: Mapped[str] = mapped_column(String(30), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)

    contracts: Mapped[list["Contract"]] = relationship(back_populates="player")
    performances: Mapped[list["Performance"]] = relationship(back_populates="player")
    offers: Mapped[list["PlayerOffer"]] = relationship(back_populates="player")
    login: Mapped["PlayerLogin | None"] = relationship(back_populates="player")


class PlayerLogin(Base):
    __tablename__ = "player_logins"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False, default="demo123")

    player: Mapped[Player] = relationship(back_populates="login")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    founding_year: Mapped[int | None] = mapped_column(Integer)
    stadium: Mapped[str | None] = mapped_column(String(120))

    contracts: Mapped[list["Contract"]] = relationship(back_populates="team")
    offers: Mapped[list["PlayerOffer"]] = relationship(back_populates="team")
    home_matches: Mapped[list["MatchTeam"]] = relationship(
        back_populates="home_team", foreign_keys="MatchTeam.home_team_id"
    )
    away_matches: Mapped[list["MatchTeam"]] = relationship(
        back_populates="away_team", foreign_keys="MatchTeam.away_team_id"
    )
    login: Mapped["TeamLogin | None"] = relationship(back_populates="team")


class TeamLogin(Base):
    __tablename__ = "team_logins"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False, default="demo123")

    team: Mapped[Team] = relationship(back_populates="login")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    salary: Mapped[float | None] = mapped_column(Numeric(12, 2))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    player: Mapped[Player] = relationship(back_populates="contracts")
    team: Mapped[Team] = relationship(back_populates="contracts")


class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[str] = mapped_column(String(20), nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)

    player: Mapped[Player] = relationship(back_populates="performances")


class PlayerOffer(Base):
    __tablename__ = "player_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    amount_offered: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    player: Mapped[Player] = relationship(back_populates="offers")
    team: Mapped[Team] = relationship(back_populates="offers")


class MatchTeam(Base):
    __tablename__ = "match_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    home_team_score: Mapped[int] = mapped_column(Integer, default=0)
    away_team_score: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[str] = mapped_column(String(12), nullable=False)

    home_team: Mapped[Team] = relationship(back_populates="home_matches", foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(back_populates="away_matches", foreign_keys=[away_team_id])
