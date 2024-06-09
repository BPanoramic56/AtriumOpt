import time
import pandas as pd
import configparser
import pymysql
import AtriumOpt
import Notifier
import SQLHandler

config = configparser.ConfigParser()
config.read("configurations.ini")
Possible_Access = config(["Access Information"]["Possible"]).split(", ")

if __name__ == "__main__":
    while True:
        access  = input("Type the new card Access(s): ")
        exit = False
        
        for single_access in access:
            if single_access not in Possible_Access:
                print(f"The given access contains invalid words: {single_access}")
                exit = True

        if exit == True:
            continue

        card    = input("Type the new card ID(s): ")
        user    = input("Type the new card User: ")

        for card_id in card:
            SQLHandler.__init__(card_id, access, user)