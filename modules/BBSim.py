import database_operations as dbo

def BBSim():
	SQL = "SELECT * FROM autotrader.atbat ORDER BY game_id, num, inning, half"
	game_data = dbo.read_from_db(SQL,["game_id","num"],True)
	return game_data
print BBSim()
os.system('pause')