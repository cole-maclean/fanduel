from __future__ import division
from bs4 import BeautifulSoup
import urllib2
import ast
import data_scrapping_utils as uds
import data_scrapping #Cole: imported data_scrapping module for get_FD_playerlist()
import general_utils as Ugen


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
    else:
        return False 
def get_team_odds(sport):
    url="http://www.oddsshark.com/"+sport+"/odds/fullgame/moneyline"
    content= urllib2.urlopen(url).read()
    soup = BeautifulSoup(content)
    i=1 #counter for cells in excel
    odds_list={}
    date_raw=soup.find("div",{"class":"time type"}).get_text().split()
    date=date_raw[0]+date_raw[1][0]+date_raw[1][1] #Ian: first date in the table. if any of the row's dates do not equal this then it wont get the odds for that game because its on a diff day
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
            row_date=row_date_raw[0]+row_date_raw[1][0]+row_date_raw[1][1]

            if row_date==date: #Ian: check if current games date is equal to the date in the first row
                moneyline1=row.findAll("div",{"class":"book moneyline book-"+"1"})[0].get_text().split() #for now just do opening odds
                Cell("Output",i,3).value=moneyline1      #Cole: Changed excel writes to sheet Output      
                Cell("Output",i,1).value=team1
                Cell("Output",i,2).value=team2
                team_map = Ugen.excel_mapping("Team Map",3,1)
                if moneyline1:
                    odds_list[team_map[team1]]=round(odds_to_prob(moneyline1[0],'American Moneyline'),2)#Cole:incorporated mapping to change city name to NHL team name
                    odds_list[team_map[team2]]=round(odds_to_prob(moneyline1[1],'American Moneyline'),2)
            
            i=i+1
    Cell("Output",15,5).value=odds_list
    return odds_list

get_team_odds('NHL')