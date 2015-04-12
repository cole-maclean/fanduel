from logging import getLogger, Handler
from urllib import urlopen
from warnings import simplefilter
from time import sleep
import requests

class NullHandler(Handler):
    def emit(self, record):
        pass

class CONSTANTS:
    BASE = 'http://gd2.mlb.com/components/game/%LEAGUE%/'
    FETCH_TRIES = 10

class Fetcher:
    @classmethod
    def fetch(self, url):
        for i in xrange(CONSTANTS.FETCH_TRIES):
            logger.debug('FETCH %s' % url)
            try:
                r = requests.get(url)
            except IOError, e:
                if i == CONSTANTS.FETCH_TRIES-1:
                    logger.error('ERROR %s (max tries %s exhausted)' % (url, CONSTANTS.FETCH_TRIES))
                sleep(1)
                continue

            if r.status_code == 404:
                return None
            else:
                return r.text
            break

logger = getLogger('gameday')
logger.addHandler(NullHandler())

