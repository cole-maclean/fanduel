import json
import urllib2
def get_JSON_data(sUrl,clean_strings = ''):
	try:
		response = urllib2.urlopen(sUrl)
		cdata = response.read()
		for cstr in clean_strings:
			cdata = cdata.replace(cstr,'')
		return json.loads(cdata)
	except urllib2.HTTPError, e:
		return "URL not found"
def parse_html(sUrl,sStart,sEnd):
    response = urllib2.urlopen(sUrl)
    shtml = response.read()
    shtml = shtml.replace('false',"False")
    intStart = shtml.find(sStart)
    intEnd = shtml.find(sEnd,intStart)
    parsed_html = shtml[intStart:intEnd].replace(sStart,"")
    return parsed_html
def cookie_login(login_URL,site_URL,sPassword):
	# Browser
	br = mechanize.Browser()
	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	br.addheaders = [('User-agent', 'Chrome')]
	# The site we will navigate into, handling it's session
	br.open(login_URL)
	# View available forms
	for f in br.forms():
	    print f
	# Select the second (index one) form (the first form is a search query box)
	br.select_form(nr=0)
	# User credentials
	#br.form['login'] = 'maclean.cole@gmail.com'
	br.form['password'] = sPassword
	# Login
	br.submit()
	return br.open(site_URL).read()