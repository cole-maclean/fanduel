from . import *
import MySQLdb
import sys
import general_utils as Ugen
import os

class Store:
    def __init__(self, **args):
        DB_parameters = Ugen.ConfigSectionMap('db')
        user = DB_parameters['user']
        password = DB_parameters['password']
        db = DB_parameters['db']
        
        args = {'user': user, 'passwd': password, 'db': db, 'charset': 'utf8'}
        
        self.db = MySQLdb.connect(**args)
        self.cursor = self.db.cursor()
        
    def save(self):
        self.db.commit()
    
    def finish(self):
        self.db.commit()
        self.db.close()
        
    def query(self, query, values = None):
        simplefilter("error", MySQLdb.Warning)
        
        try:
            res = self.cursor.execute(query, values)
            return self.cursor.fetchall()
        except (MySQLdb.Error, MySQLdb.Warning), e:
            if type(e.args) is tuple and len(e.args) > 1:
                msg = e.args[1]
            else:
                msg = str(e)
            logger.error('%s\nQUERY: %s\nVALUES: %s\n\n' % (msg, query, ','.join([str(v) for v in values])))
            os.system('pause')

