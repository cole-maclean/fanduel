from sklearn import linear_model
import numpy
import os

def test():
	feature_matrix = numpy.array(Cell("Output",1,1).value)
	feature_matrix.astype(float)
	target_matrix = numpy.array(Cell("Output",1,2).value)
	target_matrix.astype(float)
	print target_matrix
	regr = linear_model.LinearRegression()
	regr.fit(feature_matrix,target_matrix)
	return feature_matrix

print test()
os.system("pause")

