import re
import requests
import general_utils as Ugen
import os
from bs4 import BeautifulSoup
import json
import string_utils as Ustr
import ast
import datetime
import data_scrapping_utils as Uds

def get_fanduel_session():#Refactor - think this needs to be turned into a class
	Fanduel_login=Ugen.ConfigSectionMap('fanduel') #Ian added ref to config file to avoid hardcoding
	s = requests.session()
	r = s.get('https://www.fanduel.com/p/login')
	soup = BeautifulSoup(r.text)
	session_id = soup.find('input', {'name': 'cc_session_id'}).get('value')
	headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7'}
	data = {'cc_session_id':session_id,'cc_action':'cca_login','cc_failure_url':'https://www.fanduel.com/p/login',\
	'cc_success_url':'https://www.fanduel.com/p/home','email':Fanduel_login['email'],'password':Fanduel_login['password'],'login':'Log in'}
	s.post('https://www.fanduel.com/c/CCAuth',data,headers=headers)
	return s, session_id

def end_fanduel_session(s):
	r = s.get('https://www.fanduel.com/c/CCAuth?cc_action=cca_logout&cc_success_url=https//www.fanduel.com/&cc_failure_url=https//www.fanduel.com/')
	return r.headers

def get_FD_contests(s):
	data = s.get('https://www.fanduel.com/p/Home').text
	data= data.replace('false',"False")
	data= data.replace('true',"True")
	data= data.replace('null',"")
	intStart = data.find('LobbyConnection.initialData = ')
	intEnd = data.find('};',intStart)
	parsed_html = data[intStart:intEnd + 1].replace('LobbyConnection.initialData = ',"")
	parsed_html = parsed_html.replace(':,',':0,')
	contest_dict = ast.literal_eval(parsed_html)
	return contest_dict['additions']

def get_daily_contests(sport):
	daily_contests = {}
	FD_ses,ses_id = get_fanduel_session()
	FD_contests = get_FD_contests(FD_ses)
	for contest in FD_contests:
		if datetime.date.fromtimestamp(contest['startTime']).day == datetime.date.today().day and contest['gameId'] not in daily_contests and contest['sport']==sport.lower():
			daily_contests[contest['gameId']] = 'https://www.fanduel.com/e/Game/' + str(contest['gameId']) + '?tableId=' + str(contest['uniqueId']) + '&fromLobby=true'
	return daily_contests

def enter_contest(s,session_id,contest_url,player_data):
	player_data = player_data.replace(' ','')
	player_data = player_data.replace("'",'"')
	game_id = re.findall('[0-9]{5,5}',contest_url)[0]
	table_id = re.findall('[0-9]{8,8}',contest_url)[0]
	headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7'}
	data = {'cc_session_id':session_id,'cc_action':'cca_jointable','cc_failure_url':contest_url,\
	'game_id':game_id,'playerData':player_data,'table_id':table_id,'tablespec_id':'','is_public':'1','currencytype':'1'}
	r = s.post('https://www.fanduel.com/c/CCEntry',data,headers=headers)
	if r.status_code == 200:
		try:
			entry_url = Ustr.find_between(r.headers['refresh'],'=','?')
			r = s.get(entry_url)
			soup = BeautifulSoup(r.text)
			entry_id = soup.find(id='seatid_current').get_text()
			entry_status = 'success'
		except KeyError:
			soup = BeautifulSoup(r.text)
			fail_reason = soup.find('span', {'class' : 'error-message'}).get_text()
			entry_id = 0
			entry_status = fail_reason
	else:
		print 'entry failed with HTTP error ' + r.status_code
		entry_id = 0
		entry_status = 'failed'
	return entry_id, entry_status

def get_FD_player_dict(contest_url):
	return ast.literal_eval(Uds.parse_html(contest_url,"FD.playerpicker.allPlayersFullData = ",";"))

def get_contest_teams(contest_url):
	FD_team_dict= ast.literal_eval(Uds.parse_html(contest_url,"FD.playerpicker.teamIdToFixtureCompactString = ",";"))
	team_dict = {}
	for team,matchup in FD_team_dict.iteritems():
		print matchup
		if '@<b>' in matchup:
			matchup_split = matchup.split('@<b>')
			print matchup_split
			team_dict[matchup_split[0]] = matchup_split[1][0:3]
	inv_map = {v: k for k, v in team_dict.iteritems()}
	team_dict.update(inv_map)
	return team_dict

