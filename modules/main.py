import database_operations as dbo
import ast
import data_scrapping as ds
import collections
import difflib
import numpy
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
	if run_time > update_model_interval:
		contest_rosters = {}
		if 'MLB' in sport_list:
			daily_contests = fdo.get_daily_contests('mlb')
			print daily_contests
			MLB= Sport.MLB()
			for contest,url in daily_contests.iteritems():
				print contest
				for contest_type,confidence in MLB.contest_types.iteritems():
					model_roster = MLB.optimal_roster(url,confidence)
					print model_roster
					if model_roster['roster'] != []:
						contest_rosters['MLB_' + str(contest) + '_' + str(contest_type)] = model_roster
	while True:#current_time < last_contest_time
		FD_contests = fdo.get_FD_contests(FD_session)
		for contest in FD_contests:
			if int(contest['entryFee']) <=25 and (contest['sport'].upper() + '_' + str(contest['gameId']) + '_' + str(contest['flags'])) in contest_rosters.keys():
				roster_data =contest_rosters[(contest['sport'].upper() + '_' + str(contest['gameId']) + '_' + str(contest['flags']))]
				entry_decision,contest = enter_contest_decider(contest)
				if current_bet >=max_bet:
					return current_bet
				elif entry_decision == True:
					entry_id,entry_status =fdo.enter_contest(FD_session,session_id,'https://www.fanduel.com/e/Game/' + str(contest['gameId']) + '?tableId=' + str(contest['uniqueId']) + '&fromLobby=true',str(roster_data['roster']))
					print str(contest['gameId']) + " entry attempt"
					if entry_status == 'success':
						current_bet = current_bet + int(contest['entryFee'])
						contest['entry_id'] = entry_id
						contest['timestamp'] = str(datetime.now())
						contest['model_confidence'] = roster_data['confidence']
						cols = ", ".join([key for key in contest.keys()])
						data = ", ".join(['"' + str(v) + '"' for v in contest.values()])
						dbo.insert_mysql('fanduel_contests',cols,data)
						print str(contest['gameId']) + " entry success"
						time.sleep(1)
					else:
						print str(contest['gameId']) + " entry failed - " + entry_status
		sleep(10)
	return contest_rosters

def enter_contest_decider(contest):
	contest_user_wins = ds.get_contest_userwins(contest)
	print contest_user_wins
	print numpy.mean(contest_user_wins[contest['sport'].upper()])
	print float(contest['entriesData'])
	print float(contest['size'])
	print float(contest['entriesData'])/float(contest['size'])
	if numpy.mean(contest_user_wins[contest['sport'].upper()]) <= 100 and float(contest['entriesData'])/float(contest['size']) >=0.5: #Cole: this is where the decision clasifier will be used to determine contest entry
		contest['entries_win_dict'] = contest_user_wins
		return True,contest
	else:
		return False,contest

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
print run_program(["MLB"],10,10)
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