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

class Sport(): #Cole: Class has functions that should be stripped out and place into more appropriate module/class
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def FD_point_model(self,hist_data):
		for player,data in hist_data.iteritems():
			player_model_data = self.build_model_dataset(data)
			features = Model.Model().prune_features(player_model_data,'FD_points','day_of_month')
			print features
		return player_model_data

	def events(self,event_date):
		self.gameid = None
		return XMLStats.main(self,'events',{'sport':self.sport,'date':event_date})['event']

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

	def get_daily_game_data(self,event_dates,store = False):#Cole:event_date format is yyyyMMdd, must be a list
		for event_date in event_dates:
			day_events = self.events(event_date)
			event_list = ([game['event_id'] for game in day_events if game['event_status'] == 'completed'
							 and game['season_type'] == 'regular' or 'post'])
			all_game_data = {}
			for game_id in event_list:
				self.gameid = game_id
				if store == False:
					game_data = XMLStats.main(self,'boxscore',None)
				elif store == True and self.gameid not in self.gameids().all_gameids: #Cole: this will make it so this method of the class can only be used if Sport class generated from individual sport class (ie MLB, NHL)
					print "loading " + game_id
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
						else:
							player_data[datum] = player[datum]
					data_cols = [data_model[datum] for datum in player_data.keys() if datum in data_model.keys()]
					cols = ", ".join(meta_cols + data_cols)
					data = ", ".join(['"' + unicode(v) + '"' for v in player_data.values()])
					dbo.insert_mysql('hist_player_data',cols,data)
		return self

	def get_db_gamedata(self): #Cole: How do we make it so this only queries X number of games?
		sql = "SELECT * FROM hist_player_data WHERE Sport = '"+ self.sport +"' ORDER BY Date Desc"
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

	def avg_stat(self,stats_data):
		np_array = numpy.array(stats_data)
		avg =numpy.mean(np_array)
		if numpy.isnan(avg):
			return 0
		else:
			return avg

	def trend_stat(self,stats_data):
		xi = numpy.arange(0,len(stats_data))
		matrix_ones = numpy.ones(len(stats_data))
		array = numpy.array([xi,matrix_ones])
		return numpy.linalg.lstsq(array.T,stats_data)[0][0]

	def get_FD_player_dict(self,contest_url):
		return ast.literal_eval(Uds.parse_html(contest_url,"FD.playerpicker.allPlayersFullData = ",";"))

	def optimal_roster(self,forecasted_player_universe):
		items = ([{key:value for key,value in stats_data.iteritems() if key in self.optimizer_items}
					 for player_key,stats_data in forecasted_player_universe.iteritems()
					 if 'Salary' in stats_data.keys()])
		objective = 'FD_points' #Cole: update this to forecast_points once model is built
		p = KSP(objective, items, goal = 'max', constraints=self.optimizer_constraints)
		r = p.solve('glpk',iprint = 0)
		return r

class MLB(Sport): #Cole: data modelling may need to be refactored, might be more elegant solution
	def __init__(self):
		Sport.__init__(self,"MLB")
		self.FD_data_columns = (['FD_Position','FD_name','MatchupID','TeamID','Dummy2','Salary','PPG',
									'GamesPlayed','Dummy3','Dummy4','Injury','InjuryAge','Dummy5'])
		self.positions = ['P','C','1B','2B','3B','SS','OF']
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
		self.optimizer_constraints = lambda values : (
    									values['Salary'] <= 55000,
									    values['P'] == 1,
									    values['C'] == 1,
									    values['1B'] == 1,
									    values['2B'] == 1,
									    values['3B'] == 1,
									    values['SS'] == 1,
									    values['OF'] == 3,)
		self.optimizer_items = ['name','Player','Player_Type','Salary','P','C','1B','2B','3B','SS','OF','FD_points']

	def build_model_dataset(self,hist_data):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
		FD_points = self.FD_points(hist_data)
		feature_dict = {}
		feature_dict['FD_points'] = []
		feature_dict['five_day_avg'] = []
		feature_dict['five_day_trend'] = []
		feature_dict['day_of_month'] = []
		for indx,FD_point in enumerate(FD_points):
			reverse_index = len(FD_points)-indx
			try:
				chunk_list = [FD_points[chunk_indx] for chunk_indx in range(reverse_index-5,reverse_index-1)]
				feature_dict['FD_points'].append(FD_point)
				feature_dict['five_day_avg'].append(self.avg_stat(chunk_list))
				feature_dict['five_day_trend'].append(self.trend_stat(chunk_list))
				feature_dict['day_of_month'].append(int(str(hist_data['Date'][indx])[6:8]))
			except IndexError:
				break
		return feature_dict

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
		db_player_data = self.get_db_gamedata() #Cole: Stats need to be summarized here (ie avg, max, what ever maths)
		FD_player_data = self.get_FD_player_dict(contest_url)
		for FD_playerid,data in FD_player_data.iteritems():
			FD_data_index = 0
			FD_name = data[1]
			if data[0] == 'P': #Cole: If this can be generalized (ie sport player type map, the entire function can be generalized as a Sport method)
				player_type = 'pitcher'
			else:
				player_type = 'batter'
			player_key = data[1] + '_' + player_type
			try:
				db_player_data[player_key]['FD_playerid'] = FD_playerid
				for FD_data in data:
					try:
						db_player_data[player_key][self.FD_data_columns[FD_data_index]] = float(FD_data)
					except ValueError:
						db_player_data[player_key][self.FD_data_columns[FD_data_index]] = FD_data
					FD_data_index = FD_data_index + 1
				position_map = {key:1 if key == db_player_data[player_key]['FD_Position'] else 0 for key in self.positions}
				tmp_dict = position_map.copy()
				db_player_data[player_key].update(tmp_dict)
			except KeyError: #Cole: need to map mis-matched names
				print player_key + ' not in db_player_data'
		return db_player_data



		