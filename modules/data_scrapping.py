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

def get_contest_userwins(contest):
	DB_parameters=Ugen.ConfigSectionMap('local text')
	with open(DB_parameters['userwinscache'],"r") as myfile: #Ian: removed hard coded reference to Cole's path
		data = myfile.read()
	user_wins_cache = ast.literal_eval(data)
	entry_url = 'https://www.fanduel.com/pg/Lobby/showTableEntriesJSON/' + contest['uniqueId'] + '/0/10000'
	response = urllib2.urlopen(entry_url)
	shtml = response.read()
	entry_dict = ast.literal_eval(shtml)
	user_wins_array = {'Total':[],'NFL':[],'MLB':[],'NBA':[],'NHL':[],'CBB':[],'CFB':[]}
	for entry_data in entry_dict['entries']:
		user_html = entry_data['userHTML']
		intStart = user_html.find("alt=''>")
		intEnd = user_html.find('<',intStart)
		username = user_html[intStart:intEnd].replace("alt=''>","")
		if username in user_wins_cache.keys():
			for sport,wins in user_wins_cache[username].iteritems():
				user_wins_array[sport].append(wins)
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
			time.sleep(1)
	with open('C:/Users/Cole/Desktop/Fanduel/fanduel/userwinscache.txt',"w") as myfile:
		myfile.write(str(user_wins_cache))
	return user_wins_array
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

def mlb_starting_lineups(date=time.strftime("%Y-%m-%d")): #take date as string 'YYYY-MM-DD'. Needs refactoring.
	url='http://www.baseballpress.com/lineups/'+date
	content= urllib2.urlopen(url).read()
	soup = BeautifulSoup(content)
	team_map = Ugen.excel_mapping("Team Map",8,6)
	team_list,pitcher_list,lineups_list,gametime_list,weather_list=([] for i in range(5))
	teamid_dict={}
	playerid_dict={}
	for event_date in soup.findAll("div",{"class":"game-time"}):
		gametime_list.append(event_date.text)
	for forecast in soup.findAll("a",{"target":"forecast"}):
		forecast_string=filter(lambda x: x in string.printable, forecast.text).split('Forecast: ')[1].split(' PoP')[0].replace(" ","-").replace("--","-").replace('F','degF')
		if len(forecast_string.split('-'))==4:
			forecast_string=forecast_string.split('-')[0]+'-'+forecast_string.split('-')[1]+' '+forecast_string.split('-')[2]+'-'+forecast_string.split('-')[3]
		weather_list.append(forecast_string)
	for team in soup.findAll("div",{"class":"team-data"}):
		team_list.append(team_map[team.find("div",{"class":"team-name"}).get_text()])
		pitcher_list.append(team.find("a",{"class":"player-link"}).get_text())
	for table in soup.findAll("div",{"class":"cssDialog clearfix"}):
		table_string=table.get_text()
		home_lineup=[]  
		away_lineup=[]
		if table_string.count("9. ")==2:
			for j in range(1,10):
				name_list_raw=table_string[table_string.find(str(j)+". ")+3:].split(" (")
				home_lineup.append(name_list_raw[0])
				name_list_raw=table_string[table_string.find((str(j)+". "),table_string.find(str(j)+". ")+3)+3:].split(" (")
				away_lineup.append(name_list_raw[0])
			lineups_list.append(home_lineup)
			lineups_list.append(away_lineup)
		else:
			lineups_list.append(['no home_lineup listed'])
			lineups_list.append(['no away_lineup listed'])
	i=j=0
	while i<len(lineups_list):
		lineups_list[i].append(pitcher_list[i])
		teamid_dict[team_list[i]]=[gametime_list[j]]
		teamid_dict[team_list[i]].append(weather_list[j])
		teamid_dict[team_list[i]].append(lineups_list[i])
		if i%2 !=0:
			j=j+1	
		i=i+1
	i=j=0
	while i<len(lineups_list):
		for e in lineups_list[i]:
			playerid_dict[e]=[gametime_list[j]]
			playerid_dict[e].append(weather_list[j])
			playerid_dict[e].append(team_list[i])
		if i%2 !=0:
			j=j+1	
		i=i+1	
	return teamid_dict,playerid_dict
# print mlb_starting_lineups()
# os.system('pause')