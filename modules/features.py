import numpy
import pandas as pd
import math


#Ian: features are going to be unique to each sport, how do we generalize? Name functions specific to each sport?? Classes?

def FD_points(df,sport):
	if sport=='MLB': #Ian: temporary, maybe break out into different functions?
		if df['Player_Type'][0] == 'batter':
			df['FD_points'] = (df['singles']*1+df['doubles']*2+df['triples']*3+
							df['home_runs']*4+df['rbi']*1+df['runs']*1+
								df['walks']*1+df['stolen_bases']*1+df['hit_by_pitch']*1+
								(df['at_bats'] -df['hits'])*-.25)
		else:
			df['FD_points']= (df['win']*4+df['earned_runs']*-1+
								df['strike_outs']*1+df['innings_pitched']*1)	
	elif sport=='NBA':
		df['FGM2']=df['FGM']-df['3FGM'] #calculate number of 2-point FGs made
		df[df['FGM2']<0]=0 #replace negative values (i.e. only three pointers made) with 0
		df['FD_points']=(df['3FGM']*3+df['FGM2']*2+df['FTM']*1+df['rebounds']*1.2+df['assists']*1.5+
							df['blocks']*2+df['steals']*2+df['turnovers']*-1)
	return df['FD_points']

def FD_median(df):
	median_df =pd.rolling_median(df['FD_points'],window=12)
	return median_df.fillna(median_df.mean())

def param_FD_median(df):
	medn =df['FD_points'].tail(12).median()
	if math.isnan(medn):
		return 0
	else:
		return medn

def FD_median_5(df):
	median_df =pd.rolling_median(df['FD_points'],window=5)
	return median_df.fillna(median_df.mean())

def param_FD_median_5(df):
	medn =df['FD_points'].tail(5).median()
	if math.isnan(medn):
		return 0
	else:
		return medn