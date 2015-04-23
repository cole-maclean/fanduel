import os
import time
import datetime
import ast
import database_operations as dbo
import data_scrapping
import data_scrapping_utils as Uds
import re
import requests
import FD_operations as fdo
import general_utils as Ugen
import sys

def get_NHLgameID_date():
	todays_date=time.strftime("%Y-%m-%d")	
	date_id_dict={}
	NHL_gamedate_Url='http://live.nhle.com/GameData/GCScoreboard/'+todays_date+'.jsonp'
	nhle_dict=Uds.get_JSON_data(NHL_gamedate_Url, ['loadScoreboard(',')'])
	for e in nhle_dict['games']:
		date_id_dict[e['id']]=todays_date
	return date_id_dict

def hist_web_lineups():
    table='hist_lineup_optimizers'
    recordset=dbo.get_table_last_row(table,'Date')
    last_date=Cell('Backtest_Parameters','clLastDate').value
    if str(recordset[0][0])==str(last_date)[0:10]:
        print "hist_web_lineups: a recordset already exists in table: %s for entered date" % table
        time.sleep(5)   
        return
    todays_date=time.strftime("%Y-%m-%d")
    if not todays_date==str(last_date)[0:10]:
        print "hist_web_lineups: enter lineups for todays date OR ensure you've entered today's date"
        time.sleep(5)
        return   
    dfn_nba=Cell('Backtest_Parameters','clDFNNBA').value
    rw_nba=Cell('Backtest_Parameters','clRWNBA').value
    rw_mlb=Cell('Backtest_Parameters','clRWMLB').value
    rw_nhl=Cell('Backtest_Parameters','clRWNHL').value
    #nhl_odds=
    #nba_odds=
    #mlb_odds=
    db_data=[todays_date,dfn_nba,rw_nba,rw_mlb,rw_nhl]
    columns='Date,DFN_NBA,RW_NBA,RW_MLB,RW_NHL'
    placeholders = ', '.join(['%s'] * len(db_data))
    print 'now historizing'
    dbo.insert_mysql(table,columns,db_data,placeholders)
    print 'web_lineups historized succesfully'
    return

def hist_FD_playerdata(Sport,Url,ContestID):
    #player_map = Ugen.excel_mapping('Player Map',1,2)
    FD_dict = ast.literal_eval(Uds.parse_html(Url,"FD.playerpicker.allPlayersFullData = ",";"))
    todays_date=time.strftime("%Y-%m-%d")
    db_data=[]
    for fd_key in FD_dict:
        player_name=FD_dict[fd_key][1]
        position=FD_dict[fd_key][0]
        FD_Salary=FD_dict[fd_key][5]
        FD_FPPG=FD_dict[fd_key][6]
        FD_GP=FD_dict[fd_key][7]
        db_data=[ContestID,Sport,todays_date,player_name,FD_Salary,FD_FPPG,FD_GP,position]
        columns='contestID,Sport,Date,Player,FD_Salary,FD_FPPG,FD_GP,Position'
        placeholders = ', '.join(['%s'] * len(db_data))
        table='hist_fanduel_data'
        #print 'now historizing %s contest#: %d player %s' % (Sport,ContestID,player_name)
        dbo.insert_mysql(table,columns,db_data,placeholders)
    return

def hist_FD_contest_salaries():
    todays_date=time.strftime("%Y-%m-%d")
    table='hist_fanduel_data'
    recordset=dbo.get_table_last_row(table,'Date')
    if str(recordset[0][1])==todays_date:
        print "hist_fd_contest_salares: salaries already historized in %s for today " % table
        time.sleep(5)   
        return
    s,session_id=fdo.get_fanduel_session()
    contest_dict=data_scrapping.get_FD_contests(s)
    sports_list=['mlb','nba','nhl','nfl'] #pick this option if you wanna historize all sports
    #sports_list=['mlb','nba']
    for sport in sports_list:
        sport_contest_dict=(x for x in contest_dict if x['sport']==sport)
        test_dict_case=(x for x in contest_dict if x['sport']==sport) #assign duplicate var to avoid list mutation
        if len(list(test_dict_case))>0: #test if there are contests for the sport
            i=1 #iterator
            historized_contests=[]
            ContestID=''
            for contest in sport_contest_dict: #loop through each for given sport
                Url='https://www.fanduel.com/e/Game'+contest['entryURL'][contest['entryURL'].find('Game\\')+5:]
                if i==1 and len(contest['startString'])<14 and contest['entryURL'].find('accept_public_challenge')==-1:
                    ContestID=contest['gameId'] #ContestID is a unique identifier for contests @unique time
                    print 'now historizing %s contest#: %d' % (sport,ContestID)
                    hist_FD_playerdata(sport.upper(),Url,ContestID)
                    print '%s contest#: %d historized succesfully' % (sport,ContestID)
                    historized_contests.append(ContestID)
                if contest['gameId']!=ContestID and contest['gameId'] not in historized_contests and len(contest['startString'])<14 and contest['entryURL'].find('accept_public_challenge')==-1: #check for contests at other times
                    ContestID=contest['gameId']
                    print 'now historizing %s contest#: %d' % (sport,ContestID)
                    hist_FD_playerdata(sport.upper(),Url,ContestID)
                    print '%s contest#: %d historized succesfully' % (sport,ContestID)
                    historized_contests.append(ContestID)
                i=i+1
    fdo.end_fanduel_session(s)
    return

hist_web_lineups()
hist_FD_contest_salaries()