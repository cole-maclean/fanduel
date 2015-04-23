import general_utils as Ugen
import data_scrapping_utils as Uds

#wunderground API
#URL structure: http://api.wunderground.com/api/access_key/feature/q/CA/city
#http://www.wunderground.com/weather/api/d/docs?d=data/index

def get_weather(feature,state_city): #Ian: feature/state_city are both string inputs, state_city 'CA/San Franscisco'
	wunderground = Ugen.ConfigSectionMap('wunderground')
	if len(state_city.split())>1:
		state_city='_'.join(state_city.split())
	URL='http://api.wunderground.com/api/'+wunderground['key']+'/'+feature+'/q/'+state_city+'.json'
	print URL
	response=Uds.get_JSON_data(URL)

	return response

Cell(1,1).value=get_weather('forecast','NY/New_York')
Cell(2,1).value=get_weather('forecast','94107')
os.system('pause')