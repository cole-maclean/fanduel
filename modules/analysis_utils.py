import Sport
import Model
import matplotlib.pyplot as plt
import operator
from scipy.stats import norm
import numpy as np

def best_chunk_size():
	MLB= Sport.MLB()
	db_data = MLB.get_db_gamedata("20140401","20150422")
	first_guy = 'Brandon Finnegan_pitcher'
	for player,data in db_data.iteritems():
		if data['Player_Type'][-1] == 'pitcher':
			if player != first_guy:
				for key,player_data in data.iteritems():
					db_data[first_guy][key].extend(player_data)
	all_data = db_data[first_guy]
	chunk_coefs = test_chunk_size(MLB,all_data)
	return dict(sorted(chunk_coefs.iteritems(), key=operator.itemgetter(1), reverse=True)[:3])

def test_chunk_size(MLB,hist_data):#Cole: How do we generalize this method. Some out-of-box method likely exists. Defs need to refactor
	FD_points = MLB.FD_points(hist_data)
	model_confidence = {}
	for chunk_size in range(22,23):
		feature_dict = {}
		feature_dict['FD_points'] = []
		feature_dict['FD_avg' + str(chunk_size)] = []
		for indx,FD_point in enumerate(FD_points):
			reverse_index = len(FD_points)-indx -1
			try:
				avg_chunk_list = [FD_points[chunk_indx] for chunk_indx in range(reverse_index-chunk_size,reverse_index-1)]
				feature_dict['FD_points'].append(FD_points[reverse_index]) #Cole:Need to do some testing on most informative hist FD points data feature(ie avg, trend, combination)
				feature_dict['FD_avg' + str(chunk_size)].append(MLB.avg_stat(avg_chunk_list))
			except IndexError:
				break
		model = Model.Model(feature_dict,chunk_size)
		model.FD_points_model(True)
		if model.modelled:
			model_confidence[chunk_size] = model.model.score(model.test_feature_matrix,model.test_target_matrix)
		else:
			model_confidence[chunk_size] = 0
	return model_confidence

def check_model_accuracy():
	model_accuracy = {}
	MLB= Sport.MLB()
	db_data = MLB.get_db_gamedata("20140401","20150422")
	for player,data in db_data.iteritems():
		model_data = MLB.build_model_dataset(data)
		model  = Model.Model(model_data,player)
		model.FD_points_model(False)
		if model.modelled:
			model_accuracy[player] = model.model.score(model.test_feature_matrix,model.test_target_matrix)
		else:
			model_accuracy[player] = 0
	return model_accuracy

def plot_model_accuracy():
	accuracies = check_model_accuracy()
	# Fit a normal distribution to the data:
	data = np.array(accuracies.values())
	print data
	print np.mean(data[np.nonzero(data)])
	print np.median(data[np.nonzero(data)])
	mu, std = norm.fit(data)
	# Plot the histogram.
	plt.hist(data, bins=250, normed=True, alpha=0.6, color='g')
	# Plot the PDF.
	xmin, xmax = plt.xlim()
	x = np.linspace(xmin, xmax, 100)
	p = norm.pdf(x, mu, std)
	plt.plot(x, p, 'k', linewidth=2)
	title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
	plt.title(title)
	plt.show()

