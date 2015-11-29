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
import pprint
import features as ff

class Sport(): #Cole: Class has functions that should be stripped out and place into more appropriate module/class
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def FD_points_model(self,df,visualize = False):
		FD_projection= collections.namedtuple("FD_projection", ["projected_points", "confidence"])
		player_model_data,parameter_array = self.build_model_dataset(df)
		print parameter_array
		player_model = Model.Model(player_model_data,df['name'][0])
		player_model.FD_points_model(visualize)
		if player_model.modelled:	#Cole: need to develop parameters for each player
			print '%s modelled' % df['name'][0]
			if len(player_model.test_feature_matrix) > 1: #Test dataset needs to contain at least 2 datapoints to compute score
				projected_FD_points = (FD_projection(player_model.model.predict(parameter_array)[-1],
												player_model.model.score(player_model.test_feature_matrix,player_model.test_target_matrix)))
				print projected_FD_points
			else:
				projected_FD_points = FD_projection(player_model.model.predict(parameter_array)[-1],0)
		else:
			print '%s not modelled' % df['name'][0]
			try:
				default_projection = self.player_model_data['FD_median'][-1]
				projected_FD_points = FD_projection(0,0) #Cole: this is the default model prediction and confidence if player cannot be modelled
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


	def get_daily_game_data(self,start_date,end_date,store = False):
		event_dates = [d.strftime('%Y%m%d') for d in pandas.date_range(start_date,end_date)]
		for event_date in event_dates:
			odds_dict= {}
			day_events = self.events(event_date)
			event_list = ([game['event_id'] for game in day_events if game['event_status'] == 'completed'
							 and game['season_type'] == 'regular' or 'post'])
			all_game_data = {}
			#Ian: need to add a check if events have alreayd been historized? investigate what happens if you don't check??
			for indx,game_id in enumerate(event_list):
				#if game_id not in db_eventids.key():
				self.gameid = game_id
				if store == False:
					game_data = XMLStats.main(self,'boxscore',None)
				elif store == True: #and self.gameid not in self.gameids().all_gameids: 
					print "loading " + game_id
					# self.parse_event_data(day_events[indx],event_date,odds_dict) 
					game_data = XMLStats.main(self,'boxscore',None)
					if game_data != None:
						self.parse_event_data(game_data)
					 	parsed_data = self.parse_boxscore_data(game_data)
					print game_id + " succesfully loaded"
				else:
					game_data = None
				if game_data:
					all_game_data[game_id] = game_data
		return all_game_data #xml_team_list #Ian: part of player mapping


	def parse_boxscore_data(self,boxscore_data):
		player_map = {}#Ugen.excel_mapping("Player Map",6,5) #Ian: this needs to be generalized for each sport
		if boxscore_data: 
			for dataset,data_model in self.data_model.iteritems():
				for player in boxscore_data[dataset]:
					player_data={}
					player_data['gameID'] = self.gameid
					player_data['sport'] = self.sport
					player_data['player_type'] = self.player_type_map[dataset]
					player_data['date'] = dt.datetime.strptime(self.gameid[0:8],'%Y%m%d')
					meta_cols = [col for col in player_data.keys()]
					for datum,val in data_model.iteritems():
						if datum[0] == '$': #Cole: prefix with $ denotes hard coded value
							player_data[val] = datum[1:]
						elif player[datum] == True: #Cole: Convert bool to int for db write
							player_data[val] = 1
						elif player[datum] ==False:
							player_data[val] = 0
						elif datum == 'display_name': #Cole: this deals with the player mapping on the front end, so whats in db matches FD 
							if player[datum] in player_map.keys():
								player_data[val] = player_map[player[datum]]
							else:
								player_data[val] = player[datum]
						else:
							player_data[val] = player[datum]
					dbo.write_to_db('hist_player_data',player_data,False)
		return self


	def get_db_gamedata(self,player,start_date="2010-01-01",end_date="2100-01-01",GameID=False): #Ian: query by date or GameID
		if GameID:
			query={'sport':self.sport,'player':player,'gameID':GameID}
		else:
			query={'sport':self.sport,'player':player,'date':{"$gte":dt.datetime.strptime(start_date,'%Y-%m-%d'),"$lte":dt.datetime.strptime(end_date,'%Y-%m-%d')}}
		player_data=dbo.read_from_db('hist_player_data',query,{'_id':0,'sport':0})
		player_data.sort(key=lambda e: e['date'], reverse=False)
		player_data_dict={key:[doc[key] for doc in player_data] for key in player_data[0].keys()}
		event_data=[dbo.read_from_db('hist_event_data',{'sport':self.sport,'gameID':gameID},{'_id':0,'date':0,'sport':0,'gameID':0})[0] for gameID in player_data_dict['gameID']]
		event_data_dict={key:[doc[key] for doc in event_data] for key in event_data[0].keys()}
		player_data_dict.update(event_data_dict)
		df=pandas.DataFrame(player_data_dict)
		#Ian: add some check for data??
		return df

	def get_db_gamedata_old(self,player,player_type,start_date="20100101",end_date="21000101",GameID=None): #Updated to get by GameID or by Dates
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
			player_universe=self.build_player_universe(FDSession,contest_url,date,contestID)
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

class NBA(Sport): #Cole: data modelling may need to be refactored, might be more elegant solution
	def __init__(self):
		Sport.__init__(self,"NBA")
		#enter constraints: 2 PGs, 2 SGs, 2 SFs, 2 PFs, 1 C
		self.positions = {'PG':1,'SG':2,'SF':3,'PF':4,'C':5}
		self.player_type_map = {'away_stats':'bplayer','home_stats':'bplayer'} #Ian: all players are the same for stats in NBA, therefore give random name bplayer (basketbll player) not to be confused with player
		self.db_data_model = {'bplayer':{'display_name':'player','position':'position',	#Ian: no meta required for NBA, only one player type. Cole: prefix with $ to denote a hard coded value
							'team_abbreviation':'team','turnovers':'turnovers','assists':'assists','blocks':'blocks','points':'points',
								'field_goals_made':'FGM','field_goals_attempted':'FGA','is_starter':'starter','free_throws_made':'FTM',
								'free_throws_attempted':'FTA','three_point_field_goals_made':'3FGM','personal_fouls':'fouls',
										'three_point_field_goals_attempted':'3FGA','steals':'steals','rebounds':'rebounds','minutes':'minutes'}}
		
		self.optimizer_items = ['name','Player_Type','salary','P','C','1B','2B','3B','SS','OF','projected_FD_points','confidence'] #Ian: we need to change Player_Type to position???
		
		self.totals_data_model={'assists':'assists','blocks':'blocks','field_goals_attempted':'FGA','field_goals_made':'FGM',
								'free_throws_made':'FTM','free_throws_attempted':'FTA','three_point_field_goals_attempted':'3FGA',
								'three_point_field_goals_made':'3FGM','personal_fouls':'fouls','points':'points',
								'rebounds':'rebounds','steals':'steals','turnovers':'turnovers'}
		
		self.event_info_data_model=['attendance','duration','season_type']
		self.data_model = ({'away_stats':self.db_data_model['bplayer'],'home_stats':self.db_data_model['bplayer']})		

	def FD_points(self, data):
		FGM2=numpy.subtract(numpy.array(data['FGM']),numpy.array(data['3FGM']))
		FGM2[FGM2<0]=0 #Ian: replace negative values (i.e. only three pointers made) with 0
		FD_points=(numpy.array(data['3FGM'])*3+numpy.array(FGM2)*2+numpy.array(data['FTM'])*1+numpy.array(data['rebounds'])*1.2+
					numpy.array(data['assists'])*1.5+numpy.array(data['blocks'])*2+numpy.array(data['steals'])*2+numpy.array(data['turnovers'])*-1)
		return FD_points

	def parse_event_data(self,boxscore_data): 
		event_data={}
		if boxscore_data:
			event_data['gameID']=self.gameid
			event_data['sport']=self.sport
			event_data['date']=dt.datetime.strptime(self.gameid[0:8],'%Y%m%d')
			event_data['away_period_scores']=boxscore_data['away_period_scores']
			event_data['away_team']=boxscore_data['away_team']['abbreviation']
			event_data['home_period_scores']=boxscore_data['home_period_scores']
			event_data['home_team']=boxscore_data['home_team']['abbreviation']
			event_data['away_totals']={val:boxscore_data['away_totals'][key] for key,val in self.totals_data_model.iteritems()}
			event_data['home_totals']={val:boxscore_data['home_totals'][key] for key,val in self.totals_data_model.iteritems()}
			event_data['event_information']={key:boxscore_data['event_information'][key] for key in self.event_info_data_model}
			event_data['officials']=[official['first_name']+' '+official['last_name'] for official in boxscore_data['officials']]
			dbo.write_to_db('hist_event_data',event_data,False)
		return

	def build_player_universe(self,FDSession,contest_url,date=False,contestID = ""): 
		if date:
			query={'sport':self.sport,'date':dt.datetime.strptime(date,'%Y-%m-%d'),'contest_ID':contestID}
			FD_player_data=dbo.read_from_db('hist_fanduel_data',query)[0]['contest_dict']
			# teams,starting_lineups = 0 #Ian: create starting lineups function, ensure they get mapped to FD names
			starting_players =[]#[player.split("_")[0] for player in starting_lineups.keys() if starting_lineups[player]['teamid'] not in omitted_teams and 'PPD' not in starting_lineups[player]['start_time']] 
			FD_starting_player_data = {player:player_data for player,player_data in FD_player_data.iteritems() if player not in starting_players} #Ian: change to "in starting_players" once lineups function is added
		else:
			FD_player_data = FDSession.fanduel_api_data(contest_url)['players']
			#Ian: create FD_starting_player_data variable to create dict like the one from backtests
		for FD_playerid,data in FD_starting_player_data.iteritems():
			db_df = self.get_db_gamedata(FD_playerid,'2015-10-01',end_date=Ugen.previous_day(date))
 			player_key = FD_playerid
 			player_universe={}
			if player_key == db_df['player'][0]:
				player_universe[player_key] = {}
				projected_FD_points = self.FD_points_model(db_df)
				player_universe[player_key]['projected_FD_points'] = projected_FD_points.projected_points
				player_universe[player_key]['confidence'] = projected_FD_points.confidence
				player_universe[player_key]['Player_Type'] = player_type
				player_universe[player_key]['name'] = player_key
				
				#Ian: add this back in once projected_FD_points is working
				# for key,player_data in data.iteritems():
				# 	player_universe[player_key][key] = player_data
				# position_map = {key:1 if key == player_universe[player_key]['position'] else 0 for key in self.positions.keys()}
				# tmp_dict = position_map.copy()
				# player_universe[player_key].update(tmp_dict)
			else:
				print player_key + ' not in db_player_data'
		return player_universe



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
		self.features=({'pitcher':[[ff.FD_median,ff.param_FD_median],[ff.FD_median_5,ff.param_FD_median_5]],
						'batter':[[ff.FD_median,ff.param_FD_median],[ff.FD_median_5,ff.param_FD_median_5]]})
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
	
	def parse_event_data(self,event_data,event_date,odds_data): #Ian: needs to be updated for mongodb
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

	def batter_lineup_stats(self,date,lineup_data,player_arm): #Ian: needs refactoring!!
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
	
	def pitcher_season_averages(self,hist_data,home_away,year):
		team_map=Ugen.mlb_map(11,4)
		season_avg={}
		if not home_away and stat=='innings_pitched':
			try:
				season_avg['K9']=numpy.mean([float(SO/IP*9) for SO,date,IP in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched']) if str(date).split("-")[0]==year and IP>3])
				season_avg['IP']=numpy.mean([IP for AT,HT,IP,date in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 		hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]==year and (player in AT or player in HT)])
			except:
				season_avg['IP']=numpy.mean([IP for IP,date in zip(hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]=='2015'and IP>3])	
		elif home_away=='home':
			try:
				season_avg['K9']=numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]==year and IP>3 and team==team_map[home_team]])
				season_avg['IP']=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
									hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
									if str(date).split("-")[0]==year and (player in AT or player in HT) and team==team_map[home_team]])
				season_avg['ER']=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 		hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 		if str(date).split("-")[0]==year and (player in AT or player in HT) and team==team_map[home_team]])
			except:
				season_avg['IP']=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
									hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]==year and IP>3 and team==team_map[home_team]])
				season_avg['ER']=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								 	hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]==year and IP>3 and team==team_map[home_team]])
		elif home_away=='away':
			try:
				season_avg['K9']=numpy.mean([float(SO/IP*9) for SO,date,IP,team,home_team,away_team \
					 		   		in zip(hist_data['strike_outs'],hist_data['Date'],hist_data['innings_pitched'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
					 		   		if str(date).split("-")[0]==year and IP>3 and team==team_map[home_team]])
				season_avg['IP']=numpy.mean([IP for AT,HT,IP,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
									hist_data['innings_pitched'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
									if str(date).split("-")[0]==year and (player in AT or player in HT) and team==team_map[away_team]])
				season_avg['ER']=numpy.mean([ER for AT,HT,ER,date,team,home_team,away_team in zip(hist_data['away_starting_lineup'],hist_data['home_starting_lineup'], \
							 		hist_data['earned_runs'],hist_data['Date'],hist_data['Team'],hist_data['home_team'],hist_data['away_team']) \
							 		if str(date).split("-")[0]==year and (player in AT or player in HT) and team==team_map[away_team]])
			except:
				season_avg['IP']=numpy.mean([IP for team,home_team,away_team,IP,date in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
									hist_data['innings_pitched'],hist_data['Date']) if str(date).split("-")[0]==year and IP>3 and team==team_map[away_team]])
				season_avg['ER']=numpy.mean([ER for team,home_team,away_team,IP,date,ER in zip(hist_data['Team'],hist_data['home_team'],hist_data['away_team'],\
								 	hist_data['innings_pitched'],hist_data['Date'],hist_data['earned_runs']) if str(date).split("-")[0]==year and IP>3 and team==team_map[away_team]])

		return season_avg

	def season_averages(self,hist_data,player): 	
		if player.split('_')[1]=='pitcher':
			season_averages={
				"league_K%_avg": {'2015':0.234,'2014':0.204,'2013':0.199,},
				'pitcher_K9_avg': {
							'2015':pitcher_season_averages(hist_data,False,'2015')['K9'],
							'2014':pitcher_season_averages(hist_data,False,'2014')['K9'],
							'2013':pitcher_season_averages(hist_data,False,'2013')['K9']},
				'pitcher_K9_avg_ha': {
							'2015_home':pitcher_season_averages(hist_data,'home','2015')['K9'],
							'2015_away':pitcher_season_averages(hist_data,'away','2015')['K9'],
							'2014_home':pitcher_season_averages(hist_data,'home','2014')['K9'],
							'2014_away':pitcher_season_averages(hist_data,'away','2014')['K9'],
							'2013_home':pitcher_season_averages(hist_data,'home','2013')['K9'],
							'2013_away':pitcher_season_averages(hist_data,'away','2013')['K9']},
				'pitcher_IP_avg': {
							'2015':pitcher_season_averages(hist_data,False,'2015')['IP'],
							'2014':pitcher_season_averages(hist_data,False,'2014')['IP'],
							'2013':pitcher_season_averages(hist_data,False,'2013')['IP']},
				'pitcher_IP_avg_ha': {
							'2015_home':pitcher_season_averages(hist_data,'home','2015')['IP'],
							'2015_away':pitcher_season_averages(hist_data,'away','2015')['IP'],
							'2014_home':pitcher_season_averages(hist_data,'home','2014')['IP'],
							'2014_away':pitcher_season_averages(hist_data,'away','2014')['IP'],
							'2013_home':pitcher_season_averages(hist_data,'home','2013')['IP'],
							'2013_away':pitcher_season_averages(hist_data,'away','2013')['IP']},
				'pitcher_ER_avg_ha': {
							'2015_home':pitcher_season_averages(hist_data,'home','2015')['ER'],
							'2015_away':pitcher_season_averages(hist_data,'away','2015')['ER'],
							'2014_home':pitcher_season_averages(hist_data,'home','2014')['ER'],
							'2014_away':pitcher_season_averages(hist_data,'away','2014')['ER'],
							'2013_home':pitcher_season_averages(hist_data,'home','2013')['ER'],
							'2013_away':pitcher_season_averages(hist_data,'away','2013')['ER']},
			}

		season_averages=season_averages_check(season_averages)
		return season_averages

	def season_averages_check(season_averages):
		#Ian: added this loop to replace nan values with previous year averages, otherwise give them a zero..
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

	def build_model_dataset(self,df):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
		print 'now building dataset for %s' % df['name'][0]
		feature_df= pandas.DataFrame(ff.FD_points(df))
		parameter_array = []
		for feature in self.features[df['Player_Type'][0]]:
			feature_df[feature[0].__name__] = feature[0](df)#Index 0 is the feature function of each feature, index 1 is the corresponding parameter function
			parameter_array.append(feature[1](df))
		return feature_df,parameter_array

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

	def build_player_universe(self,FDSession,contest_url,date="20250101",contestID = ""): #Cole: this desperately needs documentation. Entire data structure needs documentation
		if date != "20250101":
			sql = "SELECT * FROM hist_fanduel_data Where Sport='MLB' And Date="+"'" +date+"' And contestID=" + "'" +contestID+"'"
			FD_player_data= dbo.read_dict_from_db(sql,['Player']).values()
			teams,starting_lineups = ds.mlb_starting_lineups(date)
		else:
			FD_player_data = FDSession.fanduel_api_data(contest_url)['players']#Cole:need to build some sort of test that FD_names and starting lineup names match - Ian: players now get mapped in the mlb_starting_lineups function itself.
			teams,starting_lineups = ds.mlb_starting_lineups() #Cole: need to write verification that all required teams have lineups
		omitted_teams = []
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
			db_df = self.get_db_gamedata(FD_playerid,player_type,end_date=Ugen.previous_day(date).replace("-",""))
 			player_key = FD_playerid + '_' + player_type
			if player_key == db_df['name'][0]:
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



nba=NBA()

# dbo.delete_by_date(nba.sport,'hist_event_data','2015-02-26','2015-02-26')
# dbo.delete_by_date(nba.sport,'hist_player_data','2015-02-26','2015-02-26')

# events=nba.get_daily_game_data('2014-10-28','2015-04-15',True) #2014 regular season
# events=nba.get_daily_game_data('2015-11-18','2015-11-28',True) #2015 - last historize

date='2015-11-27'
def get_contests(sport,date): #Ian: Move to backtest module
	query={'sport':sport,'date':dt.datetime.strptime(date,'%Y-%m-%d')}
	resultset=dbo.read_from_db('hist_fanduel_data',query)
	return [contest['contest_ID'] for contest in resultset]

contest_list=get_contests('NBA',date)

player_universe=nba.build_player_universe(0,0,date,contest_list[0])

# dataset=nba.get_db_gamedata('DeMar DeRozan','2011-12-31','2015-12-10')

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(player_universe)



##IAN TO DO:
#1: Player Maps
#2: build_player_universe function
