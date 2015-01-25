import MySQLdb
import collections
import general_utils as Ugen
import time
def get_connection_cursor():
    with open('C:\Users\Cole\Desktop\Fanduel\Parameters.txt',"r") as myfile:
        passwd = myfile.read()
    conn = MySQLdb.Connection(db="autotrader",host="localhost",user="root",passwd=passwd);
    cur = conn.cursor()
    return cur
def get_player_data_dict(GameIDLimit):#TODO: Limits for history games and season
    cur = get_connection_cursor()
    sql = "SELECT Player, GameID, Stat1, Stat2, Stat3, Stat4, Stat5, Stat6, Stat7, Team FROM hist_player_data WHERE GameID > " + GameIDLimit
    cur.execute(sql)
    resultset = cur.fetchall()
    player_dict = collections.OrderedDict()
    for rw in resultset:
        if rw[8] != None: #Check if player is goalie, hack job need to clean
            if  rw[0] in player_dict:
                data_index = 1
                for data_point in player_dict[rw[0]]:
                    player_dict[rw[0]][data_point].append(rw[data_index])
                    data_index = data_index + 1
            else:
                player_dict[rw[0]] = build_data_dict_structure(['GameID','Assists','num','Goals','SoG','ToI','PlusMinus','PiM','Team'],rw,1)
        else:
            if  rw[0] in player_dict:
                data_index = 1
                for data_point in player_dict[rw[0]]:
                    if data_point == 'weighted_toi':
                        try:
                            if rw[7]:
                                player_dict[rw[0]][data_point].append(Ugen.getSec(rw[4]) * float(rw[7])) #Weighted goilie ToI, arbitrary div by 3 scaling
                            else:
                                player_dict[rw[0]][data_point].append(0)
                        except TypeError:
                            player_dict[rw[0]][data_point].append(0)
                    else:
                        player_dict[rw[0]][data_point].append(rw[data_index])
                    data_index = data_index + 1
            else:
                player_dict[rw[0]] = build_data_dict_structure(['GameID','num','Saves','ToI','GoalsAgainst','ShotsAgainst','SavePercent','weighted_toi','Team'],rw,1)
    return player_dict
def build_data_dict_structure(column_names, rw_data, start_rw = 0): #TODO: seems like a good place for functional thing (decorator) 
    d = collections.OrderedDict()
    for column in column_names:
        if column == 'weighted_toi': #TODO: hack job, need to clean up with functional way of allowing functions in column definition and values
            try:
                if d['SavePercent'][0] == '':
                    d[column] = [0]
                else:
                    d[column] = [Ugen.getSec(d['ToI'][0]) * float(d['SavePercent'][0])]
            except TypeError:
                d[column] = [0]
            except ValueError:
                print d['SavePercent'][0]
                print 2
                print rw_data[0]
                os.system('pause')
        else:
            d[column] = [rw_data[start_rw]]
        start_rw = start_rw + 1
    return d
def write_to_db(static_columns,static_data,write_data): #TODO: need to generalize (columns, placeholders, etc.)
    row_data = [str(v) for v in write_data.values()]
    static_data.extend(row_data)
    placeholders = ', '.join(['%s'] * (len(static_data)))
    columns = static_columns
    for i in range(1,len(row_data) + 1):
        columns = columns + ', Stat' + str(i)
    insert_mysql(columns, placeholders, static_data)
def insert_mysql(table, columns, placeholders, data):
    sql = "INSERT INTO " + table + " (%s) VALUES (%s)" % (columns, placeholders)
    cur = get_connection_cursor()
    cur.execute(sql, data)
    cur.execute('COMMIT')
    time.sleep(.1)
#def compute_avg_toi(player_data_dict,game_limit):
#Cell(1,2).value = get_player_data_dict('2014020001')['Marc-Andre Fleury']
#os.system("pause")