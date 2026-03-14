import sys
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QStackedWidget, QTableWidgetItem, QLineEdit, QPushButton, QMessageBox, QLabel, QTableWidget
from PyQt6 import uic
import pyodbc as odbc
from datetime import datetime
import random
import string


#run the code with python app.py

# Database connection setup
DRIVER_NAME = 'SQL SERVER'
SERVER_NAME = 'DESKTOP-SDOJ0MC\MSSQLSERVER01'
DATABASE_NAME = 'DB Project'

connection_string = f"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trusted_Connection=yes;
"""
try:
    connection = odbc.connect(connection_string)
    print('Connected to the database')
except odbc.DatabaseError as e:
    print(f"Error connecting to the database: {e}")
    sys.exit(1)

current_user_id = None 
current_team_id = None
bid = None

# Screen classes
class Dashboard(QMainWindow):
    def __init__(self):
        super(Dashboard, self).__init__()
        uic.loadUi("1_Dashboard.ui", self)
        self.setup_ui()

    def setup_ui(self):
        """
        Setup the UI elements and initial data.
        """
        self.squad_table = self.findChild(QtWidgets.QTableWidget, "_1_tableWidge_SquadData")
        
        # Buttons
        self.player_portal_button = self.findChild(QtWidgets.QPushButton, "_1_pushButton_PlayerPortal")
        self.team_portal_button = self.findChild(QtWidgets.QPushButton, "_1_pushButton_TeamPortal")
        self.admin_portal_button = self.findChild(QtWidgets.QPushButton, "_1_pushButton_AdminPortal")
        
        # Load player data
        self.load_player_data()

        # Button connections
        self.player_portal_button.clicked.connect(lambda: self.open_login_screen("player"))
        self.team_portal_button.clicked.connect(lambda: self.open_login_screen("team"))
        self.admin_portal_button.clicked.connect(lambda: self.open_login_screen("admin"))

    def load_player_data(self):
        """
        Loads player data from the database into the table widget.
        """
        try:
            cursor = connection.cursor()

            # Corrected Query
            query = """
                WITH LatestContracts AS (
    SELECT 
        PlayerId, 
        TeamId,
        ROW_NUMBER() OVER (PARTITION BY PlayerId ORDER BY StartDate DESC, EndDate DESC) AS RowNum
    FROM 
        Contract
)
SELECT 
    p.Name AS PlayerName, 
    DATEDIFF(YEAR, p.DOB, GETDATE()) AS Age, 
    ISNULL(t.Name, 'No Team') AS Team, 
    p.Position, 
    SUM(ISNULL(ps.Goals, 0)) AS Goals, 
    SUM(ISNULL(ps.Assists, 0)) AS Assists
FROM 
    Player p
LEFT JOIN 
    Performance ps ON p.PlayerId = ps.PlayerId
LEFT JOIN 
    LatestContracts lc ON p.PlayerId = lc.PlayerId AND lc.RowNum = 1
LEFT JOIN 
    Team t ON lc.TeamId = t.TeamId
GROUP BY 
    p.PlayerId, p.Name, p.DOB, p.Position, t.Name;




            """

            cursor.execute(query)
            results = cursor.fetchall()

            # Update QTableWidget
            self.squad_table.setRowCount(len(results))
            self.squad_table.setColumnCount(6)  # Number of columns in the query
            self.squad_table.setHorizontalHeaderLabels(
                ["Player Name", "Age", "Team", "Position", "Goals", "Assists"]
            )

            # Populate the table with data
            for row_idx, row_data in enumerate(results):
                for col_idx, cell_data in enumerate(row_data):
                    self.squad_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

            cursor.close()

        except odbc.DatabaseError as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def open_login_screen(self, portal_type):
        """
        Set the portal type and navigate to the login screen.
        """
        widget.current_login_type = portal_type  # Store portal type globally or on the widget
        widget.setCurrentIndex(4)  # Navigate to Login screen

class PlayerBidding(QMainWindow):
    def __init__(self):
        super(PlayerBidding, self).__init__()
        uic.loadUi("2_PlayerBidding.ui", self)
        self.setup_ui()
        self.display_contracts_ending_soon()

    def setup_ui(self):
        # Back button
        self.findChild(QtWidgets.QPushButton, "_2_BackButton").clicked.connect(self.back)

        # Table widget
        self.table_widget = self.findChild(QtWidgets.QTableWidget, "_2_tableWidget_PlayerDetails")
        if self.table_widget:
            self.table_widget.itemClicked.connect(self.row_selected)

    def back(self):
        widget.setCurrentIndex(6)  # Navigate back to the previous screen

    def row_selected(self, item):
        """
        Handles row selection in the table and navigates to the Calculate Bid screen.
        """
        row = item.row()  # Get the row of the clicked item
        player_id = self.table_widget.item(row, 0).text()  # Assuming Player ID is in column 0
        global current_user_id
        current_user_id = player_id
        # Pass the selected Player ID to the Calculate Bid screen
        self.open_calculate_bid_screen(player_id)

    def open_calculate_bid_screen(self, player_id):
        """
        Opens the Calculate Bid screen and pre-fills the Player ID field.
        """
        # Assuming the CalculateBid screen is at index 2 and has a Player ID input field
        # calculate_bid_screen = widget.widget(2)  # Replace '2' with the actual index of Calculate Bid screen
        # calculate_bid_screen.findChild(QtWidgets.QLineEdit, "_2_lineEdit_PlayerName").setText(player_id)
        widget.setCurrentIndex(7)  # Navigate to the Calculate Bid screen

    def display_contracts_ending_soon(self):
        """
        Fetch and display players with contracts ending soon in the table widget.
        """
        try:
            # Query to fetch players with contracts ending within the next 3 months
            cursor = connection.cursor()
#             query = """
#                 SELECT 
#     p.PlayerId AS PlayerID,
#     p.Name AS PlayerName, 
#     c.TeamId AS TeamID, 
#     c.EndDate AS ContractEndDate
# FROM 
#     Player p
# INNER JOIN 
#     Contract c ON p.PlayerId = c.PlayerId
# WHERE 
#     c.endDate <=  DATEADD(MONTH, 3, GETDATE());

#             """
            query = '''WITH LatestContracts AS (
    SELECT 
        PlayerId,
        TeamId,
        EndDate,
        ROW_NUMBER() OVER (PARTITION BY PlayerId ORDER BY StartDate DESC) AS RowNum
    FROM Contract
    WHERE EndDate <= DATEADD(MONTH, 3, GETDATE())
)
SELECT 
    p.PlayerId AS PlayerID,
    p.Name AS PlayerName,
    lc.TeamId AS TeamID,
    lc.EndDate AS ContractEndDate
FROM 
    Player p
INNER JOIN 
    LatestContracts lc ON p.PlayerId = lc.PlayerId
WHERE 
    lc.RowNum = 1;
'''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Populate the table with query results
            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(4)
            self.table_widget.setHorizontalHeaderLabels(["Player ID", "Player Name", "Team ID", "Contract End Date"])

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    self.table_widget.setItem(i, j, QTableWidgetItem(str(value)))

            cursor.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")



class TeamPlayers(QMainWindow):
    def __init__(self):
        """
        Initialize the TeamPlayers screen.
        """
        super(TeamPlayers, self).__init__()
        uic.loadUi("TeamPlayers.ui", self)  # Load the UI file

        # Call UI setup
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and button connections.
        """
        # Find UI components
        self.players_table = self.findChild(QTableWidget, "tableWidget")
        self.back_button = self.findChild(QPushButton, "pushButton")

        # Connect the "Back" button
        self.back_button.clicked.connect(self.go_back)

        # Set table properties
        self.players_table.setColumnCount(5)
        self.players_table.setHorizontalHeaderLabels(["PlayerID", "Player Name", "Nationality", "Position", "DOB"])

    def load_team_players(self):
        """
        Load the players of the currently logged-in team into the table.
        """
        global current_team_id

        if not current_team_id:
            QMessageBox.warning(self, "Error", "No team is currently logged in.")
            return

        try:
            cursor = connection.cursor()
            query = """
                SELECT 
    p.PlayerId, 
    p.Name, 
    p.Nationality, 
    p.Position, 
    DATEDIFF(YEAR, p.DOB, GETDATE()) AS DOB
FROM Player p
INNER JOIN Contract c ON p.PlayerId = c.PlayerId
WHERE 
    c.TeamId = ?
ORDER BY c.StartDate DESC;


            """
            cursor.execute(query, (current_team_id,))
            rows = cursor.fetchall()

            # Populate the table
            self.players_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    self.players_table.setItem(i, j, QTableWidgetItem(str(value)))

            cursor.close()

        except odbc.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while loading players: {e}")

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        widget.setCurrentIndex(6)  # Replace '6' with the appropriate index for the previous screen

    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(TeamPlayers, self).showEvent(event)
        self.load_team_players()



class CalculateBid(QMainWindow):
    def __init__(self):
        super(CalculateBid, self).__init__()
        uic.loadUi("Calculate Bid.ui", self)  # Load the UI file
        self.setup_ui()
        self.load_player_data()  # Load player data after initializing the UI

    def setup_ui(self):
        """
        Set up UI components and button connections.
        """
        # LineEdit fields
        self.matches_played_input = self.findChild(QLineEdit, "lineEdit_MP")
        self.goals_input = self.findChild(QLineEdit, "lineEdit_G1")
        self.assists_input = self.findChild(QLineEdit, "lineEdit_A1")
        self.saves_input = self.findChild(QLineEdit, "lineEdit_S1")
        self.tackles_input = self.findChild(QLineEdit, "lineEdit_T1")
        self.yellow_cards_input = self.findChild(QLineEdit, "lineEdit_YC1")
        self.red_cards_input = self.findChild(QLineEdit, "lineEdit_RC1")
        self.dob_input = self.findChild(QLineEdit, "lineEdit_RC1_2")  # Date of Birth

        # Buttons
        self.calculate_button = self.findChild(QPushButton, "pushButton_2")
        self.back_button = self.findChild(QPushButton, "pushButton")

        # Connect button functionality
        self.calculate_button.clicked.connect(self.calculate_bid)
        self.back_button.clicked.connect(self.go_back)

    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(CalculateBid, self).showEvent(event)  # Correct superclass reference
        self.load_player_data()  # Load the player data when the screen is displayed

    def load_player_data(self):
        """
        Loads player data from the database based on the current_user_id.
        """
        global current_user_id

        # Check if the user ID is available
        if not current_user_id:
            QMessageBox.warning(self, "Error", "No player is currently logged in.")
            return

        try:
            cursor = connection.cursor()

            # Query to fetch player data
            query = """
                SELECT  
    FLOOR(DATEDIFF(DAY, p.DOB, GETDATE()) / 365.25) AS Age,  
    perf.MatchesPlayed, 
    perf.Goals, 
    perf.Assists, 
    perf.Saves, 
    perf.Tackles, 
    perf.YellowCards, 
    perf.RedCards
FROM Player p
INNER JOIN Performance perf ON p.PlayerId = perf.PlayerId
WHERE p.PlayerId = ?;


            """
            cursor.execute(query, (current_user_id,))
            player_data = cursor.fetchone()

            # Check if data exists
            if not player_data:
                QMessageBox.warning(self, "Data Not Found", f"No data found for Player ID: {current_user_id}")
                return

            # Populate fields with data
            self.dob_input.setText(str(player_data[0]))  # Date of Birth
            self.matches_played_input.setText(str(player_data[1] or 0))
            self.goals_input.setText(str(player_data[2] or 0))
            self.assists_input.setText(str(player_data[3] or 0))
            self.saves_input.setText(str(player_data[4] or 0))
            self.tackles_input.setText(str(player_data[5] or 0))
            self.yellow_cards_input.setText(str(player_data[6] or 0))
            self.red_cards_input.setText(str(player_data[7] or 0))

            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def calculate_bid(self):
        """
        Calculates the estimated bid for the player based on performance stats.
        """
        global current_user_id

        if not current_user_id:
            QMessageBox.warning(self, "Error", "No player is currently logged in.")
            return

        try:
            cursor = connection.cursor()
            query = """
                SELECT 
    FLOOR(DATEDIFF(DAY, p.DOB, GETDATE()) / 365.25) AS Age, 
    CAST(perf.Goals AS FLOAT) / NULLIF(perf.MatchesPlayed, 0) AS AverageGoalsPerMatch,
    CAST(perf.Assists AS FLOAT) / NULLIF(perf.MatchesPlayed, 0) AS AverageAssistsPerMatch,
    CAST(c.Salary AS FLOAT) AS LatestSalary
FROM Player p
INNER JOIN Performance perf ON p.PlayerId = perf.PlayerId
LEFT JOIN (
    SELECT 
        c.PlayerId, 
        c.Salary 
    FROM Contract c
    WHERE c.EndDate = (
        SELECT MAX(EndDate) FROM Contract WHERE PlayerId = c.PlayerId
    )
) c ON p.PlayerId = c.PlayerId
WHERE p.PlayerId = ?;


            """
            cursor.execute(query, (current_user_id,))
            player_data = cursor.fetchone()

            if not player_data:
                QMessageBox.warning(self, "Player Not Found", f"No data found for Player ID: {current_user_id}")
                return

            # Extract player data
            age, avg_goals, avg_assists, latest_salary = player_data

            # Ensure values are valid
            avg_goals = float(avg_goals or 0.0)
            avg_assists = float(avg_assists or 0.0)
            latest_salary = float(latest_salary or 0.0)
            age = float(age or 0.0)

            # Calculate the bid price
            bid_price = (
                (2 * avg_goals + avg_assists) * 10000 +
                (latest_salary * 12) +
                (35 - age * 5000)
            )
            global bid
            bid= bid_price

            QMessageBox.information(self, "Bid Price", f"Estimated Bid Price: {bid_price:.2f}")
            cursor.close()
            widget.setCurrentIndex(8) 
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def go_back(self):
        """
        Navigates back to the previous screen.
        """
        global bid
        global current_user_id
        bid = None
        current_user_id = None
        widget.setCurrentIndex(1)  # Replace '1' with the appropriate index for the previous screen



class MakeOffer(QMainWindow):
    def __init__(self):
        """
        Initialize the MakeOffer screen.
        """
        super(MakeOffer, self).__init__()
        uic.loadUi("Make Offer.ui", self)  # Load the UI file (save your XML file as Make_Offer.ui)

        # Call UI setup
        self.setup_ui()

    def setup_ui(self):
        """
        Connect widgets to variables and attach functionality.
        """
        # Find UI components
        self.estimated_bid_input = self.findChild(QLineEdit, "lineEdit_MP")
        self.my_offer_input = self.findChild(QLineEdit, "lineEdit_MP_2")
        self.make_offer_button = self.findChild(QPushButton, "pushButton")
        self.header_label = self.findChild(QLabel, "label_MP1_2")

        # Set placeholder text for inputs
        self.estimated_bid_input.setPlaceholderText("Estimated Bid Amount")
        self.my_offer_input.setPlaceholderText("Enter Your Offer")

        # Connect the "Make Offer" button
        self.make_offer_button.clicked.connect(self.make_offer)

        # Header display
        self.header_label.setText("Make an Offer")

    def make_offer(self):
        """
        Handles the process of making an offer, including input validation, saving the offer to the database,
        and providing feedback to the user.
        """
        try:
            # Retrieve manual offer amount
            offer_amount_input = self.my_offer_input.text().strip()
            if not offer_amount_input:
                QMessageBox.warning(self, "Input Error", "Please enter an offer amount.")
                return

            # Convert offer amount to float
            try:
                offer_amount = float(offer_amount_input)
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid numeric offer amount.")
                return

            # Retrieve estimated bid from input
            estimated_bid = self.estimated_bid_input.text().strip()
            if estimated_bid:
                try:
                    estimated_bid = float(estimated_bid)
                    if offer_amount < estimated_bid:
                        QMessageBox.warning(self, "Warning", "Your offer is below the estimated bid.")
                except ValueError:
                    QMessageBox.warning(self, "Input Error", "Invalid value in the Estimated Bid field.")
                    return

            # Retrieve global player ID
            global current_user_id
            if not current_user_id:
                QMessageBox.warning(self, "Error", "No player is currently logged in.")
                return

            # Retrieve team name (this could be fetched dynamically based on current_team_id if needed)
            global current_team_id
            cursor = connection.cursor()
            team_query = """
                SELECT Name FROM Team WHERE TeamId = ?
            """
            cursor.execute(team_query, (current_team_id,))
            team_data = cursor.fetchone()
            if not team_data:
                QMessageBox.warning(self, "Error", "Your team information could not be retrieved.")
                return

            team_name = team_data[0]

            # Save the offer to the PlayerOffers table
            save_offer_query = """
                INSERT INTO PlayerOffers (PlayerId, TeamName, AmountOffered)
                VALUES (?, ?, ?)
            """
            cursor.execute(save_offer_query, (current_user_id, team_name, offer_amount))
            connection.commit()

            # Show success message
            QMessageBox.information(self, "Offer Saved", "The offer has been successfully saved!")

            cursor.close()
            # global current_user_id
            global bid
            current_user_id = None
            bid = None
            print(bid)
            widget.setCurrentIndex(1)

        except odbc.DatabaseError as db_err:
            QMessageBox.critical(self, "Database Error", f"An error occurred while interacting with the database: {db_err}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def show_estimated_bid(self, estimated_bid):
        """
        Pre-populate the estimated bid field with a given value.
        """
        self.estimated_bid_input.setText(str(estimated_bid))

    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(MakeOffer, self).showEvent(event)

        # Use global bid variable
        global bid
        if bid is not None:
            self.show_estimated_bid(bid)


   



class OfferDetails(QMainWindow):
    def __init__(self):
        """
        Initialize the Offer Details screen.
        """
        super(OfferDetails, self).__init__()
        uic.loadUi("OfferDetails.ui", self)  # Load the UI file
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and button connections.
        """
        # Find UI components
        self.team_details_table = self.findChild(QTableWidget, "tableWidget_TeamDetails")
        self.back_button = self.findChild(QPushButton, "pushButton")
        self.accept_bid_button = self.findChild(QPushButton, "AcceptBidButton")
        self.winning_percentage_input = self.findChild(QLineEdit, "lineEdit_Win")

        # Connect buttons
        self.back_button.clicked.connect(self.back)
        self.accept_bid_button.clicked.connect(self.accept_bid)

    def back(self):
        """
        Navigate back to the previous screen.
        """
        global current_team_id
        current_team_id = None
        widget.setCurrentIndex(3)  # Navigate to OffersScreen (replace '3' with the correct index for your screen)

    def load_team_details(self):
        """
        Load all team players and the win percentage for the team mentioned in the PlayerOffers table.
        """
        global current_team_id
        if not current_team_id:
            QMessageBox.warning(self, "Error", "No team selected.")
            return

        try:
            # Establish a database cursor
            cursor = connection.cursor()

            # Step 1: Fetch all players of the team
            query_players = """
                SELECT 
    Player.Name AS PlayerName,
    Player.Position,
    FLOOR(DATEDIFF(DAY, Player.DOB, GETDATE()) / 365.25) AS DOB,  
    Team.Name AS TeamName
FROM Player
INNER JOIN Contract ON Player.PlayerId = Contract.PlayerId
INNER JOIN Team ON Contract.TeamId = Team.TeamId
WHERE Team.Name = (
    SELECT PlayerOffers.TeamName 
    FROM PlayerOffers 
    WHERE PlayerOffers.OfferId = ?
)
AND GETDATE() BETWEEN Contract.StartDate AND Contract.EndDate;



            """
            cursor.execute(query_players, (current_team_id,))
            results = cursor.fetchall()

            # Step 2: Calculate the team's win percentage
            query_win_percentage = """
SELECT 
    COUNT(*) AS TotalMatches,
    SUM(CASE WHEN (MatchTeam.Result = MatchTeam.homeTeamID or MatchTeam.Result = MatchTeam.homeTeamID) THEN 1 ELSE 0 END) AS Wins,
    (SUM(CASE WHEN (MatchTeam.Result = MatchTeam.homeTeamID or MatchTeam.Result = MatchTeam.homeTeamID) THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS WinPercentage
FROM MatchTeam
WHERE MatchTeam.homeTeamID = (
    SELECT Team.TeamID
    FROM PlayerOffers
    INNER JOIN Team ON PlayerOffers.TeamName = Team.Name
    WHERE PlayerOffers.OfferId = ?

) or  MatchTeam.awayTeamID = (
    SELECT Team.TeamID
    FROM PlayerOffers
    INNER JOIN Team ON PlayerOffers.TeamName = Team.Name
    WHERE PlayerOffers.OfferId = ?

) ;


                

            """
            cursor.execute(query_win_percentage, (current_team_id,current_team_id))
            win_stats = cursor.fetchone()

            total_matches = win_stats[0] if win_stats[0] else 0
            wins = win_stats[1] if win_stats[1] else 0
            win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0

            # Step 3: Display win percentage in the LineEdit
            self.winning_percentage_input.setText(f"{win_percentage:.2f}%")

            # Step 4: Populate the team details table
            self.team_details_table.clearContents()
            self.team_details_table.setRowCount(len(results))
            self.team_details_table.setColumnCount(4)
            self.team_details_table.setHorizontalHeaderLabels(["Player Name", "Position", "DOB", "Team Name"])

            for row_idx, row_data in enumerate(results):
                for col_idx, cell_data in enumerate(row_data):
                    self.team_details_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

            # Close the cursor
            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")



    def accept_bid(self):
        """
        Accept the selected bid for the team mentioned in the PlayerOffers table based on the Offer ID.
        """
        global current_team_id  # current_team_id contains the OfferId
        if not current_team_id:
            QMessageBox.warning(self, "Error", "No offer selected.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Fetch the PlayerId, TeamId, and AmountOffered from the PlayerOffers table using OfferId
            offer_query = """
                SELECT 
    PlayerOffers.PlayerId,
    Team.TeamId,
    PlayerOffers.AmountOffered
FROM PlayerOffers
INNER JOIN Team ON PlayerOffers.TeamName = Team.Name
WHERE PlayerOffers.OfferId = ?;

            """
            cursor.execute(offer_query, (current_team_id,))
            offer_details = cursor.fetchone()

            if not offer_details:
                QMessageBox.warning(self, "Offer Not Found", "The selected offer does not exist.")
                return

            player_id, team_id, amount_offered = offer_details

            # Step 2: Fetch the player's current contract end date
            contract_query = """
                SELECT MAX(EndDate) AS CurrentEndDate
                FROM Contract
                WHERE PlayerId = ?;
            """
            cursor.execute(contract_query, (player_id,))
            current_contract = cursor.fetchone()

            if not current_contract or not current_contract[0]:
                QMessageBox.warning(self, "Contract Not Found", "No existing contract found for the player.")
                return

            current_end_date = current_contract[0]

            # Step 3: Generate a unique ContractId
            contract_id_query = """
                SELECT ISNULL(MAX(ContractId), 0) + 1 AS NewContractId
                FROM Contract;
            """
            cursor.execute(contract_id_query)
            new_contract_id = cursor.fetchone()[0]

            # Step 4: Insert a new contract for the player with the new team
            new_contract_query = """
                INSERT INTO Contract (ContractId, PlayerId, TeamId, Salary, StartDate, EndDate)
                VALUES (?, ?, ?, ?, DATEADD(DAY, 1, ?), DATEADD(YEAR, 3, DATEADD(DAY, 1, ?)));
            """
            cursor.execute(new_contract_query, (new_contract_id, player_id, team_id, amount_offered, current_end_date, current_end_date))
            connection.commit()

            # Step 5: Generate a unique TransferId
            transfer_id_query = """
                SELECT ISNULL(MAX(TransferId), 0) + 1 AS NewTransferId
                FROM Transfer;
            """
            cursor.execute(transfer_id_query)
            new_transfer_id = cursor.fetchone()[0]

            # Step 6: Insert the transfer record
            transfer_query = """
                WITH RankedContracts AS (
                    SELECT 
                        ContractId,
                        PlayerId,
                        ROW_NUMBER() OVER (PARTITION BY PlayerId ORDER BY EndDate DESC) AS RowNum
                    FROM Contract
                )
                INSERT INTO Transfer (TransferId, OldContractId, NewContractId, Date, Fee)
                VALUES (
                    ?, 
                    (SELECT ContractId FROM RankedContracts WHERE PlayerId = ? AND RowNum = 2),
                    (SELECT ContractId FROM RankedContracts WHERE PlayerId = ? AND RowNum = 1),
                    GETDATE(),
                    ?
                );
            """
            cursor.execute(transfer_query, (new_transfer_id, player_id, player_id, amount_offered))
            connection.commit()
            global current_user_id
            # Step 7: Delete the accepted offer from the PlayerOffers table
            delete_offer_query = """
                DELETE FROM PlayerOffers WHERE playerId = ?;
            """
            cursor.execute(delete_offer_query, (current_user_id,))
            connection.commit()

            # Refresh the table data
            self.load_team_details()
            QMessageBox.information(self, "Success", "Offer accepted, new contract created, and transfer updated.")

            cursor.close()
            widget.setCurrentIndex(5)
            current_team_id = None

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")



    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(OfferDetails, self).showEvent(event)
        self.load_team_details()



class OffersScreen(QMainWindow):
    def __init__(self):
        """
        Initialize the Offers screen.
        """
        super(OffersScreen, self).__init__()
        uic.loadUi("4_PendingOffers.ui", self)
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and button connections.
        """
        # Find UI components
        self.offers_table = self.findChild(QtWidgets.QTableWidget, "_4_tableWidget_Offers")
        self.back_button = self.findChild(QtWidgets.QPushButton, "__4_BackButton")

        # Connect button and table row selection
        self.back_button.clicked.connect(self.back)
        self.offers_table.itemSelectionChanged.connect(self.handle_row_selection)

    def back(self):
        """
        Navigate back to the dashboard.
        """
        widget.setCurrentIndex(5)

    def load_offers_data(self):
        """
        Load all pending offers from the database into the table.
        """
        try:
            # Query to fetch all offers from PlayerOffers table
            cursor = connection.cursor()
            query = """
                SELECT OfferId, TeamName, AmountOffered
                FROM PlayerOffers
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Set row and column count for the table
            self.offers_table.setRowCount(len(results))
            self.offers_table.setColumnCount(3)
            self.offers_table.setHorizontalHeaderLabels(["Offer ID", "Team Name", "Amount Offered"])

            # Populate the table with data
            for row_idx, row_data in enumerate(results):
                for col_idx, cell_data in enumerate(row_data):
                    self.offers_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

            cursor.close()

        except odbc.DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while fetching offers: {e}")

    def handle_row_selection(self):
        """
        Handle selection of a row in the table and navigate to the Offer Details screen.
        """
        global current_team_id

        # Get the currently selected row
        selected_items = self.offers_table.selectedItems()
        if selected_items:
            offer_id = selected_items[0].text()  # Assuming Offer ID is in the first column
            current_team_id = offer_id  # Save Offer ID to global variable
            print(current_team_id)
            # Navigate to Offer Details screen
            widget.setCurrentIndex(10)  # Replace '4' with the index of the Offer Details screen

    def showEvent(self, event):
        """
        Overrides the showEvent method to reload data when the screen is shown.
        """
        super(OffersScreen, self).showEvent(event)
        self.load_offers_data()

    # def accept_bid(self):
    #     try:
    #         # Retrieve the Offer ID from input
    #         offer_id_input = self.findChild(QtWidgets.QLineEdit, "_4_lineEdit_OfferID").text()
    #         if not offer_id_input:
    #             QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter an Offer ID.")
    #             return

    #         cursor = connection.cursor()

    #         # Fetch the selected offer details
    #         offer_query = """
    #             WITH LatestContract AS (
    #                 SELECT 
    #                     c.PlayerId, 
    #                     MAX(c.StartDate) AS LatestStartDate
    #                 FROM Contract c
    #                 GROUP BY c.PlayerId
    #             )
    #             SELECT 
    #                 p.PlayerId, 
    #                 t.TeamId AS NewTeamId, 
    #                 o.AmountOffered
    #             FROM Player p
    #             INNER JOIN PlayerOffers o ON p.PlayerId = o.PlayerId
    #             INNER JOIN Team t ON t.Name = o.TeamName -- Join Team using TeamName from PlayerOffers
    #             WHERE o.OfferId = ?;
    #         """
    #         cursor.execute(offer_query, (offer_id_input,))
    #         offer_details = cursor.fetchone()

    #         if not offer_details:
    #             print(f"DEBUG: No offer found for OfferId: {offer_id_input}")
    #             QtWidgets.QMessageBox.warning(self, "Offer Not Found", "The selected offer does not exist.")
    #             return

    #         player_id, new_team_id, amount_offered = offer_details

    #         # Fetch the player's current contract end date
    #         contract_query = """
    #             SELECT MAX(EndDate) AS CurrentEndDate
    #             FROM Contract
    #             WHERE PlayerId = ?
    #         """
    #         cursor.execute(contract_query, (player_id,))
    #         current_contract = cursor.fetchone()

    #         if not current_contract or not current_contract[0]:
    #             QtWidgets.QMessageBox.warning(self, "Contract Not Found", "No existing contract found for the player.")
    #             return

    #         current_end_date = current_contract[0]

    #         # Generate a unique ContractId
    #         contract_id_query = """
    #             SELECT ISNULL(MAX(ContractId), 0) + 1 AS NewContractId
    #             FROM Contract;
    #         """
    #         cursor.execute(contract_id_query)
    #         new_contract_id = cursor.fetchone()[0]

    #         # Insert a new contract for the player with the new team
    #         new_contract_query = """
    #             INSERT INTO Contract (ContractId, PlayerId, TeamId, Salary, StartDate, EndDate)
    #             VALUES (?, ?, ?, ?, DATEADD(DAY, 1, ?), DATEADD(YEAR, 3, DATEADD(DAY, 1, ?)))
    #         """
    #         cursor.execute(new_contract_query, (new_contract_id, player_id, new_team_id, amount_offered, current_end_date, current_end_date))
    #         connection.commit()

    #         # Generate a unique TransferId
    #         transfer_id_query = """
    #             SELECT ISNULL(MAX(TransferId), 0) + 1 AS NewTransferId
    #             FROM Transfer;
    #         """
    #         cursor.execute(transfer_id_query)
    #         new_transfer_id = cursor.fetchone()[0]

    #         # Insert the transfer record using ROW_NUMBER for handling offsets
    #         transfer_query = """
    #             WITH RankedContracts AS (
    #                 SELECT 
    #                     ContractId,
    #                     PlayerId,
    #                     ROW_NUMBER() OVER (PARTITION BY PlayerId ORDER BY EndDate DESC) AS RowNum
    #                 FROM Contract
    #             )
    #             INSERT INTO Transfer (TransferId, OldContractId, NewContractId, Date, Fee)
    #             VALUES (
    #                 ?, 
    #                 (SELECT ContractId FROM RankedContracts WHERE PlayerId = ? AND RowNum = 2),
    #                 (SELECT ContractId FROM RankedContracts WHERE PlayerId = ? AND RowNum = 1),
    #                 GETDATE(),
    #                 ?
    #             )
    #         """
    #         cursor.execute(transfer_query, (new_transfer_id, player_id, player_id, amount_offered))
    #         connection.commit()

    #         # Delete all offers for this player from the PlayerOffers table
    #         delete_offers_query = """
    #             DELETE FROM PlayerOffers WHERE PlayerId = ?
    #         """
    #         cursor.execute(delete_offers_query, (player_id,))
    #         connection.commit()

    #         # Refresh the table data
    #         self.load_offers_data()
    #         QtWidgets.QMessageBox.information(self, "Success", "Offer accepted, new contract created, and transfer updated.")

    #     except odbc.DatabaseError as e:
    #         QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
    #     except Exception as e:
    #         QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


class TeamPortal(QMainWindow):
    def __init__(self):
        super(TeamPortal, self).__init__()
        uic.loadUi("TeamPortal.ui", self)  # Load the Team_Portal.ui file
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and button connections.
        """
        # LineEdit fields
        self.team_name_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_TN")
        self.wins_input = self.findChild(QtWidgets.QLineEdit, "lineEdit")
        self.losses_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_2")
        self.draws_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_3")
        self.win_percentage_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_4")

        self.current_wins = self.findChild(QtWidgets.QLineEdit, "lineEdit_8")
        self.current_losses = self.findChild(QtWidgets.QLineEdit, "lineEdit_6")
        self.current_draws = self.findChild(QtWidgets.QLineEdit, "lineEdit_7")
        self.goals_for_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_5")
        self.goals_against_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_9")
        self.goal_difference_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_10")

        # Buttons
        self.bid_button = self.findChild(QtWidgets.QPushButton, "pushButton")
        self.players_button = self.findChild(QtWidgets.QPushButton, "pushButton_2")
        self.logout_button = self.findChild(QtWidgets.QPushButton, "pushButton_3")

        # Button connections
        self.bid_button.clicked.connect(self.open_bid_screen)
        self.players_button.clicked.connect(self.open_players_screen)
        self.logout_button.clicked.connect(self.logout)

    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(TeamPortal, self).showEvent(event)  # Correct call to parent class
        self.load_team_data()  # Ensure data is loaded dynamically

    def load_team_data(self):
        """
        Load team performance data into the respective fields dynamically after login.
        """
        global current_team_id
        if not current_team_id:
            QMessageBox.warning(self, "Error", "No team is logged in.")
            return

        try:
            cursor = connection.cursor()

            # Fetch Team Name and Overall Performance
            overall_query = """
                SELECT 
    t.Name AS TeamName,
    SUM(CASE 
            WHEN mt.Result = mt.HomeTeamId THEN 1  
            WHEN mt.Result = mt.AwayTeamId THEN 1  
            ELSE 0 
        END) AS Wins,
    SUM(CASE WHEN mt.Result = 0 THEN 1 ELSE 0 END) AS Draws,
    COUNT(mt.MatchId) - SUM(CASE 
            WHEN mt.Result = mt.HomeTeamId THEN 1 
            WHEN mt.Result = mt.AwayTeamId THEN 1 
            ELSE 0 
        END) - SUM(CASE WHEN mt.Result = 0 THEN 1 ELSE 0 END) AS Losses,
    CAST(
        CASE 
            WHEN COUNT(mt.MatchId) = 0 THEN 0 
            ELSE SUM(CASE 
                        WHEN mt.Result = mt.HomeTeamId THEN 1 
                        WHEN mt.Result = mt.AwayTeamId THEN 1 
                        ELSE 0 
                    END) * 100.0 / COUNT(mt.MatchId)
        END AS FLOAT
    ) AS WinPercentage
FROM 
    Team t
LEFT JOIN 
    MatchTeam mt ON t.TeamId = mt.HomeTeamId OR t.TeamId = mt.AwayTeamId
WHERE 
    t.TeamId = ?
GROUP BY 
    t.Name, t.TeamId;



            """
            cursor.execute(overall_query, (current_team_id,))
            overall_data = cursor.fetchone()

            if overall_data:
                self.team_name_input.setText(overall_data[0] or "")
                self.wins_input.setText(str(overall_data[1] or 0))
                self.draws_input.setText(str(overall_data[2] or 0))
                self.losses_input.setText(str(overall_data[3] or 0))
                self.win_percentage_input.setText(f"{overall_data[4]:.2f}" if overall_data[4] is not None else "0.00")

            # Fetch Current Season Performance
            current_query = """
                SELECT 
    SUM(CASE 
            WHEN mt.Result = mt.HomeTeamId THEN 1  
            WHEN mt.Result = mt.AwayTeamId THEN 1  
            ELSE 0 
        END) AS Wins,
    SUM(CASE WHEN mt.Result = 0 THEN 1 ELSE 0 END) AS Draws,
    COUNT(mt.MatchId) - SUM(CASE 
            WHEN mt.Result = mt.HomeTeamId THEN 1 
            WHEN mt.Result = mt.AwayTeamId THEN 1 
            ELSE 0 
        END) - SUM(CASE WHEN mt.Result = 0 THEN 1 ELSE 0 END) AS Losses,
    SUM(
        CASE 
            WHEN t.TeamId = mt.HomeTeamId THEN mt.HomeTeamScore
            WHEN t.TeamId = mt.AwayTeamId THEN mt.AwayTeamScore
        END
    ) AS GoalsFor,
    SUM(
        CASE 
            WHEN t.TeamId = mt.HomeTeamId THEN mt.AwayTeamScore
            WHEN t.TeamId = mt.AwayTeamId THEN mt.HomeTeamScore
        END
    ) AS GoalsAgainst,
    SUM(
        CASE 
            WHEN t.TeamId = mt.HomeTeamId THEN mt.HomeTeamScore
            WHEN t.TeamId = mt.AwayTeamId THEN mt.AwayTeamScore
        END
    ) - SUM(
        CASE 
            WHEN t.TeamId = mt.HomeTeamId THEN mt.AwayTeamScore
            WHEN t.TeamId = mt.AwayTeamId THEN mt.HomeTeamScore
        END
    ) AS GoalDifference
FROM 
    Team t
LEFT JOIN 
    MatchTeam mt ON t.TeamId = mt.HomeTeamId OR t.TeamId = mt.AwayTeamId
WHERE 
    t.TeamId = ? AND mt.Season = 2024
GROUP BY 
    t.TeamId;



            """
            cursor.execute(current_query, (current_team_id,))
            current_data = cursor.fetchone()

            if current_data:
                self.current_wins.setText(str(current_data[0] or 0))
                self.current_draws.setText(str(current_data[1] or 0))
                self.current_losses.setText(str(current_data[2] or 0))
                self.goals_for_input.setText(str(current_data[3] or 0))
                self.goals_against_input.setText(str(current_data[4] or 0))
                self.goal_difference_input.setText(str(current_data[5] or 0))

            cursor.close()

        except odbc.DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def open_bid_screen(self):
        widget.setCurrentIndex(1)  # Replace with actual index for the bidding screen

    def open_players_screen(self):
        widget.setCurrentIndex(9)

    def logout(self):
        global current_team_id
        current_team_id = None
        QMessageBox.information(self, "Logout", "Successfully logged out.")
        widget.setCurrentIndex(0)  # Navigate back to the login screen


class PlayerPortal(QMainWindow):
    def __init__(self):
        super(PlayerPortal, self).__init__()
        uic.loadUi("Player_Portal.ui", self)  # Load the PlayerPortal UI
        self.setup_ui()

    def setup_ui(self):
        """
        Connects the logout button.
        """
        # Button to log out and return to the login screen
        self.logout_button = self.findChild(QtWidgets.QPushButton, "LogoutButton_PP")
        self.logout_button.clicked.connect(self.logout)
        
        self.offers_button = self.findChild(QtWidgets.QPushButton, "pushButton_Offers")
        self.offers_button.clicked.connect(self.offers)
        
        self.contract_button = self.findChild(QtWidgets.QPushButton, "pushButton_Contract")
        # self.contract_button.clicked.connect(self.contract)

    def offers(self):
        widget.setCurrentIndex(3)
        
    # def contract(self):
    #     widget.setCurrentIndex()

    def showEvent(self, event):
        """
        Overrides the showEvent method to load data when the screen is shown.
        """
        super(PlayerPortal, self).showEvent(event)
        self.load_performance_data()

    def load_performance_data(self):
        """
        Loads the player's performance data (overall and current season) into the UI fields.
        """
        global current_user_id
        if not current_user_id:
            print("Error: No player logged in.")
            return

        try:
            cursor = connection.cursor()

            # Query for Overall Performance
            overall_query = """
                SELECT 
                    SUM(MatchesPlayed) AS TotalMatches, 
                    SUM(Goals) AS TotalGoals, 
                    SUM(Assists) AS TotalAssists, 
                    SUM(Saves) AS TotalSaves,
                    SUM(Tackles) AS TotalTackles,
                    SUM(YellowCards) AS TotalYellowCards,
                    SUM(RedCards) AS TotalRedCards
                FROM Performance
                WHERE PlayerId = ?;
            """
            cursor.execute(overall_query, (current_user_id,))
            overall_data = cursor.fetchone()

            if overall_data:
                self.findChild(QtWidgets.QLineEdit, "lineEdit_MP").setText(str(overall_data[0] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_G1").setText(str(overall_data[1] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_A1").setText(str(overall_data[2] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_S1").setText(str(overall_data[3] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_T1").setText(str(overall_data[4] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_YC1").setText(str(overall_data[5] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_RC1").setText(str(overall_data[6] or 0))

            # Query for Current Season Performance
            current_query = """
                SELECT TOP 1
                    MatchesPlayed, Goals, Assists, Saves, Tackles, YellowCards, RedCards
                FROM Performance
                WHERE PlayerId = ?
                ORDER BY Season DESC;
            """
            cursor.execute(current_query, (current_user_id,))
            current_data = cursor.fetchone()

            if current_data:
                self.findChild(QtWidgets.QLineEdit, "lineEdit_MP2").setText(str(current_data[0] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_G2").setText(str(current_data[1] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_A2").setText(str(current_data[2] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_S2").setText(str(current_data[3] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_T2").setText(str(current_data[4] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_YC2").setText(str(current_data[5] or 0))
                self.findChild(QtWidgets.QLineEdit, "lineEdit_RC2").setText(str(current_data[6] or 0))

            # Fetch Player Name and Team Name
            player_query = """
                SELECT TOP 1
                    p.Name AS PlayerName, 
                    t.Name AS TeamName
                FROM Player p
                INNER JOIN Contract c ON p.PlayerId = c.PlayerId
                INNER JOIN Team t ON c.TeamId = t.TeamId
                WHERE p.PlayerId = ?
                ORDER BY c.EndDate DESC;
            """
            cursor.execute(player_query, (current_user_id,))
            player_info = cursor.fetchone()

            if player_info:
                self.findChild(QtWidgets.QLineEdit, "lineEdit_PN").setText(player_info[0])  # Player Name
                self.findChild(QtWidgets.QLineEdit, "lineEdit_TN").setText(player_info[1])  # Team Name

            cursor.close()

        except odbc.DatabaseError as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def logout(self):
        """
        Logs out the player and returns to the login screen.
        """
        global current_user_id
        current_user_id = None  # Clear the logged-in Player ID
        widget.setCurrentIndex(0)  # Navigate back to the login screen





class Login(QMainWindow):
    def __init__(self):
        super(Login, self).__init__()
        uic.loadUi("Login.ui", self)  # Create a UI file for login if not done already
        self.setup_ui()

    def setup_ui(self):
        # Reference to login elements
        self.id_input = self.findChild(QtWidgets.QLineEdit, "l_lineEdit_UserName")
        self.password_input = self.findChild(QtWidgets.QLineEdit, "l_lineEdit_Password")
        
        self.login_button = self.findChild(QtWidgets.QPushButton, "l_pushButton_Login")
        # Connect login buttons
        self.login_button.clicked.connect(self.dynamic_verify_login)
        self.back_button = self.findChild(QtWidgets.QPushButton, "l_BackButton").clicked.connect(self.go_to_dashboard)
        
        
    def go_to_dashboard(self):
        widget.setCurrentIndex(0)
        # self.close()


    def dynamic_verify_login(self):
        """
        Calls the appropriate login function based on the portal type.
        """
        portal_type = getattr(widget, "current_login_type", None)
        
        if portal_type == "team":
            self.verify_team_login()
        elif portal_type == "player":
            self.verify_player_login()
        elif portal_type == "admin":
            self.verify_admin_login()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Unknown login portal type.")
        # self.close()

    def verify_team_login(self):
        username = self.id_input.text().strip()
        password = self.password_input.text().strip()
        global current_team_id

        if not username or not password or not username.startswith('T'):
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid Team Username and Password.")
            return

        try:
            cursor = connection.cursor()
            team_query = """
                SELECT password, teamid
                FROM team_login
                WHERE username = ?
            """
            cursor.execute(team_query, (username,))
            team_result = cursor.fetchone()

            if team_result and team_result[0] == password:
                QtWidgets.QMessageBox.information(self, "Login Success", "Team login successful!")
                current_team_id = team_result[1]
                widget.setCurrentIndex(6)  # Navigate to Player Bidding screen
            else:
                QtWidgets.QMessageBox.warning(self, "Login Error", "Invalid Password for Team Username.")

            cursor.close()
        except odbc.DatabaseError as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def verify_player_login(self):
        username = self.id_input.text().strip()
        password = self.password_input.text().strip()
        global current_user_id

        if not username or not password or not username.startswith('P'):
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid Player Username and Password.")
            return

        try:
            cursor = connection.cursor()
            player_query = """
                SELECT password, playerid
                FROM player_login
                WHERE username = ?
            """
            cursor.execute(player_query, (username,))
            player_result = cursor.fetchone()

            if player_result and player_result[0] == password:
                QtWidgets.QMessageBox.information(self, "Login Success", "Player login successful!")
                current_user_id = player_result[1]
                widget.setCurrentIndex(5)  # Navigate to Player Offers screen
            else:
                QtWidgets.QMessageBox.warning(self, "Login Error", "Invalid Password for Player Username.")

            cursor.close()
        except odbc.DatabaseError as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def verify_admin_login(self):
        username = self.id_input.text().strip()
        password = self.password_input.text().strip()

        if username == "admin" and password == "admin1":
            QtWidgets.QMessageBox.information(self, "Login Success", "Admin login successful!")
            widget.setCurrentIndex(11)  # Navigate to Player Portal screen
        else:
            QtWidgets.QMessageBox.warning(self, "Login Error", "Invalid Admin Username or Password.")





class TeamPerformance(QMainWindow):
    def __init__(self):
        super(TeamPerformance, self).__init__()
        uic.loadUi("3_TeamPerformance.ui", self)  # Load the UI file for Team Performance
        self.setup_ui()
        self.display_team_performance()

    def setup_ui(self):
        self.performance_table = self.findChild(QtWidgets.QTableWidget, "_3_tableWidget_TeamPerformance")
        self.findChild(QtWidgets.QPushButton, "_3_BackButton").clicked.connect(self.go_to_dashboard)
        
    def go_to_dashboard(self):
        widget.setCurrentIndex(0)

    def display_team_performance(self):
        try:
            cursor = connection.cursor()

            # SQL Query to calculate team performance
            query = """
                WITH TeamStats AS (
    SELECT 
        t.TeamId,
        t.Name AS TeamName,
        COUNT(mt.MatchId) AS MatchesPlayed,
        SUM(CASE 
                WHEN mt.Result = mt.HomeTeamId THEN 1  -- Home Team Wins
                WHEN mt.Result = mt.AwayTeamId THEN 1  -- Away Team Wins
                ELSE 0 
            END) AS MatchesWon,
        SUM(
            CASE 
                WHEN t.TeamId = mt.HomeTeamId THEN mt.HomeTeamScore  -- Goals scored as Home Team
                WHEN t.TeamId = mt.AwayTeamId THEN mt.AwayTeamScore  -- Goals scored as Away Team
                ELSE 0 
            END
        ) AS TotalGoals
    FROM Team t
    LEFT JOIN MatchTeam mt 
        ON t.TeamId = mt.HomeTeamId OR t.TeamId = mt.AwayTeamId
    GROUP BY t.TeamId, t.Name
),
MidfieldStats AS (
    SELECT 
        t.TeamId,
        COALESCE(AVG(CAST(pp.Assists AS FLOAT) / NULLIF(pp.MatchesPlayed, 0)), 0) AS AvgMidfieldAssists
    FROM Player p
    INNER JOIN Performance pp ON p.PlayerId = pp.PlayerId
    INNER JOIN Contract c ON p.PlayerId = c.PlayerId
    INNER JOIN Team t ON c.TeamId = t.TeamId
    WHERE p.Position = 'Midfielder'
    GROUP BY t.TeamId
),
DefenseStats AS (
    SELECT 
        t.TeamId,
        COALESCE(AVG(CAST(pp.Tackles AS FLOAT) / NULLIF(pp.MatchesPlayed, 0)), 0) AS AvgDefenseTackles
    FROM Player p
    INNER JOIN Performance pp ON p.PlayerId = pp.PlayerId
    INNER JOIN Contract c ON p.PlayerId = c.PlayerId
    INNER JOIN Team t ON c.TeamId = t.TeamId
    WHERE p.Position = 'Defender'
    GROUP BY t.TeamId
)
SELECT 
    ts.TeamName,
    COALESCE(CAST(ts.MatchesWon AS FLOAT) / NULLIF(ts.MatchesPlayed, 0) * 100, 0) AS WinPercentage,
    COALESCE(ts.TotalGoals * 2, 0) AS AttackRating,  -- Scale goals scored to a 10-point rating
    COALESCE(ms.AvgMidfieldAssists * 2, 0) AS MidfieldRating,  -- Scale assists to a 10-point rating
    COALESCE(ds.AvgDefenseTackles * 2, 0) AS DefenseRating  -- Scale tackles to a 10-point rating
FROM TeamStats ts
LEFT JOIN MidfieldStats ms ON ts.TeamId = ms.TeamId
LEFT JOIN DefenseStats ds ON ts.TeamId = ds.TeamId
ORDER BY WinPercentage DESC, AttackRating DESC;




            """

            cursor.execute(query)
            results = cursor.fetchall()

            # Populate the table widget with results
            self.performance_table.setRowCount(len(results))
            self.performance_table.setColumnCount(5)
            self.performance_table.setHorizontalHeaderLabels(
                ["Team Name", "Win %", "Attack Rating", "Midfield Rating", "Defense Rating"]
            )

            for row_idx, row_data in enumerate(results):
                for col_idx, cell_data in enumerate(row_data):
                    self.performance_table.setItem(row_idx, col_idx, QTableWidgetItem(f"{cell_data:.2f}" if isinstance(cell_data, float) else str(cell_data)))

            cursor.close()

        except odbc.DatabaseError as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


  

class AdminPortal(QMainWindow):
    def __init__(self):
        """
        Initialize the Admin Portal window.
        """
        super(AdminPortal, self).__init__()
        uic.loadUi("AdminPortal.ui", self)  # Save the XML file as admin_portal.ui

        # Set up UI components
        self.setup_ui()

    def setup_ui(self):
        """
        Connect buttons to their respective functions.
        """
        # Find widgets
        self.player_deletion_button = self.findChild(QPushButton, "pushButton_2")
        self.player_addition_button = self.findChild(QPushButton, "pushButton")
        self.team_addition_button = self.findChild(QPushButton, "pushButton_3")
        self.team_deletion_button = self.findChild(QPushButton, "pushButton_4")
        self.add_match_button = self.findChild(QPushButton, "pushButton_5")
        self.logout_button = self.findChild(QPushButton, "pushButton_6")

        self.title_label = self.findChild(QLabel, "label")

        # Set button connections
        self.player_deletion_button.clicked.connect(self.handle_player_deletion)
        self.player_addition_button.clicked.connect(self.handle_player_addition)
        self.team_addition_button.clicked.connect(self.handle_team_addition)
        self.team_deletion_button.clicked.connect(self.handle_team_deletion)
        self.add_match_button.clicked.connect(self.handle_match_details)
        self.logout_button.clicked.connect(self.logout)

    def handle_player_deletion(self):
        """
        Handle Player Deletion action.
        """
        widget.setCurrentIndex(12)
        # QMessageBox.information(self, "Player Deletion", "Player Deletion functionality selected.")

    def handle_player_addition(self):
        """
        Handle Player Addition action.
        """
        widget.setCurrentIndex(13)
        # QMessageBox.information(self, "Player Addition", "Player Addition functionality selected.")

    def handle_team_addition(self):
        """
        Handle Team Addition action.
        """
        widget.setCurrentIndex(14)
        # QMessageBox.information(self, "Team Addition", "Team Addition functionality selected.")

    def handle_team_deletion(self):
        """
        Handle Team Deletion action.
        """
        widget.setCurrentIndex(15)
        # QMessageBox.information(self, "Team Deletion", "Team Deletion functionality selected.")

    def handle_match_details(self):
        """
        Handle Add Match Details and Stats action.
        """
        widget.setCurrentIndex(16)
        # QMessageBox.information(self, "Add Match Details", "Add Match Details and Stats functionality selected.")

    def logout(self):
        """
        Handle Logout action.
        """
        QMessageBox.information(self, "Logout", "Logging out...")
        widget.setCurrentIndex(0)
        # QApplication.quit()



class PlayerAddition(QMainWindow):
    def __init__(self):
        """
        Initialize the Player Addition window.
        """
        super(PlayerAddition, self).__init__()
        uic.loadUi("PA.ui", self)  # Save the XML file as player_addition.ui
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect buttons to their respective methods.
        """
        # Input fields
        self.name_input = self.findChild(QLineEdit, "lineEdit")
        self.dob_input = self.findChild(QLineEdit, "lineEdit_2")
        self.nationality_input = self.findChild(QLineEdit, "lineEdit_3")
        self.position_input = self.findChild(QLineEdit, "lineEdit_4")
        self.team_id_input = self.findChild(QLineEdit, "lineEdit_5")

        # Buttons
        self.add_button = self.findChild(QPushButton, "pushButton")
        self.back_button = self.findChild(QPushButton, "pushButton_2")

        # Connect buttons
        self.add_button.clicked.connect(self.add_player)
        self.back_button.clicked.connect(self.go_back)

    


    def generate_random_password(self, length=6):
        """
        Generate a random password with the specified length.
        """
        import random
        import string
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))


    def add_player(self):
        """
        Validate inputs and add a new player to the database, including PlayerLogin and Performance.
        """
        # Retrieve input values
        name = self.name_input.text().strip()
        dob = self.dob_input.text().strip()
        nationality = self.nationality_input.text().strip()
        position = self.position_input.text().strip()
        team_id = self.team_id_input.text().strip()

        # Input Validation
        if not all([name, dob, nationality, position, team_id]):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        try:
            # Validate the format of DOB
            dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Date of Birth must be in the format YYYY-MM-DD.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Insert the player into the Player table
            dob_str = dob.strftime('%Y-%m-%d')  # Explicitly format DOB as string
            insert_player_query = """
                INSERT INTO Player (PlayerId, Name, DOB, Nationality, Position)
                SELECT COALESCE(MAX(PlayerId), 0) + 1, ?, ?, ?, ?
                FROM Player;
            """
            cursor.execute(insert_player_query, (name, dob_str, nationality, position))

            # Fetch the newly inserted Player ID
            cursor.execute("SELECT MAX(PlayerId) FROM Player;")
            player_id = cursor.fetchone()[0]

            # Other steps remain unchanged...
            insert_performance_query = """
                INSERT INTO Performance (PlayerId, Season, MatchesPlayed, Goals, Assists, Saves, Tackles, YellowCards, RedCards)
                VALUES (?, YEAR(GETDATE()), 0, 0, 0, 0, 0, 0, 0);
            """
            cursor.execute(insert_performance_query, (player_id,))

            insert_contract_query = """
                INSERT INTO Contract (ContractId, PlayerId, TeamId, Salary, StartDate, EndDate)
                VALUES (
                    (SELECT ISNULL(MAX(ContractId), 0) + 1 FROM Contract), 
                    ?, ?, 0, GETDATE(), DATEADD(YEAR, 3, GETDATE())
                );
            """
            cursor.execute(insert_contract_query, (player_id, team_id))

            username = f"P{player_id}"
            password = self.generate_random_password()
            insert_login_query = """
                INSERT INTO Player_Login (PlayerId, Username, Password)
                VALUES (?, ?, ?);
            """
            cursor.execute(insert_login_query, (player_id, username, password))

            connection.commit()
            QMessageBox.information(self, "Success", f"Player added successfully!\n\nUsername: {username}\nPassword: {password}")
            cursor.close()
            self.clear_inputs()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")




    def clear_inputs(self):
        """
        Clear all input fields.
        """
        self.name_input.clear()
        self.age_input.clear()
        self.nationality_input.clear()
        self.position_input.clear()
        self.team_id_input.clear()

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(11)
        self.close()


class PlayerDeletion(QMainWindow):
    def __init__(self):
        """
        Initialize the Player Deletion window.
        """
        super(PlayerDeletion, self).__init__()
        uic.loadUi("PD.ui", self)  # Save the XML as PD.ui
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect buttons to their respective methods.
        """
        # Input field
        self.player_id_input = self.findChild(QLineEdit, "lineEdit")

        # Buttons
        self.remove_button = self.findChild(QPushButton, "pushButton")
        self.back_button = self.findChild(QPushButton, "pushButton_2")

        # Connect buttons
        self.remove_button.clicked.connect(self.remove_player)
        self.back_button.clicked.connect(self.go_back)

    def remove_player(self):
        """
        Validate the Player ID input and delete the player and all related data from the database.
        """
        player_id = self.player_id_input.text().strip()

        if not player_id:
            QMessageBox.warning(self, "Input Error", "Player ID cannot be empty.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Check if the Player ID exists
            check_query = "SELECT COUNT(*) FROM Player WHERE PlayerId = ?;"
            cursor.execute(check_query, (player_id,))
            player_exists = cursor.fetchone()[0]

            if not player_exists:
                QMessageBox.warning(self, "Error", "Player ID not found in the database.")
                return

            # Step 2: Delete dependent rows in the correct order
            # Delete from Transfer table (using ContractId linked to PlayerId)
            delete_transfer_query = """
                DELETE FROM Transfer
                WHERE OldContractId IN (SELECT ContractId FROM Contract WHERE PlayerId = ?)
                   OR NewContractId IN (SELECT ContractId FROM Contract WHERE PlayerId = ?);
            """
            cursor.execute(delete_transfer_query, (player_id, player_id))

            # Delete from PlayerOffers table
            delete_offers_query = "DELETE FROM PlayerOffers WHERE PlayerId = ?;"
            cursor.execute(delete_offers_query, (player_id,))

            # Delete from Performance table
            delete_performance_query = "DELETE FROM Performance WHERE PlayerId = ?;"
            cursor.execute(delete_performance_query, (player_id,))

            # Delete from PlayerLogin table
            delete_login_query = "DELETE FROM Player_Login WHERE PlayerId = ?;"
            cursor.execute(delete_login_query, (player_id,))

            # Delete from Contract table
            delete_contract_query = "DELETE FROM Contract WHERE PlayerId = ?;"
            cursor.execute(delete_contract_query, (player_id,))

            # Step 3: Delete the player from the Player table
            delete_player_query = "DELETE FROM Player WHERE PlayerId = ?;"
            cursor.execute(delete_player_query, (player_id,))

            # Commit all changes
            connection.commit()

            # Success message
            QMessageBox.information(self, "Success", f"Player with ID {player_id} and related data have been removed successfully.")
            self.player_id_input.clear()

            cursor.close()

        except odbc.DatabaseError as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the player: {e}")

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(11)
        self.close()



class TeamAddition(QMainWindow):
    def __init__(self):
        """
        Initialize the Team Addition window.
        """
        super(TeamAddition, self).__init__()
        uic.loadUi("TA.ui", self)  # Save the XML as team_addition.ui
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect buttons to their respective methods.
        """
        # Input fields
        self.team_name_input = self.findChild(QLineEdit, "lineEdit")
        self.founding_year_input = self.findChild(QLineEdit, "lineEdit_2")
        self.stadium_input = self.findChild(QLineEdit, "lineEdit_4")

        # Buttons
        self.add_button = self.findChild(QPushButton, "pushButton")
        self.back_button = self.findChild(QPushButton, "pushButton_2")

        # Connect buttons
        self.add_button.clicked.connect(self.add_team)
        self.back_button.clicked.connect(self.go_back)

    def generate_random_password(self, length=6):
        """
        Generate a random password with the specified length.
        """
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def add_team(self):
        """
        Validate inputs and add a new team to the Team table and team_login table.
        """
        # Retrieve input values
        team_name = self.team_name_input.text().strip()
        founding_year = self.founding_year_input.text().strip()
        stadium = self.stadium_input.text().strip()

        # Input Validation
        if not all([team_name, founding_year, stadium]):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        try:
            founding_year = int(founding_year)
            if founding_year < 1800 or founding_year > 2024:
                QMessageBox.warning(self, "Input Error", "Founding Year must be between 1800 and 2024.")
                return
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Founding Year must be a valid number.")
            return

        try:
            cursor = connection.cursor()

            # Check if the team already exists
            check_query = "SELECT COUNT(*) FROM Team WHERE Name = ?;"
            cursor.execute(check_query, (team_name,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Error", "A team with this name already exists.")
                return

            # Step 1: Insert team into the Team table
            insert_team_query = """
                INSERT INTO Team (TeamId, Name, FoundingYear, Stadium)
                VALUES (
                    (SELECT COALESCE(MAX(TeamId), 0) + 1 FROM Team),
                    ?, ?, ?
                );
            """
            cursor.execute(insert_team_query, (team_name, founding_year, stadium))

            # Step 2: Fetch the newly inserted Team ID
            cursor.execute("SELECT MAX(TeamId) FROM Team;")
            team_id = cursor.fetchone()[0]

            # Step 3: Generate login credentials
            username = f"T{team_id}"  # Username: "T" followed by Team ID
            password = self.generate_random_password()

            # Step 4: Insert team login credentials into the team_login table
            insert_login_query = """
                INSERT INTO team_login (teamid, username, password)
                VALUES (?, ?, ?);
            """
            cursor.execute(insert_login_query, (team_id, username, password))

            # Commit changes
            connection.commit()

            # Success message
            QMessageBox.information(
                self, 
                "Success", 
                f"Team '{team_name}' added successfully!\n\nUsername: {username}\nPassword: {password}"
            )

            self.clear_inputs()
            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def clear_inputs(self):
        """
        Clear all input fields.
        """
        self.team_name_input.clear()
        self.founding_year_input.clear()
        self.stadium_input.clear()

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(11)
        self.close()


class TeamDeletion(QMainWindow):
    def __init__(self):
        """
        Initialize the Team Deletion window.
        """
        super(TeamDeletion, self).__init__()
        uic.loadUi("TD.ui", self)  # Load the UI file for team deletion
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect buttons to their respective methods.
        """
        # Input field
        self.team_id_input = self.findChild(QLineEdit, "lineEdit")  # Only Team ID input

        # Buttons
        self.delete_button = self.findChild(QPushButton, "pushButton")
        self.back_button = self.findChild(QPushButton, "pushButton_2")

        # Connect buttons
        self.delete_button.clicked.connect(self.delete_team)
        self.back_button.clicked.connect(self.go_back)

    def delete_team(self):
        """
        Validate inputs, delete the team and all its associated players but skip MatchTeam deletion.
        """
        team_id = self.team_id_input.text().strip()

        if not team_id:
            QMessageBox.warning(self, "Input Error", "Team ID cannot be empty.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Check if the team exists
            check_query = "SELECT COUNT(*) FROM Team WHERE TeamId = ?;"
            cursor.execute(check_query, (team_id,))
            team_exists = cursor.fetchone()[0]

            if not team_exists:
                QMessageBox.warning(self, "Error", "No team found with the specified ID.")
                return

            # Step 2: Temporarily disable foreign key constraints
            disable_constraints_query = "ALTER TABLE MatchTeam NOCHECK CONSTRAINT ALL;"
            cursor.execute(disable_constraints_query)

            # Step 3: Fetch all Player IDs associated with the team
            fetch_players_query = """
                SELECT PlayerId 
                FROM Contract 
                WHERE TeamId = ?;
            """
            cursor.execute(fetch_players_query, (team_id,))
            players = cursor.fetchall()
            player_ids = [player[0] for player in players]

            # Step 4: Delete all dependent data for each player
            for player_id in player_ids:
                # Delete from Transfer table
                delete_transfer_query = """
                    DELETE FROM Transfer 
                    WHERE OldContractId IN (
                        SELECT ContractId FROM Contract WHERE PlayerId = ?
                    )
                    OR NewContractId IN (
                        SELECT ContractId FROM Contract WHERE PlayerId = ?
                    );
                """
                cursor.execute(delete_transfer_query, (player_id, player_id))

                # Delete from Performance table
                delete_performance_query = "DELETE FROM Performance WHERE PlayerId = ?;"
                cursor.execute(delete_performance_query, (player_id,))

                # Delete from PlayerOffers table
                delete_offers_query = "DELETE FROM PlayerOffers WHERE PlayerId = ?;"
                cursor.execute(delete_offers_query, (player_id,))

                # Delete from PlayerLogin table
                delete_login_query = "DELETE FROM Player_Login WHERE PlayerId = ?;"
                cursor.execute(delete_login_query, (player_id,))

                # Delete Contracts
                delete_contract_query = "DELETE FROM Contract WHERE PlayerId = ?;"
                cursor.execute(delete_contract_query, (player_id,))

                # Finally, delete the Player
                delete_player_query = "DELETE FROM Player WHERE PlayerId = ?;"
                cursor.execute(delete_player_query, (player_id,))

            # Step 5: Delete TeamLogin records
            delete_team_login_query = "DELETE FROM team_login WHERE teamid = ?;"
            cursor.execute(delete_team_login_query, (team_id,))

            # Step 6: Delete the Team itself
            delete_team_query = "DELETE FROM Team WHERE TeamId = ?;"
            cursor.execute(delete_team_query, (team_id,))

            # Step 7: Re-enable foreign key constraints
            enable_constraints_query = "ALTER TABLE MatchTeam CHECK CONSTRAINT ALL;"
            cursor.execute(enable_constraints_query)

            # Commit all changes
            connection.commit()

            # Success message
            QMessageBox.information(self, "Success", f"Team with ID {team_id} and all associated players have been deleted successfully.")
            self.clear_inputs()

            cursor.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")



    def clear_inputs(self):
        """
        Clear the input field.
        """
        self.team_id_input.clear()

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(11)
        self.close()


class MatchScoreAddition(QMainWindow):
    def __init__(self):
        """
        Initialize the Match Score Addition window.
        """
        super(MatchScoreAddition, self).__init__()
        uic.loadUi("Add_Match_Score.ui", self)  # Load your UI file here
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect buttons to their respective methods.
        """
        # Input fields
        self.home_team_id_input = self.findChild(QLineEdit, "lineEdit")   # Home Team ID
        self.home_score_input = self.findChild(QLineEdit, "lineEdit_2")  # Home Team Score
        self.away_team_id_input = self.findChild(QLineEdit, "lineEdit_3")   # Away Team ID
        self.away_score_input = self.findChild(QLineEdit, "lineEdit_4")  # Away Team Score

        # Buttons
        self.back_button = self.findChild(QPushButton, "pushButton_2")
        self.add_stats_button = self.findChild(QPushButton, "pushButton_3")

        # Connect buttons
        self.add_stats_button.clicked.connect(self.add_match_score)
        self.back_button.clicked.connect(self.go_back)

    def add_match_score(self):
        """
        Validate inputs and add match stats to the database.
        """
        # Retrieve input values
        home_team_id = self.home_team_id_input.text().strip()
        home_score = self.home_score_input.text().strip()
        away_team_id = self.away_team_id_input.text().strip()
        away_score = self.away_score_input.text().strip()

        global current_user_id 
        global current_team_id
        current_user_id = home_team_id
        current_team_id = away_team_id
        
        # Input validation
        if not all([home_team_id, home_score, away_team_id, away_score]):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        try:
            home_score = int(home_score)
            away_score = int(away_score)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Scores must be valid numbers.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Insert the match into the Match table
            insert_match_query = """
                INSERT INTO Match (MatchId, Date)
                VALUES (
                    (SELECT ISNULL(MAX(MatchId), 0) + 1 FROM Match),
                    GETDATE()
                );
            """
            # Determine the match result based on scores
            if home_score > away_score:
                match_result = home_team_id
            elif away_score > home_score:
                match_result =away_team_id
            else:
                match_result = 0

            cursor.execute(insert_match_query)
            connection.commit()

            # Step 2: Fetch the newly added Match ID
            cursor.execute("SELECT MAX(MatchId) FROM Match;")
            match_id = cursor.fetchone()[0]

            # Step 3: Insert stats into MatchTeam table
            insert_team_stats = """
                INSERT INTO MatchTeam (MatchId, season, HometeamID, awayteamID , hometeamScore,awayteamscore,result)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            

            cursor.execute(insert_team_stats, (match_id, datetime.now().year, home_team_id, away_team_id, home_score, away_score, match_result))
            connection.commit()

            # Success message
            QMessageBox.information(self, "Success", "Match scores added successfully!")

            # Clear the input fields
            self.clear_inputs()

            cursor.close()

            # Navigate to the next screen
            widget.setCurrentIndex(17)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def clear_inputs(self):
        """
        Clear all input fields.
        """
        self.home_team_id_input.clear()
        self.home_score_input.clear()
        self.away_team_id_input.clear()
        self.away_score_input.clear()

    def go_back(self):
        """
        Navigate back to the previous screen.
        """
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(11)  # Adjust widget index if necessary
        # self.close()

    def go_to_next_screen(self):
        """
        Navigate to the next screen after successfully adding stats.
        """
        self.widget.setCurrentIndex(12)  # Adjust the index for the next screen in your stacked widget


class TeamPlayersDisplay(QMainWindow):
    def __init__(self):
        """
        Initialize the Home and Away Team Players Display window.
        """
        super(TeamPlayersDisplay, self).__init__()
        uic.loadUi("Match_Team_PlayersTable.ui", self)  # Load the XML UI file
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and populate team tables.
        """
        global bid

        # Table Widgets
        self.home_team_table = self.findChild(QTableWidget, "tableWidget")
        self.away_team_table = self.findChild(QTableWidget, "tableWidget_2")

        # Buttons
        self.done_button = self.findChild(QPushButton, "pushButton_3")

        # Connect Buttons
        self.done_button.clicked.connect(self.done_button_clicked)

        # Table Row Selection (Item Clicked Event)
        if self.home_team_table:
            self.home_team_table.itemClicked.connect(self.home_row_selected)
        if self.away_team_table:
            self.away_team_table.itemClicked.connect(self.away_row_selected)

    def showEvent(self, event):
        """
        Called when the window is shown. Loads the data dynamically using global variables.
        """
        super(TeamPlayersDisplay, self).showEvent(event)
        self.load_team_players()

    def load_team_players(self):
        """
        Load players of both Home and Away teams into respective tables using global variables.
        """
        try:
            cursor = connection.cursor()

            # Load Home Team Players using current_user_id
            home_team_query = """
                
    SELECT Player.PlayerId, Player.Name, Player.Nationality, Player.Position, 
           FLOOR(DATEDIFF(DAY, Player.DOB, GETDATE()) / 365.25) AS Age
    FROM Player
    INNER JOIN Contract ON Player.PlayerId = Contract.PlayerId
    WHERE Contract.TeamId = ?;
"""

            
            cursor.execute(home_team_query, (current_user_id,))
            home_players = cursor.fetchall()
            self.populate_table(self.home_team_table, home_players)

            # Load Away Team Players using current_team_id
            away_team_query = """
                SELECT Player.PlayerId, Player.Name, Player.Nationality, Player.Position, 
           FLOOR(DATEDIFF(DAY, Player.DOB, GETDATE()) / 365.25) AS Age
    FROM Player
    INNER JOIN Contract ON Player.PlayerId = Contract.PlayerId
    WHERE Contract.TeamId = ?;
            """
            cursor.execute(away_team_query, (current_team_id,))
            away_players = cursor.fetchall()
            self.populate_table(self.away_team_table, away_players)

            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while loading players: {e}")

    def populate_table(self, table, players):
        """
        Populate a QTableWidget with player data.
        """
        table.setRowCount(len(players))
        table.setColumnCount(5)  # Columns: PlayerID, Player Name, Nationality, Position, Age
        table.setHorizontalHeaderLabels(["PlayerID", "Player Name", "Nationality", "Position", "Age"])

        for row_idx, player in enumerate(players):
            for col_idx, value in enumerate(player):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        # Enable single-row selection for PyQt6
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def home_row_selected(self, item):
        """
        Handles row selection in the Home Team table.
        """
        row = item.row()
        global bid
        bid = self.home_team_table.item(row, 0).text()  # PlayerID is in column 0
        self.navigate_to_next_screen()

    def away_row_selected(self, item):
        """
        Handles row selection in the Away Team table.
        """
        row = item.row()
        global bid
        bid = self.away_team_table.item(row, 0).text()  # PlayerID is in column 0
        self.navigate_to_next_screen()

    def navigate_to_next_screen(self):
        """
        Navigate to the next screen after selecting a player.
        """
        widget.setCurrentIndex(18)

    def done_button_clicked(self):
        """
        Reset global variables and navigate to the previous screen.
        """
        global current_user_id, current_team_id, bid
        current_user_id = None
        current_team_id = None
        bid = None
        widget.setCurrentIndex(11)
        self.close()



class InputStats(QMainWindow):
    def __init__(self):
        """
        Initialize the Input Stats window.
        """
        super(InputStats, self).__init__()
        uic.loadUi("Player_stats_input.ui", self)  # Load the XML file
        self.setup_ui()

    def setup_ui(self):
        """
        Set up UI components and connect the Done button.
        """
        # LineEdits for input
        self.goals_input = self.findChild(QLineEdit, "lineEdit_G1")
        self.assists_input = self.findChild(QLineEdit, "lineEdit_A1")
        self.saves_input = self.findChild(QLineEdit, "lineEdit_S1")
        self.tackles_input = self.findChild(QLineEdit, "lineEdit_T1")
        self.yellow_cards_input = self.findChild(QLineEdit, "lineEdit_YC1")
        self.red_cards_input = self.findChild(QLineEdit, "lineEdit_RC1")

        # Buttons
        self.done_button = self.findChild(QPushButton, "pushButton")
        self.done_button.clicked.connect(self.update_performance_stats)

    def showEvent(self, event):
        """
        This method is triggered when the screen is displayed.
        Resets inputs and loads necessary data.
        """
        super(InputStats, self).showEvent(event)
        self.load_screen()

    def load_screen(self):
        """
        Clear inputs and prepare the screen for a fresh start.
        """
        # Clear all inputs
        self.clear_inputs()
        
        # Load the PlayerID from global variable bid
        global bid
        if bid:
            self.findChild(QLineEdit, "lineEdit_MP").setText(str(bid))
        else:
            QMessageBox.warning(self, "Error", "No player selected.")
            widget.setCurrentIndex(17)  # Navigate back to the previous screen if no player ID exists
            self.close()

    def update_performance_stats(self):
        """
        Update the performance stats for the player in the Performance table.
        """
        global bid  # Player ID passed from previous screen
        if not bid:
            QMessageBox.warning(self, "Error", "No player selected.")
            return

        # Retrieve input values
        goals = self.goals_input.text().strip()
        assists = self.assists_input.text().strip()
        saves = self.saves_input.text().strip()
        tackles = self.tackles_input.text().strip()
        yellow_cards = self.yellow_cards_input.text().strip()
        red_cards = self.red_cards_input.text().strip()

        # Input Validation and Conversion
        try:
            goals = int(goals) if goals else 0
            assists = int(assists) if assists else 0
            saves = int(saves) if saves else 0
            tackles = int(tackles) if tackles else 0
            yellow_cards = int(yellow_cards) if yellow_cards else 0
            red_cards = int(red_cards) if red_cards else 0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "All stat fields must be valid numbers.")
            return

        try:
            cursor = connection.cursor()

            # Step 1: Get the latest season for the player
            latest_season_query = """
                SELECT MAX(Season) FROM Performance WHERE PlayerId = ?;
            """
            cursor.execute(latest_season_query, (bid,))
            latest_season = cursor.fetchone()[0]

            if not latest_season:
                QMessageBox.warning(self, "Error", "No performance record found for the player.")
                return

            # Step 2: Update the performance stats
            update_query = """
                UPDATE Performance
                SET Goals = Goals + ?,
                    Assists = Assists + ?,
                    Saves = Saves + ?,
                    Tackles = Tackles + ?,
                    YellowCards = YellowCards + ?,
                    RedCards = RedCards + ?,
                    MatchesPlayed = MatchesPlayed + 1
                WHERE PlayerId = ? AND Season = ?;
            """
            cursor.execute(update_query, (goals, assists, saves, tackles, yellow_cards, red_cards, bid, latest_season))
            connection.commit()

            QMessageBox.information(self, "Success", "Player stats updated successfully!")

            # Clear inputs and navigate back
            self.clear_inputs()
            self.go_back()

            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

    def clear_inputs(self):
        """
        Clear all input fields.
        """
        self.goals_input.clear()
        self.assists_input.clear()
        self.saves_input.clear()
        self.tackles_input.clear()
        self.yellow_cards_input.clear()
        self.red_cards_input.clear()

    def go_back(self):
        """
        Reset global variables and navigate back to the previous screen.
        """
        global bid
        bid = None

        # Navigate to the previous screen
        QMessageBox.information(self, "Back", "Returning to the previous screen...")
        widget.setCurrentIndex(17)  # Update this as per your widget navigation logic
        self.close()






  

# Add other screens as classes following the same pattern

# Main Application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create QStackedWidget
    widget = QStackedWidget()

    # Add screens to the QStackedWidget in the desired order
    dashboard_screen = Dashboard()          # Index 0
    player_bidding_screen = PlayerBidding() # Index 1
    team_performance_screen = TeamPerformance() # Index 2
    offers_screen = OffersScreen()          # Index 3
    login_screen = Login()                  # Index 4
    player_portal = PlayerPortal()          # Index 5
    team_portal = TeamPortal()              # Index 6
    calculate_bid = CalculateBid()          # Index 7
    make_offer = MakeOffer()                # Index 8
    team_players = TeamPlayers()            # Index 9
    offer_details = OfferDetails()          # Index 10
    admin_portal = AdminPortal()            # Index 11
    player_addition = PlayerAddition()      # Index 12
    player_deletion = PlayerDeletion()      # Index 13
    team_addition = TeamAddition()          # Index 14
    team_deletion = TeamDeletion()          # Index 15
    match_score = MatchScoreAddition()        # Index 16
    teams_display = TeamPlayersDisplay()    # Index 17
    input_stats = InputStats()              # Index 18

    widget.addWidget(dashboard_screen)     
    widget.addWidget(player_bidding_screen) 
    widget.addWidget(team_performance_screen ) 
    widget.addWidget(offers_screen)         
    widget.addWidget(login_screen)
    widget.addWidget(player_portal)
    widget.addWidget(team_portal)
    widget.addWidget(calculate_bid)
    widget.addWidget(make_offer)
    widget.addWidget(team_players)
    widget.addWidget(offer_details)
    widget.addWidget(admin_portal)
    widget.addWidget(player_addition)
    widget.addWidget(player_deletion)
    widget.addWidget(team_addition)
    widget.addWidget(team_deletion)
    widget.addWidget(match_score)
    widget.addWidget(teams_display)
    widget.addWidget(input_stats)

    # Set initial screen
    widget.setCurrentIndex(0)

    # Configure window size
    widget.setFixedHeight(800)
    widget.setFixedWidth(1000)

    # Show the stacked widget
    widget.show()

    # Execute the application
    sys.exit(app.exec())

