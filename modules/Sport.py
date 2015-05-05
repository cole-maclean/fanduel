import data_scrapping as ds
import data_scrapping_utils as Uds
import database_operations as dbo
import collections
import XMLStats
import os
import numpy
import ast
from openopt import *
import Model
import pandas
import datetime, dateutil.parser
import general_utils as Ugen
import FD_operations as fdo

class Sport(): #Cole: Class has functions that should be stripped out and place into more appropriate module/class
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def FD_points_model(self,player,hist_data,visualize = False):
		FD_projection= collections.namedtuple("FD_projection", ["projected_points", "confidence"])
		self.player_model_data = self.build_model_dataset(hist_data)
		player_model = Model.Model(self.player_model_data,player)
		player_model.FD_points_model(visualize)
		if player_model.modelled:	#Cole: need to develop parameters for each player
			parameters = self.get_parameters(player_model.feature_labels,player)
			if len(player_model.test_feature_matrix) > 1: #Test dataset needs to contain at least 2 datapoints to compute score
				projected_FD_points = (FD_projection(player_model.model.predict(parameters)[-1],
												player_model.model.score(player_model.test_feature_matrix,player_model.test_target_matrix)))
				print projected_FD_points
			else:
				projected_FD_points = FD_projection(player_model.model.predict(parameters)[-1],0)
		else:
			try:
				default_projection = self.player_model_data['FD_median'][-1]
				projected_FD_points = FD_projection(default_projection,0) #Cole: this is the default model prediction and confidence if player cannot be modelled
			except:
				projected_FD_points = FD_projection(0,0)
		player_model = None
		return projected_FD_points

	def events(self,event_date):
		self.gameid = None
		return XMLStats.main(self,'events',{'sport':self.sport,'date':event_date})['event']

	def get_db_event_data(self):
		sql = "SELECT * FROM event_data"
		return dbo.read_from_db(sql,"event_id",True)

	def gameids(self): #Cole: Returns namedtuple of [lastgameid,list of all gameids in db]
		gameid_data = collections.namedtuple("gameid_data", ["lastgameid", "all_gameids"])
		sql = "SELECT hist_player_data.GameID FROM hist_player_data WHERE Sport = '"+ self.sport +"'"
		query_data = dbo.read_from_db(sql,['GameID'],True)
		if query_data:
			return gameid_data(query_data.keys()[0],query_data.keys())
		else:
		    return gameid_data(None,[])

	def get_game_data(self,game_id):
		self.gameid = game_id
		return XMLStats.main(self,'boxscore',None)

	def get_daily_game_data(self,start_date,end_date,store = False):
		event_dates = [d.strftime('%Y%m%d') for d in pandas.date_range(start_date,end_date)]
		#db_eventids = self.get_db_event_data()
		for event_date in event_dates:
			day_events = self.events(event_date)
			event_list = ([game['event_id'] for game in day_events if game['event_status'] == 'completed'
							 and game['season_type'] == 'regular' or 'post'])
			all_game_data = {}
			for indx,game_id in enumerate(event_list):
				#if game_id not in db_eventids.key():
				self.gameid = game_id
				if store == False:
					game_data = XMLStats.main(self,'boxscore',None)
				elif store == True and self.gameid not in self.gameids().all_gameids:
					print "loading " + game_id
					self.parse_event_data(day_events[indx],event_date)
					game_data = XMLStats.main(self,'boxscore',None)
					if game_data != None:
						parsed_data = self.parse_boxscore_data(game_data)
					print game_id + " succesfully loaded"
				else:
					game_data = None
				if game_data:
					all_game_data[game_id] = game_data
		return all_game_data

	def parse_boxscore_data(self,boxscore_data):
		player_map = Ugen.excel_mapping("Player Map",6,5)
		if boxscore_data:
			for dataset,data_model in self.data_model.iteritems():
				for player in boxscore_data[dataset]:
					player_data = collections.OrderedDict()
					player_data['GameID'] = self.gameid
					player_data['Sport'] = self.sport
					player_data['Player_Type'] = self.player_type_map[dataset]
					player_data['Date'] = self.gameid[0:8]
					meta_cols = [col for col in player_data.keys()]
					for datum in data_model.keys():
						if datum[0] == '$': #Cole: prefix with $ denotes hard coded value
							player_data[datum] = datum[1:]
						elif player[datum] == True: #Cole: Convert bool to int for db write
							player_data[datum] = 1
						elif player[datum] ==False:
							player_data[datum] = 0
						elif datum == 'display_name': #Cole: this deals with the player mapping on the front end, so whats in db matches FD 
							if player[datum] in player_map.keys():
								player_data[datum] = player_map[player[datum]]
							else:
								player_data[datum] = player[datum]
						else:
							player_data[datum] = player[datum]
					data_cols = [data_model[datum] for datum in player_data.keys() if datum in data_model.keys()]
					cols = ", ".join(meta_cols + data_cols)
					data = ", ".join(['"' + unicode(v) + '"' for v in player_data.values()])
					dbo.insert_mysql('hist_player_data',cols,data)
		return self

	def parse_event_data(self,event_data,event_date): #Cole: How to generaize parsing event data for each sport?
		event_data_dict = {}
		if event_data:
			event_data_dict['event_id'] = event_data['event_id']
			event_data_dict['sport'] = event_data['sport']
			event_data_dict['start_date_time'] = event_data['start_date_time']
			event_data_dict['season_type'] = event_data['season_type']
			event_data_dict['away_team'] = event_data['away_team']['team_id']
			event_data_dict['home_team'] = event_data['home_team']['team_id']			
			event_data_dict['stadium'] = event_data['home_team']['site_name']
			home_team = event_data['home_team']['abbreviation']
			away_team = event_data['away_team']['abbreviation']
			event_date = event_date[0:4] + "-" + event_date[4:6] + "-" + event_date[6:8]
			team_dict,player_dict = ds.mlb_starting_lineups(event_date)
			try:
				event_data_dict['forecast'] = team_dict[home_team][1]
				if team_dict[home_team][0] == 'PPD':
					event_data_dict['PPD'] = True
				else:
					event_data_dict['PPD'] = False
				event_data_dict['home_starting_lineup'] = team_dict[home_team][2]
				event_data_dict['away_starting_lineup'] = team_dict[away_team][2]
			except:
				print "dont think this is a real event"
			cols = ", ".join(event_data_dict.keys())
			data = ", ".join(['"' + unicode(v) + '"' for v in event_data_dict.values()])
			dbo.insert_mysql('event_data',cols,data)
		return event_data_dict

	def get_db_gamedata(self,start_date,end_date,player):
		sql = ("SELECT hist_player_data.*, event_data.* FROM hist_player_data "
				 "INNER JOIN event_data ON hist_player_data.GameID=event_data.event_id "
				   "WHERE hist_player_data.Sport = '"+ self.sport +"' AND Player = '"+ player +"' AND Date BETWEEN '" + start_date +"' AND "
				    "'" + end_date + "' ORDER BY Date ASC")
		db_data = dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
		player_data_dict = {}
		for key,player_game in db_data.iteritems():
			player_type = player_game['Player_Type']
			player_data_map = self.inv_db_data_model[player_type]
			data_map = {key:player_data_map[key] if 'Stat' in key else key for key in player_data_map} #Cole: updated so only Stat columns change
			player_key = player_game['Player'] + '_' + player_game['Player_Type']
			if player_key in player_data_dict.keys():
				player_data_dict[player_key]['name'].append(player_key) #Cole: adding the field 'name' is required for openopts results output
				for db_key,player_data in player_game.iteritems():
					stat_key = data_map[db_key] if db_key in data_map.keys() else db_key
					try:
						player_data_dict[player_key][stat_key].append(float(player_data))#Cole: Attempt to convert data to float, else keep as string
					except:
						player_data_dict[player_key][stat_key].append(player_data)
			else:
				player_data_dict[player_key] = {}
				player_data_dict[player_key]['name'] = [player_key]
				for db_key,player_data in player_game.iteritems():
					stat_key = data_map[db_key] if db_key in data_map.keys() else db_key
					try:
						player_data_dict[player_key][stat_key] = [float(player_data)]
					except:
						player_data_dict[player_key][stat_key] = [player_data]
		return player_data_dict

	def get_stadium_data(self,prime_key = 'stadium'):
		sql = "SELECT * FROM stadium_data"
		return dbo.read_from_db(sql,[prime_key],True)

	def avg_stat(self,stats_data,include_zero = True):
		np_array = numpy.array(stats_data)
		if include_zero:
			avg =numpy.mean(np_array)
		else:
			avg =numpy.mean(np_array[numpy.nonzero(np_array)])
		if numpy.isnan(avg):
			return 0
		else:
			return avg

	def median_stat(self,stats_data,include_zero=True):
		np_array = numpy.array(stats_data)
		if include_zero:
			median =numpy.median(np_array)
		else:
			median =numpy.median(np_array[numpy.nonzero(np_array)])
		if numpy.isnan(median):
			return 0
		else:
			return median

	def trend_stat(self,stats_data):
		xi = numpy.arange(0,len(stats_data))
		matrix_ones = numpy.ones(len(stats_data))
		array = numpy.array([xi,matrix_ones])
		return numpy.linalg.lstsq(array.T,stats_data)[0][0]

	def time_between(self,start_time,end_time):
		secondsdelta = (dateutil.parser.parse(end_time) - dateutil.parser.parse(start_time)).seconds
		if  abs(secondsdelta) < 864000: #Timedelta needs to be less then 10days to ensure exclusion of rest_time between seasons
			return float(secondsdelta)
		else:
			return 0.0

	def optimal_roster(self,contest_url,confidence = 0):
		DB_parameters=Ugen.ConfigSectionMap('local text')
		player_universe = self.build_player_universe(contest_url)
		items = ([{key:value for key,value in stats_data.iteritems() if key in self.optimizer_items}
					 for player_key,stats_data in player_universe.iteritems()
					 if 'Salary' in stats_data.keys()])
		objective = 'projected_FD_points'
		if items:
			p = KSP(objective, items, goal = 'max', constraints=self.get_constraints(confidence))
			r = p.solve('glpk',iprint = 0)
			roster_data = []
			rw = 2
			sum_confidence = 0
			for player in r.xf:
				roster_data.append([player_universe[player]['FD_Position'],str(int(player_universe[player]['FD_playerid'])),str(int(player_universe[player]['MatchupID'])),str(int(player_universe[player]['TeamID']))])
				Cell("Roster",rw,1).value = player
				Cell("Roster",rw,2).value = player_universe[player]['TeamID']
				Cell("Roster",rw,3).value = player_universe[player]['FD_Position']
				Cell("Roster",rw,4).value = player_universe[player]['projected_FD_points']
				Cell("Roster",rw,5).value = player_universe[player]['confidence']
				Cell("Roster",rw,6).value = player_universe[player]['Salary']
				sum_confidence = sum_confidence + player_universe[player]['confidence']
				rw = rw + 1
			sorted_roster = sorted(roster_data, key=self.sort_positions)
			with open(DB_parameters['rostertext'],"w") as myfile: #Ian: replaced hard-coded folder path with reference to config file
				myfile.write(str(sorted_roster).replace(' ',''))
			return {'confidence':sum_confidence,'roster':sorted_roster}
		else:
			return {'confidence':0,'roster':[]}

class MLB(Sport): #Cole: data modelling may need to be refactored, might be more elegant solution
	def __init__(self):
		Sport.__init__(self,"MLB")
		self.FD_data_columns = (['FD_Position','FD_name','MatchupID','TeamID','Dummy2','Salary','PPG',
									'GamesPlayed','Dummy3','Dummy4','Injury','InjuryAge','Dummy5'])
		self.positions = {'P':1,'C':2,'1B':3,'2B':4,'3B':5,'SS':6,'OF':7}
		self.player_type_map = {'away_batters':'batter','home_batters':'batter','away_pitchers':'pitcher','home_pitchers':'pitcher'}
		self.db_data_model = collections.OrderedDict({'meta':{'gameid':'GameID','sport':'Sport','type':'Player_Type'}, #Cole: prefix with $ to denote a hard coded value
							'batter':{'display_name':'Player','position':'Position','team_abbreviation':'Team',
								'singles':'Stat1','doubles':'Stat2','triples':'Stat3','home_runs':'Stat4',
									'hits':'Stat5','rbi':'Stat6','at_bats':'Stat7','stolen_bases':'Stat8','total_bases':'Stat9','runs':'Stat10',
										'walks':'Stat11','strike_outs':'Stat12','hit_by_pitch':'Stat13'},
										  'pitcher':{'display_name':'Player','$P':'Position','team_abbreviation':'Team','win':'Stat1','era':'Stat2',
										     'whip':'Stat3','innings_pitched':'Stat4','hits_allowed':'Stat5','runs_allowed':'Stat6',
										       'earned_runs':'Stat7','walks':'Stat8','strike_outs':'Stat9','home_runs_allowed':'Stat10',
										          'pitch_count':'Stat11','pitches_strikes':'Stat12'}})
		self.inv_db_data_model = {dataset:dict(zip(self.db_data_model[dataset].values(), self.db_data_model[dataset].keys())) for dataset in self.db_data_model}
		self.data_model = ({'away_batters':self.db_data_model['batter'],'away_pitchers':self.db_data_model['pitcher'],
							'home_batters':self.db_data_model['batter'],'home_pitchers':self.db_data_model['pitcher']})
		self.event_data_model = ({'event':{'event_id':'event_id','sport':'sport','start_date_time':'start_date_time','season_type':'season_type'},
									'away_team':{'team_id':'away_team'},'home_team':{'team_id':'home_team','site_name':'stadium'}})

		self.optimizer_items = ['name','Player_Type','Salary','P','C','1B','2B','3B','SS','OF','projected_FD_points','confidence']
		self.median_stat_chunk_size = {'batter':13,'pitcher':15} #Cole: might need to play with these
		self.model_version = '0.0.0001'
		self.model_description = "Lasso Linear regression on median_FD and Stadium HR factors"
		self.model_mean_score = -1.70
		self.contest_types = {"{'50_50': 1, 'standard': 1}":-10}

	def get_constraints(self,confidence=0):
		return lambda values : (
								values['Salary'] <= 35000,
							    values['P'] == 1,
							    values['C'] == 1,
							    values['1B'] == 1,
							    values['2B'] == 1,
							    values['3B'] == 1,
							    values['SS'] == 1,
							    values['OF'] == 3,
							    values['confidence'] >=confidence)

	def sort_positions(self,sort_list):
		return self.positions[sort_list[0]]

	def build_model_dataset(self,hist_data):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
		player_type = hist_data['Player_Type'][-1]
		FD_points = self.FD_points(hist_data)
		feature_dict = {}
		feature_dict['FD_points'] = []
		feature_dict['FD_median'] = []
		feature_dict['HR_ballpark_factor'] = [] #Cole:tempory parameter until batter handedness is figured out
		#feature_dict['rest_time'] = []
		#feature_dict['LHB_ballpark_factor'] = [] #Cole: do we split feature into RH\LH based on batter?
		#feature_dict['RHB_ballpark_factor'] = []
		#feature_dict['day_of_month'] = []
		for indx,FD_point in enumerate(FD_points):
			reverse_index = len(FD_points)-indx -1
			try:
				median_chunk_list = [FD_points[chunk_indx] for chunk_indx in range(reverse_index-self.median_stat_chunk_size[player_type],reverse_index-1)]
				feature_dict['FD_points'].append(FD_points[reverse_index]) #Cole:Need to do some testing on most informative hist FD points data feature(ie avg, trend, combination)
				feature_dict['FD_median'].append(self.median_stat(median_chunk_list,False))
				feature_dict['HR_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['HR']))
				#feature_dict['rest_time'].append(self.time_between(hist_data['start_date_time'][reverse_index-1],hist_data['start_date_time'][reverse_index])) #this will include rest_days between season, need to remove
				#feature_dict['LHB_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['LHB']))
				#feature_dict['RHB_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['RHB']))
				#feature_dict['day_of_month'].append(int(str(hist_data['Date'][reverse_index])[8:10]))#Cole: used as spurious feature
			except IndexError:
				break
		return feature_dict

	def get_parameters(self,features,player):
		player_id =player.split("_")
		player_name = player_id[0]
		player_type = player_id[1]
		player_gtd = game_time_data = ds.mlb_starting_lineups()[1][player_name]
		team_abr = player_gtd[2]
		stadium_data = self.get_stadium_data('home_team')[team_abr]
		parameters = []
		for feature in features:
			if feature == 'rest_time':
				parameters.append(86400) #Cole: default 1 day for now
			elif feature == 'FD_median':
				 parameters.append(self.median_stat(self.player_model_data['FD_points'][-self.median_stat_chunk_size[player_type]:]))
			elif feature == 'HR_ballpark_factor':
				parameters.append(float(stadium_data['HR']))
			elif feature == 'temp':
				parameters.append(stadium_data['forecast'].split('oF')[0]) 
		return parameters

	def FD_points(self, data):
		if data['Player_Type'][-1] == 'batter':
			FD_points = (numpy.array(data['singles'])*1+numpy.array(data['doubles'])*2+numpy.array(data['triples'])*3+
							numpy.array(data['home_runs'])*4+numpy.array(data['rbi'])*1+numpy.array(data['runs'])*1+
								numpy.array(data['walks'])*1+numpy.array(data['stolen_bases'])*1+
								numpy.subtract(numpy.array(data['at_bats']),numpy.array(data['hits']))*-.25)
		else:
			FD_points= (numpy.array(data['win'])*4+numpy.array(data['earned_runs'])*-1+
								numpy.array(data['strike_outs'])*1+numpy.array(data['innings_pitched'])*1)
		return FD_points

	def build_player_universe(self,contest_url): #Cole: this desperately needs documentation. Entire data structure needs documentation
		team_map = Ugen.excel_mapping("Team Map",9,6)
		FD_player_data = fdo.get_FD_player_dict(contest_url)#Cole:need to build some sort of test that FD_names and starting lineup names match
		teams,starting_lineups = ds.mlb_starting_lineups() #Cole: need to write verification that all required teams have lineups
		missing_lineups = [team for team in teams.keys() if len(teams[team][2])<8] #Cole: this whole method needs to be split out into more reasonable functions
		contest_teams = fdo.get_contest_teams(contest_url) #Cole: This needs mapping
		FD_missing_lineups = [team for team in contest_teams if team_map[team] in missing_lineups]
		print FD_missing_lineups
		if FD_missing_lineups: #Check that no required lineups are missing
			return {}
		starting_players = [player for player in starting_lineups.keys() if 'PPD' not in starting_lineups[player][1]] #Cole: is the PPD working?
		FD_starting_player_data = {FD_playerid:data for FD_playerid,data in FD_player_data.iteritems() if data[1] in starting_players} #data[1] if FD_player_name
		player_universe = {}
		for FD_playerid,data in FD_starting_player_data.iteritems():
			db_data = self.get_db_gamedata("20120401","20170422",data[1])
			if data[0] == 'P': #Cole: If this can be generalized (ie sport player type map, the entire function can be generalized as a Sport method)
				player_type = 'pitcher'
			else:
				player_type = 'batter'
 			player_key = data[1]+ '_' + player_type	
			if player_key in db_data.keys():
				player_universe[player_key] = {}
				player_universe[player_key]['FD_playerid'] = FD_playerid
				projected_FD_points = self.FD_points_model(player_key,db_data[player_key],False)
				player_universe[player_key]['projected_FD_points'] = projected_FD_points.projected_points
				player_universe[player_key]['confidence'] = projected_FD_points.confidence
				player_universe[player_key]['Player_Type'] = player_type
				player_universe[player_key]['name'] = player_key
				for indx,FD_data in enumerate(data):
					try:
						player_universe[player_key][self.FD_data_columns[indx]] = float(FD_data)
					except ValueError:
						player_universe[player_key][self.FD_data_columns[indx]] = FD_data
				position_map = {key:1 if key == player_universe[player_key]['FD_Position'] else 0 for key in self.positions.keys()}
				tmp_dict = position_map.copy()
				player_universe[player_key].update(tmp_dict)
			else:
				print player_key + ' not in db_player_data'
		return player_universe
