## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

"""Invenio BibSort Administrator Interface."""

from invenio.access_control_engine import acc_authorize_action
from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_URL, CFG_BIBSORT_BUCKETS, CFG_ETCDIR, CFG_SITE_LANG
from invenio.messages import gettext_set_language, language_list_long
from invenio.bibsort_engine import delete_all_data_for_method, add_sorting_method
from invenio.bibsort_washer import get_all_available_washers
from invenio.bibrankadminlib import write_outcome, modify_translations, \
    get_i8n_name, get_languages, \
    tupletotable, createhiddenform


def perform_index(ln, action, bsrcode, sm_name, sm_def_type, sm_def_value, sm_washer, sm_locale):
    """
    Create the BibSort main page that displays all the sorting methods.
    """
    _ = gettext_set_language(ln)

    out = create_important_box('<p>If you have questions, please see the %s.</p>' \
                               %get_admin_guide_link(ln), '#66CCFF')

    if not CFG_BIBSORT_BUCKETS:
        return create_important_box('<p>BibSort is not enabled. In order to enable it, \
                                    CFG_BIBSORT_BUCKETS needs to have a positive value.<br\>\
                                    Please see the %s for more details.</p>' %get_admin_guide_link(ln))

    #Treatment of the possible actions
    if action == 'delete':
        result = delete_all_data_for_method(bsrcode)
        if not result:
            return create_important_box('<p> There was an error deleting method %s. <br/>\
                                   You can try deleting methods directly in the config file: \
                                   (<b>%s/bibsort/bibsort.cfg</b>) <br/>\
                                   and then load the configuration into the database using the command line tool.<br/>\
                                   Please see the %s for more details.</p>' \
                                   %(bsrcode, CFG_ETCDIR, get_admin_guide_link(ln)))

    elif action == 'add':
        sm_method = '%s: %s' % (sm_def_type.upper(), sm_def_value)
        if sm_locale != 'en':
            #it's not the default one, let's store it in the db with the washer
            sm_washer += ':%s' % sm_locale
        result = add_sorting_method(sm_name, sm_method, sm_washer)
        if not result:
            return create_important_box('<p> There was an error adding method %s. <br/>\
                                   You can try adding methods directly in the config file: \
                                   (<b>%s/bibsort/bibsort.cfg</b>) \
                                   and then load the configuration into the database using the command line tool.<br/>\
                                   Please see the %s for more details.</p>' \
                                   %(sm_name, CFG_ETCDIR, get_admin_guide_link(ln)))

    sorting_methods = get_sorting_methods()
    if not sorting_methods:
        out = create_important_box('<p>The BibSort contains no methods.<br/>\
                                   If you wish to load a previous configuration (ex: <b>%s/bibsort/bibsort.cfg</b>) \
                                   please use the bibsort command line tool.<br/>\
                                   Please see the %s for more details.</p>' \
                                   %(CFG_ETCDIR, get_admin_guide_link(ln)))
    else:
        #display the sorting methods in a table
        #header
        header_list = ['Name', 'Definition', 'Washer', 'Translation', 'Action']
        sm_table_header = ''
        for item in header_list:
            sm_table_header += '''<th class="adminheader">%s</th>''' % item
        #body
        sm_table_body = ''
        for (sm_id, sm_name, sm_def, sm_washer) in sorting_methods:
            trans_link = create_adminaction_link('modifytranslations', 'Modify', {'bsrID': sm_id, 'ln': ln})
            delete_link = create_action_delete_link(sm_name, sm_id, bsrcode, ln)
            sm_table_body += '''<tr>
                <td class="admintdleft">%(name)s</td>
                <td class="admintdleft">%(def)s</td>
                <td class="admintdleft">%(washer)s</td>
                <td class="admintdleft">%(trans)s</td>
                <td class="admintdleft">%(action)s</td>
               </tr>
            '''% {'name': sm_name, 'def': sm_def, \
                  'washer': sm_washer, 'trans': trans_link, \
                  'action': delete_link}
        #the sorting methods table
        sm_table = '''
            <table class="admin_wvar_nomargin">
            <tr>%(header)s</tr>
            %(body)s
            </table>
            ''' % {'header': sm_table_header, 'body': sm_table_body}
        out += sm_table

    # add new bibsort method button
    out += create_action_add_link()

    return out


def create_action_add_link():
    """
    Creates the Add action link and the Add new method form and java script attached to it.
    """
    add_form_js = '''
    <script>
      $(document).ready(function(){
        $('#addform').hide();
        $('#addsortingmethod').click(function() {
            $('#addform').slideDown()
        });
      });
    </script>'''

    button_style = '''color: #FFFFFF; background: #3366CC; 
                   text-decoration:none; font-weight:bold;
                   font-size:small; padding:5px;'''

    #get the available washers
    def get_washer_value():
        """Returns all the available washer methods"""
        sm_washer_code = '''<select name="sm_washer">'''
        sm_washer_code += '''<option value='NOOP'>NOOP</option>'''
        washers = get_all_available_washers()
        for washer in washers:
            sm_washer_code += '''<option value='%(washer)s'>%(washer)s</option>''' \
                              % {'washer': washer}
        sm_washer_code += '''</select>'''
        return sm_washer_code

    #get possibilities for field
    def get_field_value():
        """Returns all the available logical fields"""
        field_value = '''<div><select id='fieldmore' name="sm_field_value">'''
        fields = get_all_available_fields()
        for field in fields:
            field_value += '''<option value='%(field)s'>%(field)s</option>''' \
                           % {'field': field[0]}
        field_value += '''</select></div>'''
        return field_value

    #get possibilities for marc
    def get_marc_value():
        """Returns the input field for the MARC tag"""
        return '''
            <div>
                <input type='text' id='marcmore' name='sm_marc_value' />
            </div>'''

    #get possibilities for rnk
    def get_rnk_value():
        """Returns all the available rnk methods"""
        rnk_value = '''<div><select id='rnkmore' name="sm_rnk_value">'''
        rnks = get_all_available_rnks()
        for rnk in rnks:
            rnk_value += '''<option value='%(rnk)s'>%(rnk)s</option>''' \
                         % {'rnk': rnk[0]}
        rnk_value += '''</select></div>'''
        return rnk_value

    #get possibilities for bibrec
    def get_bibrec_value():
        """Returns all the available bibrec methods"""
        return '''
            <div>
            <select id='bibrecmore' name="sm_bibrec_value">
                <option value='creation_date'>creation date</option>
                <option value='modification_date'>modification date</option>
            </select>
            </div>'''

    #get possibilities for language
    def get_locale_value():
        """Returns all the available languages"""
        sm_locale_code = '''<select name="sm_locale">'''
        sm_locale_code += '''<option value='en'>English (default)</option>'''
        langs = language_list_long(True)
        for lang in langs:
            if lang[0] != 'en': # we already added English as default
                sm_locale_code += '''<option value='%(lang_short)s'>%(lang_long)s</option>''' \
                                  % {'lang_short': lang[0], 'lang_long': lang[1]}
        sm_locale_code += '''</select>'''
        return sm_locale_code

    #get the possible definition types
    sm_types = ['field', 'marc', 'rnk', 'bibrec']
    sm_def_code = '''<table cellspan='5' cellpadding='5'>'''
    for sm_type in sm_types:
        sm_def_code += '''
                    <tr>
                        <td><input type="radio" name="sm_def_type" value="%(type)s" id="%(id)s">%(name)s</td>
                        <td id="%(type_id)s">%(type_value)s</td>
                    </tr>''' \
                       % {'type': sm_type,
                          'id': sm_type + 'radio',
                          'name': sm_type.upper(),
                          'type_id': 'type' + sm_type,
                          'type_value': locals()['get_' + sm_type + '_value']()}
        #javascript code for: when one method is selected, show it's value and hide the values for the others
        sm_def_code += '''<script>
            $(document).ready(function(){
                $('#%(type_id)s').hide();
                $('#%(id)s').click(function() {
                    $('#%(type_id)s').show();
                    all_types = $.map($('input:radio[name=sm_def_type]'), function(el){return el.value;})
                    for (sm_type in all_types){
                        if ('type' + all_types[sm_type] != '%(type_id)s'){
                            $('#type' + all_types[sm_type]).hide();
                        }
                    }
                });
            });
            </script>''' \
            % {'id': sm_type + 'radio',
               'type_id': 'type' + sm_type}
    sm_def_code += '''</table>'''

    #javascript for: populate field sm_def_value and delete all the sm_[type]_value
    add_form = '''<script>
    $(document).ready(function(){
        $('#addsubmission').submit(function(){
            selected_type = $('input:radio[name=sm_def_type]:checked').val();
            selected_value = $('[name=sm_' + selected_type + '_value]').val();
            $('[name=sm_def_value]').val(selected_value);
            all_types = $.map($('input:radio[name=sm_def_type]'), function(el){return el.value;})
            for (type in all_types){
                $('#' + all_types[type] + 'more').remove();
            }
        });
    });
    </script>'''

    add_form += '''
    <div id='addform' style='border: 1px solid #FF9966; padding:10px; margin-top:20px; margin-left:10px; width:-moz-fit-content;'>
    <form action='bibsortadmin.py' id='addsubmission'>
       <input type='hidden' name='action' value='add'/>
       <input type='hidden' name='sm_def_value' value=''/>
       <table cellspacing="5" style='text-size:small;'>
         <tr>
           <td><b><small>Method Name:</small></b></td>
           <td><input type='text' name='sm_name'/></td>
         </tr>
         <tr>
           <td valign="top"><b><small>Method Definition:</small></b></td>
           <td>%(sm_def_code)s</td>
         </tr>
         <tr>
           <td><b><small>Method Washer:</small></b></td>
           <td>%(sm_washer_code)s</td>
         </tr>
         <tr>
           <td><b><small>Use this language when sorting:</small></b></td>
           <td>%(sm_locale_code)s</td>
         </tr>
         <tr>
           <td colspan=2 align='right'><input type='submit' value='Add' style="%(button_style)s"/></td>
         </tr>
       </table> 
    </form>
    </div>
    '''% {'button_style': button_style,
          'sm_washer_code': get_washer_value(),
          'sm_locale_code': get_locale_value(),
          'sm_def_code': sm_def_code}

    button_link = '''<div style="padding-top:20px; padding-left:10px;">\
                        <a href='#' style='%s' id='addsortingmethod'>Add New Sorting Method</a>\
                    </div>''' % button_style

    return button_link + add_form_js + add_form


def create_action_delete_link(sm_name, sm_id, bsrcode, ln):
    """
    Creates the Delete action link.
    """
    if sm_id == bsrcode:
        # the deletion was not successful, the method that should have been deleted is still in the database
        return '<span style="color:red">Error: the method was not deleted. Please check the database permissions.</span>'
    delete_confirm = '''Are you sure you want to delete the sorting method <<%s>> and all the data asociated with it? [If in doubt, see the BibSort Admin Guide for details].''' % sm_name
    on_click = '''return confirm('%s')''' % delete_confirm
    return create_adminaction_link('', 'Delete', options={'bsrID': sm_id, 'ln': ln, 'action': 'delete'}, style='', on_click=on_click)


def getnavtrail(previous = ''):
    """Get the navtrail"""

    navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (CFG_SITE_URL,)
    navtrail = navtrail + previous
    return navtrail


def check_user(req, role, authorized=0):
    """
    Checks if the user is authorized to access the admin area.
    """
    auth_code, auth_message = acc_authorize_action(req, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)


def get_sorting_name(bsrcode):
    """
    Returns the name asociated with the bsrcode in the bsrMETHOD table.
    """
    try:
        return run_sql('SELECT name from bsrMETHOD where id = %s', (bsrcode,))[0][0]
    except IndexError:
        return ''


def get_sorting_methods():
    """
    Returns the list of all sorting methods defined
    """
    return run_sql('SELECT id, name, definition, washer from bsrMETHOD')


def create_important_box(content, color='#FF9966'):
    """
    Returns the code for a red box containing an important message
    """
    return '''<div style="border:1px solid %(color)s; background: %(color)s; width=100%%; margin-bottom:10px;">
                <center><i>%(content)s</i></center>
              </div>''' % {'color': color, 'content': content}


def create_adminaction_link(action, name, options=None, style='', on_click=''):
    """
    Returns the link coresponding to an action

    @param action: the action the url should point to
    @param name: the name displayed to the user
    @param options: dictionary containing the url parameters
    """
    #create the link parameters from the options dictionarly
    link_params = options and '&'.join('%s=%s' %(item, options[item]) for item in options) or ''
    return '<a style="%(style)s" onclick="%(on_click)s" \
                     href="%(site)s/admin/bibsort/bibsortadmin.py/%(action)s?%(link_params)s">%(name)s</a>' \
            % {'style': style,
               'on_click': on_click,
               'site': CFG_SITE_URL,
               'action':action,
               'link_params':link_params,
               'name':name}


def get_admin_guide_link(ln):
    """
    Returns the link to the admin guide.
    """
    _ = gettext_set_language(ln)
    return '<a href="%s/help/admin/bibsort-admin-guide">%s</a>' % (CFG_SITE_URL, _('BibSort Guide'))


def get_all_available_fields():
    """
    Returns all fields
    """
    return run_sql("SELECT code FROM field ORDER BY code")


def get_all_available_rnks():
    """
    Returns all ranking methods
    """
    return run_sql("SELECT name FROM rnkMETHOD ORDER BY name")


def perform_modifytranslations(ln, bsrID, trans=None, confirm=0):
    """Modify the translations of a sort method"""

    _ = gettext_set_language(ln)

    output = create_important_box('<p>If you have questions, please see the %s.</p>' %get_admin_guide_link(ln), '#66CCFF')

    sel_type = 'ln' #Long name
    table_name = 'bsrMETHOD'
    sitelangs = get_languages()

    if not trans:
        trans = []
    if type(trans) is str:
        trans = [trans]

    if confirm == 2 and bsrID:
        finresult = modify_translations(bsrID, sitelangs, sel_type, trans, table_name)

    bsr_dict = dict(get_i8n_name(bsrID, ln, sel_type, table_name))

    if bsrID and bsr_dict.has_key(bsrID):
        header = ['Language', 'Translation']
        actions = []
        if not confirm:
            trans = []
            for (key, dummy) in sitelangs:
                try:
                    trans.append(get_i8n_name(bsrID, key, sel_type, table_name)[0][1])
                except StandardError:
                    trans.append('')

        for i in range(0, len(sitelangs)):
            actions.append(["%s %s" % (sitelangs[i][1], (sitelangs[i][0]==CFG_SITE_LANG and '<small>(def)</small>' or ''))])
            actions[-1].append('<input type="text" name="trans" size="30" value="%s"/>' % trans[i])

        text = tupletotable(header=header, tuple=actions)
        output += createhiddenform(action="modifytranslations",
                                   text=text,
                                   button="Modify",
                                   bsrID=bsrID,
                                   ln=ln,
                                   confirm=2)

        if sel_type and len(trans) and confirm == 2:
            output += write_outcome(finresult)

    return output
