import data_scrapping as ds
class Sport():
	def __init__(self,sport,last_game_id):
		self.sport = sport
		self.last_game_id = last_game_id

	def update_data(self):
		import_result = ds.update_gamedata(self.sport,self.last_game_id)


class NHL(Sport):
	def __init__(self):
		pass