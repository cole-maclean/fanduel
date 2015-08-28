import data_scrapping as ds
import data_scrapping_utils as Uds
import database_operations as dbo
import string_utils as Ustr
import collections
import XMLStats
import os
import math
import numpy
import ast
from openopt import *
import Model
import pandas
import datetime, dateutil.parser
import general_utils as Ugen
import FD_operations as fdo
from sklearn.cross_validation import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction import DictVectorizer
import time
import weather
import datetime as dt
import TeamOdds

class Sport(): #Cole: Class has functions that should be stripped out and place into more appropriate module/class
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def FD_points_model(self,player,hist_data,starting_lineups,weather_forecast=False,visualize = True,odds_dict=False,date=False):
		FD_projection= collections.namedtuple("FD_projection", ["projected_points", "confidence"])
		self.player_model_data = self.build_model_dataset(hist_data,starting_lineups,player)
		player_model = Model.Model(self.player_model_data,player)
		print '%s modelled' % player
		player_model.FD_points_model(visualize)
		if player_model.modelled:	#Cole: need to develop parameters for each player
			parameters = self.get_parameters(player_model.feature_labels,player,starting_lineups,hist_data,weather_forecast,odds_dict,date)
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
		return dbo.read_from_db(sql,["event_id"],True)

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
	
	def modify_db_data(self,start_date,end_date,modify_dict): # modify_dict in form {hist_player_data:[column1,column2],event_data:[column1,column2,...]}
		event_dates = [d.strftime('%Y%m%d') for d in pandas.date_range(start_date,end_date)]
		db_eventids = self.get_db_event_data()
		# print db_eventids
		# os.system('pause')
		team_map=Ugen.mlb_map(11,4)
		#player_map = Ugen.mlb_map(1,0) #Ian: this player map isnt working for some names...
		player_map = Ugen.excel_mapping("Player Map",6,5) 
		for event_date in event_dates:
			# odds_dict=TeamOdds.vegas_odds_sportsbook(event_date)
			team_dict,player_dict = ds.mlb_starting_lineups(event_date)
			day_events = self.events(event_date)
			event_list = ([game['event_id'] for game in day_events if game['event_status'] == 'completed'
						 and game['season_type'] == 'regular' or 'post'])
			for indx,game_id in enumerate(event_list):
				if game_id in db_eventids.keys():
					print "modifying " + game_id
					self.gameid = game_id
					if "event_data" in modify_dict:
						self.modify_event_data(day_events,indx,event_date,team_dict,modify_dict['event_data'],team_map)
					if 'hist_player_data' in modify_dict: #Ian: may be put this part below in separate function? function would return cols,vals. Right now it modifies all columns.
						boxscore_data = XMLStats.main(self,'boxscore',None)
						if boxscore_data != None and boxscore_data:
							self.modify_boxscore_data(boxscore_data,player_map,modify_dict['hist_player_data'])
							print "hist_player_data successfully modified for " + game_id 
				else:
					print "event %s not in database. event not modified" % (game_id)
		return 

	def modify_event_data(self,day_events,indx,event_date,team_dict,modify_cols,team_map): #Ian: pass in odds dict?
		event_data_dict={}
		away_team=team_map[day_events[indx]['away_team']['team_id']]
		home_team=team_map[day_events[indx]['home_team']['team_id']]
		if "vegas_odds" in modify_cols:
			event_data_dict['vegas_odds']={}
			event_data_dict['vegas_odds'][away_team]=odds_dict[away_team]
			event_data_dict['vegas_odds'][home_team]=odds_dict[home_team]
		if "wunderground_forecast" in modify_cols:
			event_date = event_date[0:4] + "-" + event_date[4:6] + "-" + event_date[6:8]
			if home_team in team_dict and away_team in team_dict:
				if 'PPD' not in team_dict[home_team]['start_time']:
					wunderground_dict=weather.weather_hist(home_team,event_date,team_dict[home_team]['start_time'])
				try:			
					event_data_dict['wunderground_forecast']=wunderground_dict
					event_data_dict['wind']=str(wunderground_dict['wind']['wind_dir'])+'_'+str(wunderground_dict['wind']['wind_speed'])
				except:
					print 'no weather data for %s' % event_data_dict['event_id']
		if "home_starting_lineup" or "away_starting_lineup" in modify_cols:
				event_data_dict['home_starting_lineup'] = team_dict[home_team]['lineup']
				event_data_dict['away_starting_lineup'] = team_dict[away_team]['lineup']
				event_data_dict['forecast'] = team_dict[home_team]['weather_forecast']
		cols = ", ".join(event_data_dict.keys())
		data = ", ".join(['"' + unicode(v) + '"' for v in event_data_dict.values()])
		try:
			dbo.modify_db_table('event_data',cols,data,['event_id'],[game_id])
			print 'event_id table - event: %s was updated' % game_id
		except:
			print 'event: %s was not updated' % game_id
		return
	
	def modify_boxscore_data(self,boxscore_data,player_map,modify_cols): #Right now it modifies all columns in hist_player_data
		for dataset,data_model in self.data_model.iteritems():
			for player in boxscore_data[dataset]:
				if self.player_type_map[dataset]=='pitcher':
					continue
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
				# cols = ", ".join(meta_cols + data_cols)
				# data = ", ".join(['"' + unicode(v) + '"' for v in player_data.values()])
				cols = [meta_cols + data_cols][0]
				data = ['"' + unicode(v) + '"' for v in player_data.values()]
				data = [s.replace("'","''") for s in data]
				try:
					dbo.modify_db_table('hist_player_data',cols,data,['GameID',"Player","Player_Type"],[player_data['GameID'],player_data['display_name'].replace("'","''"),player_data['Player_Type']])
					# print "hist_player_data was updated for event: %s player: %s" % (game_id,player_data['display_name'])
				except:
					print 'event: %s was not updated for player %s' % (game_id,player_data['display_name'])
		return

	def get_daily_game_data(self,start_date,end_date,store = False):
		event_dates = [d.strftime('%Y%m%d') for d in pandas.date_range(start_date,end_date)]
		#db_eventids = self.get_db_event_data()
		# xml_name_list=[] #Ian: part of player mapping
		for event_date in event_dates:
			odds_dict= {}#ds.historical_vegas_odds_sportsbook(event_date) #Ian: only call it once for speed purposes
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
					self.parse_event_data(day_events[indx],event_date,odds_dict) 
					game_data = XMLStats.main(self,'boxscore',None)
					if game_data != None:
					 	parsed_data = self.parse_boxscore_data(game_data)
					 	# xml_name_list.extend(player for player in parsed_data if player not in xml_name_list)
					print game_id + " succesfully loaded"
				else:
					game_data = None
				if game_data:
					all_game_data[game_id] = game_data
		return all_game_data #xml_team_list #Ian: part of player mapping

	def parse_boxscore_data(self,boxscore_data):
		player_map = Ugen.excel_mapping("Player Map",6,5)
		# player_name_list=[] #Ian: Part of player mapping
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
					data.replace("'","''")
					# player_name_list.append(player_data['display_name']) #Ian: part of player mapping
					dbo.insert_mysql('hist_player_data',cols,data)
		return self

	def parse_event_data(self,event_data,event_date,odds_data): #Cole: How to generalize parsing event data for each sport?
		event_data_dict = {}
		if event_data:
			event_data_dict['event_id'] = event_data['event_id']
			event_data_dict['sport'] = event_data['sport']
			event_data_dict['start_date_time'] = event_data['start_date_time']
			event_data_dict['season_type'] = event_data['season_type']
			event_data_dict['away_team'] = event_data['away_team']['team_id']
			event_data_dict['home_team'] = event_data['home_team']['team_id']
			home_team = event_data['home_team']['abbreviation']
			away_team = event_data['away_team']['abbreviation']
			event_data_dict['vegas_odds']={}
			try:
				event_data_dict['vegas_odds'][home_team]=odds_data[home_team]
				event_data_dict['vegas_odds'][away_team]=odds_data[away_team]
			except KeyError:
				print 'no vegas odds for event: %s' % event_data['event_id']
			event_data_dict['stadium'] = event_data['home_team']['site_name']
			event_date = event_date[0:4] + "-" + event_date[4:6] + "-" + event_date[6:8]
			team_dict,player_dict = ds.mlb_starting_lineups(event_date)
			if home_team in team_dict and away_team in team_dict:
				if 'PPD' not in team_dict[home_team]['start_time']:
					wunderground_dict=weather.weather_hist(home_team,event_date,team_dict[home_team]['start_time'])
				try:			
					event_data_dict['wunderground_forecast']=wunderground_dict
					event_data_dict['wind']=str(wunderground_dict['wind']['wind_dir'])+'_'+str(wunderground_dict['wind']['wind_speed'])
				except:
					print 'no weather data for %s' % event_data_dict['event_id']
				event_data_dict['home_starting_lineup'] = team_dict[home_team]['lineup']
				event_data_dict['away_starting_lineup'] = team_dict[away_team]['lineup']
				event_data_dict['forecast'] = team_dict[home_team]['weather_forecast']
				if team_dict[home_team]['start_time'] == 'PPD':
					event_data_dict['PPD'] = True
				else:
					event_data_dict['PPD'] = False
			else:
				print 'no data from baseball lineups website for this event'
			cols = ", ".join(event_data_dict.keys())
			data = ", ".join(['"' + unicode(v) + '"' for v in event_data_dict.values()])
			dbo.insert_mysql('event_data',cols,data)
		return event_data_dict

	def get_db_gamedata(self,player,start_date="",end_date="",GameID=""): #Updated to get by GameID or by Dates
		if start_date:
			sql = ("SELECT hist_player_data.*, event_data.* FROM hist_player_data "
					 "INNER JOIN event_data ON hist_player_data.GameID=event_data.event_id "
					   "WHERE hist_player_data.Sport = '"+ self.sport +"' AND Player = '"+ player.replace("'","''") +"' AND Date BETWEEN '" + start_date +"' AND "
					    "'" + end_date + "' ORDER BY Date ASC") #Ian: modified SQL statement so it can read names like "Travis D'Arnaud" from DB
		else:
			sql = ("SELECT hist_player_data.* FROM hist_player_data "
					"WHERE Player = '"+ player.replace("'","''") +"' AND "
					"GameID = '"+ GameID.replace("'","''") +"'")
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

	def optimal_roster(self,contest_url,confidence = 0,date=False,contestID=False): #Ian: added optional date for backtesting
		DB_parameters=Ugen.ConfigSectionMap('local text')
		if date:
			player_universe=self.hist_build_player_universe(date,contestID)
		else:
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
			if date:
				roster_dict={}
				for player in r.xf:
					roster_dict[player]={}
					roster_dict[player]['FD_Position']=player_universe[player]['FD_Position']
					roster_dict[player]['projected_FD_points']=player_universe[player]['projected_FD_points']
					roster_dict[player]['confidence']=player_universe[player]['confidence']
					roster_dict[player]['Salary']=player_universe[player]['Salary']
				return roster_dict,len(player_universe)
			else:
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
										'walks':'Stat11','strike_outs':'Stat12','hit_by_pitch':'Stat13','plate_appearances':'Stat14','obp':'Stat15','slg':'Stat16','ops':'Stat17','sac_flies':'Stat18'},
										  'pitcher':{'display_name':'Player','$P':'Position','team_abbreviation':'Team','win':'Stat1','era':'Stat2',
										     'whip':'Stat3','innings_pitched':'Stat4','hits_allowed':'Stat5','runs_allowed':'Stat6',
										       'earned_runs':'Stat7','walks':'Stat8','strike_outs':'Stat9','home_runs_allowed':'Stat10',
										          'pitch_count':'Stat11','pitches_strikes':'Stat12','intentional_walks':'Stat13','errors':'Stat14','hits_allowed':'Stat15','wild_pitches':'Stat16'}})
		self.inv_db_data_model = {dataset:dict(zip(self.db_data_model[dataset].values(), self.db_data_model[dataset].keys())) for dataset in self.db_data_model}
		self.data_model = ({'away_batters':self.db_data_model['batter'],'away_pitchers':self.db_data_model['pitcher'],
							'home_batters':self.db_data_model['batter'],'home_pitchers':self.db_data_model['pitcher']})
		self.event_data_model = ({'event':{'event_id':'event_id','sport':'sport','start_date_time':'start_date_time','season_type':'season_type'},
									'away_team':{'team_id':'away_team'},'home_team':{'team_id':'home_team','site_name':'stadium'}})

		self.optimizer_items = ['name','Player_Type','Salary','P','C','1B','2B','3B','SS','OF','projected_FD_points','confidence']
		self.median_stat_chunk_size = {'batter':13,'pitcher':15} #Cole: might need to play with these
		self.model_version = '0.0.0001'
		self.features={'pitcher':['pred_strikeouts','FD_median'],'batter':['FD_median']}
		self.model_description = "Lasso Linear regression and %s" % self.features
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
	
	def batter_lineup_stats(self,date,lineup_data,player_arm):
		lineup_stats_dict={}
		hist_lineup_strikeout_rate=[]
		team_map=Ugen.mlb_map(11,4)
		avg_plate_appearances={'1':0.12239,'2':0.11937,'3':0.11683,'4':0.11417,'5':0.11161,'6':0.10848,'7':0.10555,'8':0.10243,'9':0.09917} #move this to sport class init function
		avg_plate_appearances_list=[]
		for player in lineup_data[0]:
			hist_strikeout_rate=[]
			hist_strikeout_rate_HA_splits=[]
			if player.split("_")[1]!='pitcher':
				player_data=self.get_db_gamedata(player.split("_")[0],"20130301",Ugen.previous_day(str(date)).replace("-","")) #may need to play with how much data you use to get batter's K avg
				try:
					player_data=player_data[player] 
				except KeyError:
					#print 'player %s not in db, needs new player map' % player
					continue
				events=[event for event in player_data['event_id']]
				for indx,event in enumerate(events):
					try:
						reverse_index = len(events)-indx-1
						team=player_data['Team'][reverse_index]
						home_away=lineup_data[1] #This tells us whether the batter facing the current pitcher is at home or away. We want his K% splits for H/A
						home_team=team_map[player_data['home_team'][reverse_index]]
						try:
							if team==home_team:
								matchup='home'
								opposing_lineup=ast.literal_eval(player_data['away_starting_lineup'][reverse_index])
							else:
								matchup='away'
								opposing_lineup=ast.literal_eval(player_data['home_starting_lineup'][reverse_index])
							opposing_pitcher_hand=[opposing_player_data['arm'] for opposing_player,opposing_player_data in opposing_lineup.iteritems() if 'pitcher' in opposing_player][0]

							if matchup==home_away and (player_arm==opposing_pitcher_hand or player_arm=='S'): #
								strike_outs=player_data['strike_outs'][reverse_index]
								plate_appearances=player_data['plate_appearances'][reverse_index]
								if plate_appearances>0:
									strikeout_rate=float(strike_outs/plate_appearances)
									if numpy.isnan(strikeout_rate):
										print "isnan error for calculated strikeout rate %s,%s" % (player,player_data['GameID'][reverse_index])
										hist_strikeout_rate.append(0.200)
									else:
										hist_strikeout_rate.append(strikeout_rate)
						except ValueError: #This is when there is no starting lineups data (usually)
							#print 'Value error %s %s' %(player_data["Date"][reverse_index],player)
							pass
					except IndexError:
						print 'index error'
						break
				batting_order=lineup_data[0][player]['batting_order']
				if len(hist_strikeout_rate)>2: #say we need 3 min values to incorporate the players strikeout rate into feature
					hist_lineup_strikeout_rate.append(float(avg_plate_appearances[batting_order]*numpy.mean(hist_strikeout_rate)))
					avg_plate_appearances_list.append(avg_plate_appearances[batting_order])
		lineup_stats_dict['strikeout_rate']=numpy.sum(hist_lineup_strikeout_rate)/numpy.sum(avg_plate_appearances_list)
		#print lineup_stats_dict['strikeout_rate']
		return lineup_stats_dict

	def season_averages(self,hist_data,player): #put this in mlb class? Specific to pitcher strikeouts right now, can change to generalize based on demand.
		team_map=Ugen.mlb_map(11,4) #Ian: make a function that does some of these things below
		try:
			s2015_pitcher_IP=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015'and (player in AT or player in HT)])
			s2015_pitcher_IP_home=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2015' and (player in AT or player in HT) and team==team_map[home_team]])
			s2015_pitcher_IP_away=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2015' and (player in AT or player in HT) and team==team_map[away_team]])			
		except:
			s2015_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015'and IP>3])	
			s2015_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[home_team]])
			s2015_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[away_team]])				
		try:
			s2014_pitcher_IP=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014'and (player in AT or player in HT)])
			s2014_pitcher_IP_home=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[home_team]])
			s2014_pitcher_IP_away=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[away_team]])			
		except:
			s2014_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014'and IP>3])	
			s2014_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[home_team]])
			s2014_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[away_team]])
		try:
			s2013_pitcher_IP=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013'and (player in AT or player in HT)])
			s2013_pitcher_IP_home=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[home_team]])
			s2013_pitcher_IP_away=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[away_team]])			
		except:
			s2013_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013'and IP>3])	
			s2013_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[home_team]])
			s2013_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[away_team]])
		season_averages={
			"league_K%_avg": {
						'2015':0.234,
						'2014':0.204,
						'2013':0.199,
			},
			'pitcher_K9_avg': {
						'2015':numpy.mean([float(SO/IP*9) for SO,date,IP in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched']) if str(date).split("-")[0]=='2015' and IP>3]),
						'2014':numpy.mean([float(SO/IP*9) for SO,date,IP in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched']) if str(date).split("-")[0]=='2014' and IP>3]),
						'2013':numpy.mean([float(SO/IP*9) for SO,date,IP in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched']) if str(date).split("-")[0]=='2013' and IP>3]),
			},
			'pitcher_K9_avg_ha': {
						'2015_home':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[home_team]]),
						'2015_away':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[away_team]]),
						'2014_home':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[home_team]]),
						'2014_away':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[away_team]]),
						'2013_home':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[home_team]]),
						'2013_away':numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[away_team]]),
			},
			'pitcher_IP_avg': {
						'2015':s2015_pitcher_IP,
						'2014':s2014_pitcher_IP,
						'2013':s2013_pitcher_IP,
			},
			'pitcher_IP_avg_ha': {
						'2015_home':s2015_pitcher_IP_home,
						'2015_away':s2015_pitcher_IP_away,
						'2014_home':s2014_pitcher_IP_home,
						'2014_away':s2014_pitcher_IP_away,
						'2013_home':s2013_pitcher_IP_home,
						'2013_away':s2013_pitcher_IP_away,
			}
		}
		return season_averages
	
	def build_model_dataset(self,hist_data,starting_lineups,player):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
		print 'now building dataset for %s' % player
		player_arm=starting_lineups[player]['arm']
		team_map=Ugen.mlb_map(11,4)
		player_type = hist_data['Player_Type'][-1]
		FD_points = self.FD_points(hist_data)
		feature_dict = {}
		if player.split("_")[1]=='batter':
			feature_dict['FD_points'] = []
			feature_dict['FD_median'] = []
			feature_dict['op_pitcher_arm'] = []
			feature_dict['op_pitcher_strikeouts'] = []
			feature_dict['op_pitcher_era'] = []
		if player.split("_")[1]=='pitcher':
			#feature_dict['moneyline'] = []
			feature_dict['FD_points'] = []
			feature_dict['FD_median'] = []
			#feature_dict['proj_run_total']=[]
			# feature_dict['strikeouts']=[]
			feature_dict['pred_strikeouts']=[]
			season_averages=self.season_averages(hist_data,player)
			print season_averages['pitcher_IP_avg_ha']
		# feature_dict['wind_dir'] = []
		#feature_dict['wind_speed'] = []
		#feature_dict['temp']=[]
		#feature_dict['humidity']=[]
		#feature_dict['rest_time'] = []
		#feature_dict['BH_ballpark_factor']=[]
		feature_dict['HR_ballpark_factor'] = [] #Cole:tempory parameter until batter handedness is figured out
		#feature_dict['day_of_month'] = []
		for indx,FD_point in enumerate(FD_points):
			reverse_index = len(FD_points)-indx -1
			# if hist_data['home_starting_lineup'][reverse_index] and hist_data['away_starting_lineup'][reverse_index]:
			# 	if player not in hist_data['home_starting_lineup'][reverse_index] and player not in hist_data['away_starting_lineup'][reverse_index]:
			# 		continue
			# if player.split("_")[1]=='pitcher' and 'strikeouts' in feature_dict:			
			# 	if '2013-04' in str(hist_data['Date'][reverse_index]): #Ian: added this since batter_lineup_stats features wont be accurate for older dates (since htey pull historical data starting from date)
			# 		break
			
			try:
				team=hist_data['Team'][reverse_index]
				home_team=team_map[hist_data['home_team'][reverse_index]]
				away_team=team_map[hist_data['away_team'][reverse_index]]	
				median_chunk_list = [FD_points[chunk_indx] for chunk_indx in range(reverse_index-self.median_stat_chunk_size[player_type],reverse_index-1)]
				#if player.split("_")[1]=='batter':
				# feature_dict['FD_points'].append(FD_points[reverse_index]) #Cole:Need to do some testing on most informative hist FD points data feature(ie avg, trend, combination)
				# feature_dict['FD_median'].append(self.median_stat(median_chunk_list,False))
				#feature_dict['rest_time'].append(self.time_between(hist_data['start_date_time'][reverse_index-1],hist_data['start_date_time'][reverse_index])) #this will include rest_days between season, need to remove
				feature_dict['HR_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['HR']))
				feature_dict['FD_points'].append(FD_points[reverse_index]) #Cole:Need to do some testing on most informative hist FD points data feature(ie avg, trend, combination)
				feature_dict['FD_median'].append(self.median_stat(median_chunk_list,False))
				if player.split("_")[1]=='batter':
					try:
						if player in ast.literal_eval(hist_data['away_starting_lineup'][reverse_index]).keys():
							op_pitcher_data = {player:data for player,data in ast.literal_eval(hist_data['home_starting_lineup'][reverse_index]).iteritems() if 'pitcher' in player}
						else:
							op_pitcher_data = {player:data for player,data in ast.literal_eval(hist_data['away_starting_lineup'][reverse_index]).iteritems() if 'pitcher' in player}
						op_pitcher = op_pitcher_data.keys()[0].split("_")[0]
						if op_pitcher_data[op_pitcher + '_pitcher']['arm'] == 'R':
							feature_dict['op_pitcher_arm'].append(1)
						else:
							feature_dict['op_pitcher_arm'].append(0)
						pitcher_data = self.get_db_gamedata(op_pitcher,GameID=hist_data['GameID'][reverse_index])
						if op_pitcher + '_pitcher' in pitcher_data.keys():
							feature_dict['op_pitcher_era'].append(pitcher_data[op_pitcher + '_pitcher']['era'][0])
							feature_dict['op_pitcher_strikeouts'].append(pitcher_data[op_pitcher + '_pitcher']['strike_outs'][0])
						else:
							print op_pitcher +  " not in db"
							feature_dict['op_pitcher_era'].append(3) #What #'s to use if pitcher doesnt exist?'
							feature_dict['op_pitcher_strikeouts'].append(3)
					except:
						feature_dict['op_pitcher_arm'].append(1)
						feature_dict['op_pitcher_era'].append(3) #What #'s to use if pitcher doesnt exist?'
						feature_dict['op_pitcher_strikeouts'].append(3)

				# if player.split("_")[1]=='batter':
				#  	if player_arm=='L':
				#  		feature_dict['BH_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['LHB']))
				#  	else: #Accounts for switch hitters
				#  		feature_dict['BH_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['RHB']))
				# # 		#feature_dict['HR_ballpark_factor'].append(float(self.get_stadium_data()[hist_data['stadium'][reverse_index]]['HR']))
				
				# odds_data_raw=hist_data['vegas_odds'][reverse_index]				

				if player.split("_")[1]=='pitcher':
					if hist_data['home_starting_lineup'][reverse_index] and hist_data['away_starting_lineup'][reverse_index]: #If there is lineup data for given evenet
						if player not in hist_data['home_starting_lineup'][reverse_index] and player not in hist_data['away_starting_lineup'][reverse_index]: #Check if they werent starting if they werent starting
							#print 'player %s did not start on %s for team %s' %(player,hist_data['Date'][reverse_index],team)
							continue #skip to next iteration
					else: #this means there is no lineup data
						continue
					#feature_dict['FD_points'].append(FD_points[reverse_index]) #Cole:Need to do some testing on most informative hist FD points data feature(ie avg, trend, combination)
					#feature_dict['FD_median'].append(self.median_stat(median_chunk_list,False))
					
														#VEGAS ODDS FEATURES
					# try:
					# 	odds_data=ast.literal_eval(odds_data_raw)[team]
					# 	try:
					# 		if odds_data['moneyline']>5: #Ian: check if value is nothing
					# 			feature_dict['moneyline'].append(odds_data['moneyline'])
					# 		else:
					# 			feature_dict['moneyline'].append(50)
					# 	except:
					# 		print 'no moneyline data available for event: %s' % hist_data['event_id'][reverse_index]
					# 		# print odds_data
					# 		# os.system('pause')
					# 		feature_dict['moneyline'].append(50)
					# 	try:
					# 		if odds_data['proj_run_total']>0:
					# 			feature_dict['proj_run_total'].append(odds_data['proj_run_total'])
					# 		else:
					# 			feature_dict['proj_run_total'].append(3)
					# 	except:
					# 		print 'no projected run total for this event: %s' % hist_data['event_id'][reverse_index]
					# 		feature_dict['proj_run_total'].append(3)
					# except:
					# 	print 'malformed vegas_odds string/nonetype for event: %s' % hist_data['event_id'][reverse_index]
					# 	feature_dict['moneyline'].append(50)
					# 	feature_dict['proj_run_total'].append(3)
					
														#PITCHER STRIKEOUT PREDICTOR FEATURE
					# feature_dict['strikeouts'].append(hist_data['strike_outs'][reverse_index])
					try:
						year=str(hist_data['Date'][reverse_index]).split("-")[0]
						if team==home_team:
							year_team=str(hist_data['Date'][reverse_index]).split("-")[0]+"_home"
							lineup_data=[ast.literal_eval(hist_data['away_starting_lineup'][reverse_index]),'away']
						elif team==away_team:
							lineup_data=[ast.literal_eval(hist_data['home_starting_lineup'][reverse_index]),'home']
							year_team=str(hist_data['Date'][reverse_index]).split("-")[0]+"_away"
					except Exception,error:
						print 'error for event: %s' % hist_data['event_id'][reverse_index]
						print str(error)
						os.system('pause')
					#feature_dict['FD_median'].append(self.median_stat(median_chunk_list,False))
					#feature_dict['strikeouts'].append(hist_data['strike_outs'][reverse_index]) #this is for plotting strikeouts vs. predicted strikeouts.
					if len(lineup_data)!=0: #will need to reconfigure this in future 
						lineup_stats_dict=self.batter_lineup_stats(hist_data['Date'][reverse_index],lineup_data,player_arm)
						if numpy.isnan(lineup_stats_dict['strikeout_rate']): #If function returned Nan value, assume lineup's K rate equal to league average
							lineup_stats_dict['strikeout_rate']=season_averages['league_K%_avg'][year]
						off_k_avg=float((lineup_stats_dict['strikeout_rate']-season_averages['league_K%_avg'][year])/season_averages['league_K%_avg'][year])
						pred_strikeouts=float((season_averages['pitcher_K9_avg_ha'][year_team]*off_k_avg+season_averages['pitcher_K9_avg_ha'][year_team])/9*season_averages['pitcher_IP_avg_ha'][year_team])
						if numpy.isnan(pred_strikeouts) or pred_strikeouts<0:
							feature_dict['pred_strikeouts'].append(3)
						else:
							feature_dict['pred_strikeouts'].append(pred_strikeouts)
					else:
						pred_strikeouts=float(season_averages['pitcher_K9_avg_ha'][year_team]/9*season_averages['pitcher_IP_avg_ha'][year_team])
						if numpy.isnan(pred_strikeouts) or pred_strikeouts<0: #if pitcher doesnt have enough data for given season, append 3 K's.
							feature_dict['pred_strikeouts'].append(3)
						else:
							feature_dict['pred_strikeouts'].append(pred_strikeouts)
				#Ian: need to fix this to eliminate any Nan values!!				

								#WEATHER FEATURE
				# try:
				# 	wunderground_data=ast.literal_eval(hist_data['wunderground_forecast'][reverse_index])
				# 	if wunderground_data['temp']>0 and wunderground_data['temp']<150:
				# 		feature_dict['temp'].append(wunderground_data['temp'])
				# 	else:
				# 		feature_dict['temp'].append(0) #Change to value regression will ignore
				# 	# if wunderground_data['humidity']>0 and wunderground_data['humidity']<100: #Ian: assuming given a relative humidity, need to check
				# 	# 	feature_dict['humidity'].append(wunderground_data['humidity'])
				# 	# else:
				# 	# 	feature_dict['humidity'].append(0) #Change to value regression will ignore
				# except:
				# 	feature_dict['temp'].append(0)
					# feature_dict['humidity'].append(0)
				# wind_data=hist_data['wind'][reverse_index]
				# if wind_data:
				# 	wind_speed=float(wind_data.split('_')[1])
				# 	wind_dir=float(wind_data.split('_')[0])
				# 	if wind_dir>=0 and wind_dir<=360 and wind_speed>=0 and wind_speed<=100:
				# 		# if hist_data['Player_Type'][-1]=='pitcher':
				# 		# 	feature_dict['wind_dir'].append(180-wind_dir)
				# 		# else:
				# 		# 	feature_dict['wind_dir'].append(wind_dir)
				# 		feature_dict['wind_speed'].append(wind_speed)
				# 	else: #Ian: these need to be changed to values that the regression will ignore...
				# 		#feature_dict['wind_dir'].append(0)
				# 		feature_dict['wind_speed'].append(0) 	
				# else: #Ian: these need to be changed to values that the regression will ignore...
				# 	#feature_dict['wind_dir'].append(0)
				# 	feature_dict['wind_speed'].append(0)
			except IndexError: #Ian: May need to change this? Depending on which feature has an index error first, other features may have already appended values for that indx...
				break
		return feature_dict

	def get_parameters(self,features,player,starting_lineups,hist_data,weather_forecast=False,odds_dict=False,date=False): #Ian: added date variable for backtesting
		player_id =player.split("_")
		player_name = player_id[0]
		player_type = player_id[1]
		player_gtd = starting_lineups[player]
		player_arm=player_gtd['arm']
		player_team=player_gtd['teamid']
		home_team = player_gtd['home_teamid'] #Ian: updated this as function now returns a nested dict
		if odds_dict:
			try:
				odds_dict=odds_dict[starting_lineups[player]['teamid']]
			except:
				odds_dict={}
				odds_dict['moneyline']=50
				odds_dict['proj_run_total']=5
		if weather_forecast:
			weather_data=weather_forecast[starting_lineups[player]['home_teamid']]
		stadium_data = self.get_stadium_data('home_team')
		HR_factor = stadium_data[home_team]['HR']
		if player_arm=='L':
			BH_factor= stadium_data[home_team]['LHB']
		else:
			BH_factor= stadium_data[home_team]['RHB']
		parameters = []
		print features
		for feature in features: 
			if feature == 'rest_time':
				parameters.append(86400) #Cole: default 1 day for now
			elif feature == 'FD_median':
			 	 parameters.append(self.median_stat(self.player_model_data['FD_points'][-self.median_stat_chunk_size[player_type]:]))
			elif feature == 'HR_ballpark_factor':
				parameters.append(float(HR_factor))
			elif feature == 'BH_ballpark_factor':
				parameters.append(float(BH_factor))
			elif feature == 'temp':
				parameters.append(weather_data['temp'])
			elif feature == 'humidity':
				if weather_data['humidity']>=0 and weather_data['humidity']<=100:  
					parameters.append(weather_data['humidity'])	
				else:
					parameters.append(50)	 
			elif feature == 'moneyline':
				try:
					parameters.append(odds_dict['moneyline'])
				except:
					parameters.append(50)
			elif feature == 'proj_run_total':
				try:
					parameters.append(odds_dict['proj_run_total'])
				except:
					parameters.append(3)
			elif feature=='wind_dir':
				if player_type=='pitcher':
					parameters.append(180-weather_data['wind']['wind_dir'])
				else:
					parameters.append(weather_data['wind']['wind_dir'])
			elif feature=='wind_speed':
				parameters.append(weather_data['wind']['wind_speed'])
			elif feature=='pred_strikeouts':
				if len(starting_lineups[player]['opposing_lineup'])!=0:
					year=str(hist_data['Date'][-1]).split("-")[0]
					if player_team==home_team:
						year_team=year+"_home"
					else:
						year_team=year+"_away"
					opposing_lineup_stats=self.batter_lineup_stats(date,[starting_lineups[player]['opposing_lineup'],year_team],player_arm)
					season_averages=self.season_averages(hist_data,player)
					if numpy.isnan(opposing_lineup_stats['strikeout_rate']):
						opposing_lineup_stats['strikeout_rate']=season_averages['league_K%_avg'][year]
					off_k_avg=float((opposing_lineup_stats['strikeout_rate']-season_averages['league_K%_avg'][year])/season_averages['league_K%_avg'][year])
					pred_strikeouts=float((season_averages['pitcher_K9_avg_ha'][year_team]*off_k_avg+season_averages['pitcher_K9_avg_ha'][year_team])/9*season_averages['pitcher_IP_avg_ha'][year_team])
				else:
					pred_strikeouts=float(season_averages['pitcher_K9_avg_ha'][year_team]/9*season_averages['pitcher_IP_avg_ha'][year_team])

				if pred_strikeouts<0 or numpy.isnan(pred_strikeouts):
					parameters.append(3)
				else:
					parameters.append(pred_strikeouts)
			elif feature=='op_pitcher_arm':
				if len(starting_lineups[player]['opposing_lineup'])!=0:
					op_pitcher_data = {player:data for player,data in starting_lineups[player]['opposing_lineup'].iteritems() if 'pitcher' in player}
					op_pitcher = op_pitcher_data.keys()[0]
					if op_pitcher_data[op_pitcher]['arm'] == 'R':
						parameters.append(1)
					else:
						parameters.append(0)
			elif feature =='op_pitcher_era':
				if len(starting_lineups[player]['opposing_lineup'])!=0:
					op_pitcher_data = {player:data for player,data in starting_lineups[player]['opposing_lineup'].iteritems() if 'pitcher' in player}
					op_pitcher = op_pitcher_data.keys()[0].split("_")[0]
					pitcher_data = self.get_db_gamedata(op_pitcher,"20130101","20170101")
					if op_pitcher + '_pitcher' in pitcher_data.keys():
						parameters.append(self.median_stat(pitcher_data[op_pitcher + '_pitcher']['era'][-13:]))
					else:
						print op_pitcher + " not in db"
						parameters.append(3)
			elif feature =='op_pitcher_strikeouts':
				if len(starting_lineups[player]['opposing_lineup'])!=0:
					op_pitcher_data = {player:data for player,data in starting_lineups[player]['opposing_lineup'].iteritems() if 'pitcher' in player}
					op_pitcher = op_pitcher_data.keys()[0].split("_")[0]
					pitcher_data = self.get_db_gamedata(op_pitcher,"20130101","20170101")
					if op_pitcher + '_pitcher' in pitcher_data.keys():
						parameters.append(self.median_stat(pitcher_data[op_pitcher + '_pitcher']['strike_outs'][-13:]))
					else:
						print op_pitcher + " not in db"
						parameters.append(3)
		return parameters

	def FD_points(self, data):
		if data['Player_Type'][-1] == 'batter':
			FD_points = (numpy.array(data['singles'])*1+numpy.array(data['doubles'])*2+numpy.array(data['triples'])*3+
							numpy.array(data['home_runs'])*4+numpy.array(data['rbi'])*1+numpy.array(data['runs'])*1+
								numpy.array(data['walks'])*1+numpy.array(data['stolen_bases'])*1+numpy.array(data['hit_by_pitch'])*1+
								numpy.subtract(numpy.array(data['at_bats']),numpy.array(data['hits']))*-.25)
		else:
			FD_points= (numpy.array(data['win'])*4+numpy.array(data['earned_runs'])*-1+
								numpy.array(data['strike_outs'])*1+numpy.array(data['innings_pitched'])*1)
		return FD_points

	def weather_checker(self,stadium,forecast):
		sql = "SELECT * FROM event_data WHERE stadium = '" + stadium +"'"
		event_data = dbo.read_from_db(sql,['event_id'],True)
		forecast_data =[{'forecast':data['forecast'].split("-")[1],'PoP':float(data['forecast'].split("-")[-1].replace("%",""))} for data in event_data.values()]
		vec = DictVectorizer()
		transformed_forecast_data = vec.fit_transform(forecast_data).toarray()
		print transformed_forecast_data
		PPD_data = numpy.array([0.0 if data['PPD'] == 'False' else 1.0 for data in event_data.values()])
		clf = DecisionTreeClassifier(min_samples_split=1).fit(transformed_forecast_data, PPD_data)
		PPD_pred =clf.predict(vec.transform(forecast))
		return PPD_pred

	def weather_classfier():
		pass

	def build_player_universe(self,contest_url): #Cole: this desperately needs documentation. Entire data structure needs documentation
		team_map = Ugen.excel_mapping("Team Map",9,6)
		FD_player_data = fdo.get_FD_player_dict(contest_url)#Cole:need to build some sort of test that FD_names and starting lineup names match - Ian: players now get mapped in the mlb_starting_lineups function itself.
		teams,starting_lineups = ds.mlb_starting_lineups() #Cole: need to write verification that all required teams have lineups
		team_dict={team:data['start_time'] for team,data in teams.iteritems() if team==data['home_teamid']}
		#weather_forecast={team:weather.weather_hourly(team,start_time) for team,start_time in team_dict.iteritems()}
		weather_forecast={}
		print 'getting weather'
		for team,start_time in team_dict.iteritems():
			weather_forecast[team]=weather.weather_hist(team,date,start_time)
			time.sleep(6.1) #so we don't exceed the alotted 10 calls per minute
		print 'weather retrieved'
		omitted_teams = []
		missing_lineups = [team for team in teams.keys() if len(teams[team]['lineup'])<8 and team not in omitted_teams] #Cole: this whole method needs to be split out into more reasonable functions
		print missing_lineups
		starting_players = [player.split("_")[0] for player in starting_lineups.keys() if starting_lineups[player]['teamid'] not in omitted_teams and 'PPD' not in starting_lineups[player]['start_time']] #Cole: is the PPD working?
		FD_starting_player_data = {FD_playerid:data for FD_playerid,data in FD_player_data.iteritems() if data[1] in starting_players} #data[1] is FD_player_name
		player_universe = {}
		odds_dict=TeamOdds.vegas_odds_sportsbook(dt.datetime.today().strftime("%Y%m%d"))
		for FD_playerid,data in FD_starting_player_data.iteritems():
			db_data = self.get_db_gamedata(data[1],"20140301","20141212")
			if data[0] == 'P': #Cole: If this can be generalized (ie sport player type map, the entire function can be generalized as a Sport method)
				player_type = 'pitcher'
			else:
				player_type = 'batter'
 			player_key = data[1]+ '_' + player_type	
			if player_key in db_data.keys():
				player_universe[player_key] = {}
				player_universe[player_key]['FD_playerid'] = FD_playerid
				projected_FD_points = self.FD_points_model(player_key,db_data[player_key],starting_lineups,weather_forecast,False,False)
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

	def hist_build_player_universe(self,date,contestID): #Ian: Decided to build separate from original, thought it would get too big..consider refactoring both.. 'yyyy-mm-dd'
			sql = "SELECT * FROM hist_fanduel_data Where Sport='MLB' And Date="+"'" +date+"' And contestID=" + "'" +contestID+"'"
			FD_db_data= dbo.read_from_db(sql,['Player','Position','contestID'],True)
			teams,starting_lineups = ds.mlb_starting_lineups(date)
			weather_forecast={}
			team_dict={team:data['start_time'] for team,data in teams.iteritems() if team==data['home_teamid']}
			#odds_dict=TeamOdds.vegas_odds_sportsbook(date)
			odds_dict={}

			#Ian: if you add this back in add weather var back into FD_points_model function call
			#weather_forecast={team:weather.weather_hist(team,date,start_time) for team,start_time in team_dict.iteritems()}
			# print 'getting weather'
			# for team,start_time in team_dict.iteritems():
			# 	weather_forecast[team]=weather.weather_hist(team,date,start_time)
			# 	time.sleep(6.1)
			#print 'weather retrieved'
			omitted_teams = []
			for FD_playerid,data in FD_db_data.iteritems(): #Ian: could this be turned into generator??
				if data['Position'] == 'P':
					player_type = 'pitcher'
				else:
					player_type = 'batter'
	 			data['player_key'] = data['Player']+ '_' + player_type
			starting_players = [player for player in starting_lineups.keys() if starting_lineups[player]['teamid'] not in omitted_teams and 'PPD' not in starting_lineups[player]['start_time']] #Cole: is the PPD working?
			#FD_starting_player_data = {FD_playerid:data for FD_playerid,data in FD_db_data.iteritems() if data['player_key'] in starting_players and (int(starting_lineups[data['player_key']]['batting_order'])<=5 or int(starting_lineups[data['player_key']]['batting_order'])==10)}
			FD_starting_player_data = {FD_playerid:data for FD_playerid,data in FD_db_data.iteritems() if data['player_key'] in starting_players}
			player_universe = {}
			for FD_playerid,data in FD_starting_player_data.iteritems():
				db_data = self.get_db_gamedata(data['Player'],"20140301",Ugen.previous_day(date).replace("-",""))
				# db_data = self.get_db_gamedata('Matt Wisler',"20130301",Ugen.previous_day(date).replace("-",""))
				player_key=data['player_key']
				# player_key='Matt Wisler_pitcher'
				if player_key in db_data.keys():
					player_universe[player_key] = {}
					player_universe[player_key]['FD_playerid'] = FD_playerid
					projected_FD_points = self.FD_points_model(player_key,db_data[player_key],starting_lineups,False,False,odds_dict,date)
					time.sleep(0.5)
					# os.system('pause')
					player_universe[player_key]['projected_FD_points'] = projected_FD_points.projected_points
					player_universe[player_key]['confidence'] = projected_FD_points.confidence
					player_universe[player_key]['Player_Type'] = player_key.split("_")[1]
					# if player_universe[player_key]['Player_Type']=='pitcher':
					# 	os.system('pause')
					player_universe[player_key]['name'] = player_key
					player_universe[player_key]['Salary']=float(data['FD_Salary'])
					player_universe[player_key]['GamesPlayed']=float(data['FD_GP'])
					player_universe[player_key]['PPG']=float(data['FD_FPPG'])
					player_universe[player_key]['FD_Position']=data['Position']
					player_universe[player_key]['FD_name']=data['Player']
					position_map = {key:1 if key == player_universe[player_key]['FD_Position'] else 0 for key in self.positions.keys()}
					tmp_dict = position_map.copy()
					player_universe[player_key].update(tmp_dict)
				else:
					print player_key + ' not in db_player_data'
			return player_universe

# mlb=MLB()
#data=mlb.hist_build_player_universe('2015-08-06','12748')
# data=mlb.hist_build_player_universe('2015-07-25','12691')
# data=mlb.get_db_gamedata("20140301",Ugen.previous_day('2015-06-10').replace("-",""),'Shane Victorino')
# data=data['Shane Victorino_batter']

# i=0
# for e,date,event_id in zip(data['wunderground_forecast'],data['Date'],data['event_id']):
# 	try:
# 		e=ast.literal_eval(e)
# 		print e['temp']
# 	except:
# 		i=i+1
# 		print event_id
# 		os.system('pause')
# print i
# os.system('pause')

