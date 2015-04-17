
import json
import urllib2
import os
import time
import datetime
import ast
from bs4 import BeautifulSoup
import numpy
import operator
import math
import database_operations as dbo
import data_scrapping
import data_scrapping_utils as Uds
import re
import requests
import FD_operations as fdo
import general_utils as Ugen
import sys

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).
    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_NHLgameID_date():
	todays_date=time.strftime("%Y-%m-%d")	
	date_id_dict={}
	NHL_gamedate_Url='http://live.nhle.com/GameData/GCScoreboard/'+todays_date+'.jsonp'
	nhle_dict=Uds.get_JSON_data(NHL_gamedate_Url, ['loadScoreboard(',')'])
	for e in nhle_dict['games']:
		date_id_dict[e['id']]=todays_date
	return date_id_dict

def get_FD_playerdata_old():
 	FD_list = data_scrapping.get_FD_playerlist()
 	FD_player_dict={}
 	for fd_key in FD_list:
 		FD_player_dict[FD_list[fd_key][1]]={}
 		FD_player_dict[FD_list[fd_key][1]]['Position']=FD_list[fd_key][0]
 		FD_player_dict[FD_list[fd_key][1]]['FD_Salary']=FD_list[fd_key][5]
 		FD_player_dict[FD_list[fd_key][1]]['FD_FPPG']=FD_list[fd_key][6]
 		FD_player_dict[FD_list[fd_key][1]]['FD_GP']=FD_list[fd_key][7]

 	Cell('Output',1,1).value=FD_player_dict
 	return FD_player_dict 

def hist_web_lineups():
    todays_date=time.strftime("%Y-%m-%d")
    last_date=Cell('Parameters','clLastDate').value
    if not todays_date==str(last_date)[0:10]:
        print 'enter lineups for todays date'
        os.system('pause')
        return
    dfn_nba=Cell('Parameters','clDFNNBA').value
    rw_nba=Cell('Parameters','clRWNBA').value
    rw_mlb=Cell('Parameters','clRWMLB').value
    db_data=[todays_date,dfn_nba,rw_nba,rw_mlb]
    columns='Date,DFN_NBA,RW_NBA,RW_MLB'
    table='hist_backtest_data'
    placeholders = ', '.join(['%s'] * len(db_data))
    print 'now historizing'
    dbo.insert_mysql(table,columns,placeholders,db_data)
    print 'web_lineups historized succesfully'
    return

def sample_sql_select():
    sql="SELECT * FROM hist_backtest_data WHERE Date='2015-04-12'"
    cur = dbo.get_connection_cursor()
    cur.execute(sql)
    resultset = cur.fetchall()
    return resultset

def hist_FD_playerdata(Sport):
    question= 'Only run this function if salaries are for todays games. Continue?'
    if not query_yes_no(question,'no'):
        return
    player_map = Ugen.excel_mapping('Player Map',1,2)
    FD_dict = data_scrapping.get_FD_playerlist()
    todays_date=time.strftime("%Y-%m-%d")
    db_data=[]
    for fd_key in FD_dict:
        player=FD_dict[fd_key][1]
        if player in player_map:
            mapped_player=player_map[player]
        else:
            mapped_player=player
        position=FD_dict[fd_key][0]
        FD_Salary=FD_dict[fd_key][5]
        FD_FPPG=FD_dict[fd_key][6]
        FD_GP=FD_dict[fd_key][7]
        db_data=[Sport,todays_date,mapped_player,FD_Salary,FD_FPPG,FD_GP,position]
        columns='Sport,Date,Player,FD_Salary,FD_FPPG,FD_GP,Position'
        placeholders = ', '.join(['%s'] * len(db_data))
        table='hist_fanduel_data'
        print 'now historizing %s player %s' % (Sport,mapped_player)
        dbo.insert_mysql(table,columns, placeholders, db_data)
    return

#hist_web_lineups()
#hist_FD_playerdata('MLB')
#print sample_sql_select()
#Remove duplicate rows SQL statement
#ALTER IGNORE TABLE hist_backtest_data ADD UNIQUE KEY idx1(date);


#TESTING COLE'S GET CONTESTS FUNCTIONS
s,session_id=fdo.get_fanduel_session()
contest_dict=data_scrapping.get_FD_contests(s)
i=1
for e in contest_dict:
    Cell(i,1).value=e
    i=i+1
fdo.end_fanduel_session(s)
