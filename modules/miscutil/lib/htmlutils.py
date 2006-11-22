# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""HTML utilities."""

__revision__ = "$Id$"

from HTMLParser import HTMLParser
import re
import cgi

# List of allowed tags (tags that won't create any XSS risk)
cfg_html_buffer_allowed_tag_whitelist = ['a', 
                                         'p', 'br', 'blockquote',
                                         'strong', 'b', 'u', 'i', 'em',
                                         'ul', 'ol', 'li']
# List of allowed attributes. Be cautious, some attributes may be risky:
# <p style="background: url(myxss_suite.js)">
cfg_html_buffer_allowed_attribute_whitelist = ['href', 'name']

def escape_html(text, escape_quotes=False):
    """Escape all HTML tags, avoiding XSS attacks.
    < => &lt;
    > => &gt;
    & => &amp:
    @param text: text to be escaped from HTML tags
    @param escape_quotes: if True, escape any quote mark to its HTML entity:
                          " => &quot;
                          ' => &#34;
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if escape_quotes:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#34;')
    return text

class HTMLWasher(HTMLParser):
    """
    Creates a washer for HTML, avoiding XSS attacks. See wash function for 
    details on parameters.
    
    Usage: from inveniohtmlutils import HTMLWasher
           washer = HTMLWasher()
           escaped_text = washer.wash(unescaped_text)
           
    Examples:
        a.wash('Spam and <b><blink>eggs</blink></b>')
        => 'Spam and <b>eggs&lt;u&gt;</b>'
        a.wash('Spam and <b><blink>eggs</blink></b>', True)
        => 'Spam and <b>&lt;blink&gt;eggs&lt;blink&gt;</b>'
        a.wash('Spam and <b><a href="python.org">eggs</u></b>')
        => 'Spam and <b><a href="python.org">eggs</a></b>'
        a.wash('Spam and <b><a href="javascript:xss();">eggs</a></b>')
        =>'Spam and <b><a href="">eggs</a></b>'
        a.wash('Spam and <b><a href="jaVas  cRipt:xss();">poilu</a></b>')
        =>'Spam and <b><a href="">eggs</a></b>'
    """
    
    def __init__(self):
        """ Constructor; initializes washer """
        HTMLParser.__init__(self)
        self.result = ''
        self.render_unallowed_tags = False
        self.allowed_tag_whitelist = \
                cfg_html_buffer_allowed_tag_whitelist
        self.allowed_attribute_whitelist = \
                cfg_html_buffer_allowed_attribute_whitelist
        # javascript:
        self.re_js = re.compile( ".*(j|&#106;)"\
                                "\s*(a|&#97;)"\
                                "\s*(v|&#118;)"\
                                "\s*(a|&#97;)"\
                                "\s*(s|&#115;)"\
                                "\s*(c|&#99;)"\
                                "\s*(r|&#114;)"\
                                "\s*(i|&#195;)"\
                                "\s*(p|&#112;)"\
                                "\s*(t|&#112;)"\
                                "\s*(:|&#58;).*", re.IGNORECASE | re.DOTALL)
        # vbscript:                           
        self.re_vb = re.compile( ".*(v|&#118;)"\
                                "\s*(b|&#98;)"\
                                "\s*(s|&#115;)"\
                                "\s*(c|&#99;)"\
                                "\s*(r|&#114;)"\
                                "\s*(i|&#195;)"\
                                "\s*(p|&#112;)"\
                                "\s*(t|&#112;)"\
                                "\s*(:|&#58;).*", re.IGNORECASE | re.DOTALL)

    def wash(self, html_buffer, 
             render_unallowed_tags=False,
             allowed_tag_whitelist=cfg_html_buffer_allowed_tag_whitelist,
             allowed_attribute_whitelist=\
                    cfg_html_buffer_allowed_attribute_whitelist):
        """
        Wash HTML buffer, escaping XSS attacks.
        @param html_buffer: text to escape
        @param render_unallowed_tags: if True:
                                         print unallowed tags escaping < and >.
                                      else:
                                         only print content of unallowed tags.
        @param allowed_tag_whitelist: list of allowed tags
        @param allowed_attribute_whitelist: list of allowed attributes
        """
        self.result = ''
        self.render_unallowed_tags = render_unallowed_tags
        self.allowed_tag_whitelist = allowed_tag_whitelist
        self.allowed_attribute_whitelist = allowed_attribute_whitelist
        HTMLParser.feed(self, html_buffer)
        return self.result
    
    def handle_starttag(self, tag, attrs):
        """Function called for new opening tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            self.result  += '<' + tag
            for (attr, value) in attrs:
                if attr.lower() in self.allowed_attribute_whitelist:
                    self.result += ' %s="%s"' % \
                                     (attr, self.handle_attribute_value(value))
            self.result += '>'
        else:
            if self.render_unallowed_tags:
                self.result += '&lt;' + cgi.escape(tag)
                for (attr, value) in attrs:
                    self.result += ' %s="%s"' % \
                                     (attr, cgi.escape(value, True))
                self.result += '&gt;'
        
    def handle_data(self, data):
        """Function called for text nodes"""
        self.result += cgi.escape(data, True)
    
    def handle_endtag(self, tag):
        """Function called for ending of tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            self.result  += '</' + tag + '>'
        else:
            if self.render_unallowed_tags:
                self.result += '&lt;/' + cgi.escape(tag) + '&gt;'
    
    def handle_startendtag(self, tag, attrs):
        """Function called for empty tags (e.g. <br />)""" 
        if tag.lower() in self.allowed_tag_whitelist:
            self.result  += '<' + tag
            for (attr, value) in attrs:
                if attr.lower() in self.allowed_attribute_whitelist:
                    self.result += ' %s="%s"' % \
                                     (attr, self.handle_attribute_value(value))
            self.result += ' />'
        else:
            if self.render_unallowed_tags:
                self.result += '&lt;' + cgi.escape(tag)
                for (attr, value) in attrs:
                    self.result += ' %s="%s"' % \
                                     (attr, cgi.escape(value, True))
                self.result += ' /&gt;'
                                
    def handle_attribute_value(self, value):
        """Check attribute. Especially designed for avoiding URLs in the form:
        javascript:myXSSFunction();"""
        value = cgi.escape(value, True)
        if self.re_js.match(value) or self.re_vb.match(value):
            return ''
        return value