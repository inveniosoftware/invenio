# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
WebJournal widget - Display weather forecast
"""
import os
import time
import re
import socket
try:
    # Try to load feedparser.  Remember for later if it was installed
    # or not. Note that feedparser is slow to load: if we don't load
    # it in a 'global' way, it will be loaded for every call to this
    # element.
    global feedparser
    import feedparser
    feedparser_available = 1
except ImportError:
    feedparser_available = 0

from invenio.config import \
     CFG_CACHEDIR, \
     CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.ext.logging import register_exception
from invenio.legacy.webjournal.utils import \
     parse_url_string, WEBJOURNAL_OPENER
from invenio.base.i18n import gettext_set_language

re_image_pattern = re.compile(r'<img\s*(class=["\']imageScale["\'])*?\s*src="(?P<image>\S*)"\s*/>',
                              re.DOTALL | re.IGNORECASE | re.VERBOSE)

yahoo_weather_rss_base_url = 'http://weather.yahooapis.com/forecastrss?w=%(location)s&u=%(degree_unit)s'

def format_element(bfo, location='782041', degree_unit='c' ,
           display_weather_icon='false', weather_icon_only='false'):
    """
    Display the latest weather forecast from Yahoo Weather

    (See http://developer.yahoo.com/weather/)

    @param location: Yahoo location code for the forecast
    @param degree_unit: Degree unit ('f'=Fahrenheit or 'c'=Celsius)
    @param display_weather_icon: if 'true', display weather icon inside the forecasts
    @param weather_icon_only: it 'true' display only the wheater icon (without text)
    """
    if not feedparser_available:
        return ""

    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    cached_filename = "webjournal_widget_weather_%s.rss" % journal_name
    expire_time_filename = "webjournal_widget_weather_%s_RSS_expires" % \
                           journal_name

    out = get_widget_html(yahoo_weather_rss_base_url % \
                          {'location': location, 'degree_unit': degree_unit},
                          cached_filename,
                          expire_time_filename,
                          journal_name)

    if weather_icon_only == 'true':
        try:
            out = '<img alt="" src="%s" align="bottom" />' % \
                  re_image_pattern.findall(out)[0][1]
        except:
            register_exception(req=bfo.req)
            out = ''
    elif display_weather_icon == 'false':
        try:
            out = re.sub(re_image_pattern, "", out)
        except:
            register_exception(req=bfo.req)
            out = ''

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def get_widget_html(yahoo_weather_rss, cached_filename, expire_time_filename, journal_name):
    """
    weather forecast using Yahoo! Weather service
    we check and store the "expires" data from the rss feed to decide when
    an update is needed.
    there always resides a cached version in cds CFG_CACHEDIR along with a flat
    file that indicates the time when the feed expires.
    """
    cached_weather_box =  _get_weather_from_cache(journal_name)
    if cached_weather_box:
        return cached_weather_box

    # No HTML cache? Then read locally saved feed data, and even
    # refresh it from Yahoo if it has expired.
    try:
        cached_rss_path = os.path.join(CFG_CACHEDIR, cached_filename)
        assert(os.path.exists(cached_rss_path))
        weather_feed = feedparser.parse(cached_rss_path)
        assert(not weather_feed.bozo_exception)
    except:
        try:
            _update_feed(yahoo_weather_rss, cached_filename, expire_time_filename)
            weather_feed = feedparser.parse('%s/%s' % \
                                            (CFG_CACHEDIR, cached_filename))
        except:
            return "<ul><li><i>" + _("No information available") + "</i></li></ul>"

    now_in_gmt = time.gmtime()
    try:
        expire_time = time.strptime(open(expire_time_filename).read(),
                                    "%a, %d %b %Y %H:%M:%S %Z")
        diff = time.mktime(expire_time) - time.mktime(now_in_gmt)
    except:
        diff = -1
    if diff < 0:
        try:
            _update_feed(yahoo_weather_rss, cached_filename, expire_time_filename)
            weather_feed = feedparser.parse('%s/%s' % \
                                            (CFG_CACHEDIR, cached_filename))
        except:
            return "<ul><li><i>" + _("No information available") + "</i></li></ul>"

    # Construct the HTML. Well, simply take the one provided by
    # Yahoo..
    html = weather_feed.entries[0]['summary']
    cache_weather(html, journal_name)

    return html


def _get_weather_from_cache(journal_name):
    """
    Try to get the weather information from cache. Return False if
    cache does not exist
    """
    cache_path = os.path.abspath('%s/webjournal/%s/weather.html' % \
                                  (CFG_CACHEDIR,
                                   journal_name))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Make sure we are reading from correct directory (you
        # know, in case there are '../../' inside journal name..)
        return False
    try:
        last_update = os.path.getctime(cache_path)
    except:
        return False

    now = time.time()
    if (last_update + 15*60) < now:
        # invalidate after 15 minutes
        return False
    try:
        cached_file = open(cache_path).read()
    except:
        return False

    return cached_file

def cache_weather(html, journal_name):
    """
    Caches the weather box for 30 minutes.
    """
    if not CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        cache_path = os.path.abspath('%s/webjournal/%s/weather.html' % \
                                      (CFG_CACHEDIR,
                                       journal_name))
        if cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
            # Do not try to cache if the journal name led us to some
            # other directory ('../../' inside journal name for
            # example)
            cache_dir = CFG_CACHEDIR + '/webjournal/' + journal_name
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
            cache_file = file(cache_path, "w")
            cache_file.write(html)
            cache_file.close()

def _update_feed(yahoo_weather_rss, cached_filename, expire_time_filename):
    """
    Retrieve the latest weather information from Yahoo and write it to
    'cached_filename'. Also write the supposed expiration date
    provided by Yahoo to 'expire_time_filename'.
    """
    default_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(2.0)
    try:
        try:
            feed = WEBJOURNAL_OPENER.open(yahoo_weather_rss)
        except:
            return
    finally:
        socket.setdefaulttimeout(default_timeout)

    cached_file = open('%s/%s' % (CFG_CACHEDIR, cached_filename), 'w')
    cached_file.write(feed.read())
    cached_file.close()

    feed_data = feedparser.parse(yahoo_weather_rss)
    expire_time = feed_data.headers['expires']
    expire_file = open('%s/%s' % (CFG_CACHEDIR, expire_time_filename), 'w')
    expire_file.write(expire_time)
    expire_file.close()

_ = gettext_set_language('en')
dummy = _("Under the CERN sky")
