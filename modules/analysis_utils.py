import Sport

def best_chunk_size():
	db_data = self.get_db_gamedata("20140401","20150422")
	all_data = []
	for player,data in db_data:
		all_data.append(data)
	MLB= Sport.MLB()
	all_model_data = MBL.build_model_dataset(all_data)
	print all_model_data