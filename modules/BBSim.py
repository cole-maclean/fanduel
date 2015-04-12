import database_operations as dbo

def BBSim():
	SQL = "SELECT * FROM autotrader.atbat ORDER BY game_id, num, inning, half"
	return dbo.read_from_db(SQL,[0,3])

print BBSim()