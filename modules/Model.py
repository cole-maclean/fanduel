import matplotlib.pyplot as plt
class Model():
	def __init__(self,model_data):
		self.model_data = model_data

	def build_feature_dataset(self):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
			FD_points = self.FD_points(stats_data)
			feature_dict = {}
			feature_dict['FD_points'] = []
			feature_dict['five_day_avg'] = []
			feature_dict['five_day_trend'] = []
			feature_dict['day'] = []
			for indx,FD_point in enumerate(FD_points):
				reverse_index = len(FD_points)-indx
				try:
					chunk_list = [FD_points[chunk_indx] for chunk_indx in range(reverse_index-5,reverse_index-1)]
					feature_dict['FD_points'].append(FD_point)
					feature_dict['five_day_avg'].append(self.avg_stat(chunk_list))
					feature_dict['five_day_trend'].append(self.trend_stat(chunk_list))
					feature_dict['day'].append(int(str(stats_data['Date'][indx])[6:8]))
				except IndexError:
					break
			feature_data[player] = feature_dict
		return feature_data

	def prune_features(self,feature_data,target,spurious_feature):
		feature_matrix = numpy.array([[feature_data[key][index] for key in feature_data.keys() if key != target] for index in range(0,len(feature_data[target]))])
		feature_labels = [feature for feature in  feature_data.keys() if feature !=target]
		spurious_index = feature_labels.index(spurious_feature)
		target_data = numpy.array(feature_data[target])
		k = len(feature_labels) - 1
		feature_scores = SelectKBest(f_classif,k=k).fit(feature_matrix,target_data).pvalues_
		print feature_scores
		features = [feature for indx,feature in enumerate(feature_labels) if feature_scores[indx] > feature_scores[spurious_index]]
		return features

	def visualize(self):
		pass

class Utility(Model):
	def __init__(self):
		pass

	def avg_stat(self,stats_data):
		np_array = numpy.array(stats_data)
		avg =numpy.mean(np_array)
		if numpy.isnan(avg):
			return 0
		else:
			return avg

	def trend_stat(self,stats_data):
		xi = numpy.arange(0,len(stats_data))
		matrix_ones = numpy.ones(len(stats_data))
		array = numpy.array([xi,matrix_ones])
		return numpy.linalg.lstsq(array.T,stats_data)[0][0]
