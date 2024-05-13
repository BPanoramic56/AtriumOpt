import mysql.connector
from mysql.connector import Error
import pandas as pd
import configparser

config      = configparser.ConfigParser()
config.read("configurations.ini")
Location    = config["UserInformation"]["Location"]
Name        = config["UserInformation"]["Name"]
Password    = config["UserInformation"]["Password"]

def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = host_name,
            user = user_name,
            passwd = user_password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

def raw_query(query):
    connection._execute_query(query)

connection = create_server_connection(Location, Name, Password)
print(connection)