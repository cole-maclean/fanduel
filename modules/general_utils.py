import math
from datetime import datetime
import time
import ConfigParser
import getpass
import sys

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).
    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

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
def excel_mapping(map_sheet,key_col,map_col):#Cole: built general mapping utility to use excel as mapping matrix. Data must start at row 2
	excel_map = {}
	rw = 2
	while Cell(map_sheet,rw,key_col).value != None:
		excel_map[Cell(map_sheet,rw,key_col).value] = Cell(map_sheet,rw,map_col).value
		rw = rw + 1
	return excel_map
def ConfigSectionMap(section):
	Config = ConfigParser.ConfigParser()
	if getpass.getuser() == 'Cole':
		config_path = 'C:/Users/Cole/Desktop/FanDuel/db.ini'
	else:
		config_path = 'C:/Users/Ian Whitestone/Documents/Python Projects/fanduel-master/db.ini'
	Config.read(config_path)
	dict1 = {}
	options = Config.options(section)
	for option in options:
	    try:
	        dict1[option] = Config.get(section, option)
	        if dict1[option] == -1:
	            DebugPrint("skip: %s" % option)
	    except:
	        print("exception on %s!" % option)
	        dict1[option] = None
	return dict1