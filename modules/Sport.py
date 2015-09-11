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
import time
import weather
import datetime as dt
import TeamOdds
import features as ff

class Sport(): #Cole: Class has functions that should be stripped out and place into more appropriate module/class
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def FD_points_model(self,df,visualize = True):
		FD_projection= collections.namedtuple("FD_projection", ["projected_points", "confidence"])
		self.player_model_data = self.build_model_dataset(df)
		player_model = Model.Model(self.player_model_data,player)
		print '%s modelled' % df['name'][0]
		player_model.FD_points_model(visualize)
		if player_model.modelled:	#Cole: need to develop parameters for each player
			parameters = numpy.nan_to_num(self.get_parameters(player_model.feature_labels,player,starting_lineups,hist_data,weather_forecast,odds_dict,date))
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

	def get_db_gamedata(self,player,player_type,start_date="20100101",end_date="21000101",GameID=None): #Updated to get by GameID or by Dates
		if GameID:
			sql = ("SELECT hist_player_data.*, event_data.* FROM hist_player_data "
				 "INNER JOIN event_data ON hist_player_data.GameID=event_data.event_id "
				   "WHERE hist_player_data.Sport = '"+ self.sport +"' AND "
				   " Player = '"+ player.replace("'","''") +"' AND Player_Type ='"+ player_type +"'" +"' AND GameID ='"+ GameID +"'"
				    " ORDER BY Date ASC")
		else:
			sql = ("SELECT hist_player_data.*, event_data.* FROM hist_player_data "
					 "INNER JOIN event_data ON hist_player_data.GameID=event_data.event_id "
					   "WHERE hist_player_data.Sport = '"+ self.sport +"' AND "
					   "Player = '"+ player.replace("'","''") +"' AND Player_Type ='"+ player_type +"' AND "
					    "Date BETWEEN '" + start_date +"' AND "
					    "'" + end_date + "' ORDER BY Date ASC")
		df = dbo.read_from_db(sql)
		df.rename(columns=self.inv_db_data_model[df['Player_Type'][0]],inplace=True)
		df['name'] = df['display_name'] + "_" + df['Player_Type']  #Cole: adding the field 'name' is required for openopts results output
		for col in list(df):
			try:
				df[col] = df[col].astype(float)
			except:
				pass
		return df

	def get_stadium_data(self,prime_key = 'stadium'):
		sql = "SELECT * FROM stadium_data"
		return dbo.read_from_db(sql,[prime_key],True)

	def optimal_roster(self,FDSession,contest_url,confidence = -100,date=False,contestID=False): #Ian: added optional date for backtesting
		DB_parameters=Ugen.ConfigSectionMap('local text')
		if date:
			player_universe=self.hist_build_player_universe(date,contestID)
		else:
			player_universe = self.build_player_universe(FDSession,contest_url)
		items = ([{key:value for key,value in stats_data.iteritems() if key in self.optimizer_items}
					 for player_key,stats_data in player_universe.iteritems()
					 if 'salary' in stats_data.keys()])
		objective = 'projected_FD_points'
		if items:
			p = KSP(objective, items, goal = 'max', constraints=self.get_constraints(confidence))
			r = p.solve('glpk',iprint = 0)
			roster_data = []
			rw = 2
			sum_confidence = 0
			for player in r.xf:
				#roster_data.append([player_universe[player]['position'],str(int(player_universe[player]['FD_playerid'])),str(int(player_universe[player]['MatchupID'])),str(int(player_universe[player]['TeamID']))])
				Cell("Roster",rw,1).value = player
				Cell("Roster",rw,2).value = player_universe[player]['team']
				Cell("Roster",rw,3).value = player_universe[player]['position']
				Cell("Roster",rw,4).value = player_universe[player]['projected_FD_points']
				Cell("Roster",rw,5).value = player_universe[player]['confidence']
				Cell("Roster",rw,6).value = player_universe[player]['salary']
				sum_confidence = sum_confidence + player_universe[player]['confidence']
				rw = rw + 1
			lineup = [{'position':player_universe[player]['position'],'player':{'id':player_universe[player]['id']}} for player in r.xf]
			sorted_roster = sorted(lineup, key=self.sort_positions)
			print sorted_roster
			os.system('pause')
			entry_dict = {"entries":[{"entry_fee":{"currency":"usd"},"roster":{"lineup":sorted_roster}}]}
			with open(DB_parameters['rostertext'],"w") as myfile: #Ian: replaced hard-coded folder path with reference to config file
					myfile.write(str(entry_dict).replace(' ',''))
			return {'confidence':sum_confidence,'roster':entry_dict,'optimizer':r}
		else:
			return {'confidence':0,'roster':[],'optimizer':None}

class MLB(Sport): #Cole: data modelling may need to be refactored, might be more elegant solution
	def __init__(self):
		Sport.__init__(self,"MLB")
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

		self.optimizer_items = ['name','Player_Type','salary','P','C','1B','2B','3B','SS','OF','projected_FD_points','confidence']
		self.model_version = '0.0.0001'
		self.features={'pitcher':[ff.FD_median],'batter':[ff.FD_median]}
		self.model_description = "Lasso Linear regression and %s" % self.features
		self.model_mean_score = -1.70
		self.contest_constraints = ({'size':[{'max': 2, 'min': 2},{'max': 3, 'min': 3},{'max': 4, 'min': 4},
									{'max': 5, 'min': 5},{'max': 6, 'min': 6},{'max': 7, 'min': 7},{'max': 8, 'min': 8},{'max': 10, 'min': 10},
									{'max': 14, 'min': 14},{'max': 20, 'min': 20},{'max': 50, 'min': 50}],
									'type':[{u'_members': [u'FIFTY_FIFTY'], u'_ref': u'contest_types.id'}],
									'entry_fee':[1,2,5]})
		self.avg_plate_appearances={'1':0.12239,'2':0.11937,'3':0.11683,'4':0.11417,'5':0.11161,'6':0.10848,'7':0.10555,'8':0.10243,'9':0.09917} #move this to sport class init function

	def get_constraints(self,confidence=-100):
		return lambda values : (
								values['salary'] <= 35000,
							    values['P'] == 1,
							    values['C'] == 1,
							    values['1B'] == 1,
							    values['2B'] == 1,
							    values['3B'] == 1,
							    values['SS'] == 1,
							    values['OF'] == 3,
							    values['confidence'] >=confidence)

	def sort_positions(self,sort_list):
		return self.positions[sort_list['position']]
	
	def batter_lineup_stats(self,date,lineup_data,player_arm):
		lineup_stats_dict={}
		hist_lineup_strikeout_rate,hist_lineup_ops,hist_lineup_slg,strikeout_PAs_list,ops_PAs_list,slg_PAs_list=([] for i in range(6))
		team_map=Ugen.mlb_map(11,4)
		for player in lineup_data[0]:
			player_strikeout_rate_splits,player_ops_splits,player_slg_splits=([] for i in range(3))
			if player.split("_")[1]!='pitcher':
				player_data=self.get_db_gamedata(player.split("_")[0],"20130301",Ugen.previous_day(str(date)).replace("-","")) #may need to play with how much data you use to get batter's K avg
				try:
					player_data=player_data[player] 
				except KeyError:
					print 'player %s not in db, needs new player map' % player
					rw=2
					map_list=[]
					while Cell("Output",rw,7).value:
						map_list.append(Cell("Output",rw,7).value)
						rw+=1
					if player not in map_list:
						Cell("Output",rw,7).value=player
						Cell("Output",rw,8).value=Ugen.previous_day(str(date)).replace("-","")
					continue
				for indx,event in enumerate(player_data['event_id']):
					try:
						reverse_index = len(player_data['event_id'])-indx-1
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
										player_strikeout_rate_splits.append(0.200)
									else:
										player_strikeout_rate_splits.append(strikeout_rate)
									if player_data['ops'][reverse_index]>=0:
										player_ops_splits.append(player_data['ops'][reverse_index])
									else:
										player_ops_splits.append(0)
									if player_data['slg'][reverse_index]>=0:
										player_slg_splits.append(player_data['slg'][reverse_index])
									else:
										player_slg_splits.append(0)
						except ValueError: #This is when there is no starting lineups data (usually)
							#print 'Value error %s %s' %(player_data["Date"][reverse_index],player)
							pass
					except IndexError:
						print 'index error'
						break
				batting_order=lineup_data[0][player]['batting_order']
				if len(player_strikeout_rate_splits)>2: #say we need 3 min values to incorporate the players strikeout rate into feature
					hist_lineup_strikeout_rate.append(float(self.avg_plate_appearances[batting_order]*numpy.mean(player_strikeout_rate_splits)))
					strikeout_PAs_list.append(self.avg_plate_appearances[batting_order])
				if len(player_ops_splits)>2:
					hist_lineup_ops.append(float(self.avg_plate_appearances[batting_order]*numpy.mean(player_ops_splits)))
					ops_PAs_list.append(self.avg_plate_appearances[batting_order])
				if len(player_slg_splits)>2:
					hist_lineup_slg.append(float(self.avg_plate_appearances[batting_order]*numpy.mean(player_slg_splits)))
					slg_PAs_list.append(self.avg_plate_appearances[batting_order])

		lineup_stats_dict['strikeout_rate']=numpy.sum(hist_lineup_strikeout_rate)/numpy.sum(strikeout_PAs_list)
		lineup_stats_dict['ops']=numpy.sum(hist_lineup_ops)/numpy.sum(ops_PAs_list)
		lineup_stats_dict['slg']=numpy.sum(hist_lineup_slg)/numpy.sum(slg_PAs_list)
		# print lineup_stats_dict
		# os.system('pause')
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
			s2015_pitcher_ER_home=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2015' and (player in AT or player in HT) and team==team_map[home_team]])
			s2015_pitcher_ER_away=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2015' and (player in AT or player in HT) and team==team_map[away_team]])			
		except:
			s2015_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015'and IP>3])	
			s2015_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[home_team]])
			s2015_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[away_team]])
			s2015_pitcher_ER_home=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[home_team]])
			s2015_pitcher_ER_away=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2015' and IP>3 and team==team_map[away_team]])
		try:
			s2014_pitcher_IP=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014'and (player in AT or player in HT)])
			s2014_pitcher_IP_home=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[home_team]])
			s2014_pitcher_IP_away=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[away_team]])
			s2014_pitcher_ER_home=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[home_team]])
			s2014_pitcher_ER_away=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2014' and (player in AT or player in HT) and team==team_map[away_team]])				
		except:
			s2014_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014'and IP>3])	
			s2014_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[home_team]])
			s2014_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[away_team]])
			s2014_pitcher_ER_home=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[home_team]])
			s2014_pitcher_ER_away=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2014' and IP>3 and team==team_map[away_team]])
		try:
			s2013_pitcher_IP=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013'and (player in AT or player in HT)])
			s2013_pitcher_IP_home=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[home_team]])
			s2013_pitcher_IP_away=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[away_team]])			
			s2013_pitcher_ER_home=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[home_team]])
			s2013_pitcher_ER_away=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 if str(date).split("-")[0]=='2013' and (player in AT or player in HT) and team==team_map[away_team]])				
		except:
			s2013_pitcher_IP=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013'and IP>3])	
			s2013_pitcher_IP_home=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[home_team]])
			s2013_pitcher_IP_away=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[away_team]])
			s2013_pitcher_ER_home=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[home_team]])
			s2013_pitcher_ER_away=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								  hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]=='2013' and IP>3 and team==team_map[away_team]])		

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
			},
			'pitcher_ER_avg_ha': {
						'2015_home':s2015_pitcher_ER_home,
						'2015_away':s2015_pitcher_ER_away,
						'2014_home':s2014_pitcher_ER_home,
						'2014_away':s2014_pitcher_ER_away,
						'2013_home':s2013_pitcher_ER_home,
						'2013_away':s2013_pitcher_ER_away,
			}
		}

		# # Ian: added this loop to replace nan values with previous year averages, otherwise give them a zero..
		for outer_key,outer_val in season_averages.iteritems(): 
			for inner_key,inner_val in outer_val.iteritems():
				if numpy.isnan(inner_val) and "_" in inner_key:
					# print 'nan found in %s for following key:val - %s:%s' %(outer_key,inner_key,inner_val)
					split_key=inner_key.split("_")
					if split_key[0]=='2013':
						season_averages[outer_key][split_key[0]+'_away']=0
						season_averages[outer_key][split_key[0]+'_home']=0
						continue #otherwise we will error when we try prev_year_key of 2012
					prev_year_key=str(int(split_key[0])-1)+'_'+split_key[1]
					if not numpy.isnan(season_averages[outer_key][prev_year_key]):
						season_averages[outer_key][inner_key]=season_averages[outer_key][prev_year_key]
						if split_key[1]=='home': #If we're replacing one H/A avg with the previous year, replace the other too...
							season_averages[outer_key][split_key[0]+'_away']=season_averages[outer_key][prev_year_key.split("_")[0]+'_away']														
						else:	
							season_averages[outer_key][split_key[0]+'_home']=season_averages[outer_key][prev_year_key.split("_")[0]+'_home']	
					else: #If we don't have 2015 or 2014 data, put in a zero
						season_averages[outer_key][split_key[0]+'_away']=0
						season_averages[outer_key][split_key[0]+'_home']=0

		return season_averages
#Ian: reverse index is day before, check how this may affect your stuff
	def build_model_dataset(self,df):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
		print 'now building dataset for %s' % df['name'][0]
		feature_df= pandas.DataFrame(ff.FD_points(df))
		for feature in self.features[df['Player_Type'][0]]:
			feature_df[feature.__name__] = feature(df)
		return feature_df

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
		if ('pred_strikeouts' or 'batter_lineup_ops' or 'batter_lineup_slg') in features and len(starting_lineups[player]['opposing_lineup'])!=0:
			season_averages=self.season_averages(hist_data,player)
			year=str(hist_data['Date'][-1]).split("-")[0]
			if player_team==home_team:
				year_team=year+"_home"
				batter_matchup='away'
			else:
				year_team=year+"_away"
				batter_matchup='home'
			if date:
				opposing_lineup_stats=self.batter_lineup_stats(date,[starting_lineups[player]['opposing_lineup'],batter_matchup],player_arm)
			else:
				opposing_lineup_stats=self.batter_lineup_stats(time.strftime("%Y-%m-%d"),[starting_lineups[player]['opposing_lineup'],batter_matchup],player_arm)
		
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
					if numpy.isnan(opposing_lineup_stats['strikeout_rate']):
						opposing_lineup_stats['strikeout_rate']=season_averages['league_K%_avg'][year]
					off_k_avg=float((opposing_lineup_stats['strikeout_rate']-season_averages['league_K%_avg'][year])/season_averages['league_K%_avg'][year])
					pred_strikeouts=float((season_averages['pitcher_K9_avg_ha'][year_team]*off_k_avg+season_averages['pitcher_K9_avg_ha'][year_team])/9*season_averages['pitcher_IP_avg_ha'][year_team])
				else:
					pred_strikeouts=float(season_averages['pitcher_K9_avg_ha'][year_team]/9*season_averages['pitcher_IP_avg_ha'][year_team])
				if pred_strikeouts<0 or numpy.isnan(pred_strikeouts): 
					parameters.append(0)#Ian: consider giving him a zero to force a lower score? if we dont have enough data we don't want him
				else:
					parameters.append(pred_strikeouts)
			elif feature=='batter_lineup_ops':
				if len(starting_lineups[player]['opposing_lineup'])>1:
					parameters.append(opposing_lineup_stats['ops'])
				else:
					parameters.append(0.710)
			elif feature=='batter_lineup_slg':
				if len(starting_lineups[player]['opposing_lineup'])>1:
					parameters.append(opposing_lineup_stats['slg'])
				else:
					parameters.append(0.400)
			elif feature=='innings_pitched':
				if len(starting_lineups[player]['opposing_lineup'])>1:
					parameters.append(season_averages['pitcher_IP_avg_ha'][year_team])
				else:
					parameters.append(5)
			elif feature=='earned_runs':
				if len(starting_lineups[player]['opposing_lineup'])>1:
					parameters.append(season_averages['pitcher_ER_avg_ha'][year_team])
				else:
					parameters.append(4)
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
					if date:
						pitcher_data = self.get_db_gamedata(op_pitcher,"20130101",Ugen.previous_day(date).replace("-",""))
					else:
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
					if date:
						pitcher_data = self.get_db_gamedata(op_pitcher,"20130101",Ugen.previous_day(date).replace("-",""))
					else:
						pitcher_data = self.get_db_gamedata(op_pitcher,"20130101","20170101")
					if op_pitcher + '_pitcher' in pitcher_data.keys():
						parameters.append(self.median_stat(pitcher_data[op_pitcher + '_pitcher']['strike_outs'][-13:]))
					else:
						print op_pitcher + " not in db"
						parameters.append(3)
		return parameters

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

	def build_player_universe(self,FDSession,contest_url): #Cole: this desperately needs documentation. Entire data structure needs documentation
		FD_player_data = FDSession.fanduel_api_data(contest_url)['players']#Cole:need to build some sort of test that FD_names and starting lineup names match - Ian: players now get mapped in the mlb_starting_lineups function itself.
		teams,starting_lineups = ds.mlb_starting_lineups() #Cole: need to write verification that all required teams have lineups
		missing_lineups = [team for team in teams.keys() if len(teams[team]['lineup'])<8 and team not in omitted_teams] #Cole: this whole method needs to be split out into more reasonable functions
		print missing_lineups
		starting_players = [player.split("_")[0] for player in starting_lineups.keys() if starting_lineups[player]['teamid'] not in omitted_teams and 'PPD' not in starting_lineups[player]['start_time']] #Cole: is the PPD working?
		FD_starting_player_data = {player['first_name'] + " " + player['last_name']:player for player in FD_player_data if player['first_name'] + " " + player['last_name'] in starting_players} #data[1] is FD_player_name
		player_universe = {}
		for FD_playerid,data in FD_starting_player_data.iteritems():
			try: #Cole: this tests if the player is a batter or pitcher in tonights lineup - this might cause issues if FD name doesnt math lineup names
				test = starting_lineups[FD_playerid +"_batter"]
				player_type = 'batter'
			except KeyError:
				player_type = 'pitcher'
			db_df = self.get_db_gamedata(FD_playerid,player_type)
 			player_key = FD_playerid + '_' + player_type	
			if player_key == db_df['name']:
				player_universe[player_key] = {}
				projected_FD_points = self.FD_points_model(db_df)
				player_universe[player_key]['projected_FD_points'] = projected_FD_points.projected_points
				player_universe[player_key]['confidence'] = projected_FD_points.confidence
				player_universe[player_key]['Player_Type'] = player_type
				player_universe[player_key]['name'] = player_key
				for key,player_data in data.iteritems():
					player_universe[player_key][key] = player_data
				position_map = {key:1 if key == player_universe[player_key]['position'] else 0 for key in self.positions.keys()}
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
				# db_data = self.get_db_gamedata('Roenis Elias',"20130301",Ugen.previous_day(date).replace("-",""))
				player_key=data['player_key']
				# player_key='Roenis Elias_pitcher'
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

