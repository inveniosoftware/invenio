# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2014 CERN.
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

__revision__ = "$Id$"

"""Template for the bibclassify -
this modules is NOT standalone safe - it is not expected to be
used in a stanalone mode ever.

Some template variables are coming directly from the config
module, those starting with CFG_BIBCLASSIFY_WEB....
"""

import cgi
from invenio import config
from invenio.base.i18n import gettext_set_language
from urllib import quote
from invenio.utils.html import escape_html
import config as bconfig

log = bconfig.get_logger("bibclassify.template")


class Template:
    def tmpl_page(self,
                  keywords=None,
                  top='',
                  middle='',
                  bottom='',
                  navbar=None,
                  req=None,
                  ln=None,
                  generate=None,
                  sorting=None,
                  type=None,
                  numbering=None,
                  showall=None):
        """This function generates the final output for every bibclassify page - it is called
        from the other templating functions to finalize the output. This way, all the logic
        about routing (which page to display) will rest with the webinterface, and templates
        care only for output.
        @keyword keywords: keywords to display
        @keyword top: string, what to put at top
        @keyword middle: string
        @keyword bottom: string
        @keyword navbar: if supplied, we will not add the generic navigation bar
        @keyword req: wsgi req object
        -- all the rest keyword parameters are common with the tmp_page_... calls
        @return: html string
        """

        if navbar is None:
            navbar = self.tmpl_snippet_sorting_options(keywords,
                                                       ln=ln,
                                                       generate=generate,
                                                       sorting=sorting,
                                                       type=type,
                                                       numbering=numbering,
                                                       showall=showall)


        # well, integration with other moduels needs to get better (but for now this will do)
        bottom += self.call_external_modules(keywords=keywords,
                                             req=req,
                                             ln=ln,
                                             generate=generate,
                                             sorting=sorting,
                                             type=type,
                                             numbering=numbering,
                                             showall=showall)
        #thread_id, cache = reader.test_cache()
        #bottom += 'This is thread id: %s, cache id: %s, main cache: %s' % (thread_id, id(cache), id(reader._CACHE))

        top = top and '<div class="bibclassify-top"> %s </div>' % top or ''

        return '''
        <div class="bibclassify">
            <div class="bibclassify-nav"> %s </div>
            %s
            %s
            <div class="bibclassify-bottom"> %s </div>
        </div>''' % (navbar, top, middle, bottom)


    def tmpl_page_msg(self, req=None, ln=None, msg=None):
        return self.tmpl_page(middle=msg)

    def tmpl_page_tagcloud(self, keywords,
                           req=None,
                           ln=None,
                           generate=None,
                           sorting=None,
                           type=None,
                           numbering=None,
                           showall=None):
        """Writes the html of the tag cloud
        @var keywords: dictionary of KeywordToken objects
            key is a KeywordToken object
            value is a list: [[(pos1,pos1), (pos2,pos2)..], font-level]
        @return: str, html page
        """


        # Define the range of fonts.
        f_min = 12
        f_increment = 3
        f_number = 8
        fonts = [f_min + i * f_increment for i in range(f_number)]
        # compute font levels
        _get_font_levels(keywords, no_steps=f_number)
        _ = gettext_set_language(ln)

        msg = _("Automatically generated <span class=\"keyword single\">single</span>,\
        <span class=\"keyword composite\">composite</span>, <span class=\"keyword author-kw\">author</span>,\
        and <span class=\"keyword other-kw\">other keywords</span>.")

        cloud = []

        cloud.append('<div class="tagcloud" levels="%s">' % (' '.join(map(lambda x: '%spx' % x, fonts))))

        format_link = self.tmpl_href
        max = config.CFG_BIBCLASSIFY_WEB_MAXKW or 1000
        i = 0

        if numbering == 'on':
            for kw, info in keywords.items()[0:max]:
                cloud.append('<span style="font-size: %spx;">%s&nbsp;(%s)</span>' %
                             (fonts[info[-1]],
                              format_link(kw, ln),
                              len(info[0])))
        else:
            for kw, info in keywords.items()[0:max]:
                cloud.append('<span style="font-size: %spx;">%s&nbsp;</span>' %
                             (fonts[info[-1]],
                              format_link(kw, ln)))

        cloud.append('</div>')

        cloud = '''
            <div class="cloud">
              %s
            </div>''' % ('\n'.join(cloud))
        return self.tmpl_page(keywords=keywords, bottom=msg, middle=cloud,
                              req=req,
                              ln=ln,
                              generate=generate,
                              sorting=sorting,
                              type=type,
                              numbering=numbering,
                              showall=showall)


    def tmpl_page_list(self, keywords,
                       req=None,
                       ln=None,
                       generate=None,
                       sorting=None,
                       type=None,
                       numbering=None,
                       showall=None):
        """Page with keywords as a list"""
        _ = gettext_set_language(ln)
        kw = self.tmpl_list_of_keywords(keywords,
                                        ln=ln,
                                        generate=generate,
                                        sorting=sorting,
                                        type=type,
                                        numbering=numbering,
                                        showall=showall)
        msg = _(_("Automatically generated <span class=\"keyword single\">single</span>,\
        <span class=\"keyword composite\">composite</span>, <span class=\"keyword author-kw\">author</span>,\
        and <span class=\"keyword other-kw\">other keywords</span>."))
        return self.tmpl_page(keywords=keywords, middle=kw, bottom=msg,
                              req=req,
                              ln=ln,
                              generate=generate,
                              sorting=sorting,
                              type=type,
                              numbering=numbering,
                              showall=showall)

    def tmpl_page_xml_output(self, keywords, xml=None,
                             req=None,
                             ln=None,
                             generate=None,
                             sorting=None,
                             type=None,
                             numbering=None,
                             showall=None):
        kw = '<pre class="bibclassify-marcxml"><code>%s</code></pre>' % escape_html(xml)
        return self.tmpl_page(keywords, middle=kw,
                              ln=ln,
                              generate=generate,
                              sorting=sorting,
                              type=type,
                              numbering=numbering,
                              showall=showall)

    def tmpl_page_generate_keywords(self,
                                    req=None,
                                    ln=None,
                                    generate=None,
                                    sorting=None,
                                    type=None,
                                    numbering=None,
                                    showall=None):
        """ Text to return when no keywords are found"""

        _ = gettext_set_language(ln)

        msg = '''
            <form action="" method="get">
              %s
              <input type="hidden" name="generate" value="yes">
              <input type="submit" value="%s">
            </form>''' % (_('Automated keyword extraction wasn\'t run for this document yet.'), _('Generate keywords') )
        return self.tmpl_page(top=msg,
                              ln=ln,
                              generate=generate,
                              sorting=sorting,
                              type=type,
                              numbering=numbering,
                              showall=showall)


    def tmpl_page_no_keywords(self, ln=None, generate=None, sorting=None, type=None, numbering=None, showall=None):
        _ = gettext_set_language(ln)
        return self.tmpl_page(top=_('There are no suitable keywords for display in this record.'),
                              navbar='',
                              ln=ln,
                              generate=generate,
                              sorting=sorting,
                              type=type,
                              numbering=numbering,
                              showall=showall)


    def tmpl_list_of_keywords(self, keywords,
                              ln=None,
                              generate=None,
                              sorting=None,
                              type=None,
                              numbering=None,
                              showall=None):
        """Formats the list of keywords - no distinction is made
        between weighted or not """

        _ = gettext_set_language(ln)
        format_link = self.tmpl_href

        s_keywords = map(lambda x: (x[0], 1000 - len(x[1][0]), len(x[1][0])), keywords.items())
        # need to sort by heights weight (reverse) and then alphabetically
        # that's why the substraction above
        s_keywords.sort(key=lambda x: (x[1], str(x[0])), reverse=False)

        if showall != 'on':
            s_keywords = s_keywords[0:config.CFG_BIBCLASSIFY_WEB_MAXKW]

        out = []

        if numbering == 'on':
            for kw, weight, real_weight in s_keywords[0:config.CFG_BIBCLASSIFY_WEB_MAXKW]:
                out.append('%s (%s)' % (format_link(kw, ln), real_weight))
        else:
            for kw, weight, real_weight in s_keywords[0:config.CFG_BIBCLASSIFY_WEB_MAXKW]:
                out.append(format_link(kw, ln))

        if len(keywords) > len(s_keywords):
            out.append('<a href="%s" class="moreinfo %s">%s</a>' %
                       ('?ln=%s&type=list&sorting=%s&showall=on' % (ln, sorting),
                        'show-more',
                        _("Show more...")))

        half = int(len(out) / 2)
        out = '<div class="kw-list">%s</div><div class="kw-list">%s</div>' % (
            '<br/>'.join(out[0:half]), '<br/>'.join(out[half:]))

        return '''
        <div class="bibclassify-kwlist">
          %s
        <hr />
        </div>''' % (out)


    def tmpl_format_list_of_keywords(self, keywords,
                                     ln=None,
                                     generate=None,
                                     sorting=None,
                                     type=None,
                                     numbering=None,
                                     showall=None):
        """Formats the list of keywords"""

        _ = gettext_set_language(ln)
        format_link = self.tmpl_href

        sorted_keywords = _get_sorted_keywords(keywords)

        _numbering = numbering is 'on'
        out = []
        for type in ('composite', 'single'):
            if sorted_keywords['unweighted'][type]:
                out.append('<b>%s</b>' % _('Unweighted %(x_name)s keywords:', x_name=type))
                for keyword, info in sorted_keywords['unweighted'][type]:
                    out.append(format_link(keyword, ln))

        for type in ('composite', 'single'):
            if sorted_keywords['weighted'][type]:
                out.append('<b>%s</b>' % _('Weighted %(x_name)s keywords:', x_name=type))
                for keyword, info in sorted_keywords['weighted'][type]:
                    if _numbering:
                        out.append("%s (%d)" % (format_link(keyword, ln), len(info[0])))
                    else:
                        out.append(format_link(keyword, ln))

        return '''
        <div class="cloud">
          %s
        </div>''' % ('<br/>'.join(out))

    def tmpl_search_link(self, keyword, ln):
        """Returns a link that searches for a keyword."""
        return """%s/search?f=keyword&amp;p=%s&amp;ln=%s""" % (
            config.CFG_SITE_URL,
            quote('"%s"' % keyword),
            ln)

    def tmpl_href(self, keyword, ln):
        return '<a href="%s" class="keyword %s %s">%s</a>' % (
            self.tmpl_search_link(keyword, ln), keyword.getType(), keyword.isComposite() and 'composite' or 'single',
            cgi.escape(str(keyword)))


    def tmpl_snippet_sorting_options(self, keywords,
                                     ln=None,
                                     generate=None,
                                     sorting=None,
                                     type=None,
                                     numbering=None,
                                     showall=None
    ):
        """Returns the HTML view of the sorting options. Takes care of
        enabling only some options based on the page shown."""

        if not keywords:
            return ''

        _ = gettext_set_language(ln)

        out = '<b>%s:</b>\n' % _('Keywords')

        for (_type, label) in ( ('tagcloud', _('tag cloud')),
                                ('list', _('list')),
                                ('xml', _('XML')) ):
            k = {'langlink': ln, 'type': _type, 'sorting': sorting, 'label': _(label)}
            if _type not in type:
                out += '[ <a href="?ln=%(langlink)s&type=%(type)s&sorting=%(sorting)s">%(label)s</a> ]' % k
            else:
                out += '[ %(label)s ]' % k

        out += '\n<br/>\n'
        """
        out += '<b>Sort keywords:</b>\n'

        for (sort_type, label) in ( ('occurences', 'by occurences'),
                               ('related', 'by related documents'),):
            k = {'langlink' : ln, 'type': type_arg, 'sort' : sort_type, 'label' : _(label)}
            if sort_type not in sort_arg:
                out += '[ <a href="?ln=%(langlink)s&type=%(type)s&sort=%(sort)s">%(label)s</a> ]' % k
            else:
                out += '[ %(label)s ]' % k
        """

        return ('''<div class="nav-links">
        %s
        </div>''' % out)

    def call_external_modules(self, **kwargs):
        """Give external modules chance to change bibclassify output
        - so far, there is no clear way how to discover modules etc.
        It is hardcoded now."""

        _modules = bconfig.CFG_EXTERNAL_MODULES
        out = ''
        for m, v in _modules.items():
            try:
                if not callable(v):
                    x = __import__(m, globals=globals(), locals={})
                    if hasattr(x, v):
                        v = getattr(x, v)
                        _modules[m] = v
                    else:
                        raise Exception("The registered call %s does not exist in the module %s" % (v, m))
                result = v('bibclassify', **kwargs)
                if result and isinstance(result, str):
                    out += result
                else:
                    log.error("Module %s returned wrong results? %s" % (m, str(result)[:50]))
            except Exception as msg:
                log.error("Error importing module: %s" % (m))
                log.error(msg)
                del (_modules[m])
        return out


def _get_sorted_keywords(keywords):
    """Returns a list of keywords."""
    # Separate keywords with and without weight, and single and
    # composite keywords.
    sorted_keywords = {
        'unweighted': {'single': [], 'composite': []},
        'weighted': {'single': [], 'composite': []}
    }

    for k, info in keywords.items():
        if len(info[0]) > 0:
            state = 'weighted'
        else:
            state = 'unweighted'
        if k.isComposite():
            sorted_keywords[state]['composite'].append([k, info])
        else:
            sorted_keywords[state]['single'].append([k, info])

    for type in ('single', 'composite'):
        sorted_keywords['unweighted'][type].sort(key=lambda x: str(x[0]).lower()) #keyword label
        sorted_keywords['weighted'][type].sort(key=lambda x: len(x[1][0])) # number of spans

    return sorted_keywords


def _get_font_levels(keywords, no_steps=8):
    """Takes keywords dictionary {keyw1: [[], ]....}
     computes the fontlevel and adds it to the dictionary
     @return: nothing, it changes keywords dictionary directly"""

    if not keywords:
        return keywords

    # Extract the weights from the keywords.
    try:
        weights = map(lambda x: len(x[0]), keywords.values())
    except IndexError:
        return keywords

    # Define the range of fonts.
    f_number = no_steps

    # Get some necessary values.
    w_min = float(min(weights))
    w_max = float(max(weights))

    # Compute the distribution function.
    if w_max == w_min:
        level = lambda weight: 1
    else:
        slope = f_number / (w_max - w_min)
        y_intercept = - w_min * slope
        level = lambda weight: int(slope * weight + y_intercept)

    # Compute the font level for each weight.
    for keyword, info in keywords.items():
        w = level(len(info[0]))
        if w >= f_number:
            w = f_number - 1
        info.append(w)
