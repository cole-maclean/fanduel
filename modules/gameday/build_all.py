import MySQLdb

from datetime import timedelta
from datetime import date
from time import *
import string, os, sys, subprocess

start_date = date(2011,3,13)
end_date = date(2014,5,30)
type = 'mlb'


day_count = (end_date - start_date).days + 1
for single_date in [d for d in (start_date + timedelta(n) for n in range(day_count)) if d <= end_date]:
	    print 'Now building: ' + strftime("%Y-%m-%d", single_date.timetuple())
	    fmtdate = strftime("%m/%d/%Y", single_date.timetuple())

	    #filez = open('temp.log','w')

	    commander = 'python "C:/Users/Cole/Desktop/FanduelV2/fanduel/modules/gameday/gameday_mssql.py" --year=%s --month=%s --day=%s --type=%s  ' % \
				( strftime("%Y", single_date.timetuple()), strftime("%m", single_date.timetuple()) , strftime("%d", single_date.timetuple()), type  )
	    process = subprocess.Popen(commander, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
	    output = process.communicate()


	    print commander
	    #print subprocess.STDOUT
	    #os.system(commander)

	    #file = open('temp.log','rw')

	    #output = o
	    stroutput = str(output[0])
	    print  stroutput
os.system("pause")