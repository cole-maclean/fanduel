import database_operations as dbo
import ast
import data_scrapping as ds
import collections
import difflib
import numpy as np
from openopt import *
import general_utils as Ugen
import FD_operations as fdo
import operator
from datetime import datetime
import time
import TeamOdds
import Sport
import os

def run_program(sport_list,update_model_interval,max_bet):
	FD_session,session_id = fdo.get_fanduel_session()
	current_bet = 0
	#last contest_time = get_last_contest_time() - return last time for latest contest tonight
	run_time = 1000
	while current_bet <= max_bet:
		if run_time > update_model_interval:
			contest_rosters = build_contest_rosters(FD_session,sport_list)
			run_time = 10
		else:
			for contest_id,roster in contest_rosters.iteritems():
				contest_list = fdo.fanduel_data(FD_session,"https://api.fanduel.com/contests?fixture_list="+contest_id)[0]['contests']
				for contest in contest_list:
					enter, enetered_contest = contest_entry_decider(FD_session,contest,roster)
					enetered_contest['model_confidence'] = roster['confidence']
					enetered_contest['timestamp'] = datetime.now()
					if enter  ==True:
						print 'entering contest'
						os.system('pause')
						if fdo.enter_contest(FD_session,session_id,contest['entries']['_url'],roster['roster'],entered_contest) == True:
							current_bet = current_bet + contest['entry_fee']
							print 'current bet=' + current_bet

def build_contest_rosters(s,sport_list):
	contest_rosters = {}
	for sport in sport_list:
		if sport == 'MLB':
			Sport_Class = Sport.MLB()
		daily_contests = fdo.get_daily_contests(s,sport)
		for contest_id,url in daily_contests.iteritems():
			model_roster = Sport_Class.optimal_roster(s,url,0,False,False)
			model_roster['class'] = Sport_Class
		if model_roster['roster'] != []:
			print model_roster
			contest_rosters[contest_id] = model_roster
	return contest_rosters

def contest_entry_decider(s,contest,roster):
	Sport_Class = roster['class']
	for key,data in Sport_Class.contest_constraints.iteritems():
		if contest[key] not in data:
			return False, contest
	entries_data = fdo.fanduel_data(s,contest['entries']['_url'])[0]
	if 'error' in entries_data.keys():
		print entries_data['error']
		return False, contest
	if entries_data['_meta']['entries']['count'] > 0:
		user_list = entries_data['users']
		user_wins_dict = ds.get_contest_userwins(user_list)[Sport_Class.sport]
	if np.mean(user_wins_dict) <= 100000:
		contest['user_wins_dict'] = user_wins_dict
		return True, contest
	else:
		contest['user_wins_dict'] = user_wins_dict
		return False, contest

def ian_contest_loop():
	FD_session,session_id = fdo.get_fanduel_session()
	FD_contests = fdo.get_FD_contests(FD_session)
	rw=2
	contests=[]
	for contest in FD_contests:
		entries=contest['entriesData']
		if type(entries)==list:
			continue
		if int(contest['entryFee'])<=3 and int(contest['entriesData'])>0 and contest['contestType']=='FIFTY_FIFTY' and contest['startString']=='4:05&nbsp;pm':
			contest_user_wins = ds.get_contest_userwins(contest)
			Cell("Sheet1",rw,1).value=contest_user_wins
			Cell("Sheet1",rw,2).value=contest['entriesData']
			Cell("Sheet1",rw,7).value=contest['size']
			Cell("Sheet1",rw,6).value=contest['contestType']
			Cell("Sheet1",rw,9).value="https://www.fanduel.com/games/"+str(contest['gameId'])+"/contests/"+str(contest['gameId'])+"-"+str(contest['uniqueId'])+"/enter"
			Cell("Sheet1",rw,10).value=contest['title']
			Cell("Sheet1",rw,11).value=contest['startString']
			if len(contest_user_wins['MLB'])>0:
					Cell("Sheet1",rw,3).value=numpy.amax(contest_user_wins['MLB'])
					Cell("Sheet1",rw,4).value=numpy.mean(contest_user_wins['MLB'])
					Cell("Sheet1",rw,5).value=numpy.median(contest_user_wins['MLB'])
			rw=rw+1
			contests.append(contest['uniqueId'])
	return

def build_pWins_vs_topwins_dict(bin_size):
	hist_performance = build_hist_win_tuples()
	Pwins_dict = {}
	for x,y in hist_performance:
		try: 
			Pwins_dict[Ugen.bin_mapping(x,bin_size)].append(y)
		except KeyError:
			Pwins_dict[Ugen.bin_mapping(x,bin_size)] = [y]
	for key,win_data in Pwins_dict.iteritems():
		Pwins_dict[key].append(numpy.mean(numpy.array(win_data)))
	return Pwins_dict
def build_hist_win_tuples():
	hist_perf_tuples = []
	sql = ('SELECT fd_table_contests.avg_top_wins, hist_performance.Winnings'
	' FROM autotrader.fd_table_contests'
	' INNER JOIN autotrader.hist_performance'
	' ON autotrader.fd_table_contests.entry_id = hist_performance.Entry_Id')
	result_set = dbo.read_from_db(sql)
	for key,rw in result_set.iteritems():
		if rw[1] > 0: #should change this to mapping
			hist_perf_tuples.append((rw[0],1))
		else:
			hist_perf_tuples.append((rw[0],0))
	return hist_perf_tuples


#print run_program(["MLB"],100,50)
print run_program(["MLB"],100,50)
os.system('pause')
#MLB= Sport.MLB()
#print MLB.optimal_roster("https://www.fanduel.com/games/12872/contests/12872-14373582/enter",0,False,False)
# MLB = Sport.MLB()
# #MLB.get_daily_game_data(['20150420','20150419','20150418','20150417','20150416','20150415'],True)
# MLB.get_db_gamedata()

# #data_scrapping.update_gamedata('MLB',Cell("Parameters",'clLastGameDataID').value)
# #print output_final_roster(40)
# #print run_enter_best_contests(100,25)#paramter passing getting out of hand, need to figure out how refactor. Classes?
# #dbo.load_csv_into_db('C:/Users/Cole/Desktop/FanDuel/fanduel entry history.csv','hist_performance')
# #print Ugen.output_dict(build_pWins_vs_topwins_dict(5))
# os.system('pause')
# run_program(["MLB"],10,100)

#ian_contest_loop()
