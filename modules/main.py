import database_operations as dbo
import ast
import data_scrapping
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

def run_program(sport_list,update_model_interval):
	#last contest_time = get_last_contest_time() - return last time for latest contest tonight
	#while current_time < last_contest_time:
		if run_time < update_model_interval:
			contest_rosters = {}
			if 'MLB' in sport_list:
				MLB_rosters = {}
				MLB= Sport.MLB()
				for contest,url in MLB.daily_contests.iteritems():
					contest_type_rosters ={}
					for contest_type in MLB.contest_types.keys():
						pass



def build_player_universe(full_playerlist,goalie_list):
	delkeys = []
	for key,data in full_playerlist.iteritems():
		if 'Salary' in full_playerlist[key]:
			player =  key
			position = data['Position']
			if position == 'G':
				if not any(player in s for s in goalie_list):
					delkeys.append(key)
	for key in delkeys:
		full_playerlist.pop(key)
	return full_playerlist
def build_lineup_avg_goals_dict(player_data_dict):
	rw = 2
	team_lineups = data_scrapping.build_lineup_dict()
	player_map = Ugen.excel_mapping('Player Map',3,2)
	for team in team_lineups:
		for lineup in team_lineups[team]:
			lineup_goals = []
			for player in lineup:
				if player in player_map.keys():
					mapped_name = player_map[player]
				else:
					mapped_name = player
				try: #Need to modularize player mapping
					np_array = numpy.array(map(float,player_data_dict[mapped_name]['Goals']))
					Avg_Goals = numpy.mean(np_array)
					lineup_goals.append(Avg_Goals)
				except KeyError:
					Cell('Player Map',5,5).value = mapped_name
					print mapped_name
			np_array = numpy.array(lineup_goals)
			Avg_Goals = numpy.mean(np_array)
			for player in lineup:
				if player in player_map.keys():
					mapped_name = player_map[player]
				else:
					mapped_name = player
				try:
					if 'Avg_Line_Goals' in player_data_dict[mapped_name]:
						player_data_dict[mapped_name]['Avg_Line_Goals'] = max(player_data_dict[mapped_name]['Avg_Line_Goals'],Avg_Goals)
					else:
		 				d = None
		 				d = collections.OrderedDict()
		 				d['Avg_Line_Goals'] = Avg_Goals
						player_data_dict[mapped_name].update(d)
				except KeyError:
					print mapped_name
	return player_data_dict
def build_full_player_dictionary():
	player_map = Ugen.excel_mapping('Player Map',1,2)
	rw = 2
	player_data_dict = dbo.get_player_data_dict('NHL','2014021100')
	lineup_avg_goals_dict = build_lineup_avg_goals_dict(player_data_dict)
	columns = ['PlayerID','G','C','LW','RW','D','Position','FD_name','MatchupID','TeamID','Dummy2','Salary','PPG','GamesPlayed','Dummy3','Dummy4','Injury','InjuryAge','Dummy5','PlayerID']
 	for player_id,player_data in data_scrapping.get_FD_playerlist().iteritems():
 		d = None
 		d = collections.OrderedDict()
 		d[columns[0]] = player_id
 		for i in range(1,6):
 			column_index = i
 			if columns[column_index] == player_data[0]: #Player position
 				d[columns[column_index]] = 1
 			else:
 				d[columns[column_index]] = 0
  		for data in player_data:
  			column_index = column_index + 1
 			d[columns[column_index]] = data
 		try:
 			if player_data[1] in player_map.keys():
 				mapped_name = player_map[player_data[1]]
 			else:
 				mapped_name = player_data[1]
 			player_data_dict[mapped_name].update(d)
 			d = None
 			d = collections.OrderedDict()
			if player_data_dict[mapped_name]['Position'] == 'G':
				np_array = numpy.array(player_data_dict[mapped_name]['weighted_toi'])
				Avg_ToI = numpy.mean(np_array[numpy.nonzero(np_array)])
				d['Avg_ToI'] = Avg_ToI/3#Aribitrary scaling
				np_array = numpy.array(map(float,player_data_dict[mapped_name]['SavePercent']))
				Avg_SavePercent = numpy.mean(np_array)
				d['Avg_Line_Goals'] = (Avg_SavePercent - 1) * 10#arbitrary scaling
			else:
				np_array = numpy.array([Ugen.getSec(s) for s in player_data_dict[mapped_name]['ToI']])
				Avg_ToI = numpy.mean(numpy.mean(np_array[numpy.nonzero(np_array)]))
				d['Avg_ToI'] = Avg_ToI
			player_data_dict[mapped_name].update(d)
		except KeyError: #need to map names
			if int(player_data[6]) > 0 and int(player_data[5]) >3000 :
 				print player_data[1] + " not in player_data_dict"
 				Cell('Player Mapping',rw,1).value = player_data[1]
 				close_matches = difflib.get_close_matches(player_data[1],player_data_dict.keys(),10)
 				col = 2
 				for close_player in close_matches:
 					Cell('Player Mapping',rw,col).value = close_player
 					col = col + 1
 				rw = rw + 1
 	return player_data_dict
def optimum_roster(vegas_threshold):
	player_data_dict = build_full_player_dictionary()
	starting_goalies = data_scrapping.get_starting_goalies()
	player_universe = build_player_universe(player_data_dict,starting_goalies)
	team_odds = TeamOdds.get_team_odds('NHL')
	slate_size = len(team_odds)/2
	losing_team_list =[s for s in team_odds.keys() if team_odds[s] <= vegas_threshold] #Cole: incorporated TeamOdds into optimum roster
	#losing_team_list.extend(['OTT','WSH'])
	print losing_team_list
	ex_list = []
	items = [
         {
             'name': player,
             'Position': player_data_dict[player]['Position'],
             'PlayerID': player_data_dict[player]['PlayerID'],
             'MatchupID': player_data_dict[player]['MatchupID'],
             'TeamID': player_data_dict[player]['TeamID'],
             'Salary': int(player_data_dict[player]['Salary']),
             'Team': player_data_dict[player]['Team'][-1],
             'G': int(player_data_dict[player]['G']), 
             'C': int(player_data_dict[player]['C']),
             'LW':  int(player_data_dict[player]['LW']), 
             'RW': int(player_data_dict[player]['RW']),
             'D': int(player_data_dict[player]['D'],),
             'PPG': int(player_data_dict[player]['PPG']),
             'Avg_ToI' :int(player_data_dict[player]['Avg_ToI']),
             'Weighted_Avg_Line_Goals' :float(player_data_dict[player]['Avg_Line_Goals'])*float(player_data_dict[player]['Avg_ToI']),
         } 
         for player in player_universe if 'Salary' in player_universe[player] and 'Avg_Line_Goals' in player_universe[player] and player_universe[player]['Team'][-1] not in losing_team_list and player not in ex_list 
         ]
	constraints = lambda values : (
    	values['Salary'] <= 55000,
    	values['Salary'] >=53000,
        values['G'] == 1,
        values['C'] == 2,
        values['LW'] == 2,
        values['RW'] == 2,
        values['D'] == 2,
    )
	objective  = 'Weighted_Avg_Line_Goals'
	p = KSP(objective, items, goal = 'max', constraints=constraints)
	r = p.solve('glpk',iprint = 0)
	return r,player_universe,objective
def output_final_roster(vegas_threshold):
	DB_parameters=Ugen.ConfigSectionMap('local text')
	r,player_universe,objective = optimum_roster(vegas_threshold)
	strategy_data = {}
	roster_data = []
	strategy_data['strat_params'] = {'objective':objective,'vegas':vegas_threshold,'slate_size':4}
	rw = 2
	for player in r.xf:
		roster_data.append([player_universe[player]['Position'],player_universe[player]['PlayerID'],player_universe[player]['MatchupID'],player_universe[player]['TeamID']])
		Cell("Roster",rw,1).value = player
		Cell("Roster",rw,2).value = player_universe[player]['Team']
		Cell("Roster",rw,3).value = player_universe[player]['Position']
		Cell("Roster",rw,4).value = player_universe[player]['Avg_Line_Goals'] * player_universe[player]['Avg_ToI']
		Cell("Roster",rw,5).value = player_universe[player]['Salary']
		rw = rw + 1
	strategy_data['player_data'] = sorted(roster_data, key=get_sort_key)
	with open(DB_parameters['rostertext'],"w") as myfile: #Ian: replaced hard-coded folder path with reference to config file
		myfile.write(str(strategy_data).replace(' ',''))
	return strategy_data
def get_sort_key(sort_list):
	sort_keys = {'LW':1,'RW':2,'C':3,'D':4,'G':5}
	return sort_keys[sort_list[0]]
def run_enter_best_contests(daily_bet,bin_size):
	s, session_id = fdo.get_fanduel_session()
	total_bet = 0
	time_remaining = Ugen.get_time_remain('15:00')
	wins_data = build_pWins_vs_topwins_dict(bin_size)
	print wins_data
	while total_bet < daily_bet and time_remaining > 0:
		tmp_total_bet = total_bet
		potential_contests = data_scrapping.get_potential_contests(s,['nhl'],[{"standard":1}],[3,5],[1,2,5,10,25],0.6,'5:00')
		print potential_contests
		total_bet = total_bet + data_scrapping.enter_best_contests(s,session_id,'NHL',(daily_bet - total_bet),potential_contests,time_remaining,wins_data,bin_size)
		time.sleep(60)
		time_remaining = Ugen.get_time_remain('15:00')
	fdo.end_fanduel_session(s)
	return total_bet
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

# MLB = Sport.MLB()
# #MLB.get_daily_game_data(['20150420','20150419','20150418','20150417','20150416','20150415'],True)
# MLB.get_db_gamedata()

# #data_scrapping.update_gamedata('MLB',Cell("Parameters",'clLastGameDataID').value)
# #print output_final_roster(40)
# #print run_enter_best_contests(100,25)#paramter passing getting out of hand, need to figure out how refactor. Classes?
# #dbo.load_csv_into_db('C:/Users/Cole/Desktop/FanDuel/fanduel entry history.csv','hist_performance')
# #print Ugen.output_dict(build_pWins_vs_topwins_dict(5))
# os.system('pause')