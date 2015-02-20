import re
import requests
import os
from bs4 import BeautifulSoup
import json
import string_utils as Ustr
def get_fanduel_session():#Refactor - think this needs to be turned into a class
	with open('C:\Users\Cole\Desktop\Fanduel\Parameters.txt',"r") as myfile:
	    passwd = myfile.read().split(',')[1]
	s = requests.session()
	r = s.get('https://www.fanduel.com/p/login')
	soup = BeautifulSoup(r.text)
	session_id = soup.find('input', {'name': 'cc_session_id'}).get('value')
	data = {'cc_session_id':session_id,'cc_action':'cca_login','cc_failure_url':'https://www.fanduel.com/p/login',\
	'cc_success_url':'https://www.fanduel.com/p/home','email':'maclean.cole@gmail.com','password':passwd,'login':'Log in'}
	s.post('https://www.fanduel.com/c/CCAuth',data)
	return s, session_id
def enter_contest(s,session_id,contest_url,player_data):
	game_id = re.findall('[0-9]{5,5}',contest_url)[0]
	table_id = re.findall('[0-9]{8,8}',contest_url)[0]
	data = {'cc_session_id':session_id,'cc_action':'cca_jointable','cc_failure_url':contest_url,\
	'game_id':game_id,'playerData':player_data,'table_id':table_id,'tablespec_id':'','is_public':'1','currencytype':'1'}
	r = s.post('https://www.fanduel.com/c/CCEntry',data)
	print contest_url
	print r.headers
	if r.status_code == 200:
		try:
			entry_url = Ustr.find_between(r.headers['refresh'],'=','?')
			r = s.get(entry_url)
			soup = BeautifulSoup(r.text)
			entry_id = soup.find(id='seatid_current').get_text()
			entry_status = 'success'
		except KeyError:
			print 'entry failed'
			entry_id = 0
			entry_status = 'failed'
	else:
		print 'entry failed with HTTP error ' + r.status_code
		entry_id = 0
		entry_status = 'failed'
	os.system('pause')
	return entry_id, entry_status