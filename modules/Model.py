import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.cross_validation import train_test_split
import math
class Model():
	def __init__(self,model_data,player): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		self.player = player
		self.model_data = model_data
		self.target = 'FD_points'
		self.dataset_length = len(model_data[self.target])
		self.target_matrix = numpy.array(model_data[self.target]).astype(float)
		self.feature_matrix = numpy.array([[model_data[key][index] for key in model_data.keys() if key != self.target] for index in range(0,len(model_data[self.target]))]).astype(float)
		self.feature_labels = [feature for feature in  model_data.keys() if feature !=self.target]
	def linear_regression(self):
		if len(set(self.training_target_matrix)) > 1 and len(self.training_target_matrix) > 3: #Cole: data must contain sufficent datapoints to model
			try:
				regr = linear_model.RANSACRegressor(linear_model.LinearRegression()) #Cole: Need to investigate more to find best model to use
				regr.fit(self.training_feature_matrix,self.training_target_matrix)
				self.modelled = True
				return regr
			except ValueError:
				self.modelled = False
				return None
		else:
			self.modelled = False
			return None

	def split_training_test_data(self,percent_training):
		self.training_feature_matrix,self.test_feature_matrix, self.training_target_matrix,self.test_target_matrix= train_test_split(self.feature_matrix,self.target_matrix,test_size=0.1,random_state=42)
		return self

	def min_max_scaling(self,feature_data):
		scaler = MinMaxScaler
		rescaled_feature = scaler.fit_transform(feature_data)
		return rescaled_feature

	def FD_points_model(self,visualize = False): #Cole: need to indentify minimum dataset required to model, flag if player unmodelled
		#self.prune_features('day_of_month')
		self.split_training_test_data(0.9)
		self.model = self.linear_regression()
		if self.modelled:
			if visualize:
				if len(self.feature_labels) == 1:
					fig = plt.figure()
					ax = fig.add_subplot(1,1,1)
					ax.plot()
					ax.set_title(self.player)
					ax.set_xlabel(self.feature_labels[0])
					ax.set_ylabel(self.target)
					ax.scatter(self.training_feature_matrix, self.training_target_matrix,  color='black')
					plt.plot(self.training_feature_matrix, self.model.predict(self.training_feature_matrix), color='blue',linewidth=3)
					plt.scatter(self.test_feature_matrix, self.test_target_matrix,  color='red')
					plt.show()
				elif len(self.feature_labels) == 2:
					fig = plt.figure(figsize=(14,6))
					ax = fig.add_subplot(1, 2, 1, projection='3d')
					ax.scatter(self.training_feature_matrix[:,0],self.training_feature_matrix[:,1], self.training_target_matrix)
					ax.set_title(self.player)
					ax.set_xlabel(self.feature_labels[0])
					ax.set_ylabel(self.feature_labels[1])
					ax.set_zlabel(self.target)
					plt.show()
				else:
					print "higher dimensions unplottable"				
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




