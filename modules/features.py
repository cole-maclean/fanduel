import numpy
import pandas as pd
import math
import datetime as dt
import database_operations as dbo


# dict_Structure={'2015':{'TOR':{'PG':65,'SG':60}},'2014':{'TOR':,...}}

class FD_features(): #Ian: some features are going to be unique to each sport, maybe split into different classes
	def __init__(self, sport, features, teams):
		self.sport=sport
		if self.sport=='NBA':
			self.seasons={'2014':['2014-10-28','2015-04-15'],'2015':['2015-10-27','2016-04-13']} #could split this up into 4 quarters for each season for more representative averages
			self.positions=['PG','SG','SF','PF','C']
			if 'opposing_defense_PA' in [feature[0] for feature in features]:
				self.defense_season_avgs={season:{team:self.opposing_defense_stats(team,season) for team in teams} for season in self.seasons.keys()}
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

	def FD_median(self,df):
		median_df =pd.rolling_median(df['FD_points'],window=12)
		return median_df.fillna(median_df.mean())

	def param_FD_median(self,df):
		medn =df['FD_points'].tail(12).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

	def FD_median_5(self,df):
		median_df =pd.rolling_median(df['FD_points'],window=5)
		return median_df.fillna(median_df.mean())

	def param_FD_median_5(self,df):
		medn =df['FD_points'].tail(5).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

	def opposing_defense_PA(self,df):
		df['opponent']=df.apply(self.determine_opponent,axis=1)##identify opposing team
		return df.apply(self.opposing_defense_stats,axis=1)
	
	def param_opposing_defense_PA(self,df):
		return

	def determine_opponent(self,df):
		if df['team']==df['home_team']:
			return df['away_team']
		else:
			return df['home_team']

	def opposing_defense_stats(self,team,season):
		# print 'season: %s team: %s position: %s' % (season,team,position)
		dateframe={"$gte":dt.datetime.strptime(self.seasons[season][0],'%Y-%m-%d'),
					"$lte":dt.datetime.strptime(self.seasons[season][1],'%Y-%m-%d')}
		db_df=pd.DataFrame(dbo.read_from_db('hist_event_data',{'sport':self.sport,'date':dateframe, "$or":[{'home_team':team}, 
									{'away_team':team}]},{'gameID':1,'home_team':1,'away_team':1,'sport':1,'_id':0}))
		db_df['team']=team #team is defensive team
		db_df['off_team']=db_df.apply(self.determine_opponent,axis=1)

		points_allowed_df=db_df.apply(self.position_FD_points,axis=1)
				
		return {'PG':points_allowed_df[0].mean(),'SG':points_allowed_df[1].mean(),
					'SF':points_allowed_df[2].mean(),'PF':points_allowed_df[3].mean(),
						'C':points_allowed_df[4].mean()}

	def position_FD_points(self,df):
		db_data=dbo.read_from_db('hist_player_data',{'gameID':df['gameID'],'sport':df['sport'],'team':df['off_team']},{'_id':0})
		db_data=[{key:[value] for key,value in player.iteritems()} for player in db_data] #pandas cannot convert scalars to a dataframe
		points_allowed=[sum([self.FD_points(pd.DataFrame(player)).iloc[-1] for player in db_data if player['position'][0]==position]) for position in self.positions]
		return pd.Series(points_allowed)













