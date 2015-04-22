import general_utils as Ugen
import data_scrapping_utils as Uds

#8c86f475a79900d8 #wunderground API
#URL structure: http://api.wunderground.com/api/access_key/feature/q/CA/city

def get_weather(feature,city):
	wunderground = Ugen.ConfigSectionMap('wunderground')
	URL='http://api.wunderground.com/api/'+wunderground[key]+'/'+feature+'/q/CA/'+city
	response=Uds.get_JSON_data(URL)