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
	FDSession = fdo.FDSession()
	current_bet = 0
	#last contest_time = get_last_contest_time() - return last time for latest contest tonight
	run_time = 1000
	while current_bet <= max_bet:
		if run_time > update_model_interval:
			contest_rosters = build_contest_rosters(FDSession,sport_list)
			run_time = 10
		else:
			for contest_id,roster in contest_rosters.iteritems():
				contest_list = FDSession.fanduel_api_data("https://api.fanduel.com/contests?fixture_list="+contest_id)['contests']
				for contest in contest_list:
					enter, entered_contest = contest_entry_decider(FDSession,contest,roster)
					if enter  ==True:
						entered_contest['model_confidence'] = roster['confidence']
						entered_contest['slate_player_count'] = roster['slate_player_count']
						entered_contest['timestamp'] = str(datetime.now())
						entered_contest['sport'] = roster['class'].sport
						print 'entering contest'
						os.system('pause')
						if FDSession.enter_contest(contest['entries']['_url'],roster['roster'],entered_contest) == True:
							current_bet = current_bet + contest['entry_fee']
							print 'current bet=' + str(current_bet)
		raw_input('Loop: Enter to continue')

def build_contest_rosters(FDSession,sport_list):
	contest_rosters = {}
	model_roster={}
	for sport in sport_list:
		if sport == 'MLB':
			Sport_Class = Sport.MLB()
		elif sport=='NBA':
			Sport_Class=Sport.NBA()
		daily_contests = FDSession.get_daily_contests(sport)
		print 'daily contests: %s' % daily_contests
		for contest_id,url in daily_contests.iteritems():
			sport_output=Sport_Class.optimal_roster(FDSession,url,-100,False,False)
			model_roster={'confidence':sport_output['confidence'],'roster':sport_output['roster'],
							'optimizer':sport_output['optimizer']}
			model_roster['slate_player_count'] = len(FDSession.fanduel_api_data(url)['players'])
			model_roster['class'] = Sport_Class
			if model_roster['roster'] != []:
				contest_rosters[contest_id] = model_roster
	return contest_rosters

def contest_entry_decider(FDSession,contest,roster):
	Sport_Class = roster['class']
	for key,data in Sport_Class.contest_constraints.iteritems():
		if contest[key] not in data:
			return False, contest
	entries_data = FDSession.fanduel_api_data(contest['entries']['_url'])
	if entries_data == {}:
		return False, contest
	if float(entries_data['_meta']['entries']['count'])/float(contest['size']['max']) > 0.25:
		return True, contest
	else:
		return False,contest

# MLB=Sport.MLB()
# MLB.get_daily_game_data('20150831','20150901',True)
# print run_program(["NBA"],10,1)