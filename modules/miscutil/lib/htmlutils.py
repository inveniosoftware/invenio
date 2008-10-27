# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
from invenio.config import CFG_SITE_URL
import re
import cgi

try:
    from invenio.fckeditor import fckeditor
    fckeditor_available = True
except ImportError, e:
    fckeditor_available = False
# List of allowed tags (tags that won't create any XSS risk)
cfg_html_buffer_allowed_tag_whitelist = ('a',
                                         'p', 'br', 'blockquote',
                                         'strong', 'b', 'u', 'i', 'em',
                                         'ul', 'ol', 'li', 'sub', 'sup')
# List of allowed attributes. Be cautious, some attributes may be risky:
# <p style="background: url(myxss_suite.js)">
cfg_html_buffer_allowed_attribute_whitelist = ('href', 'name')

def nmtoken_from_string(text):
    """
    Returns a Nmtoken from a string.
    It is useful to produce XHTML valid values for the 'name'
    attribute of an anchor.

    CAUTION: the function is surjective: 2 different texts might lead to
    the same result. This is improbable on a single page.

    Nmtoken is the type that is a mixture of characters supported in
    attributes such as 'name' in HTML 'a' tag. For example,
    <a name="Articles%20%26%20Preprints"> should be tranformed to
    <a name="Articles372037263720Preprints"> using this function.
    http://www.w3.org/TR/2000/REC-xml-20001006#NT-Nmtoken

    Also note that this function filters more characters than
    specified by the definition of Nmtoken ('CombiningChar' and
    'Extender' charsets are filtered out).
    """
    text = text.replace('-', '--')
    return ''.join( [( ((not char.isalnum() and not char in ['.', '-', '_', ':']) and str(ord(char))) or char)
            for char in text] )

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

    Usage: from invenio.htmlutils import HTMLWasher
           washer = HTMLWasher()
           escaped_text = washer.wash(unescaped_text)

    Examples:
        a.wash('Spam and <b><blink>eggs</blink></b>')
        => 'Spam and <b>eggs</b>'
        a.wash('Spam and <b><blink>eggs</blink></b>', True)
        => 'Spam and <b>&lt;blink&gt;eggs&lt;/blink&gt;</b>'
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
        self.re_js = re.compile( ".*(j|&#106;|&#74;)"\
                                "\s*(a|&#97;|&#65;)"\
                                "\s*(v|&#118;|&#86;)"\
                                "\s*(a|&#97;|&#65;)"\
                                "\s*(s|&#115;|&#83;)"\
                                "\s*(c|&#99;|&#67;)"\
                                "\s*(r|&#114;|&#82;)"\
                                "\s*(i|&#195;|&#73;)"\
                                "\s*(p|&#112;|&#80;)"\
                                "\s*(t|&#112;|&#84)"\
                                "\s*(:|&#58;).*", re.IGNORECASE | re.DOTALL)
        # vbscript:
        self.re_vb = re.compile( ".*(v|&#118;|&#86;)"\
                                "\s*(b|&#98;|&#66;)"\
                                "\s*(s|&#115;|&#83;)"\
                                "\s*(c|&#99;|&#67;)"\
                                "\s*(r|&#114;|&#82;)"\
                                "\s*(i|&#195;|&#73;)"\
                                "\s*(p|&#112;|&#80;)"\
                                "\s*(t|&#112;|&#84;)"\
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
        self.reset()
        self.result = ''
        self.render_unallowed_tags = render_unallowed_tags
        self.allowed_tag_whitelist = allowed_tag_whitelist
        self.allowed_attribute_whitelist = allowed_attribute_whitelist
        self.feed(html_buffer)
        self.close()

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
        if self.re_js.match(value) or self.re_vb.match(value):
            return ''
        return value

    def handle_charref(self, name):
        """Process character references of the form "&#ref;". Return it as it is."""
        self.result += '&#' + name + ';'

    def handle_entityref(self, name):
        """Process a general entity reference of the form "&name;".
        Return it as it is."""
        self.result += '&' + name + ';'

def get_html_text_editor(name, id=None, content='', textual_content=None, width='300px', height='200px',
                         enabled=True, file_upload_url=None, toolbar_set="Basic"):
    """
    Returns a wysiwyg editor (FCKeditor) to embed in html pages.

    Fall back to a simple textarea when the library is not installed,
    or when the user's browser is not compatible with the editor, or
    when 'enable' == False, or when javascript is not enabled.

    NOTE that the output also contains a hidden field named
    'editor_type' that contains the kind of editor used: 'textarea' or
    'fckeditor'

    Based on 'editor_type' you might want to take different actions,
    like replace \n\r with <br/> when editor_type == 'textarea', but
    not when editor_type == 'fckeditor'.

    Parameters:

           name - *str* the name attribute of the returned editor

             id - *str* the id attribute of the returned editor (when
                  applicable)

        content - *str* the default content of the editor.

textual_content - *str* a content formatted for the case where the
                  wysiwyg editor is not available for user. When not
                  specified, use value of 'content'

          width - *str* width of the editor in an html compatible unit:
                  Eg: '400px', '50%'

         height - *str* height of the editor in an html compatible unit:
                  Eg: '400px', '50%'

         enable - *bool* if the wysiwyg editor is return (True) or if a
                  simple texteara is returned (False)

file_upload_url - *str* the URL used to upload new files via the
                  editor upload panel. You have to implement the
                  handler for your own use. The URL handler will get
                  form variables 'File' as POST for the uploaded file,
                  and 'Type' as GET for the type of file ('file',
                  'image', 'flash', 'media')
                  When value is not given, the file upload is disabled.

    toolbar_set - *str* the name of the toolbar layout to
                  use. FCKeditor comes by default with 'Basic' and
                  'Default'. To define other sets, customize the
                  config file in
                  /opt/cds-invenio/var/www/fckeditor/invenio-fckconfig.js

    Returns:

        the HTML markup of the editor

    """

##     NOTE that the FCKeditor is instantiated using the Python interface
##     provided with the editor, which must have access to the
##     os.environ['HTTP_USER_AGENT'] variable to check if user's browser
##     is compatible with the editor. This value is set in the
##     webinterface_handler file.

    if textual_content is None:
        textual_content = content

    editor = ''
    textarea = '<textarea %(id)s name="%(name)s" style="width:%(width)s;height:%(height)s">%(content)s</textarea>' \
                     % {'content': textual_content,
                        'width': width,
                        'height': height,
                        'name': name,
                        'id': id and ('id="%s"' % id) or ''}

    if enabled and fckeditor_available:
        oFCKeditor = fckeditor.FCKeditor(name)
        oFCKeditor.BasePath = '/fckeditor/'
        # TODO: check if path would not better be a parameter of the function
        oFCKeditor.Config["CustomConfigurationsPath"] = "/fckeditor/invenio-fckeditor-config.js"

        # Though not recommended, it is much better that users gets a
        # <br/> when pressing carriage return than a <p> element. Then
        # when a user replies to a webcomment without the FCKeditor,
        # line breaks are nicely displayed.
        oFCKeditor.Config["EnterMode"] = 'br'

        if file_upload_url is not None:
            oFCKeditor.Config["LinkUploadURL"] = file_upload_url
            oFCKeditor.Config["ImageUploadURL"] = file_upload_url + '%3Ftype%3DImage'
            oFCKeditor.Config["FlashUploadURL"] = file_upload_url + '%3Ftype%3DFlash'
            oFCKeditor.Config["MediaUploadURL"] = file_upload_url + '%3Ftype%3DMedia'

            oFCKeditor.Config["LinkUpload"] = 'true'
            oFCKeditor.Config["ImageUpload"] = 'true'
            oFCKeditor.Config["FlashUpload"] = 'true'
        else:
            oFCKeditor.Config["LinkUpload"] = 'false'
            oFCKeditor.Config["ImageUpload"] = 'false'
            oFCKeditor.Config["FlashUpload"] = 'false'

        # In any case, disable browsing on the server
        oFCKeditor.Config["LinkBrowser"] = 'false'
        oFCKeditor.Config["ImageBrowser"] = 'false'
        oFCKeditor.Config["FlashBrowser"] = 'false'

        # Set the toolbar
        oFCKeditor.ToolbarSet = toolbar_set
        #toolbar_set_js_repr = repr(toolbar_set) + ';'
        #oFCKeditor.Config["ToolbarSets"] = {}
        #oFCKeditor.Config['ToolbarSets["Default"]'] = toolbar_set_js_repr

        # Set the CSS used by Invenio, so that it is also applied
        # inside the editor
        oFCKeditor.Config["EditorAreaCSS"] = CFG_SITE_URL + '/img/cds.css'

        oFCKeditor.Value = content
        oFCKeditor.Height = height
        oFCKeditor.Width = width
        if oFCKeditor.IsCompatible():
            # Browser seems compatible
            editor += '<script language="JavaScript" type="text/javascript">'
            editor += "document.write('" + oFCKeditor.Create().replace('\n', '').replace('\r', '') + "');"
            editor += "document.write('<input type=\"hidden\" name=\"editor_type\" value=\"fckeditor\" />');"
            editor += '</script>'
            # In case javascript is disabled
            editor += '<noscript>' + textarea + \
                      '<input type="hidden" name="editor_type" value="textarea" /></noscript>'
        else:
            # Browser is not compatible
            editor = textarea
            editor += '<input type="hidden" name="editor_type" value="textarea" />'
    else:
        # FCKedior is not installed
        editor = textarea
        editor += '<input type="hidden" name="editor_type" value="textarea" />'

    return editor
