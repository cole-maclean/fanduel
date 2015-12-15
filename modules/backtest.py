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
            print 'contest: %s date: %s sport: %s' % (contest,date,sport.sport)
            output=sport.optimal_roster(0,0,-100,date,contest)
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
    lineup_points=0
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
        hist_lineups_dict=hist_model_lineups(sport, '2015-11-18','2015-12-10')
    else:
        hist_lineups_dict=hist_model_lineups(sport, '2015-12-02','2015-12-02')
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(hist_lineups_dict)
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
    # data=([0.42594964453014472, 0.41974994199752103, 0.57301700162639368, 0.63203724969370145, 0.53787127936458878, 0.62011084238325986, 0.63603472961859386, 0, 0.5909700225209672, 0.54344139788255141, 0.50799992314455655, 0.57467339194745226, 0.75232383098673117, 0.63166678632585749, 0.4264428137866707, 0.52516243592522427, 0.69032133876059931, 0.5717965494140631, 0.56999134212702862, 0.52142286694651541, 0.453271982702248, 0.58839663567561229, 0.50187462216112055, 0.57551652080502391, 0.47644432997189856, 0.44615608147895813, 0.54596147511316695, 0.47153849765272438, 0.58396256509382083, 0.52577612066925783, 0.58978539661076312, 0.68565122666761213, 0.59318002359793243, 0.57960770610691792, 0.51186835194791347, 0.40796801023858287, 0.43622106714639708, 0.56587238117635708, 0.55414580127796209, 0.58287468507176166, 0.3635651784803462, 0.57811702073175963, 0.53655289311730991, 0.7426084299745922, 0.47021554328473258, 0.49417683584901539, 0.60434375193628731, 0.4506752331955014, 0.68168990883527369, 0.5978436085191825, 0.49903570047797197, 0.44299458619307841, 0.53171919983021243, 0.67679479710453427, 0.46734800189121617, 0.52236835255285419, 0.57062305569531646, 0.67193767309302688, 0.44240098361567015, 0.56232208995981181, 0.54439665650375968, 0.5486758292417564, 0.37926357902059959, 0.58560989155469967, 0.7148680614000773, 0.54356835786552959], [-0.11218212688757934, 0.7309877188563908, 0.65123755411167394, 0.62175781654368234, 0.34687923892407779, 0.43805016660519658, 0.49628108978126728, 0, 0.1036477357528226, 0.18624175009332311, 0.48743440466688281, 0.76646224866789059, 0.50622776375272394, 0.57034311159638862, -0.15506823009802129, 0.37370808277098394, -1.9930923196371639, 0.58987446098165108, 0.38356438998197412, 0.21254371453200552, 0.60746270571765781, -0.11810944773120569, 0.17881122565641405, 0.66528517172813006, 0.49988691265397622, 0.36545185112822165, 0.29047875924913669, -0.24530400776495664, 0.21930918329490157, 0.170593541598, 0.64105004507383989, 0.56171728127666953, 0.37037973823134401, 0.72290487566660078, 0.40879842719405279, 0.51317037132392906, 0.47524296949052541, 0.47689902387879346, 0.41870973655211363, 0.44233345344558106, -18.751916349968557, 0.83358096234737133, 0.18178895472500478, 0.65454238793667341, -0.40687829970340461, 0.054792762018626373, 0.17610961953279058, -0.5575938745524629, 0.78603752440125996, 0.23622546885432172, 0.17759013333786833, 0.5622682413985659, 0.41677561961990839, 0.68830722066821348, 0.6040568569096566, 0.38531687876543019, -1.2829699506010557, 0.40445012472128894, 0.45030442667515225, 0.26552473770378837, 0.050892727273583183, 0.46719724273887275, -41.429323797064356, 0.69120353649564503, 0.13844156062386459, 0.22993126917082454])
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

###                TO DO
##---------------------------------------
##0: feature engineering
##1: refactor backtest into class

##3: add a write to CSV function to track backtests or start using juptyer
##4: player maps!
##7: add db check if event has already been historized
##8: study more information from hist_lineups_dict --> do we do better in certain contest sizes??


##BENCHMARK TO BEAT FOR SCORING
#https://www.fanduel.com/insider/2015/11/10/fanduel-nba-benchmarks-points-to-target-in-each-contest-type/

