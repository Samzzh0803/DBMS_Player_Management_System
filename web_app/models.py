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


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    founding_year: Mapped[int | None] = mapped_column(Integer)
    stadium: Mapped[str | None] = mapped_column(String(120))

    contracts: Mapped[list["Contract"]] = relationship(back_populates="team")


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
