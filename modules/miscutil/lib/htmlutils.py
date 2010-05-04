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
from invenio.textutils import indent_text
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
                                         'ul', 'ol', 'li', 'sub', 'sup', 'div', 'strike')
# List of allowed attributes. Be cautious, some attributes may be risky:
# <p style="background: url(myxss_suite.js)">
cfg_html_buffer_allowed_attribute_whitelist = ('href', 'name', 'class')

## precompile some often-used regexp for speed reasons:
re_html = re.compile("(?s)<[^>]*>|&#?\w+;")

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
        @param render_unallowed_tags: if True, print unallowed tags escaping
            < and >.  Else, only print content of unallowed tags.
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
            elif tag == 'style' or tag == 'script':
                # In that case we want to remove content too
                self.silent = True

    def handle_data(self, data):
        """Function called for text nodes"""
        if not self.silent:
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

def get_html_text_editor(name, id=None, content='', textual_content=None, width='300px', height='200px',
                         enabled=True, file_upload_url=None, toolbar_set="Basic",
                         custom_configurations_path='/fckeditor/invenio-fckeditor-config.js'):
    """
    Returns a wysiwyg editor (FCKeditor) to embed in html pages.

    Fall back to a simple textarea when the library is not installed,
    or when the user's browser is not compatible with the editor, or
    when 'enable' is False, or when javascript is not enabled.

    NOTE that the output also contains a hidden field named
    'editor_type' that contains the kind of editor used, 'textarea' or
    'fckeditor'.

    Based on 'editor_type' you might want to take different actions,
    like replace CRLF with <br/> when editor_type equals to
    'textarea', but not when editor_type equals to 'fckeditor'.

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
        use. FCKeditor comes by default with 'Basic' and
        'Default'. To define other sets, customize the
        config file in
        /opt/cds-invenio/var/www/fckeditor/invenio-fckconfig.js

    @param custom_configurations_path: *str* value for the FCKeditor config
        variable 'CustomConfigurationsPath',
        which allows to specify the path of a
        file that contains a custom configuration
        for the editor. The path is relative to
        /opt/cds-invenio/var/www/

    @return: the HTML markup of the editor
    """
    if textual_content is None:
        textual_content = content

    editor = ''

    if enabled and fckeditor_available:
        # Prepare upload path settings
        if file_upload_url is not None:
            file_upload_script = '''
            oFCKeditor.Config["LinkUploadURL"] = '%(file_upload_url)s';
            oFCKeditor.Config["ImageUploadURL"] = '%(file_upload_url)s%%3Ftype%%3DImage';
            oFCKeditor.Config["FlashUploadURL"] = '%(file_upload_url)s%%3Ftype%%3DFlash';
            oFCKeditor.Config["MediaUploadURL"] = '%(file_upload_url)s%%3Ftype%%3DMedia';
            oFCKeditor.Config["LinkUpload"] = true;
            oFCKeditor.Config["ImageUpload"] = true;
            oFCKeditor.Config["FlashUpload"] = true;
            ''' % {'file_upload_url': file_upload_url}
        else:
            file_upload_script = '''
            oFCKeditor.Config["LinkUpload"] = false;
            oFCKeditor.Config["ImageUpload"] = false;
            oFCKeditor.Config["FlashUpload"] = false;
            '''

        # Prepare code to instantiate an editor
        editor += '''
        <script type="text/javascript" src="%(CFG_SITE_URL)s/fckeditor/fckeditor.js"></script>
        <input type="hidden" name="editor_type" id="%(name)seditortype" value="textarea" />
        <textarea id="%(id)s" name="%(name)s" style="width:%(width)s;height:%(height)s">%(textual_content)s</textarea>
        <textarea id="%(id)shtmlvalue" name="%(name)shtmlvalue" style="display:None;width:%(width)s;height:%(height)s">%(html_content)s</textarea>
        <script type="text/javascript">
          var oFCKeditor = new FCKeditor('%(name)s', '%(width)s', '%(height)s', '%(toolbar)s') ;
          oFCKeditor.BasePath = "/fckeditor/" ;
          oFCKeditor.Config["CustomConfigurationsPath"] = '%(custom_configurations_path)s';
          /* Set paths to upload files */
          %(file_upload_script)s
          /* Disable browsing on the server, which would not work anyway */
          oFCKeditor.Config["LinkBrowser"] = false;
          oFCKeditor.Config["ImageBrowser"] = false;
          oFCKeditor.Config["FlashBrowser"] = false;

          oFCKeditor.ReplaceTextarea() ;

          function FCKeditor_OnComplete( editorInstance )
          {
            /* If FCKeditor was correctly loaded, display the nice HTML representation */
            var oEditor = FCKeditorAPI.GetInstance('%(name)s');
            var html_editor = document.getElementById('%(id)shtmlvalue');
            oEditor.SetHTML(html_editor.value);
            var editor_type_field = document.getElementById('%(name)seditortype');
            editor_type_field.value = 'fckeditor';
          }

        </script>
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
           'CFG_SITE_URL': CFG_SITE_URL}

    else:
        # FCKedior is not installed
        textarea = '<textarea %(id)s name="%(name)s" style="width:%(width)s;height:%(height)s">%(content)s</textarea>' \
                     % {'content': cgi.escape(textual_content),
                        'width': width,
                        'height': height,
                        'name': name,
                        'id': id and ('id="%s"' % id) or ''}
        editor += textarea
        editor += '<input type="hidden" name="editor_type" value="textarea" />'

    return editor

def remove_html_markup(text, replacechar=' '):
    """
    Remove HTML markup from text.

    @param text: Input text.
    @type text: string.
    @param replacechar: By which character should we replace HTML markup.
        Usually, a single space or an empty string are nice values.
    @type replacechar: string
    @return: Input text with HTML markup removed.
    @rtype: string
    """
    return re_html.sub(replacechar, text)

def create_html_tag(tag, body=None, escape_body=False, escape_attr=True, indent=0, attrs=None, **other_attrs):
    """
    Create an HTML tag.

    This function create a full HTML tag, putting toghether an
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
    attrs.update(other_attrs)
    out = "<%s" % tag
    for key, value in attrs.iteritems():
        if escape_attr:
            value = escape_html(value, escape_quotes=True)
        out += ' %s="%s"' % (key, value)
    if body:
        out += ">\n"
        if escape_body:
            body = escape_html(body)
        out += indent_text(body, 1)
        out += "</%s>" % tag
    else:
        out += " />"
    out = indent_text(out, indent)
    out = out[:-1] # Let's remove trailing new line
    return out

def create_html_select(options, selected=None, attrs=None, **other_attrs):
    """
    Create an HTML select box.

        >>> print create_html_select(["foo", "bar"], selected="bar", name="baz")
        <select name="baz">
          <option selected="selected">
            bar
          </option>
          <option>
            foo
          </option>
        </select>
        >>> print create_html_select({"foo": "oof", "bar": "rab"}, selected="bar", name="baz")
        <select name="baz">
          <option value="foo">
            oof
          </option>
          <option selected="selected" value="bar">
            rab
          </option>
        </select>

    @param options: this can either be a sequence of strings or a map of
        C{key->value}. In the former case, the C{select} tag will contain
        a list of C{option} tags (in alphabetical order), where the
        C{value} attribute is not specified. In the latter case, the
        C{value} attribute will be set to the C{key}, while the body
        of the C{option} will be set to C{value}.
    @type options: sequence or map
    @param selected: optional key/value to select by default. In case
        a map has been used for options, C{selected} must be set to an
        existing C{key}, otherwise it must be set to an existing
        C{value}.
    @type selected: string
    @param attrs: optional attributes to create the select tag.
    @type attrs: dict
    @param other_attrs: other optional attributes.
    @return: the HTML output.
    @rtype: string

    @note: the values and keys will be escaped for HTML.
    """
    body = []
    try:
        items = options.items()
        items.sort(lambda item1, item2: cmp(item1[1], item2[1]))
        for key, value in items:
            option_attrs = key == selected and {"selected": "selected"} or {}
            body.append(create_html_tag("option", body=value, escape_body=True, value=key, attrs=option_attrs))
    except AttributeError:
        options.sort()
        for value in options:
            option_attrs = value == selected and {"selected": "selected"} or {}
            body.append(create_html_tag("option", body=value, escape_body=True, attrs=option_attrs))
    return create_html_tag("select", body='\n'.join(body), attrs=attrs, **other_attrs)

