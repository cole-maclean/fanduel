import general_utils as Ugen
import data_scrapping_utils as Uds
import ast
import time
from datetime import date, timedelta
import numpy as np

#wunderground API
#URL structure: http://api.wunderground.com/api/access_key/feature/q/CA/city
#http://www.wunderground.com/weather/api/d/docs?d=data/index

def weather_response(feature,zipcode): 
	wunderground = Ugen.ConfigSectionMap('wunderground')
	URL='http://api.wunderground.com/api/'+wunderground['key']+'/'+feature+'/q/'+zipcode+'.json'
	response=Uds.get_JSON_data(URL)
	return response

def weather_hourly(teamID,gametime): #gametime is formatted as 7:30 AM or 7:00 pm,
	team_map=Ugen.mlb_map(4,8)
	batter_map=Ugen.mlb_map(4,9)
	batter_dir=batter_map[teamID]
	zipcode=str(team_map[teamID])
	try:
		gametime_hour=convert_time_24(int(gametime.split()[0].split(":")[0]),int(gametime.split()[0].split(":")[1]),gametime.split()[1])
	except:
		print 'gametime %s is not in proper format' % gametime
		return None
	data=weather_response('hourly',zipcode)
	weather_dict={}
	tzone=data['hourly_forecast'][1]['FCTTIME']['pretty'].split()[2]
	gametime_hour=convert_timezones(gametime_hour,'ET',tzone)
	temp_list,hum_list,wspd_list,wdir_list,pop_list=([] for i in range(5)) 
	i=1 #counter to make sure you don't take forecast from the next day
	for e in data['hourly_forecast']: #each e is one hours time
		forecast_hour=e['FCTTIME']['hour_padded']
		if forecast_hour[0]=='0' and forecast_hour[1]=='0':
			forecast_hour=forecast_hour.replace("0","",1)
		elif forecast_hour[0]=='0':
			forecast_hour=forecast_hour.replace("0","")
		if i<4 and (forecast_hour==str(gametime_hour) or forecast_hour==str(int(gametime_hour)+1) or forecast_hour==str(int(gametime_hour)+2)):
			try:
				temp_list.append(float(e['temp']['english'])) #temp in degF
			except:
				pass		
			try:
				hum_list.append(float(e['humidity']))
			except:
				pass
			try:
				pop_list.append(float(e['pop']))
			except:
				pass
			wdir=e['wdir']['degrees']
			try:	
				if int(wdir)<180: #wdir is the direction the wind is blowing from
					wdir_list.append(abs(float((int(wdir)+180)-batter_dir))) #right now do abs value
				else:
					wdir_list.append(abs(float((int(wdir)-180)-batter_dir)))
			except:
				pass
			try:
				wspd_list.append(float(e['wspd']['english'])) #mph or wspdm for metric
			except:
				pass
			i=i+1
		weather_dict['temp']=round(np.mean(temp_list),2)
		weather_dict['humidity']=round(np.mean(hum_list),2)
		weather_dict['wind']={}
		weather_dict['wind']['wind_dir']=round(np.mean(wdir_list),2)
		weather_dict['wind']['wind_speed']=round(np.mean(wspd_list),2)
		weather_dict['pop']=round(np.mean(pop_list),2)
	return weather_dict

def weather_hist(teamID,weather_date,gametime):
	weather_dict={}
	team_map=Ugen.mlb_map(4,8)
	batter_map=Ugen.mlb_map(4,9)
	zipcode=str(team_map[teamID])
	batter_dir=float(batter_map[teamID])
	try:
		gametime_hour=convert_time_24(int(gametime.split()[0].split(":")[0]),int(gametime.split()[0].split(":")[1]),gametime.split()[1])
	except:
		print 'gametime %s is not in proper format' % gametime
		return None
	data=weather_response('history'+'_'+weather_date.replace('-',''),zipcode)
	tzone=data['history']['observations'][1]['date']['pretty'].split()[2]
	gametime_hour=convert_timezones(gametime_hour,"ET",tzone)
	temp_list,hum_list,wspd_list,wdir_list=([] for i in range(4)) 
	for e in data['history']['observations']:
		forecast_hour=e['date']['hour']
		if forecast_hour[0]=='0' and forecast_hour[1]=='0':
			forecast_hour=forecast_hour.replace("0","",1)
		elif forecast_hour[0]=='0':
			forecast_hour=forecast_hour.replace("0","")
		if forecast_hour==str(gametime_hour) or forecast_hour==str(int(gametime_hour)+1) or forecast_hour==str(int(gametime_hour)+2):
			try:
				temp_list.append(float(e['tempi'])) #temp in degF
			except:
				pass		
			try:
				hum_list.append(float(e['hum']))
			except:
				pass
			wdir=e['wdird']
			try:	
				if int(wdir)<180:
					wdir_list.append(abs(float((int(wdir)+180)-batter_dir))) #right now do abs value
				else:
					wdir_list.append(abs(float((int(wdir)-180)-batter_dir)))
			except:
				pass
			try:
				wspd_list.append(float(e['wspdi'])) #mph or wspdm for metric
			except:
				pass
	weather_dict['temp']=round(np.mean(temp_list),2)
	weather_dict['humidity']=round(np.mean(hum_list),2)
	weather_dict['wind']={}
	weather_dict['wind']['wind_dir']=round(np.mean(wdir_list),2)
	weather_dict['wind']['wind_speed']=round(np.mean(wspd_list),2)
	return weather_dict

def convert_time_24(hour,minute,ampm): #converts time to 24 hour
	if hour==12 and ampm=='AM':
		if minute>30:
			hour=1
		else:
			hour=0
	elif ampm=='AM' or hour==12: #account for 12 pm as well
		if minute>30:
			hour+=1 #Round to next hour
	elif ampm=='PM':
		if minute>30:
			hour+=1+12 #Round to next hour, convert to 24 hour time
		else:
			hour+=12
	if hour==24:
		hour=0
	return hour

def convert_timezones(hour,cur_tzone,new_tzone): #inputs are 24 hour time, 
	if cur_tzone=='ET':
		if new_tzone=='CDT' or new_tzone=='CST':
			hour=str(int(hour)-1)
		elif new_tzone=='MDT' or new_tzone=='MST':
			hour=str(int(hour)-2)
		elif new_tzone=='PDT' or new_tzone=='PST':
			hour=str(int(hour)-3)
	else:
		return None
	return hour

#Add air density factor
#For hourly forecast will need to get pressure from the day before

# start_time='10:05 PM ET'
# weather_dict=weather_hist('LAA','2015-04-20',start_time)
# print weather_dict
# # # weather_dict=weather_hourly('PHI',start_time) 
# # print weather_dict
# os.system('pause')


#Ian Troubleshoot:
#2015-04-03 no weather data for new york mets at texas rangers