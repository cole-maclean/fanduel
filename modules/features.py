import numpy
import pandas as pd
import math
import datetime as dt
import database_operations as dbo


###             FEATURES IDEAS
##---------------------------------------
##Days Rest
##Vegas projected points scored
##Usage rate ("percentage of a teams possesions a player 'uses' while in game")
##Player efficiency rating ("The overall rating of a players per minute statistical production")
##Pace ("the number of possesions a team uses per game")
##Defensive efficiency "the number of points a team allows per 100 possesions"
##DVP "average points given up by a defense against a position vs the league average"
##FGA: L2, L5, S (avg)
##Minutes: L2,L5,S (avg)
##FP: L2, L5, S, Floor, Ceiling
##last 3,5,10,15 for multiple features (minutes, FD_points,FGA etc.) --> refactor so the functions take number of days as an input to avoid redunancy
##^^^^^we have to be careful with these when we cross over between seasons...
###(contd) (for example, last 15 games may have 5 from 2015 season and 10 from 2014 season...how to avoid this??


class FD_features(): #Ian: some features are going to be unique to each sport, maybe split into different classes
	def __init__(self, sport, features=[]):
		self.sport=sport
		if self.sport=='NBA':
			self.seasons={'2014':['2014-10-28','2015-04-15'],'2015':['2015-10-27','2015-12-02']} #'2016-04-13' #could split this up into 4 quarters for each season for more representative averages
			self.positions=['PG','SG','SF','PF','C']
			self.teams=['MIL', 'MIN', 'TOR', 'ATL', 'BOS', 'DET', 'DEN', 'NO', 'DAL', 'BKN', 'POR', 'ORL', 'MIA', 'CHI', 
						'NY', 'CHA', 'UTA', 'GS', 'CLE', 'HOU', 'WAS', 'LAL', 'PHI', 'PHO', 'MEM', 'LAC', 'SAC', 'OKC', 'IND', 'SA']
			if 'opposing_defense_PA' in [feature[0] for feature in features]: #Ian: could put 2014 averages in database? probably cut time in half
				self.defense_season_avgs={season:{team:self.opposing_defense_stats(team,season) for team in self.teams} for season in self.seasons.keys()} #takes 8 min to execute for all 30 teams
				# self.defense_season_avgs={season:{team:{'PG':2,'G':2,'F':2,'SG':2,'SF':2,'PF':2,'C':2} for team in self.teams} for season in self.seasons.keys()} #use this when testing other features for speed
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

	def FD_medn(self,df):
		median_df =pd.rolling_median(df['FD_points'],window=12)
		return median_df.fillna(median_df.mean())

	def param_FD_medn(self,df):
		medn =df['FD_points'].tail(12).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

	def FD_medn_5(self,df):
		median_df =pd.rolling_median(df['FD_points'],window=5)
		return median_df.fillna(median_df.mean())

	def param_FD_medn_5(self,df):
		medn =df['FD_points'].tail(5).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

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

	def minutes_medn(self,df): #Ian: median the best indicator? mean? Why 12?
		median_df =pd.rolling_median(df['minutes'],window=12)
		return median_df.fillna(median_df.mean())

	def param_minutes_medn(self,df):
		medn =df['minutes'].tail(12).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

	def minutes_medn_5(self,df): #Ian: median the best indicator? mean?
		median_df =pd.rolling_median(df['minutes'],window=5)
		return median_df.fillna(median_df.mean())

	def param_minutes_medn_5(self,df):
		medn =df['minutes'].tail(5).median()
		if math.isnan(medn):
			return 0
		else:
			return medn

	def opposing_defense_PA(self,df): #Ian: points allowed by opposing defense to a certain position
		df['opponent']=df.apply(self.determine_opponent,axis=1)##identify opposing team
		df['season']=df.apply(self.determine_season,axis=1)
		return df.apply(self.defense_season_avg,axis=1)
	
	def defense_season_avg(self,df):
		return self.defense_season_avgs[df['season']][df['opponent']][df['position']]

	def determine_season(self,df): #Ian: modify this once you get quarterly averages, etc.
		year=df['date'].strftime('%Y-%m-%d').split("-")[0]
		if year=='2014':
			season=year
		elif year=='2015' and df['date']<dt.datetime.strptime(self.seasons['2014'][1],'%Y-%m-%d'):
			season='2014'
		else:
			season='2015'
		return season

	def param_opposing_defense_PA(self,df):
		df['season']=df.apply(self.determine_season,axis=1)
		return self.defense_season_avgs[df['season'].iloc[-1]][df['matchup'].iloc[-1]][df['position'].iloc[-1]]
		# return df.apply(self.defense_season_avg,axis=1).iloc[-1] #Ian: old, incorrect way

	def determine_opponent(self,df):
		return (df['away_team'] if df['team']==df['home_team'] else df['home_team'])

	def opposing_defense_stats(self,team,season):
		# print 'season: %s team: %s position: %s' % (season,team,position)
		dateframe={"$gte":dt.datetime.strptime(self.seasons[season][0],'%Y-%m-%d'),
					"$lte":dt.datetime.strptime(self.seasons[season][1],'%Y-%m-%d')}
		db_df=pd.DataFrame(dbo.read_from_db('hist_event_data',{'sport':self.sport,'date':dateframe, "$or":[{'home_team':team}, 
									{'away_team':team}]},{'gameID':1,'home_team':1,'away_team':1,'sport':1,'_id':0}))
		db_df['team']=team #team is defensive team
		db_df['off_team']=db_df.apply(self.determine_opponent,axis=1)
		points_allowed_df=db_df.apply(self.position_FD_points,axis=1)
		points_allowed={'PG':points_allowed_df[0].mean(),'SG':points_allowed_df[1].mean(),
						'SF':points_allowed_df[2].mean(),'PF':points_allowed_df[3].mean(),
						'C':points_allowed_df[4].mean()}
		points_allowed['G']=(points_allowed['SG']+points_allowed['SF'])/2
		points_allowed['F']=(points_allowed['SF']+points_allowed['C'])/2
		return points_allowed

	def position_FD_points(self,df):
		db_data=dbo.read_from_db('hist_player_data',{'gameID':df['gameID'],'sport':df['sport'],'team':df['off_team']},{'_id':0})
		db_data=[{key:[value] for key,value in player.iteritems()} for player in db_data] #pandas cannot convert scalars to a dataframe
		points_allowed=[sum([self.FD_points(pd.DataFrame(player)).iloc[-1] for player in db_data if player['position'][0]==position]) for position in self.positions]
		return pd.Series(points_allowed)













