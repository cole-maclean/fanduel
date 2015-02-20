import database_operations
import ast
import data_scrapping
import collections
import difflib
import numpy
from openopt import *
import general_utils as Ugen
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
def player_mapping(key_col,map_col):
	player_map = {}
	rw = 2
	while Cell('Player Map',rw,key_col).value != None:
		player_map[Cell('Player Map',rw,key_col).value] = Cell('Player Map',rw,map_col).value
		rw = rw + 1
	return player_map
def build_lineup_avg_goals_dict(player_data_dict):
	rw = 2
	team_lineups = data_scrapping.build_lineup_dict()
	player_map = player_mapping(3,2)
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
	player_map = player_mapping(1,2)
	rw = 2
	player_data_dict = database_operations.get_player_data_dict('nhl','2014020710')
	lineup_avg_goals_dict = build_lineup_avg_goals_dict(player_data_dict)
	columns = ['G','C','LW','RW','D','Position','FD_name','Dummy1','TeamID','Dummy2','Salary','PPG','GamesPlayed','Dummy3','Dummy4','Injury','InjuryAge','Dummy5']
 	for player_data in data_scrapping.get_FD_playerlist().iteritems():
 		d = None
 		d = collections.OrderedDict()
 		for i in range(0,5):
 			column_index = i
 			if columns[column_index] == player_data[1][0]: #Player position
 				d[columns[column_index]] = 1
 			else:
 				d[columns[column_index]] = 0
  		for data in player_data[1]:
  			column_index = column_index + 1
 			d[columns[column_index]] = data
 		d['pid'] = 0 #sets up pid field for player uniqueness constraint
 		try:
 			if player_data[1][1] in player_map.keys():
 				mapped_name = player_map[player_data[1][1]]
 			else:
 				mapped_name = player_data[1][1]
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
			if int(player_data[1][6]) > 0 and int(player_data[1][5]) >3000 :
 				print player_data[1][1] + " not in player_data_dict"
 				Cell('Player Mapping',rw,1).value = player_data[1][1]
 				close_matches = difflib.get_close_matches(player_data[1][1],player_data_dict.keys(),10)
 				col = 2
 				for close_player in close_matches:
 					Cell('Player Mapping',rw,col).value = close_player
 					col = col + 1
 				rw = rw + 1
 	#rw = 1
 	#for chk_player in player_data_dict:
 		#Cell(rw,2).value = chk_player
 		#rw = rw + 1
 	return player_data_dict
def optimum_roster():
	player_data_dict = build_full_player_dictionary()
	starting_goalies = data_scrapping.get_starting_goalies()
	player_universe = build_player_universe(player_data_dict,starting_goalies)
	losing_team_list =[]
	ex_list = []
	items = [
         {
             'name': player,
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
#data_scrapping.update_gamedata(Cell("Parameters",'clLastGameDataID').value)
rw = 2
r,player_universe,objective = optimum_roster()
for player in r.xf:
	Cell("Roster",rw,1).value = player
	Cell("Roster",rw,2).value = player_universe[player]['Team']
	Cell("Roster",rw,3).value = player_universe[player]['Position']
	Cell("Roster",rw,4).value = float(player_universe[player]['Avg_Line_Goals'])*float(player_universe[player]['Avg_ToI'])
	Cell("Roster",rw,5).value = player_universe[player]['Salary']
	Cell("Roster",rw,6).value = player_universe[player]['Avg_ToI']
	Cell("Roster",rw,7).value = player_universe[player]['Avg_Line_Goals']
	rw = rw + 1
os.system('pause')