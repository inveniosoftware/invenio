# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""HTML utilities."""

__revision__ = "$Id$"

## HACK: this is needed to load local HTMLParser from Python 2.7
## in case Python 2.6 is used.
import sys
_tmp_sys_path = sys.path
_new_sys_path = []
try:
    for path in sys.path:
        if ('dist-packages' in path) or ('site-packages' in path):
            _new_sys_path.append(path)
    _new_sys_path.extend(sys.path)
    sys.path = _new_sys_path
    from HTMLParser import HTMLParser
finally:
    sys.path = _tmp_sys_path

from invenio.config import CFG_SITE_URL, \
     CFG_MATHJAX_HOSTING, \
     CFG_MATHJAX_RENDERS_MATHML, \
     CFG_SITE_LANG, \
     CFG_WEBDIR
from invenio.textutils import indent_text, encode_for_xml
import re
import cgi
import os
import sys
if sys.hexversion < 0x2060000:
    try:
        import simplejson as json
        CFG_JSON_AVAILABLE = True
    except ImportError:
        # Okay, no Ajax app will be possible, but continue anyway,
        # since this package is only recommended, not mandatory.
        CFG_JSON_AVAILABLE = False
        json = None
else:
    import json
    CFG_JSON_AVAILABLE = True
try:
    from BeautifulSoup import BeautifulSoup
    CFG_BEAUTIFULSOUP_INSTALLED = True
except ImportError:
    CFG_BEAUTIFULSOUP_INSTALLED = False
try:
    import tidy
    CFG_TIDY_INSTALLED = True
except ImportError:
    CFG_TIDY_INSTALLED = False

# List of allowed tags (tags that won't create any XSS risk)
CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST = ('a',
                                         'p', 'br', 'blockquote',
                                         'strong', 'b', 'u', 'i', 'em',
                                         'ul', 'ol', 'li', 'sub', 'sup', 'div', 'strike')
# List of allowed attributes. Be cautious, some attributes may be risky:
# <p style="background: url(myxss_suite.js)">
CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST = ('href', 'name', 'class')

## precompile some often-used regexp for speed reasons:
RE_HTML = re.compile("(?s)<[^>]*>|&#?\w+;")
RE_HTML_WITHOUT_ESCAPED_CHARS = re.compile("(?s)<[^>]*>")

# url validation regex
regex_url = re.compile(r'^(?:http|ftp)s?://' # http:// or https://
                       r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                       r'localhost|' #localhost...
                       r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                       r'(?::\d+)?' # optional port
                       r'(?:/?|[/?]\S+)$', re.IGNORECASE)

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
                          ' => &#39;
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if escape_quotes:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
    return text


CFG_JS_CHARS_MAPPINGS = {
    '\\': '\\\\',
    "'": "\\'",
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '\v': '\\v',
    }
for i in range(0x20):
    CFG_JS_CHARS_MAPPINGS.setdefault(chr(i), '\\u%04x' % (i,))
for i in (0x2028, 0x2029):
    CFG_JS_CHARS_MAPPINGS.setdefault(unichr(i), '\\u%04x' % (i,))
RE_ESCAPE_JS_CHARS = re.compile(u'''[\\x00-\\x1f\\\\"\\\\'\\b\\f\\n\\r\\t\\v\u2028\u2029]''')
RE_CLOSING_SCRIPT_TAG = re.compile('</script>', re.IGNORECASE)
def escape_javascript_string(text, escape_for_html=True, escape_quote_for_html=False, escape_CDATA=True, escape_script_tag_with_quote='"'):
    """
    Escape text in order to be used as Javascript string in various
    context.

    Examples::
    >>> text = '''"Are you a Munchkin?" asked Dorothy.
"No, but I am their friend"'''
    >>> escape_javascript_string(text)
    >>> \\"&quot;Are you a Munchkin?\\" asked Dorothy.\\n\\"No, but I am their friend\\"'

    The returned string can be enclosed either in single or double
    quotes delimiters.

    THE FUNCTION ASSUME THAT YOU HAVE ALREDADY WASHED THE STRING FROM
    UNSAFE CONTENT, according to the context you plan to use the
    string. The function will just make sure that the string will not
    break you Javascript/HTML code/markup.

    If you plan to include the string inside the body of an HTML page,
    you will probably want to set C{escape_for_html} to True, in order
    to produce XHTML-valid pages when the input string contain
    characters such as < , > and &.

    Furthermore if you plan to include the string as part of a tag
    attribute (for eg. <a href="#" onclick="foo&quot;bar"), you might
    want to set C{escape_quote_for_html} to True.

    If you plan to include the string inside the body of an HTML page,
    enclosed by CDATA delimiters, then you would *not* need to escape
    HTML tags. Using CDATA delimeters enables to include Javascript
    strings meant to refer to HTML tags (eg. in case you would like to
    manipulate the DOM tree to add new nodes to the page), which would
    not be possible when escaping the HTML. For eg.:
        /*<![CDATA[*/
            document.getElementById('foo').innerHTML = '<p>bar</p>'
        /*]]>*/
    In this case you will probably want to set C{escape_CDATA} to True
    in order to produce an XHTML-valid document, in case a closing
    CDATA delimeter is in your input string. Parameter C{escape_CDATA}
    is not considered when C{escape_for_html} is set to True.

    Note that CDATA delimiters might be automatically added by the
    browser, based on the content-type used to serve the page.

    When C{escape_for_html} is set to False, whatever option is chosen
    for C{escape_CDATA}, the string must not contain a '</script>' tag
    (apparently...). The only option to keep this '</script>' tag (if
    you need it) is to split it, which requires to know which quote
    delimiter your plan to use. For eg:

    Examples::
    >>> text = '''foo</script>bar'''
    >>> val = escape_javascript_string(text, escape_for_html=False, escape_script_tag_with_quote='"')
    >>> 'foo</scr"+"ipt>bar'
    >>> mycode = '''alert("%s")''' % val

    C{escape_script_tag_with_quote} is not considered when
    C{escape_for_html} is set to True.

    If you are planning to return the string as part of a pure
    Javascript document, then you should in principle set both
    C{escape_for_html} and C{escape_CDATA} to False, and
    C{escape_script_tag_with_quote} to None.

    @param text: string to be escaped
    @param escape_for_html: if True, also escape input for HTML
    @param escape_CDATA: if True, escape closing CDATA tags (when C{escape_for_html} is False)
    @escape_script_tag_with_quote: which quote will be used to delimit your string, in case you must wash, but keep, C{</script>} tag (when C{escape_for_html} is False)
    """
    if escape_quote_for_html:
        text = text.replace('"', '&quot;')
    if escape_for_html:
        text = cgi.escape(text)
    elif escape_CDATA:
        text = text.replace(']]>', ']]]]><![CDATA[>')

    if CFG_JSON_AVAILABLE:
        text = json.dumps(text)[1:-1].replace("'", "\\'")
    else:
        # Try to emulate
        def escape_chars(matchobj):
            return CFG_JS_CHARS_MAPPINGS[matchobj.group(0)]

        text = RE_ESCAPE_JS_CHARS.sub(escape_chars, text)

    if not escape_for_html and escape_script_tag_with_quote:
        text = RE_CLOSING_SCRIPT_TAG.sub('''</scr%(q)s+%(q)sipt>''' % {'q': escape_script_tag_with_quote}, text)

    return text

class HTMLWasher(HTMLParser):
    """
    Creates a washer for HTML, avoiding XSS attacks. See wash function for
    details on parameters.

    Usage::
       from invenio.htmlutils import HTMLWasher
       washer = HTMLWasher()
       escaped_text = washer.wash(unescaped_text)

    Examples::
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
    silent = False

    def __init__(self):
        """ Constructor; initializes washer """
        HTMLParser.__init__(self)
        self.result = ''
        self.nb = 0
        self.previous_nbs = []
        self.previous_type_lists = []
        self.url = ''
        self.render_unallowed_tags = False
        self.allowed_tag_whitelist = \
                CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST
        self.allowed_attribute_whitelist = \
                CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST
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
             allowed_tag_whitelist=CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST,
             automatic_link_transformation=False,
             allowed_attribute_whitelist=\
                    CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST):
        """
        Wash HTML buffer, escaping XSS attacks.
        @param html_buffer: text to escape
        @param render_unallowed_tags: if True, print unallowed tags escaping
            < and >.  Else, only print content of unallowed tags.
        @param allowed_tag_whitelist: list of allowed tags
        @param allowed_attribute_whitelist: list of allowed attributes
        """
        self.reset()
        self.result = ''
        self.nb = 0
        self.previous_nbs = []
        self.previous_type_lists = []
        self.url = ''
        self.render_unallowed_tags = render_unallowed_tags
        self.automatic_link_transformation = automatic_link_transformation
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
            elif tag == 'style' or tag == 'script':
                # In that case we want to remove content too
                self.silent = True

    def handle_data(self, data):
        """Function called for text nodes"""
        if not self.silent:
            if self.automatic_link_transformation:
                self.result += transform_links(data)
            else:
                self.result += cgi.escape(data, True)

    def handle_endtag(self, tag):
        """Function called for ending of tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            self.result  += '</' + tag + '>'
        else:
            if self.render_unallowed_tags:
                self.result += '&lt;/' + cgi.escape(tag) + '&gt;'

        if tag == 'style' or tag == 'script':
            self.silent = False

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

def tidy_html(html_buffer, cleaning_lib='utidylib'):
    """
    Tidy up the input HTML using one of the installed cleaning
    libraries.

    @param html_buffer: the input HTML to clean up
    @type html_buffer: string
    @param cleaning_lib: chose the preferred library to clean the HTML. One of:
                         - utidylib
                         - beautifulsoup
    @return: a cleaned version of the input HTML
    @note: requires uTidylib or BeautifulSoup to be installed. If the chosen library is missing, the input X{html_buffer} is returned I{as is}.
    """

    if CFG_TIDY_INSTALLED and cleaning_lib == 'utidylib':
        options = dict(output_xhtml=1,
                       show_body_only=1,
                       merge_divs=0,
                       wrap=0)
        try:
            output = str(tidy.parseString(html_buffer, **options))
        except:
            output = html_buffer
    elif CFG_BEAUTIFULSOUP_INSTALLED and cleaning_lib == 'beautifulsoup':
        try:
            output = str(BeautifulSoup(html_buffer).prettify())
        except:
            output = html_buffer
    else:
        output = html_buffer

    return output

def get_mathjax_header(https=False):
    """
    Return the snippet of HTML code to put in HTML HEAD tag, in order to
    enable MathJax support.
    @param https: when using the CDN, whether to use the HTTPS URL rather
        than the HTTP one.
    @type https: bool
    @note: with new releases of MathJax, update this function toghether with
           $MJV variable in the root Makefile.am
    """
    if CFG_MATHJAX_HOSTING.lower() == 'cdn':
        if https:
            mathjax_path = "https://d3eoax9i5htok0.cloudfront.net/mathjax/2.1-latest"
        else:
            mathjax_path = "http://cdn.mathjax.org/mathjax/2.1-latest"
    else:
        mathjax_path = "/MathJax"

    if CFG_MATHJAX_RENDERS_MATHML:
        mathjax_config = "TeX-AMS-MML_HTMLorMML"
    else:
        mathjax_config = "TeX-AMS_HTML"

    return """<script type="text/x-mathjax-config">
MathJax.Hub.Config({
  tex2jax: {inlineMath: [['$','$']],
            processEscapes: true},
  showProcessingMessages: false,
  messageStyle: "none"
});
</script>
<script src="%(mathjax_path)s/MathJax.js?config=%(mathjax_config)s" type="text/javascript">
</script>""" % {
    'mathjax_path': mathjax_path,
    'mathjax_config': mathjax_config,
}

def is_html_text_editor_installed():
    """
    Returns True if the wysiwyg editor (CKeditor) is installed
    """
    return os.path.exists(os.path.join(CFG_WEBDIR, 'ckeditor', 'ckeditor.js'))

ckeditor_available = is_html_text_editor_installed()

def get_html_text_editor(name, id=None, content='', textual_content=None, width='300px', height='200px',
                         enabled=True, file_upload_url=None, toolbar_set="Basic",
                         custom_configurations_path='/ckeditor/invenio-ckeditor-config.js',
                         ln=CFG_SITE_LANG):
    """
    Returns a wysiwyg editor (CKEditor) to embed in html pages.

    Fall back to a simple textarea when the library is not installed,
    or when the user's browser is not compatible with the editor, or
    when 'enable' is False, or when javascript is not enabled.

    NOTE that the output also contains a hidden field named
    'editor_type' that contains the kind of editor used, 'textarea' or
    'ckeditor'.

    Based on 'editor_type' you might want to take different actions,
    like replace CRLF with <br/> when editor_type equals to
    'textarea', but not when editor_type equals to 'ckeditor'.

    @param name: *str* the name attribute of the returned editor

    @param id: *str* the id attribute of the returned editor (when
        applicable)

    @param content: *str* the default content of the editor.

    @param textual_content: *str* a content formatted for the case where the
        wysiwyg editor is not available for user. When not
        specified, use value of 'content'

    @param width: *str* width of the editor in an html compatible unit:
        Eg: '400px', '50%'.

    @param height: *str* height of the editor in an html compatible unit:
        Eg: '400px', '50%'.

    @param enabled: *bool* if the wysiwyg editor is return (True) or if a
        simple texteara is returned (False)

    @param file_upload_url: *str* the URL used to upload new files via the
        editor upload panel. You have to implement the
        handler for your own use. The URL handler will get
        form variables 'File' as POST for the uploaded file,
        and 'Type' as GET for the type of file ('file',
        'image', 'flash', 'media')
        When value is not given, the file upload is disabled.

    @param toolbar_set: *str* the name of the toolbar layout to
        use. CKeditor comes by default with 'Basic' and
        'Default'. To define other sets, customize the
        config file in
        /opt/cds-invenio/var/www/ckeditor/invenio-ckconfig.js

    @param custom_configurations_path: *str* value for the CKeditor config
        variable 'CustomConfigurationsPath',
        which allows to specify the path of a
        file that contains a custom configuration
        for the editor. The path is relative to
        /opt/invenio/var/www/

    @return: the HTML markup of the editor
    """
    if textual_content is None:
        textual_content = content

    editor = ''

    if enabled and ckeditor_available:
        # Prepare upload path settings
        file_upload_script = ''
        if file_upload_url is not None:
            file_upload_script = ''',
            filebrowserLinkUploadUrl: '%(file_upload_url)s',
            filebrowserImageUploadUrl: '%(file_upload_url)s?type=Image',
            filebrowserFlashUploadUrl: '%(file_upload_url)s?type=Flash'
            ''' % {'file_upload_url': file_upload_url}

        # Prepare code to instantiate an editor
        editor += '''
        <script type="text/javascript" language="javascript">//<![CDATA[
        /* Load the script only once, or else multiple instance of the editor on the same page will not work */
        var INVENIO_CKEDITOR_ALREADY_LOADED
            if (INVENIO_CKEDITOR_ALREADY_LOADED != 1) {
                document.write('<script type="text/javascript" src="%(CFG_SITE_URL)s/ckeditor/ckeditor.js"><\/script>');
                INVENIO_CKEDITOR_ALREADY_LOADED = 1;
            }
        //]]></script>
        <input type="hidden" name="editor_type" id="%(id)seditortype" value="textarea" />
        <textarea rows="100" cols="80" id="%(id)s" name="%(name)s" style="width:%(width)s;height:%(height)s">%(textual_content)s</textarea>
        <textarea rows="100" cols="80" id="%(id)shtmlvalue" name="%(name)shtmlvalue" style="display:none;width:%(width)s;height:%(height)s">%(html_content)s</textarea>
        <script type="text/javascript">//<![CDATA[
          var CKEDITOR_BASEPATH = '/ckeditor/';

          CKEDITOR.replace( '%(name)s',
                            {customConfig: '%(custom_configurations_path)s',
                            toolbar: '%(toolbar)s',
                            width: '%(width)s',
                            height:'%(height)s',
                            language: '%(ln)s'
                            %(file_upload_script)s
                            });

        CKEDITOR.on('instanceReady',
          function( evt )
          {
            /* If CKeditor was correctly loaded, display the nice HTML representation */
            var oEditor = evt.editor;
            editor_id = oEditor.id
            editor_name = oEditor.name
            var html_editor = document.getElementById(editor_name + 'htmlvalue');
            oEditor.setData(html_editor.value);
            var editor_type_field = document.getElementById(editor_name + 'editortype');
            editor_type_field.value = 'ckeditor';
            var writer = oEditor.dataProcessor.writer;
            writer.indentationChars = ''; /*Do not indent source code with tabs*/
            oEditor.resetDirty();
            /* Workaround: http://dev.ckeditor.com/ticket/3674 */
             evt.editor.on( 'contentDom', function( ev )
             {
             ev.removeListener();
             evt.editor.resetDirty();
             } );
            /* End workaround */
          })

        //]]></script>
        ''' % \
          {'textual_content': cgi.escape(textual_content),
           'html_content': content,
           'width': width,
           'height': height,
           'name': name,
           'id': id or name,
           'custom_configurations_path': custom_configurations_path,
           'toolbar': toolbar_set,
           'file_upload_script': file_upload_script,
           'CFG_SITE_URL': CFG_SITE_URL,
           'ln': ln}

    else:
        # CKedior is not installed
        textarea = '<textarea rows="100" cols="80" %(id)s name="%(name)s" style="width:%(width)s;height:%(height)s">%(content)s</textarea>' \
                     % {'content': cgi.escape(textual_content),
                        'width': width,
                        'height': height,
                        'name': name,
                        'id': id and ('id="%s"' % id) or ''}
        editor += textarea
        editor += '<input type="hidden" name="editor_type" value="textarea" />'

    return editor

def remove_html_markup(text, replacechar=' ', remove_escaped_chars_p=True):
    """
    Remove HTML markup from text.

    @param text: Input text.
    @type text: string.
    @param replacechar: By which character should we replace HTML markup.
        Usually, a single space or an empty string are nice values.
    @type replacechar: string
    @param remove_escaped_chars_p: If True, also remove escaped characters
        like '&amp;', '&lt;', '&gt;' and '&quot;'.
    @type remove_escaped_chars_p: boolean
    @return: Input text with HTML markup removed.
    @rtype: string
    """
    if not remove_escaped_chars_p:
        return RE_HTML_WITHOUT_ESCAPED_CHARS.sub(replacechar, text)
    return RE_HTML.sub(replacechar, text)

def unescape(s, quote=False):
    """
    The opposite of the cgi.escape function.
    Replace escaped characters '&amp;', '&lt;' and '&gt;' with the corresponding
    regular characters. If the optional flag quote is true, the escaped quotation
    mark character ('&quot;') is also translated.
    """
    s = s.replace('&lt;', '<')
    s = s.replace('&gt;', '>')
    if quote:
        s = s.replace('&quot;', '"')
    s = s.replace('&amp;', '&')
    return s


class EscapedString(str):
    """
    This class is a stub used by the MLClass machinery in order
    to distinguish native string, from string that don't need to be
    escaped.
    """
    pass

class EscapedHTMLString(EscapedString):
    """
    This class automatically escape a non-escaped string used to initialize
    it, using the HTML escaping method (i.e. cgi.escape).
    """
    def __new__(cls, original_string='', escape_quotes=False):
        if isinstance(original_string, EscapedString):
            escaped_string = str(original_string)
        else:
            if original_string and not str(original_string).strip():
                escaped_string = '&nbsp;'
            else:
                escaped_string = cgi.escape(str(original_string), escape_quotes)
        obj = str.__new__(cls, escaped_string)
        obj.original_string = original_string
        obj.escape_quotes = escape_quotes
        return obj

    def __repr__(self):
        return 'EscapedHTMLString(%s, %s)' % (repr(self.original_string), repr(self.escape_quotes))

    def __add__(self, rhs):
        return EscapedHTMLString(EscapedString(str(self) + str(rhs)))

class EscapedXMLString(EscapedString):
    """
    This class automatically escape a non-escaped string used to initialize
    it, using the XML escaping method (i.e. encode_for_xml).
    """
    def __new__(cls, original_string='', escape_quotes=False):
        if isinstance(original_string, EscapedString):
            escaped_string = str(original_string)
        else:
            if original_string and not str(original_string).strip():
                escaped_string = '&nbsp;'
            else:
                escaped_string = encode_for_xml(str(original_string), wash=True, quote=escape_quotes)
        obj = str.__new__(cls, escaped_string)
        obj.original_string = original_string
        obj.escape_quotes = escape_quotes
        return obj

    def __repr__(self):
        return 'EscapedXMLString(%s, %s)' % (repr(self.original_string), repr(self.escape_quotes))

    def __add__(self, rhs):
        return EscapedXMLString(EscapedString(str(self) + str(rhs)))

def create_tag(tag, escaper=EscapedHTMLString, opening_only=False, body=None, escape_body=False, escape_attr=True, indent=0, attrs=None, **other_attrs):
    """
    Create an XML/HTML tag.

    This function create a full XML/HTML tag, putting toghether an
    optional inner body and a dictionary of attributes.

        >>> print create_html_tag ("select", create_html_tag("h1",
        ... "hello", other_attrs={'class': "foo"}))
        <select>
          <h1 class="foo">
            hello
          </h1>
        </select>

    @param tag: the tag (e.g. "select", "body", "h1"...).
    @type tag: string
    @param body: some text/HTML to put in the body of the tag (this
        body will be indented WRT the tag).
    @type body: string
    @param escape_body: wether the body (if any) must be escaped.
    @type escape_body: boolean
    @param escape_attr: wether the attribute values (if any) must be
        escaped.
    @type escape_attr: boolean
    @param indent: number of level of indentation for the tag.
    @type indent: integer
    @param attrs: map of attributes to add to the tag.
    @type attrs: dict
    @return: the HTML tag.
    @rtype: string
    """

    if attrs is None:
        attrs = {}
    for key, value in other_attrs.iteritems():
        if value is not None:
            if key.endswith('_'):
                attrs[key[:-1]] = value
            else:
                attrs[key] = value
    out = "<%s" % tag
    for key, value in attrs.iteritems():
        if escape_attr:
            value = escaper(value, escape_quotes=True)
        out += ' %s="%s"' % (key, value)
    if body is not None:
        if callable(body) and body.__name__ == 'handle_body':
            body = body()
        out += ">"
        if escape_body and not isinstance(body, EscapedString):
            body = escaper(body)
        out += body
        if not opening_only:
            out += "</%s>" % tag
    elif not opening_only:
        out += " />"
    if indent:
        out = indent_text(out, indent)[:-1]
    return EscapedString(out)

class MLClass(object):
    """
    Swiss army knife to generate XML or HTML strings a la carte.

    >>> from invenio.htmlutils import X, H
    >>> X.foo()()
    ... '<foo />'
    >>> X.foo(bar='baz')()
    ... '<foo bar="baz" />'
    >>> X.foo(bar='baz&pi')()
    ... '<foo bar="baz&amp;pi" />'
    >>> X.foo("<body />", bar='baz')
    ... '<foo bar="baz"><body /></foo>'
    >>> X.foo(bar='baz')(X.body())
    ... '<foo bar="baz"><body /></foo>'
    >>> X.foo(bar='baz')("<body />") ## automatic escaping
    ... '<foo bar="baz">&lt;body /></foo>'
    >>> X.foo()(X.p(), X.p()) ## magic concatenation
    ... '<foo><p /><p /></foo>'
    >>> X.foo(class_='bar')() ## protected keywords...
    ... '<foo class="bar" />'
    >>> X["xml-bar"]()()
    ... '<xml-bar />'
    """

    def __init__(self, escaper):
        self.escaper = escaper

    def __getattr__(self, tag):
        def tag_creator(body=None, opening_only=False, escape_body=False, escape_attr=True, indent=0, attrs=None, **other_attrs):
            if body:
                return create_tag(tag, body=body, opening_only=opening_only, escape_body=escape_body, escape_attr=escape_attr, indent=indent, attrs=attrs, **other_attrs)
            else:
                def handle_body(*other_bodies):
                    full_body = None
                    if other_bodies:
                        full_body = ""
                        for body in other_bodies:
                            if callable(body) and body.__name__ == 'handle_body':
                                full_body += body()
                            elif isinstance(body, EscapedString):
                                full_body += body
                            else:
                                full_body += self.escaper(str(body))
                    return create_tag(tag, body=full_body, opening_only=opening_only, escape_body=escape_body, escape_attr=escape_attr, indent=indent, attrs=attrs, **other_attrs)
                return handle_body
        return tag_creator

    __getitem__ = __getattr__


H = MLClass(EscapedHTMLString)
X = MLClass(EscapedXMLString)

def create_html_select(options, name=None, selected=None, disabled=None, multiple=False, attrs=None, **other_attrs):
    """
    Create an HTML select box.

        >>> print create_html_select(["foo", "bar"], selected="bar", name="baz")
        <select name="baz">
          <option selected="selected" value="bar">
            bar
          </option>
          <option value="foo">
            foo
          </option>
        </select>
        >>> print create_html_select([("foo", "oof"), ("bar", "rab")], selected="bar", name="baz")
        <select name="baz">
          <option value="foo">
            oof
          </option>
          <option selected="selected" value="bar">
            rab
          </option>
        </select>

    @param options: this can either be a sequence of strings, or a sequence
        of couples or a map of C{key->value}. In the former case, the C{select}
        tag will contain a list of C{option} tags (in alphabetical order),
        where the C{value} attribute is not specified. In the latter case,
        the C{value} attribute will be set to the C{key}, while the body
        of the C{option} will be set to C{value}.
    @type options: sequence or map
    @param name: the name of the form element.
    @type name: string
    @param selected: optional key(s)/value(s) to select by default. In case
        a map has been used for options.
    @type selected: string (or list of string)
    @param disabled: optional key(s)/value(s) to disable.
    @type disabled: string (or list of string)
    @param multiple: whether a multiple select box must be created.
    @type mutable: bool
    @param attrs: optional attributes to create the select tag.
    @type attrs: dict
    @param other_attrs: other optional attributes.
    @return: the HTML output.
    @rtype: string

    @note: the values and keys will be escaped for HTML.

    @note: it is important that parameter C{value} is always
        specified, in case some browser plugin play with the
        markup, for eg. when translating the page.
    """
    body = []
    if selected is None:
        selected = []
    elif isinstance(selected, (str, unicode)):
        selected = [selected]
    if disabled is None:
        disabled = []
    elif isinstance(disabled, (str, unicode)):
        disabled = [disabled]
    if name is not None and multiple and not name.endswith('[]'):
        name += "[]"
    if isinstance(options, dict):
        items = options.items()
        items.sort(lambda item1, item2: cmp(item1[1], item2[1]))
    elif isinstance(options, (list, tuple)):
        options = list(options)
        items = []
        for item in options:
            if isinstance(item, (str, unicode)):
                items.append((item, item))
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                items.append(tuple(item))
            else:
                raise ValueError('Item "%s" of incompatible type: %s' % (item, type(item)))
    else:
        raise ValueError('Options of incompatible type: %s' % type(options))
    for key, value in items:
        option_attrs = {}
        if key in selected:
            option_attrs['selected'] = 'selected'
        if key in disabled:
            option_attrs['disabled'] = 'disabled'
        body.append(create_tag("option", body=value, escape_body=True, value=key, attrs=option_attrs))
    if attrs is None:
        attrs = {}
    if name is not None:
        attrs['name'] = name
    if multiple:
        attrs['multiple'] = 'multiple'
    return create_tag("select", body='\n'.join(body), attrs=attrs, **other_attrs)

class _LinkGetter(HTMLParser):
    """
    Hidden class that, by deriving from HTMLParser, will intercept all
    <a> tags and retrieve the corresponding href attribute.
    All URLs are available in the urls attribute of the class.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for (name, value) in attrs:
                if name == 'href':
                    self.urls.add(value)

def get_links_in_html_page(html):
    """
    @param html: the HTML text to parse
    @type html: str
    @return: the list of URLs that were referenced via <a> tags.
    @rtype: set of str
    """
    parser = _LinkGetter()
    parser.feed(html)
    return parser.urls


def transform_links(data):
    """
    Create html links from possible_urls in input string
    @param data: input string where links have to be transformed
    @type data: str
    """
    possible_urls = re.findall(r'(https?://[\w\d:#%/;$()~_?\-=\\\.&]*)', data)
    # validate possible urls
    # we'll transform them just in case
    # they are valid.
    result = ""
    if possible_urls:
        for url in possible_urls:
            if regex_url.search(url):
                transformed_url = '<a href="%s">%s</a>' % (url, url)
                data = data.replace(url, transformed_url)
        result += data
    else:
        result = data
    return result
