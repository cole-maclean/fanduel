# coding=utf-8
import time,ast
import datetime as dt
import main
import database_operations as dbo
import data_scrapping as ds
import data_scrapping_utils as Uds
import FD_operations as fdo
import general_utils as Ugen
import pandas
import Sport
import numpy as np
import pprint
import features
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D

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

def hist_model_lineups(sport,start_date,end_date): #date format in 'YYYY-MM-DD' #Ian: Refactor whole module into class
    date_list = [d.strftime('%Y-%m-%d') for d in pandas.date_range(start_date,end_date)]
    hist_lineups_dict={}
    if sport=='MLB':
        sport=Sport.MLB()
    elif sport=='NBA':
        sport=Sport.NBA()
    for date in date_list:
        if date==dt.date.today().strftime('%Y-%m-%d'): #Ian: need to change this so it checks if date is in db...
            break
        contest_list=get_contests(sport.sport,date)
        hist_lineups_dict[date]={}
        for contest in contest_list: 
            print 'contest: %s date: %s sport: %s' % (contest,date,sport.sport)
            start = time.time()
            output=sport.optimal_roster(0,0,-100,date,contest)
            end = time.time()
            print 'time elapsed: %s' % (end - start)
            player_list=[player for player in output['roster'].keys()]
            roster_points,count=hist_lineup_points(sport,player_list,date)
            print {'points':roster_points,'missing_players':count,'date':date,'contest':contest}
            hist_lineups_dict[date][contest]={}
            hist_lineups_dict[date][contest]['points']=roster_points
            hist_lineups_dict[date][contest]['missing_players']=count
            hist_lineups_dict[date][contest]['player_universe_size']=output['player_pool_size']
            hist_lineups_dict[date][contest]['roster_dict']=output['roster']
    return hist_lineups_dict

def hist_lineup_points(sport,lineup,date):
    ff=features.FD_features(sport.sport,[])
    dfn_player_map={'Ish Smith':'Ishmael Smith','J.J. Barea':'Jose Barea','Patty Mills':'Patrick Mills',
                    'Dennis Schroder':'Dennis Schröder','Nikola Vucevic':'Nikola Vučević',
                    'Kristaps Porzingis':'Kristaps Porziņģis'}
    lineup_points=0
    lineup=[dfn_player_map[player] if player in dfn_player_map.keys() else player for player in lineup]
    db_data=[sport.get_db_gamedata(player,date,date) for player in lineup]
    count=sum([1 if db_df.empty else 0 for db_df in db_data])
    lineup_points=sum([ff.FD_points(db_df)[0] for db_df in db_data if not db_df.empty])
    return lineup_points,count

def average_lineup_points(hist_lineups_dict):
    full_lineup_points=[contest_dict['points'] for date in hist_lineups_dict.keys() for contest,contest_dict in hist_lineups_dict[date].iteritems() 
                        if contest_dict['points']>0 and contest_dict['missing_players']==0]
    print full_lineup_points
    return np.mean(full_lineup_points),np.amax(full_lineup_points),np.std(full_lineup_points),np.median(full_lineup_points)


def run_backtest(length,sport):
    if length=='full':
        # hist_lineups_dict=hist_model_lineups(sport, '2015-11-18','2015-12-10')
        # hist_lineups_dict=hist_model_lineups(sport, '2015-12-11','2015-12-28')
        hist_lineups_dict=hist_model_lineups(sport, '2015-11-18','2015-12-28')
    else:
        hist_lineups_dict=hist_model_lineups(sport, '2015-12-12','2015-12-12')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(hist_lineups_dict)
    if hist_lineups_dict:
        mean_points,max_points,stdev,medn_points=average_lineup_points(hist_lineups_dict)
        print 'average lineup points: %s \nmaximum lineup points: %s' % (mean_points,max_points)
        print 'standard deviation: %s \nmedian lineup points: %s' % (stdev,medn_points)
    return

def hist_model_score(sport,date):
    if sport=='MLB':
        sport=Sport.MLB()
    elif sport=='NBA':
        sport=Sport.NBA()
    sport.backtest_date=date
    contest_list=get_contests(sport.sport,date)
    sport.backtest_contestID=contest_list[0] #for now, pick one contest
    data=tuple([data[key] if data[key]>-1 else 0 for player,data in sport.build_player_universe('','').iteritems()] for key in ['R2','confidence'])
    summary={'R2':{'mean':np.mean(data[0]),'medn':np.median(data[0]),'stdev':np.std(data[0])},
                'Confidence':{'mean':np.mean(data[1]),'medn':np.median(data[1]),'stdev':np.std(data[1])}}
    print summary
    fig = plt.figure(figsize=(16, 8.65))
    ax1 = fig.add_subplot(2,1,1)
    ax2 = fig.add_subplot(2,1,2)
    x=[i for i in range(1,len(data[0])+1)]
    ax1.set_title('R2')
    ax2.set_title('confidence') 
    ax1.plot(x, data[0],'bo')
    ax2.plot(x, data[1],'bo')
    plt.show()  
    return

def todays_lineups(sport_list):
    FDSession = fdo.FDSession()
    contest_rosters = main.build_contest_rosters(FDSession,sport_list)
    #write to csv!
    return

###                TO DO
##---------------------------------------
#does order matter for feature_df and parameter array??? does it just work out?

##0: feature engineering
##1: refactor backtest into class
##2: historize opposing_defense_stats
##3: check points diff vs. confidence

##for features like FD_points_mean, median etc. does it make sense that we are including the game that day in those means/medians??
##it will increase our model R2/conf but does nothing for future predictions..

##3: add a write to CSV function to track backtests or start using juptyer
##4: player maps!
##7: add db check if event has already been historized
##8: study more information from hist_lineups_dict --> do we do better in certain contest sizes??


##BENCHMARK TO BEAT FOR SCORING
#https://www.fanduel.com/insider/2015/11/10/fanduel-nba-benchmarks-points-to-target-in-each-contest-type/

