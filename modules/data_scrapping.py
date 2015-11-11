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
import data_scrapping_utils as Uds
import re
import requests
import FD_operations as fdo
import general_utils as Ugen
import subprocess
import string
import weather
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import os

def get_NHL_gamedata(sGameSeason,sGameID):
	game_stats_Url = 'http://live.nhle.com/GameData/' + sGameSeason + '/' + sGameID + '/gc/gcbx.jsonp'
	game_stats_data = Uds.get_JSON_data(game_stats_Url, ['GCBX.load(',')'])
	if game_stats_data == "URL not found":
		Cell("Parameters",'clLastGameDataID').value = int(sGameID[-4:]) -1
		return "URL not found"
	roster_data_Url = 'http://live.nhle.com/GameData/' + sGameSeason + '/' + sGameID + '/gc/gcsb.jsonp'
	roster_data = Uds.get_JSON_data(roster_data_Url, ['GCSB.load(',')'])
	HomeTeam = roster_data['h']['ab']
	AwayTeam = roster_data['a']['ab']
	print HomeTeam + " " + write_nhl_game_data(game_stats_data['rosters']['home'],HomeTeam,sGameID)
	print AwayTeam + " " + write_nhl_game_data(game_stats_data['rosters']['away'],AwayTeam,sGameID)

def get_NHL_team_players(team):
	roster_data_url = 'http://nhlwc.cdnak.neulion.com/fs1/nhl/league/teamroster/' + team + '/iphone/clubroster.json'
	roster_data = Uds.get_JSON_data(roster_data_url)
	team_player_num_lookup = {}
	for position in roster_data.values()[1:]:
		for player in position:
			try:
				team_player_num_lookup[player['number']] = player['name']
			except KeyError:
				print player['name'] + " num lookup failure"
	return team_player_num_lookup

def get_starting_goalies():
	goalie_list = []
	response = urllib2.urlopen('http://www2.dailyfaceoff.com/starting-goalies/')
	shtml = response.read()
	soup = BeautifulSoup(shtml)
	for goalie_data in soup.findAll("div", { "class":"goalie home" }):
		goalie_table = goalie_data.find('dt')
		goalie_heading = goalie_data.find('h5')
		if goalie_table and goalie_heading:
			if goalie_table.get_text() == 'Confirmed':
				goalie = goalie_heading.get_text()
				goalie_list.append(goalie)
	for goalie_data in soup.findAll("div", { "class":"goalie away" }):
		goalie_table = goalie_data.find('dt')
		goalie_heading = goalie_data.find('h5')
		if goalie_table and goalie_heading:
			if goalie_table.get_text() == 'Confirmed':
				goalie = goalie_heading.get_text()
				goalie_list.append(goalie)
	return goalie_list

def get_contest_userwins(user_list):
	DB_parameters=Ugen.ConfigSectionMap('local text')
	with open(DB_parameters['userwinscache'],"r") as myfile: #Ian: removed hard coded reference to Cole's path
		data = myfile.read()
	user_wins_cache = ast.literal_eval(data)
	user_wins_dict = {}
	user_wins_array = {'Total':[],'NFL':[],'MLB':[],'NBA':[],'NHL':[],'CBB':[],'CFB':[]}
	for user_data in user_list:
		username = user_data['username']
		if username in user_wins_cache.keys():
			user_wins_dict[username] = user_wins_cache[username]
		else:
			user_url = 'https://www.fanduel.com/users/'+username
			response = urllib2.urlopen(user_url)
			shtml = response.read()
			soup = BeautifulSoup(shtml)
			table = soup.find('table', {'class': 'condensed'})
			td = table.find('th').findNext('td')
			user_wins_cache[username] = {}
			for th in table.findAll('th'):
				try:
					user_wins_array[th.text].append(int(td.text))
					user_wins_cache[username][th.text] = int(td.text)
					td = td.findNext('td')
				except ValueError:
					user_wins_array[th.text].append(0)
					user_wins_cache[username][th.text] = 0
					td = td.findNext('td')					
				except KeyError:
					pass
			user_wins_dict[username] = user_wins_cache[username]	
			time.sleep(1)
	with open(DB_parameters['userwinscache'],"w") as myfile: #Ian: removed hard coded reference to Cole's path
		myfile.write(str(user_wins_cache))
	return user_wins_dict
def get_FD_playerlist(): #Cole: move this to FD operations
 	FD_list = ast.literal_eval(Uds.parse_html(Cell('Parameters','cLineUpURL').value,"FD.playerpicker.allPlayersFullData = ",";"))
 	return FD_list
def build_lineup_dict():
	rw = 2
	if Cell('Parameters','clLineupsCache').value == None:
		team_map = Ugen.excel_mapping('Team Map',1,2)
		team_lineups_dict = {}
		for team in team_map.keys():
			roster_url = 'http://www2.dailyfaceoff.com/teams/lines/' + str(team_map[team]) +'/'
			response = urllib2.urlopen(roster_url)
			shtml = response.read()
			soup = BeautifulSoup(shtml)
			lineups = soup.findAll('td')
			lines = []
			line = []
			line_id = 1
			for lineup in lineups:
				if lineup.get('id') == 'G1':
					lines.append(line)
					break
				elif lineup.get('id')[-1] == line_id:
 					try:
 						line.append(str(lineup.get_text()).strip())
 					except:
 						print lineup.get_text()
				else:
					if line:
						lines.append(line)
					line = []
 					try:
 						line.append(str(lineup.get_text()).strip())
 					except:
 						print lineup.get_text()
					line_id = lineup.get('id')[-1]			
			team_lineups_dict[team] = lines
		Cell('Parameters','clLineupsCache').value = team_lineups_dict
	else:
		team_lineups_dict = ast.literal_eval(Cell('Parameters','clLineupsCache').value)
	return team_lineups_dict
def get_live_contest_ids():
	s, session_id = fdo.get_fanduel_session()
	r = s.get('https://www.fanduel.com/mycontests/162491/live?start=0&number=10000')
	live_contest_dict = json.loads(r.text)
	for contest in live_contest_dict['seats']:
		dbo.write_to_db('FD_table_contests','table_id,contest_id',[str(contest[2].split(r'/')[2]),str(contest[0])])
def get_contest_utlity(avg_top_wins,time_remaining,wins_data,bin_size):
	future_utility = 0.0007*time_remaining #predicting future utility, currently assumes 0.6 at T-600mins and 0.0 at T-0 min. Needs more rigourous stats
	try:
		contest_utility = wins_data[Ugen.bin_mapping(avg_top_wins,bin_size)][-1]
		#if avg_top_wins <=500:
			#contest_utility = 1#tempory contest utilities until hist performance dataset builts
		#else:
			#contest_utility = 0
	except KeyError:
		print 'wins data bin for ' + str(avg_top_wins) + ' does not exist'
		contest_utility = 0
	return contest_utility,future_utility

def mlb_starting_lineups(date=time.strftime("%Y-%m-%d")): #take date as string 'YYYY-MM-DD'.
	print date
	url='http://www.baseballpress.com/lineups/'+date
	content=urllib2.urlopen(url).read()
	soup=BeautifulSoup(content,"html.parser") #Ian: added this html.parser option based on suggestion from OSX terminal...may not be necessary on windows??
	team_map=Ugen.mlb_map(6,4)
	player_map=Ugen.mlb_map(2,0)
	team_list,pitcher_list,lineups_list,gametime_list,weather_list,pitcher_arm_list,player_arm_list=([] for i in range(7))
	teamid_dict={}
	playerid_dict={}

	gametime_list=[event_date.text for event_date in soup.findAll("div",{"class":"game-time"})]
	gametime_list=[x for pair in zip(gametime_list,gametime_list) for x in pair] #duplicate elements in list
	for forecast in soup.findAll("a",{"target":"forecast"}):
		forecast_string=filter(lambda x: x in string.printable, forecast.text).split('Forecast: ')[1].split(' PoP')[0].replace(" ","-").replace("--","-").replace('F','degF')
		if len(forecast_string.split('-'))==4:
			forecast_string=forecast_string.split('-')[0]+'-'+forecast_string.split('-')[1]+' '+forecast_string.split('-')[2]+'-'+forecast_string.split('-')[3]
		weather_list.append(forecast_string)
		weather_list.append(forecast_string)

	for team in soup.findAll("div",{"class":"team-data"}):
		team_name=team.find("div",{"class":"team-name"}).get_text()
		pitcher_name=team.find("a",{"class":"player-link"}).get_text()
		pitcher_arm=team.find('div',{"class":"text"}).get_text().split('(')[1].split(')')[0]
		if team_name in team_map: #Ian: Check if team name has been listed
			team_name=team_map[team_name]
		if pitcher_name in player_map:
			pitcher_name=player_map[pitcher_name]
		team_list.append(team_name)
		pitcher_list.append(pitcher_name.replace("'","")+'_'+'pitcher')
		pitcher_arm_list.append(pitcher_arm)
	
	for table in soup.findAll("div",{"class":"cssDialog clearfix"}):
		table_string=table.get_text()
		home_lineup,away_lineup,home_lineup_arms,away_lineup_arms=([] for i in range(4))  
		if table_string.count("9. ")==2: #Ian: rethink; checks that both teams lineups have been listed. What if only one has been.. 
			for j in range(1,10):
				name_list_raw=table_string[table_string.find(str(j)+". ")+3:].split(" (")
				player=name_list_raw[0]
				home_lineup_arms.append(name_list_raw[1].split(')')[0])
				if player in player_map:
					player=player_map[player]
				home_lineup.append(player.replace("'","")+'_'+'batter')
				name_list_raw=table_string[table_string.find((str(j)+". "),table_string.find(str(j)+". ")+3)+3:].split(" (")
				player=name_list_raw[0]
				away_lineup_arms.append(name_list_raw[1].split(')')[0])
				if player in player_map:
					player=player_map[player]
				away_lineup.append(player.replace("'","")+'_'+'batter')
			lineups_list.append(home_lineup)
			lineups_list.append(away_lineup)
			player_arm_list.append(home_lineup_arms)
			player_arm_list.append(away_lineup_arms)
		else:
			lineups_list.append(['no home_lineup listed'])
			lineups_list.append(['no away_lineup listed'])
			player_arm_list.append(['no hitting style listed'])
			player_arm_list.append(['no hitting style listed'])


	opponent_dict={team_list[i]:{'home_team':team_list[i],'opponent':team_list[i-1]} for i in range(0,len(team_list)) if i%2 !=0}
	opponent_dict.update({team_list[i]:{'home_team':team_list[i+1],'opponent':team_list[i+1]} for i in range(0,len(team_list)) if team_list[i] not in opponent_dict})
	
	teamid_dict={}
	for i in range(0,len(lineups_list)):
		batting_order=range(1,len(lineups_list[i])+1)
		lineups_list[i].append(pitcher_list[i])
		player_arm_list[i].append(pitcher_arm_list[i])
		player_arm_dict={player:{'arm':arm,'batting_order':order} for player,arm,order in zip(lineups_list[i],player_arm_list[i],batting_order)}
		teamid_dict.update({team_list[i]:{'start_time':gametime_list[i],'date':date,'lineup':player_arm_dict,'home_teamid':opponent_dict[team_list[i]]['home_team'], \
							'opponent':opponent_dict[team_list[i]]['opponent'],'weather_forecast':weather_list[i]}})
	
	playerid_dict={player:{'start_time':teamid_dict[team_id]['start_time'],'weather_forecast':teamid_dict[team_id]['weather_forecast'], \
					'teamid':team_id,'opposing_lineup': teamid_dict[teamid_dict[team_id]['opponent']]['lineup'],'arm':teamid_dict[team_id]['lineup'][player]['arm'], \
					'batting_order':teamid_dict[team_id]['lineup'][player]['batting_order'],'home_teamid':teamid_dict[team_id]['home_teamid']} \
					 for team_id in teamid_dict for player in teamid_dict[team_id]['lineup']}

	return teamid_dict,playerid_dict

def get_rw_optimal_lineups(sport): #Ian: Need to remove time.sleep's and change to loops till pages are loaded
	driver = webdriver.Chrome() #Ian: use this for debugging
	#driver = webdriver.PhantomJS()
	driver.get("http://www.rotowire.com/daily/"+sport+"/optimizer.htm")
	time.sleep(5)
	html=driver.page_source 
	soup = BeautifulSoup(html)
	#Dont need this stuff below anymore since you cant exclude players.
	#results=soup.find("tbody",{"id":"players"})
	# for row in results.findAll("tr",{"class":"playerSet"}):
		# player_name=row.find("td",{"class":"firstleft lineupopt-name"}).get_text()
		# if len(player_name.split(', ')[1].split())>1:
		# 	data_value=row.find("td",{"class":"lineupopt-exclude"})['data-value']
		# 	driver.find_element_by_css_selector(".lineupopt-exclude[data-value="+"'"+str(data_value)+"']").click()
	button=driver.find_element_by_css_selector('.btn.btn-primaryflat.btn-large.optimize-'+sport.lower()+'lineup')
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

def dfn(sport):
	driver = webdriver.Chrome() #Ian: use this for debugging
	login = Ugen.ConfigSectionMap('dailyfantasynerd')
	#driver = webdriver.PhantomJS()
	driver.get("https://dailyfantasynerd.com/optimizer/fanduel/"+sport.lower())
	time.sleep(5)
	driver.find_element_by_id('input-username').send_keys(login['username'])
	driver.find_element_by_id('input-password').send_keys(login['password'])
	#driver.find_element_by_css_selector(".text[id='input-username']")
	driver.find_element_by_css_selector('.btn.btn-success').click()
	time.sleep(15)
	driver.find_element_by_css_selector('.btn.btn-info.generate').click()
	time.sleep(10)
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

def roster_nerds(sport):
	url='http://'+sport.lower()+'.rosternerds.com/'
	driver = webdriver.Chrome()
	driver.get(url)
	time.sleep(5)
	html=driver.page_source
	driver.close() 
	# html= urllib2.urlopen(url).read()
	soup = BeautifulSoup(html)
	table=soup.find("table",{"class":"players"})
	lineup=[]
	for row in table.findAll("tr",{"class":"odd"}):
		lineup.append(row.find("td",{"class":"player-cell"}).get_text())
	for row in table.findAll("tr",{"class":"even"}):
		lineup.append(row.find("td",{"class":"player-cell"}).get_text())
	lineup_string=''
	for e in lineup:
		lineup_string=lineup_string+e+', '
	return lineup_string.rsplit(', ',1)[0]



# a,b=mlb_starting_lineups('2015-10-04')
# print a
# os.system('pause')