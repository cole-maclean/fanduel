import math
from datetime import datetime
import time
def getSec(s):
    try:
        if len(s) == 2:
            s = s + ':00'
        l = s.split(':')
        return int(l[0]) * 60 + int(l[1])
    except ValueError:
        return 0
def bin_mapping(x,bin_size):
	return math.trunc(x) - math.trunc(x)%bin_size
def get_time_remain(future_time):
	contest_time = datetime.strptime(future_time,'%H:%M')
	current_time = datetime.strptime(str(datetime.now().hour) + ':' + str(datetime.now().minute),'%H:%M')
	tdelta = contest_time - current_time
	time_remaining = tdelta.total_seconds()/60
	return time_remaining
def output_dict(data_dict):
	new_sheet()
	rw = 0
	for key, items in data_dict.iteritems():
		rw = rw + 1
		col = 1
		for data_item in items:
			Cell(rw,col).value = data_item
			col = col + 1
	return data_dict
