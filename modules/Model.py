import matplotlib.pyplot as plt
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
import math
class Model():
	def __init__(self,model_data,player): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		self.player = player
		self.model_data = model_data
		self.target = 'FD_points'
		self.dataset_length = len(model_data[self.target])
		self.target_matrix = numpy.array(model_data[self.target])
		self.feature_matrix = numpy.array([[model_data[key][index] for key in model_data.keys() if key != self.target] for index in range(0,len(model_data[self.target]))])
		self.feature_labels = [feature for feature in  model_data.keys() if feature !=self.target]

	def linear_regression(self):
		if self.training_feature_matrix.any():
			regr = linear_model.LinearRegression()
			regr.fit(self.training_feature_matrix,self.training_target_matrix)
			self.modelled = True
			return regr
		else:
			self.modelled = False
			return None	
	
	def split_training_test_data(self,percent_training):
		len_train = self.dataset_length*percent_training
		self.training_target_matrix = self.target_matrix[0:len_train]
		self.test_target_matrix = self.target_matrix[len_train:self.dataset_length]
		self.training_feature_matrix = self.feature_matrix[0:len_train]
		self.test_feature_matrix = self.feature_matrix[len_train:self.dataset_length]
		return self

	def min_max_scaling(self,feature_data):
		scaler = MinMaxScaler
		rescaled_feature = scaler.fit_transform(feature_data)
		return rescaled_feature

	def FD_points_model(self,visualize = False): #Cole: need to indentify minimum dataset required to model, flag if player unmodelled
		self.prune_features('day_of_month')
		self.split_training_test_data(0.9)
		self.model = self.linear_regression()
		if self.modelled:
			if visualize:
				plt.scatter(self.training_feature_matrix, self.training_target_matrix,  color='black')
				plt.plot(self.training_feature_matrix, self.model.predict(self.training_feature_matrix), color='blue',linewidth=3)
				plt.scatter(self.test_feature_matrix, self.test_target_matrix,  color='red')
				plt.show()
		else:
			print self.player + " not modelled"
		return self

	def prune_features(self,spurious_feature):
		if self.feature_matrix.any():
			spurious_index = self.feature_labels.index(spurious_feature)
			k = len(self.feature_labels) - 1
			self.selector = SelectKBest(f_regression,k=k).fit(self.feature_matrix,self.target_matrix)
			self.feature_labels = [feature for indx,feature in enumerate(self.feature_labels) if self.selector.pvalues_[indx] > self.selector.pvalues_[spurious_index]]
			self.feature_matrix =  numpy.array([[self.model_data[key][index] for key in self.feature_labels if key != self.target] for index in range(0,len(self.model_data[self.target]))])
		else:
			self.features = []
		return self

	def scatter(self,x_data,y_data,xlabel,ylabel): #Cole: this should be taken out of model and develop seperate general vizulization tools
		fig = plt.figure()
		ax = fig.add_subplot(1,1,1)
		ax.plot()
		ax.set_title(self.player)
		ax.set_xlabel(xlabel)
		ax.set_ylabel(ylabel)
		ax.scatter(x_data,y_data)
		plt.show()





