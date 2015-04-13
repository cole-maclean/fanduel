import database_operations as dbo

def BBSim():
	batting_SQL = "SELECT * FROM autotrader.atbat WHERE game_id = '2015/04/07/anamlb-seamlb-1' ORDER BY game_id, num"
	pitching_SQL = "SELECT * FROM autotrader.pitch WHERE game_id = '2015/04/07/anamlb-seamlb-1' ORDER BY game_id, num, id"
	batting_data = dbo.read_from_db(batting_SQL,["game_id","num"],True)
	pitching_data = dbo.read_from_db(pitching_SQL,["game_id","num","id"],True)
	for key, pitching_event in pitching_data.iteritems():
		print pitching_event
		Cell("Baseball Simulation","clPitch").value = pitching_event['des']
		Cell("Baseball Simulation","clPitcher").value = pitching_event['pitcher']
		Cell("Baseball Simulation","clBatter").value = pitching_event['batter']
		Cell("Baseball Simulation","cl1st").value = pitching_event['on_1b']
		Cell("Baseball Simulation","cl2nd").value = pitching_event['on_2b']
		Cell("Baseball Simulation","cl3rd").value = pitching_event['on_3b']
		if pitching_event['type'] == "X":
			Cell("Baseball Simulation","clEvent").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['event']
			Cell("Baseball Simulation","clEventDesc").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['des']
			Cell("Baseball Simulation","clOut").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['o']
			Cell("Baseball Simulation","clHomeScore").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['home_team_runs']
			Cell("Baseball Simulation","clAwayScore").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['away_team_runs']
			Cell("Baseball Simulation","clInning").value = batting_data['2015/04/07/anamlb-seamlb-1_' + str(pitching_event['num'])]['inning']
		os.system('pause')
	return pitching_data
print BBSim()
os.system('pause')