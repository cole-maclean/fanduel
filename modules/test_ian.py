import database_operations as dbo
import time
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import data_scrapping as ds
import general_utils as Ugen
from selenium import webdriver
import string
import pandas

def fanduel_lineup_points(playerlist,Date): #Need to incorporate cole's sport class, already has a similar func. Needs refactoring.
	player_list=playerlist.split(', ')
	not_starting_dict={}
	player_dict={}
	player_map=Ugen.excel_mapping('Player Map',8,5)
	for player in player_list:#build dict of stats for lineup on given date
		if player in player_map:
			player=player_map[player]
		sql="SELECT * FROM hist_player_data WHERE Sport = 'MLB' AND Player = "+ "'" +player+"'" + " AND Date = "+ "'" +Date+"'"
		player_data=dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
		if len(player_data)==0:
			print 'no db_data found for %s'%player
			not_starting_dict[player+' '+Date]=0
		for player_key,stat_dict in player_data.iteritems():
			player_dict[player]=stat_dict	
	FD_points=0
	player_map=Ugen.excel_mapping('Player Map',5,7)
	for player,stats in player_dict.iteritems():
		team_dict,lineup_dict=ds.mlb_starting_lineups(Date)
		if stats['Player_Type']== 'batter':
				player_points= (int(stats['Stat1'])*1 + int(stats['Stat2'])*2 + int(stats['Stat3'])*3 + int(stats['Stat4'])*4 + int(stats['Stat6'])*1 + int(stats['Stat10'])*1
											 + int(stats['Stat11'])*1 + int(stats['Stat8'])*1 + int(stats['Stat13']) * 1 - ((int(stats['Stat5'])-int(stats['Stat7']))*.25))
		elif stats['Player_Type']== 'pitcher':
			player_points = (int(stats['Stat1'])*4 - int(stats['Stat7'])*1 + int(stats['Stat9'])*1 + float(stats['Stat4'])*1)
		else:
			print 'unknown positions for %s' %player
		FD_points=FD_points+player_points

		#All this below is to test if player wasn't in starting lineups that day, can be removed in future
		if player in player_map:
			mapped_name=player_map[player]
		else:
			mapped_name=player
		if mapped_name not in lineup_dict:
			print "%s was not found in starting lineups dict"%mapped_name
			not_starting_dict[mapped_name+' '+Date]=player_points
	return FD_points,not_starting_dict

def rotowire_lineup_points():
	sql = "SELECT * FROM hist_lineup_optimizers"
	db_data= dbo.read_from_db(sql,["Date"],True)
	hist_points={}
	not_starting_list=[]
	for date,lineup in db_data.iteritems():
		mlb_lineup=lineup['RW_MLB']
		print "now calculating points for %s"%date
		lineup_points,not_starting=fanduel_lineup_points(mlb_lineup,date)
		hist_points[date]=lineup_points
		not_starting_list.append(not_starting)
	return hist_points,not_starting_list

points,not_starting=rotowire_lineup_points()

i=1
for e in not_starting:
	Cell('Output',i,1).value=e
	i=i+1
os.system('pause')
#PLAYER MAPPING

# sql = "SELECT * FROM hist_lineup_optimizers"
# db_data= dbo.read_from_db(sql,["Date"],True)

# rw_player_list=[]
# for date,lineup in db_data.iteritems():
# 	player_names=lineup['RW_MLB'].split(', ')
# 	for e in player_names:
# 		if e not in rw_player_list:
# 			rw_player_list.append(e)

# sql = "SELECT * FROM hist_player_data WHERE Sport = 'MLB'"
# db_data= dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
# xml_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in xml_team_list:
#         xml_team_list.append(Player)

# i=2
# for e in rw_player_list:
# 	if e not in xml_team_list:
# 		Cell('Output',i,1).value=e
# 		i=i+1

# i=2
# for e in xml_team_list:
# 	if e not in rw_player_list:
# 		Cell('Output',i,3).value=e
# 		i=i+1

# sql = "SELECT * FROM hist_fanduel_data WHERE Sport = 'MLB'"
# db_data = dbo.read_from_db(sql,["Date","Player","Position","contestID"],True)

# fanduel_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in fanduel_team_list:
#         fanduel_team_list.append(Player)


# start_date='2015-04-01'
# end_date='2015-05-02'
# event_dates = [d.strftime('%Y-%m-%d') for d in pandas.date_range(start_date,end_date)]
# lineups_name_list=[]
# for event_date in event_dates:
# 	print 'now loading %s' % event_date
# 	team_dict,player_dict=ds.mlb_starting_lineups(event_date)
# 	for player in player_dict:
# 		if player not in lineups_name_list:
# 			lineups_name_list.append(player)

# # player_map=Ugen.excel_mapping("Player Map",6,5)


# i=2
# for e in lineups_name_list:
# 	if e not in fanduel_team_list:
# 		Cell('Output',i,1).value=e
# 		i=i+1

# i=2
# for e in fanduel_team_list:
# 	if e not in lineups_name_list:
# 		Cell('Output',i,3).value=e
# 		i=i+1



#Remove duplicate rows SQL statement
#ALTER IGNORE TABLE hist_backtest_data ADD UNIQUE KEY idx1(date);
#Append column to table
#ALTER TABLE hist_fanduel_data ADD contestID TEXT 
#Delete single row by ID
#DELETE FROM hist_lineup_optimizers WHERE DataID=8 LIMIT 1

#LOAD CSV FILE INTO DB
# LOAD DATA LOCAL INFILE 'C:/Users/Ian Whitestone/Documents/Python Projects/Fanduel-master/fanduel/stadium_data.csv' 
# INTO TABLE stadium_data
# FIELDS TERMINATED BY ',' 
# ENCLOSED BY '"'
# LINES TERMINATED BY '\n'
# IGNORE 1 ROWS;


# Delete FROM autotrader.hist_player_data WHERE Date='2014-04-14';
# Delete FROM autotrader.event_data WHERE event_id='20140414-washington-nationals-at-miami-marlins';
# Delete FROM autotrader.event_data WHERE event_id='20140414-tampa-bay-rays-at-baltimore-orioles';
# Delete FROM autotrader.event_data WHERE event_id='20140414-atlanta-braves-at-philadelphia-phillies';