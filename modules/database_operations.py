import MySQLdb
import collections
import general_utils as Ugen
import time
import os
from Tkinter import Tk
def get_connection_cursor(dict_cursor=False): #Cole: Updated to allow for db reads to return a Dict cursor
    DB_parameters = Ugen.ConfigSectionMap('db')
    conn = MySQLdb.Connection(db=DB_parameters['db'],host="localhost",user=DB_parameters['user'],passwd=DB_parameters['password']);
    conn.autocommit(True)
    if dict_cursor == True:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
    else:
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
def build_data_dict_structure(player_dict,column_names, rw_data, start_rw =  0): #TODO: seems like a good place for functional thing (decorator) 
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
def read_from_db(sql,primary_key_col = [0],dict_cursor=False):#Cole: updated to allow list of columns that make up key
    cur = get_connection_cursor(dict_cursor)
    cur.execute(sql)
    resultset = cur.fetchall()
    query_dict = collections.OrderedDict()
    for rw in resultset:
        prime_key = "_".join(str(rw[s]) for s in primary_key_col)
        if dict_cursor == True:
            query_dict[prime_key] = rw
        else:
            for col in rw:
                query_dict[prime_key].append(col)
    cur.close()
    return query_dict
def write_to_db(table,static_columns,static_data,write_data={}):
    row_data = [str(v) for v in write_data.values()]
    if row_data != []:
        static_data.extend(row_data)
    placeholders = ', '.join(['%s'] * (len(static_data)))
    columns = static_columns
    for i in range(1,len(row_data) + 1):
        columns = columns + ', Stat' + str(i)
    insert_mysql(table,columns, placeholders, static_data)
    
def insert_mysql(table, columns, data,placeholders=False):
    if placeholders:
        sql = "INSERT INTO " + table + " (%s) VALUES (%s)" % (columns, placeholders)
    else:
        sql = "INSERT INTO " + table + " (%s) VALUES (%s)" % (columns, data)
    cur = get_connection_cursor()
    try:
        if placeholders:
            cur.execute(sql,data)
        else:
            cur.execute(sql)
        cur.execute('COMMIT')
    except MySQLdb.Error, e:
        print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
    time.sleep(.1)

def load_csv_into_db(csv_file,table):
    sql = "LOAD DATA INFILE '" + csv_file + "' IGNORE INTO TABLE " + table + " FIELDS TERMINATED BY ';' IGNORE 1 LINES"
    cur = get_connection_cursor()
    cur.execute(sql)
    cur.execute('COMMIT')
    time.sleep(.1)

def get_table_last_row(table_name,table_key):
    sql="SELECT * FROM " + table_name +" ORDER BY " + table_key + " DESC LIMIT 1"
    cur = get_connection_cursor()
    cur.execute(sql)
    resultset = cur.fetchall()
    cur.close
    return resultset

def delete_from_db(table,date1): #Ian: allows you to delete a specified set of records based on date. Only works for two tables right now. Date format YYYY-MM-DD 
    if table=='event_data':
        date1=date1.replace("-","")
        column='event_id'
    elif table=='hist_player_data':
        column='Date'
    sql="DELETE FROM autotrader." + table + " WHERE "+ column +" LIKE '%" + date1 + "%'"
    # print sql
    # os.system('pause')
    cur = get_connection_cursor(False)
    cur.execute(sql)
    cur.close()
    print 'records from %s were successfully deleted for %s' % (table,date1)
    return 

def modify_db_table(table_name,columns,values,table_key,table_key_val):
    # print columns,values
    cur = get_connection_cursor(False)
    for column,value in zip(columns,values):
        # print column,value
        if len(table_key)==1:
            sql="UPDATE " + table_name + " SET " + column + "=" + value + " WHERE " + table_key[0] + "=" + "'"+table_key_val[0]+"'"
        elif len(table_key)==3:
            sql="UPDATE " + table_name + " SET " + column + "=" + value + " WHERE " + table_key[0] + "=" + "'"+table_key_val[0]+"'" \
                +" AND " + table_key[1] + "=" + "'"+table_key_val[1]+"'"+" AND "+ table_key[2] + "=" + "'"+table_key_val[2]+"'"
        else:
            print "modify_db_table function not configured for given table keys"
            break
        # print sql
        # os.system('pause')
        cur.execute(sql)
    cur.close()
    return