import time
import pandas as pd
import configparser
import pymysql
import AtriumOpt
import Notifier
import SQLHandler

config = configparser.ConfigParser()
config.read("configurations.ini")

if __name__ == "__main__":
    while True:
        card    = input("Type the new card ID(s): ")
        access  = input("Type the new card Access(s): ")
        user    = input("Type the new card User: ")

        if len(access) == 1:
            access = "CONF" + access

        for card_id in card:
            SQLHandler.__init__(card_id, access, user)