from __future__ import division
import math
from datetime import datetime,date,timedelta
import time
import ConfigParser
import getpass
import sys
import csv
import unicodedata

def convert_proj_total(total):
	if len(total)==2:
		if unicodedata.numeric(total[1])==0.5:
			total=float(total[0])+unicodedata.numeric(total[1])
		else:
			total=float(total)
	elif len(total)==3:
		total=float(total[0:2])+unicodedata.numeric(total[2])
	elif len(total)==1:
		total=float(total)
	return total

def proj_run_total(odds_dict):
	total=odds_dict['totals']['total']	
	moneyline=odds_dict['moneyline']/100
	#prt_old=float(spread+total/2+spread_moneyline/100*total/2)
	#prt=float((spread+total/2)/(1-spread_moneyline/200))
	P=float(1/1.83)
	Q=float(math.pow((moneyline/(1-moneyline)),P))
	prt=round(float(total*Q/(1+Q)),2)
	return prt

def odds_to_prob(odd,type): #takes in a "string odd" and returns probability as %
    #http://www.bettingexpert.com/blog/how-to-convert-odds
    if type=='American Moneyline':
        if odd[0]=='+':
           return round(100/(int(odd[1:4])+100)*100,2)
        elif odd[0]=='-':
            return round(int(odd[1:4])/(int(odd[1:4])+100)*100,2)
        else:
        	return 
    return 

def mlb_map(key_index,map_index):
	map_dict={}
	config_parameter=ConfigSectionMap('local text')
	with open(config_parameter['mlbmaps'], 'rb') as f:
	    reader = csv.reader(f)
	    for row in reader:
	        if len(row[key_index])!=0 and len(row[map_index])!=0:
	        	map_dict[row[key_index]]=row[map_index]
	#0:MLB FD Name	
	#1:MLB XML Stats Name	
	#2:MLB Lineups Name	
	#3:RW_MLB	

	#Team Map
	#4:Player Data TeamID	
	#5:Vegas Odds-MLB	
	#6:BaseballPress Lineups	
	#7: FD TeamID	
	#8: Stadium Zipcode	
	#9: Batter Orientation
	#10: SBR Odds
	#11: XMLStats team ids
	return map_dict

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
	print 'in mapping function'
	rw = 2
	while Cell(map_sheet,rw,key_col).value != None or Cell(map_sheet,rw,map_col).value != None: 
		if Cell(map_sheet,rw,key_col).value != None and Cell(map_sheet,rw,map_col).value != None:
			excel_map[Cell(map_sheet,rw,key_col).value] = Cell(map_sheet,rw,map_col).value
			rw += 1
		else:
			rw += 1
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

def previous_day(todays_date): #YYYY-MM-DD
	t=time.strptime(todays_date.replace("-",''),'%Y%m%d')
	previous_day=date(t.tm_year,t.tm_mon,t.tm_mday)-timedelta(1)
	return str(previous_day)
