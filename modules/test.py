# -*- coding: utf-8 -*-
# Welcome to the DataNitro Editor
# Use Cell(row,column).value, or Cell(name).value, to read or write to cells
# Cell(1,1) and Cell("A1") refer to the top-left cell in the spreadsheet
# 
# Note: To run this file, save it and run it from Excel (click "Run from File")
# If you have trouble saving, try using a different directory

import urllib
import urllib2
import ast
import os
import pywapi
import json
import geopy
import geopy.distance
from BeautifulSoup import BeautifulSoup
from gameday import Fetcher, store
import MySQLdb
import numpy
import re

#TODO: Make dict data into nampedtuples
#TODO: player_universe in general call (currently repeatidly generating)
def parse_html(sUrl,sStart,sEnd):
    response = urllib2.urlopen(sUrl)
    shtml = response.read()
    shtml = shtml.replace('false',"False")
    intStart = shtml.find(sStart)
    intEnd = shtml.find(sEnd,intStart)
    parsed_html = shtml[intStart:intEnd].replace(sStart,"")
    return parsed_html

def get_matchups():
	matchups ={}
	matchup_text = parse_html(Cell("cLineUpURL").value,"FD.playerpicker.teamIdToFixtureCompactString = ",";")
	formatted_text = multiple_replace(matchup_text,{'<b>':'','</b>':'','[':'',"'":'','{':'','"':'',':':'',',':'','@':'','}':''})
	start_char = 0
	while start_char < len(formatted_text):
		team_id = formatted_text[start_char:start_char + 3]
		team_name = formatted_text[start_char + 3:start_char + 6]
		rival_name = formatted_text[start_char + 6:start_char + 9]
		rival_id = formatted_text[start_char + 9:start_char + 12]
		matchups[team_id] = [team_name,rival_name,rival_id]
		matchups[rival_id] = [rival_name,team_name,team_id]
		#print str(team_id) +',' + team_name + ',' + rival_name + ',' + str(rival_id)
		start_char = start_char + 18
	#print matchups
	#Cell("B17").value = formatted_text
	return matchups
def get_FD_playerlist(matchups):
 	FD_list = ast.literal_eval(parse_html(Cell("cLineUpURL").value,"FD.playerpicker.allPlayersFullData = ",";"))
 	for player_data in FD_list:
 		rival_team = matchups[FD_list[player_data][3]][1]
 		FD_list[player_data].append(rival_team)
 	return FD_list
def get_weather():
	weather_com_result = pywapi.get_weather_from_weather_com('10001')
	return weather_com_result
def makeRequest(request_url):
    request = urllib2.Request(request_url)
    request.add_header("token","YXaUMlzRewULRDmvEiezOAgWCUreuSkA")
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        if e.code == 400:
        	response = ""
        	print e.reason
        else:
        	print e
    data = json.load(response)
    return data

def get_historical_weather():
	url = "http://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&locationid=ZIP:85004&startdate=2014-05-10&enddate=2014-05-16"
	response_data = makeRequest(url)
	return response_data

def build_team_location_dict():
	mlbteam_location_dict = ast.literal_eval(Cell("I1").value)
	for team_data in mlbteam_location_dict:
		team_lat_cord = team_data["lat"]
		team_lng_cord = team_data["lng"]
		station_ids = ['','','']
		tmpdist1 = 1000000
		tmpdist2 = 1000000
		tmpdist3 = 1000000
		for i in range(2,49472,1):
			station_lat_cord = Cell(i,2).value
			station_lng_cord = Cell(i,3).value
			pt1 = geopy.Point(team_lat_cord, team_lng_cord)
			pt2 = geopy.Point(station_lat_cord, station_lng_cord)
			dist = geopy.distance.distance(pt1, pt2).km
			if dist < tmpdist1:
					station_elevation = Cell(i,4).value
					station_ids[0] = str(Cell(i,1).value)
					tmpdist1 = dist
			elif dist < tmpdist2:
					station_ids[1] = str(Cell(i,1).value)
					tmpdist2=dist
			elif dist < tmpdist3:
					station_ids[2] = str(Cell(i,1).value)
					tmpdist3 = dist
		team_data["stationid"] = station_ids
		team_data["elevation"] = station_elevation
		print team_data["team"]
	return mlbteam_location_dict

def get_station_id_strlist():
	mlbteam_location_dict = ast.literal_eval(Cell("cTeamLocationDict").value)
	stationid_list = ""
	for team_data in mlbteam_location_dict:
		for station_id in team_data['stationid']:
			stationid_list = stationid_list + "'" + station_id + "',"
	return stationid_list
def build_mlb_lineup_list():
	lineup = []
	url = "http://www.rotowire.com/baseball/daily_lineups.htm"
	soup = BeautifulSoup(Fetcher.fetch(url))
	vis_playerdivs = soup.findAll("div", { "class" : "dlineups-vplayer" })
	home_playerdivs  = soup.findAll("div", { "class" : "dlineups-hplayer" })
	for div in vis_playerdivs:
		lineup.append(str(div.a['title']))
	for div in home_playerdivs:
		lineup.append(str(div.a['title']))
	return lineup
def build_player_universe(FD_playerlist, mlb_playerlist):
	delkeys = []
	for key,data in FD_playerlist.iteritems():
		player =  data[1]
		if not any(player in s for s in mlb_playerlist):
			#print key
			delkeys.append(key)
	for key in delkeys:
		FD_playerlist.pop(key)
	return FD_playerlist
def get_player_data_dict():
	player_dict = {}
	DB = store.Store()
	strSQL = "SELECT CONCAT(first_name,' ',last_name) AS player_name, team, id, pos, type, bats FROM player GROUP BY id"
	resultset = DB.query(strSQL)
	for rw in resultset:
		player_dict[rw[0]] = rw #TODO: Check for duplicates
	return player_dict
def get_histbatter_points_dict():
	DB = store.Store()
	strSQL = "SELECT * FROM batpointspg"
	return DB.dict_query(strSQL)
def build_batter_points_dict():
	batter_dict = {}
	hist_data = get_histbatter_points_dict()
	for rw in hist_data:
		batter = int(rw['batter'])
		pitcher = int(rw['pitcher'])
		data_point = [rw['game_date'],float(rw['BatPointsPG'])]
		if batter in batter_dict:
			if pitcher in batter_dict[batter]:
				batter_dict[batter][pitcher].append(data_point)
			else:
				batter_dict[batter][pitcher] = [data_point]
		else:
			batter_dict[batter] = {pitcher:[data_point]}
	return batter_dict
def build_batter_pointforecast_dict():
	forecastpoints_dict = {}
	matchups = get_matchups()
	player_universe = build_player_universe(get_FD_playerlist(matchups),build_mlb_lineup_list())
	pitcher_dict = build_pitcher_team_dict(get_FD_playerlist(matchups)) #TODO: make this playeruniverse
	player_data_dict = get_player_data_dict()
	batter_points_dict = build_batter_points_dict()
	for player_id in player_universe:
		try:
			batter_name = player_universe[player_id][1]
			rival_team_id = matchups[player_universe[player_id][3]][2]
			pitcher_id = pitcher_dict[rival_team_id]
			pitcher_name = player_universe[pitcher_id][1]
			histstats_batterid = int(player_data_dict[batter_name][2])
			histstat_pitcherid = int(player_data_dict[pitcher_name][2])
			print histstats_batterid
			try:
				player_histstats = batter_points_dict[histstats_batterid][histstat_pitcherid]
				print "histpitcherid is" + str(histstat_pitcherid)
				player_universe[player_id].append(player_histstats)
				print pitcher_name
				print pitcher_id + "in universe"
				print player_id
			except KeyError:
				pass
		except KeyError:
			print pitcher_id + "not in universe"
			#print player_name
			#print pitcher_name
	return player_universe
def build_pitcher_team_dict(lineup):
	pitcher_team = {}
	for player_data in lineup:
		if lineup[player_data][0] == "P":
			pitcher_team[lineup[player_data][3]] = player_data
	print pitcher_team
	return pitcher_team
def multiple_replace(string, rep_dict):
    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)

#def build_batter_point_distributions():


#print build_player_data_dict()
#print build_batter_points_dict()
#print build_histbatter_points_dict()
#Cell("B10").value = build_mlb_lineup_list()
#Cell("B11").value = get_FD_playerlist()
#Cell("B12").value = build_player_universe(get_FD_playerlist(),build_mlb_lineup_list())
#Cell("B13").value = get_player_data_dict()
#Cell("B15").value = build_pitcher_team_dict()
#Cell("B16").value = get_matchups()
Cell("B18").value = build_batter_pointforecast_dict()
os.system("pause")
