import MySQLdb
import collections
import general_utils as Ugen
import time
def get_connection_cursor():
    DB_parameters = Ugen.ConfigSectionMap('db')
    conn = MySQLdb.Connection(db=DB_parameters['db'],host="localhost",user=DB_parameters['user'],passwd=DB_parameters['password']);
    cur = conn.cursor()
    return cur
def get_data_dict_structure(sport,position):
    data_dict_structures = {'NHL':{'player':['GameID','Assists','num','Goals','SoG','ToI','PlusMinus','PiM','Team'],'goalie':['GameID','num','Saves','ToI','GoalsAgainst','ShotsAgainst','SavePercent','weighted_toi=int(Ugen.getSec(player_dict[rw_data[0]]["ToI"][-1]))*float(player_dict[rw_data[0]]["SavePercent"][-1])','Team']}} #might need to move this to config file
    return data_dict_structures[sport][position]
def get_player_data_dict(sport, GameIDLimit):#TODO: Limits for history games and season
    cur = get_connection_cursor()
    sql = "SELECT Player, GameID, Stat1, Stat2, Stat3, Stat4, Stat5, Stat6, Stat7, Team, Sport FROM hist_player_data WHERE Sport=%s AND GameID > " + GameIDLimit
    print sql
    cur.execute(sql,(sport))
    resultset = cur.fetchall()
    player_dict = collections.OrderedDict()
    for rw in resultset:
        if rw[8] != None: #Check if player is goalie, hack job need to clean
            player_dict = build_data_dict_structure(player_dict,get_data_dict_structure(sport,'player'),rw,1)
        else:
            player_dict = build_data_dict_structure(player_dict,get_data_dict_structure(sport,'goalie'),rw,1)
    return player_dict
def build_data_dict_structure(player_dict,column_names, rw_data, start_rw = 0): #TODO: seems like a good place for functional thing (decorator) 
    d = collections.OrderedDict()
    for column in column_names:
        if '=' in column:
            parsed_column = column.split("=")
            col_name = parsed_column[0]
            col_function = parsed_column[1]
            data_value = eval(col_function)
        else:
            col_name = column
            data_value = rw_data[start_rw]
        if rw_data[0] in player_dict and col_name in player_dict[rw_data[0]]:
            player_dict[rw_data[0]][col_name].append(data_value)
        else:
            d[col_name] = [data_value]
            player_dict[rw_data[0]] = d
        start_rw = start_rw + 1
    return player_dict
def read_from_db(sql,primary_key_col = 0):
    cur = get_connection_cursor()
    cur.execute(sql)
    resultset = cur.fetchall()
    query_dict = collections.OrderedDict()
    for rw in resultset:
        query_dict[rw[primary_key_col]] = []
        for col in rw:
            query_dict[rw[primary_key_col]].append(col)
    return query_dict
def write_to_db(table,static_columns,static_data,write_data={}): #TODO: need to generalize (columns, placeholders, etc.)
    row_data = [str(v) for v in write_data.values()]
    if row_data != []:
        static_data.extend(row_data)
    placeholders = ', '.join(['%s'] * (len(static_data)))
    columns = static_columns
    for i in range(1,len(row_data) + 1):
        columns = columns + ', Stat' + str(i)
    insert_mysql(table,columns, placeholders, static_data)
def insert_mysql(table, columns, placeholders, data):
    sql = "INSERT INTO " + table + " (%s) VALUES (%s)" % (columns, placeholders)
    cur = get_connection_cursor()
    cur.execute(sql, data)
    cur.execute('COMMIT')
    time.sleep(.1)
def load_csv_into_db(csv_file,table):
    sql = "LOAD DATA INFILE '" + csv_file + "' IGNORE INTO TABLE " + table + " FIELDS TERMINATED BY ',' IGNORE 1 LINES"
    cur = get_connection_cursor()
    cur.execute(sql)
    cur.execute('COMMIT')
    time.sleep(.1)