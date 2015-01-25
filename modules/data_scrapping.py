import json
import mechanize
import cookielib
import urllib2
import MySQLdb
import os
import time
import ast
from bs4 import BeautifulSoup
import numpy
import operator
import math
from openopt import *
def update_gamedata(LastGameDataID): #TODO: add optional paramters for which tables to update, check team roster for player #s, consideration for other sports
	# game data
	print 'Only update game data when no games are currently in progress'
	os.system('pause')
	for i in range(LastGameDataID + 1,10000): 
		sGameID = '201402' + str(i).zfill(4)
		data_status = NHL_gamedata('20142015',sGameID)
		if data_status == "URL not found":
			break
def NHL_gamedata(sGameSeason,sGameID):
	sUrl = 'http://live.nhle.com/GameData/' + sGameSeason + '/' + sGameID + '/gc/gcbx.jsonp'
	json_data = get_JSON_data(sUrl, ['GCBX.load(',')'])
	if json_data == "URL not found":
		Cell("Parameters",'clLastGameDataID').value = int(sGameID[-4:]) -1
		return "URL not found"
	home_player_num_lookup,home_team, away_player_num_lookup,away_team = get_NHL_roster_data(sGameSeason,sGameID)
	roster_team = 'home'
	for team in json_data['rosters'].values(): #roster_team is a hackjob, need to clean this up
		if roster_team == 'home':
			player_num_lookup = home_player_num_lookup
			player_team = home_team
		elif roster_team == 'away':
			player_num_lookup = away_player_num_lookup
			player_team = away_team
		for player_types in team.values():
			for player_stats in player_types:
				try:
					player = player_num_lookup[player_stats['num']]
				except KeyError:
					print str(player_stats['num']) + " KeyError"
					player = str(player_stats['num']) + " KeyError"
				write_to_db('Player, GameID, Team',[player,sGameID,player_team],player_stats)
		roster_team = 'away'
	return "Data Succesfully loaded"
def get_NHL_roster_data(sGameSeason, sGameID):
	home_player_num_lookup = {}
	away_player_num_lookup = {}
	sUrl = 'http://live.nhle.com/GameData/' + sGameSeason + '/' + sGameID + '/gc/gcsb.jsonp'
	json_data = get_JSON_data(sUrl, ['GCSB.load(',')'])
	HomeTeam = json_data['h']['ab']
	AwayTeam = json_data['a']['ab']
	HUrl = 'http://nhlwc.cdnak.neulion.com/fs1/nhl/league/teamroster/' + HomeTeam + '/iphone/clubroster.json'
	AUrl = 'http://nhlwc.cdnak.neulion.com/fs1/nhl/league/teamroster/' + AwayTeam + '/iphone/clubroster.json'
	home_roster_data = get_JSON_data(HUrl)
	for position in home_roster_data.values()[1:]:
		for player in position:
			try:
				home_player_num_lookup[player['number']] = player['name']
			except KeyError:
				print player['name'] + " num lookup failure"
	away_roster_data = get_JSON_data(AUrl)
	for position in away_roster_data.values()[1:]:
		for player in position:
			try:
				away_player_num_lookup[player['number']] = player['name']
			except KeyError:
				print player['name'] + " num lookup failure"
	return home_player_num_lookup, HomeTeam, away_player_num_lookup,AwayTeam
def insert_mysql(columns, placeholders, data):
    sql = "INSERT INTO hist_player_data (%s) VALUES (%s)" % (columns, placeholders)
    conn = MySQLdb.Connection(db="autotrader",host="localhost",user="root",passwd="Timeflies1");
    cur = conn.cursor()
    cur.execute(sql, data)
    cur.execute('COMMIT')
    time.sleep(.1)
def get_JSON_data(sUrl,clean_strings = ''):
	try:
		response = urllib2.urlopen(sUrl)
		cdata = response.read()
		for cstr in clean_strings:
			cdata = cdata.replace(cstr,'')
		return json.loads(cdata)
	except urllib2.HTTPError, e:
		return "URL not found"
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
def write_to_db(static_columns,static_data,write_data): #TODO: need to generalize (columns, placeholders, etc.)
	row_data = [str(v) for v in write_data.values()]
	static_data.extend(row_data)
	placeholders = ', '.join(['%s'] * (len(static_data)))
	columns = static_columns
	for i in range(1,len(row_data) + 1):
		columns = columns + ', Stat' + str(i)
	insert_mysql(columns, placeholders, static_data)
def parse_html(sUrl,sStart,sEnd):
    response = urllib2.urlopen(sUrl)
    shtml = response.read()
    shtml = shtml.replace('false',"False")
    intStart = shtml.find(sStart)
    intEnd = shtml.find(sEnd,intStart)
    parsed_html = shtml[intStart:intEnd].replace(sStart,"")
    return parsed_html
def multiple_replace(string, rep_dict):
    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)
def get_matchups():
	matchups ={}
	matchup_text = parse_html(Cell("cLineUpURL").value,"FD.playerpicker.teamIdToFixtureCompactString = ",";")
	formatted_text = multiple_replace(matchup_text,{'<b>':'','</b>':'','[':'',"'":'','{':'','"':'',':':'',',':'','@':'','}':''})
	start_char = 0
	while start_char < len(formatted_text):
		team_id = formatted_text[start_char:start_char + 3]
		team_name = formatted_text[start_char + 3:start_char + 6]
		rival_name = formatted_text[start_char + 6:start_char + 9]
		rival_id = formatted_text[start_char + 9:start_char + 12]
		matchups[team_id] = [team_name,rival_name,rival_id]
		matchups[rival_id] = [rival_name,team_name,team_id]
		#print str(team_id) +',' + team_name + ',' + rival_name + ',' + str(rival_id)
		start_char = start_char + 18
	#print matchups
	#Cell("B17").value = formatted_text
	return matchups
def cookie_login(login_URL,site_URL,sPassword):
	# Browser
	br = mechanize.Browser()
	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	br.addheaders = [('User-agent', 'Chrome')]
	# The site we will navigate into, handling it's session
	br.open(login_URL)
	# View available forms
	for f in br.forms():
	    print f
	# Select the second (index one) form (the first form is a search query box)
	br.select_form(nr=0)
	# User credentials
	#br.form['login'] = 'maclean.cole@gmail.com'
	br.form['password'] = sPassword
	# Login
	br.submit()
	return br.open(site_URL).read()
def get_FD_contests():
	with open('C:/Users/Cole/Desktop/FanduelV2/fanduel/contest html.html',"r") as myfile:
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
def get_best_contests(sport_list,game_type_list,size_range,entry_fee_list,percent_full):
	contest_dict = get_FD_contests()
	with open('C:/Users/Cole/Desktop/FanduelV2/fanduel/userwinscache.txt',"r") as myfile:
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
         } 
         for contest in contest_dict if contest['sport'] in sport_list and size_range[0] <= int(contest['size']) <=size_range[1] \
          and contest['entryFee'] in entry_fee_list and  contest['flags'] in game_type_list and \
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
						print th.text	
				time.sleep(1)
		contest['user_wins_array'] = user_wins_array
		for contest_sport in sport_list:
			arr = numpy.array(user_wins_array[contest_sport.upper()])
			top_player_count = math.ceil(0.25*contest['size'])
			contest[contest_sport + '_avg_top_wins'] = numpy.mean(arr[arr.argsort()[-top_player_count:][::-1]])#Need to decide best stats for paticualar contest type
			contest[contest_sport + '_avg_top_wins_weighted_avg'] = contest[contest_sport + '_avg_top_wins']*contest['entryFee']/Cell('Parameters','clEntryLimit').value
		contest['game_url'] = 'https://www.fanduel.com/e/Game/' + contest['game_id'] + '?tableId=' + contest['contest_id'] + '&fromLobby=true'
	with open('C:/Users/Cole/Desktop/FanduelV2/fanduel/userwinscache.txt',"w") as myfile:
		myfile.write(str(user_wins_cache))
	return potential_contests
def get_FD_playerlist():
 	FD_list = ast.literal_eval(parse_html('https://www.fanduel.com/e/Game/11498?tableId=9979076&fromLobby=true',"FD.playerpicker.allPlayersFullData = ",";"))
 	#for player_data in FD_list:
 		#rival_team = matchups[FD_list[player_data][3]][1]
 		#FD_list[player_data].append(rival_team)
 	return FD_list
def team_mapping():
	team_map = {}
	for rw in range(2,31):#This isnt great...
		team_map[Cell('Team Map',rw,1).value] = Cell('Team Map',rw,2).value
	return team_map
def build_lineup_dict():
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
						print strlineup.get_text()
					line_id = lineup.get('id')[-1]			
			team_lineups_dict[team] = lines
		Cell('Parameters','clLineupsCache').value = team_lineups_dict
	else:
		team_lineups_dict = ast.literal_eval(Cell('Parameters','clLineupsCache').value)
	return team_lineups_dict
def output_best_contests():
	rw = 2
	items = [contest for contest in get_best_contests(['nhl'],[{"standard":1,"50_50":1}],[3,100],[1,2,5,10],0.5) if contest['nhl_avg_top_wins'] <= Cell('Parameters','clMaxAvgWins').value]
	constraints = lambda values : (
    	values['entryFee'] <= Cell('Parameters','clEntryLimit').value,
    	values['entryFee'] >= Cell('Parameters','clEntryLimit').value*.7,
    )
	objective  = 'nhl_avg_top_wins_weighted_avg'
	p = KSP(objective, items, goal = 'min', constraints=constraints)
	r = p.solve('glpk',iprint = 0)
	for contest in r.xf:
		Cell('Best Contests',rw,1).value = items[contest]['game_url']
		Cell('Best Contests',rw,2).value = items[contest]['nhl_avg_top_wins']
		Cell('Best Contests',rw,3).value = items[contest]['entriesData']
		Cell('Best Contests',rw,4).value = items[contest]['entryFee']
		rw = rw + 1
#print output_best_contests()
#print build_lineup_dict()['TOR']
#os.system('pause')
