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
import Sport
import numpy as np
import backtest
import TeamOdds
import datetime as dt

#backtest.hist_model_points()
#backtest.run_hist_lineups()

backtest.hist_model_lineups(backtest_dates)

# backtest.hist_FD_contest_salaries()

# MLB=Sport.MLB()
# MLB.get_daily_game_data('20150420','20150524',True)




# points,not_starting=rotowire_lineup_points()
#print fanduel_lineup_points('Madison Bumgarner, Marcell Ozuna, Marcus Semien, Giancarlo Stanton, Coco Crisp, Robinson Cano, Albert Pujols, Josh Phegley, Kyle Seager','20150509')[0]

# i=1
# for e in not_starting:
# 	Cell('Output',i,1).value=e
# 	i=i+1
# os.system('pause')

# sql = "SELECT * FROM hist_fanduel_data Where Date='2015-05-09' And Sport='MLB'"
# db_data= dbo.read_from_db(sql,['Player','Position','contestID'],True)

# for player_key,data in db_data.iteritems():
# 	print player_key,data['FD_Salary']

# time.sleep(20)



#PLAYER MAPPING



# player_map1 = Ugen.excel_mapping("Player Map",6,5) #XML to FD
# player_map2 = Ugen.excel_mapping("Player Map",7,5) #MLB Lineups to FD

# sql = "SELECT * FROM hist_lineup_optimizers"
# db_data= dbo.read_from_db(sql,["Date"],True)

# rw_player_list=[]
# for date,lineup in db_data.iteritems():
# 	player_names=lineup['RW_MLB'].split(', ')
# 	for e in player_names:
# 		if e not in rw_player_list:
# 			rw_player_list.append(e)

#XML STATs Player names
# sql = "SELECT * FROM hist_player_data WHERE Sport = 'MLB' LIMIT 0,18446744073709551615"
# db_data= dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
# xml_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in xml_team_list:
#         xml_team_list.append(Player)

# xml_team_list=[]

# MLB=Sport.MLB()
# xml_team_list=MLB.get_daily_game_data('20150502','20150820',True) 

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

# sql = "SELECT * FROM hist_fanduel_data WHERE Sport = 'MLB' LIMIT 0,18446744073709551615"
# db_data = dbo.read_from_db(sql,["Date","Player","Position","contestID"],True)

# fanduel_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in fanduel_team_list:
#         fanduel_team_list.append(Player)


# start_date='2015-05-02'
# end_date='2015-08-20'
# event_dates = [d.strftime('%Y-%m-%d') for d in pandas.date_range(start_date,end_date)]
# lineups_name_list=[]
# for event_date in event_dates:
# 	print 'now loading %s' % event_date
# 	team_dict,player_dict=ds.mlb_starting_lineups(event_date)
# 	for player in player_dict:
# 		player_name=player.split("_")[0]
# 		if player_name not in lineups_name_list:
# 			lineups_name_list.append(player_name)

# # player_map=Ugen.excel_mapping("Player Map",6,5)

# print lineups_name_list

# i=2
# for e in lineups_name_list:
# 	if e not in fanduel_team_list and e not in player_map2:
# 		Cell('Output',i,1).value=e
# 		i=i+1
# i=2
# for e in fanduel_team_list:
# 	if e not in lineups_name_list and e not in player_map2.itervalues():
# 		Cell('Output',i,2).value=e
# 		i=i+1


# i=2
# for e in xml_team_list:
# 	if e not in fanduel_team_list and e not in player_map1:
# 		# if "Colom" in e:
# 		# 	print e
# 		# 	print str(e)
# 		# 	#print e.decode("latin-1")
# 		# 	os.system('pause')
# 		# print i
# 		Cell('Output',i,3).value=e
# 		i=i+1
# i=2
# for e in fanduel_team_list:
# 	if e not in xml_team_list and e not in player_map1.itervalues():
# 		Cell('Output',i,4).value=e
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


# Delete FROM autotrader.hist_player_data WHERE Date='2015-07-11';
# Delete FROM autotrader.event_data WHERE event_id LIKE '%20150711%';

# Delete FROM autotrader.event_data WHERE event_id='20140414-washington-nationals-at-miami-marlins';
# Delete FROM autotrader.event_data WHERE event_id='20140414-tampa-bay-rays-at-baltimore-orioles';
# Delete FROM autotrader.event_data WHERE event_id='20140414-atlanta-braves-at-philadelphia-phillies';