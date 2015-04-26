import database_operations as dbo
import time
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import general_utils as Ugen

#player_list='Adam Wainwright, Derek Norris, Edwin Encarnacion, Brian Dozier, Luis Valbuena, Marcus Semien, Kole Calhoun, George Springer, Mookie Betts'
#Date='20150419'
#sql=

def fanduel_lineup_points(playerlist,Date):
	player_list=playerlist.split(', ')
	#build dict of stats for lineup on given date
	player_dict={}
	for player in player_list:
		sql="SELECT * FROM hist_player_data WHERE Sport = 'MLB' AND Player = "+ "'" +player+"'" + " AND Date = "+ "'" +Date+"'"
		player_data=dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
		#print if a certain player was not found!!
		for player_key,stat_dict in player_data.iteritems():
			player_dict[player]=stat_dict
	FD_points=0
	for player,stats in player_dict.iteritems():
		# print player
		# os.system('pause')
		outs=0
		if (int(stats['Stat5'])-int(stats['Stat7']))>0: #if outs is negative, we don't want to add it!
				outs=int(stats['Stat5'])-int(stats['Stat7'])
		if stats['Player_Type']== 'batter':
				FD_points= (int(stats['Stat1'])*1 + int(stats['Stat2'])*2 + int(stats['Stat3'])*3 + int(stats['Stat4'])*4 + int(stats['Stat6'])*1 + int(stats['Stat10'])*1
											 + int(stats['Stat11'])*1 + int(stats['Stat8'])*1 + int(stats['Stat13']) * 1 - (outs*.25))+FD_points
		elif stats['Player_Type']== 'pitcher':
			FD_points = (int(stats['Stat1'])*4 - int(stats['Stat7'])*1 + int(stats['Stat9'])*1 + float(stats['Stat4'])*1)+FD_points
		else:
			print 'unknown positions for %s' %player
	#Cell('Output',1,1).value=player_dict
	return FD_points

# points=fanduel_lineup_points(player_list,Date)
# print points


def mlb_starting_lineups(date): #take date as string 'YYYY-MM-DD'
	url='http://www.baseballpress.com/lineups/'+date
	content= urllib2.urlopen(url).read()
	soup = BeautifulSoup(content)
	team_map = Ugen.excel_mapping("Team Map",8,6)
	team_list=[]
	pitcher_list=[]
	lineups_list=[]
	for team in soup.findAll("div",{"class":"team-data"}):
		team_list.append(team_map[team.find("div",{"class":"team-name"}).get_text()])
		pitcher_list.append(team.find("a",{"class":"player-link"}).get_text())
	for table in soup.findAll("div",{"class":"cssDialog clearfix"}):
		table_string=table.get_text()
		home_lineup=[]  
		away_lineup=[]
		if table_string.count("9. ")==2:
			for j in range(1,10):
				name_list_raw=table_string[table_string.find(str(j)+". ")+3:].split(" (")
				home_lineup.append(name_list_raw[0])
				name_list_raw=table_string[table_string.find((str(j)+". "),table_string.find(str(j)+". ")+3)+3:].split(" (")
				away_lineup.append(name_list_raw[0])
			lineups_list.append(home_lineup)
			lineups_list.append(away_lineup)
		else:
			lineups_list.append(['no home_lineup listed'])
			lineups_list.append(['no away_lineup listed'])
	i=0
	for e in lineups_list: #NEED TO ENSURE EACH LIST IS THE SAME LENGTH
		lineups_list[i].reverse()
		lineups_list[i].append(pitcher_list[i])
		lineups_list[i].append(team_list[i])
		lineups_list[i].reverse()
		i=i+1
	return lineups_list
a=mlb_starting_lineups('2015-04-25')
Cell('Output',1,1).value=a
os.system('pause')








# sql = "SELECT * FROM hist_player_data WHERE Sport = 'MLB'"
# db_data= dbo.read_from_db(sql,["Player","GameID","Player_Type"],True)
# xml_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in xml_team_list:
#         xml_team_list.append(Player)


# sql = "SELECT * FROM hist_fanduel_data WHERE Sport = 'MLB'"
# db_data = dbo.read_from_db(sql,["Date","Player","Position","contestID"],True)

# fanduel_team_list=[]
# for player,stat_dict in db_data.iteritems():
#     Player=stat_dict['Player']
#     if Player not in fanduel_team_list:
#         fanduel_team_list.append(Player)

# test_player=Cell(1,10).value

# if test_player.encode('latin_1') in xml_team_list:
#     print 'player found in list'
# else:
#     print 'player not found in list'
# os.system('pause')

# i=2
# for e in fanduel_team_list:
#     if e not in xml_team_list:
#         split_name=e.split(' ',1)
#         Cell('Output',i,1).value=split_name[0]
#         Cell('Output',i,2).value=split_name[1]
#         i=i+1

# i=2
# for e in xml_team_list:
#     if e not in fanduel_team_list:
#         split_name=e.decode('latin_1').split(' ',1)
#         Cell('Output',i,3).value=split_name[0]
#         Cell('Output',i,4).value=split_name[1]
#         i=i+1


#Remove duplicate rows SQL statement
#ALTER IGNORE TABLE hist_backtest_data ADD UNIQUE KEY idx1(date);
#Append column to table
#ALTER TABLE hist_fanduel_data ADD contestID TEXT 
#Delete single row by ID
#DELETE FROM hist_lineup_optimizers WHERE DataID=8 LIMIT 1