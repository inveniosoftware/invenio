# -*- coding: utf-8 -*-
#
# handles rendering of webmessage module
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

""" templates for webmessage module """

__revision__ = "$Id$"

from invenio.utils.mail import email_quoted_txt2html, email_quote_txt
from invenio.modules.messages.config import CFG_WEBMESSAGE_STATUS_CODE, \
                                            CFG_WEBMESSAGE_SEPARATOR, \
                                            CFG_WEBMESSAGE_RESULTS_FIELD, \
                                            CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES
from invenio.utils.date import convert_datetext_to_dategui, \
                              datetext_default, \
                              create_day_selectbox, \
                              create_month_selectbox, \
                              create_year_selectbox
from invenio.utils.url import create_html_link, create_url
from invenio.utils.html import escape_html
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webuser import get_user_info

class Template:
    """Templates for WebMessage module"""

    def tmpl_display_inbox(self, messages, infos=[], warnings=[], nb_messages=0, no_quota=0, ln=CFG_SITE_LANG):
        """
        Displays a list of messages, with the appropriate links and buttons
        @param messages: a list of tuples:
                         [(message_id,
                           user_from_id,
                           user_from_nickname,
                           subject,
                           sent_date,
                           status=]
        @param infos: a list of informations to print on top of page
        @param warnings: a list of warnings to display
        @param nb_messages: number of messages user has
        @param no_quota: 1 if user has no quota (admin) or 0 else.
        @param ln: language of the page.
        @return: the list in HTML format
        """
        _ = gettext_set_language(ln)
        dummy = 0
        inbox = self.tmpl_warning(warnings, ln)
        inbox += self.tmpl_infobox(infos, ln)
        if not(no_quota):
            inbox += self.tmpl_quota(nb_messages, ln)
        inbox += """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr class="inboxheader">
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
    </tr>
  </thead>
  <tfoot>
    <tr style="height:0px;">
      <td></td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">""" % (_("Subject"),
                                    _("Sender"),
                                    _("Date"),
                                    _("Action"))
        if len(messages) == 0:
            inbox += """
    <tr class="mailboxrecord" style="height: 100px;">
      <td colspan="4" style="text-align: center;">
        <b>%s</b>
      </td>
    </tr>""" %(_("No messages"),)
        for (msgid, id_user_from, user_from_nick,
             subject, sent_date, status) in messages:
            if not(subject):
                subject = _("No subject")
            subject_link = create_html_link(
                                CFG_SITE_URL + '/yourmessages/display_msg',
                                {'msgid': msgid, 'ln': ln},
                                escape_html(subject))
            if user_from_nick:
                from_link = '%s'% (user_from_nick)
            else:
                from_link = get_user_info(id_user_from, ln)[2]
            action_link = create_html_link(CFG_SITE_URL + '/yourmessages/write',
                                           {'msg_reply_id': msgid, 'ln': ln},
                                           _("Reply"))
            action_link += ' '
            action_link += create_html_link(CFG_SITE_URL + '/yourmessages/delete',
                                            {'msgid': msgid, 'ln': ln},
                                            _("Delete"))
            s_date = convert_datetext_to_dategui(sent_date, ln)
            stat_style = ''
            if (status == CFG_WEBMESSAGE_STATUS_CODE['NEW']):
                stat_style = ' style="font-weight:bold"'
            inbox += """
    <tr class="mailboxrecord">
      <td%s>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
    </tr>""" %(stat_style, subject_link, from_link, s_date, action_link)
        inbox += """
    <tr class="mailboxfooter">
      <td colspan="2">
        <form name="newMessage" action="%(url_new)s" method="post">
          <input type="submit" name="del_all" value="%(write_label)s" class="formbutton" />
        </form>
      </td>
      <td>&nbsp;</td>
      <td>
        <form name="deleteAll" action="%(url_delete_all)s" method="post">
          <input type="submit" name="del_all" value="%(delete_all_label)s" class="formbutton" />
        </form>
      </td>
    </tr>
  </tbody>
</table>""" % {'url_new': create_url(CFG_SITE_URL + '/yourmessages/write',
                                     {'ln': ln}),
               'url_delete_all': create_url(CFG_SITE_URL + '/yourmessages/delete_all',
                                            {'ln': ln}),
               'write_label': _("Write new message"),
               'delete_all_label': _("Delete All")}
        return inbox

    def tmpl_write(self,
                   msg_to="", msg_to_group="",
                   msg_id=0,
                   msg_subject="", msg_body="",
                   msg_send_year=0, msg_send_month=0, msg_send_day=0,
                   warnings=[],
                   search_results_list=[],
                   search_pattern="",
                   results_field=CFG_WEBMESSAGE_RESULTS_FIELD['NONE'],
                   ln=CFG_SITE_LANG):
        """
        Displays a writing message form with optional prefilled fields
        @param msg_to: nick of the user (prefills the To: field)
        @param msg_subject: subject of the message (prefills the Subject: field)
        @param msg_body: body of the message (prefills the Message: field)
        @param msg_send_year: prefills to year field
        @param msg_send_month: prefills the month field
        @param msg_send_day: prefills the day field
        @param warnings: display warnings on top of page
        @param search_results_list: list of tuples. (user/groupname, is_selected)
        @param search_pattern: pattern used for searching
        @param results_field: 'none', 'user' or 'group', see CFG_WEBMESSAGE_RESULTS_FIELD
        @param ln: language of the form
        @return: the form in HTML format
        """
        _ = gettext_set_language(ln)
        write_box = self.tmpl_warning(warnings)

        # escape forbidden character
        msg_to = escape_html(msg_to)
        msg_to_group = escape_html(msg_to_group)
        msg_subject = escape_html(msg_subject)
        search_pattern = escape_html(search_pattern)

        to_select = self.tmpl_user_or_group_search(search_results_list,
                                                   search_pattern,
                                                   results_field,
                                                   ln)
        if msg_id:
            msg_subject = _("Re:") + " " + msg_subject
            msg_body = email_quote_txt(msg_body)
        write_box += """
<form name="write_message" action="%(url_form)s" method="post">
  <div style="float: left; vertical-align:text-top; margin-right: 10px;">
    <table class="mailbox">
      <thead class="mailboxheader">
        <tr>
          <td class="inboxheader" colspan="2">
            <table class="messageheader">
              <tr>
                <td class="mailboxlabel">%(to_label)s</td>
                <td class="mailboxlabel">%(users_label)s</td>
                <td style="width:100%%;">
                  <input class="mailboxinput" type="text" name="msg_to_user" value="%(to_users)s" />
                </td>
              </tr>
              <tr>
                <td class="mailboxlabel">&nbsp;</td>
                <td class="mailboxlabel">%(groups_label)s</td>
                <td style="width:100%%;">
                  <input class="mailboxinput" type="text" name="msg_to_group" value="%(to_groups)s" />
                </td>
              </tr>
              <tr>
                <td class="mailboxlabel">&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
              </tr>
              <tr>
                <td class="mailboxlabel">%(subject_label)s</td>
                <td colspan="2">
                  <input class="mailboxinput" type="text" name="msg_subject" value="%(subject)s" />
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </thead>
      <tfoot>
        <tr>
          <td style="height:0px" colspan="2"></td>
        </tr>
      </tfoot>
      <tbody class="mailboxbody">
        <tr>
          <td class="mailboxlabel">%(message_label)s</td>
          <td>
            <textarea name="msg_body" rows="10" cols="50">"""
        write_box_part2 = """
          </td>
        </tr>
        <tr>
          <td class="mailboxlabel">%(send_later_label)s</td>
          <td>
            %(day_field)s
            %(month_field)s
            %(year_field)s
          </td>
        </tr>
        <tr class="mailboxfooter">
          <td colspan="2" class="mailboxfoot">
            <input type="submit" name="send_button" value="%(send_label)s" class="formbutton"/>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div style="vertical-align:top; margin-left: 5px; float: left;">
    %(to_select)s
  </div>
</form>
"""
        write_box += "%(body)s</textarea>" + write_box_part2
        day_field = create_day_selectbox('msg_send_day',
                                          msg_send_day, ln)
        month_field = create_month_selectbox('msg_send_month',
                                              msg_send_month, ln)
        year_field = create_year_selectbox('msg_send_year', -1, 10,
                                            msg_send_year, ln)
        write_box = write_box % {'url_form': create_url(
                                                CFG_SITE_URL + '/yourmessages/send',
                                                {'ln': ln}),
                                 'to_users' : msg_to,
                                 'to_groups': msg_to_group,
                                 'subject' : msg_subject,
                                 'body' : msg_body,
                                 'ln': ln,
                                 'day_field': day_field,
                                 'month_field': month_field,
                                 'year_field': year_field,
                                 'to_select': to_select,
                                 'send_later_label': _("Send later?"),
                                 'to_label': _("To:"),
                                 'users_label': _("Users"),
                                 'groups_label': _("Groups"),
                                 'subject_label': _("Subject:"),
                                 'message_label': _("Message:"),
                                 'send_label': _("SEND")}
        return write_box

    def tmpl_display_msg(self,
                         msg_id="",
                         msg_from_id="",
                         msg_from_nickname="",
                         msg_sent_to="",
                         msg_sent_to_group="",
                         msg_subject="",
                         msg_body="",
                         msg_sent_date="",
                         msg_received_date=datetext_default,
                         ln=CFG_SITE_LANG):
        """
        Displays a given message
        @param msg_id: id of the message
        @param msg_from_id: id of user who sent the message
        @param msg_from_nickname: nickname of the user who sent the message
        @param msg_sent_to: list of users who received the message
                            (comma separated string)
        @param msg_sent_to_group: list of groups who received the message
                                  (comma separated string)
        @param msg_subject: subject of the message
        @param msg_body: body of the message
        @param msg_sent_date: date at which the message was sent
        @param msg_received_date: date at which the message had to be received
                                  (if this argument != 0000-00-00 => reminder
        @param ln: language of the page
        @return: the message in HTML format
        """

        # load the right message language
        _ = gettext_set_language(ln)

        sent_to_link = ''
        tos = msg_sent_to.split(CFG_WEBMESSAGE_SEPARATOR)
        if (tos):
            for to in tos[0:-1]:
                to_display = to
                if to.isdigit():
                    (dummy, to, to_display) = get_user_info(int(to), ln)
                sent_to_link += create_html_link(CFG_SITE_URL + '/yourmessages/write',
                                                 {'msg_to': to, 'ln': ln},
                                                 escape_html(to_display))
                sent_to_link += CFG_WEBMESSAGE_SEPARATOR
            to_display = tos[-1]
            to = tos[-1]
            if to.isdigit():
                (dummy, to, to_display) = get_user_info(int(to), ln)
            sent_to_link += create_html_link(CFG_SITE_URL + '/yourmessages/write',
                                             {'msg_to': to, 'ln': ln},
                                             escape_html(to_display))
        group_to_link = ""
        groups = msg_sent_to_group.split(CFG_WEBMESSAGE_SEPARATOR)
        if (groups):
            for group in groups[0:-1]:
                group_to_link += create_html_link(
                                    CFG_SITE_URL + '/yourmessages/write',
                                    {'msg_to_group': group, 'ln': ln},
                                    escape_html(group))
                group_to_link += CFG_WEBMESSAGE_SEPARATOR
            group_to_link += create_html_link(
                                CFG_SITE_URL + '/yourmessages/write',
                                {'msg_to_group': groups[-1], 'ln': ln},
                                escape_html(groups[-1]))
        # format the msg so that the '>>' chars give vertical lines
        final_body = email_quoted_txt2html(msg_body)

        out = """
<table class="mailbox" style="width: 70%%;">
  <thead class="mailboxheader">
    <tr>
      <td class="inboxheader" colspan="2">
        <table class="messageheader">
          <tr>
            <td class="mailboxlabel">%(from_label)s</td>
            <td>%(from_link)s</td>
          </tr>
          <tr>
            <td class="mailboxlabel">%(subject_label)s</td>
            <td style="width: 100%%;">%(subject)s</td>
          </tr>
          <tr>
            <td class="mailboxlabel">%(sent_label)s</td>
            <td>%(sent_date)s</td>
          </tr>"""
        if (msg_received_date != datetext_default):
            out += """
          <tr>
            <td class="mailboxlabel">%(received_label)s</td>
            <td>%(received_date)s</td>
          </tr>"""
        out += """
          <tr>
            <td class="mailboxlabel">%(sent_to_label)s</td>
            <td>%(sent_to)s</td>
          </tr>"""
        if (msg_sent_to_group != ""):
            out += """
          <tr>
            <td class="mailboxlabel">%(groups_label)s</td>
            <td>%(sent_to_group)s</td>
          </tr>"""
        out += """
        </table>
      </td>
    </tr>
  </thead>
  <tfoot>
    <tr>
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">
    <tr class="mailboxrecord">
      <td colspan="2">%(body)s</td>
    </tr>
    <tr class="mailboxfooter">
      <td>
        <form name="reply" action="%(reply_url)s" method="post">
          <input class="formbutton" name="reply" value="%(reply_but_label)s" type="submit" />
        </form>
      </td>
      <td>
        <form name="deletemsg" action="%(delete_url)s" method="post">
          <input class="formbutton" name="delete" value="%(delete_but_label)s" type="submit" />
        </form>
      </td>
    </tr>
  </tbody>
</table>
        """
        if msg_from_nickname:
            msg_from_display = msg_from_nickname
        else:
            msg_from_display = get_user_info(msg_from_id, ln)[2]
            msg_from_nickname = msg_from_id

        return out % {'from_link': create_html_link(
                                        CFG_SITE_URL + '/yourmessages/write',
                                        {'msg_to': msg_from_nickname,
                                         'ln': ln},
                                        msg_from_display),
                     'reply_url': create_url(CFG_SITE_URL + '/yourmessages/write',
                                             {'msg_reply_id': msg_id,
                                             'ln':  ln}),
                     'delete_url': create_url(CFG_SITE_URL + '/yourmessages/delete',
                                             {'msgid': msg_id,
                                             'ln':  ln}),
                     'sent_date' : convert_datetext_to_dategui(msg_sent_date, ln),
                     'received_date': convert_datetext_to_dategui(msg_received_date, ln),
                     'sent_to': sent_to_link,
                     'sent_to_group': group_to_link,
                     'subject' : msg_subject,
                     'body' : final_body,
                     'reply_to': msg_from_id,
                     'ln': ln,
                     'from_label':_("From:"),
                     'subject_label':_("Subject:"),
                     'sent_label': _("Sent on:"),
                     'received_label':_("Received on:"),
                     'sent_to_label': _("Sent to:"),
                     'groups_label': _("Sent to groups:"),
                     'reply_but_label':_("REPLY"),
                     'delete_but_label': _("DELETE")}

    def tmpl_navtrail(self, ln=CFG_SITE_LANG, title=""):
        """
        display the navtrail, e.g.:
        Your account > Your messages > title
        @param title: the last part of the navtrail. Is not a link
        @param ln: language
        return html formatted navtrail
        """
        _ = gettext_set_language(ln)
        nav_h1 = create_html_link(CFG_SITE_URL + '/youraccount/display',
                                  {'ln': ln},
                                  _("Your Account"),
                                  {'class': 'navtrail'})
        nav_h2 = ""
        if (title != ""):
            nav_h2 += create_html_link(CFG_SITE_URL + '/yourmessages/display',
                                       {'ln': ln},
                                       _("Your Messages"),
                                       {'class': 'navtrail'})
            return nav_h1 + ' &gt; ' + nav_h2
        return nav_h1

    def tmpl_confirm_delete(self, ln=CFG_SITE_LANG):
        """
        display a confirm message
        @param ln: language
        @return: html output
        """
        _ = gettext_set_language(ln)
        out = """
<table class="confirmoperation">
  <tr>
    <td colspan="2" class="confirmmessage">
      %(message)s
    </td>
  </tr>
  <tr>
    <td>
      <form name="validate" action="delete_all" method="post">
        <input type="hidden" name="confirmed" value="1" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(yes_label)s" class="formbutton" />
      </form>
    </td>
    <td>
      <form name="cancel" action="display" method="post">
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="submit" value="%(no_label)s" class="formbutton" />
      </form>
    </td>
  </tr>
</table>"""% {'message': _("Are you sure you want to empty your whole mailbox?"),
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("No")}
        return out

    def tmpl_infobox(self, infos, ln=CFG_SITE_LANG):
        """Display len(infos) information fields
        @param infos: list of strings
        @param ln=language
        @return: html output
        """
        _ = gettext_set_language(ln)
        if not((type(infos) is list) or (type(infos) is tuple)):
            infos = [infos]
        infobox = ""
        for info in infos:
            infobox += "<div class=\"infobox\">"
            lines = info.split("\n")
            for line in lines[0:-1]:
                infobox += line + "<br />\n"
            infobox += lines[-1] + "</div><br />\n"
        return infobox

    def tmpl_warning(self, warnings, ln=CFG_SITE_LANG):
        """
        Display len(warnings) warning fields
        @param infos: list of strings
        @param ln=language
        @return: html output
        """
        _ = gettext_set_language(ln)
        if not((type(warnings) is list) or (type(warnings) is tuple)):
            warnings = [warnings]
        warningbox = ""
        if warnings != []:
            warningbox = "<div class=\"warningbox\">\n  <b>Warning:</b>\n"
            for warning in warnings:
                lines = warning.split("\n")
                warningbox += "  <p>"
                for line in lines[0:-1]:
                    warningbox += line + "    <br />\n"
                warningbox += lines[-1] + "  </p>"
            warningbox += "</div><br />\n"
        return warningbox

    def tmpl_error(self, error, ln=CFG_SITE_LANG):
        """
        Display error
        @param error: string
        @param ln=language
        @return: html output
        """
        _ = gettext_set_language(ln)
        errorbox = ""
        if error != "":
            errorbox = "<div class=\"errorbox\">\n  <b>Error:</b>\n"
            errorbox += "  <p>"
            errorbox += error + "  </p>"
            errorbox += "</div><br />\n"
        return errorbox

    def tmpl_quota(self, nb_messages=0, ln=CFG_SITE_LANG):
        """
        Display a quota bar.
        @nb_messages: number of messages in inbox.
        @ln=language
        @return: html output
        """
        _ = gettext_set_language(ln)
        quota = float(CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES)
        ratio = float(nb_messages) / quota
        out = """
%(quota_label)s<br />
<div class="quotabox">
  <div class="quotabar" style="width:%(width)ipx"></div>
</div>""" % {'quota_label': _("Quota used: %(x_nb_used)i messages out of max. %(x_nb_total)i",
                              x_nb_used=nb_messages, x_nb_total=CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES),
             'width': int(ratio * 200)}

        return out


    def tmpl_multiple_select(self, select_name, tuples_list, ln=CFG_SITE_LANG):
        """displays a multiple select environment
        @param tuples_list: a list of (value, isSelected) tuples
        @return: HTML output
        """
        _ = gettext_set_language(ln)
        if not((type(tuples_list) is list) or (type(tuples_list) is tuple)):
            tuples_list = [tuples_list]
        out = """
        %s
<select name="%s" multiple="multiple" style="width:100%%">"""% (_("Please select one or more:"), select_name)
        for (value, is_selected) in tuples_list:
            out += '  <option value="%s"'% value
            if is_selected:
                out += " selected=\"selected\""
            out += ">%s</option>\n"% value
        out += "</select>\n"
        return out


    def tmpl_user_or_group_search(self,
                                  tuples_list=[],
                                  search_pattern="",
                                  results_field=CFG_WEBMESSAGE_RESULTS_FIELD['NONE'],
                                  ln=CFG_SITE_LANG):
        """
        Display a box for user searching
        @param tuples_list: list of (value, is_selected) tuples
        @param search_pattern: text to display in this field
        @param results_field: either 'none', 'user', 'group', look at CFG_WEBMESSAGE_RESULTS_FIELD
        @param ln: language
        @return: html output
        """
        _ = gettext_set_language(ln)
        multiple_select = ''
        add_button = ''
        if results_field != CFG_WEBMESSAGE_RESULTS_FIELD['NONE'] and results_field in CFG_WEBMESSAGE_RESULTS_FIELD.values():
            if len(tuples_list):
                multiple_select = self.tmpl_multiple_select('names_selected', tuples_list)
                add_button = '<input type="submit" name="%s" value="%s" class="nonsubmitbutton" />'
                if results_field == CFG_WEBMESSAGE_RESULTS_FIELD['USER']:
                    add_button = add_button % ('add_user', _("Add to users"))
                else:
                    add_button = add_button % ('add_group', _("Add to groups"))
            else:
                if results_field == CFG_WEBMESSAGE_RESULTS_FIELD['USER']:
                    multiple_select = _("No matching user")
                else:
                    multiple_select = _("No matching group")
        out = """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr class ="inboxheader">
      <td colspan="3">
        %(title_label)s
        <input type="hidden" name="results_field" value="%(results_field)s" />
      </td>
    </tr>
  </thead>
  <tfoot>
    <tr><td colspan="3"></td></tr>
  </tfoot>
  <tbody class="mailboxbody">
  <tr class="mailboxsearch">
      <td>
        <input type="text" name="search_pattern" value="%(search_pattern)s" />
      </td>
      <td>
        <input type="submit" name="search_user" value="%(search_user_label)s" class="nonsubmitbutton" />
      </td>
      <td>
        <input type="submit" name="search_group" value="%(search_group_label)s" class="nonsubmitbutton" />
      </td>
    </tr>
    <tr class="mailboxresults">
      <td colspan="2">
        %(multiple_select)s
      </td>
      <td>
        %(add_button)s
      </td>
    </tr>
  </tbody>
</table>
"""
        out = out % {'title_label'        : _("Find users or groups:"),
                     'search_user_label'  : _("Find a user"),
                     'search_group_label' : _("Find a group"),
                     'results_field'      : results_field,
                     'search_pattern'     : search_pattern,
                     'multiple_select'    : multiple_select,
                     'add_button'         : add_button}
        return out

    def tmpl_account_new_mail(self, nb_new_mail=0, total_mail=0, ln=CFG_SITE_LANG):
        """
        display infos about inbox (used by myaccount.py)
        @param nb_new_mail: number of new mails
        @param ln: language
        return: html output.
        """
        _ = gettext_set_language(ln)
        out = _("You have %(x_nb_new)s new messages out of %(x_nb_total)s messages") % \
              {'x_nb_new': '<b>' + str(nb_new_mail) + '</b>',
               'x_nb_total': create_html_link(CFG_SITE_URL + '/yourmessages/',
                                              {'ln': ln},
                                              str(total_mail),
                                              {},
                                              False, False)}
        return out + '.'


