from __future__ import division
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import data_scrapping #Cole: imported data_scrapping module for get_FD_playerlist()
import general_utils as Ugen
from selenium import webdriver
from selenium.webdriver.support.ui import Select

def odds_to_prob(odd,type): #takes in a "string odd" and returns probability as %
    #http://www.bettingexpert.com/blog/how-to-convert-odds
    if type=='American Moneyline':
        if odd[0]=='+':
            return 100/(int(odd)+100)*100
        elif odd[0]=='-':
            return (-1)*int(odd)/((-1)*int(odd)+100)*100
        else:
            return 
    return 

def get_teamname_exceptions(name_str,sport):
    #NHL: New Jersey, NY Rangers or NY Islanders, Los Angeles, St.Louis, San Jose, Tampa Bay 
    #NBA: LA Clippers, LA Lakers, San Antonio, New Orleans, Oklahoma City, Golden State
    #MLB: St. Louis, NY Yankees, NY Mets, San Francisco, LA Dodgers, LA Angels, Kansas City, Tampa Bay, Chi White Sox, Chi Cubs 
    #NFL:  
    list=[]  
    if sport=='NHL':
        list=['NY','Los','New','San','Tampa','St.']
    elif sport=='NBA':
        list=['LA','San','New','Oklahoma','Golden',]
    elif sport=='MLB':
        list=['St.','NY','San','Chi','Kansas','LA','Tampa']
    else: #sport does not have exceptions list entered in this function
        print ('sport does not have exceptions list entered in this function')
    if name_str in list:
        return True
    return False

def get_team_odds(sport):
    url="http://www.oddsshark.com/"+sport+"/odds/fullgame/moneyline"
    content= urllib2.urlopen(url).read()
    soup = BeautifulSoup(content)
    i=1 #counter for cells in excel
    mlb_map=Ugen.excel_mapping("Team Map",7,6)
    nhl_map=Ugen.excel_mapping("Team Map",3,1)
    odds_list={}
    date_raw=soup.find("div",{"class":"time type"}).get_text().split()
    date=date_raw[0]+' '+date_raw[1][0]+date_raw[1][1] #Ian: first date in the table. if any of the row's dates do not equal this then it wont get the odds for that game because its on a diff day
    for z in range(0,2,1):
        if z==0:
            row_type='even'
        elif z==1:
            row_type='odd'
        for row in soup.findAll("div",{"class":"odds-row odds-row-moneyline "+row_type}): 
            teams=row.findAll("div",{ "class":"first teams type" })
            teams_list=teams[0].get_text().split() #two word teams get split into different elements here, teams_list=['New','Jersey','Calgary']
            j=0  
            for z in range(0,2,1):
                if get_teamname_exceptions(teams_list[j],sport):
                    if z==0:
                        if teams_list[j]=='Chi' and teams_list[j+1]=='White':
                            team1=teams_list[j]+ ' ' + teams_list[j+1]+ ' ' + teams_list[j+2]
                            j=j+3
                        else:
                            team1=teams_list[j]+ ' ' + teams_list[j+1]
                            j=j+2
                    elif z==1:
                        if teams_list[j]=='Chi' and teams_list[j+1]=='White':
                            team2=teams_list[j]+ ' ' + teams_list[j+1]+ ' ' + teams_list[j+2]
                        else:
                            team2=teams_list[j]+ ' ' + teams_list[j+1]
                else:
                    if z==0:
                        team1=teams_list[j]
                        j=j+1
                    elif z==1:
                        team2=teams_list[j]
            row_date_raw=row.find("div",{"class":"time type"}).get_text().split()
            row_date=row_date_raw[0]+' '+row_date_raw[1][0]+row_date_raw[1][1]
            if row_date==date: #Ian: check if current games date is equal to the date in the first row
                moneyline1=row.findAll("div",{"class":"book moneyline book-"+"1"})[0].get_text().split() #for now just do opening odds
                if sport=='MLB':
                    team_map = mlb_map
                elif sport=='NHL':
                    team_map=nhl_map
                else:
                    print 'team map does not exist for entered sport: %s' % sport
                    #return
                if moneyline1:
                    odds_list[team_map[team1]]=round(odds_to_prob(moneyline1[0],'American Moneyline'),2)#Cole:incorporated mapping to change city name to NHL team name
                    odds_list[team_map[team2]]=round(odds_to_prob(moneyline1[1],'American Moneyline'),2)
                    #odds_list[team1]=round(odds_to_prob(moneyline1[0],'American Moneyline'),2)
                    #odds_list[team2]=round(odds_to_prob(moneyline1[1],'American Moneyline'),2)
            i=i+1
    # Cell("Output",1,1).value=odds_list
    return [odds_list,date]


def vegas_odds_sportsbook(date): #takes in date YYYY-MM-DD or YYYYMMDD
    print 'getting odds for %s' % date
    url='http://www.sportsbookreview.com/betting-odds/mlb-baseball/merged/?date='+date.replace("-","")
    content=urllib2.urlopen(url).read()
    soup=BeautifulSoup(content)
    team_map=Ugen.mlb_map(10,4)
    table=soup.find("div",{"class":"eventGroup class-mlb-baseball"})
    odds_dict={}
    for row in soup.findAll("div",{"class":"event-holder holder-complete"}):
        row_data=row.find("div",{"class":"eventLine odd status-complete "})
        if not row_data:
            row_data=row.find("div",{"class":"eventLine  status-complete "})
        hyperlink=row_data.find("meta",{"itemprop":"url"})
        matchup_dict=get_gameday_odds(hyperlink.get('content'),team_map)
        for team,odds in matchup_dict.iteritems(): 
            if team not in odds_dict.keys(): #Ian: this is here so we don't take the second game of a double header (FD usually does first)
                odds_dict[team]=odds
    return odds_dict

def get_gameday_odds(url,team_map): #Ian: Refactor
    content=urllib2.urlopen(url).read()
    soup=BeautifulSoup(content)
    teams_raw=soup.find("h1",{"class":"teams"}).get_text()
    dayofweek=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day=[day for day in dayofweek if day in teams_raw.split(" vs ")[1]]
    try:
        team1_key=teams_raw.split(" vs ")[0]
        team2_key=teams_raw.split(" vs ")[1].split(day[0])[0].replace(u'\xa0\n',"").rstrip()
        team1=team_map[team1_key]
        team2=team_map[team2_key]
    except:
        print 'error in team names'
        return {}
    table=soup.find("div",{"class":"event-holder holder-complete"})
    odds_dict={}
    odds_dict[team1]={}
    odds_dict[team1]['home_team']=team2
    odds_dict[team1]['opponent']=team2
    odds_dict[team1]['point_spread']={}
    odds_dict[team1]['totals']={}
    odds_dict[team2]={}
    odds_dict[team2]['home_team']=team2
    odds_dict[team2]['opponent']=team1
    odds_dict[team2]['point_spread']={}
    odds_dict[team2]['totals']={}
    i=1
    for row in table.findAll("div",{"class":"eventLine status-complete"}):
        spread1=row.find("div",{"class":"el-div eventLine-opener"}).findAll("div",{"class":"eventLine-book-value"})[0].get_text()
        spread2=row.find("div",{"class":"el-div eventLine-opener"}).findAll("div",{"class":"eventLine-book-value"})[1].get_text()
        z=0
        if len(spread1)==0 or len(spread2)==0: #This is in case there aren't any opening odds
            for row in row.findAll("div",{"class":"el-div eventLine-book"}):
                spread1=row.findAll("div",{"class":"eventLine-book-value"})[0].get_text()
                spread2=row.findAll("div",{"class":"eventLine-book-value"})[1].get_text()
                if len(spread1)!=0 and len(spread2)!=0:
                    break
        if i==1:
            try:
                odds_dict[team1]['point_spread']['runline']=float(spread1.split()[0][0]+'1.5')
                odds_dict[team2]['point_spread']['runline']=float(spread2.split()[0][0]+'1.5')
                odds_dict[team1]['point_spread']['moneyline']=Ugen.odds_to_prob(spread1.split()[1],'American Moneyline')
                odds_dict[team2]['point_spread']['moneyline']=Ugen.odds_to_prob(spread2.split()[1],'American Moneyline')
            except:
                print 'no point spreads for given date'
        elif i==2:
            try:
                odds_dict[team1]['moneyline']=Ugen.odds_to_prob(spread1,'American Moneyline')
                odds_dict[team2]['moneyline']=Ugen.odds_to_prob(spread2,'American Moneyline')
            except:
                print 'no moneylines for given date'
        elif i==3:
            try:
                odds_dict[team1]['totals']['total']=Ugen.convert_proj_total(spread1.split()[0])
                odds_dict[team2]['totals']['total']=Ugen.convert_proj_total(spread2.split()[0])
                odds_dict[team1]['totals']['moneyline']=Ugen.odds_to_prob(spread1.split()[1],'American Moneyline')
                odds_dict[team2]['totals']['moneyline']=Ugen.odds_to_prob(spread2.split()[1],'American Moneyline')
                odds_dict[team1]['proj_run_total']=Ugen.proj_run_total(odds_dict[team1])
                odds_dict[team2]['proj_run_total']=Ugen.proj_run_total(odds_dict[team2])
            except:
                print 'no totals for given date'
        else:
            break
        i=i+1
    return odds_dict