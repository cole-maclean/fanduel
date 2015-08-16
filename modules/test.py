from sklearn import linear_model
import numpy
import os
import Sport
import data_scrapping as ds
import database_operations as dbo
import backtest
import time

def test():
	feature_matrix = numpy.array(Cell("Output",1,1).value)
	feature_matrix.astype(float)
	target_matrix = numpy.array(Cell("Output",1,2).value)
	target_matrix.astype(float)
	print target_matrix
	regr = linear_model.LinearRegression()
	regr.fit(feature_matrix,target_matrix)
	return feature_matrix

# ds.historical_vegas_odds()

# MLB=Sport.MLB()
# MLB.get_daily_game_data('20150717','20150729',True) #LAST HISTORIZE
# MLB.get_daily_game_data('20150729','20150801',True) #LAST HISTORIZE


# dbo.delete_from_db('event_data','2014-05-07')
# dbo.delete_from_db('hist_player_data','2014-05-07')
# MLB.get_daily_game_data('20140507','20140507',True) 


backtest.run_hist_lineups()
# MLB.modify_db_data('20131028','20150801',{'hist_player_data':['stuff']})


#backtest.hist_model_points()


