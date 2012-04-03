# -*- coding: utf-8 -*-
##
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

"""
Handle requests from the web interface to configure BibFormat.
"""

__revision__ = "$Id$"

import os
import re
import stat
import time
import cgi

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, CFG_ETCDIR
from invenio.bibformat_config import \
     CFG_BIBFORMAT_TEMPLATES_PATH, \
     CFG_BIBFORMAT_OUTPUTS_PATH, \
     CFG_BIBFORMAT_ELEMENTS_PATH, \
     CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION, \
     InvenioBibFormatError
from invenio.urlutils import wash_url_argument
from invenio.errorlib import register_exception
from invenio.messages import gettext_set_language, wash_language, language_list_long
from invenio.search_engine import perform_request_search
from invenio import bibformat_dblayer
from invenio import bibformat_engine
from invenio.textutils import encode_for_xml

import invenio.template
bibformat_templates = invenio.template.load('bibformat')

def getnavtrail(previous = '', ln=CFG_SITE_LANG):
    """
    Get the navtrail

    @param previous: suffix of the navtrail
    @param ln: language
    @return: HTML markup of the navigation trail
    """
    previous = wash_url_argument(previous, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = '''<a class="navtrail" href="%s/help/admin">%s</a> &gt; <a class="navtrail" href="%s/admin/bibformat/bibformatadmin.py?ln=%s">%s</a> ''' % \
               (CFG_SITE_URL, _("Admin Area"), CFG_SITE_URL, ln,  _("BibFormat Admin"))
    navtrail = navtrail + previous
    return navtrail

def perform_request_index(ln=CFG_SITE_LANG, warnings=None, is_admin=False):
    """
    Returns the main BibFormat admin page.

    @param ln: language
    @param is_admin: indicate if user is authorized to use BibFormat
    @return: the main admin page
    """
    return bibformat_templates.tmpl_admin_index(ln, warnings, is_admin)

def perform_request_format_templates_management(ln=CFG_SITE_LANG, checking=0):
    """
    Returns the main management console for format templates

    @param ln: language
    @param checking: the level of checking (0: basic, 1:extensive (time consuming) )
    @return: the main page for format templates management
    """


    # Reload in case a format was changed
    bibformat_engine.clear_caches()

    # Get formats lists of attributes
    formats = bibformat_engine.get_format_templates(with_attributes=True)
    formats_attrs = []
    for filename in formats:
        attrs = formats[filename]['attrs']
        attrs['filename'] = filename
        if filename.endswith('.xsl'):
            attrs['name'] += ' (XSL)'
        attrs['editable'] = can_write_format_template(filename)
        path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename
        try:
            attrs['last_mod_date'] = time.ctime(os.stat(path)[stat.ST_MTIME])
        except OSError:
            # File does not exist. Happens with temporary files
            # created by editors.
            continue

        status = check_format_template(filename, checking)
        import string
        if len(status) > 1 or (len(status)==1 and status[0].find('Could not read format template named') == -1):
            status = '''
            <a style="color: rgb(255, 0, 0);"
            href="%(siteurl)s/admin/bibformat/bibformatadmin.py/validate_format?ln=%(ln)s&amp;bft=%(bft)s">Not OK</a>
            ''' % {'siteurl':CFG_SITE_URL,
                   'ln':ln,
                   'bft':filename}
        else:
            status = '<span style="color: rgb(0, 255, 0);">OK</span>'
        attrs['status'] = status
        formats_attrs.append(attrs)

    def sort_by_attr(seq):
        """
        Sort 'seq' by attribute name.
        @param seq: a list of dictionaries, containing each one key named 'name'
        """
        intermed = [ (x['name'].lower(), i, x) for i, x in enumerate(seq)]
        intermed.sort()
        return [x[-1] for x in intermed]

    sorted_format_templates = sort_by_attr(formats_attrs)

    return bibformat_templates.tmpl_admin_format_templates_management(ln, sorted_format_templates)

def perform_request_format_template_show(bft, ln=CFG_SITE_LANG, code=None,
                                         ln_for_preview=CFG_SITE_LANG, pattern_for_preview="",
                                         content_type_for_preview="text/html"):
    """
    Returns the editor for format templates.

    @param ln: language
    @param bft: the template to edit
    @param code: the code being edited
    @param ln_for_preview: the language for the preview (for bfo)
    @param pattern_for_preview: the search pattern to be used for the preview (for bfo)
    @param content_type_for_preview: content-type to use to serve preview
    @return: the main page for formats management
    """
    format_template = bibformat_engine.get_format_template(filename=bft, with_attributes=True)

    # Either use code being edited, or the original code inside template
    if code is None:
        code = cgi.escape(format_template['code'])

    # Build a default pattern if it is empty
    if pattern_for_preview == "":
        recIDs = perform_request_search()
        if len(recIDs) > 0:
            recID = recIDs[0]
            pattern_for_preview = "recid:%s" % recID

    editable = can_write_format_template(bft)

    # Look for all existing content_types
    content_types = bibformat_dblayer.get_existing_content_types()

    # Add some standard content types if not already there
    standard_content_types = ['text/xml', 'application/rss+xml', 'text/plain', 'text/html']
    content_types.extend([content_type for content_type in standard_content_types
                          if content_type not in content_types])

    return bibformat_templates.tmpl_admin_format_template_show(ln, format_template['attrs']['name'],
                                                               format_template['attrs']['description'],
                                                               code, bft,
                                                               ln_for_preview=ln_for_preview,
                                                               pattern_for_preview=pattern_for_preview,
                                                               editable=editable,
                                                               content_type_for_preview=content_type_for_preview,
                                                               content_types=content_types)

def perform_request_format_template_show_dependencies(bft, ln=CFG_SITE_LANG):
    """
    Show the dependencies (on elements) of the given format.

    @param ln: language
    @param bft: the filename of the template to show
    @return: HTML markup
    """
    format_template = bibformat_engine.get_format_template(filename=bft, with_attributes=True)
    name = format_template['attrs']['name']
    output_formats = get_outputs_that_use_template(bft)
    format_elements = get_elements_used_by_template(bft)
    tags = []
    for output_format in output_formats:
        for tag in output_format['tags']:
            tags.append(tag)
    for format_element in format_elements:
        for tag in format_element['tags']:
            tags.append(tag)

    tags.sort()
    return bibformat_templates.tmpl_admin_format_template_show_dependencies(ln,
                                                                            name,
                                                                            bft,
                                                                            output_formats,
                                                                            format_elements,
                                                                            tags)

def perform_request_format_template_show_attributes(bft, ln=CFG_SITE_LANG, new=False):
    """
    Page for template name and descrition attributes edition.

    If format template is new, offer the possibility to
    make a duplicate of an existing format template.

    @param ln: language
    @param bft: the template to edit
    @param new: if True, the template has just been added (is new)
    @return: the main page for format templates attributes edition
    """
    all_templates = []
    if new:
        all_templates_attrs = bibformat_engine.get_format_templates(with_attributes=True)
        if all_templates_attrs.has_key(bft): # Sanity check. Should always be true at this stage
            del all_templates_attrs[bft] # Remove in order not to make a duplicate of self..

    # Sort according to name, inspired from Python Cookbook

        def sort_by_name(seq, keys):
            """
            Sort the sequence 'seq' by 'keys'
            """
            intermed = [(x['attrs']['name'], keys[i], i, x) for i, x in enumerate(seq)]
            intermed.sort()
            return [(x[1], x[0]) for x in intermed]

        all_templates = sort_by_name(all_templates_attrs.values(), all_templates_attrs.keys())
        #keys = all_templates_attrs.keys()
        #keys.sort()
        #all_templates = map(lambda x: (x, all_templates_attrs.get(x)['attrs']['name']), keys)

    format_template = bibformat_engine.get_format_template(filename=bft, with_attributes=True)
    name = format_template['attrs']['name']
    description = format_template['attrs']['description']
    editable = can_write_format_template(bft)

    return bibformat_templates.tmpl_admin_format_template_show_attributes(ln,
                                                                          name,
                                                                          description,
                                                                          bft,
                                                                          editable,
                                                                          all_templates,
                                                                          new)


def perform_request_format_template_show_short_doc(ln=CFG_SITE_LANG, search_doc_pattern=""):
    """
    Returns the format elements documentation to be included inside format templated editor.

    Keep only elements that have 'search_doc_pattern' text inside description,
    if pattern not empty

    @param ln: language
    @param search_doc_pattern: a search pattern that specified which elements to display
    @return: a brief version of the format element documentation
    """
    # Get format elements lists of attributes
    elements = bibformat_engine.get_format_elements(with_built_in_params=True)

    keys =  elements.keys()
    keys.sort()
    elements = map(elements.get, keys)

    def filter_elem(element):
        """Keep element if is string representation contains all keywords of search_doc_pattern,
        and if its name does not start with a number (to remove 'garbage' from elements in tags table)"""
        if element['type'] != 'python' and \
               element['attrs']['name'][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
        text = str(element).upper() # Basic text representation
        if search_doc_pattern != "":
            for word in search_doc_pattern.split():
                if word.upper() != "AND" and text.find(word.upper()) == -1:
                    return False

        return True

    elements = filter(filter_elem, elements)



    return bibformat_templates.tmpl_admin_format_template_show_short_doc(ln, elements)

def perform_request_format_elements_documentation(ln=CFG_SITE_LANG):
    """
    Returns the main management console for format elements.

    Includes list of format elements and associated administration tools.
    @param ln: language
    @return: the main page for format elements management
    """
    # Get format elements lists of attributes
    elements = bibformat_engine.get_format_elements(with_built_in_params=True)

    keys =  elements.keys()
    keys.sort()
    elements = map(elements.get, keys)
    # Remove all elements found in table and that begin with a number (to remove 'garbage')
    filtered_elements = [element for element in elements \
                         if element is not None and \
                         element['type'] == 'python' and \
                         element['attrs']['name'][0] not in \
                         ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']]

    return bibformat_templates.tmpl_admin_format_elements_documentation(ln, filtered_elements)

def perform_request_format_element_show_dependencies(bfe, ln=CFG_SITE_LANG):
    """
    Show the dependencies of the given format.

    @param ln: language
    @param bfe: the filename of the format element to show
    @return: HTML markup of elements dependencies page
    """
    format_templates = get_templates_that_use_element(bfe)
    tags = get_tags_used_by_element(bfe)

    return bibformat_templates.tmpl_admin_format_element_show_dependencies(ln,
                                                                           bfe,
                                                                           format_templates,
                                                                           tags)

def perform_request_format_element_test(bfe, ln=CFG_SITE_LANG, param_values=None, user_info=None):
    """
    Show the dependencies of the given format.

    'param_values' is the list of values to pass to 'format'
    function of the element as parameters, in the order ...
    If params is None, this means that they have not be defined by user yet.

    @param ln: language
    @param bfe: the name of the format element to show
    @param param_values: the list of parameters to pass to element format function
    @param user_info: the user_info of this request
    @return: HTML markup of elements test page
    """
    _ = gettext_set_language(ln)
    format_element = bibformat_engine.get_format_element(bfe, with_built_in_params=True)

    # Load parameter names and description
    ##
    param_names = []
    param_descriptions = []

    # First value is a search pattern to choose the record
    param_names.append(_("Test with record:")) # Caution: keep in sync with same text below
    param_descriptions.append(_("Enter a search query here."))

    # Parameters defined in this element
    for param in format_element['attrs']['params']:
        param_names.append(param['name'])
        param_descriptions.append(param['description'])

    # Parameters common to all elements of a kind
    for param in format_element['attrs']['builtin_params']:
        param_names.append(param['name'])
        param_descriptions.append(param['description'])

    # Load parameters values
    ##

    if param_values is None: #First time the page is loaded
        param_values = []

        # Propose an existing record id by default
        recIDs = perform_request_search()
        if len(recIDs) > 0:
            recID = recIDs[0]
            param_values.append("recid:%s" % recID)

        # Default values defined in this element
        for param in format_element['attrs']['params']:
            param_values.append(param['default'])

        #Parameters common to all elements of a kind
        for param in format_element['attrs']['builtin_params']:
            param_values.append(param['default'])


    # Execute element with parameters
    ##
    params = dict(zip(param_names, param_values))

    # Find a record corresponding to search pattern
    search_pattern = params[_("Test with record:")] # Caution keep in sync with same text above and below
    recIDs = perform_request_search(p=search_pattern)
    del params[_("Test with record:")] # Caution keep in sync with same text above

    if len(recIDs) > 0:
        bfo = bibformat_engine.BibFormatObject(recID = recIDs[0],
                                               ln = ln,
                                               search_pattern = search_pattern.split(' '),
                                               xml_record = None,
                                               user_info = user_info)
        (result, dummy) = bibformat_engine.eval_format_element(format_element, bfo, params)
    else:
        try:
            raise InvenioBibFormatError(_('No Record Found for %s.') % search_pattern)
        except InvenioBibFormatError, exc:
            register_exception()
            result = exc.message

    return bibformat_templates.tmpl_admin_format_element_test(ln,
                                                              bfe,
                                                              format_element['attrs']['description'],
                                                              param_names,
                                                              param_values,
                                                              param_descriptions,
                                                              result)

def perform_request_output_formats_management(ln=CFG_SITE_LANG, sortby="code"):
    """
    Returns the main management console for output formats.

    Includes list of output formats and associated administration tools.
    @param ln: language
    @param sortby: the sorting crieteria (can be 'code' or 'name')
    @return: the main page for output formats management
    """
    # Reload in case a format was changed
    bibformat_engine.clear_caches()

    # Get output formats lists of attributes
    output_formats_list = bibformat_engine.get_output_formats(with_attributes=True)
    output_formats = {}
    for filename in output_formats_list:
        output_format = output_formats_list[filename]
        code = output_format['attrs']['code']
        path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename
        output_format['editable'] = can_write_output_format(code)
        try:
            output_format['last_mod_date'] = time.ctime(os.stat(path)[stat.ST_MTIME])
        except OSError:
            # File does not exist. Happens with temporary files
            # created by editors.
            continue
        # Validate the output format
        status = check_output_format(code)
        # If there is an error but the error is just 'format is not writable', do not display as error
        if len(status) > 1 or (len(status)==1 and status[0].find('BibFormat could not write to output format') == -1):
            status = '''
            <a style="color: rgb(255, 0, 0);"
            href="%(siteurl)s/admin/bibformat/bibformatadmin.py/validate_format?ln=%(ln)s&bfo=%(bfo)s">Not OK</a>
            ''' % {'siteurl':CFG_SITE_URL,
                   'ln':ln,
                   'bfo':code}
        else:
            status = '<span style="color: rgb(0, 255, 0);">OK</span>'
        output_format['status'] = status
        output_formats[filename] = output_format

    # Sort according to code or name, inspired from Python Cookbook
    def get_attr(dic, attr):
        """
        Returns the value given by 'attr' in the dictionary 'dic', representing
        an output format attributes.
        If attr is equal to 'code', returns the code attribute of the dictionary.
        Else returns the generic name

        @param dic: a dictionary of the attribute of an output format, as returned by bibformat_engine.get_output_format
        @param the: attribute we want to fetch. Either 'code' or any other string
        """
        if attr == "code":
            return dic['attrs']['code']
        else:
            return dic['attrs']['names']['generic']

    def sort_by_attr(seq, attr):
        """
        Sort dictionaries given in 'seq' according to parameter 'attr'
        """
        intermed = [ (get_attr(x, attr), i, x) for i, x in enumerate(seq)]
        intermed.sort()
        return [x[-1] for x in intermed]

    if sortby != "code" and sortby != "name":
        sortby = "code"

    sorted_output_formats = sort_by_attr(output_formats.values(), sortby)

    return bibformat_templates.tmpl_admin_output_formats_management(ln, sorted_output_formats)

def perform_request_output_format_show(bfo, ln=CFG_SITE_LANG, r_fld=[], r_val=[], r_tpl=[], default="", r_upd="", args={}):
    """
    Returns the editing tools for a given output format.

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

    IMPORTANT: we display rules evaluation index starting at 1 in
    interface, but we start internally at 0

    @param ln: language
    @param bfo: the filename of the output format to show
    @param r_fld: the list of 'field' attribute for each rule
    @param r_val: the list of 'value' attribute for each rule
    @param r_tpl: the list of 'template' attribute for each rule
    @param default: the default format template used by this output format
    @param r_upd: the rule that we want to increase/decrease in order of evaluation
    @param args: additional parameters to move rules. See above
    @return: HTML markuo for editing tools of a given output format.
    """

    output_format = bibformat_engine.get_output_format(bfo, with_attributes=True)
    format_templates =  bibformat_engine.get_format_templates(with_attributes=True)
    name = output_format['attrs']['names']['generic']
    rules = []
    debug = ""
    if len(r_fld) == 0 and r_upd=="":
        # Retrieve rules from file
        rules = output_format['rules']
        default = output_format['default']
    else:
        # Retrieve rules from given lists

        # Transform a single rule (not considered as a list with length
        # 1 by the templating system) into a list
        if not isinstance(r_fld, list):
            r_fld = [r_fld]
            r_val = [r_val]
            r_tpl = [r_tpl]

        for i in range(len(r_fld)):
            rule = {'field': r_fld[i],
                    'value': r_val[i],
                    'template': r_tpl[i]}
            rules.append(rule)
        # Execute action
        _ = gettext_set_language(ln)
        if r_upd.startswith(_("Remove Rule")):
            # Remove rule
            index = int(r_upd.split(" ")[-1]) -1
            del rules[index]
        elif r_upd.startswith(_("Save Changes")):
            # Save
            update_output_format_rules(bfo, rules, default)
        elif r_upd.startswith(_("Add New Rule")):
            # Add new rule
            rule = {'field': "",
                    'value': "",
                    'template': ""}
            rules.append(rule)
        else:
            # Get the action in 'args'
            # The action must be constructed from string of the kind:
            # + 5  or  - 4  or + 5.x  or -4.y
            for button_val in args.keys():#for all elements of form not handled yet
                action = button_val.split(" ")
                if action[0] == '-' or action[0] == '+':
                    index = int(action[1].split(".")[0]) -1
                    if action[0] == '-':
                        # Decrease priority
                        rule = rules[index]
                        del rules[index]
                        rules.insert(index + 1, rule)
                        # debug = 'Decrease rule '+ str(index)
                        break
                    elif action[0] == '+':
                        # Increase priority
                        rule = rules[index]
                        del rules[index]
                        rules.insert(index - 1, rule)
                        # debug = 'Increase rule ' + str(index)
                        break


    editable = can_write_output_format(bfo)

    return bibformat_templates.tmpl_admin_output_format_show(ln,
                                                            bfo,
                                                            name,
                                                            rules,
                                                            default,
                                                            format_templates,
                                                            editable)

def perform_request_output_format_show_dependencies(bfo, ln=CFG_SITE_LANG):
    """
    Show the dependencies of the given format.

    @param ln: language
    @param bfo: the filename of the output format to show
    @return: HTML markup of the output format dependencies pages
    """
    output_format = bibformat_engine.get_output_format(code=bfo, with_attributes=True)
    name = output_format['attrs']['names']['generic']
    format_templates = get_templates_used_by_output(bfo)

    return bibformat_templates.tmpl_admin_output_format_show_dependencies(ln,
                                                                          name,
                                                                          bfo,
                                                                          format_templates)

def perform_request_output_format_show_attributes(bfo, ln=CFG_SITE_LANG):
    """
    Page for output format names and description attributes edition.

    @param ln: language
    @param bfo: filename of output format to edit
    @return: the main page for output format attributes edition
    """
    output_format = bibformat_engine.get_output_format(code=bfo, with_attributes=True)

    name = output_format['attrs']['names']['generic']
    description = output_format['attrs']['description']
    content_type = output_format['attrs']['content_type']
    visible = output_format['attrs']['visibility']
    # Get translated names. Limit to long names now.
    # Translation are given in order of languages in language_list_long()
    names_trans = []
    for lang in language_list_long():
        name_trans = output_format['attrs']['names']['ln'].get(lang[0], "")
        names_trans.append({'lang':lang[1], 'trans':name_trans})

    editable = can_write_output_format(bfo)

    return bibformat_templates.tmpl_admin_output_format_show_attributes(ln,
                                                                        name,
                                                                        description,
                                                                        content_type,
                                                                        bfo,
                                                                        names_trans,
                                                                        editable,
                                                                        visible)

def add_format_template():
    """
    Adds a new format template (mainly create file with unique name)

    @return: the filename of the created format
    """
    (filename, name) = bibformat_engine.get_fresh_format_template_filename("Untitled")

    out = ""
    if not filename.endswith(".xsl"):
        out = '<name>%(name)s</name><description></description>' % {'name': name}
    path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename
    format = open(path, 'w')
    format.write(out)
    format.close

    return filename

def delete_format_template(filename):
    """
    Delete a format template given by its filename

    If format template is not writable, do not remove

    @param filename: the format template filename
    @return: None
    """
    if not can_write_format_template(filename):
        return

    path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename
    os.remove(path)
    bibformat_engine.clear_caches()

def update_format_template_code(filename, code=""):
    """
    Saves code inside template given by filename

    @param filename: filename of the template to edit
    @param code: content of the template
    @return: None
    """
    format_template = bibformat_engine.get_format_template_attrs(filename)
    name = format_template['name']
    description = format_template['description']
    code = re.sub("\r\n", "\n", code)
    out = ""
    if not filename.endswith(".xsl"):
        out = """<name>%(name)s</name>
<description>%(description)s</description>
""" % {'name': name, 'description': description}
    out += code
    path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename
    format = open(path, 'w')
    format.write(out)
    format.close

    bibformat_engine.clear_caches()

def update_format_template_attributes(filename, name="", description="", duplicate=None):
    """
    Saves name and description inside template given by filename.

    the filename must change according to name, and every output format
    having reference to filename must be updated.

    If name already exist, use fresh filename (we never overwrite other templates) amd
    remove old one.

    if duplicate is different from None and is not empty string, then it means that we must copy
    the code of the template whoose filename is given in 'duplicate' for the code
    of our template.

    @param filename: filename of the template to update
    @param name: name to use for the template
    @param description: description to use for the template
    @param duplicate: the filename of a template that we want to copy
    @return: the filename of the modified format
    """
    if filename.endswith('.'+CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
        format_template = bibformat_engine.get_format_template(filename, with_attributes=True)
        if duplicate is not None and duplicate != "":
            format_template_to_copy = bibformat_engine.get_format_template(duplicate)
            code = format_template_to_copy['code']
        else:
            code = format_template['code']
        if format_template['attrs']['name'] != name:
            # Name has changed, so update filename
            old_filename = filename
            old_path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + old_filename
            # Remove old one
            os.remove(old_path)

            (filename, name) = bibformat_engine.get_fresh_format_template_filename(name)

            # Change output formats that calls this template
            output_formats = bibformat_engine.get_output_formats()

            for output_format_filename in output_formats:
                if can_read_output_format(output_format_filename) and can_write_output_format(output_format_filename):
                    output_path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + output_format_filename
                    format = open(output_path, 'r')
                    output_text = format.read()
                    format.close
                    output_pattern = re.compile("---(\s)*" + old_filename, re.IGNORECASE)
                    mod_output_text = output_pattern.sub("--- " + filename, output_text)
                    if output_text != mod_output_text:
                        format = open(output_path, 'w')
                        format.write(mod_output_text)
                        format.close

        description = cgi.escape(description)
        name = cgi.escape(name)
        # Write updated format template
        out = ""
        if not filename.endswith(".xsl"):
            out = """<name>%(name)s</name><description>%(description)s</description>""" % {'name': name,
                                                                                           'description': description,}
        out += code

        path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename
        format = open(path, 'w')
        format.write(out)
        format.close

        bibformat_engine.clear_caches()

    return filename

def add_output_format():
    """
    Adds a new output format (mainly create file with unique name)

    @return: the code of the created format, or None if it could not be created
    """

    if not os.access(CFG_BIBFORMAT_OUTPUTS_PATH, os.W_OK):
        return None

    (filename, code) = bibformat_engine.get_fresh_output_format_filename("UNTLD")

    # Add entry in database
    bibformat_dblayer.add_output_format(code)
    bibformat_dblayer.set_output_format_name(code, "Untitled", lang="generic")
    bibformat_dblayer.set_output_format_content_type(code, "text/html")

    # Add file
    out = ""
    path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename
    format = open(path, 'w')
    format.write(out)
    format.close

    return code

def delete_output_format(code):
    """
    Delete a format template given by its code

    if file is not writable, don't remove

    @param code: the 6 letters code of the output format to remove
    @return: None
    """
    if not can_write_output_format(code):
        return

    # Remove entry from database
    bibformat_dblayer.remove_output_format(code)

    # Remove file
    filename = bibformat_engine.resolve_output_format_filename(code)
    path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename
    os.remove(path)

    bibformat_engine.clear_caches()


def update_output_format_rules(code, rules=[], default=""):
    """
    Saves rules inside output format given by code

    @param code: the code of the output format to update
    @param rules: the rules to apply for the output format
    @param default: the default template when no rule match
    @return: None
    """

    # Generate output format syntax
    # Try to group rules by field
    previous_field = ""
    out = ""
    for rule in rules:
        field = rule["field"]
        value = rule["value"]
        template = rule["template"]
        if previous_field != field:
            out += "tag %s:\n" % field

        out +="%(value)s --- %(template)s\n" % {'value':value, 'template':template}
        previous_field = field

    out += "default: %s" % default
    filename = bibformat_engine.resolve_output_format_filename(code)
    path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename
    format = open(path, 'w')
    format.write(out)
    format.close

    bibformat_engine.clear_caches()

def update_output_format_attributes(code, name="", description="", new_code="",
                                    content_type="", names_trans=[], visibility=1):
    """
    Saves name and description inside output format given by filename.

    If new_code already exist, use fresh code (we never overwrite other output).

    @param description: the new description
    @param name: the new name
    @param new_code: the new short code (== new bfo) of the output format
    @param code: the code of the output format to update
    @param names_trans: the translations in the same order as the languages from get_languages()
    @param content_type: the new content_type of the output format
    @param visibility: the visibility of the output format in the output formats list (public pages)
    @return: the filename of the modified format
    """

    bibformat_dblayer.set_output_format_description(code, description)
    bibformat_dblayer.set_output_format_content_type(code, content_type)
    bibformat_dblayer.set_output_format_visibility(code, visibility)
    bibformat_dblayer.set_output_format_name(code, name, lang="generic")
    i = 0
    for lang in language_list_long():
        if names_trans[i] != "":
            bibformat_dblayer.set_output_format_name(code, names_trans[i], lang[0])
        i += 1

    new_code = new_code.upper()
    if code != new_code:
        # If code has changed, we must update filename with a new unique code
        old_filename = bibformat_engine.resolve_output_format_filename(code)
        old_path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + old_filename
        (new_filename, new_code) = bibformat_engine.get_fresh_output_format_filename(new_code)
        new_path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + new_filename
        os.rename(old_path, new_path)
        bibformat_dblayer.change_output_format_code(code, new_code)

    bibformat_engine.clear_caches()

    return new_code

def can_read_format_template(filename):
    """
    Returns 0 if we have read permission on given format template, else
    returns other integer

    @param filename: name of a format template
    @return: True if template X{bft} can be read or not
    """
    path = "%s%s%s" % (CFG_BIBFORMAT_TEMPLATES_PATH, os.sep, filename)
    return os.access(path, os.R_OK)

def can_read_output_format(bfo):
    """
    Returns 0 if we have read permission on given output format, else
    returns other integer

    @param bfo: name of an output format
    @return: True if output format X{bfo} can be read or not
    """
    filename = bibformat_engine.resolve_output_format_filename(bfo)
    path = "%s%s%s" % (CFG_BIBFORMAT_OUTPUTS_PATH, os.sep, filename)
    return os.access(path, os.R_OK)

def can_read_format_element(name):
    """
    Returns 0 if we have read permission on given format element, else
    returns other integer

    @param name: name of a format element
    @return: True if element X{name} can be read or not
    """

    filename = bibformat_engine.resolve_format_element_filename(name)
    path = "%s%s%s" % (CFG_BIBFORMAT_ELEMENTS_PATH, os.sep, filename)
    return os.access(path, os.R_OK)

def can_write_format_template(bft):
    """
    Returns 0 if we have write permission on given format template, else
    returns other integer

    @param bft: name of a format template
    @return: True if template X{bft} can be edited or not
    """
    if not can_read_format_template(bft):
        return False

    path = "%s%s%s" % (CFG_BIBFORMAT_TEMPLATES_PATH, os.sep, bft)
    return os.access(path, os.W_OK)

def can_write_output_format(bfo):
    """
    Returns 0 if we have write permission on given output format, else
    returns other integer

    @param bfo: name of an output format
    @return: True if output format X{bfo} can be edited or not
    """
    if not can_read_output_format(bfo):
        return False

    filename = bibformat_engine.resolve_output_format_filename(bfo)
    path = "%s%s%s" % (CFG_BIBFORMAT_OUTPUTS_PATH, os.sep, filename)
    return os.access(path, os.W_OK)

def can_write_etc_bibformat_dir():
    """
    Returns true if we can write in etc/bibformat dir.

    @return: True if can write, or False
    """
    path = "%s%sbibformat" % (CFG_ETCDIR, os.sep)
    return os.access(path, os.W_OK)

def get_outputs_that_use_template(filename):
    """
    Returns a list of output formats that call the given format template.
    The returned output formats also give their dependencies on tags.

    We don't return the complete output formats but some reference to
    them (filename + names)::

        [ {'filename':"filename_1.bfo"
           'names': {'en':"a name", 'fr': "un nom", 'generic':"a name"}
           'tags': ['710__a', '920__']
          },
          ...
        ]

    @param filename: a format template filename
    @return: output formats references sorted by (generic) name
    """
    output_formats_list = {}
    tags = []
    output_formats = bibformat_engine.get_output_formats(with_attributes=True)
    for output_format in output_formats:
        name = output_formats[output_format]['attrs']['names']['generic']
        # First look at default template, and add it if necessary
        if output_formats[output_format]['default'] == filename:
            output_formats_list[name] = {'filename':output_format,
                                         'names':output_formats[output_format]['attrs']['names'],
                                         'tags':[]}
        # Second look at each rule
        found = False
        for rule in output_formats[output_format]['rules']:
            if rule['template'] == filename:
                found = True
                tags.append(rule['field']) #Also build dependencies on tags

        # Finally add dependency on template from rule (overwrite default dependency,
        # which is weaker in term of tag)
        if found:
            output_formats_list[name] = {'filename':output_format,
                                         'names':output_formats[output_format]['attrs']['names'],
                                         'tags':tags}



    keys = output_formats_list.keys()
    keys.sort()
    return map(output_formats_list.get, keys)

def get_elements_used_by_template(filename):
    """
    Returns a list of format elements that are called by the given format template.
    The returned elements also give their dependencies on tags.

    Dependencies on tag might be approximative. See get_tags_used_by_element()
    doc string.

    We must handle usage of bfe_field in a special way if we want to retrieve
    used tag: used tag is given in "tag" parameter, not inside element code.

    The list is returned sorted by name::

        [ {'filename':"filename_1.py"
           'name':"filename_1"
           'tags': ['710__a', '920__']
          },
          ...
        ]

    @param filename: a format template filename
    @return: elements sorted by name
    """
    format_elements = {}
    format_template = bibformat_engine.get_format_template(filename=filename, with_attributes=True)
    code = format_template['code']
    format_elements_iter = bibformat_engine.pattern_tag.finditer(code)
    for result in format_elements_iter:
        function_name = result.group("function_name").lower()
        if function_name is not None and not format_elements.has_key(function_name) \
               and not function_name == "field":
            filename = bibformat_engine.resolve_format_element_filename("BFE_"+function_name)
            if filename is not None:
                tags = get_tags_used_by_element(filename)
                format_elements[function_name] = {'name':function_name.lower(),
                                                  'filename':filename,
                                                  'tags':tags}
        elif function_name == "field":
            # Handle bfe_field element in a special way
            if not format_elements.has_key(function_name):
                #Indicate usage of bfe_field if not already done
                filename = bibformat_engine.resolve_format_element_filename("BFE_"+function_name)
                format_elements[function_name] = {'name':function_name.lower(),
                                                  'filename':filename,
                                                  'tags':[]}
            # Retrieve value of parameter "tag"
            all_params = result.group('params')
            function_params_iterator = bibformat_engine.pattern_function_params.finditer(all_params)
            for param_match in function_params_iterator:
                name = param_match.group('param')
                if name == "tag":
                    value = param_match.group('value')
                    if not value in format_elements[function_name]['tags']:
                        format_elements[function_name]['tags'].append(value)
                    break

    keys = format_elements.keys()
    keys.sort()
    return map(format_elements.get, keys)


# Format Elements Dependencies
##

def get_tags_used_by_element(filename):
    """
    Returns a list of tags used by given format element

    APPROXIMATIVE RESULTS: the tag are retrieved in field(), fields()
    and control_field() function. If they are used computed, or saved
    in a variable somewhere else, they are not retrieved
    @TODO: There is room for improvements. For example catch
    call to BibRecord functions.

    @param filename: a format element filename
    @return: tags sorted by value
    """
    tags = {}

    format_element = bibformat_engine.get_format_element(filename)
    if format_element is None:
        return []
    elif format_element['type']=="field":
        tags = format_element['attrs']['tags']
        return tags

    filename = bibformat_engine.resolve_format_element_filename(filename)
    path = CFG_BIBFORMAT_ELEMENTS_PATH + os.sep + filename
    format = open(path, 'r')
    code = format.read()
    format.close
    tags_pattern = re.compile('''
    (field|fields|control_field)\s*       #Function call
    \(\s*                                 #Opening parenthesis
    [\'"]+                                #Single or double quote
    (?P<tag>.+?)                          #Tag
    [\'"]+\s*                             #Single or double quote
    (,[^\)]+)*                            #Additional function param
    \)                                    #Closing parenthesis
     ''', re.VERBOSE | re.MULTILINE)

    tags_iter = tags_pattern.finditer(code)
    for result in tags_iter:
        tags[result.group("tag")] = result.group("tag")

    return tags.values()

def get_templates_that_use_element(name):
    """
    Returns a list of format templates that call the given format element.
    The returned format templates also give their dependencies on tags::

        [ {'filename':"filename_1.bft"
           'name': "a name"
           'tags': ['710__a', '920__']
          },
          ...
        ]

    @param name: a format element name
    @return: templates sorted by name
    """
    format_templates = {}
    tags = []
    files = os.listdir(CFG_BIBFORMAT_TEMPLATES_PATH) #Retrieve all templates
    for possible_template in files:
        if possible_template.endswith(CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
            format_elements = get_elements_used_by_template(possible_template) #Look for elements used in template
            format_elements = map(lambda x: x['name'].lower(), format_elements)
            try: #Look for element
                format_elements.index(name.lower()) #If not found, get out of "try" statement

                format_template = bibformat_engine.get_format_template(filename=possible_template, with_attributes=True)
                template_name = format_template['attrs']['name']
                format_templates[template_name] = {'name':template_name,
                                                   'filename':possible_template}
            except:
                pass

    keys = format_templates.keys()
    keys.sort()
    return map(format_templates.get, keys)

# Output Formats Dependencies
##

def get_templates_used_by_output(code):
    """
    Returns a list of templates used inside an output format give by its code
    The returned format templates also give their dependencies on elements and tags::

        [ {'filename':"filename_1.bft"
           'name': "a name"
           'elements': [{'filename':"filename_1.py", 'name':"filename_1", 'tags': ['710__a', '920__']
          }, ...]
          },
          ...
        ]

    @param code: outpout format code
    @return: templates sorted by name
    """
    format_templates = {}
    output_format = bibformat_engine.get_output_format(code, with_attributes=True)

    filenames = map(lambda x: x['template'], output_format['rules'])
    if output_format['default'] != "":
        filenames.append(output_format['default'])

    for filename in filenames:
        template = bibformat_engine.get_format_template(filename, with_attributes=True)
        name = template['attrs']['name']
        elements = get_elements_used_by_template(filename)
        format_templates[name] = {'name':name,
                                  'filename':filename,
                                  'elements':elements}


    keys = format_templates.keys()
    keys.sort()
    return map(format_templates.get, keys)


# Validation tools
##

def perform_request_format_validate(ln=CFG_SITE_LANG, bfo=None, bft=None, bfe=None):
    """
    Returns a page showing the status of an output format or format
    template or format element. This page is called from output
    formats management page or format template management page or
    format elements documentation.

    The page only shows the status of one of the format, depending on
    the specified one. If multiple are specified, shows the first one.

    @param ln: language
    @param bfo: an output format 6 chars code
    @param bft: a format element filename
    @param bfe: a format element name
    @return: HTML markup
    """

    if bfo is not None:
        messages = check_output_format(bfo)
    elif bft is not None:
        messages = check_format_template(bft, checking=1)
    elif bfe is not None:
        messages = check_format_element(bfe)
    if messages is None:
        messages = []

    messages = map(lambda x: encode_for_xml(x[1]), messages)

    return bibformat_templates.tmpl_admin_validate_format(ln, messages)


def check_output_format(code):
    """
    Returns the list of errors in the output format given by code

    The errors are the formatted errors defined in bibformat_config.py file.

    @param code: the 6 chars code of the output format to check
    @return: a list of errors
    """
    _ = gettext_set_language(CFG_SITE_LANG)
    errors = []
    filename = bibformat_engine.resolve_output_format_filename(code)
    if can_read_output_format(code):
        path = CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename
        format = open(path)
        current_tag = ''
        i = 0
        for line in format:
            i += 1
            if line.strip() == "":
                # Ignore blank lines
                continue
            clean_line = line.rstrip("\n\r ") #remove spaces and eol
            if line.strip().endswith(":") or (line.strip().lower().startswith("tag") and line.find('---') == -1):
                # Check tag
                if not clean_line.endswith(":"):
                    # Column misses at the end of line
                    try:
                        raise InvenioBibFormatError(_('Tag specification "%s" must end with column ":" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                if not clean_line.lower().startswith("tag"):
                    # Tag keyword is missing
                    try:
                        raise InvenioBibFormatError(_('Tag specification "%s" must start with "tag" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                elif not clean_line.startswith("tag"):
                    # Tag was not lower case
                    try:
                        raise InvenioBibFormatError(_('"tag" must be lowercase in "%s" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)

                clean_line = clean_line.rstrip(": ") #remove : and spaces at the end of line

                current_tag = "".join(clean_line.split()[1:]).strip() #the tag starts at second position
                if len(clean_line.split()) > 2: #We should only have 'tag' keyword and tag
                    try:
                        raise InvenioBibFormatError(_('Should be "tag field_number:" at line %s.') % i)
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                else:
                    if len(check_tag(current_tag)) > 0:
                        # Invalid tag
                        try:
                            raise InvenioBibFormatError(_('Invalid tag "%s" at line %s.') % (current_tag, i))
                        except InvenioBibFormatError, exc:
                            register_exception()
                            errors.append(exc.message)
                    if not clean_line.startswith("tag"):
                        try:
                            raise InvenioBibFormatError(_('Should be "tag field_number:" at line %s.') % i)
                        except InvenioBibFormatError, exc:
                            register_exception()
                            errors.append(exc.message)

            elif line.find('---') != -1:
                # Check condition
                if current_tag == "":
                    try:
                        raise InvenioBibFormatError(_('Condition "%s" is outside a tag specification at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)

                words = line.split('---')
                if len(words) != 2:
                    try:
                        raise InvenioBibFormatError(_('Condition "%s" can only have a single separator --- at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                template = words[-1].strip()
                path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + template
                if not os.path.exists(path):
                    try:
                        raise InvenioBibFormatError(_('Template "%s" does not exist at line %s.') % (template, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)

            elif line.find(':') != -1 or (line.strip().lower().startswith("default") and line.find('---') == -1):
                # Check default template
                clean_line = line.strip()
                if line.find(':') == -1:
                    # Column misses after default
                    try:
                        raise InvenioBibFormatError(_('Missing column ":" after "default" in "%s" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                if not clean_line.startswith("default"):
                    # Default keyword is missing
                    try:
                        raise InvenioBibFormatError(_('Default template specification "%s" must start with "default :" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                if not clean_line.startswith("default"):
                    # Default was not lower case
                    try:
                        raise InvenioBibFormatError(_('"default" keyword must be lowercase in "%s" at line %s.') % (line, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                default = "".join(line.split(':')[1]).strip()
                path = CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + default
                if not os.path.exists(path):
                    try:
                        raise InvenioBibFormatError(_('Template "%s" does not exist at line %s.') % (default, i))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)

            else:
                # Check others
                try:
                    raise InvenioBibFormatError(_('Line %s could not be understood at line %s.') % (line, i))
                except InvenioBibFormatError, exc:
                    register_exception()
                    errors.append(exc.message)
    else:
        try:
            raise InvenioBibFormatError(_('Output format %s cannot not be read. %s') % (filename, ""))
        except InvenioBibFormatError, exc:
            register_exception()
            errors.append(exc.message)

    return errors

def check_format_template(filename, checking=0):
    """
    Returns the list of errors in the format template given by its filename

    The errors are the formatted errors defined in bibformat_config.py file.

    @param filename: the filename of the format template to check
    @param checking: the level of checking (0:basic, >=1 extensive (time-consuming))
    @return: a list of errors
    """
    errors = []
    _ = gettext_set_language(CFG_SITE_LANG)
    if can_read_format_template(filename):#Can template be read?
        if filename.endswith('.'+CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
            #format_template = bibformat_engine.get_format_template(filename, with_attributes=True)
            format = open("%s%s%s" % (CFG_BIBFORMAT_TEMPLATES_PATH, os.sep, filename))
            code = format.read()
            format.close()
            # Look for name
            match = bibformat_engine.pattern_format_template_name.search(code)
            if match is None:#Is tag <name> defined in template?
                try:
                    raise InvenioBibFormatError(_('Could not find a name specified in tag "<name>" inside format template %s.') % filename)
                except InvenioBibFormatError, exc:
                    register_exception()
                    errors.append(exc.message)

            # Look for description
            match = bibformat_engine.pattern_format_template_desc.search(code)
            if match is None:#Is tag <description> defined in template?
                try:
                    raise InvenioBibFormatError(_('Could not find a description specified in tag "<description>" inside format template %s.') % filename)
                except InvenioBibFormatError, exc:
                    register_exception()
                    errors.append(exc.message)

            format_template = bibformat_engine.get_format_template(filename, with_attributes=False)
            code = format_template['code']
            # Look for calls to format elements
            # Check existence of elements and attributes used in call
            elements_call = bibformat_engine.pattern_tag.finditer(code)
            for element_match in elements_call:
                element_name = element_match.group("function_name")
                filename = bibformat_engine.resolve_format_element_filename(element_name)
                if filename is None and not bibformat_dblayer.tag_exists_for_name(element_name): #Is element defined?
                    try:
                        raise InvenioBibFormatError(_('Format template %s calls undefined element "%s".') % (filename, element_name))
                    except InvenioBibFormatError, exc:
                        register_exception()
                        errors.append(exc.message)
                else:
                    format_element = bibformat_engine.get_format_element(element_name, with_built_in_params=True)
                    if format_element is None:#Can element be loaded?
                        if not can_read_format_element(element_name):
                            try:
                                raise InvenioBibFormatError(_('Format template %s calls unreadable element "%s". Check element file permissions.') % (filename, element_name))
                            except InvenioBibFormatError, exc:
                                register_exception()
                                errors.append(exc.message)
                        else:
                            try:
                                raise InvenioBibFormatError(_('Cannot load element "%s" in template %s. Check element code.') % (element_name, filename))
                            except InvenioBibFormatError, exc:
                                register_exception()
                                errors.append(exc.message)
                    else:
                        # Are the parameters used defined in element?
                        params_call = bibformat_engine.pattern_function_params.finditer(element_match.group())
                        all_params = {}
                        for param_match in params_call:
                            param = param_match.group("param")
                            value = param_match.group("value")
                            all_params[param] = value
                            allowed_params = []

                            # Built-in params
                            for allowed_param in format_element['attrs']['builtin_params']:
                                allowed_params.append(allowed_param['name'])

                            # Params defined in element
                            for allowed_param in format_element['attrs']['params']:
                                allowed_params.append(allowed_param['name'])

                            if not param in allowed_params:
                                try:
                                    raise InvenioBibFormatError(_('Format element %s uses unknown parameter "%s" in format template %s.') % (element_name, param, filename))
                                except InvenioBibFormatError, exc:
                                    register_exception()
                                    errors.append(exc.message)

                        # The following code is too much time consuming. Only do where really requested
                        if checking > 0:
                            # Try to evaluate, with any object and pattern
                            recIDs = perform_request_search()
                            if len(recIDs) > 0:
                                recID = recIDs[0]
                                bfo = bibformat_engine.BibFormatObject(recID, search_pattern="Test")
                                (result, errors_) = bibformat_engine.eval_format_element(format_element, bfo, all_params, verbose=7)
                                errors.extend(errors_)

    else:# Template cannot be read
        try:
            raise InvenioBibFormatError(_('Could not read format template named %s. %s') % (filename, ""))
        except InvenioBibFormatError, exc:
            register_exception()
            errors.append(exc.message)
    return errors

def check_format_element(name):
    """
    Returns the list of errors in the format element given by its name

    The errors are the formatted errors defined in bibformat_config.py file.

    @param name: the name of the format element to check
    @return: a list of errors
    """
    errors = []
    _ = gettext_set_language(CFG_SITE_LANG)
    filename = bibformat_engine.resolve_format_element_filename(name)
    if filename is not None:#Can element be found in files?
        if can_read_format_element(name):#Can element be read?
            # Try to load
            try:
                module_name = filename
                if module_name.endswith(".py"):
                    module_name = module_name[:-3]

                module = __import__("invenio.bibformat_elements."+module_name)
                try:
                    function_format  = module.bibformat_elements.__dict__[module_name].format_element
                except AttributeError, e:
                    function_format  = module.bibformat_elements.__dict__[module_name].format

                # Try to evaluate, with any object and pattern
                recIDs = perform_request_search()
                if len(recIDs) > 0:
                    recID = recIDs[0]
                    bfo = bibformat_engine.BibFormatObject(recID, search_pattern="Test")
                    element = bibformat_engine.get_format_element(name)
                    (result, errors_) = bibformat_engine.eval_format_element(element, bfo, verbose=7)
                    errors.extend(errors_)
            except Exception, e:
                try:
                    raise InvenioBibFormatError(_('Error in format element %s. %s.') % (name, e))
                except InvenioBibFormatError, exc:
                    register_exception()
                    errors.append(exc.message)
        else:
            try:
                raise InvenioBibFormatError(_('Format element %s cannot not be read. %s') % (filename, ""))
            except InvenioBibFormatError, exc:
                register_exception()
                errors.append(exc.message)
    elif bibformat_dblayer.tag_exists_for_name(name):#Can element be found in database?
        pass
    else:
        try:
            raise InvenioBibFormatError(_('Could not find format element named %s.') % name)
        except InvenioBibFormatError, exc:
            register_exception()
            errors.append(exc.message)
    return errors

def check_tag(tag):
    """
    Checks the validity of a tag

    @param tag: tag to check
    @return: list of errors for the tag
    """
    errors = []
    return errors


def perform_request_dreamweaver_floater():
    """
    Returns a floater for Dreamweaver with all Format Elements available.

    @return: HTML markup (according to Dreamweaver specs)
    """
    # Get format elements lists of attributes
    elements = bibformat_engine.get_format_elements(with_built_in_params=True)

    keys =  elements.keys()
    keys.sort()
    elements = map(elements.get, keys)

    def filter_elem(element):
        """Keep element if is string representation contains all keywords of search_doc_pattern,
        and if its name does not start with a number (to remove 'garbage' from elements in tags table)"""
        if element['type'] != 'python' and \
               element['attrs']['name'][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
        else:
            return True

    elements = filter(filter_elem, elements)

    return bibformat_templates.tmpl_dreamweaver_floater(CFG_SITE_LANG, elements)




