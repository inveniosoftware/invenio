## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio BibFormat Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import MySQLdb

from invenio import bibformatadminlib, \
                    bibformat_dblayer,\
                    bibformat_engine
from invenio.bibrankadminlib import check_user
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, page_not_authorized, collect_user_info
from invenio.messages import wash_language, gettext_set_language
from invenio.urlutils import wash_url_argument, redirect_to_url
from invenio.search_engine import search_pattern, \
                           create_basic_search_units
from invenio.bibformat_config import InvenioBibFormatError, InvenioBibFormatWarning
from invenio.errorlib import register_exception
from invenio.config import CFG_SITE_LANG, CFG_SITE_NAME, CFG_SITE_SECURE_URL

def index(req, ln=CFG_SITE_LANG):
    """
    Main BibFormat administration page.

    Displays a warning if we find out that etc/biformat dir is not writable by us
    (as most opeation of BibFormat must write in this directory).

    @param req: the request object
    @param ln: language
    @return: a web page
    """
    warnings = []
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    if not bibformatadminlib.can_write_etc_bibformat_dir():
        try:
            raise InvenioBibFormatWarning(_('Cannot write in etc/bibformat dir of your Invenio installation. Check directory permission.'))
        except InvenioBibFormatWarning, exc:
            register_exception(stream='warning', req=req)
            warnings.append(exc.message)

    # Check if user is authorized to administer
    # If not, still display page but offer to log in
    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        is_admin = True
    else:
        is_admin = False

    navtrail = '''<a class="navtrail" href="%s/help/admin">%s</a>''' % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))

    return page(title=_("BibFormat Admin"),
                body=bibformatadminlib.perform_request_index(ln=ln,
                                                             warnings=warnings,
                                                             is_admin=is_admin),
                language=ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req)

def output_formats_manage(req, ln=CFG_SITE_LANG, sortby="code"):
    """
    Main page for output formats management. Check for authentication and print output formats list.

    @param req: the request object
    @param ln: language
    @param sortby: the sorting crieteria (can be 'code' or 'name')
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail()

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        sortby = wash_url_argument(sortby, 'str')
        return page(title=_("Manage Output Formats"),
                body=bibformatadminlib.perform_request_output_formats_management(ln=ln, sortby=sortby),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)

def output_format_show(req, bfo, ln=CFG_SITE_LANG,
                       r_fld=[], r_val=[], r_tpl=[],
                       default="", r_upd="", chosen_option="",
                       **args):
    """
    Show a single output format. Check for authentication and print output format settings.

    The page either shows the output format from file, or from user's
    POST session, as we want to let him edit the rules without
    saving. Policy is: r_fld, r_val, rules_tpl are list of attributes
    of the rules.  If they are empty, load from file. Else use
    POST. The i th value of each list is one of the attributes of rule
    i. Rule i is the i th rule in order of evaluation.  All list have
    the same number of item.

    r_upd contains an action that has to be performed on rules. It
    can composed of a number (i, the rule we want to modify) and an
    operator : "save" to save the rules, "add" or "del".
    syntax: operator [number]
    For eg: r_upd = _("Save Changes") saves all rules (no int should be specified).
    For eg: r_upd = _("Add New Rule") adds a rule (no int should be specified).
    For eg: r_upd = _("Remove Rule") + " 5"  deletes rule at position 5.
    The number is used only for operation delete.

    An action can also be in **args. We must look there for string starting
    with '(+|-) [number]' to increase (+) or decrease (-) a rule given by its
    index (number).
    For example "+ 5" increase priority of rule 5 (put it at fourth position).
    The string in **args can be followed by some garbage that looks like .x
    or .y, as this is returned as the coordinate of the click on the
    <input type="image">. We HAVE to use args and reason on its keys, because for <input> of
    type image, iexplorer does not return the value of the tag, but only the name.

    Action is executed only if we are working from user's POST session
    (means we must have loaded the output format first, which is
    totally normal and expected behaviour)


    @param req: the request object
    @param bfo: the filename of the output format to show
    @param ln: language
    @param r_fld: the list of 'field' attribute for each rule
    @param r_val: the list of 'value' attribute for each rule
    @param r_tpl: the list of 'template' attribute for each rule
    @param default: the default format template used by this output format
    @param r_upd: the rule that we want to increase/decrease in order of evaluation
    @param chosen_option: emptry string when user has not yet confirmed to go on
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/output_formats_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln, _("Manage Output Formats")))
    code = wash_url_argument(bfo, 'str')

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        bfo = wash_url_argument(bfo, 'str')
        default = wash_url_argument(default, 'str')
        r_upd = wash_url_argument(r_upd, 'str')

        if not bibformatadminlib.can_read_output_format(bfo): #No read permission
            try:
                raise InvenioBibFormatError(_('Output format %s cannot not be read. %s') % (bfo, ""))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Restricted Output Format"),
                            body = """You don't have permission to
                            view this output format.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

        output_format = bibformat_engine.get_output_format(code=bfo,
                                                           with_attributes=True)
        name = output_format['attrs']['names']['generic']
        if name == "":
            name = bfo

        if not bibformatadminlib.can_write_output_format(bfo) and \
               chosen_option == "":#No write permission
            return dialog_box(req=req,
                              ln=ln,
                              title="File Permission on %s" % name,
                              message="You don't have write permission " \
                              "on <i>%s</i>.<br/> You can view the output " \
                              "format, but not edit it." % name,
                              navtrail=navtrail_previous_links,
                              options=[ _("Ok")])

        return page(title=_('Output Format %s Rules' % name),
                    body=bibformatadminlib.perform_request_output_format_show(bfo=bfo,
                                                                              ln=ln,
                                                                              r_fld=r_fld,
                                                                              r_val=r_val,
                                                                              r_tpl=r_tpl,
                                                                              default=default,
                                                                              r_upd=r_upd,
                                                                              args=args),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)

def output_format_show_attributes(req, bfo, ln=CFG_SITE_LANG):
    """
    Page for output format names and descrition attributes edition.

    @param req: the request object
    @param ln: language
    @param bfo: the filename of the template to show
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/output_formats_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln , _("Manage Output Formats")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        bfo = wash_url_argument(bfo, 'str')

        if not bibformatadminlib.can_read_output_format(bfo): #No read permission
            try:
                raise InvenioBibFormatError(_('Output format %s cannot not be read. %s') % (bfo, ""))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Restricted Output Format"),
                            body = """You don't have permission to
                            view this output format.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

        output_format = bibformat_engine.get_output_format(code=bfo,
                                                           with_attributes=True)
        name = output_format['attrs']['names']['generic']

        return page(title=_("Output Format %s Attributes" % name),
                    body=bibformatadminlib.perform_request_output_format_show_attributes(bfo, ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links ,
                    lastupdated=__lastupdated__,
                    req=req)

    else:
        return page_not_authorized(req=req, text=auth_msg)

def output_format_show_dependencies(req, bfo, ln=CFG_SITE_LANG):
    """
    Show the dependencies of the given output format.

    @param req: the request object
    @param ln: language
    @param bfo: the filename of the output format to show
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s </a>''' % (CFG_SITE_SECURE_URL, ln, _("Manage Output Formats")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        bfo = wash_url_argument(bfo, 'str')

        if not bibformatadminlib.can_read_output_format(bfo): #No read permission
            try:
                raise InvenioBibFormatError(_('Output format %s cannot not be read. %s') % (bfo, ""))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Restricted Output Format"),
                            body = """You don't have permission
                            to view this output format.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

        format_name = bibformat_engine.get_output_format_attrs(bfo)['names']['generic']

        return page(title=_("Output Format %s Dependencies" % format_name),
                    body=bibformatadminlib.perform_request_output_format_show_dependencies(bfo, ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    else:
        return page_not_authorized(req=req, text=auth_msg)

def output_format_update_attributes(req, bfo, ln=CFG_SITE_LANG,
                                    name = "", description="",
                                    code="", content_type="",
                                    names_trans=[], visibility="0"):
    """
    Update the name, description and code of given output format

    @param req: the request object
    @param ln: language
    @param description: the new description
    @param name: the new name
    @param code: the new short code (== new bfo) of the output format
    @param content_type: the new content_type of the output format
    @param bfo: the filename of the output format to update
    @param names_trans: the translations in the same order as the languages from get_languages()
    @param visibility: the visibility of the output format in the output formats list (public pages)
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:

        name = wash_url_argument(name, 'str')
        description = wash_url_argument(description, 'str')
        bfo = wash_url_argument(bfo, 'str')
        code = wash_url_argument(code, 'str')
        visibility = wash_url_argument(visibility, 'int')
        bfo = bibformatadminlib.update_output_format_attributes(bfo,
                                                                name,
                                                                description,
                                                                code,
                                                                content_type,
                                                                names_trans,
                                                                visibility)

        redirect_to_url(req, "output_format_show?ln=%(ln)s&bfo=%(bfo)s" % {'ln':ln,
                                                                           'bfo':bfo,
                                                                           'names_trans':names_trans})
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg)

def output_format_delete(req, bfo, ln=CFG_SITE_LANG, chosen_option=""):
    """
    Delete an output format

    @param req: the request object
    @param bfo: the filename of the output format to delete
    @param ln: language
    @param chosen_option: empty string when user has not yet confirmed, else "Delete" to apply
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/output_formats_manage?ln=%s">%s</a> &gt; %s''' % (CFG_SITE_SECURE_URL, ln, _("Manage Output Formats"), _("Delete Output Format")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:

        #Ask confirmation to user if not already done
        chosen_option = wash_url_argument(chosen_option, 'str')
        if chosen_option == "":
            bfo = wash_url_argument(bfo, 'str')
            format_name = bibformat_dblayer.get_output_format_names(bfo)['generic']
            return dialog_box(req=req,
                              ln=ln,
                              title="Delete %s"%format_name,
                              message="Are you sure you want to" \
                              "delete output format <i>%s</i>?" % format_name,
                              navtrail=navtrail_previous_links,
                              options=[_("Cancel"), _("Delete")])

        elif chosen_option==_("Delete"):
            bibformatadminlib.delete_output_format(bfo)
        redirect_to_url(req, "output_formats_manage?ln=%(ln)s"%{'ln':ln})
    else:
        return page_not_authorized(req=req, text=auth_msg)

def output_format_add(req, ln=CFG_SITE_LANG):
    """
    Adds a new output format

    @param req: the request object
    @param ln: language
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:

        bfo = bibformatadminlib.add_output_format()
        if bfo == None:
            return page(title=_("Cannot create output format"),
                        body = """BibFormat cannot add an output format.
                        Check output formats directory permissions.""",
                        language=ln,
                        lastupdated=__lastupdated__,
                        req=req)
        redirect_to_url(req, "output_format_show_attributes?ln=%(ln)s&bfo=%(bfo)s" % {'ln':ln, 'bfo':bfo})
    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_templates_manage(req, ln=CFG_SITE_LANG, checking='0'):
    """
    Main page for formats templates management. Check for authentication and print formats list.

    @param req: the request object
    @param ln: language
    @param checking: if 0, basic checking. Else perform extensive checking (time-consuming)
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail()

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        checking_level = wash_url_argument(checking, 'int')
        return page(title=_("Manage Format Templates"),
                body=bibformatadminlib.perform_request_format_templates_management(ln=ln, checking=checking_level),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)


def format_template_show(req, bft, code=None, ln=CFG_SITE_LANG,
                         ln_for_preview=CFG_SITE_LANG,
                         pattern_for_preview="",
                         content_type_for_preview="text/html",
                         chosen_option=""):
    """
    Main page for template edition. Check for authentication and print formats editor.

    @param req: the request object
    @param ln: language
    @param code: the code being edited
    @param bft: the name of the template to show
    @param ln_for_preview: the language for the preview (for bfo)
    @param pattern_for_preview: the search pattern to be used for the preview (for bfo)
    @param content_type_for_preview: the (MIME) content type of the preview
    @param chosen_option: returned value for dialog_box warning
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    navtrail_previous_links = bibformatadminlib.getnavtrail('''
    &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln ,  _("Manage Format Templates")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        format_template = wash_url_argument(bft, 'str')
        ln_preview = wash_language(ln_for_preview)
        pattern_preview = wash_url_argument(pattern_for_preview, 'str')
        if not bibformatadminlib.can_read_format_template(bft): #No read permission
            try:
                raise InvenioBibFormatError(_('Format template %s cannot not be read. %s') % (format_template, ""))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Restricted Format Template"),
                            body = """You don't have permission
                            to view this format template.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

        format_name = bibformat_engine.get_format_template_attrs(bft)['name']
        if not bibformatadminlib.can_write_format_template(bft) and \
               chosen_option == "": #No write permission
            return dialog_box(req=req,
                              ln=ln,
                              title="File Permission on %s" % format_name,
                              message="You don't have write permission " \
                              "on <i>%s</i>.<br/> You can view the template" \
                              ", but not edit it." % format_name,
                              navtrail=navtrail_previous_links,
                              options=[ _("Ok")])


        if bft.endswith('.xsl'):
            format_name += ' (XSL)'
        return page(title=_("Format Template %s"%format_name),
                body=bibformatadminlib.perform_request_format_template_show(format_template,
                                                          code=code,
                                                          ln=ln,
                                                          ln_for_preview=ln_preview,
                                                          pattern_for_preview=pattern_preview,
                                                          content_type_for_preview=content_type_for_preview),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)

def format_template_show_attributes(req, bft, ln=CFG_SITE_LANG, new=0):
    """
    Page for template name and descrition attributes edition.

    This is also the first page shown when a format template
    has just been added. In that case new is different from
    False and we can offer specific option to user (for ex
    let him make a duplicate of existing template).

    @param req: the request object
    @param ln: language
    @param bft: the name of the template to show
    @param new: if "False", the template has not just been added
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln, _("Manage Format Templates")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        format_template = wash_url_argument(bft, 'str')
        format_name = bibformat_engine.get_format_template_attrs(bft)['name']
        is_new = wash_url_argument(new, 'int')

        if not bibformatadminlib.can_read_format_template(bft): #No read permission
            try:
                raise InvenioBibFormatError(_('Format template %s cannot not be read. %s') % (format_template, ""))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Restricted Format Template"),
                            body = """You don't have permission
                            to view this format template.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

        return page(title=_("Format Template %s Attributes"%format_name),
                    body=bibformatadminlib.perform_request_format_template_show_attributes(bft, ln=ln, new=is_new),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links ,
                    lastupdated=__lastupdated__,
                    req=req)

    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_show_dependencies(req, bft, ln=CFG_SITE_LANG):
    """
    Show the dependencies (on elements) of the given format.

    @param req: the request object
    @param ln: language
    @param bft: the filename of the template to show
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln, _("Manage Format Templates")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        format_template = wash_url_argument(bft, 'str')
        format_name = bibformat_engine.get_format_template_attrs(bft)['name']

        return page(title=_("Format Template %s Dependencies" % format_name),
                    body=bibformatadminlib.perform_request_format_template_show_dependencies(bft, ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_update_attributes(req, bft, ln=CFG_SITE_LANG,
                                      name = "", description="",
                                      duplicate=None):
    """
    Update the name and description of given format template

    @param req: the request object
    @param ln: language
    @param description: the new description
    @param name: the new name
    @param bft: the filename of the template to update
    @param duplicate: the filename of template that we want to copy (the code)
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:

        if duplicate is not None:
            duplicate = wash_url_argument(duplicate, 'str')
        name = wash_url_argument(name, 'str')
        description = wash_url_argument(description, 'str')
        bft = bibformatadminlib.update_format_template_attributes(bft,
                                                                  name,
                                                                  description,
                                                                  duplicate)

        redirect_to_url(req, "format_template_show?ln=%(ln)s&bft=%(bft)s" % {'ln':ln, 'bft':bft})
    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_delete(req, bft, ln=CFG_SITE_LANG, chosen_option=""):
    """
    Delete a format template

    @param req: the request object
    @param bft: the filename of the template to delete
    @param ln: language
    @param chosen_option: empty string when user has not yet confirm. Else "Delete" to confirm
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail('''
    &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s</a> &gt; %s''' % (CFG_SITE_SECURE_URL, ln ,_("Manage Format Templates"),_("Delete Format Template")))

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        #Ask confirmation to user if not already done
        chosen_option = wash_url_argument(chosen_option, 'str')
        if chosen_option == "":
            format_template = wash_url_argument(bft, 'str')
            format_name = bibformat_engine.get_format_template_attrs(bft)['name']
            return dialog_box(req=req,
                              ln=ln,
                              title="Delete %s" % format_name,
                              message="Are you sure you want to delete" \
                              "format template <i>%s</i>?" % format_name,
                              navtrail=navtrail_previous_links,
                              options=[_("Cancel"), _("Delete")])

        elif chosen_option==_("Delete"):
            bibformatadminlib.delete_format_template(bft)

        redirect_to_url(req, "format_templates_manage?ln=%(ln)s" % {'ln':ln})
    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_add(req, ln=CFG_SITE_LANG):
    """
    Adds a new format template

    @param req: the request object
    @param ln: language
    @return: a web page (or redirection to a web page)
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:

        bft = bibformatadminlib.add_format_template()
        redirect_to_url(req, "format_template_show_attributes?ln=%(ln)s&bft=%(bft)s&new=1" % {'ln':ln, 'bft':bft})
    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_show_preview_or_save(req, bft, ln=CFG_SITE_LANG, code=None,
                                         ln_for_preview=CFG_SITE_LANG,
                                         pattern_for_preview="",
                                         content_type_for_preview='text/html',
                                         save_action=None,
                                         navtrail=""):
    """
    Print the preview of a record with a format template. To be included inside Format template
    editor. If the save_action has a value, then the code should also be saved at the same time

    @param req: the request object
    @param code: the code of a template to use for formatting
    @param ln: language
    @param ln_for_preview: the language for the preview (for bfo)
    @param pattern_for_preview: the search pattern to be used for the preview (for bfo)
    @param content_type_for_preview: the content-type to use to serve the preview page
    @param save_action: has a value if the code has to be saved
    @param bft: the filename of the template to save
    @param navtrail: navigation trail
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        user_info = collect_user_info(req)
        uid = user_info['uid']
        bft = wash_url_argument(bft, 'str')
        if save_action is not None and code is not None:
            #save
            bibformatadminlib.update_format_template_code(bft, code=code)
        bibformat_engine.clear_caches()
        if code is None:
            code = bibformat_engine.get_format_template(bft)['code']

        ln_for_preview = wash_language(ln_for_preview)
        pattern_for_preview = wash_url_argument(pattern_for_preview, 'str')
        if pattern_for_preview == "":
            try:
                recID = search_pattern(p='-collection:DELETED').pop()
            except KeyError:
                return page(title="No Document Found",
                            body="",
                            uid=uid,
                            language=ln_for_preview,
                            navtrail = "",
                            lastupdated=__lastupdated__,
                            req=req,
                            navmenuid='search')

            pattern_for_preview = "recid:%s" % recID
        else:
            try:
                recID = search_pattern(p=pattern_for_preview + \
                                        ' -collection:DELETED').pop()
            except KeyError:
                return page(title="No Record Found for %s" % pattern_for_preview,
                            body="",
                            uid=uid,
                            language=ln_for_preview,
                            navtrail = "",
                            lastupdated=__lastupdated__,
                            req=req)

        units = create_basic_search_units(None, pattern_for_preview, None)
        keywords = [unit[1] for unit in units if unit[0] != '-']
        bfo = bibformat_engine.BibFormatObject(recID = recID,
                                               ln = ln_for_preview,
                                               search_pattern = keywords,
                                               xml_record = None,
                                               user_info = user_info)
        body = bibformat_engine.format_with_format_template(bft,
                                                            bfo,
                                                            verbose=7,
                                                            format_template_code=code)

        if content_type_for_preview == 'text/html':
            #Standard page display with CDS headers, etc.
            return page(title="",
                        body=body,
                        uid=uid,
                        language=ln_for_preview,
                        navtrail = navtrail,
                        lastupdated=__lastupdated__,
                        req=req,
                        navmenuid='search')
        else:
            #Output with chosen content-type.
            req.content_type = content_type_for_preview
            req.send_http_header()
            req.write(body)
    else:
        return page_not_authorized(req=req, text=auth_msg)

def format_template_show_short_doc(req, ln=CFG_SITE_LANG, search_doc_pattern=""):
    """
    Prints the format elements documentation in a brief way. To be included inside Format template
    editor.

    @param req: the request object
    @param ln: language
    @param search_doc_pattern: a search pattern that specified which elements to display
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        search_doc_pattern = wash_url_argument(search_doc_pattern, 'str')
        return bibformatadminlib.perform_request_format_template_show_short_doc(ln=ln, search_doc_pattern=search_doc_pattern)
    else:
        return page_not_authorized(req=req, text=auth_msg)


def format_elements_doc(req, ln=CFG_SITE_LANG):
    """
    Main page for format elements documentation. Check for authentication and print format elements list.

    @param req: the request object
    @param ln: language
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail()

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Format Elements Documentation"),
                body=bibformatadminlib.perform_request_format_elements_documentation(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)

def format_element_show_dependencies(req, bfe, ln=CFG_SITE_LANG):
    """
    Shows format element dependencies

    @param req: the request object
    @param req: the request object
    @param bfe: the name of the bfe to show
    @param ln: language
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_elements_doc?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln , _("Format Elements Documentation")))
    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        bfe = wash_url_argument(bfe, 'str')
        return page(title=_("Format Element %s Dependencies" % bfe),
                body=bibformatadminlib.perform_request_format_element_show_dependencies(bfe=bfe, ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def format_element_test(req, bfe, ln=CFG_SITE_LANG, param_values=None):
    """
    Allows user to test element with different parameters and check output

    'param_values' is the list of values to pass to 'format'
    function of the element as parameters, in the order ...
    If params is None, this means that they have not be defined by user yet.

    @param req: the request object
    @param bfe: the name of the element to test
    @param ln: language
    @param param_values: the list of parameters to pass to element format function
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_elements_doc?ln=%s">%s</a>''' %( CFG_SITE_SECURE_URL, ln , _("Format Elements Documentation")))

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        bfe = wash_url_argument(bfe, 'str')
        user_info = collect_user_info(req)
        uid = user_info['uid']
        return page(title=_("Test Format Element %s" % bfe),
                body=bibformatadminlib.perform_request_format_element_test(bfe=bfe,
                                                                           ln=ln,
                                                                           param_values=param_values,
                                                                           user_info=user_info),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)


def validate_format(req, ln=CFG_SITE_LANG, bfo=None, bft=None, bfe=None):
    """
    Returns a page showing the status of an output format or format
    template or format element. This page is called from output
    formats management page or format template management page or
    format elements documentation.

    The page only shows the status of one of the format, depending on
    the specified one. If multiple are specified, shows the first one.

    @param req: the request object
    @param ln: language
    @param bfo: an output format 6 chars code
    @param bft: a format element filename
    @param bfe: a format element name
    @return: a web page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        if bfo is not None: #Output format validation
            bfo = wash_url_argument(bfo, 'str')
            navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/output_formats_manage?ln=%s">%s</a>'''%(CFG_SITE_SECURE_URL, ln, _("Manage Output Formats")))

            if not bibformatadminlib.can_read_output_format(bfo): #No read permission
                try:
                    raise InvenioBibFormatError(_('Output format %s cannot not be read. %s') % (bfo, ""))
                except InvenioBibFormatError, exc:
                    register_exception(req=req)
                    return page(title=_("Restricted Output Format"),
                            body = """You don't have permission
                            to view this output format.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)

            output_format = bibformat_engine.get_output_format(code=bfo,
                                                               with_attributes=True)
            name = output_format['attrs']['names']['generic']
            title = _("Validation of Output Format %s" % name)

        elif bft is not None: #Format template validation
            bft = wash_url_argument(bft, 'str')
            navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_templates_manage?ln=%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln, _("Manage Format Templates")))

            if not bibformatadminlib.can_read_format_template(bft): #No read permission
                try:
                    raise InvenioBibFormatError(_('Format template %s cannot not be read. %s') % (bft, ""))
                except InvenioBibFormatError, exc:
                    register_exception(req=req)
                    return page(title=_("Restricted Format Template"),
                            body = """You don't have permission to
                            view this format template.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)
            name = bibformat_engine.get_format_template_attrs(bft)['name']
            title = _("Validation of Format Template %s" % name)

        elif bfe is not None: #Format element validation
            bfe = wash_url_argument(bfe, 'str')
            navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/format_elements_doc?ln=%s#%s">%s</a>''' % (CFG_SITE_SECURE_URL, ln , bfe.upper() , _("Format Elements Documentation")))

            if not bibformatadminlib.can_read_format_element(bfe) and \
                   not bibformat_dblayer.tag_exists_for_name(bfe): #No read permission
                try:
                    raise InvenioBibFormatError(_('Format element %s cannot not be read. %s') % (bfe, ""))
                except InvenioBibFormatError, exc:
                    register_exception(req=req)
                    return page(title=_("Restricted Format Element"),
                            body = """You don't have permission
                            to view this format element.""",
                            language=ln,
                            navtrail = navtrail_previous_links,
                            lastupdated=__lastupdated__,
                            req=req)
            title = _("Validation of Format Element %s" % bfe)

        else: #No format specified
            try:
                raise InvenioBibFormatError(_('No format specified for validation. Please specify one.'))
            except InvenioBibFormatError, exc:
                register_exception(req=req)
                return page(title=_("Format Validation"),
                        body="No format has been specified.",
                        uid=uid,
                        language=ln,
                        navtrail = navtrail_previous_links,
                        lastupdated=__lastupdated__,
                        req=req)

        return page(title=title,
                    body=bibformatadminlib.perform_request_format_validate(ln=ln,
                                                                           bfo=bfo,
                                                                           bft=bft,
                                                                           bfe=bfe),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    else:
        navtrail_previous_links = bibformatadminlib.getnavtrail(''' &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py/?ln=%s'''%(CFG_SITE_SECURE_URL, ln))

        return page_not_authorized(req=req,
                                   text=auth_msg,
                                   navtrail=navtrail_previous_links)

def download_dreamweaver_floater(req):
    """
    Trigger download of a BibFormat palette for Dreamweaver.

    @param req: the request object
    @return: the palette code to be used within Dreamweaver
    """
    #bibformat_templates = invenio.template.load('bibformat')
    req.content_type = 'text/html'
    req.headers_out["Content-Disposition"] = "attachment; filename=BibFormat_floater.html"
    req.send_http_header()
    req.write(bibformatadminlib.perform_request_dreamweaver_floater())

def dialog_box(req, url="", ln=CFG_SITE_LANG, navtrail="",
               title="", message="", options=[]):
    """
    Returns a dialog box with a given title, message and options.
    Used for asking confirmation on actions.

    The page that will receive the result must take 'chosen_option' as parameter.

    @param req: the request object
    @param url: the url used to submit the options chosen by the user
    @param ln: language
    @param navtrail: navigation trail
    @param title: title of the page/dialog
    @param message: message to display in the dialog box
    @param options: the list of labels for the buttons given as choice to user
    @return: a dialog page
    """
    import invenio
    bibformat_templates = invenio.template.load('bibformat')

    return page(title="",
                body = bibformat_templates.tmpl_admin_dialog_box(url,
                                                                 ln,
                                                                 title,
                                                                 message,
                                                                 options),
                language=ln,
                lastupdated=__lastupdated__,
                navtrail=navtrail,
                req=req)

def error_page(req):
    """
    Returns a default error page

    @param req: the request object
    @return: a web page
    """
    return page(title="Internal Error",
                body = create_error_box(req, ln=CFG_SITE_LANG),
                description="%s - Internal Error" % CFG_SITE_NAME,
                keywords="%s, Internal Error" % CFG_SITE_NAME,
                language=CFG_SITE_LANG)
