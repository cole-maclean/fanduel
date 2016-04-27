# import database_operations as dbo
import time
from bs4 import BeautifulSoup
import ast
# import data_scrapping_utils as uds
# import data_scrapping as ds
# import general_utils as Ugen
from selenium import webdriver
import string
import pandas
# import Sport
# import Model
import numpy as np
# import backtest
import random
import datetime as dt
from pandas.tools.plotting import scatter_matrix
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D
import seaborn as sns
import matplotlib as mpl
from scipy import stats


def hist_starting_lineups(sport,date,player_universe): #historical starting lineups for backtesting
		db_data=[sport.get_db_gamedata(player,date,date) for player in player_universe]
		return [df['player'][0] for df in db_data if (not df.empty and df['starter'][0]==1)]

def build_model_dataset(sport,df):
	# print 'now building dataset for %s' % df['player'][0]
	feature_df= pandas.DataFrame(sport.ff.FD_points(df))
	for feature in sport.features:
		feature_df[feature[0]] = getattr(sport.ff,feature[0])(df)#Index 0 is the feature function of each feature, index 1 is the corresponding parameter function
	return feature_df


###MODEL EXPLORATION - turn this into a class
def model_exploration(): #Ian: temporary,split up, refactor etc.
	sport=Sport.NBA()
	date='2015-12-02'
	query={'sport':sport.sport,'date':dt.datetime.strptime(date,'%Y-%m-%d'),'contest_ID':'13834'}
	FD_player_data=dbo.read_from_db('hist_fanduel_data',query)[0]['contest_dict']
	starting_players =hist_starting_lineups(sport,date,[player for player in FD_player_data.keys()])
	FD_starting_player_data = {player:player_data for player,player_data in FD_player_data.iteritems() if player in starting_players} 

	feature_df=[]
	for FD_playerid,data in FD_starting_player_data.iteritems():
		# print 'building player_universe for: %s' % FD_playerid
		db_df = sport.get_db_gamedata(FD_playerid,'2014-10-01',end_date=date)
		feature_df.append(build_model_dataset(sport,db_df))

	player_model_data=pandas.concat(feature_df)

	###PLOTTING
	#http://stackoverflow.com/questions/6963035/pyplot-axes-labels-for-subplots
	return

def plot(x,y): #x & y are lists containing (optionally) multiple x & y arrays
	fig = plt.figure(figsize=(16, 8.65))
	ax = fig.add_subplot(1,1,1)
	# ax.set_title(self.player) 
	ax.plot(x[0], y[0],'bo')
	if len(x)>1: #Ian: reconfig, and move this to Ugen
		# ax.plot(x[1],y[1],'r--')
		ax.plot(x[1],y[1],'ro')
	# ax.set_xlabel(self.feature_labels[indx])
	# ax.set_ylabel(self.target)
	plt.show()	
	return

def scatter_plot(df,columns): #columns=['col1','col2','col3']
	plotting_df=df[columns]
	fig=scatter_matrix(plotting_df, alpha=0.2, figsize=(16, 8.65), diagonal='kde')
	plt.tight_layout()
	plt.show()
	return

def r2(x, y):
    return stats.pearsonr(x, y)[0] ** 2

def seaborn_plot(df,columns,plot_type='pairplot'):
	sns.set()
	mpl.rc("figure", figsize=(16, 8.65))
	plotting_df=df[columns]
	if plot_type=='pairplot':
		sns.pairplot(plotting_df)
	elif plot_type=='corr_plot':
		sns.corrplot(plotting_df)
	sns.plt.show()
	return

def test_nba_feature():
	nba=Sport.NBA()
	nba.backtest_date='2015-12-05' #this date has to be a date they played on
	# df=nba.get_db_gamedata('Andrew Wiggins','2011-12-31','2015-12-04')
	# df=nba.get_db_gamedata('DeMar DeRozan','2011-12-31','2015-12-04')
	# df=nba.get_db_gamedata('Stephen Curry','2011-12-31','2015-12-04')
	df=nba.get_db_gamedata('Stephen Curry','2015-12-11','2015-12-31')
	# df=nba.get_db_gamedata('Kyle Lowry','2011-01-10','2015-12-04')
	feature_df,param_array=nba.build_model_dataset(df)
	feature_df['date']=df['date']
	# print feature_df
	# print 'parameter array: %s' % param_array
	return

def minutes_projection_test(date):
	sport=Sport.NBA()
	sport.backtest_date=date
	contest_list=backtest.get_contests(sport.sport,date)
	sport.backtest_contestID=contest_list[0]
	query={'sport':sport.sport,'date':dt.datetime.strptime(sport.backtest_date,'%Y-%m-%d'),'contest_ID':sport.backtest_contestID}
	FD_player_data=dbo.read_from_db('hist_fanduel_data',query)[0]['contest_dict']
	starting_players =sport.hist_starting_lineups([player for player in FD_player_data.keys()])
	FD_starting_player_data = {player:player_data for player,player_data in FD_player_data.iteritems() if player in starting_players} 

	conf_list=[]
	R2_list=[]

	for player,data in FD_starting_player_data.iteritems():
		db_df = sport.get_db_gamedata(player,'2012-10-01',end_date=Ugen.previous_day(date)) #2012/2013/2014/2015 seasons
		if db_df.empty: #Ian: need player maps!
			continue
		conf,R2=sport.ff.param_minutes(db_df)
		if conf and R2:
			conf_list.append(conf)
			R2_list.append(R2)
	# print R2_list
	# print conf_list
	# print 'R2_mean: %s R2_median: %s conf_mean: %s conf_median: %s' % (np.mean(R2_list),np.median(R2_list),np.mean(conf_list),np.median(conf_list))
	return	

def lineups_explorations(hist_lineups_dict):
	lineup_points_list=[]
	player_universe_size=[]
	sum_confidence=[]
	player_points=[]
	player_proj_points=[]
	sport=Sport.NBA(historize=True)
	player_confidence=[]
	for date in hist_lineups_dict.keys():
		for contest,contest_dict in hist_lineups_dict[date].iteritems():
			lineup_points_list.append(contest_dict['points'])
			player_universe_size.append(contest_dict['player_universe_size'])
			sum_confidence.append(sum([data['confidence'] for player,data in contest_dict['roster_dict'].iteritems()]))
			player_points+=[backtest.hist_lineup_points(sport,[player],date)[0] for player in contest_dict['roster_dict'].keys()]
			player_confidence+=[data['confidence'] for player,data in contest_dict['roster_dict'].iteritems()]
			player_proj_points+=[data['projected_FD_points'] for player,data in contest_dict['roster_dict'].iteritems()]
	
	# return player_points,player_confidence,player_proj_points
	# points_diff=np.subtract(player_points,player_proj_points)
	# plot(player_confidence,points_diff)
	# print 'total mean: %s total median: %s' % (np.mean(lineup_points_list),np.median(lineup_points_list))
	large_contest_average=[contest_dict['points'] for date in hist_lineups_dict.keys() 
								for contest,contest_dict in hist_lineups_dict[date].iteritems() if contest_dict['player_universe_size']>120]
	large_contest_dates=[date for date in hist_lineups_dict.keys() 
								for contest,contest_dict in hist_lineups_dict[date].iteritems() if contest_dict['player_universe_size']>120]
	
	large_contest_average=[]
	large_contest_dates=[]
	for date in hist_lineups_dict.keys():
		for contest,contest_dict in hist_lineups_dict[date].iteritems():
			if date not in large_contest_dates and contest_dict['player_universe_size']<100:
				large_contest_dates.append(date)
				large_contest_average.append(contest_dict['points'])

	# print large_contest_dates
	# print large_contest_average		
	# print 'large_contest len: %s' % len(large_contest_average)
	# print 'large_contest mean: %s' % np.mean(large_contest_average)
	# print 'large_contest median: %s' % np.median(large_contest_average)
	plot([player_universe_size],[lineup_points_list])
	return

# merged_dict = hist_lineups_dict.copy()
# # merged_dict.update(hist_lineups_dict_2)
# merged_dict.update(hist_lineups_dict_3)
# lineups_explorations(hist_lineups_dict_3)
