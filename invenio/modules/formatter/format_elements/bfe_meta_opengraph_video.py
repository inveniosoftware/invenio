# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2013 CERN.
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

"""BibFormat element - return the video of a record"""

import cgi
from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_CERN_SITE
from invenio.legacy.bibdocfile.api import BibRecDocs, get_superformat_from_format
from invenio.config import CFG_WEBSEARCH_ENABLE_OPENGRAPH

def format_element(bfo):
    """
    Return the video of the record, suitable for the Open Graph protocol.
    """
    if not CFG_WEBSEARCH_ENABLE_OPENGRAPH:
        return ""
    bibarchive = BibRecDocs(bfo.recID)
    bibdocs = bibarchive.list_bibdocs()
    additional_tags = ""
    tags = []
    videos = []
    images = []

    for doc in bibdocs:
        found_icons = []
        found_image_url = ''
        for docfile in doc.list_latest_files():
            if docfile.is_icon():
                found_icons.append((docfile.get_size(), docfile.get_url()))
            elif get_superformat_from_format(docfile.get_format()).lower() in [".mp4", '.webm', '.ogv']:
                found_image_url = docfile.get_url()
        found_icons.sort()

        for icon_size, icon_url in found_icons:
            images.append((icon_url, icon_url.replace(CFG_SITE_URL, CFG_SITE_SECURE_URL)))
        if found_image_url:
            videos.append((found_image_url, found_image_url.replace(CFG_SITE_URL, CFG_SITE_SECURE_URL)))

    if CFG_CERN_SITE:
        mp4_urls = [url.replace('http://mediaarchive.cern.ch', 'https://mediastream.cern.ch') \
                    for url in bfo.fields('8567_u') if url.endswith('.mp4')]
        img_urls = [url.replace('http://mediaarchive.cern.ch', 'https://mediastream.cern.ch') \
                    for url in bfo.fields('8567_u') if url.endswith('.jpg') or url.endswith('.png')]

        if mp4_urls:
            mp4_url = mp4_urls[0]
            if "4/3" in bfo.field("300__b"):
                width = "640"
                height = "480"
            else:
                width = "640"
                height = "360"
            additional_tags += '''
                <meta property="og:video" content="%(CFG_CERN_PLAYER_URL)s?file=%(mp4_url_relative)s&streamer=%(CFG_STREAMER_URL)s&provider=rtmp&stretching=exactfit&image=%(image_url)s" />
                <meta property="og:video:height" content="%(height)s" />
                <meta property="og:video:width" content="%(width)s" />
                <meta property="og:video:type" content="application/x-shockwave-flash" />
                <meta property="og:video" content="%(mp4_url)s" />
                <meta property="og:video:type" content="video/mp4" />
                <meta property="og:image" content="%(image_url)s" />
                <meta name="twitter:player:height" content="%(height)s" />
                <meta name="twitter:player:width" content="%(width)s" />

                <link rel="image_src" href="%(image_url)s" />
                <link rel="video_src" href="%(CFG_CERN_PLAYER_URL)s?file=%(mp4_url_relative)s&streamer=%(CFG_STREAMER_URL)s&provider=rtmp&stretching=exactfit&image=%(image_url)s"/>
                ''' % {'CFG_CERN_PLAYER_URL': "https://cds.cern.ch/mediaplayer.swf",
                       'CFG_STREAMER_URL': "rtmp://wowza.cern.ch:1935/vod",
                       'width': width,
                       'height': height,
                       'image_url': img_urls and img_urls[0] or '',
                       'mp4_url': mp4_url.replace('http://mediaarchive.cern.ch', 'https://mediastream.cern.ch'),
                       'mp4_url_relative': '/' + '/'.join(mp4_url.split('/')[4:])}
            try:
                from invenio.media_utils import generate_embedding_url
                embed_url = generate_embedding_url(bfo.field('037__a'))
                additional_tags += '''<meta name="twitter:player" content="%s"/>''' % cgi.escape(embed_url, quote=True).replace('http://', 'https://', 1)
            except:
                pass


    tags = ['<meta property="og:image" content="%s" />%s' % (image_url, image_url != image_secure_url and '\n<meta property="og:image:secure_url" content="%s" />' % image_secure_url or "") for image_url, image_secure_url in images]
    tags.extend(['<meta property="og:video" content="%s" />%s' % (video_url, video_url != video_secure_url and '\n<meta property="og:video:secure_url" content="%s" />' % video_secure_url or "") for video_url, video_secure_url in videos])


    return "\n".join(tags) + additional_tags


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
