import MySQLdb
import collections
import general_utils as Ugen
import time
import os
from Tkinter import Tk
from pymongo import MongoClient


def get_db(db_name):
    # For local use
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    db = client[db_name]
    return db

#make read from db, write to db, modify db functions as required



