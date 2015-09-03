import MySQLdb
import collections
import general_utils as Ugen
import time
import os
import pandas as pd

def get_db_connection(): #Cole: Updated to allow for db reads to return a Dict cursor
    DB_parameters = Ugen.ConfigSectionMap('db')
    conn = MySQLdb.Connection(db=DB_parameters['db'],host="localhost",user=DB_parameters['user'],passwd=DB_parameters['password']);
    return conn

def read_from_db(sql):#Cole: updated to allow list of columns that make up key
    conn = get_db_connection()
    df = pd.read_sql(sql,conn)
    return df

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
    cur = get_db_connection().cursor()
    try:
        if placeholders:
            cur.execute(sql,data)
        else:
            cur.execute(sql)
        cur.execute('COMMIT')
    except MySQLdb.Error, e:
        print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
        os.system('pause')
    time.sleep(.1)

def load_csv_into_db(csv_file,table):
    sql = "LOAD DATA INFILE '" + csv_file + "' IGNORE INTO TABLE " + table + " FIELDS TERMINATED BY ';' IGNORE 1 LINES"
    cur = get_db_connection().cursor()
    cur.execute(sql)
    cur.execute('COMMIT')
    time.sleep(.1)

def get_table_last_row(table_name,table_key):
    sql="SELECT * FROM " + table_name +" ORDER BY " + table_key + " DESC LIMIT 1"
    cur = get_db_connection().cursor()
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
    cur = get_db_connection().cursor()
    cur.execute(sql)
    cur.close()
    print 'records from %s were successfully deleted for %s' % (table,date1)
    return 

def modify_db_table(table_name,columns,values,table_key,table_key_val):
    # print columns,values
    cur = get_db_connection().cursor()
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