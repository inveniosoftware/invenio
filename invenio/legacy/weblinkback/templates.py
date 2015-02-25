# -*- coding: utf-8 -*-
# Comments and reviews for records.

# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""WebLinkback - Web Templates"""

from invenio.legacy.weblinkback.db_layer import get_all_linkbacks, \
                                        get_url_title
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_LATEST_COUNT_VALUES, \
                                       CFG_WEBLINKBACK_ACTION_RETURN_CODE
from invenio.legacy.weblinkback.api import generate_redirect_url
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import convert_datetext_to_dategui
from invenio.config import CFG_SITE_RECORD, \
                           CFG_SITE_URL, \
                           CFG_WEBCOMMENT_USE_MATHJAX_IN_COMMENTS
from invenio.utils.html import get_mathjax_header
from invenio.modules.formatter import format_record

import cgi


class Template:

    def tmpl_linkbacks_general(self, recid, ln):
        """
        Display general linkback information
        """
        _ = gettext_set_language(ln)

        url = get_trackback_url(recid)
        out = '<h4>'
        out += _("Trackback URL: ")
        out += '<a href="%s" onclick="return false" rel="nofollow">%s</a>' % (url, url)
        out += '</h4>'
        out += '<div class="comment-subscribe">Trackbacks are used in blog systems to refer to external content. Please copy and paste this trackback URL to the appropriate field of your blog post if you want to refer to this record.</div>'
        out += '<br/>'

        return out

    def tmpl_linkbacks(self, approved_linkbacks, ln):
        """
        Display the approved linkbacks of a record
        @param approved_linkbacks: approved linkbacks to display
        """
        _ = gettext_set_language(ln)

        out = self.tmpl_linkbacks_count(approved_linkbacks, ln)

        if approved_linkbacks:
            out += self.tmpl_linkback_tuple(approved_linkbacks, ln)

        return out

    def tmpl_linkbacks_admin(self, pending_linkbacks, recid, ln):
        """
        Display the pending linkbacks of a record and admin approve/reject features
        @param pending_linkbacks: pending linkbacks
        """
        _ = gettext_set_language(ln)
        out = ''

        out += self.tmpl_linkbacks_count(pending_linkbacks, ln, _('to review'))
        out += self.tmpl_linkback_tuple_admin(url_approve_prefix=generate_redirect_url(recid, ln, 'approve'),
                                                  url_reject_prefix=generate_redirect_url(recid, ln, 'reject'),
                                                  linkbacks=pending_linkbacks,
                                                  ln=ln)

        return out

    def tmpl_linkbacks_count(self, linkbacks, ln, additional_text = ''):
        """
        Display the count of linkbacks plus an additional text in a grey field
        @param linkbacks: collection of linkbacks
        @param additional_text: additional text to be display
        """
        _ = gettext_set_language(ln)

        middle_text = ""
        if additional_text != "":
            middle_text = " " + additional_text
        return self.tmpl_heading(cgi.escape(_('Linkbacks%(x_name)s: %(x_num)s', x_name=middle_text, x_num=len(linkbacks))))

    def tmpl_heading(self, text):
        """
        Display a text in a grey field
        @param text: text
        """
        return '''
            <table><tr>
             <td>
              <table><tr><td class="blocknote">%s</td></tr></table>
             </td>
            </tr></table>
            ''' % text

    def tmpl_linkback_tuple(self, linkbacks, ln):
        """
        Display a linkback
        @param linkbacks: collection of linkbacks: [(linkback_id,
                                                     origin_url,
                                                     recid,
                                                     additional_properties,
                                                     type,
                                                     status,
                                                     insert_time)]
        """
        _ = gettext_set_language(ln)

        out = '<table width="95%" style="display: inline";>'

        for current_linkback in linkbacks:
            url = current_linkback[1]
            out += '''<tr><td><font class="rankscoreinfo"><a>(%(type)s)&nbsp;</a></font><small>&nbsp;<a href="%(origin_url)s" target="_blank">%(page_title)s</a>&nbsp;%(submit_date)s</small></td></tr>''' % {
                       'type': current_linkback[4],
                       'origin_url': cgi.escape(url),
                       'page_title': cgi.escape(get_url_title(url)),
                       'submit_date': '(submitted on <i>' + convert_datetext_to_dategui(str(current_linkback[6])) + '</i>)'}

        out += '</table>'
        return out

    def tmpl_linkback_tuple_admin(self, url_approve_prefix, url_reject_prefix, linkbacks, ln):
        """
        Display linkbacks with admin approve/reject features
        @param linkbacks: collection of linkbacks: [(linkback_id,
                                                     origin_url,
                                                     recid,
                                                     additional_properties,
                                                     type,
                                                     status,
                                                     insert_time)]
        """
        _ = gettext_set_language(ln)
        out = ''

        for current_linkback in linkbacks:
            linkbackid = current_linkback[0]
            url = current_linkback[1]

            out += '<div style="margin-bottom:20px;background:#F9F9F9;border:1px solid #DDD">'
            out += '<div style="background-color:#EEE;padding:2px;font-size:small">&nbsp;%s</div>' % (_('Submitted on') + ' <i>' + convert_datetext_to_dategui(str(current_linkback[6])) + '</i>:')
            out += '<br />'
            out += '<blockquote>'
            out += '''<font class="rankscoreinfo"><a>(%(type)s)&nbsp;</a></font><small>&nbsp;<a href="%(origin_url)s" target="_blank">%(page_title)s</a></small>''' % {
                       'type': current_linkback[4],
                       'origin_url': cgi.escape(url),
                       'page_title': cgi.escape(get_url_title(url))}
            out += '</blockquote>'
            out += '<br />'
            out += '<div style="float:right">'
            out += '<small>'
            out += '''<a style="color:#8B0000;" href="%s&linkbackid=%s">%s</a>''' % (url_approve_prefix, linkbackid, _("Approve"))
            out += '&nbsp;|&nbsp;'
            out += '''<a style="color:#8B0000;" href="%s&linkbackid=%s">%s</a>''' % (url_reject_prefix, linkbackid, _("Reject"))
            out += '</small>'
            out += '</div>'
            out += '</div>'

        return out

    def tmpl_get_mathjaxheader_jqueryheader(self):
        mathjaxheader = ''
        if CFG_WEBCOMMENT_USE_MATHJAX_IN_COMMENTS:
            mathjaxheader = get_mathjax_header()
        jqueryheader = '''
        <script src="%(CFG_SITE_URL)s/vendors/jquery/dist/jquery.min.js" type="text/javascript"></script>
        <script src="%(CFG_SITE_URL)s/vendors/jquery-multifile/jquery.MultiFile.pack.js" type="text/javascript"></script>
        ''' % {'CFG_SITE_URL': CFG_SITE_URL}
        return (mathjaxheader, jqueryheader)

    def tmpl_get_latest_linkbacks_top(self, current_value, ln):
        """
        Top elements to select the count of approved latest added linkbacks to display
        @param current_value: current value option will be selected if it exists
        """
        _ = gettext_set_language(ln)
        result = """<form action='linkbacks' style='form { display: inline; }'><b>%s</b>
                        <select name="rg" size="1">
                 """ % _("View last")

        for i in range(len(CFG_WEBLINKBACK_LATEST_COUNT_VALUES)):
            latest_count_string = str(CFG_WEBLINKBACK_LATEST_COUNT_VALUES[i])
            if CFG_WEBLINKBACK_LATEST_COUNT_VALUES[i] == current_value:
                result += '<option SELECTED>' + latest_count_string + '</option>'
            else:
                result += '<option value=' + latest_count_string + '>' + latest_count_string + '</option>'

        result += """   </select> <b>linkbacks</b>
                        <input type="submit" class="adminbutton" value="%s">
                    </form>
                  """ % _("Refresh")
        return result

    def tmpl_get_latest_linkbacks(self, latest_linkbacks, ln):
        """
        Display approved latest added linkbacks to display
        @param latest_linkbacks: a list of lists of linkbacks
        """
        result = ''

        for i in range(len(latest_linkbacks)):
            day_group = latest_linkbacks[i]

            date = day_group[0][6]
            date_day_month = convert_datetext_to_dategui(str(date))[:6]

            result += self.tmpl_heading(date_day_month)
            for j in range(len(day_group)):
                current_linkback = day_group[j]
                link_type = current_linkback[4]
                url = str(current_linkback[1])
                recordid = current_linkback[2]
                result += '<font class="rankscoreinfo"><a>(%s)&nbsp;</a></font>' % link_type
                result += '<small>'
                result += '<a href="%s">%s</a> links to ' % (cgi.escape(url), cgi.escape(get_url_title(url)))
                result += format_record(recID=recordid, of='hs', ln=ln)
                result += '</small>'
                result += '<br>'
            result += '<br>'
        return result

    def tmpl_admin_index(self, ln):
        """
        Index page of admin interface
        """
        _ = gettext_set_language(ln)

        out = '<ol>'

        pending_linkback_count = len(get_all_linkbacks(status=CFG_WEBLINKBACK_STATUS['PENDING']))
        stat_pending_text = ""
        if pending_linkback_count > 0:
            stat_pending_text = ' <span class="moreinfo"> ('
            if pending_linkback_count == 1:
                stat_pending_text += "%s pending linkback request" % pending_linkback_count
            elif pending_linkback_count > 1:
                stat_pending_text += "%s pending linkback requests"% pending_linkback_count
            stat_pending_text += ')</span>'
        out += '<li><a href="%(siteURL)s/admin/weblinkback/weblinkbackadmin.py/linkbacks?ln=%(ln)s&amp;status=%(status)s">%(label)s</a>%(stat)s</li>' % \
                {'siteURL': CFG_SITE_URL,
                 'ln': ln,
                 'status': CFG_WEBLINKBACK_STATUS['PENDING'],
                 'label': _("Pending Linkbacks"),
                 'stat': stat_pending_text}

        out += '<li><a href="%(siteURL)s/linkbacks?ln=%(ln)s">%(label)s</a></li>' % \
                {'siteURL': CFG_SITE_URL,
                 'ln': ln,
                 'label': _("Recent Linkbacks")}

        out += '<li><a href="%(siteURL)s/admin/weblinkback/weblinkbackadmin.py/lists?ln=%(ln)s&amp;returncode=%(returnCode)s">%(label)s</a></li>' % \
                {'siteURL': CFG_SITE_URL,
                 'ln': ln,
                 'returnCode': CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK'],
                 'label': _("Linkback Whitelist/Blacklist Manager")}


        out += '</ol>'
        from invenio.legacy.bibrank.adminlib import addadminbox
        return addadminbox('<b>%s</b>'% _("Menu"), [out])


def get_trackback_url(recid):
    return '%s/%s/%s/linkbacks/sendtrackback' % (CFG_SITE_URL, CFG_SITE_RECORD, recid)


def get_trackback_auto_discovery_tag(recid):
    return '<link rel="trackback" type="application/x-www-form-urlencoded" href="%s" />' \
                % cgi.escape(get_trackback_url(recid), True)
