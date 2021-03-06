import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D
import numpy
from sklearn.feature_selection import f_regression
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.metrics import r2_score
from sklearn.cross_validation import train_test_split
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest
import math

class Model():
	def __init__(self,model_df,player,target): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		self.player = player
		self.model_data = model_df
		self.target = target
		self.dataset_length = len(model_df[self.target])
		self.target_matrix = numpy.array(model_df[self.target]).astype(float)
		self.feature_matrix = numpy.array([[model_df[key][index] for key in model_df.keys() if key != self.target] for index in range(0,len(model_df[self.target]))]).astype(float)
		self.feature_labels = [feature for feature in  model_df.keys() if feature !=self.target]

	def best_estimator(self, X, y):
		try:
			pca = PCA(n_components=2)
			selection = SelectKBest(k=2)
			combined_features = FeatureUnion([("pca", pca), ("univ_select", selection)])
			X_features = combined_features.fit(X, y).transform(X)
			regr = linear_model.LassoCV()
			pipeline = Pipeline([("features", combined_features), ("regression", regr)])

			if 'batter' in self.player:
				param_grid = dict(features__pca__n_components=[1],
				                  features__univ_select__k=[1])
			else:
				param_grid = dict(features__pca__n_components=[1,2,3,4],
				                  features__univ_select__k=[1,2,3,4])

			grid_search = GridSearchCV(pipeline, param_grid=param_grid, verbose=0)
			grid_search.fit(X, y)
			self.modelled = True
			regr = grid_search
			self.R2=r2_score(self.target_matrix,regr.predict(self.feature_matrix)) #Ian: should do R2 on predicted points vs. points on a given day
			return regr
		except ValueError,e:
			print e
			self.modelled = False
			return None

	def lin_regression(self, X, y): #Ian: test
		try:
			regr = linear_model.LassoCV()
			regr.fit(X,y)
			self.modelled = True
			self.R2=r2_score(self.target_matrix,regr.predict(self.feature_matrix))
			return regr
		except ValueError,e:
			print e
			self.modelled = False
			return None

	def split_training_test_data(self,test_frac):
		self.training_feature_matrix,self.test_feature_matrix,self.training_target_matrix,self.test_target_matrix= train_test_split(self.feature_matrix,self.target_matrix,test_size=test_frac,random_state=42)
		return self

	def min_max_scaling(self,feature_data): #SVM's and K-means clustering are affected by feature scaling
		scaler = MinMaxScaler
		rescaled_feature = scaler.fit_transform(feature_data)
		return rescaled_feature

	def FD_points_model(self,visualize = False): #Cole: need to indentify minimum dataset required to model, flag if player unmodelled
		self.split_training_test_data(0.1)
		# self.model = self.best_estimator(self.training_feature_matrix,self.training_target_matrix)
		self.model = self.lin_regression(self.training_feature_matrix,self.training_target_matrix)
		if self.modelled:
			if visualize:
				num_plots=len(self.feature_labels)
				fig = plt.figure(figsize=(16, 8.65))
				for indx,feature in enumerate(self.feature_labels):
					ax = fig.add_subplot(num_plots,1,indx+1)
					x=self.training_feature_matrix[:,indx]
					y=self.training_target_matrix
					z = numpy.polyfit(x,y,1)
					p = numpy.poly1d(z)
					if indx==0: ax.set_title(self.player) 
					ax.plot(x, y,'bo',x,p(x),'r--')
					ax.set_xlabel(self.feature_labels[indx])
					ax.set_ylabel(self.target)
				plt.show()	
				# raw_input("enter to continue")
		else:
			print self.player + " not modelled"
		return self



