import database_operations as dbo
import time
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import data_scrapping as ds
import general_utils as Ugen
from selenium import webdriver
import string
import pandas
import Sport
import Model
import numpy as np
import random
import datetime as dt
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d.axes3d import Axes3D


###MODEL EXPLORATION - turn this into a class

def hist_starting_lineups(sport,date,player_universe): #historical starting lineups for backtesting
		db_data=[sport.get_db_gamedata(player,date,date) for player in player_universe]
		return [df['player'][0] for df in db_data if (not df.empty and df['starter'][0]==1)]

def build_model_dataset(sport,df):
	print 'now building dataset for %s' % df['player'][0]
	feature_df= pandas.DataFrame(sport.ff.FD_points(df))
	for feature in sport.features:
		feature_df[feature[0]] = getattr(sport.ff,feature[0])(df)#Index 0 is the feature function of each feature, index 1 is the corresponding parameter function
	return feature_df

def model_exploration(): #Ian: temporary,split up
	sport=Sport.NBA()
	date='2015-12-02'
	query={'sport':sport.sport,'date':dt.datetime.strptime(date,'%Y-%m-%d'),'contest_ID':'13834'}
	FD_player_data=dbo.read_from_db('hist_fanduel_data',query)[0]['contest_dict']
	starting_players =hist_starting_lineups(sport,date,[player for player in FD_player_data.keys()])
	FD_starting_player_data = {player:player_data for player,player_data in FD_player_data.iteritems() if player in starting_players} 

	feature_df=[]
	for FD_playerid,data in FD_starting_player_data.iteritems():
		print 'building player_universe for: %s' % FD_playerid
		db_df = sport.get_db_gamedata(FD_playerid,'2014-10-01',end_date=date)
		feature_df.append(build_model_dataset(sport,db_df))

	player_model_data=pandas.concat(feature_df)


	# plt.figure()
	# player_model_data.plot(x='FD_median', y='FD_points')
	# plt.show()

	# fig = plt.figure()
	# ax = fig.add_subplot(1,1,1)
	# ax.plot()
	# ax.set_xlabel('FD_median')
	# ax.set_ylabel('FD_points')
	x1=np.array(player_model_data['FD_median'])
	x2=np.array(player_model_data['FD_median_5'])
	x3=np.array(player_model_data['opposing_defense_PA'])
	y=np.array(player_model_data['FD_points'])
	# z = np.polyfit(x,y,1)
	# p = np.poly1d(z)
	# ax.plot(x, y,'bo',x,p(x),'r--')
	# plt.show()

	# plt.figure(1)
	# plt.subplot(211)
	# plt.plot(x1,y, 'bo')

	# plt.subplot(212)
	# plt.plot(x2,y, 'ro')
	# plt.show()



	# x = range(1, 101)
	# y1 = [random.randint(1, 100) for _ in xrange(len(x))]
	# y2 = [random.randint(1, 100) for _ in xrange(len(x))]
	fig = plt.figure()
	# ax = fig.add_subplot(111)    # The big subplot
	ax1 = fig.add_subplot(211)
	ax2 = fig.add_subplot(212)

	# Turn off axis lines and ticks of the big subplot
	# ax.spines['top'].set_color('none')
	# ax.spines['bottom'].set_color('none')
	# ax.spines['left'].set_color('none')
	# ax.spines['right'].set_color('none')
	# ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')

	ax1.plot(x1, y,'bo')
	ax2.plot(x3, y,'ro')

	# Set common labels
	# ax.set_xlabel('common xlabel')
	# ax.set_ylabel('common ylabel')

	ax1.set_title('ax1 title')
	ax2.set_title('ax2 title')
	plt.show()

	###PLOTTING
	#http://stackoverflow.com/questions/6963035/pyplot-axes-labels-for-subplots
	return


def test_nba_feature():
	nba=Sport.NBA()
	df=nba.get_db_gamedata('Andrew Wiggins','2011-12-31','2015-11-17')
	feature_df,param_array=nba.build_model_dataset(df)
	print feature_df
	return