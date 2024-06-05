import time
import pandas as pd
import configparser
import pymysql
import AtriumOpt
import threading
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

def create_server_connection():
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

def raw_query(server_connection, query):
    server_connection._execute_query(query)

def state_card_existence(server_connection, card_number):
    with server_connection.cursor() as cursor:
        print(Database)
        query = f"SELECT * FROM {Table} WHERE CardID = \"{card_number}\""
        cursor.execute(query)
        if (len(cursor.fetchall()) > 0):
            return True
        return False

def change_card(card_number, card_access, user):
    card_access = " - ".join(card_access)
    server_connection = create_server_connection()
    if (state_card_existence(server_connection, card_number)):
        update_card(server_connection, card_number, card_access, user)
    else:
        create_card(server_connection, card_number, card_access, user)
    server_connection.close()

def create_card(server_connection, card_number, card_access, user):
    with server_connection.cursor() as cursor:
        query = f"INSERT INTO {Table} (CardID, Access, User) VALUES (\"{card_number}\", \"{card_access}\", \"{user}\")"
        cursor.execute(query)
    server_connection.commit()
    
def update_card(server_connection, card_number, card_access, user):
    with server_connection.cursor() as cursor:
        query = f"UPDATE {Table} SET Access = \"{card_access}\", User = \"{user}\" WHERE CardID = {card_number}"
        cursor.execute(query)
    server_connection.commit()

def fectch_changes():
    print("Fetching changes")
    server_connection = create_server_connection()
    with server_connection.cursor() as cursor:
        query = f"SELECT * FROM {Table} WHERE Completed = 0"
        cursor.execute(query)
        card_change_list = cursor.fetchall()
    
    if (len(card_change_list) == 0):
        return
    
    processed_info = dict()
        
    # Iterate over each row
    for row in card_change_list:
        processed_info[row["CardID"]] = row["Access"]

    for item in processed_info:
        current_access = processed_info[item]
        id_list = [k for k,v in processed_info.items() if v == current_access]
        print("Processed Info 1: " + str(processed_info))
        for id in id_list:
            processed_info.pop(id)
        print("Processed Info 2: " + str(processed_info))

        sender = AtriumOpt.AtriumCrawler(Username, AtriumPwd, id_list, current_access.split(", "))
        
        for id in id_list:
            with server_connection.cursor() as cursor:
                query = f"UPDATE CardChange SET Completed = 1 WHERE CardID = \'{id}\'"
                cursor.execute(query)
                card_change_list = cursor.fetchall()
            Notifier.notify("Card Change in Progress: ", f"Card {id} changed to access {current_access} by user {Username}", "", 0)

        sender.run()
        server_connection.commit()

    server_connection.close()

while True:
    fectch_changes()
    time.sleep(20)