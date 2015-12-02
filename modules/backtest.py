import os
import time
import datetime as dt
import ast
import database_operations as dbo
import data_scrapping as ds
import data_scrapping_utils as Uds
import re
import requests
import FD_operations as fdo
import general_utils as Ugen
import sys
import TeamOdds
import json
import string
import pandas
import Sport
import numpy as np
import pprint
import features
import random

def hist_FD_contest_salaries():
    todays_date=dt.datetime.strptime(time.strftime("%Y-%m-%d"),"%Y-%m-%d")
    pp = pprint.PrettyPrinter(indent=4)
    FDSession = fdo.FDSession()
    sport_list=['NBA','NHL','NFL','MLB']
    for sport in sport_list:
        daily_contests = FDSession.get_daily_contests(sport)
        for contest_ID,contest_url in daily_contests.iteritems():
            player_dict={player['first_name']+' '+player['last_name']:{'fppg':player['fppg'],'salary':player['salary'],'position':player['position'],
                         'games_played':player['played'],'injury_status':player['injury_status']}
                         for player in FDSession.fanduel_api_data(contest_url)['players']}
            print 'now historizing %s contest: %s' % (sport,contest_ID)
            dbo.write_to_db('hist_fanduel_data',{'sport':sport,'date':todays_date,'contest_ID':contest_ID,'contest_dict':player_dict},False)
            print 'contest: %s historized successfully' % sport
    return

def get_contests(sport,date): 
    query={'sport':sport,'date':dt.datetime.strptime(date,'%Y-%m-%d')}
    resultset=dbo.read_from_db('hist_fanduel_data',query)
    return [contest['contest_ID'] for contest in resultset]

def hist_model_lineups(sport,start_date,end_date): #date format in 'YYYY-MM-DD'
    date_list = [d.strftime('%Y-%m-%d') for d in pandas.date_range(start_date,end_date)]
    hist_lineups_dict={}
    if sport=='MLB':
        sport=Sport.MLB()
    elif sport=='NBA':
        sport=Sport.NBA()
    else:
        print 'sport: %s not configured'
        return
    for date in date_list:
        if date==dt.date.today().strftime('%Y-%m-%d'):
            break
        contest_list=get_contests(sport.sport,date)
        hist_lineups_dict[date]={}
        for contest in contest_list:    
            output=sport.optimal_roster(0,0,-100,date,contest)
            player_list=[player for player in output['roster'].keys()]
            roster_points,count=hist_lineup_points(sport,player_list,date)
            hist_lineups_dict[date][contest]={}
            hist_lineups_dict[date][contest]['points']=roster_points
            hist_lineups_dict[date][contest]['missing_players']=count
            hist_lineups_dict[date][contest]['player_universe_size']=output['player_pool_size']
            hist_lineups_dict[date][contest]['roster_dict']=output['roster']
    return hist_lineups_dict

def hist_lineup_points(sport,lineup,date):
    lineup_points=0
    count=0
    for player in lineup:
        db_df = sport.get_db_gamedata(player,date,date)
        if db_df.empty:
            count+=1
            continue
        player_points=features.FD_points(db_df,sport.sport)
        lineup_points+=player_points
    return lineup_points.iloc[-1],count

# hist_FD_contest_salaries()

hist_lineups_dict=hist_model_lineups('NBA', '2015-11-27','2015-11-27')

# hist_lineups_dict=hist_model_lineups('NBA', '2015-11-18','2015-12-30')
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(hist_lineups_dict)

######TO DO:
##3: add a write to CSV function to track backtests or start using juptyer

##BENCHMARK TO BEAT FOR SCORING
#https://www.fanduel.com/insider/2015/11/10/fanduel-nba-benchmarks-points-to-target-in-each-contest-type/


full_lineup_points=[contest_dict['points'] for date in hist_lineups_dict.keys() for contest,contest_dict in hist_lineups_dict[date].iteritems() 
                    if contest_dict['points']>0 and contest_dict['missing_players']==0]

partial_lineup_points=[contest_dict['points'] for date in hist_lineups_dict.keys() for contest,contest_dict in hist_lineups_dict[date].iteritems() 
                    if contest_dict['points']>0 and contest_dict['missing_players']>0]

print np.mean(full_lineup_points)
print np.mean(partial_lineup_points)