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
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D


def hist_starting_lineups(sport,date,player_universe): #historical starting lineups for backtesting
		db_data=[sport.get_db_gamedata(player,date,date) for player in player_universe]
		return [df['player'][0] for df in db_data if (not df.empty and df['starter'][0]==1)]

def build_model_dataset(sport,df):
	print 'now building dataset for %s' % df['player'][0]
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
		print 'building player_universe for: %s' % FD_playerid
		db_df = sport.get_db_gamedata(FD_playerid,'2014-10-01',end_date=date)
		feature_df.append(build_model_dataset(sport,db_df))

	player_model_data=pandas.concat(feature_df)

	###PLOTTING
	#http://stackoverflow.com/questions/6963035/pyplot-axes-labels-for-subplots
	return


def test_nba_feature():
	nba=Sport.NBA()
	nba.backtest_date='2015-12-05'
	df=nba.get_db_gamedata('Andrew Wiggins','2011-12-31','2015-12-04')
	feature_df,param_array=nba.build_model_dataset(df)
	feature_df['date']=df['date']
	print feature_df
	print 'parameter array: %s' % param_array
	return
