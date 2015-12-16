import numpy
import pandas as pd
import math
import datetime as dt
import database_operations as dbo
import general_utils as Ugen

###             FEATURES IDEAS
##---------------------------------------
##Vegas projected points scored
##DVP "average points given up by a defense against a position vs the league average"

##For last 5,10,15 mean/median we have to be careful with these when we cross over between seasons...
###(contd) (for example, last 15 games may have 5 from 2015 season and 10 from 2014 season...how to avoid this??


class FD_features(): #Ian: some features are going to be unique to each sport, maybe split into different classes?
	def __init__(self, sport, features=[]):
		self.sport=sport
		if self.sport=='NBA':
			self.seasons={'2012':['2012-10-30','2013-04-17'],'2013':['2013-10-29','2014-04-16'], #'2016-04-16'<-- 2015 end date 
							'2014':['2014-10-28','2015-04-15'],'2015':['2015-10-27','2015-12-10']} #Ian: have to manually update last date, reconfig?
			self.num_splits={'2011':4,'2012':8,'2013':8,'2014':8,'2015':3} #2011 was a lockout, 2015 is underway
			self.season_ranges={season:Ugen.split_datetime_range(dates[0],dates[1],self.num_splits[season]) 
									for season,dates in self.seasons.iteritems()}
			self.split_seasons={season+'-'+str(indx):date_range for season,split_list in self.season_ranges.iteritems() for indx,date_range in enumerate(self.season_ranges[season])}
			# self.seasons_dt={season:[dt.datetime.strptime(dates[0],'%Y-%m-%d'),dt.datetime.strptime(dates[1],'%Y-%m-%d')] 
			# 						for season,dates in self.seasons.iteritems()}
			self.positions=['PG','SG','SF','PF','C']
			self.teams=['MIL', 'MIN', 'TOR', 'ATL', 'BOS', 'DET', 'DEN', 'NO', 'DAL', 'BKN', 'POR', 'ORL', 'MIA', 'CHI', 
						'NY', 'CHA', 'UTA', 'GS', 'CLE', 'HOU', 'WAS', 'LAL', 'PHI', 'PHO', 'MEM', 'LAC', 'SAC', 'OKC', 'IND', 'SA']
			if 'opposing_defense_PA' in [feature[0] for feature in features]: #Ian: put 2012/2013/2014 seasons in database
				self.defense_season_avgs={season:{team:self.opposing_defense_stats(team,season) for team in self.teams} 
												for season in self.split_seasons.keys()} 
		elif self.sport=='MLB':
			pass

	def FD_points(self,df):
		if self.sport=='MLB':
			if df['Player_Type'][0] == 'batter':
				df['FD_points'] = (df['singles']*1+df['doubles']*2+df['triples']*3+
								df['home_runs']*4+df['rbi']*1+df['runs']*1+
									df['walks']*1+df['stolen_bases']*1+df['hit_by_pitch']*1+
									(df['at_bats'] -df['hits'])*-.25)
			else:
				df['FD_points']= (df['win']*4+df['earned_runs']*-1+
									df['strike_outs']*1+df['innings_pitched']*1)	
		elif self.sport=='NBA':
			df['FGM2']=df['FGM']-df['3FGM'] #calculate number of 2-point FGs made
			df[df['FGM2']<0]=0 #replace negative values (i.e. only three pointers made) with 0
			df['FD_points']=(df['3FGM']*3+df['FGM2']*2+df['FTM']*1+df['rebounds']*1.2+df['assists']*1.5+
								df['blocks']*2+df['steals']*2+df['turnovers']*-1)
		return df['FD_points']


	def median(self,df,feature,num_events):
		median_df =pd.rolling_median(df[feature.replace('_medn','')],window=num_events)
		return median_df.fillna(median_df.mean())

	def param_median(self,df,feature,num_events):
		medn =df[feature.replace('_medn','')].tail(num_events).median() #Ian: Cole, isn't this the same as just taking the last index of df[feature]? it will already be equal to the median of last X events
		if math.isnan(medn):
			return 0
		else:
			return medn

	def mean(self,df,feature,num_events):
		mean_df =pd.rolling_mean(df[feature.replace('_mean','')],window=num_events)
		return mean_df.fillna(mean_df.mean())

	def param_mean(self,df,feature,num_events):
		mean =df[feature.replace('_mean','')].tail(num_events).mean() #Ian: Cole, isn't this the same as just taking the last index of df[feature]? it will already be equal to the median of last X events
		if math.isnan(mean):
			return 0
		else:
			return mean

	def days_rest(self,df):
		df['days_rest']=(df['date']-df['date'].shift()).fillna(0)
		return df.apply(self.convert_days_to_int,axis=1)

	def convert_days_to_int(self,df):
		days_rest=df['days_rest']
		days_int=(days_rest/numpy.timedelta64(1, 'D')).astype(int)
		return (days_int if days_int<10 else 2) #Ian: we get values like 196 between seasons, or what if they were injured? will throw off modelling..

	def param_days_rest(self,df):
		df['days_rest']=(df['today']-df['date'].shift()).fillna(0)
		return df.apply(self.convert_days_to_int,axis=1).iloc[-1]

	def opposing_defense_PA(self,df): #Ian: points allowed by opposing defense to a certain position
		df['opponent']=df.apply(self.determine_opponent,axis=1)##identify opposing team
		df['season']=df.apply(self.determine_season,axis=1)
		df['mapped_position']=df.apply(self.position_mapping,axis=1)
		return df.apply(self.defense_season_avg,axis=1)
	
	def position_mapping(self,df):
		position=('SF' if (df['position'] == 'F' or df['position'] == 'G') else df['position']) #replace 'G' or 'F' syntax used on xml stats
		return ('S'+position if df['starter']==1 else 'B'+position)

	def defense_season_avg(self,df):
		return self.defense_season_avgs[df['season']][df['opponent']][df['mapped_position']]

	def determine_season(self,df): #Ian: modify this once you get quarterly averages, etc.
		return [season for season,dates in self.split_seasons.iteritems() if df['date']>=dates[0] and df['date']<=dates[1]][0]

	def param_opposing_defense_PA(self,df):
		df['mapped_position']=df.apply(self.position_mapping,axis=1)
		df['season']=df.apply(self.determine_season,axis=1)
		return self.defense_season_avgs[df['season'].iloc[-1]][df['matchup'].iloc[-1]][df['mapped_position'].iloc[-1]]


	def determine_opponent(self,df):
		return (df['away_team'] if df['team']==df['home_team'] else df['home_team'])

	def opposing_defense_stats(self,team,season):
		dateframe={"$gte":self.split_seasons[season][0],"$lte":self.split_seasons[season][1]}
		db_df=pd.DataFrame(dbo.read_from_db('hist_event_data',{'sport':self.sport,'date':dateframe, "$or":[{'home_team':team}, 
									{'away_team':team}]},{'gameID':1,'home_team':1,'away_team':1,'sport':1,'_id':0}))
		db_df['team']=team #team is defensive team
		db_df['off_team']=db_df.apply(self.determine_opponent,axis=1)
		points_allowed_df=db_df.apply(self.position_FD_points,axis=1) #points allowed to opposing position in each game of season
		points_allowed={'SPG':points_allowed_df[0].mean(),'SSG':points_allowed_df[1].mean(),
						'SSF':points_allowed_df[2].mean(),'SPF':points_allowed_df[3].mean(),
						'SC':points_allowed_df[4].mean(),'BPG':points_allowed_df[5].mean(),
						'BSG':points_allowed_df[6].mean(),'BSF':points_allowed_df[7].mean(),
						'BPF':points_allowed_df[8].mean(),'BC':points_allowed_df[9].mean()}
		return points_allowed

	def position_FD_points(self,df): #Ian: could modify this so it returns points allowed to starters? bench players?? depending on which player you are modelling
		db_data=dbo.read_from_db('hist_player_data',{'gameID':df['gameID'],'sport':df['sport'],'team':df['off_team']},{'_id':0})
		db_data=[{key:[value] for key,value in player.iteritems()} for player in db_data] #pandas cannot convert scalars to a dataframe

		starter_points_allowed=[numpy.mean([self.FD_points(pd.DataFrame(player)).iloc[-1] for player in db_data 
								if (player['position'][0]==position and player['starter'][0]==1)]) for position in self.positions]
		bench_points_allowed=[numpy.mean([self.FD_points(pd.DataFrame(player)).iloc[-1] for player in db_data 
								if (player['position'][0]==position and player['starter'][0]==0)]) for position in self.positions]
		return pd.Series(starter_points_allowed+bench_points_allowed)













