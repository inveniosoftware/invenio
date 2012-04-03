## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import urllib
import cgi

from invenio.config import \
     CFG_CERN_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_URL, \
     CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS, \
     CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS, \
     CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
     CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS, \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_SITE_RECORD
from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO, \
        CFG_EXTERNAL_AUTH_LOGOUT_SSO
from invenio.urlutils import make_canonical_urlargd, create_url, create_html_link
from invenio.htmlutils import escape_html, nmtoken_from_string
from invenio.messages import gettext_set_language, language_list_long
from invenio.websession_config import CFG_WEBSESSION_GROUP_JOIN_POLICY
class Template:
    def tmpl_back_form(self, ln, message, url, link):
        """
        A standard one-message-go-back-link page.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'message' *string* - The message to display

          - 'url' *string* - The url to go back to

          - 'link' *string* - The link text
        """
        out = """
                 <table>
                    <tr>
                      <td align="left">%(message)s
                       <a href="%(url)s">%(link)s</a></td>
                    </tr>
                 </table>
             """% {
               'message' : message,
               'url'     : url,
               'link'    : link,
               'ln'      : ln
             }

        return out

    def tmpl_external_setting(self, ln, key, value):
        _ = gettext_set_language(ln)
        out = """
        <tr>
            <td align="right"><strong>%s:</strong></td>
            <td><i>%s</i></td>
        </tr>""" % (key, value)
        return out

    def tmpl_external_user_settings(self, ln, html_settings):
        _ = gettext_set_language(ln)
        out = """
        <p><big><strong class="headline">%(external_user_settings)s</strong></big></p>
        <table>
            %(html_settings)s
        </table>
        <p><big><strong class="headline">%(external_user_groups)s</strong></big></p>
        <p>%(consult_external_groups)s</p>
        """ % {
            'external_user_settings' : _('External account settings'),
            'html_settings' : html_settings,
            'consult_external_groups' : _('You can consult the list of your external groups directly in the %(x_url_open)sgroups page%(x_url_close)s.') % {
                'x_url_open' : '<a href="../yourgroups/display?ln=%s#external_groups">' % ln,
                'x_url_close' : '</a>'
            },
            'external_user_groups' : _('External user groups'),
        }
        return out

    def tmpl_user_preferences(self, ln, email, email_disabled, password_disabled, nickname):
        """
        Displays a form for the user to change his email/password.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'email' *string* - The email of the user

          - 'email_disabled' *boolean* - If the user has the right to edit his email

          - 'password_disabled' *boolean* - If the user has the right to edit his password

          - 'nickname' *string* - The nickname of the user (empty string if user does not have it)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
                <p><big><strong class="headline">%(edit_params)s</strong></big></p>
                <form method="post" action="%(sitesecureurl)s/youraccount/change" name="edit_logins_settings">
                <p>%(change_user)s</p>
                <table>
                  <tr><td align="right" valign="top"><strong>
                      <label for="nickname">%(nickname_label)s:</label></strong><br />
                      <small class="important">(%(mandatory)s)</small>
                    </td><td valign="top">
                      %(nickname_prefix)s%(nickname)s%(nickname_suffix)s<br />
                      <small><span class="quicknote">%(note)s:</span>
                       %(fixed_nickname_note)s
                      </small>
                    </td>
                  </tr>
                  <tr><td align="right"><strong>
                      <label for="email">%(new_email)s:</label></strong><br />
                      <small class="important">(%(mandatory)s)</small>
                    </td><td>
                      <input type="text" size="25" name="email" id="email" %(email_disabled)s value="%(email)s" /><br />
                      <small><span class="quicknote">%(example)s:</span>
                        <span class="example">john.doe@example.com</span>
                      </small>
                    </td>
                  </tr>
                  <tr><td></td><td align="left">
                    <code class="blocknote"><input class="formbutton" type="submit" value="%(set_values)s" /></code>&nbsp;&nbsp;&nbsp;
                  </td></tr>
                </table>
                <input type="hidden" name="action" value="edit" />
                </form>
            """ % {
                'change_user' : _("If you want to change your email or set for the first time your nickname, please set new values in the form below."),
                'edit_params' : _("Edit login credentials"),
                'nickname_label' : _("Nickname"),
                'nickname' : nickname,
                'nickname_prefix' : nickname=='' and '<input type="text" size="25" name="nickname" id="nickname" value=""' or '',
                'nickname_suffix' : nickname=='' and '" /><br /><small><span class="quicknote">'+_("Example")+':</span><span class="example">johnd</span></small>' or '',
                'new_email' : _("New email address"),
                'mandatory' : _("mandatory"),
                'example' : _("Example"),
                'note' : _("Note"),
                'set_values' : _("Set new values"),
                'email' : email,
                'email_disabled' : email_disabled and "readonly" or "",
                'sitesecureurl': CFG_SITE_SECURE_URL,
                'fixed_nickname_note' : _('Since this is considered as a signature for comments and reviews, once set it can not be changed.')
            }

        if not password_disabled and not CFG_EXTERNAL_AUTH_USING_SSO:
            out += """
                <form method="post" action="%(sitesecureurl)s/youraccount/change" name="edit_password">
                <p>%(change_pass)s</p>
                <table>
                  <tr>
                    <td align="right"><strong><label for="old_password">%(old_password)s:</label></strong><br />
                    </td><td align="left">
                      <input type="password" size="25" name="old_password" id="old_password" %(password_disabled)s /><br />
                      <small><span class="quicknote">%(note)s:</span>
                       %(old_password_note)s
                      </small>
                    </td>
                  </tr>
                  <tr>
                    <td align="right"><strong><label for="new_password">%(new_password)s:</label></strong><br />
                    </td><td align="left">
                      <input type="password" size="25" name="password" id="new_password" %(password_disabled)s /><br />
                      <small><span class="quicknote">%(note)s:</span>
                       %(password_note)s
                      </small>
                    </td>
                  </tr>
                  <tr>
                    <td align="right"><strong><label for="new_password2">%(retype_password)s:</label></strong></td>
                    <td align="left">
                      <input type="password" size="25" name="password2" id="new_password2" %(password_disabled)s value="" />
                    </td>
                  </tr>
                  <tr><td></td><td align="left">
                    <code class="blocknote"><input class="formbutton" type="submit" value="%(set_values)s" /></code>&nbsp;&nbsp;&nbsp;
                  </td></tr>
                </table>
                <input type="hidden" name="action" value="edit" />
                </form>
                """ % {
                    'change_pass' : _("If you want to change your password, please enter the old one and set the new value in the form below."),
                    'mandatory' : _("mandatory"),
                    'old_password' : _("Old password"),
                    'new_password' : _("New password"),
                    'optional' : _("optional"),
                    'note' : _("Note"),
                    'password_note' : _("The password phrase may contain punctuation, spaces, etc."),
                    'old_password_note' : _("You must fill the old password in order to set a new one."),
                    'retype_password' : _("Retype password"),
                    'set_values' : _("Set new password"),
                    'password_disabled' : password_disabled and "disabled" or "",
                    'sitesecureurl': CFG_SITE_SECURE_URL,
                }
        elif not CFG_EXTERNAL_AUTH_USING_SSO and CFG_CERN_SITE:
            out += "<p>" + _("""If you are using a lightweight CERN account you can
                %(x_url_open)sreset the password%(x_url_close)s.""") % \
                    {'x_url_open' : \
                        '<a href="http://cern.ch/LightweightRegistration/ResetPassword.aspx%s">' \
                        % (make_canonical_urlargd({'email': email, 'returnurl' : CFG_SITE_SECURE_URL + '/youraccount/edit' + make_canonical_urlargd({'lang' : ln}, {})}, {})), 'x_url_close' : '</a>'} + "</p>"
        elif CFG_EXTERNAL_AUTH_USING_SSO and CFG_CERN_SITE:
            out += "<p>" + _("""You can change or reset your CERN account password by means of the %(x_url_open)sCERN account system%(x_url_close)s.""") % \
                {'x_url_open' : '<a href="https://cern.ch/login/password.aspx">', 'x_url_close' : '</a>'} + "</p>"
        return out


    def tmpl_user_bibcatalog_auth(self, bibcatalog_username="", bibcatalog_password="", ln=CFG_SITE_LANG):
        """template for setting username and pw for bibcatalog backend"""
        _ = gettext_set_language(ln)
        out = """
            <form method="post" action="%(sitesecureurl)s/youraccount/change" name="edit_bibcatalog_settings">
              <p><big><strong class="headline">%(edit_bibcatalog_settings)s</strong></big></p>
              <table>
                <tr>
                  <td> %(username)s: <input type="text" size="25" name="bibcatalog_username" value="%(bibcatalog_username)s" id="bibcatuid"></td>
                  <td> %(password)s: <input type="password" size="25" name="bibcatalog_password" value="%(bibcatalog_password)s" id="bibcatpw"></td>
                </tr>
                <tr>
                  <td><input class="formbutton" type="submit" value="%(update_settings)s" /></td>
                </tr>
              </table>
        """ % {
          'sitesecureurl' : CFG_SITE_SECURE_URL,
          'bibcatalog_username' : bibcatalog_username,
          'bibcatalog_password' : bibcatalog_password,
          'edit_bibcatalog_settings' : _("Edit cataloging interface settings"),
          'username' :  _("Username"),
          'password' :  _("Password"),
          'update_settings' : _('Update settings')
        }
        return out


    def tmpl_user_lang_edit(self, ln, preferred_lang):
        _ = gettext_set_language(ln)
        out = """
            <form method="post" action="%(sitesecureurl)s/youraccount/change" name="edit_lang_settings">
              <p><big><strong class="headline">%(edit_lang_settings)s</strong></big></p>
              <table>
                <tr><td align="right"><select name="lang" id="lang">
        """ % {
          'sitesecureurl' : CFG_SITE_SECURE_URL,
          'edit_lang_settings' : _("Edit language-related settings"),
        }
        for short_ln, long_ln in language_list_long():
            out += """<option %(selected)s value="%(short_ln)s">%(long_ln)s</option>""" % {
                'selected' : preferred_lang == short_ln and 'selected="selected"' or '',
                'short_ln' : short_ln,
                'long_ln' : escape_html(long_ln)
            }
        out += """</select></td><td valign="top"><strong><label for="lang">%(select_lang)s</label></strong></td></tr>
            <tr><td></td><td><input class="formbutton" type="submit" value="%(update_settings)s" /></td></tr>
        </table></form>""" % {
            'select_lang' : _('Select desired language of the web interface.'),
            'update_settings' : _('Update settings')
        }
        return out

    def tmpl_user_websearch_edit(self, ln, current = 10, show_latestbox = True, show_helpbox = True):
        _ = gettext_set_language(ln)
        out = """
            <form method="post" action="%(sitesecureurl)s/youraccount/change" name="edit_websearch_settings">
              <p><big><strong class="headline">%(edit_websearch_settings)s</strong></big></p>
              <table>
                <tr><td align="right"><input type="checkbox" %(checked_latestbox)s value="1" name="latestbox" id="latestbox"/></td>
                <td valign="top"><b><label for="latestbox">%(show_latestbox)s</label></b></td></tr>
                <tr><td align="right"><input type="checkbox" %(checked_helpbox)s value="1" name="helpbox" id="helpbox"/></td>
                <td valign="top"><b><label for="helpbox">%(show_helpbox)s</label></b></td></tr>
                <tr><td align="right"><select name="group_records" id="group_records">
        """ % {
          'sitesecureurl' : CFG_SITE_SECURE_URL,
          'edit_websearch_settings' : _("Edit search-related settings"),
          'show_latestbox' : _("Show the latest additions box"),
          'checked_latestbox' : show_latestbox and 'checked="checked"' or '',
          'show_helpbox' : _("Show collection help boxes"),
          'checked_helpbox' : show_helpbox and 'checked="checked"' or '',
        }
        for i in 10, 25, 50, 100, 250, 500:
            if i <= CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS:
                out += """<option %(selected)s>%(i)s</option>
                    """ % {
                        'selected' : current == i and 'selected="selected"' or '',
                        'i' : i
                    }
        out += """</select></td><td valign="top"><strong><label for="group_records">%(select_group_records)s</label></strong></td></tr>
              <tr><td></td><td><input class="formbutton" type="submit" value="%(update_settings)s" /></td></tr>
              </table>
            </form>""" % {
                'update_settings' : _("Update settings"),
                'select_group_records' : _("Number of search results per page"),
            }
        return out


    def tmpl_user_external_auth(self, ln, methods, current, method_disabled):
        """
        Displays a form for the user to change his authentication method.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'methods' *array* - The methods of authentication

          - 'method_disabled' *boolean* - If the user has the right to change this

          - 'current' *string* - The currently selected method
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
                 <form method="post" action="%(sitesecureurl)s/youraccount/change">
                   <big><strong class="headline">%(edit_method)s</strong></big>
                   <p>%(explain_method)s:</p>
                   <table>
                     <tr><td valign="top"><b>%(select_method)s:</b></td><td>
               """ % {
                 'edit_method' : _("Edit login method"),
                 'explain_method' : _("Please select which login method you would like to use to authenticate yourself"),
                 'select_method' : _("Select method"),
                 'sitesecureurl': CFG_SITE_SECURE_URL,
               }
        for system in methods:
            out += """<input type="radio" name="login_method" value="%(system)s" id="%(id)s" %(disabled)s %(selected)s /><label for="%(id)s">%(system)s</label><br />""" % {
                     'system' : system,
                     'disabled' : method_disabled and 'disabled="disabled"' or "",
                     'selected' : current == system and 'checked="checked"' or "",
                     'id' : nmtoken_from_string(system),
                   }
        out += """  </td></tr>
                   <tr><td>&nbsp;</td>
                     <td><input class="formbutton" type="submit" value="%(select_method)s" /></td></tr></table>
                    </form>""" % {
                     'select_method' : _("Select method"),
                   }

        return out

    def tmpl_lost_password_form(self, ln):
        """
        Displays a form for the user to ask for his password sent by email.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - Explicative message on top of the form.
        """

        # load the right message language
        _ = gettext_set_language(ln)
        out = "<p>" + _("If you have lost the password for your %(sitename)s %(x_fmt_open)sinternal account%(x_fmt_close)s, then please enter your email address in the following form in order to have a password reset link emailed to you.") % {'x_fmt_open' : '<em>', 'x_fmt_close' : '</em>', 'sitename' : CFG_SITE_NAME_INTL[ln]} + "</p>"

        out += """
          <blockquote>
          <form  method="post" action="../youraccount/send_email">
          <table>
                <tr>
              <td align="right"><strong><label for="p_email">%(email)s:</label></strong></td>
              <td><input type="text" size="25" name="p_email" id="p_email" value="" />
                  <input type="hidden" name="ln" value="%(ln)s" />
                  <input type="hidden" name="action" value="lost" />
              </td>
            </tr>
            <tr><td>&nbsp;</td>
              <td><code class="blocknote"><input class="formbutton" type="submit" value="%(send)s" /></code></td>
            </tr>
          </table>

          </form>
          </blockquote>
          """ % {
            'ln': ln,
            'email' : _("Email address"),
            'send' : _("Send password reset link"),
          }

        if CFG_CERN_SITE:
            out += "<p>" + _("If you have been using the %(x_fmt_open)sCERN login system%(x_fmt_close)s, then you can recover your password through the %(x_url_open)sCERN authentication system%(x_url_close)s.") % {'x_fmt_open' : '<em>', 'x_fmt_close' : '</em>', 'x_url_open' : '<a href="https://cern.ch/lightweightregistration/ResetPassword.aspx%s">' \
            % make_canonical_urlargd({'lf': 'auth', 'returnURL' : CFG_SITE_SECURE_URL + '/youraccount/login?ln='+ln}, {}), 'x_url_close' : '</a>'} + " "
        else:
            out += "<p>" + _("Note that if you have been using an external login system, then we cannot do anything and you have to ask there.") + " "
        out += _("Alternatively, you can ask %s to change your login system from external to internal.") % ("""<a href="mailto:%(email)s">%(email)s</a>""" % { 'email' : CFG_SITE_SUPPORT_EMAIL }) + "</p>"


        return out

    def tmpl_account_info(self, ln, uid, guest, CFG_CERN_SITE):
        """
        Displays the account information

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'uid' *string* - The user id

          - 'guest' *boolean* - If the user is guest

          - 'CFG_CERN_SITE' *boolean* - If the site is a CERN site
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<p>%(account_offer)s</p>
                 <blockquote>
                 <dl>
              """ % {
                'account_offer' : _("%s offers you the possibility to personalize the interface, to set up your own personal library of documents, or to set up an automatic alert query that would run periodically and would notify you of search results by email.") % CFG_SITE_NAME_INTL[ln],
              }

        if not guest:
            out += """
                   <dt>
                   <a href="./edit?ln=%(ln)s">%(your_settings)s</a>
                   </dt>
                   <dd>%(change_account)s</dd>""" % {
                     'ln' : ln,
                     'your_settings' : _("Your Settings"),
                     'change_account' : _("Set or change your account email address or password. Specify your preferences about the look and feel of the interface.")
                   }

        out += """
        <dt><a href="../youralerts/display?ln=%(ln)s">%(your_searches)s</a></dt>
        <dd>%(search_explain)s</dd>""" % {
          'ln' : ln,
          'your_searches' : _("Your Searches"),
          'search_explain' : _("View all the searches you performed during the last 30 days."),

        }
        out += """
        <dt><a href="../yourbaskets/display?ln=%(ln)s">%(your_baskets)s</a></dt>
        <dd>%(basket_explain)s""" % {
        'ln' : ln,
        'your_baskets' : _("Your Baskets"),
        'basket_explain' : _("With baskets you can define specific collections of items, store interesting records you want to access later or share with others."),
        }
        if guest and CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
            out += self.tmpl_warning_guest_user(ln = ln, type = "baskets")
        out += """</dd>
        <dt><a href="../youralerts/list?ln=%(ln)s">%(your_alerts)s</a></dt>
        <dd>%(explain_alerts)s""" % {
          'ln' : ln,
          'your_alerts' : _("Your Alerts"),
          'explain_alerts' : _("Subscribe to a search which will be run periodically by our service. The result can be sent to you via Email or stored in one of your baskets."),
        }
        if guest and CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
            out += self.tmpl_warning_guest_user(type="alerts", ln = ln)
        out += "</dd>"
        if CFG_CERN_SITE:
            out += """</dd>
            <dt><a href="%(CFG_SITE_SECURE_URL)s/yourloans/display?ln=%(ln)s">%(your_loans)s</a></dt>
            <dd>%(explain_loans)s</dd>""" % {
              'your_loans' : _("Your Loans"),
              'explain_loans' : _("Check out book you have on loan, submit borrowing requests, etc. Requires CERN ID."),
            'ln': ln,
            'CFG_SITE_SECURE_URL': CFG_SITE_SECURE_URL
            }

        out += """
        </dl>
        </blockquote>"""

        return out

    def tmpl_warning_guest_user(self, ln, type):
        """
        Displays a warning message about the specified type

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'type' *string* - The type of data that will get lost in case of guest account (for the moment: 'alerts' or 'baskets')
        """

        # load the right message language
        _ = gettext_set_language(ln)
        if (type=='baskets'):
            msg = _("You are logged in as a guest user, so your baskets will disappear at the end of the current session.") + ' '
        elif (type=='alerts'):
            msg = _("You are logged in as a guest user, so your alerts will disappear at the end of the current session.") + ' '
        msg += _("If you wish you can %(x_url_open)slogin or register here%(x_url_close)s.") % {'x_url_open': '<a href="' + CFG_SITE_SECURE_URL + '/youraccount/login?ln=' + ln + '">',
                                                                                               'x_url_close': '</a>'}
        return """<table class="errorbox" summary="">
                            <tr>
                             <th class="errorboxheader">%s</th>
                            </tr>
                          </table>""" % msg

    def tmpl_account_body(self, ln, user):
        """
        Displays the body of the actions of the user

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'user' *string* - The username (nickname or email)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = _("You are logged in as %(x_user)s. You may want to a) %(x_url1_open)slogout%(x_url1_close)s; b) edit your %(x_url2_open)saccount settings%(x_url2_close)s.") %\
            {'x_user': user,
             'x_url1_open': '<a href="' + CFG_SITE_SECURE_URL + '/youraccount/logout?ln=' + ln + '">',
             'x_url1_close': '</a>',
             'x_url2_open': '<a href="' + CFG_SITE_SECURE_URL + '/youraccount/edit?ln=' + ln + '">',
             'x_url2_close': '</a>',
             }
        return out + "<br /><br />"

    def tmpl_account_template(self, title, body, ln, url):
        """
        Displays a block of the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'title' *string* - The title of the block

          - 'body' *string* - The body of the block

          - 'url' *string* - The URL to go to the proper section
        """

        out ="""
              <table class="youraccountbox" width="90%%" summary=""  >
                            <tr>
                             <th class="youraccountheader"><a href="%s">%s</a></th>
                            </tr>
                            <tr>
                             <td class="youraccountbody">%s</td>
                            </tr>
                          </table>""" % (url, title, body)
        return out

    def tmpl_account_page(self, ln, warnings, warning_list, accBody, baskets, alerts, searches, messages, loans, groups, submissions, approvals, tickets, administrative):
        """
        Displays the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'accBody' *string* - The body of the heading block

          - 'baskets' *string* - The body of the baskets block

          - 'alerts' *string* - The body of the alerts block

          - 'searches' *string* - The body of the searches block

          - 'messages' *string* - The body of the messages block

          - 'groups' *string* - The body of the groups block

          - 'submissions' *string* - The body of the submission block

          - 'approvals' *string* - The body of the approvals block

          - 'administrative' *string* - The body of the administrative block
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""

        if warnings == "1":
            out += self.tmpl_general_warnings(warning_list)

        out += self.tmpl_account_template(_("Your Account"), accBody, ln, '/youraccount/edit?ln=%s' % ln)
        if messages:
            out += self.tmpl_account_template(_("Your Messages"), messages, ln, '/yourmessages/display?ln=%s' % ln)

        if loans:
            out += self.tmpl_account_template(_("Your Loans"), loans, ln, '/yourloans/display?ln=%s' % ln)

        if baskets:
            out += self.tmpl_account_template(_("Your Baskets"), baskets, ln, '/yourbaskets/display?ln=%s' % ln)

        if alerts:
            out += self.tmpl_account_template(_("Your Alert Searches"), alerts, ln, '/youralerts/list?ln=%s' % ln)

        if searches:
            out += self.tmpl_account_template(_("Your Searches"), searches, ln, '/youralerts/display?ln=%s' % ln)

        if groups:
            groups_description = _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s you are administering or are a member of.")
            groups_description %= {'x_url_open': '<a href="' + CFG_SITE_URL + '/yourgroups/display?ln=' + ln + '">',
                               'x_url_close': '</a>'}
            out += self.tmpl_account_template(_("Your Groups"), groups_description, ln, '/yourgroups/display?ln=%s' % ln)

        if submissions:
            submission_description = _("You can consult the list of %(x_url_open)syour submissions%(x_url_close)s and inquire about their status.")
            submission_description %= {'x_url_open': '<a href="' + CFG_SITE_URL + '/yoursubmissions.py?ln=' + ln + '">',
                                   'x_url_close': '</a>'}
            out += self.tmpl_account_template(_("Your Submissions"), submission_description, ln, '/yoursubmissions.py?ln=%s' % ln)

        if approvals:
            approval_description =  _("You can consult the list of %(x_url_open)syour approvals%(x_url_close)s with the documents you approved or refereed.")
            approval_description %=  {'x_url_open': '<a href="' + CFG_SITE_URL + '/yourapprovals.py?ln=' + ln + '">',
                                  'x_url_close': '</a>'}
            out += self.tmpl_account_template(_("Your Approvals"), approval_description, ln, '/yourapprovals.py?ln=%s' % ln)

        #check if this user might have tickets
        if tickets:
            ticket_description =  _("You can consult the list of %(x_url_open)syour tickets%(x_url_close)s.")
            ticket_description %=  {'x_url_open': '<a href="' + CFG_SITE_URL + '/yourtickets?ln=' + ln + '">',
                                    'x_url_close': '</a>'}
            out += self.tmpl_account_template(_("Your Tickets"), ticket_description, ln, '/yourtickets?ln=%s' % ln)
        if administrative:
            out += self.tmpl_account_template(_("Your Administrative Activities"), administrative, ln, '/admin')
        return out

    def tmpl_account_emailMessage(self, ln, msg):
        """
        Displays a link to retrieve the lost password

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - Explicative message on top of the form.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out =""
        out +="""
        <body>
           %(msg)s <a href="../youraccount/lost?ln=%(ln)s">%(try_again)s</a>

              </body>

          """ % {
            'ln' : ln,
            'msg' : msg,
            'try_again' : _("Try again")
          }
        return out

    def tmpl_account_reset_password_email_body(self, email, reset_key, ip_address, ln=CFG_SITE_LANG):
        """
        The body of the email that sends lost internal account
        passwords to users.
        """

        _ = gettext_set_language(ln)

        out = """
%(intro)s

%(intro2)s

<%(link)s>

%(outro)s

%(outro2)s""" % {
            'intro': _("Somebody (possibly you) coming from %(x_ip_address)s "
                "has asked\nfor a password reset at %(x_sitename)s\nfor "
                "the account \"%(x_email)s\"." % {
                    'x_sitename' :CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
                    'x_email' : email,
                    'x_ip_address' : ip_address,
                    }
                ),
            'intro2' : _("If you want to reset the password for this account, please go to:"),
            'link' : "%s/youraccount/access%s" %
                (CFG_SITE_SECURE_URL, make_canonical_urlargd({
                    'ln' : ln,
                    'mailcookie' : reset_key
                }, {})),
            'outro' : _("in order to confirm the validity of this request."),
            'outro2' : _("Please note that this URL will remain valid for about %(days)s days only.") % {'days': CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS},
        }
        return out

    def tmpl_account_address_activation_email_body(self, email, address_activation_key, ip_address, ln=CFG_SITE_LANG):
        """
        The body of the email that sends email address activation cookie
        passwords to users.
        """

        _ = gettext_set_language(ln)

        out = """
%(intro)s

%(intro2)s

<%(link)s>

%(outro)s

%(outro2)s""" % {
            'intro': _("Somebody (possibly you) coming from %(x_ip_address)s "
                "has asked\nto register a new account at %(x_sitename)s\nfor the "
                "email address \"%(x_email)s\"." % {
                    'x_sitename' :CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
                    'x_email' : email,
                    'x_ip_address' : ip_address,
                    }
                ),
            'intro2' : _("If you want to complete this account registration, please go to:"),
            'link' : "%s/youraccount/access%s" %
                (CFG_SITE_SECURE_URL, make_canonical_urlargd({
                    'ln' : ln,
                    'mailcookie' : address_activation_key
                }, {})),
            'outro' : _("in order to confirm the validity of this request."),
            'outro2' : _("Please note that this URL will remain valid for about %(days)s days only.") % {'days' : CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS},
        }
        return out

    def tmpl_account_emailSent(self, ln, email):
        """
        Displays a confirmation message for an email sent

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'email' *string* - The email to which the message has been sent
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out =""
        out += _("Okay, a password reset link has been emailed to %s.") % email
        return out

    def tmpl_account_delete(self, ln):
        """
        Displays a confirmation message about deleting the account

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>" + _("""Deleting your account""") + '</p>'
        return out

    def tmpl_account_logout(self, ln):
        """
        Displays a confirmation message about logging out

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)
        out = _("You are no longer recognized by our system.") + ' '
        if CFG_EXTERNAL_AUTH_USING_SSO and CFG_EXTERNAL_AUTH_LOGOUT_SSO:
            out += _("""You are still recognized by the centralized
                %(x_fmt_open)sSSO%(x_fmt_close)s system. You can
                %(x_url_open)slogout from SSO%(x_url_close)s, too.""") % \
                {'x_fmt_open' : '<strong>', 'x_fmt_close' : '</strong>',
                 'x_url_open' : '<a href="%s">' % CFG_EXTERNAL_AUTH_LOGOUT_SSO,
                 'x_url_close' : '</a>'}
            out += '<br />'
        out += _("If you wish you can %(x_url_open)slogin here%(x_url_close)s.") % \
                {'x_url_open': '<a href="./login?ln=' + ln + '">',
                 'x_url_close': '</a>'}
        return out

    def tmpl_login_form(self, ln, referer, internal, register_available, methods, selected_method, msg=None):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'internal' *boolean* - If we are producing an internal authentication

          - 'register_available' *boolean* - If users can register freely in the system

          - 'methods' *array* - The available authentication methods

          - 'selected_method' *string* - The default authentication method

          - 'msg' *string* - The message to print before the form, if needed
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if msg is "":
            out = "<p>%(please_login)s</p>" % {
                    'please_login' : cgi.escape(_("If you already have an account, please login using the form below."))
                }

            if CFG_CERN_SITE:
                out += "<p>" + _("If you don't own a CERN account yet, you can register a %(x_url_open)snew CERN lightweight account%(x_url_close)s.") % {'x_url_open' : '<a href="https://www.cern.ch/lightweightregistration/RegisterAccount.aspx">', 'x_url_close' : '</a>'} + "</p>"
            else:
                if register_available:
                    out += "<p>"+_("If you don't own an account yet, please %(x_url_open)sregister%(x_url_close)s an internal account.") %\
                        {'x_url_open': '<a href="../youraccount/register?ln=' + ln + '">',
                        'x_url_close': '</a>'} + "</p>"
                else:
                    # users cannot register accounts, so advise them
                    # how to get one, or be silent about register
                    # facility if account level is more than 4:
                    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 5:
                        out += "<p>" + _("If you don't own an account yet, please contact %s.") % ('<a href="mailto:%s">%s</a>' % (cgi.escape(CFG_SITE_SUPPORT_EMAIL, True), cgi.escape(CFG_SITE_SUPPORT_EMAIL))) + "</p>"

        else:
            out = "<p>%s</p>" % msg

        out += """<form method="post" action="../youraccount/login">
                  <table>

               """
        if len(methods) > 1:
            # more than one method, must make a select
            login_select = """<select name="login_method" id="login_method">"""
            for method in methods:
                login_select += """<option value="%(method)s" %(selected)s>%(method)s</option>""" % {
                                  'method' : cgi.escape(method, True),
                                  'selected' : (method == selected_method and 'selected="selected"' or "")
                                }
            login_select += "</select>"
            out += """
                   <tr>
                      <td align="right"><strong><label for="login_method">%(login_title)s</label></strong></td>
                      <td>%(login_select)s</td>
                   </tr>""" % {
                     'login_title' : cgi.escape(_("Login method:")),
                     'login_select' : cgi.escape(login_select),
                   }
        else:
            # only one login method available
            out += """<input type="hidden" name="login_method" value="%s" />""" % cgi.escape(methods[0], True)

        out += """<tr>
                   <td align="right">
                     <input type="hidden" name="ln" value="%(ln)s" />
                     <input type="hidden" name="referer" value="%(referer)s" />
                     <strong><label for="p_un">%(username)s:</label></strong>
                   </td>
                   <td><input type="text" size="25" name="p_un" id="p_un" value="" /></td>
                  </tr>
                  <tr>
                   <td align="right"><strong><label for="p_pw">%(password)s:</label></strong></td>
                   <td align="left"><input type="password" size="25" name="p_pw" id="p_pw" value="" /></td>
                  </tr>
                  <tr>
                   <td></td>
                   <td align="left"><input type="checkbox" name="remember_me" id="remember_me"/><em><label for="remember_me">%(remember_me)s</label></em></td>
                  <tr>
                   <td></td>
                   <td align="center" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(login)s" /></code>""" % {
                       'ln': cgi.escape(ln, True),
                       'referer' : cgi.escape(referer, True),
                       'username' : cgi.escape(_("Username")),
                       'password' : cgi.escape(_("Password")),
                       'remember_me' : cgi.escape(_("Remember login on this computer.")),
                       'login' : cgi.escape(_("login")),
                       }
        if internal:
            out += """&nbsp;&nbsp;&nbsp;(<a href="./lost?ln=%(ln)s">%(lost_pass)s</a>)""" % {
                     'ln' : cgi.escape(ln, True),
                     'lost_pass' : cgi.escape(_("Lost your password?"))
                   }
        out += """</td>
                    </tr>
                  </table></form>"""

        out += """<p><strong>%(note)s:</strong> %(note_text)s</p>""" % {
               'note' : cgi.escape(_("Note")),
               'note_text': cgi.escape(_("You can use your nickname or your email address to login."))}

        return out

    def tmpl_lost_your_password_teaser(self, ln=CFG_SITE_LANG):
        """Displays a short sentence to attract user to the fact that
        maybe he lost his password.  Used by the registration page.
        """

        _ = gettext_set_language(ln)

        out = ""
        out += """<a href="./lost?ln=%(ln)s">%(maybe_lost_pass)s</a>""" % {
                     'ln' : ln,
                     'maybe_lost_pass': ("Maybe you have lost your password?")
                     }
        return out

    def tmpl_reset_password_form(self, ln, email, reset_key, msg=''):
        """Display a form to reset the password."""

        _ = gettext_set_language(ln)

        out = ""
        out = "<p>%s</p>" % _("Your request is valid. Please set the new "
            "desired password in the following form.")
        if msg:
            out += """<p class='warning'>%s</p>""" % msg
        out += """
<form method="post" action="../youraccount/resetpassword?ln=%(ln)s">
<input type="hidden" name="k" value="%(reset_key)s" />
<input type="hidden" name="e" value="%(email)s" />
<input type="hidden" name="reset" value="1" />
<table>
<tr><td align="right"><strong>%(set_password_for)s</strong>:</td><td><em>%(email)s</em></td></tr>
<tr><td align="right"><strong><label for="password">%(type_new_password)s:</label></strong></td>
<td><input type="password" name="password" id="password" value="123" /></td></tr>
<tr><td align="right"><strong><label for="password2">%(type_it_again)s:</label></strong></td>
<td><input type="password" name="password2" id="password2" value="" /></td></tr>
<tr><td align="center" colspan="2">
<input class="formbutton" type="submit" name="action" value="%(set_new_password)s" />
</td></tr>
</table>
</form>""" % {
            'ln' : ln,
            'reset_key' : reset_key,
            'email' : email,
            'set_password_for' : _('Set a new password for'),
            'type_new_password' : _('Type the new password'),
            'type_it_again' : _('Type again the new password'),
            'set_new_password' : _('Set the new password')
        }
        return out

    def tmpl_register_page(self, ln, referer, level):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'level' *int* - Login level (0 - all access, 1 - accounts activated, 2+ - no self-registration)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if level <= 1:
            out += _("Please enter your email address and desired nickname and password:")
            if level == 1:
                out += _("It will not be possible to use the account before it has been verified and activated.")
            out += """
              <form method="post" action="../youraccount/register">
              <input type="hidden" name="referer" value="%(referer)s" />
              <input type="hidden" name="ln" value="%(ln)s" />
              <table>
                <tr>
                 <td align="right"><strong><label for="p_email">%(email_address)s:</label></strong><br /><small class="important">(%(mandatory)s)</small></td>
                 <td><input type="text" size="25" name="p_email" id="p_email" value="" /><br />
                     <small><span class="quicknote">%(example)s:</span>
                     <span class="example">john.doe@example.com</span></small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong><label for="p_nickname">%(nickname)s:</label></strong><br /><small class="important">(%(mandatory)s)</small></td>
                 <td><input type="text" size="25" name="p_nickname" id="p_nickname" value="" /><br />
                     <small><span class="quicknote">%(example)s:</span>
                     <span class="example">johnd</span></small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong><label for="p_pw">%(password)s:</label></strong><br /><small class="quicknote">(%(optional)s)</small></td>
                 <td align="left"><input type="password" size="25" name="p_pw" id="p_pw" value="" /><br />
                    <small><span class="quicknote">%(note)s:</span> %(password_contain)s</small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong><label for="p_pw2">%(retype)s:</label></strong></td>
                 <td align="left"><input type="password" size="25" name="p_pw2" id="p_pw2" value="" /></td>
                 <td></td>
                </tr>
                <tr>
                 <td></td>
                 <td align="left" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(register)s" /></code></td>
                </tr>
              </table>
              </form>
              <p><strong>%(note)s:</strong> %(explain_acc)s""" % {
                'referer' : cgi.escape(referer),
                'ln' : cgi.escape(ln),
                'email_address' : _("Email address"),
                'nickname' : _("Nickname"),
                'password' : _("Password"),
                'mandatory' : _("mandatory"),
                'optional' : _("optional"),
                'example' : _("Example"),
                'note' : _("Note"),
                'password_contain' : _("The password phrase may contain punctuation, spaces, etc."),
                'retype' : _("Retype Password"),
                'register' : _("register"),
                'explain_acc' : _("Please do not use valuable passwords such as your Unix, AFS or NICE passwords with this service. Your email address will stay strictly confidential and will not be disclosed to any third party. It will be used to identify you for personal services of %s. For example, you may set up an automatic alert search that will look for new preprints and will notify you daily of new arrivals by email.") % CFG_SITE_NAME,
              }
        else:
            # level >=2, so users cannot register accounts
            out += "<p>" + _("It is not possible to create an account yourself. Contact %s if you want an account.") % ('<a href="mailto:%s">%s</a>' % (CFG_SITE_SUPPORT_EMAIL, CFG_SITE_SUPPORT_EMAIL)) + "</p>"
        return out

    def tmpl_account_adminactivities(self, ln, uid, guest, roles, activities):
        """
        Displays the admin activities block for this user

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'uid' *string* - The used id

          - 'guest' *boolean* - If the user is guest

          - 'roles' *array* - The current user roles

          - 'activities' *array* - The user allowed activities
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # guest condition
        if guest:
            return _("You seem to be a guest user. You have to %(x_url_open)slogin%(x_url_close)s first.") % \
                        {'x_url_open': '<a href="../youraccount/login?ln=' + ln + '">',
                         'x_url_close': '<a/>'}

        # no rights condition
        if not roles:
            return "<p>" + _("You are not authorized to access administrative functions.") + "</p>"

        # displaying form
        out += "<p>" + _("You are enabled to the following roles: %(x_role)s.") % {'x_role': ('<em>' + ", ".join(roles) + "</em>")} + '</p>'

        if activities:
            # print proposed links:
            activities.sort(lambda x, y: cmp(x.lower(), y.lower()))
            tmp_out = ''
            for action in activities:
                if action == "runbibedit":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/%s/edit/">%s</a>""" % (CFG_SITE_URL, CFG_SITE_RECORD, _("Run Record Editor"))
                if action == "runbibeditmulti":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/%s/multiedit/">%s</a>""" % (CFG_SITE_URL, CFG_SITE_RECORD, _("Run Multi-Record Editor"))
                if action == "runbibcirculation":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibcirculation/bibcirculationadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Run BibCirculation"))
                if action == "runbibmerge":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/%s/merge/">%s</a>""" % (CFG_SITE_URL, CFG_SITE_RECORD, _("Run Record Merger"))
                if action == "runbibswordclient":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/%s/bibsword/">%s</a>""" % (CFG_SITE_URL, CFG_SITE_RECORD, _("Run BibSword Client"))
                if action == "runbatchuploader":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/batchuploader/metadata?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Run Batch Uploader"))
                if action == "cfgbibformat":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibformat/bibformatadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure BibFormat"))
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/kb?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure BibKnowledge"))
                if action == "cfgoaiharvest":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibharvest/oaiharvestadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure OAI Harvest"))
                if action == "cfgoairepository":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibharvest/oairepositoryadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln,  _("Configure OAI Repository"))
                if action == "cfgbibindex":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibindex/bibindexadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure BibIndex"))
                if action == "cfgbibrank":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibrank/bibrankadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure BibRank"))
                if action == "cfgwebaccess":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/webaccess/webaccessadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure WebAccess"))
                if action == "cfgwebcomment":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/webcomment/webcommentadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure WebComment"))
                if action == "cfgwebjournal":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/webjournal/webjournaladmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure WebJournal"))
                if action == "cfgwebsearch":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/websearch/websearchadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure WebSearch"))
                if action == "cfgwebsubmit":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/websubmit/websubmitadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure WebSubmit"))
                if action == "runbibdocfile":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/submit/managedocfiles?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Run Document File Manager"))
                if action == "cfgbibsort":
                    tmp_out += """<br />&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibsort/bibsortadmin.py?ln=%s">%s</a>""" % (CFG_SITE_URL, ln, _("Configure BibSort"))
            if tmp_out:
                out += _("Here are some interesting web admin links for you:") + tmp_out

                out += "<br />" + _("For more admin-level activities, see the complete %(x_url_open)sAdmin Area%(x_url_close)s.") %\
                {'x_url_open': '<a href="' + CFG_SITE_URL + '/help/admin?ln=' + ln + '">',
                    'x_url_close': '</a>'}
        return out

    def tmpl_create_userinfobox(self, ln, url_referer, guest, username, submitter, referee, admin, usebaskets, usemessages, usealerts, usegroups, useloans, usestats):
        """
        Displays the user block

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'url_referer' *string* - URL of the page being displayed

          - 'guest' *boolean* - If the user is guest

          - 'username' *string* - The username (nickname or email)

          - 'submitter' *boolean* - If the user is submitter

          - 'referee' *boolean* - If the user is referee

          - 'admin' *boolean* - If the user is admin

          - 'usebaskets' *boolean* - If baskets are enabled for the user

          - 'usemessages' *boolean* - If messages are enabled for the user

          - 'usealerts' *boolean* - If alerts are enabled for the user

          - 'usegroups' *boolean* - If groups are enabled for the user

          - 'useloans' *boolean* - If loans are enabled for the user

          - 'usestats' *boolean* - If stats are enabled for the user

        @note: with the update of CSS classes (cds.cds ->
            invenio.css), the variables useloans etc are not used in
            this function, since they are in the menus.  But we keep
            them in the function signature for backwards
            compatibility.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<img src="%s/img/user-icon-1-20x20.gif" border="0" alt=""/> """ % CFG_SITE_URL
        if guest:
            out += """%(guest_msg)s ::
                   <a class="userinfo" href="%(sitesecureurl)s/youraccount/login?ln=%(ln)s%(referer)s">%(login)s</a>""" % {
                     'sitesecureurl': CFG_SITE_SECURE_URL,
                     'ln' : ln,
                     'guest_msg' : _("guest"),
                     'referer' : url_referer and ('&amp;referer=%s' % urllib.quote(url_referer)) or '',
                     'login' : _('login')
                   }
        else:
            out += """
               <a class="userinfo" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(username)s</a> :: """ % {
                    'sitesecureurl' : CFG_SITE_SECURE_URL,
                    'ln' : ln,
                    'username' : username
               }
            out += """<a class="userinfo" href="%(sitesecureurl)s/youraccount/logout?ln=%(ln)s">%(logout)s</a>""" % {
                    'sitesecureurl' : CFG_SITE_SECURE_URL,
                    'ln' : ln,
                    'logout' : _("logout"),
                }
        return out

    def tmpl_create_useractivities_menu(self, ln, selected, url_referer, guest, username, submitter, referee, admin, usebaskets, usemessages, usealerts, usegroups, useloans, usestats):
        """
        Returns the main navigation menu with actions based on user's
        priviledges

        @param ln:          The language to display the interface in
        @type ln:           string
        @param selected:    If the menu is currently selected
        @type selected:     boolean
        @param url_referer: URL of the page being displayed
        @type url_referer:  string
        @param guest:       If the user is guest
        @type guest:        string
        @param username:    The username (nickname or email)
        @type username:     string
        @param submitter:   If the user is submitter
        @type submitter:    boolean
        @param referee:     If the user is referee
        @type referee:      boolean
        @param admin:       If the user is admin
        @type admin:        boolean
        @param usebaskets:  If baskets are enabled for the user
        @type usebaskets:   boolean
        @param usemessages: If messages are enabled for the user
        @type usemessages:  boolean
        @param usealerts:   If alerts are enabled for the user
        @type usealerts:    boolean
        @param usegroups:   If groups are enabled for the user
        @type usegroups:    boolean
        @param useloans:    If loans are enabled for the user
        @type useloans:     boolean
        @param usestats:    If stats are enabled for the user
        @type usestats:     boolean
        @return: html menu of the user activities
        @rtype: string
        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = '''<div class="hassubmenu%(on)s">
        <a hreflang="en" class="header%(selected)s" href="%(CFG_SITE_SECURE_URL)s/youraccount/display?ln=%(ln)s">%(personalize)s</a>
        <ul class="subsubmenu">''' % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'personalize': _("Personalize"),
                'on': selected and " on" or '',
                'selected': selected and "selected" or ''
                }
        if not guest:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/youraccount/display?ln=%(ln)s">%(account)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'account' : _('Your account')
                }
        if usealerts or guest:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/youralerts/list?ln=%(ln)s">%(alerts)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'alerts' : _('Your alerts')
                }
        if referee:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yourapprovals.py?ln=%(ln)s">%(approvals)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'approvals' : _('Your approvals')
                }
        if usebaskets or guest:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yourbaskets/display?ln=%(ln)s">%(baskets)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'baskets' : _('Your baskets')
                }
        if usegroups:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yourgroups/display?ln=%(ln)s">%(groups)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'groups' : _('Your groups')
                }
        if useloans:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yourloans/display?ln=%(ln)s">%(loans)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'loans' : _('Your loans')
                }
        if usemessages:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yourmessages/display?ln=%(ln)s">%(messages)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'messages' : _('Your messages')
                }
        if submitter:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/yoursubmissions.py?ln=%(ln)s">%(submissions)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'submissions' : _('Your submissions')
                }
        if usealerts or guest:
            out += '<li><a href="%(CFG_SITE_SECURE_URL)s/youralerts/display?ln=%(ln)s">%(searches)s</a></li>'  % {
                'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
                'ln' : ln,
                'searches' : _('Your searches')
                }
        out += '</ul></div>'
        return out

    def tmpl_create_adminactivities_menu(self, ln, selected, url_referer, guest, username, submitter, referee, admin, usebaskets, usemessages, usealerts, usegroups, useloans, usestats, activities):
        """
        Returns the main navigation menu with actions based on user's
        priviledges

        @param ln:          The language to display the interface in
        @type ln:           string
        @param selected:    If the menu is currently selected
        @type selected:     boolean
        @param url_referer: URL of the page being displayed
        @type url_referer:  string
        @param guest:       If the user is guest
        @type guest:        string
        @param username:    The username (nickname or email)
        @type username:     string
        @param submitter:   If the user is submitter
        @type submitter:    boolean
        @param referee:     If the user is referee
        @type referee:      boolean
        @param admin:       If the user is admin
        @type admin:        boolean
        @param usebaskets:  If baskets are enabled for the user
        @type usebaskets:   boolean
        @param usemessages: If messages are enabled for the user
        @type usemessages:  boolean
        @param usealerts:   If alerts are enabled for the user
        @type usealerts:    boolean
        @param usegroups:   If groups are enabled for the user
        @type usegroups:    boolean
        @param useloans:    If loans are enabled for the user
        @type useloans:     boolean
        @param usestats:    If stats are enabled for the user
        @type usestats:     boolean
        @param activities: dictionary of admin activities
        @rtype activities: dict
        @return: html menu of the user activities
        @rtype: string
        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''
        if activities:
            out += '''<div class="hassubmenu%(on)s">
            <a hreflang="en" class="header%(selected)s" href="%(CFG_SITE_SECURE_URL)s/youraccount/youradminactivities?ln=%(ln)s">%(admin)s</a>
            <ul class="subsubmenu">''' % {
            'CFG_SITE_SECURE_URL' : CFG_SITE_SECURE_URL,
            'ln' : ln,
            'admin': _("Administration"),
            'on': selected and " on" or '',
            'selected': selected and "selected" or ''
            }

            for name in sorted(activities.iterkeys()):
                url = activities[name]
                out += '<li><a href="%(url)s">%(name)s</a></li>'  % {
                    'url': url,
                    'name': name
                    }

        if usestats:
            out += """<li><a href="%(CFG_SITE_URL)s/stats/?ln=%(ln)s">%(stats)s</a></li>""" % {
                'CFG_SITE_URL' : CFG_SITE_URL,
                'ln' : ln,
                'stats' : _("Statistics"),
                }

            out += '</ul></div>'
        return out

    def tmpl_warning(self, warnings, ln=CFG_SITE_LANG):
        """
        Display len(warnings) warning fields
        @param infos: list of strings
        @param ln=language
        @return: html output
        """
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

    def tmpl_display_all_groups(self,
                                infos,
                                admin_group_html,
                                member_group_html,
                                external_group_html = None,
                                warnings=[],
                                ln=CFG_SITE_LANG):
        """
        Displays the 3 tables of groups: admin, member and external

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'admin_group_html' *string* - HTML code for displaying all the groups
          the user is the administrator of

          - 'member_group_html' *string* - HTML code for displaying all the groups
          the user is member of

          - 'external_group_html' *string* - HTML code for displaying all the
          external groups the user is member of

        """

        _ = gettext_set_language(ln)
        group_text = self.tmpl_infobox(infos)
        group_text += self.tmpl_warning(warnings)
        if external_group_html:
            group_text += """
<table>
<tr>
    <td>%s</td>
</tr>
<tr>
    <td><br />%s</td>
</tr>
<tr>
    <td><br /><a name='external_groups'></a>%s</td>
</tr>
</table>""" %(admin_group_html, member_group_html, external_group_html)
        else:
            group_text += """
<table>
<tr>
    <td>%s</td>
</tr>
<tr>
    <td><br />%s</td>
</tr>
</table>""" %(admin_group_html, member_group_html)
        return group_text


    def tmpl_display_admin_groups(self, groups, ln=CFG_SITE_LANG):
        """
        Display the groups the user is admin of.

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - All the group the user is admin of
        - 'infos' *list* - Display infos on top of admin group table
        """

        _ = gettext_set_language(ln)
        img_link = """
        <a href="%(siteurl)s/yourgroups/%(action)s?grpID=%(grpID)s&amp;ln=%(ln)s">
        <img src="%(siteurl)s/img/%(img)s" alt="%(text)s" style="border:0" width="25"
        height="25" /><br /><small>%(text)s</small>
        </a>"""


        out = self.tmpl_group_table_title(img="/img/group_admin.png",
                                          text=_("You are an administrator of the following groups:") )

        out += """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr class="inboxheader">
      <td>%s</td>
      <td>%s</td>
      <td style="width: 20px;" >&nbsp;</td>
      <td style="width: 20px;">&nbsp;</td>
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
  <tbody class="mailboxbody">""" %(_("Group"), _("Description"))
        if len(groups) == 0:
            out += """
    <tr class="mailboxrecord" style="height: 100px;">
      <td colspan="4" style="text-align: center;">
        <small>%s</small>
      </td>
    </tr>""" %(_("You are not an administrator of any groups."),)
        for group_data in groups:
            (grpID, name, description) = group_data
            edit_link = img_link % {'siteurl' : CFG_SITE_URL,
                                    'grpID' : grpID,
                                    'ln': ln,
                                    'img':"webbasket_create_small.png",
                                    'text':_("Edit group"),
                                    'action':"edit"
                                    }
            members_link = img_link % {'siteurl' : CFG_SITE_URL,
                                       'grpID' : grpID,
                                       'ln': ln,
                                       'img':"webbasket_usergroup.png",
                                       'text':_("Edit %s members") % '',
                                       'action':"members"
                                       }
            out += """
    <tr class="mailboxrecord">
      <td>%s</td>
      <td>%s</td>
      <td style="text-align: center;" >%s</td>
      <td style="text-align: center;" >%s</td>
    </tr>""" % (cgi.escape(name), cgi.escape(description), edit_link, members_link)
        out += """
    <tr class="mailboxfooter">
      <td colspan="2">
        <form name="newGroup" action="create?ln=%(ln)s" method="post">
          <input type="submit" name="create_group" value="%(write_label)s" class="formbutton" />
        </form>
      </td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
      <td>&nbsp;</td>
     </tr>
  </tbody>
</table>""" % {'ln': ln,
               'write_label': _("Create new group"),
               }
        return out

    def tmpl_display_member_groups(self, groups, ln=CFG_SITE_LANG):
        """
        Display the groups the user is member of.

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - All the group the user is member of
        """
        _ = gettext_set_language(ln)
        group_text = self.tmpl_group_table_title(img="/img/webbasket_us.png", text=_("You are a member of the following groups:"))

        group_text += """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr class="inboxheader">
      <td>%s</td>
      <td>%s</td>
    </tr>
  </thead>
  <tfoot>
    <tr style="height:0px;">
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">""" % (_("Group"), _("Description"))
        if len(groups) == 0:
            group_text += """
    <tr class="mailboxrecord" style="height: 100px;">
      <td colspan="2" style="text-align: center;">
        <small>%s</small>
      </td>
    </tr>""" %(_("You are not a member of any groups."),)
        for group_data in groups:
            (id, name, description) = group_data
            group_text += """
    <tr class="mailboxrecord">
      <td>%s</td>
      <td>%s</td>
    </tr>""" % (cgi.escape(name), cgi.escape(description))
        group_text += """
    <tr class="mailboxfooter">
      <td>
          <form name="newGroup" action="join?ln=%(ln)s" method="post">
           <input type="submit" name="join_group" value="%(join_label)s" class="formbutton" />
          </form>
        </td>
        <td>
         <form name="newGroup" action="leave?ln=%(ln)s" method="post">
          <input type="submit" name="leave" value="%(leave_label)s" class="formbutton" />
         </form>
        </td>
       </tr>
     </tbody>
</table>
 """ % {'ln': ln,
               'join_label': _("Join new group"),
               'leave_label':_("Leave group")
               }
        return group_text


    def tmpl_display_external_groups(self, groups, ln=CFG_SITE_LANG):
        """
        Display the external groups the user is member of.

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - All the group the user is member of
        """
        _ = gettext_set_language(ln)
        group_text = self.tmpl_group_table_title(img="/img/webbasket_us.png", text=_("You are a member of the following external groups:"))

        group_text += """
<table class="mailbox">
  <thead class="mailboxheader">
    <tr class="inboxheader">
      <td>%s</td>
      <td>%s</td>
    </tr>
  </thead>
  <tfoot>
    <tr style="height:0px;">
      <td></td>
      <td></td>
    </tr>
  </tfoot>
  <tbody class="mailboxbody">""" % (_("Group"), _("Description"))
        if len(groups) == 0:
            group_text += """
    <tr class="mailboxrecord" style="height: 100px;">
      <td colspan="2" style="text-align: center;">
        <small>%s</small>
      </td>
    </tr>""" %(_("You are not a member of any external groups."),)
        for group_data in groups:
            (id, name, description) = group_data
            group_text += """
    <tr class="mailboxrecord">
      <td>%s</td>
      <td>%s</td>
    </tr>""" % (cgi.escape(name), cgi.escape(description))
        group_text += """
  </tbody>
</table>
 """
        return group_text

    def tmpl_display_input_group_info(self,
                                      group_name,
                                      group_description,
                                      join_policy,
                                      act_type="create",
                                      grpID=None,
                                      warnings=[],
                                      ln=CFG_SITE_LANG):
        """
        Display group data when creating or updating a group:
        Name, description, join_policy.
        Parameters:
        - 'ln' *string* - The language to display the interface in
        - 'group_name' *string* - name of the group
        - 'group_description' *string* - description of the group
        - 'join_policy' *string* - join policy
        - 'act_type' *string* - info about action : create or edit(update)
        - 'grpID' *int* - ID of the group(not None in case of group editing)
        - 'warnings' *list* - Display warning if values are not correct

        """
        _ = gettext_set_language(ln)
        #default
        hidden_id =""
        form_name = "create_group"
        action = CFG_SITE_URL + '/yourgroups/create'
        button_label = _("Create new group")
        button_name = "create_button"
        label = _("Create new group")
        delete_text = ""

        if act_type == "update":
            form_name = "update_group"
            action = CFG_SITE_URL + '/yourgroups/edit'
            button_label = _("Update group")
            button_name = "update"
            label = _('Edit group %s') % cgi.escape(group_name)
            delete_text = """<input type="submit" value="%s" class="formbutton" name="%s" />"""
            delete_text %= (_("Delete group"),"delete")
            if grpID is not None:
                hidden_id = """<input type="hidden" name="grpID" value="%s" />"""
                hidden_id %= grpID

        out = self.tmpl_warning(warnings)
        out += """
<form name="%(form_name)s" action="%(action)s" method="post">
  <input type="hidden" name="ln" value="%(ln)s" />
  <div style="padding:10px;">
  <table class="bskbasket">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(logo)s" alt="%(label)s" />
        </td>
        <td class="bsktitle">
          <b>%(label)s</b><br />
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
              <td><label for="group_name">%(name_label)s</label></td>
              <td>
               <input type="text" name="group_name" id="group_name" value="%(group_name)s" />
              </td>
            </tr>
            <tr>
              <td><label for="group_description">%(description_label)s</label></td>
              <td>
               <input type="text" name="group_description" id="group_description" value="%(group_description)s" />
              </td>
            </tr>
            <tr>
              <td>%(join_policy_label)s</td>
              <td>
               %(join_policy)s
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </tbody>
  </table>
  %(hidden_id)s
  <table>
   <tr>
    <td>
     <input type="submit" value="%(button_label)s" class="formbutton" name="%(button_name)s" />
    </td>
    <td>
    %(delete_text)s
    </td>
    <td>
     <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel" />
    </td>
   </tr>
  </table>
  </div>
</form>

"""
        out %= {'action' : action,
                'logo': CFG_SITE_URL + '/img/webbasket_create.png',
                'label': label,
                'form_name' : form_name,
                'name_label': _("Group name:"),
                'delete_text': delete_text,
                'description_label': _("Group description:"),
                'join_policy_label': _("Group join policy:"),
                'group_name': cgi.escape(group_name, 1),
                'group_description': cgi.escape(group_description, 1),
                'button_label': button_label,
                'button_name':button_name,
                'cancel_label':_("Cancel"),
                'hidden_id':hidden_id,
                'ln': ln,
                'join_policy' :self.__create_join_policy_selection_menu("join_policy",
                                                                        join_policy,
                                                                        ln)
               }
        return out

    def tmpl_display_input_join_group(self,
                                      group_list,
                                      group_name,
                                      group_from_search,
                                      search,
                                      warnings=[],
                                      ln=CFG_SITE_LANG):

        """
        Display the groups the user can join.
        He can use default select list or the search box

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'group_list' *list* - All the group the user can join
        - 'group_name' *string* - Name of the group the user is looking for
        - 'group_from search' *list* - List of the group the user can join matching group_name
        - 'search' *int* - User is looking for group using group_name
        - 'warnings' *list* - Display warning if two group are selected
        """
        _ = gettext_set_language(ln)
        out = self.tmpl_warning(warnings)
        search_content = ""
        if search:
            search_content = """<tr><td>&nbsp;</td><td>"""
            if group_from_search != []:
                search_content += self.__create_select_menu('grpID', group_from_search, _("Please select:"))
            else:
                search_content += _("No matching group")

            search_content += """</td><td>&nbsp;</td></tr>"""

        out += """
<form name="join_group" action="%(action)s" method="post">
  <input type="hidden" name="ln" value="%(ln)s" />
  <div style="padding:10px;">
  <table class="bskbasket">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(logo)s" alt="%(label)s" />
        </td>
        <td class="bsktitle">
          <b>%(label)s</b><br />
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
              <td>%(list_label)s</td>
              <td>
               %(group_list)s
               </td>
              <td>
               &nbsp;
              </td>
            </tr>
            <tr>
              <td><br /><label for="group_name">%(label2)s</label></td>
              <td><br /><input type="text" name="group_name" id="group_name" value="%(group_name)s" /></td>
              <td><br />
               <input type="submit" name="find_button" value="%(find_label)s" class="nonsubmitbutton" />
              </td>
            </tr>
            %(search_content)s
          </table>
        </td>
      </tr>
    </tbody>
  </table>
  <table>
  <tr>
   <td>
    <input type="submit" name="join_button" value="%(label)s" class="formbutton" />
   </td>
   <td>
    <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel" />
   </td>
   </tr>
  </table>
 </div>
</form>

"""
        out %= {'action' : CFG_SITE_URL + '/yourgroups/join',
                'logo': CFG_SITE_URL + '/img/webbasket_create.png',
                'label': _("Join group"),
                'group_name': cgi.escape(group_name, 1),
                'label2':_("or find it") + ': ',
                'list_label':_("Choose group:"),
                'ln': ln,
                'find_label': _("Find group"),
                'cancel_label':_("Cancel"),
                'group_list' :self.__create_select_menu("grpID",group_list, _("Please select:")),
                'search_content' : search_content
               }
        return out

    def tmpl_display_manage_member(self,
                                   grpID,
                                   group_name,
                                   members,
                                   pending_members,
                                   infos=[],
                                   warnings=[],
                                   ln=CFG_SITE_LANG):
        """Display current members and waiting members of a group.

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'grpID *int* - ID of the group
        - 'group_name' *string* - Name of the group
        - 'members' *list* - List of the current members
        - 'pending_members' *list* - List of the waiting members
        - 'infos' *tuple of 2 lists* - Message to inform user about his last action
        - 'warnings' *list* - Display warning if two group are selected
        """

        _ = gettext_set_language(ln)
        out = self.tmpl_warning(warnings)
        out += self.tmpl_infobox(infos)
        out += """
<form name="member" action="%(action)s" method="post">
 <p>%(title)s</p>
 <input type="hidden" name="ln" value="%(ln)s" />
 <input type="hidden" name="grpID" value="%(grpID)s"/>
 <table>
   <tr>
   <td>
    <table class="bskbasket">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(imgurl)s/webbasket_usergroup.png" alt="%(img_alt_header1)s" />
        </td>

        <td class="bsktitle">
          %(header1)s<br />
          &nbsp;
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
            %(member_text)s
            </tr>
          </table>
        </td>
      </tr>
    </tbody>
  </table>
 </td>
 </tr>
 <tr>
  <td>
   <table class="bskbasket">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(imgurl)s/webbasket_usergroup_gray.png" alt="%(img_alt_header2)s" />
        </td>

        <td class="bsktitle">
          %(header2)s<br />
          &nbsp;
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
             %(pending_text)s
            </tr>
          </table>
          </td>
      </tr>
    </tbody>
  </table>
 </td>
 </tr>
 <tr>
  <td>
  <table class="bskbasket" style="width: 400px">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(imgurl)s/iconpen.gif" alt="%(img_alt_header3)s" />
        </td>

        <td class="bsktitle">
          <b>%(header3)s</b><br />
          &nbsp;
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
             <td colspan="2" style="padding: 0 5 10 5;">%(invite_text)s</td>
            </tr>
          </table>
        </td>
      </tr>
    </tbody>
  </table>
 </td>
</tr>
<tr>
 <td>
  <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel" />
 </td>
</tr>
</table>
</form>
"""

        if members :
            member_list =   self.__create_select_menu("member_id", members, _("Please select:"))
            member_text = """
            <td style="padding: 0 5 10 5;">%s</td>
            <td style="padding: 0 5 10 5;">
            <input type="submit" name="remove_member" value="%s" class="nonsubmitbutton"/>
            </td>""" %  (member_list,_("Remove member"))
        else :
            member_text = """<td style="padding: 0 5 10 5;" colspan="2">%s</td>""" % _("No members.")
        if pending_members :
            pending_list =   self.__create_select_menu("pending_member_id", pending_members, _("Please select:"))
            pending_text = """
            <td style="padding: 0 5 10 5;">%s</td>
            <td style="padding: 0 5 10 5;">
            <input type="submit" name="add_member" value="%s" class="nonsubmitbutton"/>
            </td>
            <td style="padding: 0 5 10 5;">
            <input type="submit" name="reject_member" value="%s" class="nonsubmitbutton"/>
            </td>""" %  (pending_list,_("Accept member"), _("Reject member"))
        else :
            pending_text = """<td style="padding: 0 5 10 5;" colspan="2">%s</td>""" % _("No members awaiting approval.")

        header1 = self.tmpl_group_table_title(text=_("Current members"))
        header2 = self.tmpl_group_table_title(text=_("Members awaiting approval"))
        header3 = _("Invite new members")
        write_a_message_url = create_url(
            "%s/yourmessages/write" % CFG_SITE_URL,
            {
                'ln' : ln,
                'msg_subject' : _('Invitation to join "%s" group' % escape_html(group_name)),
                'msg_body' : _("""\
Hello:

I think you might be interested in joining the group "%(x_name)s".
You can join by clicking here: %(x_url)s.

Best regards.
""") % {'x_name': group_name,
        'x_url': create_html_link("%s/yourgroups/join" % CFG_SITE_URL, { 'grpID' : grpID,
                                                                'join_button' : "1",
                                                                },
                         link_label=group_name, escape_urlargd=True, escape_linkattrd=True)}})

        link_open = '<a href="%s">' % escape_html(write_a_message_url)
        invite_text = _("If you want to invite new members to join your group, please use the %(x_url_open)sweb message%(x_url_close)s system.") % \
            {'x_url_open': link_open,
             'x_url_close': '</a>'}
        action = CFG_SITE_URL + '/yourgroups/members?ln=' + ln
        out %= {'title':_('Group: %s') % escape_html(group_name),
                'member_text' : member_text,
                'pending_text' :pending_text,
                'action':action,
                'grpID':grpID,
                'header1': header1,
                'header2': header2,
                'header3': header3,
                'img_alt_header1': _("Current members"),
                'img_alt_header2': _("Members awaiting approval"),
                'img_alt_header3': _("Invite new members"),
                'invite_text': invite_text,
                'imgurl': CFG_SITE_URL + '/img',
                'cancel_label':_("Cancel"),
                'ln':ln
                }
        return out

    def tmpl_display_input_leave_group(self,
                                       groups,
                                       warnings=[],
                                       ln=CFG_SITE_LANG):
        """Display groups the user can leave.

        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - List of groups the user is currently member of
        - 'warnings' *list* - Display warning if no group is selected
        """
        _ = gettext_set_language(ln)
        out = self.tmpl_warning(warnings)
        out += """
<form name="leave" action="%(action)s" method="post">
 <input type="hidden" name="ln" value="%(ln)s" />
  <div style="padding:10px;">
  <table class="bskbasket">
    <thead class="bskbasketheader">
      <tr>
        <td class="bskactions">
          <img src="%(logo)s" alt="%(label)s" />
        </td>
        <td class="bsktitle">
          <b>%(label)s</b><br />
        </td>
      </tr>
    </thead>
    <tfoot>
       <tr><td colspan="2"></td></tr>
    </tfoot>
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
              <td>%(list_label)s</td>
              <td>
               %(groups)s
               </td>
              <td>
               &nbsp;
              </td>
            </tr>
           </table>
        </td>
      </tr>
    </tbody>
  </table>
  <table>
  <tr>
   <td>
    %(submit)s
   </td>
   <td>
    <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel" />
   </td>
   </tr>
  </table>
 </div>
</form>
 """
        if groups:
            groups =   self.__create_select_menu("grpID", groups, _("Please select:"))
            list_label = _("Group list")
            submit = """<input type="submit" name="leave_button" value="%s" class="formbutton"/>""" % _("Leave group")
        else :
            groups = _("You are not member of any group.")
            list_label = ""
            submit = ""
        action = CFG_SITE_URL + '/yourgroups/leave?ln=%s'
        action %= (ln)
        out %= {'groups' : groups,
                'list_label' : list_label,
                'action':action,
                'logo': CFG_SITE_URL + '/img/webbasket_create.png',
                'label' : _("Leave group"),
                'cancel_label':_("Cancel"),
                'ln' :ln,
                'submit' : submit
                }
        return out


    def tmpl_confirm_delete(self, grpID, ln=CFG_SITE_LANG):
        """
        display a confirm message when deleting a group
        @param grpID *int* - ID of the group
        @param ln: language
        @return: html output
        """
        _ = gettext_set_language(ln)
        action = CFG_SITE_URL + '/yourgroups/edit'
        out = """
<form name="delete_group" action="%(action)s" method="post">
<table class="confirmoperation">
  <tr>
    <td colspan="2" class="confirmmessage">
      %(message)s
    </td>
  </tr>
  <tr>
    <td>
        <input type="hidden" name="confirmed" value="1" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="grpID" value="%(grpID)s" />
        <input type="submit" name="delete" value="%(yes_label)s" class="formbutton" />
    </td>
    <td>
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="grpID" value="%(grpID)s" />
        <input type="submit" value="%(no_label)s" class="formbutton" />
    </td>
  </tr>
</table>
</form>"""% {'message': _("Are you sure you want to delete this group?"),
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("No"),
              'grpID':grpID,
              'action': action
              }
        return out

    def tmpl_confirm_leave(self, uid, grpID, ln=CFG_SITE_LANG):
        """
        display a confirm message
        @param grpID *int* - ID of the group
        @param ln: language
        @return: html output
        """
        _ = gettext_set_language(ln)
        action = CFG_SITE_URL + '/yourgroups/leave'
        out = """
<form name="leave_group" action="%(action)s" method="post">
<table class="confirmoperation">
  <tr>
    <td colspan="2" class="confirmmessage">
      %(message)s
    </td>
  </tr>
  <tr>
    <td>
        <input type="hidden" name="confirmed" value="1" />
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="grpID" value="%(grpID)s" />
        <input type="submit" name="leave_button" value="%(yes_label)s" class="formbutton" />
    </td>
    <td>
        <input type="hidden" name="ln" value="%(ln)s" />
        <input type="hidden" name="grpID" value="%(grpID)s" />
        <input type="submit" value="%(no_label)s" class="formbutton" />
    </td>
  </tr>
</table>
</form>"""% {'message': _("Are you sure you want to leave this group?"),
              'ln':ln,
              'yes_label': _("Yes"),
              'no_label': _("No"),
              'grpID':grpID,
              'action': action
              }
        return out

    def __create_join_policy_selection_menu(self, name, current_join_policy, ln=CFG_SITE_LANG):
        """Private function. create a drop down menu for selection of join policy
        @param current_join_policy: join policy as defined in CFG_WEBSESSION_GROUP_JOIN_POLICY
        @param ln: language
        """
        _ = gettext_set_language(ln)
        elements = [(CFG_WEBSESSION_GROUP_JOIN_POLICY['VISIBLEOPEN'],
                     _("Visible and open for new members")),
                    (CFG_WEBSESSION_GROUP_JOIN_POLICY['VISIBLEMAIL'],
                     _("Visible but new members need approval"))
                    ]
        select_text = _("Please select:")
        return self.__create_select_menu(name, elements, select_text, selected_key=current_join_policy)

    def __create_select_menu(self, name, elements, select_text, multiple=0, selected_key=None):
        """ private function, returns a popup menu
        @param name: name of HTML control
        @param elements: list of (key, value)
        """
        if multiple :
            out = """
<select name="%s" multiple="multiple" style="width:100%%">"""% (name)
        else :
            out = """<select name="%s" style="width:100%%">""" % name
        out += '<option value="-1">%s</option>' % (select_text)
        for (key, label) in elements:
            selected = ''
            if key == selected_key:
                selected = ' selected="selected"'
            out += '<option value="%s"%s>%s</option>'% (key, selected, label)
        out += '</select>'
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
            infobox += '<div><span class="info">'
            lines = info.split("\n")
            for line in lines[0:-1]:
                infobox += line + "<br />\n"
            infobox += lines[-1] + "</span></div>\n"
        return infobox

    def tmpl_navtrail(self, ln=CFG_SITE_LANG, title=""):
        """
        display the navtrail, e.g.:
        Your account > Your group > title
        @param title: the last part of the navtrail. Is not a link
        @param ln: language
        return html formatted navtrail
        """
        _ = gettext_set_language(ln)
        nav_h1 = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
        nav_h2 = ""
        if (title != ""):
            nav_h2 = ' &gt; <a class="navtrail" href="%s/yourgroups/display">%s</a>'
            nav_h2 = nav_h2 % (CFG_SITE_URL, _("Your Groups"))

        return  nav_h1 % (CFG_SITE_URL, _("Your Account")) + nav_h2

    def tmpl_group_table_title(self, img="", text="", ln=CFG_SITE_LANG):
        """
        display the title of a table:
        - 'img' *string* - img path
        - 'text' *string* - title
        - 'ln' *string* - The language to display the interface in
        """
        out = "<div>"
        if img:
            out += """
            <img src="%s" alt="" />
            """ % (CFG_SITE_URL + img)
        out += """
        <b>%s</b>
        </div>""" % text
        return out

    def tmpl_admin_msg(self, group_name, grpID, ln=CFG_SITE_LANG):
        """
        return message content for joining group
        - 'group_name' *string* - name of the group
        - 'grpID' *int* - ID of the group
        - 'ln' *string* - The language to display the interface in
        """
        _ = gettext_set_language(ln)
        subject = _("Group %s: New membership request") % group_name
        url = CFG_SITE_URL + "/yourgroups/members?grpID=%s&ln=%s"
        url %= (grpID, ln)
        # FIXME: which user?  We should show his nickname.
        body = (_("A user wants to join the group %s.") % group_name) + '<br />'
        body += _("Please %(x_url_open)saccept or reject%(x_url_close)s this user's request.") % {'x_url_open': '<a href="' + url + '">',
                                                                                                  'x_url_close': '</a>'}
        body += '<br />'
        return subject, body

    def tmpl_member_msg(self,
                        group_name,
                        accepted=0,
                        ln=CFG_SITE_LANG):
        """
        return message content when new member is accepted/rejected
        - 'group_name' *string* - name of the group
        - 'accepted' *int* - 1 if new membership has been accepted, 0 if it has been rejected
        - 'ln' *string* - The language to display the interface in
        """
        _ = gettext_set_language(ln)
        if accepted:
            subject = _("Group %s: Join request has been accepted") % (group_name)
            body = _("Your request for joining group %s has been accepted.") % (group_name)
        else:
            subject = _("Group %s: Join request has been rejected") % (group_name)
            body = _("Your request for joining group %s has been rejected.") % (group_name)
        url = CFG_SITE_URL + "/yourgroups/display?ln=" + ln
        body += '<br />'
        body += _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s.") % {'x_url_open': '<a href="' + url + '">',
                                                                                              'x_url_close': '</a>'}
        body += '<br />'
        return subject, body

    def tmpl_delete_msg(self,
                        group_name,
                        ln=CFG_SITE_LANG):
        """
        return message content when new member is accepted/rejected
        - 'group_name' *string* - name of the group
        - 'ln' *string* - The language to display the interface in
        """
        _ = gettext_set_language(ln)
        subject = _("Group %s has been deleted") % group_name
        url = CFG_SITE_URL + "/yourgroups/display?ln=" + ln
        body = _("Group %s has been deleted by its administrator.") % group_name
        body += '<br />'
        body += _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s.") % {'x_url_open': '<a href="' + url + '">',
                                                                                              'x_url_close': '</a>'}
        body += '<br />'
        return subject, body

    def tmpl_group_info(self, nb_admin_groups=0, nb_member_groups=0, nb_total_groups=0, ln=CFG_SITE_LANG):
        """
        display infos about groups (used by myaccount.py)
        @param nb_admin_group: number of groups the user is admin of
        @param nb_member_group: number of groups the user is member of
        @param total_group: number of groups the user belongs to
        @param ln: language
        return: html output.
        """
        _ = gettext_set_language(ln)
        out = _("You can consult the list of %(x_url_open)s%(x_nb_total)i groups%(x_url_close)s you are subscribed to (%(x_nb_member)i) or administering (%(x_nb_admin)i).")
        out %= {'x_url_open': '<a href="' + CFG_SITE_URL + '/yourgroups/display?ln=' + ln + '">',
                'x_nb_total': nb_total_groups,
                'x_url_close': '</a>',
                'x_nb_admin': nb_admin_groups,
                'x_nb_member': nb_member_groups}
        return out

    def tmpl_general_warnings(self, warning_list, ln=CFG_SITE_LANG):
        """
        display information to the admin user about possible
        ssecurity problems in the system.
        """
        message = ""
        _ = gettext_set_language(ln)

        #Try and connect to the mysql database with the default invenio password
        if "warning_mysql_password_equal_to_invenio_password" in warning_list:
            message += "<p><font color=red>"
            message += _("Warning: The password set for MySQL root user is the same as the default Invenio password. For security purposes, you may want to change the password.")
            message += "</font></p>"

        #Try and connect to the invenio database with the default invenio password
        if "warning_invenio_password_equal_to_default" in warning_list:
            message += "<p><font color=red>"
            message += _("Warning: The password set for the Invenio MySQL user is the same as the shipped default. For security purposes, you may want to change the password.")
            message += "</font></p>"

        #Check if the admin password is empty
        if "warning_empty_admin_password" in warning_list:
            message += "<p><font color=red>"
            message += _("Warning: The password set for the Invenio admin user is currently empty. For security purposes, it is strongly recommended that you add a password.")
            message += "</font></p>"

        #Check if the admin email has been changed from the default
        if "warning_site_support_email_equal_to_default" in warning_list:
            message += "<p><font color=red>"
            message += _("Warning: The email address set for support email is currently set to info@invenio-software.org. It is recommended that you change this to your own address.")
            message += "</font></p>"

        #Check for a new release
        if "note_new_release_available" in warning_list:
            message += "<p><font color=red>"
            message += _("A newer version of Invenio is available for download. You may want to visit  ")
            message += "<a href=\"http://invenio-software.org/wiki/Installation/Download\">http://invenio-software.org/wiki/Installation/Download</a>"
            message += "</font></p>"

        #Error downloading release notes
        if "error_cannot_download_release_notes" in warning_list:
            message += "<p><font color=red>"
            message += _("Cannot download or parse release notes from http://invenio-software.org/repo/invenio/tree/RELEASE-NOTES")
            message += "</font></p>"

        return message
