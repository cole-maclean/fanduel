import general_utils as Ugen
import time
import os
from Tkinter import Tk
from pymongo import MongoClient


def create_db_connection(db_name):
    client = MongoClient('localhost:27017')
    db = client[db_name]
    return db,client

def write_to_db(collection,doc,key_check=False):
    db,client=create_db_connection('fanduel')
    db[collection].insert(doc,check_keys=key_check)
    client.close()

def remove_from_db(collection,query,max_docs=False):
    db,client=create_db_connection('fanduel')
    if max_docs:
        db[collection].remove(query,max_docs)
    else:
        db[collection].remove(query)
    client.close()


def read_from_db(collection,query,projection=False):
    db,client=create_db_connection('fanduel')

    if projection:
        resultset=db[collection].find(query,projection)
    else:
        resultset=db[collection].find(query).limit(1)
    client.close()

    return resultset

def test_db():
    db,client=create_db_connection('fanduel')
    collection=db.hist_fanduel_data

    for doc in collection.find():
        print doc
    client.close()



# query={'date':'2015-11-16','sport':'NHL'}
# resultset=read_from_db('hist_fanduel_data',query)
# for doc in resultset:
#     print doc

#make read from db, write to db, modify db functions as required



