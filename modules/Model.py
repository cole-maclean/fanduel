import matplotlib.pyplot as plt
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from sklearn.preprocessing import MinMaxScaler
import math
class Model():
	def __init__(self,model_data): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		self.model_data = model_data
		self.target = 'FD_points'
		self.dataset_length = len(model_data[self.target])
		self.target_matrix = numpy.array(model_data[self.target])
		self.feature_matrix = numpy.array([[model_data[key][index] for key in model_data.keys() if key != self.target] for index in range(0,len(model_data[self.target]))])
		self.feature_labels = [feature for feature in  model_data.keys() if feature !=self.target]

	def regression(self):
		pass

	def split_training_test_data(percent_training):
		len_train = self.dataset_length*percent_training
		self.training_target_matrix = self.target_matrix[0:len_train]
		self.test_target_matrix = self.target_matrix[len_train:self.dataset_length]
		self.training_feature_matrix = self.feature_matrix[0:len_train]
		self.test_feature_matrix = self.feature_matrix[len_train:self.dataset_length]

	def min_max_scaling(self,feature_data):
		scaler = MinMaxScaler
		rescaled_feature = scaler.fit_transform(feature_data)
		return rescaled_feature

	def FD_points_model(self,visualize = False): #Cole: need to indentify minimum dataset required to model, flag if player unmodelled
		if visualize:
			for indx,feature in enumerate(self.feature_labels):
				feature_data = self.feature_matrix[:,indx]
				self.visualize(feature_data,self.target_matrix,feature,self.target)

	def prune_features(self,spurious_feature):
		if self.feature_matrix.any():
			spurious_index = self.feature_labels.index(spurious_feature)
			k = len(feature_labels) - 1
			self.selector = SelectKBest(f_classif,k=k).fit(feature_matrix,self.target_data)
			self.features = [feature for indx,feature in enumerate(feature_labels) if self.selector.pvalues_[indx] > self.selector.pvalues_[spurious_index]]
		else:
			self.features = []
		return self

	def visualize(self,x_data,y_data,xlabel,ylabel): #Cole: this should be taken out of model and develop seperate general vizulization tools
		fig = plt.figure()
		ax = fig.add_subplot(1,1,1)
		ax.plot()
		ax.set_xlabel(xlabel)
		ax.set_ylabel(ylabel)
		ax.scatter(x_data,y_data)
		plt.show()




