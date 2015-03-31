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
	headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7'}
	data = {'cc_session_id':session_id,'cc_action':'cca_login','cc_failure_url':'https://www.fanduel.com/p/login',\
	'cc_success_url':'https://www.fanduel.com/p/home','email':'cole__maclean@hotmail.com','password':passwd,'login':'Log in'}
	s.post('https://www.fanduel.com/c/CCAuth',data,headers=headers)
	return s, session_id
def end_fanduel_session(s):
	r = s.get('https://www.fanduel.com/c/CCAuth?cc_action=cca_logout&cc_success_url=https//www.fanduel.com/&cc_failure_url=https//www.fanduel.com/')
	return r.headers
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
	with open('C:/Users/Cole/Desktop/Fanduel/fanduel/response.txt',"w") as myfile:
		myfile.write(str(r.text))
	return entry_id, entry_status