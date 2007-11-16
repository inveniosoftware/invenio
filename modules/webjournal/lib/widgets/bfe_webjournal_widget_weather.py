#!/usr/bin/env python
"""
"""
from invenio import errorlib
from invenio.config import cachedir
import feedparser
import time
from urllib2 import urlopen
from invenio.errorlib import register_exception
import re

Weather_Service = "Yahoo! Weather"
# rss feed on yahoo weather, check developer.yahoo.com/weather for details
RSS_Feed = "http://weather.yahooapis.com/forecastrss?p=SZXX0008&u=c"
# filename of the rss feed in cache
Cached_Filename = "webjournal_widget_YahooWeather.rss"
# filename of flat file in cache that holds the expire time
Expire_Time_Filename = "weather_RSS_expires"

image_pattern = re.compile('''
                           <img\s*(class=["']imageScale["'])*?\s*src=(?P<image>\S*)\s*/>*
                           '''
                           ,re.DOTALL | re.IGNORECASE | re.VERBOSE)

def format(bfo, title=""):
    """
    wrapper function needed for BibFormat to route the widget HTML
    """
    out = get_widget_HTML()
    if title != "":
        try:
            weather_image_match = image_pattern.findall(out)[0]
            weather_image = weather_image_match[1]
            out = re.sub(image_pattern, "", out)
        except:
            register_exception(req=bfo.req)
            weather_image = ""
        weather_image = weather_image.replace("\"", "\'")
        out = '''<div id="weather" style="background: url(%s) left bottom no-repeat;" class="rmenuitem">
                    <h3 class="rmenutext">%s</h3>
                </div>
                <ul class="rmenulist">
                %s
                </ul>
                ''' % (weather_image, title, out)
    return out

def escape_values(bfo):
    """
    """
    return 0

def get_widget_HTML():
    """
    weather forecast using Yahoo! Weather service
    we check and store the "expires" data from the rss feed to decide when
    an update is needed.
    there always resides a cached version in cds cachedir along with a flat
    file that indicates the time when the feed expires.
    """
    try:
        weather_feed = feedparser.parse('%s/%s' % (cachedir, Cached_Filename))
    except:
        _update_feed()
        weather_feed = feedparser.parse('%s/%s' % (cachedir, Cached_Filename))
    
    now_in_gmt = time.gmtime()
    now_time_string = time.strftime( "%a, %d %b %Y %H:%M:%S GMT", now_in_gmt)
    try:
        expire_time_string = open('%s/%s' (cachedir, Expire_Time_Filename)).read()
        expire_time = time.strptime(open(Expire_Time_Filename).read(), "%a, %d %b %Y %H:%M:%S %Z")
        #expire_time['tm_isdt'] = 0
        expire_in_seconds = time.mktime(expire_time)
        now_in_seconds = time.mktime(now_in_gmt)
        diff = time.mktime(expire_time) - time.mktime(now_in_gmt)
    except:
        diff = -1
    if diff < 0:
        _update_feed()
        weather_feed = feedparser.parse('%s/%s' % (cachedir, Cached_Filename))
    
    # construct the HTML
    html = weather_feed.entries[0]['summary']
    
    return html
    
    
def _update_feed():
    """
    helper function that updates the feed by copying the new rss file to the
    cache dir and resetting the time string on the expireTime flat file
    """
    feed = urlopen(RSS_Feed)
    cached_file = open('%s/%s' % (cachedir, Cached_Filename), 'w')
    cached_file.write(feed.read())
    cached_file.close()
    feed_data = feedparser.parse(RSS_Feed)
    expire_time = feed_data.headers['expires']
    expire_file = open('%s/%s' % (cachedir, Expire_Time_Filename), 'w')
    expire_file.write(expire_time)
    expire_file.close()

if __name__ == "__main__":
    from invenio.bibformat_engine import BibFormatObject
    myrec = BibFormatObject(7)
    format(myrec)