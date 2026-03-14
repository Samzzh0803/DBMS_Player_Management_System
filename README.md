# Football Player Management System
### Database Systems Project — Team 05

A full-stack desktop application for managing football players, teams, contracts, transfers, and match performance. Built with Python (PyQt6) and Microsoft SQL Server, this project demonstrates end-to-end database design, schema management, and application integration.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Database Design](#database-design)
- [Application Features](#application-features)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Screenshots](#screenshots)
- [Team](#team)

---

## Project Overview

This system simulates a professional football league management platform. It supports three types of authenticated users — **Players**, **Teams**, and **Admins** — each with a dedicated portal and role-specific permissions.

Key capabilities:
- Track player contracts and monitor expiry windows
- Allow teams to place and review bids on available players
- Record match results and player statistics by season
- Manage transfers between clubs with full history
- Admin controls for creating and removing players and teams

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| GUI Framework | PyQt6 + Qt Designer (`.ui` files) |
| Database | Microsoft SQL Server (MSSQL) |
| DB Driver | `pyodbc` with Windows Authentication |
| Query Style | Raw SQL with parameterized queries |

**Dependencies:**
```
pip install PyQt6 pyodbc
```

---

## Database Design

The database was designed, created, and managed entirely in **Microsoft SQL Server Management Studio (SSMS)**. The schema was built from scratch using normalized relational design principles.

### Entity-Relationship Diagram

![ERD Diagram](DBSProject_Team05/ERD%20DIAGRAM.png)

### Schema Overview

**`Player`** — Core player registry
```sql
PlayerId (PK), Name, Nationality, Position, DOB
```

**`Player_Login`** — Player authentication credentials
```sql
PlayerId (FK), Username, Password
```

**`Team`** — Club information
```sql
TeamId (PK), Name, FoundingYear, Stadium
```

**`Team_Login`** — Team authentication credentials
```sql
TeamId (FK), Username, Password
```

**`Contract`** — Player-team contracts with salary and duration
```sql
ContractId (PK), PlayerId (FK), TeamId (FK), Salary, StartDate, EndDate
```

**`Performance`** — Per-season player statistics
```sql
PlayerId (FK), Season, MatchesPlayed, Goals, Assists, Saves, Tackles, YellowCards, RedCards
```

**`PlayerOffers`** — Transfer bids placed by teams
```sql
OfferId (PK), PlayerId (FK), TeamName, AmountOffered
```

**`Match`** — Match schedule records
```sql
MatchId (PK), Date
```

**`MatchTeam`** — Match results with scores and outcome
```sql
MatchId (FK), Season, HomeTeamId, AwayTeamId, HomeTeamScore, AwayTeamScore, Result
```

**`Transfer`** — Transfer history linking old and new contracts
```sql
TransferId (PK), OldContractId, NewContractId, Date, Fee
```

### Database Features Used

- **Normalization** — Schema designed to 3NF to eliminate redundancy
- **Foreign Keys & Referential Integrity** — Enforced across all relational tables
- **CTEs (Common Table Expressions)** — Used to retrieve latest active contracts per player
- **Aggregate Functions** — `SUM()`, `COUNT()`, `AVG()` for performance and standings calculations
- **CASE Statements** — Win/Loss/Draw logic in team performance queries
- **Date Functions** — `DATEDIFF()`, `DATEADD()`, `GETDATE()` for contract expiry detection
- **JOINs** — Multi-table `INNER` and `LEFT JOIN` queries throughout
- **Parameterized Queries** — All user inputs passed via `?` placeholders to prevent SQL injection

### Example Query — Contracts Expiring Within 3 Months
```sql
WITH LatestContracts AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY PlayerId ORDER BY EndDate DESC) AS rn
    FROM Contract
)
SELECT p.Name, p.Position, t.Name AS Team, lc.EndDate, lc.Salary
FROM LatestContracts lc
JOIN Player p ON lc.PlayerId = p.PlayerId
JOIN Team t ON lc.TeamId = t.TeamId
WHERE lc.rn = 1
  AND lc.EndDate BETWEEN GETDATE() AND DATEADD(MONTH, 3, GETDATE())
```

### Example Query — Team Performance Stats
```sql
SELECT
    t.Name,
    SUM(CASE WHEN mt.Result = 'W' THEN 1 ELSE 0 END) AS Wins,
    SUM(CASE WHEN mt.Result = 'L' THEN 1 ELSE 0 END) AS Losses,
    SUM(CASE WHEN mt.Result = 'D' THEN 1 ELSE 0 END) AS Draws,
    SUM(mt.HomeTeamScore) AS GoalsFor,
    SUM(mt.AwayTeamScore) AS GoalsAgainst
FROM MatchTeam mt
JOIN Team t ON mt.HomeTeamId = t.TeamId
GROUP BY t.Name
```

---

## Application Features

### Multi-Portal Authentication
Three distinct login flows based on user type:
- **Player Portal** — Username prefix `P`
- **Team Portal** — Username prefix `T`
- **Admin Portal** — Full system access

### Dashboard
- Displays all registered players with aggregated stats (age, position, team, goals, assists)
- Entry point to all three portals

### Player Bidding Screen
- Lists players whose contracts expire within the next 3 months
- Triggers automated bid calculation based on player stats

### Bid Calculator
Calculates a recommended bid amount using player performance data:
- Age, matches played, goals, assists
- Position-specific metrics (saves for GKs, tackles for defenders)
- Card deductions (yellow/red)

### Team Portal
- Displays full club performance: wins, losses, draws, win %, goals for/against, goal difference
- Shows current squad roster

### Player Portal
- View incoming transfer offers from teams
- Review personal contract history and performance stats

### Admin Portal
Full CRUD access:
- Add / Remove Players
- Add / Remove Teams
- Input match results and scores
- Record player statistics per season

### Offer Management
- Teams place bids via the Make Offer screen
- Offer details view shows bidding team info and offer history per player

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- Microsoft SQL Server (local instance)
- SQL Server Management Studio (SSMS) — for DB setup
- Windows Authentication enabled on your SQL Server instance

### 1. Clone the Repository
```bash
git clone https://github.com/Samzzh0803/DBMS_Player_Management_System.git
cd DBMS_Player_Management_System
```

### 2. Install Python Dependencies
```bash
pip install PyQt6 pyodbc
```

### 3. Set Up the Database
1. Open **SSMS** and connect to your local SQL Server instance
2. Create a new database named `DB Project`
3. Run the schema creation scripts to create all tables and relationships
4. Populate with sample data if needed

### 4. Update the Connection String
In [DBSProject_Team05/app.py](DBSProject_Team05/app.py), update the connection string to match your server name:
```python
connection = pyodbc.connect(
    'DRIVER={SQL SERVER};'
    'SERVER=YOUR_SERVER_NAME\\MSSQLSERVER01;'
    'DATABASE=DB Project;'
    'Trusted_Connection=yes;'
)
```

---

## Running the App

```bash
cd DBSProject_Team05
python app.py
```

> All `.ui` files must remain in the same directory as `app.py`.

---

## Project Structure

```
DBSProject_Team05/
├── app.py                    # Main application — all screens and logic (2,596 lines)
├── ERD DIAGRAM.png           # Entity-Relationship Diagram
├── Login.ui                  # Login screen
├── 1_Dashboard.ui            # Main dashboard
├── 2_PlayerBidding.ui        # Expiring contracts view
├── 3_TeamPerformance.ui      # Team stats
├── 4_PendingOffers.ui        # Offers overview
├── Player_Portal.ui          # Player-specific portal
├── TeamPortal.ui             # Team-specific portal
├── AdminPortal.ui            # Admin control panel
├── Calculate Bid.ui          # Bid calculator
├── Make Offer.ui             # Offer submission form
├── OfferDetails.ui           # Offer detail view
├── Add_Match_Score.ui        # Match result entry
├── Player_stats_input.ui     # Player performance entry
├── PA.ui / PD.ui             # Player Add / Delete
├── TA.ui / TD.ui             # Team Add / Delete
└── [Additional UI files]
```

---

## Team

**Sameer Hassan** — Database Systems Project

---

*Built with Python, PyQt6, and Microsoft SQL Server.*
