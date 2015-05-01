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


player_list='Adam Wainwright, Derek Norris, Edwin Encarnacion, Brian Dozier, Luis Valbuena, Marcus Semien, Kole Calhoun, George Springer, Mookie Betts'
Date='20150419'
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

def get_rw_optimal_lineups(sport): #Ian: Need to remove time.sleep's and change to loops till pages are loaded
	driver = webdriver.Chrome() #Ian: use this for debugging
	#driver = webdriver.PhantomJS()
	driver.get("http://www.rotowire.com/daily/"+sport+"/optimizer.htm")
	time.sleep(5)
	html=driver.page_source 
	soup = BeautifulSoup(html)
	results=soup.find("tbody",{"id":"players"})
	for row in results.findAll("tr",{"class":"playerSet"}): 
		player_name=row.find("td",{"class":"firstleft lineupopt-name"}).get_text()
		if len(player_name.split(', ')[1].split())>1:
			data_value=row.find("td",{"class":"lineupopt-exclude"})['data-value']
			driver.find_element_by_css_selector(".lineupopt-exclude[data-value="+"'"+str(data_value)+"']").click()
	button=driver.find_element_by_css_selector('.offset2.btn.btn-primary.btn-large.optimize-'+sport.lower()+'lineup')
	button.click()
	time.sleep(20)
	html=driver.page_source 
	soup = BeautifulSoup(html)
	results=soup.find("tbody",{"class":"lineupopt-lineup"})
	optimal_lineup=[]
	if sport=='NBA' or sport=='NHL':
		for row in results.findAll("td",{"style":"text-align:left;padding-left:3px;"}):
			optimal_lineup.append(row.get_text())
	elif sport=='MLB':
		for row in results.findAll("td",{"style":"text-align:left;"}):
			optimal_lineup.append(row.get_text())
	driver.close()
	lineup_string=''
	for e in optimal_lineup:
		first_name=e.split(', ')[1]
		last_name=e.split(', ')[0]
		lineup_string=lineup_string+first_name+' '+last_name+', '
	return lineup_string.rsplit(', ',1)[0]

def dfn_nba():
	driver = webdriver.Chrome() #Ian: use this for debugging
	#driver = webdriver.PhantomJS()
	driver.get("https://dailyfantasynerd.com/optimizer/fanduel/nba")
	time.sleep(5)
	driver.find_element_by_id('input-username').send_keys('iwhitest')
	driver.find_element_by_id('input-password').send_keys('clover2010')
	#driver.find_element_by_css_selector(".text[id='input-username']")
	driver.find_element_by_css_selector('.btn.btn-success').click()
	time.sleep(10)
	driver.find_element_by_css_selector('.btn.btn-info.generate').click()
	time.sleep(5)
	html=driver.page_source 
	soup = BeautifulSoup(html)
	lineup=[]
	for player in soup.findAll('td',{"class":"pl-col playerName"}):
		if len(lineup)<=8:
			lineup.append(player.get_text())
	lineup_string=''
	for e in lineup:
		lineup_string=lineup_string+e+', '
	driver.close()
	return lineup_string.rsplit(', ',1)[0]


Cell('Backtest_Parameters','clRWNBA').value=get_rw_optimal_lineups('NBA')
Cell('Backtest_Parameters','clRWMLB').value=get_rw_optimal_lineups('MLB')
Cell('Backtest_Parameters','clRWNHL').value=get_rw_optimal_lineups('NHL')
Cell('Backtest_Parameters','clDFNNBA').value=dfn_nba()



#PLAYER MAPPING

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

# # print xml_team_list

# player_map=Ugen.excel_mapping("Player Map",6,5)

# for test_player in player_map:
# 	if test_player.encode('latin_1') in xml_team_list:
# 	    print 'player found in list'
# 	else:
# 	    print '%s player not found in list' % test_player

#os.system('pause')

# i=2
# for e in xml_team_list:
# 	if e.decode('latin_1') not in player_map and e.decode('latin_1') not in fanduel_team_list:
# 		Cell('Sheet1',i,1).value=e.decode('latin_1')
# 		i=i+1

# i=2
# for e in fanduel_team_list:
#     if e not in xml_team_list and e not in player_map:
#         split_name=e.split(' ',1)
#         Cell('Sheet1',i,1).value=split_name[0]
#         Cell('Sheet1',i,2).value=split_name[1]
#         i=i+1

# i=2
# for e in xml_team_list:
#     if e not in fanduel_team_list:
#         split_name=e.decode('latin_1').split(' ',1)
#         Cell('Output',i,3).value=split_name[0]
#         Cell('Output',i,4).value=split_name[1]
#         i=i+1

# new_player_list=[]
# not_found_list=[]
# for e in xml_team_list:
# 	if e.decode('latin_1') in player_map:
# 		new_player_list.append(player_map[e.decode('latin_1')])
# 	elif e.decode('latin_1') in fanduel_team_list:
# 		new_player_list.append(e.decode('latin_1'))
# 	else:
# 		not_found_list.append(e.decode('latin_1'))

# Cell('Sheet1',1,1).value=new_player_list
# Cell('Sheet1',2,1).value=not_found

# trial_list=[]
# for e in xml_team_list:
# 	trial_list.append(e.decode('latin_1'))

# Cell('Sheet1',3,1).value=trial_list

#Remove duplicate rows SQL statement
#ALTER IGNORE TABLE hist_backtest_data ADD UNIQUE KEY idx1(date);
#Append column to table
#ALTER TABLE hist_fanduel_data ADD contestID TEXT 
#Delete single row by ID
#DELETE FROM hist_lineup_optimizers WHERE DataID=8 LIMIT 1