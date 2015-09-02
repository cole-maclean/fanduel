import re
import requests
import general_utils as Ugen
import os
from bs4 import BeautifulSoup
import json
import string_utils as Ustr
import ast
import datetime
import time
import dateutil.parser
import data_scrapping_utils as Uds
import database_operations as dbo

class FDSession():
	def __init__(self):
		self.session, self.session_id = self.get_fanduel_session()
		self.headers = self.get_fanduel_headers()

	def get_fanduel_session(self):#Refactor - think this needs to be turned into a class
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

	def get_fanduel_headers(self):
		r = self.session.get('https://www.fanduel.com/games')
		XAuth = r.cookies['X-Auth-Token']
		r_text = r.text
		intStart = r_text.find("apiClientId: '")
		intEnd = r_text.find("',",intStart)
		APIclientID = 'Basic ' + r_text[intStart:intEnd].replace("apiClientId: '","")
		headers = {'Authorization':APIclientID,'X-Auth-Token':XAuth,'Accept':'*/*','Access-Control-Request-Headers':'accept, authorization, x-auth-token','Host':'api.fanduel.com','referer':'https://www.fanduel.com/games','Origin':'https://www.fanduel.com','User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7','Content-Type':'application/json'}
		return headers

	def fanduel_api_data(self,sURL):
		r = self.session.get(sURL,headers=self.headers)
		if r.status_code == 200:
			return json.loads(r.text)
		else:
			print 'fanduel api data call failed with ' + str(r.status_code)
			print r.text
			return {}

	def get_daily_contests(self,sport,start_hours = []):
		if start_hours == []:
			contests = ({contest['id']:contest['players']['_url'] for contest in
						 self.fanduel_api_data('https://api.fanduel.com/fixture-lists')['fixture_lists'] 
						 if contest['sport'] == sport and (dateutil.parser.parse(contest['start_date'])- datetime.timedelta(hours=4)).day == datetime.datetime.now().day})
		else:
			contests = ({contest['id']:contest['players']['_url'] for contest in
						 self.fanduel_api_data('https://api.fanduel.com/fixture-lists')['fixture_lists'] 
						 if contest['sport'] == sport
						 and (dateutil.parser.parse(contest['start_date'])- datetime.timedelta(hours=4)).hour in start_hours
						 and (dateutil.parser.parse(contest['start_date'])- datetime.timedelta(hours=4)).day == datetime.datetime.now().day})
		return contests

	def enter_contest(self,contest_url,roster_data,entered_contest):#Cole: Need to wrtie to db on succesful entry
		print contest_url
		r = self.session.post(contest_url,json.dumps(roster_data),headers=self.headers)
		if r.status_code == 201:
			print "entry success"
			os.system('pause')
			cols =  ", ".join([key for key in entered_contest.keys()])
			values =  ", ".join(['"' + json.dumps(data).replace('"',"'") + '"' for data in entered_contest.values()])
			dbo.insert_mysql("fanduel_contests", cols, values)
			return True
		else:
			print 'entry failed with HTTP error ' + str(r.status_code)
			print r.text
			entry_id = 0
			entry_status = 'failed'
			os.system('pause')
			return False



