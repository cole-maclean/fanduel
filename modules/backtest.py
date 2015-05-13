import os
import time
import datetime
import ast
import database_operations as dbo
import data_scrapping as ds
import data_scrapping_utils as Uds
import re
import requests
import FD_operations as fdo
import general_utils as Ugen
import sys
import TeamOdds
import json
import string
import pandas
import Sport
import numpy as np


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

    #Refactor 
    if TeamOdds.get_team_odds('MLB')[1].split()[1]!=todays_date.split('-')[2]:
        print "MLB team odds are not for today. check f'n or don't historize odds"
        time.sleep(5)
        mlb_odds=''
    else:
        mlb_odds=json.dumps(TeamOdds.get_team_odds('MLB')[0])
    if TeamOdds.get_team_odds('NHL')[1].split()[1]!=todays_date.split('-')[2]:
        print "NHL team odds are not for today. check f'n or don't historize odds"
        time.sleep(5)
        nhl_odds=''
    else:
        nhl_odds=json.dumps(TeamOdds.get_team_odds('NHL')[0])
    nba_odds=''    
    # if TeamOdds.get_team_odds('NBA')[1].split()[1]!=todays_date.split('-')[2]:
    #     print "NBA team odds are not for today. check f'n or don't historize odds"
    #     time.sleep(5)
    #     nba_odds=''
    # else:
    #     nba_odds=json.dumps(TeamOdds.get_team_odds('NBA')[0])

    dfn_nba=Cell('Backtest_Parameters','clDFNNBA').value
    rw_nba=Cell('Backtest_Parameters','clRWNBA').value
    rw_mlb=Cell('Backtest_Parameters','clRWMLB').value
    rw_nhl=Cell('Backtest_Parameters','clRWNHL').value
    rn_nba=Cell('Backtest_Parameters','clRNNBA').value
    rn_nhl=Cell('Backtest_Parameters','clRNNHL').value
    rn_mlb=Cell('Backtest_Parameters','clRNMLB').value  
    db_data=[todays_date,dfn_nba,rw_nba,rw_mlb,rw_nhl,mlb_odds,rn_nba,rn_nhl,rn_mlb,nba_odds,nhl_odds]
    columns='Date,DFN_NBA,RW_NBA,RW_MLB,RW_NHL,MLB_ODDS,RN_NBA,RN_NHL,RN_MLB,NBA_ODDS,NHL_ODDS'
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
    contest_dict=fdo.get_FD_contests(s)
    sports_list=['mlb','nba','nhl','nfl'] #pick this option if you wanna historize all sports
    #sports_list=['mlb','nba']
    for sport in sports_list:
        sport_contest_dict=(x for x in contest_dict if x['sport']==sport)
        test_dict_case=(x for x in contest_dict if x['sport']==sport) #assign duplicate var to avoid list mutation
        if len(list(test_dict_case))>0: #test if there are contests for the sport
            i=1 #iterator
            historized_contests=[]
            ContestID=''
            rw=1
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

def fanduel_lineup_points(playerlist,Date,backtest=False): #Specify backtest if not doing rotowire lineups
    if backtest:
        player_list=playerlist
    else:
        player_list=playerlist.split(', ')
    not_starting_dict={}
    player_dict={}
    player_map=Ugen.excel_mapping('Player Map',8,5)
    for player in player_list: #build dict of stats for lineup on given date
        if player in player_map and not backtest:
            player=player_map[player]
        sql="SELECT * FROM hist_player_data WHERE Sport = 'MLB' AND Player = "+ "'" +player+"'" + " AND Date = "+ "'" +Date+"'"
        player_data=dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
        
        if len(player_data)==0:
            print 'no db_data found for %s'%player
        for player_key,stat_dict in player_data.iteritems():
            if player_key.split("_")[1].split('-')[1]!='2': #Ian: right now for double headers only count points for first game
                player_dict[player_key]=stat_dict   
    FD_points=0
    for player,stats in player_dict.iteritems():
        if stats['Player_Type']== 'batter':
                player_points= (int(stats['Stat1'])*1 + int(stats['Stat2'])*2 + int(stats['Stat3'])*3 + int(stats['Stat4'])*4 + int(stats['Stat6'])*1 + int(stats['Stat10'])*1
                                             + int(stats['Stat11'])*1 + int(stats['Stat8'])*1 + int(stats['Stat13']) * 1 - ((int(stats['Stat7'])-int(stats['Stat5']))*.25))
        elif stats['Player_Type']== 'pitcher':
            player_points = (int(stats['Stat1'])*4 - int(stats['Stat7'])*1 + int(stats['Stat9'])*1 + float(stats['Stat4'])*1)
        else:
            print 'unknown positions for %s' %player
        FD_points=FD_points+player_points
    return FD_points

def rotowire_lineup_points():
    sql = "SELECT * FROM hist_lineup_optimizers"
    db_data= dbo.read_from_db(sql,["Date"],True)
    hist_points={}
    not_starting_list=[]
    for date,lineup in db_data.iteritems():
        mlb_lineup=lineup['RW_MLB']
        print "now calculating points for %s"%date
        lineup_points=fanduel_lineup_points(mlb_lineup,date)
        hist_points[date]=lineup_points
    return hist_points

def hist_model_lineups(date_list):
    MLB=Sport.MLB()
    rw=2
    while Cell("Backtest_Output",rw,1).value: #Ian: Don't overwrite existing values
        rw=rw+1
    hist_roster_dict={}
    for date in date_list:
        contest_list=hist_get_contest_ids(date)
        hist_roster_dict={}
        for contestID in contest_list:
            roster,player_universe_size=MLB.optimal_roster("https://www.fanduel.com/e/Game/12298?tableId=12594597&fromLobby=true",-10,date,contestID)
            hist_roster_dict[date+"_"+contestID]={}
            hist_roster_dict[date+"_"+contestID]['roster']=roster
            hist_roster_dict[date+"_"+contestID]['size']=player_universe_size
            Cell('Backtest_Output',rw,1).value=hist_roster_dict[date+"_"+contestID]['roster']
            Cell('Backtest_Output',rw,2).value=date
            Cell('Backtest_Output',rw,3).value=player_universe_size
            rw=rw+1
    return hist_roster_dict

def hist_model_points():
    rw=2
    while Cell("Backtest_Output",rw,4).value: #Ian: Don't overwrite existing values
        rw=rw+1
    points_list=[]
    while Cell('Backtest_Output',rw,1).value:
        roster_dict=ast.literal_eval(Cell('Backtest_Output',rw,1).value)
        roster=[player.split("_")[0] for player in roster_dict.keys()]
        points=fanduel_lineup_points(roster,str(Cell('Backtest_Output',rw,2).value)[:10],True)
        Cell("Backtest_Output",rw,4).value=points
        points_list.append(points)
        proj_points=0
        sum_conf=0
        for player_key in roster_dict:
            proj_points=proj_points+roster_dict[player_key]['projected_FD_points']
            sum_conf=sum_conf+roster_dict[player_key]['confidence']
        Cell('Backtest_Output',rw,5).value=proj_points
        Cell('Backtest_Output',rw,6).value=sum_conf
        rw=rw+1
    print points_list,np.mean(points_list)
    return np.mean(points_list)

def hist_get_contest_ids(date):
    contest_list=[]
    sql = "SELECT * FROM hist_fanduel_data Where Sport='MLB' And Date="+"'" +date+"'"
    FD_db_data= dbo.read_from_db(sql,['Player','Position','contestID'],True)
    for e in FD_db_data:
        if e.split("_")[2] not in contest_list:
            contest_list.append(e.split("_")[2])
    return contest_list


def run_hist_lineups():
    Cell('Backtest_Parameters','clRWNBA').value=''
    Cell('Backtest_Parameters','clRWMLB').value=''
    Cell('Backtest_Parameters','clRWNHL').value=''
    Cell('Backtest_Parameters','clDFNNBA').value=''
    Cell('Backtest_Parameters','clRNNBA').value=''
    Cell('Backtest_Parameters','clRNNHL').value=''
    Cell('Backtest_Parameters','clRNMLB').value= ''

    Cell('Backtest_Parameters','clRWNBA').value=ds.get_rw_optimal_lineups('NBA')
    Cell('Backtest_Parameters','clRWMLB').value=ds.get_rw_optimal_lineups('MLB')
    Cell('Backtest_Parameters','clRWNHL').value=ds.get_rw_optimal_lineups('NHL')
    Cell('Backtest_Parameters','clDFNNBA').value=ds.dfn_nba()
    Cell('Backtest_Parameters','clRNNBA').value=ds.roster_nerds('NBA')
    Cell('Backtest_Parameters','clRNNHL').value=ds.roster_nerds('NHL')
    Cell('Backtest_Parameters','clRNMLB').value=ds.roster_nerds('MLB')   
    print 'about to historize lineups'
    os.system('pause')
    hist_web_lineups()
    hist_FD_contest_salaries()
    return

#date_list=['2015-05-11','2015-05-10','2015-05-09','2015-05-08','2015-05-07','2015-05-06','2015-05-05','2015-05-04','2015-05-03','2015-05-02','2015-05-01' \
#            '2015-04-30','2015-04-29','2015-04-28','2015-04-27','2015-04-26','2015-04-25','2015-04-24','2015-04-23','2015-04-22','2015-04-21','2015-04-20']


# date_list=['2015-04-19','2015-04-18','2015-04-17']
# hist_model_lineups(date_list)


# print 'done'
#os.system('pause')
