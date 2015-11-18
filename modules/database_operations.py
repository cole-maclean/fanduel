import general_utils as Ugen
import time
import os
from Tkinter import Tk
from pymongo import MongoClient
import datetime as dt


def create_db_connection(db_name):
    client = MongoClient('localhost:27017')
    db = client[db_name]
    return db,client

def write_to_db(collection,doc,key_check=False):
    db,client=create_db_connection('fanduel')
    db[collection].insert(doc,check_keys=key_check)
    client.close()

def remove_from_db(collection,query=False,max_docs=False):
    db,client=create_db_connection('fanduel')
    if max_docs:
        db[collection].remove(query,max_docs)
    elif not query:
        print 'WARNING: you are about to drop entire collection: %s' % collection
        ans=Ugen.query_yes_no("Would you like to proceed?",'no')
        if ans:
            db[collection].remove()
            print 'collection successfully removed'
        else:
            print 'collection not removed'
    else:
        db[collection].remove(query)
        print 'record successfully removed'
    client.close()

def read_from_db(collection,query,projection=False):
    db,client=create_db_connection('fanduel')

    if projection:
        resultset=db[collection].find(query,projection)
    else:
        resultset=db[collection].find(query)#.limit(5)
    client.close()

    return list(resultset)


def delete_by_date(sport,collection,start_date,end_date=False): #date ranges are inclusive, YYYY-MM-DD format
    if end_date:
        query={'sport':sport,'date':{"$gte":dt.datetime.strptime(start_date,'%Y-%m-%d'),"$lte":dt.datetime.strptime(end_date,'%Y-%m-%d')}}
    else:
        query={'sport':sport,'date':dt.datetime.strptime(start_date,'%Y-%m-%d')}
    remove_from_db(collection,query)

def test_db():
    db,client=create_db_connection('fanduel')
    collection=db.hist_fanduel_data

    for doc in collection.find():
        print doc
    client.close()


# date='2012-02-15'
# new_date=dt.datetime.strptime(date,'%Y-%m-%d')

# resultset=read_from_db('hist_player_data',{'date':new_date,'sport':'NBA'})
# # print resultset
# for doc in resultset:
#     print doc

# remove_from_db('hist_event_data',{'sport':'NBA','date':new_date})
# remove_from_db('hist_player_data',{'sport':'NBA','date':new_date})


