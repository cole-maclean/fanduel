import os
import re
import random
import hashlib
import hmac
from string import letters
import data_scrapping
import webapp2
import jinja2
import main
import numpy

import cgi
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import rdbms
import MySQLdb
import threading

from google.appengine.ext import db
from google.appengine.api import memcache

import logging

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'),
                               autoescape = False)

# Define your production Cloud SQL instance information.
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)
class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        return render_str(template, **params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
class LoadHistData(MainHandler):
    def get(self):
        self.render("test.html")
    def post(self):
        memcache.set(key='last_gameid',value=2014021010)
        FD_url = str(self.request.get('contesturl'))
        print FD_url
        FD_contests = data_scrapping.get_FD_contests(FD_url)
        contest_count = len(FD_contests.keys())/2
        memcache.set(key='slate_size',value=contest_count)
        last_gameid = data_scrapping.update_gamedata(memcache.get('last_gameid')) - contest_count
        memcache.set(key='last_gameid',value=last_gameid)
        self.redirect("/")
class ClearWinsCache(MainHandler):
    def post(self):
        if memcache.get('winscache') == None:
            pass
        else:
            memcache.set(key='winscache',value = None)
        self.redirect("/")
class ClearLineupCache(MainHandler):
    def post(self):
        if memcache.get('lineupcache') == None:
            pass
        else:
            memcache.set(key='lineupcache',value = None)
        self.redirect("/")
class GenerateRoster(MainHandler):
    def post(self):
        memcache.set(key='last_gameid',value=2014021010)
        hist_gameid = memcache.get('last_gameid') - int(self.request.get('histgamecount'))
        FD_url = self.request.get('contesturl')
        losingteamlist = self.request.get('losingteamlist')
        result,player_universe,objective = main.optimum_roster(hist_gameid,FD_url,losingteamlist)
        print result.xf
        self.redirect("/")
class Main(MainHandler):
    def get(self):
        #memcache.set(key='lineupcache', value=[{'player':'cole','position':'LW','team':'colesteam','salary':2500,'objective':'test','keep':"True",'omit':"True"}])
        player_dict = memcache.get('lineupcache')
        self.render("main.html",player_dict = player_dict)
    def post(self):
        pass
app = webapp2.WSGIApplication([('/', Main),
                                ('/loadhistdata',LoadHistData),
                                ('/clearwinscache',ClearWinsCache),
                                ('/clearlineupcache',ClearLineupCache),
                                ('/generateroster',GenerateRoster)
                               ],
                              debug=True)