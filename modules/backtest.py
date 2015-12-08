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
        print 'initializing NBA class'
        sport=Sport.NBA()
        print 'nba class initialized'
    else:
        print 'sport: %s not configured'
        return
    for date in date_list:
        if date==dt.date.today().strftime('%Y-%m-%d'): #Ian: need to change this so it checks if date is in db...
            break
        contest_list=get_contests(sport.sport,date)
        # print contest_list
        # raw_input('test')
        hist_lineups_dict[date]={}
        for contest in contest_list:    
            try:
                output=sport.optimal_roster(0,0,-100,date,contest)
                player_list=[player for player in output['roster'].keys()]
                roster_points,count=hist_lineup_points(sport,player_list,date)
                print {'points':roster_points,'missing_players':count,'date':date,'contest':contest}
                hist_lineups_dict[date][contest]={}
                hist_lineups_dict[date][contest]['points']=roster_points
                hist_lineups_dict[date][contest]['missing_players']=count
                hist_lineups_dict[date][contest]['player_universe_size']=output['player_pool_size']
                hist_lineups_dict[date][contest]['roster_dict']=output['roster']
            except:
                print 'ERROR OCCURED!!!@ contest: %s date: %s sport: %s' % (contest,date,sport.sport)
    return hist_lineups_dict

def hist_lineup_points(sport,lineup,date):
    ff=features.FD_features(sport.sport,[])
    lineup_points=0
    db_data=[sport.get_db_gamedata(player,date,date) for player in lineup]
    count=sum([1 if db_df.empty else 0 for db_df in db_data])
    lineup_points=sum([ff.FD_points(db_df)[0] for db_df in db_data if not db_df.empty])
    return lineup_points,count

def average_lineup_points(hist_lineups_dict):
    full_lineup_points=[contest_dict['points'] for date in hist_lineups_dict.keys() for contest,contest_dict in hist_lineups_dict[date].iteritems() 
                        if contest_dict['points']>0 and contest_dict['missing_players']==0]
    return np.mean(full_lineup_points),np.amax(full_lineup_points),np.std(full_lineup_points)


def run_backtest(length):
    if length=='full':
        hist_lineups_dict=hist_model_lineups('NBA', '2015-11-18','2015-11-30')
    else:
        hist_lineups_dict=hist_model_lineups('NBA', '2015-12-02','2015-12-02')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(hist_lineups_dict)
    mean_points,max_points,stdev=average_lineup_points(hist_lineups_dict)
    print 'average lineup points: %s maximum lineup points: %s standard deviation: %s' % (mean_points,max_points,stdev)
    return

# minutes_feature_list=[261.5,258.2,258.2,281.2,249.4,244.9,254.8,292.9,280.1,278.7,280.4,243.2,226.7,270.8,272.2,271.7,248.7,277,267.5,249.2,256.4
#                         ,244.7,285.5,263.5,305.2,306.3]



######TO DO:
##---------------------------------------
##0: feature engineering
##1: refactor backtest into class
##2: refactor test_ian into class
##3: add a write to CSV function to track backtests or start using juptyer
##4: player maps!
##5: fix sport class so you dont have to uncomment the ff.FD_feature class call. perhaps take features in as argument?? 
##6: re-assign FD positions if they are a F or G - optimizer won't accept those
##7: add db check if event has already been historized


##BENCHMARK TO BEAT FOR SCORING
#https://www.fanduel.com/insider/2015/11/10/fanduel-nba-benchmarks-points-to-target-in-each-contest-type/

