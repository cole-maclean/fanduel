import sys
from StringIO import StringIO
import urllib
import urllib2
import gzip
import json
import datetime
import dateutil.parser
import httplib
import socket
import ssl
import time
import os

# Replace with your access token
access_token = "2d00a40a-70ec-43a9-97db-dadee3fcf836"

# Replace with your bot name and email/website to contact if there is a problem
# e.g., "mybot/0.1 (https://erikberg.com/)"
user_agent = "ianjameswhitestone@gmail.com"

# Some problems have been reported that Python 2.x fails to negotiate the
# correct SSL protocol when connecting over HTTPS. This code forces
# Python to use TLSv1.
# More information and code from http://bugs.python.org/issue11220
class TLS1Connection(httplib.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                ssl_version=ssl.PROTOCOL_TLSv1)

class TLS1Handler(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(TLS1Connection, req)

urllib2.install_opener(urllib2.build_opener(TLS1Handler()))

def main(Sport,method,parameters):
    # set the API method, format, and any parameters
    host = "erikberg.com"
    sport = Sport.sport.lower()
    method = method
    game_id = Sport.gameid
    data_format = "json"
    parameters = parameters

    # Pass method, format, and parameters to build request url
    url = build_url(host, sport, method, game_id, data_format, parameters)

    req = urllib2.Request(url)
    # Set Authorization header
    req.add_header("Authorization", "Bearer " + access_token)
    # Set user agent
    req.add_header("User-agent", user_agent)
    # Tell server we can handle gzipped content
    req.add_header("Accept-encoding", "gzip")

    try:
        response = urllib2.urlopen(req)
        time.sleep(10)
    except urllib2.HTTPError, err:
        print "Server returned {} error code!\n{}".format(err.code, err.read())
        time.sleep(10)
        return False
        #sys.exit(1)
    except urllib2.URLError, err:
        print "Error retrieving file: {}".format(err.reason)
        time.sleep(10)
        return False
        #sys.exit(1)

    data = None
    if "gzip" == response.info().get("Content-encoding"):
        buf = StringIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()
    else:
        data = response.read()
    if data:
        return json.loads(data)

# See https://erikberg.com/api/methods Request URL Convention for
# an explanation
def build_url(host, sport, method, game_id, data_format, parameters):
    path = "/".join(filter(None, (sport, method, game_id)));
    url = "https://" + host + "/" + path + "." + data_format
    if parameters:
        paramstring = urllib.urlencode(parameters)
        url = url + "?" + paramstring
    return url