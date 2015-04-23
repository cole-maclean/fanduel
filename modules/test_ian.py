import database_operations as dbo

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