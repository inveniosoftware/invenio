## $Id$

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

__revision__ = "$Id$"

import urllib
import time
import cgi
import gettext
import string
import locale

from invenio.config import *
from invenio.messages import gettext_set_language
from invenio.textutils import indent_text
from invenio.websession_config import CFG_WEBSESSION_GROUP_JOIN_POLICY
class Template:
    def tmpl_lost_password_message(self, ln, supportemail):
        """
        Defines the text that will be displayed on the 'lost password' page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'supportemail' *string* - The email of the support team
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("If you have lost password for your CDS Invenio internal account, then please enter your email address below and the lost password will be emailed to you.") +\
               "<br /><br />" +\
               _("Note that if you have been using an external login system (such as CERN NICE), then we cannot do anything and you have to ask there.") +\
               _("Alternatively, you can ask %s to change your login system from external to internal.") % ("""<a href="mailto:%(email)s">%(email)s</a>""" % { 'email' : supportemail }) +\
               "<br><br>"

    def tmpl_back_form(self, ln, message, act, link):
        """
        A standard one-message-go-back-link page.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'message' *string* - The message to display

          - 'act' *string* - The action to accomplish when going back

          - 'link' *string* - The link text
        """
        out = """
                 <table>
                    <tr>
                      <td align=center>%(message)s
                       <a href="./%(act)s">%(link)s</a></td>
                    </tr>
                 </table>
             """% {
               'message' : message,
               'act'     : act,
               'link'    : link
             }

        return out

    def tmpl_user_preferences(self, ln, email, email_disabled, password, password_disabled, nickname):
        """
        Displays a form for the user to change his email/password.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'email' *string* - The email of the user

          - 'email_disabled' *boolean* - If the user has the right to edit his email

          - 'password' *string* - The password of the user

          - 'password_disabled' *boolean* - If the user has the right to edit his password

          - 'nickname' *string* - The nickname of the user (empty string if user does not have it)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
                <p><big><strong class="headline">%(edit_params)s</strong></big></p>
                <form method="post" action="%(sweburl)s/youraccount/change">
                <p>%(change_user_pass)s</p>
                <table>
                  <tr><td align="right"><strong>
                      %(nickname_label)s:</strong><br/>
                      <small class="important">(%(mandatory)s)</small>
                    </td><td>
                      %(nickname_prefix)s%(nickname)s%(nickname_suffix)s
                    </td>
                    <td></td>
                  </tr>
                  <tr><td align="right"><strong>
                      %(new_email)s:</strong><br/>
                      <small class="important">(%(mandatory)s)</small>
                    </td><td>
                      <input type="text" size="25" name="email" %(email_disabled)s value="%(email)s"><br>
                      <small><span class="quicknote">%(example)s:</span>
                        <span class="example">john.doe@example.com</span>
                      </small>
                    </td>
                    <td></td>
                  </tr>
                  <tr>
                    <td align="right"><strong>%(new_password)s:</strong><br>
                      <small class="quicknote">(%(optional)s)</small>
                    </td><td align="left">
                      <input type="password" size="25" name="password" %(password_disabled)s value="%(password)s"><br>
                      <small><span class=quicknote>%(note)s:</span>
                       %(password_note)s
                      </small>
                    </td>
                  </tr>
                  <tr>
                    <td align="right"><strong>%(retype_password)s:</strong></td>
                    <td align="left">
                      <input type="password" size="25" name="password2" %(password_disabled)s value="">
                    </td>
                    <td><input type="hidden" name="action" value="edit"></td>
                  </tr>
                  <tr><td align="center" colspan="3">
                    <code class="blocknote"><input class="formbutton" type="submit" value="%(set_values)s"></code>&nbsp;&nbsp;&nbsp;
                  </td></tr>
                </table>
              </form>
        """ % {
          'change_user_pass' : _("If you want to change your email address or password, please set new values in the form below."),
          'edit_params' : _("Edit parameters"),
          'nickname_label' : _("Nickname"),
          'nickname' : nickname,
          'nickname_prefix' : nickname=='' and '<input type="text" size="25" name="nickname" value=""' or '',
          'nickname_suffix' : nickname=='' and '"><br><small><span class="quicknote">'+_("Example")+':</span><span class="example">johnd</span></small>' or '',
          'new_email' : _("New email address"),
          'mandatory' : _("mandatory"),
          'example' : _("Example"),
          'new_password' : _("New password"),
          'optional' : _("optional"),
          'note' : _("Note"),
          'password_note' : _("The password phrase may contain punctuation, spaces, etc."),
          'retype_password' : _("Retype password"),
          'set_values' : _("Set new values"),

          'email' : email,
          'email_disabled' : email_disabled and "disabled" or "",
          'password' : password,
          'password_disabled' : password_disabled and "disabled" or "",
          'sweburl': sweburl,
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
                 <form method="post" action="%(sweburl)s/youraccount/change">
                   <big><strong class="headline">%(edit_method)s</strong></big>
                   <p>%(explain_method)s:</p>
                   <table>
                     <tr><td valign="top"><b>%(select_method)s:</b></td><td>
               """ % {
                 'edit_method' : _("Edit login method"),
                 'explain_method' : _("Please select which login method you would like to use to authenticate yourself"),
                 'select_method' : _("Select method"),
                 'sweburl': sweburl,
               }
        for system in methods:
            out += """<input type="radio" name="login_method" value="%(system)s" %(disabled)s %(selected)s>%(system)s<br>""" % {
                     'system' : system,
                     'disabled' : method_disabled and "disabled" or "",
                     'selected' : current == system and "disabled" or "",
                   }
        out += """  </td><td></td></tr>
                   <tr><td></td>
                     <td><input class="formbutton" type="submit" value="%(select_method)s"></td></tr></table>
                    </form>""" % {
                     'select_method' : _("Select method"),
                   }

        return out

    def tmpl_lost_password_form(self, ln, msg):
        """
        Displays a form for the user to ask for his password sent by email.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - Explicative message on top of the form.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
          <form  method="post" action="../youraccount/send_email">
            %(msg)s
          <table>
                <tr>
              <td align="right"><strong>%(email)s:</strong></td>
              <td><input type="text" size="25" name="p_email" value=""></td>
              <td><input type="hidden" name="action" value="lost"></td>
            </tr>
            <tr><td></td>
              <td><code class="blocknote"><input class="formbutton" type="submit" value="%(send)s"></code></td>
            </tr>
          </table>

          </form>
          """ % {
            'msg' : msg,
            'email' : _("Email address"),
            'send' : _("Send lost password"),
          }
        return out

    def tmpl_account_info(self, ln, uid, guest, cfg_cern_site):
        """
        Displays the account information

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'uid' *string* - The user id

          - 'guest' *boolean* - If the user is guest

          - 'cfg_cern_site' *boolean* - If the site is a CERN site
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<p>%(account_offer)s</p>
                 <blockquote>
                 <dl>
              """ % {
                'account_offer' : _("%s offers you the possibility to personalize the interface, to set up your own personal library of documents, or to set up an automatic alert query that would run periodically and would notify you of search results by email.") % cdsnameintl[ln],
              }

        if not guest:
            out += """
                   <dt>
                   <a href="./edit?ln=%(ln)s">%(your_settings)s</a>
                   <dd>%(change_account)s""" % {
                     'ln' : ln,
                     'your_settings' : _("Your Settings"),
                     'change_account' : _("Set or change your account email address or password. Specify your preferences about the look and feel of the interface.")
                   }

        out += """
        <dt><A href="../youralerts/display?ln=%(ln)s">%(your_searches)s</A>
        <dd>%(search_explain)s

        <dt><A href="../yourbaskets/display?ln=%(ln)s">%(your_baskets)s</A>
        <dd>%(basket_explain)s""" % {
          'ln' : ln,
          'your_searches' : _("Your Searches"),
          'search_explain' : _("View all the searches you performed during the last 30 days."),
          'your_baskets' : _("Your Baskets"),
          'basket_explain' : _("With baskets you can define specific collections of items, store interesting records you want to access later or share with others."),
        }
        if guest:
            out += self.tmpl_warning_guest_user(ln = ln, type = "baskets")
        out += """
        <dt><a href="../youralerts/list?ln=%(ln)s">%(your_alerts)s</a>
        <dd>%(explain_alerts)s""" % {
          'ln' : ln,
          'your_alerts' : _("Your Alerts"),
          'explain_alerts' : _("Subscribe to a search which will be run periodically by our service. The result can be sent to you via Email or stored in one of your baskets."),
        }
        if guest:
            out += self.tmpl_warning_guest_user(type="alerts", ln = ln)

        if cfg_cern_site:
            out += """
            <dt><A href="http://weblib.cern.ch/cgi-bin/checkloan?uid=&version=2">%(your_loans)s</A>
            <dd>%(explain_loans)s""" % {
              'your_loans' : _("Your Loans"),
              'explain_loans' : _("Check out book you have on loan, submit borrowing requests, etc. Requires CERN ID."),
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
        msg += _("If you wish you can %(x_url_open)slogin or register here%(x_url_close)s.") % {'x_url_open': '<a href="' + sweburl + '/youraccount/login?ln=' + ln + '">', 
                                                                                               'x_url_close': '</a>'}
        return """<table class="errorbox" summary="">
                           <thead>
                            <tr>
                             <th class="errorboxheader">%s</th>
                            </tr>
                           </thead>
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
             'x_url1_open': '<a href="' + sweburl + '/youraccount/logout?ln=' + ln + '">',
             'x_url1_close': '</a>',
             'x_url2_open': '<a href="' + sweburl + '/youraccount/edit?ln=' + ln + '">',
             'x_url2_close': '</a>',
             }
        return out + "<br /><br />"

    def tmpl_account_template(self, title, body, ln):
        """
        Displays a block of the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'title' *string* - The title of the block

          - 'body' *string* - The body of the block
        """

        out =""
        out +="""
              <table class="searchbox" width="90%%" summary=""  >
                           <thead>
                            <tr>
                             <th class="searchboxheader">%s</th>
                            </tr>
                           </thead>
                           <tbody>
                            <tr>
                             <td class="searchboxbody">%s</td>
                            </tr>
                           </tbody>
                          </table>""" % (title, body)
        return out

    def tmpl_account_page(self, ln, weburl, accBody, baskets, alerts, searches, messages, groups, administrative):
        """
        Displays the your account page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The URL of CDS Invenio

          - 'accBody' *string* - The body of the heading block

          - 'baskets' *string* - The body of the baskets block

          - 'alerts' *string* - The body of the alerts block

          - 'searches' *string* - The body of the searches block

          - 'messages' *string* - The body of the messages block

          - 'groups' *string* - The body of the groups block

          - 'administrative' *string* - The body of the administrative block
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        out += self.tmpl_account_template(_("Your Account"), accBody, ln)
        out += self.tmpl_account_template(_("Your Messages"), messages, ln)
        out += self.tmpl_account_template(_("Your Baskets"), baskets, ln)
        out += self.tmpl_account_template(_("Your Alert Searches"), alerts, ln)
        out += self.tmpl_account_template(_("Your Searches"), searches, ln)
	groups_description = _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s you are administering or are a member of.")
	groups_description %= {'x_url_open': '<a href="' + weburl + '/yourgroups/display?ln=' + ln + '">', 
                               'x_url_close': '</a>'}
        out += self.tmpl_account_template(_("Your Groups"), groups_description, ln)
	submission_description = _("You can consult the list of %(x_url_open)syour submissions%(x_url_close)s and inquire about their status.")
	submission_description %= {'x_url_open': '<a href="' + weburl + '/yoursubmissions.py?ln=' + ln + '">', 
                                   'x_url_close': '</a>'}
        out += self.tmpl_account_template(_("Your Submissions"), submission_description, ln)
	approval_description =  _("You can consult the list of %(x_url_open)syour approvals%(x_url_close)s with the documents you approved or refereed.")
	approval_description %=  {'x_url_open': '<a href="' + weburl + '/yourapprovals.py?ln=' + ln + '">', 
                                  'x_url_close': '</a>'}
        out += self.tmpl_account_template(_("Your Approvals"), approval_description, ln)
        out += self.tmpl_account_template(_("Your Administrative Activities"), administrative, ln)
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
           %(msg)s <A href="../youraccount/lost?ln=%(ln)s">%(try_again)s</A>

              </body>

          """ % {
            'ln' : ln,
            'msg' : msg,
            'try_again' : _("Try again")
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
        out += _("Okay, password has been emailed to %s.") % email
        return out

    def tmpl_account_delete(self, ln):
        """
        Displays a confirmation message about deleting the account

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>" + _("""Deleting your account""")
        return out

    def tmpl_account_logout(self, ln):
        """
        Displays a confirmation message about logging out

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)
        out = _("You are no longer recognized.") + ' '
        out += _("If you wish you can %(x_url_open)slogin here%(x_url_close)s.") % {'x_url_open': '<a href="./login?ln=' + ln + '">', 
                                                                                    'x_url_close': '</a>'}
        return out

    def tmpl_login_form(self, ln, referer, internal, register_available, methods, selected_method, supportemail):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'internal' *boolean* - If we are producing an internal authentication

          - 'register_available' *boolean* - If users can register freely in the system

          - 'methods' *array* - The available authentication methods

          - 'selected_method' *string* - The default authentication method

          - 'supportemail' *string* - The email of the support team
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<p>%(please_login)s<br />" % {
                'please_login' : _("If you already have an account, please login using the form below.")
              }

        if register_available:
            out += _("If you don't own an account yet, please %(x_url_open)sregister%(x_url_close)s an internal account.") %\
                {'x_url_open': '<a href="../youraccount/register?ln=' + ln + '">', 
                 'x_url_close': '</a>'}
        else:
            out += _("It is not possible to create an account yourself. Contact %s if you want an account.") % ('<a href="mailto:%s">%s</a>' % (supportemail, supportemail)) 
        out += """<form method="post" action="../youraccount/login">
                  <table>

               """
        if len(methods) > 1:
            # more than one method, must make a select
            login_select = """<select name="login_method">"""
            for method in methods:
                login_select += """<option value="%(method)s" %(selected)s>%(method)s</option>""" % {
                                  'method' : method,
                                  'selected' : (method == selected_method and "selected" or "")
                                }
            login_select += "</select>"
            out += """
                   <tr>
                      <td align="right">%(login_title)s</td>
                      <td>%(login_select)s</td>
                      <td></td>
                   </tr>""" % {
                     'login_title' : _("Login via:"),
                     'login_select' : login_select,
                   }
        else:
            # only one login method available
            out += """<input type="hidden" name="login_method" value="%s">""" % (methods[0])

        out += """<tr>
                   <td align="right">
                     <input type="hidden" name="ln" value="%(ln)s">
                     <input type="hidden" name="referer" value="%(referer)s">
                     <strong>%(username)s:</strong>
                   </td>
                   <td><input type="text" size="25" name="p_un" value=""></td>
                   <td></td>
                  </tr>
                  <tr>
                   <td align="right"><strong>%(password)s:</strong></td>
                   <td align="left"><input type="password" size="25" name="p_pw" value=""></td>
                   <td></td>
                  </tr>
                  <tr>
                   <td></td>
                   <td align="center" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(login)s"></code>""" % {
                       'ln': ln,
                       'referer' : cgi.escape(referer),
                       'username' : _("Username"),
                       'password' : _("Password"),
                       'login' : _("login"),
                       }
        if internal:
            out += """&nbsp;&nbsp;&nbsp;(<a href="./lost?ln=%(ln)s">%(lost_pass)s</a>)""" % {
                     'ln' : ln,
                     'lost_pass' : _("Lost your password?")
                   }
        out += """</td><td></td>
                    </tr>
                  </table></form>"""
        return out

    def tmpl_lost_your_password_teaser(self, ln=cdslang):
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

    def tmpl_register_page(self, ln, referer, level, supportemail, cdsname):
        """
        Displays a login form

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referer' *string* - The referer URL - will be redirected upon after login

          - 'level' *int* - Login level (0 - all access, 1 - accounts activated, 2+ - no self-registration)

          - 'supportemail' *string* - The email of the support team

          - 'cdsname' *string* - The name of the installation
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
              <input type="hidden" name="referer" value="%(referer)s">
              <table>
                <tr>
                 <td align="right"><strong>%(email_address)s:</strong><br><small class="important">(%(mandatory)s)</small></td>
                 <td><input type="text" size="25" name="p_email" value=""><br>
                     <small><span class="quicknote">%(example)s:</span>
                     <span class="example">john.doe@example.com</span></small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong>%(nickname)s:</strong><br><small class="important">(%(mandatory)s)</small></td>
                 <td><input type="text" size="25" name="p_nickname" value=""><br>
                     <small><span class="quicknote">%(example)s:</span>
                     <span class="example">johnd</span></small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong>%(password)s:</strong><br><small class="quicknote">(%(optional)s)</small></td>
                 <td align="left"><input type="password" size="25" name="p_pw" value=""><br>
                    <small><span class="quicknote">%(note)s:</span> %(password_contain)s</small>
                 </td>
                 <td></td>
                </tr>
                <tr>
                 <td align="right"><strong>%(retype)s:</strong></td>
                 <td align="left"><input type="password" size="25" name="p_pw2" value=""></td>
                 <td></td>
                </tr>
                <tr>
                 <td></td>
                 <td align="left" colspan="3"><code class="blocknote"><input class="formbutton" type="submit" name="action" value="%(register)s"></code></td>
                </tr>
              </table>
              <p><strong>%(note)s:</strong> %(explain_acc)s""" % {
                'referer' : cgi.escape(referer),
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
                'explain_acc' : _("Please do not use valuable passwords such as your Unix, AFS or NICE passwords with this service. Your email address will stay strictly confidential and will not be disclosed to any third party. It will be used to identify you for personal services of %s. For example, you may set up an automatic alert search that will look for new preprints and will notify you daily of new arrivals by email.") % cdsname,
              }
        return out

    def tmpl_account_adminactivities(self, ln, weburl, uid, guest, roles, activities):
        """
        Displays the admin activities block for this user

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The address of the site

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
        out += "<p>" + _("You seem to be %(x_role)s.") % {'x_role': ('<em>' + string.join(roles, ", ") + "</em> ")} + '</p>' 
        out += _("Here are some interesting web admin links for you:")

        # print proposed links:
        activities.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
        for action in activities:
            if action == "runbibedit":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibedit/bibeditadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Run BibEdit"))
            if action == "cfgbibformat":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibformat/bibformatadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibFormat"))
            if action == "cfgbibharvest":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibharvest/bibharvestadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibHarvest"))
            if action == "cfgbibindex":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibindex/bibindexadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibIndex"))
            if action == "cfgbibrank":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/bibrank/bibrankadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure BibRank"))
            if action == "cfgwebaccess":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/webaccess/?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebAccess"))
            if action == "cfgwebcomment":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/webcomment/webcommentadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebComment"))
            if action == "cfgwebsearch":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/websearch/websearchadmin.py?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebSearch"))
            if action == "cfgwebsubmit":
                out += """<br>&nbsp;&nbsp;&nbsp; <a href="%s/admin/websubmit/?ln=%s">%s</a>""" % (weburl, ln, _("Configure WebSubmit"))
        out += "<br />" + _("For more admin-level activities, see the complete %(x_url_open)sAdmin Area%(x_url_close)s.") %\
            {'x_url_open': '<a href="' + weburl + '/admin/index.' + ln + '.html">',
             'x_url_close': '</a>'}
        return out

    def tmpl_create_userinfobox(self, ln, url_referer, guest, username, submitter, referee, admin):
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
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<img src="%s/img/head.gif" border="0" alt="">""" % weburl
        if guest:
            out += """%(guest_msg)s ::
    	       <a class="userinfo" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(session)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourbaskets/display?ln=%(ln)s">%(baskets)s</a> ::
                   <a class="userinfo" href="%(weburl)s/youralerts/list?ln=%(ln)s">%(alerts)s</a> ::
                   <a class="userinfo" href="%(sweburl)s/youraccount/login?ln=%(ln)s">%(login)s</a>""" % {
                     'weburl' : weburl,
                     'sweburl': sweburl,
                     'ln' : ln,
                     'guest_msg' : _("guest"),
                     'session' : _("session"),
                     'alerts' : _("alerts"),
                     'baskets' : _("baskets"),
                     'login' : _("login"),
                   }
        else:
            out += """%(username)s ::
    	       <a class="userinfo" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourmessages/display?ln=%(ln)s">%(messages)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourbaskets/display?ln=%(ln)s">%(baskets)s</a> ::
                   <a class="userinfo" href="%(weburl)s/youralerts/list?ln=%(ln)s">%(alerts)s</a> ::
                   <a class="userinfo" href="%(weburl)s/yourgroups/display?ln=%(ln)s">%(groups)s</a> :: """ % {
                     'username' : username,
                     'weburl' : weburl,
                     'sweburl' : sweburl,
                     'ln' : ln,
                     'account' : _("account"),
                     'alerts' : _("alerts"),
		     'messages': _("messages"),
                     'baskets' : _("baskets"),
                     'groups' : _("groups"),
                   }
            if submitter:
                out += """<a class="userinfo" href="%(weburl)s/yoursubmissions?ln=%(ln)s">%(submission)s</a> :: """ % {
                         'weburl' : weburl,
                         'ln' : ln,
                         'submission' : _("submissions"),
                       }
            if referee:
                out += """<a class="userinfo" href="%(weburl)s/yourapprovals?ln=%(ln)s">%(approvals)s</a> :: """ % {
                         'weburl' : weburl,
                         'ln' : ln,
                         'approvals' : _("approvals"),
                       }
            if admin:
                out += """<a class="userinfo" href="%(sweburl)s/youraccount/youradminactivities?ln=%(ln)s">%(administration)s</a> :: """ % {
                         'sweburl' : sweburl,
                         'ln' : ln,
                         'administration' : _("administration"),
                       }
            out += """<a class="userinfo" href="%(sweburl)s/youraccount/logout?ln=%(ln)s">%(logout)s</a>""" % {
                     'sweburl' : sweburl,
                     'ln' : ln,
                     'logout' : _("logout"),
                   }
        return out

    def tmpl_warning(self, warnings, ln=cdslang): 
        """
        Prepare the warnings list
        @param warnings: list of warning tuples (warning_msg, arg1, arg2, etc)
        @return html string of warnings
        """
        from invenio.errorlib import get_msgs_for_code_list
        span_class = 'important'
        out = ""
        if type(warnings) is not list:
            warnings = [warnings]
        if len(warnings) > 0:
            warnings_parsed = get_msgs_for_code_list(warnings, 'warning', ln)
            for (warning_code, warning_text) in warnings_parsed:
                if not warning_code.startswith('WRN'):
                    #display only warnings that begin with WRN to user
                    continue
                span_class = 'important'
                out += '''
                    <span class="%(span_class)s">%(warning)s</span><br>''' % \
                    {   'span_class'    :   span_class,
                        'warning'       :   warning_text         } 
            return out
        else:
            return ""

    def tmpl_warnings(self, warnings, ln=cdslang):
        """
        Display len(warnings) warning fields
        @param infos: list of strings
        @param ln=language
        @return html output
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
                    warningbox += line + "    <br/>\n"
                warningbox += lines[-1] + "  </p>"
            warningbox += "</div><br/>\n"
        return warningbox
    
    def tmpl_display_all_groups(self,
                                infos,
                                admin_group_html,
                                member_group_html,
                                warnings=[],
                                ln=cdslang):
        """
        Displays the 2 tables of groups: admin and member 

        Parameters:

          - 'ln' *string* - The language to display the interface in
          
          - 'admin_group_html' *string* - Html code for displaying all the groups
          the user is the administrator of 
          
          - 'member_group_html' *string* - Html code for displaying all the groups
          the user is member of

        """
        
        _ = gettext_set_language(ln)
        group_text = self.tmpl_infobox(infos)
        group_text += self.tmpl_warning(warnings)
        group_text += """
<table>
  <tr>
    <td>%s</td>
  </tr>
  <tr>
    <td><br/></br>%s</td>
  </tr>
</table>""" %(admin_group_html, member_group_html)
        return group_text

    def tmpl_display_admin_group(self, groups, ln=cdslang):
        """
        Display the groups the user is admin of.
        
        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - All the group the user is admin of
        - 'infos' *list* - Display infos on top of admin group table
        """

        _ = gettext_set_language(ln)
        img_link = """
        <a href="%(weburl)s/yourgroups/%(action)s?grpID=%(grpID)s&amp;ln=%(ln)s">
        <img src="%(weburl)s/img/%(img)s" alt="%(text)s" style="border:0" width="25" 
        height="25"><br/><small>%(text)s</small></img>
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
            edit_link = img_link % {'weburl' : weburl,
                                    'grpID' : grpID,
                                    'ln': ln,
                                    'img':"webbasket_create_small.png",
                                    'text':_("Edit group"),
                                    'action':"edit"
                                    }
            members_link = img_link % {'weburl' : weburl,
                                       'grpID' : grpID,
                                       'ln': ln,
                                       'img':"webbasket_usergroup.png",
                                       'text':_("Edit %s members") % '<br/>',
                                       'action':"members"
                                       }                     
            out += """
    <tr class="mailboxrecord">
      <td>%s</td>
      <td>%s</td>
      <td style="text-align: center;" >%s</td>
      <td style="text-align: center;" >%s</td>
    </tr>""" %(name, description, edit_link, members_link)
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
        return indent_text(out, 2)

    def tmpl_display_member_group(self, groups, ln=cdslang):
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
    </tr>""" %(name, description)
        group_text += """
    <tr>
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
        return indent_text(group_text, 2)

    def tmpl_display_input_group_info(self,
                                      group_name,
                                      group_description,
                                      join_policy,
                                      act_type="create",
                                      grpID="",
                                      warnings=[],
                                      ln=cdslang):
        """
        Display group data when creating or updating a group:
        Name, description, join_policy.
        Parameters:
        - 'ln' *string* - The language to display the interface in
        - 'group_name' *string* - name of the group
        - 'group_description' *string* - description of the group
        - 'join_policy' *string* - join policy
        - 'act_type' *string* - info about action : create or edit(update)
        - 'grpID' *string* - ID of the group(not null in case of group editing)
        - 'warnings' *list* - Display warning if values are not correct
        
        """
        _ = gettext_set_language(ln)
        #default
        hidden_id =""
        form_name = "create_group"
        action = weburl + '/yourgroups/create'
        button_label = _("Create new group")
        button_name = "create_button"
        label = _("Create new group")
        delete_text = ""
        
        if act_type == "update":
            form_name = "update_group"
            action = weburl + '/yourgroups/edit'
            button_label = _("Update group")
            button_name = "update"
            label = _('Edit group %s') % group_name
            delete_text = """<input type="submit" value="%s" class="formbutton" name="%s"/>"""
            delete_text %= (_("Delete group"),"delete")
            if grpID != "":
                hidden_id = """<input type="hidden" name="grpID" value="%s"/>"""
                hidden_id %= grpID
            
        out = self.tmpl_warning(warnings)
        out += """
<form name="%(form_name)s" action="%(action)s" method="POST">
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
    <tbody>
      <tr>
        <td colspan="2">
          <table>
            <tr>
              <td>%(name_label)s</td>
              <td>
               <input type="text" name="group_name" value="%(group_name)s"/>
              </td>
            </tr>
            <tr>
              <td>%(description_label)s</td>
              <td>
               <input type="text" name="group_description" value="%(group_description)s"/>
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
     <input type="submit" value="%(button_label)s" class="formbutton" name="%(button_name)s"/>
    </td>
    <td>
    %(delete_text)s
    </td>
    <td>
     <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel"/>
    </td>
   </tr>
  </table 
  </div>
</form>

"""
        out %= {'action' : action,
                'logo': weburl + '/img/webbasket_create.png',
                'label': label,
                'form_name' : form_name,
                'name_label': _("Group name:"),
                'delete_text': delete_text,
                'description_label': _("Group description:"),
                'join_policy_label': _("Group join policy:"),
                'group_name': group_name,
                'group_description': group_description,
                'button_label': button_label,
                'button_name':button_name,
                'cancel_label':_("Cancel"),
                'hidden_id':hidden_id,
                'ln': ln,
                'join_policy' :self.__create_join_policy_selection_menu("join_policy",
                                                                        join_policy,
                                                                        ln)
               } 
        return indent_text(out, 2)

    def tmpl_display_input_join_group(self,
                                      group_list,
                                      group_name,
                                      group_from_search,
                                      search,
                                      warnings=[],
                                      ln=cdslang):

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
<form name="join_group" action="%(action)s" method="POST">
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
              <td><br>%(label2)s</td>
              <td><br><input type="text" name="group_name" value="%(group_name)s"/></td>
              <td><br>
               <input type="submit" name="find_button" value="%(find_label)s" class="nonsubmitbutton"/>
              </td>
            </tr>
            %(search_content)s</td>
              
          </table>
        </td>
      </tr>
    </tbody>
  </table>
  <table>
  <tr>
   <td>
    <input type="submit" name="join_button" value="%(label)s" class="formbutton"/>
   </td>
   <td>
    <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel"/>
   </td>
   </tr>
  </table>
 </div>
</form>

"""
        out %= {'action' : weburl + '/yourgroups/join',
                'logo': weburl + '/img/webbasket_create.png',
                'label': _("Join group"),
                'group_name': group_name,
                'label2':_("or find it") + ': ',
                'list_label':_("Choose group:"),
                'ln': ln,
                'find_label': _("Find group"),
                'cancel_label':_("Cancel"),
                'group_list' :self.__create_select_menu("grpID",group_list, _("Please select:")),
                'search_content' : search_content
               } 
        return indent_text(out, 2)
    
    def tmpl_display_manage_member(self,
                                   grpID,
                                   group_name,
                                   members,
                                   pending_members,
                                   infos=[],
                                   warnings=[],
                                   ln=cdslang):
        """Display current members and waiting members of a group.
        
        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'grpID *string* - ID of the group
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
<form name="member" action="%(action)s" method="POST">
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
          <img src="%(imgurl)s/webbasket_usergroup.png" alt="%(header1)s" />
        </td>

        <td class="bsktitle">
          <b>%(header1)s</b><br />
          &nbsp;
        </td>
      </tr>
    </thead>
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
          <img src="%(imgurl)s/webbasket_usergroup_gray.png" alt="%(header2)s" />
        </td>

        <td class="bsktitle">
          <b>%(header2)s</b><br />
          &nbsp;
        </td>
      </tr>
    </thead>
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
          <img src="%(imgurl)s/iconpen.gif" alt="%(header3)s" />
        </td>

        <td class="bsktitle">
          <b>%(header3)s</b><br />
          &nbsp;
        </td>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td colspan="2">
          <table>          
            <tr>
             <td collspan="2" style="padding: 0 5 10 5;">%(invite_text)s</td>
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
  <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel"/>
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
            member_text = """<td style="padding: 0 5 10 5;" collspan="2">%s</td>""" % _("No members.")
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
            pending_text = """<td style="padding: 0 5 10 5;" collspan="2">%s</td>""" % _("No members awaiting approval.") 
        
        header1 = self.tmpl_group_table_title(text=_("Current members"))
        header2 = self.tmpl_group_table_title(text=_("Members awaiting approval"))
        header3 = _("Invite new members")
        link_open = '<a href="%s/yourmessages/write?ln=%s">'
        link_open %= (weburl, ln)
        invite_text = _("If you want to invite new members to join your group, please use the %(x_url_open)sweb message%(x_url_close)s system.") % \
            {'x_url_open': link_open, 
             'x_url_close': '</a>'}
        action = weburl + '/yourgroups/members?ln=' + ln
        out %= {'title':_('Group: %s') % group_name,
                'member_text' : member_text,
                'pending_text' :pending_text,
                'action':action,
                'grpID':grpID,
                'header1': header1,
                'header2': header2,
                'header3': header3,
                'invite_text': invite_text,
                'imgurl': weburl + '/img',
                'cancel_label':_("Cancel"),
                'ln':ln
                }
        return indent_text(out, 2)
    
    def tmpl_display_input_leave_group(self,
                                       groups,
                                       warnings=[],
                                       ln=cdslang):
        """Display groups the user can leave.
        
        Parameters:

        - 'ln' *string* - The language to display the interface in
        - 'groups' *list* - List of groups the user is currently member of
        - 'warnings' *list* - Display warning if no group is selected
        """
        _ = gettext_set_language(ln)
        out = self.tmpl_warning(warnings)
        out += """
<form name="leave" action="%(action)s" method="POST">
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
    <input type="submit" value="%(cancel_label)s" class="formbutton" name="cancel"/>
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
        action = weburl + '/yourgroups/leave?ln=%s'
        action %= (ln)
        out %= {'groups' : groups,
                'list_label' : list_label,
                'action':action,
                'logo': weburl + '/img/webbasket_create.png',
                'label' : _("Leave group"),
                'cancel_label':_("Cancel"),
                'ln' :ln,
                'submit' : submit
                }
        return indent_text(out, 2)
        

    def tmpl_confirm_delete(self, grpID, ln=cdslang):
        """
        display a confirm message when deleting a group
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        action = weburl + '/yourgroups/edit'
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
        return indent_text(out, 2)

    def tmpl_confirm_leave(self, uid, grpID, ln=cdslang):
        """
        display a confirm message
        @param ln: language
        @return html output
        """
        _ = gettext_set_language(ln)
        action = weburl + '/yourgroups/leave'
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
        return indent_text(out, 2)
    
    def __create_join_policy_selection_menu(self, name, current_join_policy, ln=cdslang):
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
        out += indent_text('<option value="-1">%s</option>' % (select_text))
        for (key, label) in elements:
            selected = ''
            if key == selected_key:
                selected = ' selected="selected"'
            out += indent_text('<option value="%s"%s>%s</option>'% (key, selected, label), 1)
        out += '</select>'
        return out


    def tmpl_infobox(self, infos, ln=cdslang):
        """Display len(infos) information fields
        @param infos: list of strings
        @param ln=language
        @return html output
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

    def tmpl_navtrail(self, ln=cdslang, title=""):
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
            nav_h2 = nav_h2 % (weburl, _("Your Groups"))

        return  nav_h1 % (weburl, _("Your Account")) + nav_h2

    def tmpl_group_table_title(self, img="", text="", ln=cdslang):
        """
        display the title of a table:
        - 'img' *string* - img path
        - 'text' *string* - title
        - 'ln' *string* - The language to display the interface in
        """
        out = "<div>"
        if img:
            out += """
            <img src="%s" />
            """ % (weburl + img)
        out += """
        <b>%s</b>
        </div>""" % text
        return out
 
    def tmpl_admin_msg(self, group_name, grpID, ln=cdslang):
        """
        return message content for joining group
        - 'group_name' *string* - name of the group
        - 'grpID' *string* - ID of the group
        - 'ln' *string* - The language to display the interface in
        """
        _ = gettext_set_language(ln)
        subject = _("Group %s: New membership request") % group_name
        url = weburl + "/yourgroups/members?grpID=%i&ln=%s"
        url %= (int(grpID), ln)
        # FIXME: which user?  We should show his nickname.
        body = (_("A user wants to join the group %s.") % group_name) + '<br/>'
	body += _("Please %(x_url_open)saccept or reject%(x_url_close)s this user's request.") % {'x_url_open': '<a href="' + url + '">', 
                                                                                                  'x_url_close': '</a>'}
        body += '<br />'
        return subject, body

    def tmpl_member_msg(self,
                        group_name,
                        accepted=0,
                        ln=cdslang):
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
        url = weburl + "/yourgroups/display?ln=" + ln
        body += '<br />'
        body += _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s.") % {'x_url_open': '<a href="' + url + '">', 
                                                                                              'x_url_close': '</a>'}
        body += '<br />'
        return subject, body
    
    def tmpl_delete_msg(self,
                        group_name,
                        ln=cdslang):
        """
        return message content when new member is accepted/rejected
        - 'group_name' *string* - name of the group
        - 'ln' *string* - The language to display the interface in
        """
        _ = gettext_set_language(ln)
        subject = _("Group %s has been deleted") % group_name
        url = weburl + "/yourgroups/display?ln=" + ln
        body = _("Group %s has been deleted by its administrator.") % group_name
        body += '<br/>'
        body += _("You can consult the list of %(x_url_open)syour groups%(x_url_close)s.") % {'x_url_open': '<a href="' + url + '">', 
                                                                                              'x_url_close': '</a>'} 
        body += '<br />'
        return subject, body
    
    def tmpl_group_info(self, nb_admin_groups=0, nb_member_groups=0, nb_total_groups=0, ln=cdslang):
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
        out %= {'x_url_open': '<a href="' + weburl + '/yourgroups/display?ln=' + ln + '">',
                'x_nb_total': nb_total_groups,
                'x_url_close': '</a>',
                'x_nb_admin': nb_admin_groups,
                'x_nb_member': nb_member_groups}
        return out
