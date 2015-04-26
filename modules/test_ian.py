import database_operations as dbo
import time
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import data_scrapping
import general_utils as Ugen
from selenium import webdriver
import string
#player_list='Adam Wainwright, Derek Norris, Edwin Encarnacion, Brian Dozier, Luis Valbuena, Marcus Semien, Kole Calhoun, George Springer, Mookie Betts'
#Date='20150419'
#sql=

def fanduel_lineup_points(playerlist,Date): #Need to incorporate cole's sport class, already has a similar func
	player_list=playerlist.split(', ')
	#build dict of stats for lineup on given date
	player_dict={}
	for player in player_list:
		sql="SELECT * FROM hist_player_data WHERE Sport = 'MLB' AND Player = "+ "'" +player+"'" + " AND Date = "+ "'" +Date+"'"
		player_data=dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
		#print if a certain player was not found!!
		for player_key,stat_dict in player_data.iteritems():
			player_dict[player]=stat_dict
	FD_points=0
	for player,stats in player_dict.iteritems():
		# print player
		# os.system('pause')
		outs=0
		if (int(stats['Stat5'])-int(stats['Stat7']))>0:
				outs=int(stats['Stat5'])-int(stats['Stat7'])
		if stats['Player_Type']== 'batter':
				FD_points= (int(stats['Stat1'])*1 + int(stats['Stat2'])*2 + int(stats['Stat3'])*3 + int(stats['Stat4'])*4 + int(stats['Stat6'])*1 + int(stats['Stat10'])*1
											 + int(stats['Stat11'])*1 + int(stats['Stat8'])*1 + int(stats['Stat13']) * 1 - ((int(stats['Stat5'])-int(stats['Stat7']))*.25))+FD_points
		elif stats['Player_Type']== 'pitcher':
			FD_points = (int(stats['Stat1'])*4 - int(stats['Stat7'])*1 + int(stats['Stat9'])*1 + float(stats['Stat4'])*1)+FD_points
		else:
			print 'unknown positions for %s' %player
	#Cell('Output',1,1).value=player_dict
	return FD_points

# points=fanduel_lineup_points(player_list,Date)
# print points

def test_selenium():
	#driver = webdriver.Chrome() Ian: use this for debugging
	driver = webdriver.PhantomJS()
	driver.get("http://www.rotowire.com/daily/mlb/optimizer.htm")
	button=driver.find_element_by_css_selector('.offset2.btn.btn-primary.btn-large.optimize-mlblineup')
	time.sleep(5)
	button.click()
	time.sleep(5)
	html=driver.page_source 
	driver.close()
	soup = BeautifulSoup(html)
	results=soup.find("tbody",{"class":"lineupopt-lineup"}).get_text()
	return html

a=data_scrapping.mlb_starting_lineups('2015-04-09')
Cell('Output',1,1).value=a
time.sleep(5)




#HIDING WEB BROWSER WINDOW
#http://stackoverflow.com/questions/1418082/is-it-possible-to-hide-the-browser-in-selenium-rc


# sql = "SELECT * FROM hist_player_data WHERE Sport = 'MLB'"
# db_data= dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
# xml_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in xml_team_list:
#         xml_team_list.append(Player)


# sql = "SELECT * FROM hist_fanduel_data WHERE Sport = 'MLB'"
# db_data = dbo.read_from_db(sql,["Date","Player","Position","contestID"],True)

# fanduel_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in fanduel_team_list:
#         fanduel_team_list.append(Player)

# test_player=Cell(1,10).value

# if test_player.encode('latin_1') in xml_team_list:
#     print 'player found in list'
# else:
#     print 'player not found in list'
# os.system('pause')

# i=2
# for e in fanduel_team_list:
#     if e not in xml_team_list:
#         split_name=e.split(' ',1)
#         Cell('Output',i,1).value=split_name[0]
#         Cell('Output',i,2).value=split_name[1]
#         i=i+1

# i=2
# for e in xml_team_list:
#     if e not in fanduel_team_list:
#         split_name=e.decode('latin_1').split(' ',1)
#         Cell('Output',i,3).value=split_name[0]
#         Cell('Output',i,4).value=split_name[1]
#         i=i+1


#Remove duplicate rows SQL statement
#ALTER IGNORE TABLE hist_backtest_data ADD UNIQUE KEY idx1(date);
#Append column to table
#ALTER TABLE hist_fanduel_data ADD contestID TEXT 
#Delete single row by ID
#DELETE FROM hist_lineup_optimizers WHERE DataID=8 LIMIT 1