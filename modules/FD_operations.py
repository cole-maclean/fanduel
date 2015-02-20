import re
import requests
import os
from bs4 import BeautifulSoup
def get_fanduel_session():
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
def enter_contest(contest_url,player_data):
	game_id = re.findall('[0-9]{5,5}',contest_url)[0]
	table_id = re.findall('[0-9]{8,8}',contest_url)[0]
	s, session_id = get_fanduel_session()
	data = {'cc_session_id':session_id,'cc_action':'cca_jointable','cc_failure_url':contest_url,\
	'game_id':game_id,'playerData':player_data,'table_id':table_id,'tablespec_id':'','is_public':'1','currencytype':'1'}
	s.post('https://www.fanduel.com/c/CCEntry',data)
	return s.headers
player_data = ('[["LW","8980","87942","654"],["LW","8478","87945","663"],["RW","8442","95317","652"],'
				'["RW","16969","87945","663"],["C","9279","87942","654"],["C","9992","87944","656"],'
				'["D","8689","87941","666"],["D","12952","87942","676"],["G","8532","95317","668"]]')
print enter_contest('https://www.fanduel.com/e/Game/11654?tableId=10613795&fromLobby=true',player_data)
os.system('pause')