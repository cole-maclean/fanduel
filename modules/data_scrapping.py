import json
import urllib2
import os
import time
import ast
from bs4 import BeautifulSoup
import numpy
import operator
import math
import database_operations as dbo
import data_scrapping_utils as Uds
import re
import requests
def update_gamedata(LastGameDataID): #TODO: add optional paramters for which tables to update, check team roster for player #s, consideration for other sports
	print 'Only update game data when no games are currently in progress'
	os.system('pause')
	for i in range(LastGameDataID + 1,10000): 
		sGameID = '201402' + str(i).zfill(4)
		data_status = get_NHL_gamedata('20142015',sGameID)
		if data_status == "URL not found":
			break
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
def write_nhl_game_data(team_data,player_team,sGameID):
	player_num_lookup = get_NHL_team_players(player_team)
	for player_types in team_data.values():
		for player_stats in player_types:
			try:
				player = player_num_lookup[player_stats['num']]
			except KeyError:
				print str(player_stats['num']) + " KeyError"
				player = str(player_stats['num']) + " KeyError"
			dbo.write_to_db('hist_player_data','Player, GameID, Team',[player,sGameID,player_team],player_stats)
	return 'data succesfully loaded'
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
			if goalie_table.get_text() == 'Confirmed' or goalie_table.get_text() == 'Likely':
				goalie = goalie_heading.get_text()
				goalie_list.append(goalie)
	for goalie_data in soup.findAll("div", { "class":"goalie away" }):
		goalie_table = goalie_data.find('dt')
		goalie_heading = goalie_data.find('h5')
		if goalie_table and goalie_heading:
			if goalie_table.get_text() == 'Confirmed' or goalie_table.get_text() == 'Likely':
				goalie = goalie_heading.get_text()
				goalie_list.append(goalie)
	return goalie_list
def get_FD_contests():
	with open('C:/Users/Cole/Desktop/Fanduel/fanduel/contest html.html',"r") as myfile:
		data = myfile.read()
	data= data.replace('false',"False")
	data= data.replace('true',"True")
	data= data.replace('null',"")
	intStart = data.find('LobbyConnection.initialData = ')
	intEnd = data.find('};',intStart)
	parsed_html = data[intStart:intEnd + 1].replace('LobbyConnection.initialData = ',"")
	parsed_html = parsed_html.replace(':,',':0,')
	contest_dict = ast.literal_eval(parsed_html)
	return contest_dict['additions']
def get_best_contests(sport_list,game_type_list,size_range,entry_fee_list,percent_full,game_start):
	contest_dict = get_FD_contests()
	with open('C:/Users/Cole/Desktop/Fanduel/fanduel/userwinscache.txt',"r") as myfile:
		data = myfile.read()
	user_wins_cache = ast.literal_eval(data)
	potential_contests = [
         {
             'contest_id': str(contest['uniqueId']),
             'game_id': str(contest['gameId']),
             'sport': contest['sport'],
             'startTime': contest['startTime'], 
             'entryFee': int(contest['entryFee']),
             'size':  int(contest['size']), 
             'gameType': contest['flags'],
             'entriesData': int(contest['entriesData']),
             'startString': str(contest['startString'])
         } 
         for contest in contest_dict if contest['sport'] in sport_list and size_range[0] <= int(contest['size']) <=size_range[1] \
          and contest['entryFee'] in entry_fee_list and  contest['flags'] in game_type_list and  game_start in contest['startString'] and \
           float(contest['entriesData'])/float(contest['size']) > percent_full and float(contest['entriesData'])/float(contest['size']) < 1
         ]
	for contest in potential_contests:
		entry_url = 'https://www.fanduel.com/pg/Lobby/showTableEntriesJSON/' + contest['contest_id'] + '/0/10000'
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
		contest['user_wins_array'] = user_wins_array
		for contest_sport in sport_list:
			arr = numpy.array(user_wins_array[contest_sport.upper()])
			top_player_count = math.ceil(0.25*contest['size'])
			contest[contest_sport + '_avg_top_wins'] = numpy.mean(arr[arr.argsort()[-top_player_count:][::-1]])#Need to decide best stats for paticualar contest type
			contest['game_url'] = 'https://www.fanduel.com/e/Game/' + contest['game_id'] + '?tableId=' + contest['contest_id'] + '&fromLobby=true'
	with open('C:/Users/Cole/Desktop/Fanduel/fanduel/userwinscache.txt',"w") as myfile:
		myfile.write(str(user_wins_cache))
	return sorted(potential_contests,key=operator.itemgetter('nhl_avg_top_wins'),reverse=False)
def get_FD_playerlist():
 	FD_list = ast.literal_eval(Uds.parse_html('https://www.fanduel.com/e/Game/11646?tableId=10582846&fromLobby=true',"FD.playerpicker.allPlayersFullData = ",";"))
 	return FD_list
def team_mapping():
	team_map = {}
	for rw in range(2,31):#This isnt great...
		team_map[Cell('Team Map',rw,1).value] = Cell('Team Map',rw,2).value
	return team_map
def build_lineup_dict():
	rw = 2
	if Cell('Parameters','clLineupsCache').value == None:
		team_map = team_mapping()
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
def output_best_contests():
	rw = Cell('Parameters','clBCLastRow').value
	all_contests = get_best_contests(['nhl'],[{"standard":1,"50_50":1}],[3,100],[1,2,5,10],0.5,'10:00')
	for contest in all_contests:
		if contest['nhl_avg_top_wins'] <=Cell('Parameters','clMaxAvgWins').value:
			Cell('Best Contests',rw,2).value = time.strftime("%d/%m/%Y")
			Cell('Best Contests',rw,3).value = contest['game_url']
			Cell('Best Contests',rw,1).value = re.findall('[0-9]{8,8}',contest['game_url'])[0]
			Cell('Best Contests',rw,4).value = contest['nhl_avg_top_wins']
			Cell('Best Contests',rw,5).value = contest['size']
			Cell('Best Contests',rw,6).value = contest['entryFee']
			Cell('Best Contests',rw,7).value = contest['entriesData']
			rw = rw + 1
def get_fanduel_session():
	with open('C:\Users\Cole\Desktop\Fanduel\Parameters.txt',"r") as myfile:
	    passwd = myfile.read().split(',')[1]
	s = requests.session()
	r = s.get('https://www.fanduel.com/p/login')
	soup = BeautifulSoup(r.text)
	session_id = soup.find('input', {'name': 'cc_session_id'}).get('value')
	data = {'cc_session_id':session_id,'cc_action':'cca_login','cc_failure_url':'https://www.fanduel.com/p/login','cc_success_url':'https://www.fanduel.com/p/home','email':'maclean.cole@gmail.com','password':passwd,'login':'Log in'}
	s.post('https://www.fanduel.com/c/CCAuth',data)
	return s
def get_live_contest_ids():
	s = get_fanduel_session()
	r = s.get('https://www.fanduel.com/mycontests/162491/live?start=0&number=10000')
	live_contest_dict = json.loads(r.text)
	for contest in live_contest_dict['seats']:
		dbo.write_to_db('FD_table_contests','table_id,contest_id',[str(contest[2].split(r'/')[2]),str(contest[0])])
print get_live_contest_ids()
#print output_best_contests()
#print build_lineup_dict()['TOR']
#os.system('pause')
