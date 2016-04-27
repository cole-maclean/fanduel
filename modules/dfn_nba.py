# coding=utf-8
import urllib2
import datetime as dt
import ast
from bs4 import BeautifulSoup
import numpy as np
import database_operations as dbo
import data_scrapping_utils as Uds
import re
import requests
import general_utils as Ugen
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
import backtest
import Sport
import features

def day_of_week(date):
	date=dt.datetime.strptime(date,'%Y-%m-%d')
	week   = ['Mon', 'Tue', 'Wed', 'Thu',  'Fri', 'Sat','Sun']
	return week[date.weekday()]

def dfn_lineups(sport,date_list):
	dfn_lineups_dict={}
	lineup_len={'NBA':9,'MLB':8} #Ian: double check NBA
	driver = webdriver.Chrome() #Ian: use this for debugging
	login = Ugen.ConfigSectionMap('dailyfantasynerd')
	#driver = webdriver.PhantomJS()
	driver.get("https://dailyfantasynerd.com/optimizer/fanduel/"+sport.lower())
	selenium_page_load(driver,60,{'type':'ID','element':'input-username'})
	driver.find_element_by_id('input-username').send_keys(login['username'])
	driver.find_element_by_id('input-password').send_keys(login['password'])
	driver.find_element_by_css_selector('.btn.btn-success').click()
	selenium_page_load(driver,60,{'type':'cssSelector','element':'.btn.btn-info.generate'})
	month_list=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
	for date in date_list:
		print date
		date_split=date.split('-')
		dow=day_of_week(date)
		driver.get(("https://dailyfantasynerd.com/optimizer/fanduel/"+sport.lower())+'?d='+dow+'%20' \
						+month_list[int(date_split[1])-1]+'%20'+date_split[2]+'%20'+date_split[0])
		selenium_page_load(driver,120,{'type':'cssSelector','element':'.btn.btn-info.generate'})
		driver.find_element_by_css_selector('.btn.btn-info.generate').click()
		selenium_page_load(driver,600,{'type':'ID','element':'myCarousel'})
		html=driver.page_source 
		soup = BeautifulSoup(html, "lxml")
		lineup=[player.get_text() for indx,player in enumerate(soup.findAll('td',{"class":"pl-col playerName"})) 
				if indx<=(lineup_len[sport]-1)]
		print lineup
		dfn_lineups_dict[date]=lineup
	driver.quit()
	return dfn_lineups_dict


def selenium_page_load(driver,wait_time,element):
	try:
		if element['type']=='ID':
			WebDriverWait(driver,wait_time).until(EC.presence_of_element_located((By.ID, element['element'])))
		elif element['type']=='cssSelector':
			WebDriverWait(driver,wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, element['element'])))
		return
	except:
		# driver.quit()
		pass
	return


def hist_dfn_lineup_scores(dfn_lineups_dict):
	date_list=['2015-12-12', '2015-11-18', '2015-11-30', '2015-12-28', '2015-11-25', 
					'2015-11-27', '2015-11-20', '2015-12-14', '2015-12-09', '2015-12-16', 
					'2015-12-02', '2015-12-07', '2015-12-05', '2015-12-21', '2015-12-23', '2015-12-11', 
					'2015-12-26', '2015-12-18'] #date list for full contests from your backtest
	player_list=[]
	# dfn_lineups_dict=dfn_lineups('NBA',date_list)
	sport=Sport.NBA(historize=True)
	lineup_points_dict={}
	for date,lineup in dfn_lineups_dict.iteritems():
		lineup_points=backtest.hist_lineup_points(sport,lineup,date)
		print '%s lineup points: %s missing_players: %s' % (date,lineup_points[0],lineup_points[1])
		lineup_points_dict[date]={}
		lineup_points_dict[date]={'points':lineup_points[0],'missing_players':lineup_points[1]}
		player_list+=lineup
	lineup_points_list=[date_dict['points'] for date,date_dict in lineup_points_dict.iteritems()]
	lineup_points_list2=[date_dict['points'] for date,date_dict in lineup_points_dict.iteritems() 
						if date_dict['missing_players']==0]
	lineup_points_list2.append(279.5+25)
	print 'mean: %s median: %s max: %s' % (np.mean(lineup_points_list),np.median(lineup_points_list),max(lineup_points_list))
	
	print 'NO MISSING PLAYERS mean: %s median: %s max: %s' % (np.mean(lineup_points_list2),np.median(lineup_points_list2),max(lineup_points_list2))
	print player_list
	return

# hist_dfn_lineup_scores()


####CREATE LIST OF PLAYERS FROM DFN TO MAP!
# sport=Sport.NBA(historize=True)
# dfn_players=[u'Jeremy Lin', u'John Wall', u'Gerald Henderson', u'Allen Crabbe', u'Rudy Gay', u'Kawhi Leonard', u'Derrick Favors', u'David Lee', u'DeMarcus Cousins', u'Isaiah Thomas', u'John Wall', u'Marcus Thornton', u'Bradley Beal', u'Jae Crowder', u'Gordon Hayward', u'Jared Sullinger', u'Blake Griffin', u'Clint Capela', u'Patrick Beverley', u'John Wall', u'Will Barton', u'James Harden', u'Stanley Johnson', u'Nicolas Batum', u'Kristaps Porzingis', u'Anthony Davis', u'Alex Len', u'Garrett Temple', u'Tyreke Evans', u'Rodney Hood', u'James Harden', u'Jared Dudley', u'LeBron James', u'Taj Gibson', u'Jon Leuer', u'Andre Drummond', u'Isaiah Thomas', u'Kyle Lowry', u'Jimmy Butler', u'Eric Bledsoe', u'Kyle Anderson', u'Jae Crowder', u'Jon Leuer', u'Blake Griffin', u'Bismack Biyombo', u'Mike Conley', u'Michael Carter-Williams', u'Will Barton', u'Monta Ellis', u'Tobias Harris', u'Paul George', u'John Henson', u'Paul Millsap', u'Nikola Vucevic', u'Austin Rivers', u'Jameer Nelson', u'Jamal Crawford', u'James Harden', u'Omri Casspi', u'Robert Covington', u'Kristaps Porzingis', u'Blake Griffin', u'DeMarcus Cousins', u'Kyle Lowry', u'John Wall', u'Courtney Lee', u'Will Barton', u'Jeff Green', u'Matt Barnes', u'Chris Bosh', u'Blake Griffin', u'Jahlil Okafor', u'Dennis Schroder', u'Ish Smith', u'Will Barton', u'Jimmy Butler', u'Thabo Sefolosha', u'Paul George', u'Dwight Powell', u'Paul Millsap', u'DeMarcus Cousins', u'Jeremy Lin', u'Stephen Curry', u'Courtney Lee', u'Rodney Hood', u'Gordon Hayward', u'Nicolas Batum', u'Chris Bosh', u'Jon Leuer', u'Andre Drummond', u'Jerryd Bayless', u'Deron Williams', u'O.J. Mayo', u'Will Barton', u'Kawhi Leonard', u'Kevin Durant', u'Dirk Nowitzki', u'Blake Griffin', u'Clint Capela', u'Patty Mills', u'Damian Lillard', u'Avery Bradley', u'Bradley Beal', u'Gordon Hayward', u'Jae Crowder', u'Chris Bosh', u'Draymond Green', u'Marcin Gortat', u'Raymond Felton', u"D'Angelo Russell", u'Lou Williams', u'Wesley Matthews', u'Jae Crowder', u'Nicolas Batum', u'Pau Gasol', u'Blake Griffin', u'Andre Drummond', u'J.J. Barea', u'Chris Paul', u'J.J. Redick', u'Monta Ellis', u'Tobias Harris', u'LeBron James', u'Chris Bosh', u'Jon Leuer', u'Nikola Vucevic', u'Tyreke Evans', u'Ricky Rubio', u'Langston Galloway', u'Eric Bledsoe', u'Omri Casspi', u'Gordon Hayward', u'John Henson', u'Derrick Favors', u'Andre Drummond', u'Jeremy Lin', u'Brandon Knight', u'Courtney Lee', u'James Harden', u'Matt Barnes', u'Kawhi Leonard', u'Kristaps Porzingis', u'Markieff Morris', u'Marc Gasol', u'Isaiah Canaan', u'Isaiah Thomas', u'Gerald Green', u'James Harden', u'Robert Covington', u'Kawhi Leonard', u'David West', u'Blake Griffin', u'Jahlil Okafor', u'Jeremy Lin', u'Damian Lillard', u'Jimmy Butler', u'Rodney Hood', u'Nicolas Batum', u'Jae Crowder', u'Jared Sullinger', u'Marvin Williams', u'Andre Drummond']
# ff=features.FD_features(sport.sport,[])
# db_data={player:sport.get_db_gamedata(player,'2015-11-01','2016-01-01') for player in dfn_players}
# print [player for player,db_df in db_data.iteritems() if db_df.empty]
# start_date='2015-11-01'
# end_date='2016-01-01'
# query={'sport':sport.sport,"player" : {'$regex': ".*Patrick Mills.*"},'date':{"$gte":dt.datetime.strptime(start_date,'%Y-%m-%d'),"$lte":dt.datetime.strptime(end_date,'%Y-%m-%d')}}
# player_data=dbo.read_from_db('hist_player_data',query,{'_id':0})
# print player_data


####YOUR SCORES
# total mean: 271.00617284 total median: 267.1

# ['2015-12-12', '2015-11-18', '2015-11-30', '2015-12-28', '2015-11-25', '2015-11-27', '2015-11-20', '2015-12-14', '2015-12-09', '2015-12-16', '2015-12-02', '2015-12-07', '2015-12-05', '2015-12-21', '2015-12-23', '2015-12-11', '2015-12-26', '2015-12-18']
# LIST3=[336.2, 295.8, 259.1, 300.3, 252.89999999999998, 309.90000000000003, 231.29999999999998, 252.3, 304.4, 306.2, 292.49999999999994, 287.09999999999997, 244.89999999999998, 266.90000000000003, 349.09999999999997, 243.8, 255.3, 306.09999999999997]
# LIST2=[336.2, 295.8, 259.1, 300.3, 252.89999999999998, 309.90000000000003, 231.29999999999998, 252.3, 304.4, 306.2, 292.49999999999994, 287.09999999999997, 244.89999999999998, 266.90000000000003, 349.09999999999997, 243.8, 255.3, 306.09999999999997]
# print np.median(LIST3)
# print np.mean(LIST3)
# large_contest len: 18
# large_contest mean: 283.005555556
# large_contest median: 289.8

#DFN = mean: 280.633333333 median: 284.95 max: 338.3
###YOU WINN!!!!!!! (barely?)


dfn_lineups_dict={'2015-12-12':[u'Raymond Felton', u"D'Angelo Russell", u'Lou Williams', u'Wesley Matthews', u'Jae Crowder', u'Nicolas Batum', u'Pau Gasol', u'Blake Griffin', u'Andre Drummond'],
					'2015-11-18':[u'Dennis Schroder', u'Ish Smith', u'Will Barton', u'Jimmy Butler', u'Thabo Sefolosha', u'Paul George', u'Dwight Powell', u'Paul Millsap', u'DeMarcus Cousins'],
					'2015-11-30':[u'Jerryd Bayless', u'Deron Williams', u'O.J. Mayo', u'Will Barton', u'Kawhi Leonard', u'Kevin Durant', u'Dirk Nowitzki', u'Blake Griffin', u'Clint Capela'],
					'2015-12-28':[u'J.J. Barea', u'Chris Paul', u'J.J. Redick', u'Monta Ellis', u'Tobias Harris', u'LeBron James', u'Chris Bosh', u'Jon Leuer', u'Nikola Vucevic'],
					'2015-11-25':[u'Jeremy Lin', u'Brandon Knight', u'Courtney Lee', u'James Harden', u'Matt Barnes', u'Kawhi Leonard', u'Kristaps Porzingis', u'Markieff Morris', u'Marc Gasol'],
					'2015-11-27':[u'Isaiah Canaan', u'Isaiah Thomas', u'Gerald Green', u'James Harden', u'Robert Covington', u'Kawhi Leonard', u'David West', u'Blake Griffin', u'Jahlil Okafor'],
					'2015-11-20':[u'Jeremy Lin', u'Damian Lillard', u'Jimmy Butler', u'Rodney Hood', u'Nicolas Batum', u'Jae Crowder', u'Jared Sullinger', u'Marvin Williams', u'Andre Drummond'],
					'2015-12-14':[u'Kyle Lowry', u'John Wall', u'Courtney Lee', u'Will Barton', u'Jeff Green', u'Matt Barnes', u'Chris Bosh', u'Blake Griffin', u'Jahlil Okafor'],
					'2015-12-09':[u'Isaiah Thomas', u'John Wall', u'Marcus Thornton', u'Bradley Beal', u'Jae Crowder', u'Gordon Hayward', u'Jared Sullinger', u'Blake Griffin', u'Clint Capela'],
					'2015-12-16':[u'Jeremy Lin', u'Stephen Curry', u'Courtney Lee', u'Rodney Hood', u'Gordon Hayward', u'Nicolas Batum', u'Chris Bosh', u'Jon Leuer', u'Andre Drummond'],
					'2015-12-02':[u'Patrick Beverley', u'John Wall', u'Will Barton', u'James Harden', u'Stanley Johnson', u'Nicolas Batum', u'Kristaps Porzingis', u'Anthony Davis', u'Alex Len'],
					'2015-12-07':[u'Isaiah Thomas', u'Kyle Lowry', u'Jimmy Butler', u'Eric Bledsoe', u'Kyle Anderson', u'Jae Crowder', u'Jon Leuer', u'Blake Griffin', u'Bismack Biyombo'],
					'2015-12-05':[u'Austin Rivers', u'Jameer Nelson', u'Jamal Crawford', u'James Harden', u'Omri Casspi', u'Robert Covington', u'Kristaps Porzingis', u'Blake Griffin', u'DeMarcus Cousins'],
					'2015-12-21':[u'Jeremy Lin', u'John Wall', u'Gerald Henderson', u'Allen Crabbe', u'Rudy Gay', u'Kawhi Leonard', u'Derrick Favors', u'David Lee', u'DeMarcus Cousins'],
					'2015-12-23':[u'Mike Conley', u'Michael Carter-Williams', u'Will Barton', u'Monta Ellis', u'Tobias Harris', u'Paul George', u'John Henson', u'Paul Millsap', u'Nikola Vucevic'],
					'2015-12-11':[u'Patty Mills', u'Damian Lillard', u'Avery Bradley', u'Bradley Beal', u'Gordon Hayward', u'Jae Crowder', u'Chris Bosh', u'Draymond Green', u'Marcin Gortat'],
					'2015-12-26':[u'Garrett Temple', u'Tyreke Evans', u'Rodney Hood', u'James Harden', u'Jared Dudley', u'LeBron James', u'Taj Gibson', u'Jon Leuer', u'Andre Drummond'],
					'2015-12-18':[u'Tyreke Evans', u'Ricky Rubio', u'Langston Galloway', u'Eric Bledsoe', u'Omri Casspi', u'Gordon Hayward', u'John Henson', u'Derrick Favors', u'Andre Drummond']}

# hist_dfn_lineup_scores(dfn_lineups_dict)


