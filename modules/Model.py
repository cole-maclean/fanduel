import matplotlib.pyplot as plt
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
class Model():
	def __init__(self):
		pass

	def prune_features(self,feature_data,target,spurious_feature):
		feature_matrix = numpy.array([[feature_data[key][index] for key in feature_data.keys() if key != target] for index in range(0,len(feature_data[target]))])
		if feature_matrix.any():
			feature_labels = [feature for feature in  feature_data.keys() if feature !=target]
			spurious_index = feature_labels.index(spurious_feature)
			target_data = numpy.array(feature_data[target])
			k = len(feature_labels) - 1
			feature_scores = SelectKBest(f_classif,k=k).fit(feature_matrix,target_data).pvalues_
			features = [feature for indx,feature in enumerate(feature_labels) if feature_scores[indx] > feature_scores[spurious_index]]
			return features
		return []

class Visualize():
		pass

class Utility():
	def __init__(self):
		pass




