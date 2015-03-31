import collections
import general_utils as Ugen
import time
import fanduelweb
from google.appengine.api import rdbms
import MySQLdb
import threading
import logging

_INSTANCE_NAME = 'bamboo-velocity-87603:fanduel'

def _db_connect():
  return rdbms.connect(instance=_INSTANCE_NAME, database='fanduel',user='root',passwd='Timeflies1')
_mydata = threading.local()
def with_db_cursor(do_commit = False):
  """ Decorator for managing DB connection by wrapping around web calls.

  Stores connections and open cursor count in a threadlocal
  between calls.  Sets a cursor variable in the wrapped function. Optionally
  does a commit.  Closes the cursor when wrapped method returns, and closes
  the DB connection if there are no outstanding cursors.

  If the wrapped method has a keyword argument 'existing_cursor', whose value
  is non-False, this wrapper is bypassed, as it is assumed another cursor is
  already in force because of an alternate call stack.
  """
  def method_wrap(method):
    def wrap(self, *args, **kwargs):
      if kwargs.get('existing_cursor', False):
        # Bypass everything if method called with existing open cursor.
        return method(self, None, *args, **kwargs)

      if not hasattr(_mydata, 'conn') or not _mydata.conn:
        _mydata.conn = _db_connect()
        _mydata.ref = 0
        _mydata.commit = False

      conn = _mydata.conn
      _mydata.ref = _mydata.ref + 1

      try:
        cursor = conn.cursor()
        try:
          result = method(self, cursor, *args, **kwargs)
          if do_commit or _mydata.commit:
            _mydata.commit = False
            conn.commit()
          return result
        finally:
          cursor.close()
      finally:
        _mydata.ref = _mydata.ref - 1
        if _mydata.ref == 0:
          _mydata.conn = None
          logging.info('Closing conn')
          conn.close()
    return wrap
  return method_wrap
def get_data_dict_structure(sport,position):
    data_dict_structures = {'NHL':{'player':['GameID','Assists','Goals','num','PiM','PlusMinus','SoG','ToI','Team'],'goalie':['GameID','GoalsAgainst','num','ShotsAgainst','Saves','SavePercent''ToI','weighted_toi=int(Ugen.getSec(player_dict[rw_data[0]]["ToI"][-1]))*float(player_dict[rw_data[0]]["SavePercent"][-1])','Team']}} #might need to move this to config file
    return data_dict_structures[sport][position]
@with_db_cursor(do_commit = False)
def get_player_data_dict(sport,cur, GameIDLimit):#TODO: Limits for history games and season
    sql = "SELECT Player, GameID, Stat1, Stat2, Stat3, Stat4, Stat5, Stat6, Stat7, Team, Sport FROM hist_player_data WHERE Sport= %s AND GameID > " + GameIDLimit
    print sql
    cur.execute(sql,(sport))
    resultset = cur.fetchall()
    player_dict = collections.OrderedDict()
    for rw in resultset:
        if rw[9] != None: #Check if player is goalie, hack job need to clean
            player_dict = build_data_dict_structure(player_dict,get_data_dict_structure(sport,'player'),rw,1)
        else:
            player_dict = build_data_dict_structure(player_dict,get_data_dict_structure(sport,'goalie'),rw,1)
    print player_dict
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
@with_db_cursor(do_commit = False)
def read_from_db(sql,cur,primary_key_col = 0):
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
@with_db_cursor(do_commit = True)
def insert_mysql(table,cursor, columns, placeholders, data):
    sql = "INSERT INTO " + table + " (%s) VALUES (%s)" % (columns, placeholders)
    cursor.execute(sql, data)
    time.sleep(.1)
@with_db_cursor(do_commit = True)
def load_csv_into_db(csv_file,cursor,table):
    sql = "LOAD DATA INFILE '" + csv_file + "' IGNORE INTO TABLE " + table + " FIELDS TERMINATED BY ',' IGNORE 1 LINES"
    cursor.execute(sql)
    time.sleep(.1)