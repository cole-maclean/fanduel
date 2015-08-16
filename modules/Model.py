import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.metrics import r2_score
from sklearn.cross_validation import train_test_split
from sklearn.decomposition import PCA
import math
class Model():
	def __init__(self,model_data,player): #Cole: Class accepts model_data in form {'feature1':[data],feature2:[data]}
		# print model_data
		# for feature in model_data:
		# 	print len(model_data[feature])
		# os.system('pause')
		self.player = player
		self.model_data = model_data
		if player.split("_")[1]=='batter':# or player.split("_")[1]=='pitcher': 
			self.target = 'FD_points'
		else: 
			self.target='FD_points'
			#self.target='strikeouts'
		self.dataset_length = len(model_data[self.target])
		self.target_matrix = numpy.array(model_data[self.target]).astype(float)
		self.feature_matrix = numpy.array([[model_data[key][index] for key in model_data.keys() if key != self.target] for index in range(0,len(model_data[self.target]))]).astype(float)
		self.feature_labels = [feature for feature in  model_data.keys() if feature !=self.target]
		self.pc_features=False
		
	def linear_regression(self,X,y):
		try:
			regr = linear_model.Lasso(alpha = 0.1) #Cole: Need to investigate more to find best model to use
			regr.fit(X,y)
			self.modelled = True
			return regr
		except ValueError,e:
			print e
			self.modelled = False
			return None

	def split_training_test_data(self,percent_training):
		if self.pc_features:
			self.training_feature_matrix,self.test_feature_matrix, self.training_target_matrix,self.test_target_matrix= train_test_split(self.pc_feature_matrix,self.target_matrix,test_size=0.1,random_state=42)
		else:
			self.training_feature_matrix,self.test_feature_matrix, self.training_target_matrix,self.test_target_matrix= train_test_split(self.feature_matrix,self.target_matrix,test_size=0.1,random_state=42)
		return self

	def min_max_scaling(self,feature_data): #SVM's and K-means clustering are affected by feature scaling
		scaler = MinMaxScaler
		rescaled_feature = scaler.fit_transform(feature_data)
		return rescaled_feature

	def feature_PCA(self,num_components=2):
		pca=PCA(n_components=num_components)
		X=self.feature_matrix
		try:
			X_transform=pca.fit_transform(X)
			X_pc=pca.transform(X_transform)
			self.pc_feature_matrix=X_pc
			self.pc_features=True
			self.feature_labels=['pc_var'+str(num+1) for num in range(num_components)]
		except Exception,error:
			print "error in feature_PCA: %s" % str(error)
		return self


	def FD_points_model(self,visualize = False,PCA=False): #Cole: need to indentify minimum dataset required to model, flag if player unmodelled
		#self.prune_features('day_of_month') #Cole: Lasso regression automates feature selection
		if PCA:
			self.feature_PCA(1)
		self.split_training_test_data(0.9)
		self.model = self.linear_regression(self.training_feature_matrix,self.training_target_matrix)
		if self.modelled:
			if visualize:
					for indx,feature in enumerate(self.feature_labels):
						fig = plt.figure()
						ax = fig.add_subplot(1,1,1)
						ax.plot()
						ax.set_title(self.player)
						ax.set_xlabel(self.feature_labels[indx])
						ax.set_ylabel(self.target)
						x=self.training_feature_matrix[:,indx]
						y=self.training_target_matrix
						z = numpy.polyfit(x,y,1)
						p = numpy.poly1d(z)
						ax.plot(x, y,'bo',x,p(x),'r--')
						r2=r2_score(y,p(x))
						rw=3
						while Cell("Pred_Strikeouts History",rw,1).value != None:
							rw=rw+1
						Cell("Pred_Strikeouts History",rw-1,2).value=z
						Cell("Pred_Strikeouts History",rw-1,3).value=r2
						# plt.show()	
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




