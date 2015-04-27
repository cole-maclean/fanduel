import Sport
import Model
import operator

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
			model_confidence[chunk_size] = model.model.estimator_.coef_
		else:
			model_confidence[chunk_size] = 0
	return model_confidence