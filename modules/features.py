import numpy
import pandas as pd
def FD_points(df):
	if df['Player_Type'][0] == 'batter':
		df['FD_points'] = (df['singles']*1+df['doubles']*2+df['triples']*3+
						df['home_runs']*4+df['rbi']*1+df['runs']*1+
							df['walks']*1+df['stolen_bases']*1+df['hit_by_pitch']*1+
							(df['at_bats'] -df['hits'])*-.25)
	else:
		df['FD_points']= (df['win']*4+df['earned_runs']*-1+
							df['strike_outs']*1+df['innings_pitched']*1)	
	return df['FD_points']

def FD_median(df):
	return pd.rolling_median(df['FD_points'],window=2)