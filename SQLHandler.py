import time
import configparser
import pymysql
import AtriumOpt
import Notifier

config      = configparser.ConfigParser()
config.read("configurations.ini")

Location    = config["User Information"]["Location"]
Name        = config["User Information"]["Name"]
Password    = config["User Information"]["Password"]
Database    = config["User Information"]["Database"]
Table       = config["User Information"]["Table"]
Username    = config["Atrium Information"]["Username"]
AtriumPwd   = config["Atrium Information"]["Password"]
QueryDelay  = int(config["Script Information"]["Query"])


def __init__(card, access, user):
    """
        Calls the change_card function. Used as a simple constructor
    Args:
        card (int):         The card(s) to be changed
        access (string):    The desired access for the card
        user (string):      The user making the change
    """

    server_connection = create_server_connection()
    change_card(server_connection, card, access, user)
         

def create_server_connection():
    """
        Creates the connection with the SQL Server handling card changes
    Returns:
        Connection: A pymysql connection token
    """

    try:
        connection = pymysql.connect(
            host        = Location,
            user        = Name,
            passwd      = Password,
            db          = Database,
            charset     = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor
        )
        print("MySQL Database connection successful")
        return connection
    except Exception as e:
        print("There was a problem setting up the connection with the database.\n\t %s" % (e))

def state_card_existence(server_connection, card_number):
    """
        Determines if the desired card exists. Used to determine if the card should be added or updated on the SQL Server
    Args:
        server_connection (Connection): The connection token of the SQL server
        card_number (int):              The card to be checked

    Returns:
        Boolean: True if the card exists (has to be updated), False otherwise (has to be created)
    """

    with server_connection.cursor() as cursor:
        query = f"SELECT * FROM {Table} WHERE CardID = \"{card_number}\""
        cursor.execute(query)
        if (len(cursor.fetchall()) > 0):
            return True
        return False

def change_card(server_connection, card_number, card_access, user):
    """
        Determines which method has to be utilized in other to update the given card
    Args:
        server_connection (Connection):     The connection token of the SQL server
        card_number (int):                  The card ID to be changed
        card_access (string):               The desired card access
        user (string):                      The user making the change
    """

    if (state_card_existence(server_connection, card_number)):
        update_card(server_connection, card_number, card_access, user)
    else:
        create_card(server_connection, card_number, card_access, user)
    server_connection.close()

def create_card(server_connection, card_number, card_access, user):
    """
        Utilizes the given information to add the card to the SQL table
    Args:
        sserver_connection (Connection):    The connection token of the SQL server
        card_number (int):                  The card ID to be changed
        card_access (string):               The desired card access
        user (string):                      The user making the change
    """

    with server_connection.cursor() as cursor:
        query = f"INSERT INTO {Table} (CardID, Access, User) VALUES (\"{card_number}\", \"{card_access}\", \"{user}\")"
        cursor.execute(query)
    server_connection.commit()
    
def update_card(server_connection, card_number, card_access, user):
    """
        Utilizes the given information to update the card to the SQL table
    Args:
        sserver_connection (Connection):    The connection token of the SQL server
        card_number (int):                  The card ID to be changed
        card_access (string):               The desired card access
        user (string):                      The user making the change
    """

    with server_connection.cursor() as cursor:
        query = f"UPDATE {Table} SET Access = \"{card_access}\", User = \"{user}\" WHERE CardID = {card_number}"
        cursor.execute(query)
    server_connection.commit()

def create_processed_info(card_change_list):
    """
        Creates the processed info dictionary. Created for better readability
    Args:
        card_change_list (List): The list of cards that will be changed
    """

    processed_info = dict()
        
    for row in card_change_list:
        processed_info[row["CardID"]] = row["Access"]

def create_id_list(processed_info, current_access):
    """
        Creates the ID list of all the cards that will be changed to the same access.
        Since AtriumOpt works with access batches, this improves the speed in which changes are made by pre-generating those batches
    Args:
        processed_info (Dictionary):    Dictionary that contains all the cards and the respective desired access
        current_access (string):        The current access to be searched for batch creation
    """

    id_list = [k for k,v in processed_info.items() if v == current_access]
    print("Processed Info 1: " + str(processed_info))
    for id in id_list:
        processed_info.pop(id)
    print("Processed Info 2: " + str(processed_info))

def updated_completed_column(server_connection, id_list):
    """
        Updates the Completed column of the table
    Args:
        server_connection (_type_): The connection token of the SQL server
        id_list (List):             The list of cards that had their access successfully changed to the desired access
    """
    for id in id_list:
        with server_connection.cursor() as cursor:
            query = f"UPDATE CardChange SET Completed = 1 WHERE CardID = \'{id}\'"
            cursor.execute(query)

def fectch_changes(server_connection, sender):
    """
        Queries the SQL Server for changes in any card, represented by a Completed collumn value of zero, handling the new changes as needed
    Args:
        server_connection (Connection): The connection token of the SQL server
        sender (AtriumOpt):             The AtriumOpt instance utilizing Selenium Driver for it's changes
    """

    print("Fetching changes")
    with server_connection.cursor() as cursor:
        query = f"SELECT * FROM {Table} WHERE Completed = 0"
        cursor.execute(query)
        card_change_list = cursor.fetchall()
    
    if (len(card_change_list) == 0):
        return
    
    processed_info = create_processed_info(card_change_list)

    for item in list(processed_info):
        current_access = processed_info[item]
        id_list = create_id_list(processed_info, current_access)

        sender.run(id_list, current_access.split(", "))
        
        updated_completed_column(server_connection, id_list)

        Notifier.notify("Card change batch completed", f"Cards ({id}) were changed to access {current_access} by user {Username}", "", 0)

        server_connection.commit()

    server_connection.close()


if __name__ == "__main__":
    sender = AtriumOpt.AtriumCrawler(Username, AtriumPwd)

    while True:
        start = time.time()
        connection = create_server_connection()
        
        for i in range(QueryDelay):
            print (f"{i * '-'} {(20-i) * ' '} {int(i*100/QueryDelay)}%", end = "\r")
            time.sleep(1)
        print("")
        fectch_changes(connection, sender)