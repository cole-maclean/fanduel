from sklearn import linear_model
import numpy
import os
import Sport
import data_scrapping as ds
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
# MLB.get_daily_game_data('20150703','20150710',True) #LAST HISTORIZE
#backtest.hist_model_points()

backtest.run_hist_lineups()
