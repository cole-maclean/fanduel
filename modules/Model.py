import matplotlib.pyplot as plt
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
class Model():
	def __init__(self,model_data,target): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		self.model_data = model_data
		self.target = target
		self.target_matrix = numpy.array(model_data[target])
		self.feature_matrix = numpy.array([[model_data[key][index] for key in model_data.keys() if key != target] for index in range(0,len(model_data[target]))])
		self.feature_labels = [feature for feature in  model_data.keys() if feature !=target]

	def FD_points_model(self,visualize = False):
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




