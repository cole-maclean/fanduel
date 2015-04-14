import data_scrapping as ds
import database_operations as dbo
import collections
import XMLStats
import os

#sport_data_dict = {'NHL':{:}}
class Sport():
	def __init__(self,sport):
		self.sport = sport
		self.gameid = None

	def events(self,event_date):
		return XMLStats.main(self,'events',{'sport':self.sport,'date':event_date})['event']

	def gameids(self): #Cole: Returns namedtuple of [lastgameid,list of all gameids in db]
		gameid_data = collections.namedtuple("gameid_data", ["lastgameid", "all_gameids"])
		sql = "SELECT hist_player_data.GameID FROM hist_player_data WHERE Sport = '"+ self.sport +"' ORDER BY data_load_timestamp DESC"
		query_data = dbo.read_from_db(sql,['GameID'],True)
		return gameid_data(query_data.keys()[0],query_data.keys()) #Cole: TODO error catching, ie what if first data load every, return will be nothing

	def get_daily_game_data(self,event_dates):#Cole:event_date format is yyyyMMdd, must be a list
		for event_date in event_dates:
			day_events = self.events(event_date)
			update_list = ([game['event_id'] for game in day_events if game['event_status'] == 'completed'
							 and game['season_type'] == 'regular' or 'post' and game['event_id']])
			all_game_data = {}
			for game_id in update_list:
				self.gameid = game_id
				game_data = XMLStats.main(self,'boxscore',None)
				all_game_data[game_id] = game_data
		return all_game_data
class NHL(Sport):
	def __init__(self):
		pass