## $Id$
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

__revision__ = "$Id$"

from invenio.bibedit_dblayer import *
from invenio.config import CFG_SITE_URL
from invenio.messages import gettext_set_language

## Link of edit and delete button:
btn_delete_url = CFG_SITE_URL + "/img/iconcross.gif"
btn_edit_url   = CFG_SITE_URL + "/img/iconpen.gif"
bibediturl = "%s/admin/bibedit/bibeditadmin.py" % CFG_SITE_URL

class Template:

    def tmpl_table_header(self, ln, type_table, recid, temp="false", format_tag='marc',
                          tag='', num_field=None, add=0):
        """ Return the Header of table. """

        _ = gettext_set_language(ln)

        (tag, ind1, ind2, junk) = marc_to_split_tag(tag)
        tag = tag + ind1 + ind2 + "%"

        if type_table != "record":

            if add == 1:
                print_input_add_form = self.tmpl_input('hidden', 2, 'add')
            else:
                print_input_add_form = ''

            print_action_add_subfield = print_input_add_form + self.tmpl_input('hidden', str(num_field), 'num_field')

            print_action_edit_100 = print_input_add_form + self.tmpl_input('hidden', str(num_field), 'num_field')

            if add != 1:
                link_add_subfields = self.tmpl_link(ln, _("Add Subfield"), bibediturl, 'edit',
                                                    {'recid'      : str(recid),
                                                     'tag'        : tag[:3],
                                                     'num_field'  : str(num_field),
                                                     'format_tag' : format_tag,
                                                     'temp'       : 'true',
                                                     'add'        : 1})

                link_edit_100 = ""
                print_action_edit_100 = ""

                #tag[:3] == 100x is never true, of course. This functionality TBD
                #and will be used in enrichment editing
                if str(tag[:3]) == "100x": #FIXME
                            link_edit_100 = self.tmpl_link(
                                ln, _("Edit institute"), bibediturl, 'edit',
                                {'recid'      : str(recid),
                                 'tag'        : tag[:3],
                                 'num_field'  : str(num_field),
                                 'format_tag' : format_tag,
                                 'temp'       : 'true',
                                 'add'        : 1})
                            print_action_edit_100 = """ %(field)s:
                                                        %(link_edit_100)s
                                                        """ % {'field'              : _("Field"),
                                                               'link_edit_100' : link_edit_100}



                print_action_add_subfield = """ %(field)s:
                                                %(link_add_subfields)s

                                            """ % {'field'              : _("Field"),
                                                   'link_add_subfields' : link_add_subfields}


            if add == 1:
                link_form = "edit"
            else:
                link_form = "index"

            result = """ <form action="%(bibediturl)s/%(link_form)s" method="POST">
                           %(input_recid)s
                           %(input_temp)s
                           %(input_ln)s
                         <div class="bibEditCellRight" style="font-weight: normal;">
                           %(print_action_add_subfield)s
                           %(print_action_edit_100)s
                         </div>
                     """ % {'bibediturl'            : bibediturl,
                            'input_recid'               : self.tmpl_input('hidden', recid,  'recid'),
                            'input_temp'                : self.tmpl_input('hidden', 'true', 'temp'),
                            'input_ln'                  : self.tmpl_input('hidden', ln,     'ln'),
                            'link_form'                 : link_form,
                            'print_action_add_subfield' : print_action_add_subfield,
                            'print_action_edit_100' : print_action_edit_100}
        else:
            link_submit         = ''
            link_add_field      = self.tmpl_link(ln, _("Add Field"), bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'tag'        : tag[:3],
                                                  'format_tag' : format_tag,
                                                  'temp'       : 'true',
                                                  'add'        : 3}, 'add') + " | "

            link_diplay_verbose = self.tmpl_link(ln, _("Verbose"), bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'format_tag' : 's',
                                                  'temp'       : temp})

            link_diplay_marc    = self.tmpl_link(ln, "MARC", bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'format_tag' : 'marc',
                                                  'temp'       : temp})

            if temp != "false" and add != 3:
                link_submit = self.tmpl_link(ln, _("Submit"), bibediturl, 'submit', {'recid' : str(recid)}) + " | "

            if add == 3:
                link_add_field = ''
                result = ''
            else:
                link_cancel = self.tmpl_link(ln, _("Cancel"), bibediturl, 'index', {'cancel' : str(recid)})
                link_delete = self.tmpl_link(ln, _("Delete"), bibediturl, 'index', {'delete' : str(recid),
                                                                                        'confirm_delete' :1,
                                                                                        'temp' : temp})

                result = """ <div class="bibEditCellRight" style="font-weight: normal">
                                 &nbsp;%(action)s: %(link_submit)s%(link_cancel)s

                                 &nbsp;%(record)s: %(link_add_field)s%(link_delete)s

                                 &nbsp;%(display)s: %(link_diplay_verbose)s | %(link_diplay_marc)s

                             </div> """  % {'action'              : _("Action"),
                                            'record'              : _("Record"),
                                            'display'             : _("Display"),
                                            'link_submit'         : link_submit,
                                            'link_add_field'      : link_add_field,
                                            'link_diplay_verbose' : link_diplay_verbose,
                                            'link_diplay_marc'    : link_diplay_marc,
                                            'link_cancel'         : link_cancel,
                                            'link_delete'         : link_delete}

        return """ <table class="bibEditTable">
                     <tr>
                       <th colspan="6">
                         %(record)s #%(recid)s
                         %(result)s
                         %(num_field)s
                       </th>
                     </tr> """ % {'record' : _("Record"),
                                  'recid'  : str(recid),
                                  'result' : result,
                                  'num_field': self.tmpl_input('hidden', str(num_field), 'num_field')}


    def tmpl_table_value(self, ln, recid, tag, field, format_tag, type_table, add, form_add=0):
        """ Return a field to print in table. """

        if form_add == 0:
            subfields = field[0]
            num_field = field[4]
            tag_field = split_tag_to_marc(tag, field[1], field[2])
            if format_tag != 's':
                print_tag_field = tag_field[:-1]
            else:
                tag_field = tag_field[:-1] + '%'
                if get_name_tag(tag_field) != tag_field:
                    print_tag_field = get_name_tag(tag_field)
                else:
                    print_tag_field = tag_field[:-1]
            len_subfields = len(subfields)
            if type_table == "record" and add != 3:
                print_link_function = self.tmpl_link_function(ln, len_subfields, recid, tag, num_field, format_tag)
                print_tag_form = ''
            else:
                print_link_function = ''
                if add == 1:
                    print_tag_form = self.tmpl_input('hidden', get_tag_name(print_tag_field), 'tag')
                else:
                    print_tag_form = self.tmpl_input('hidden', get_tag_name(print_tag_field), 'edit_tag')
            if add == 1:
                len_subfields += 1
                type_table = "record"

            try:
                result = """<td rowspan="%(len_subfields)s" class="bibEditCellTag">
                              %(print_tag_field)s
                              %(print_tag_form)s
                            </td>
                              %(subfield)s
                              %(print_link_function)s
                         """ % {'len_subfields'       : len_subfields,
                                'print_tag_field'     : print_tag_field,
                                'print_tag_form'      : print_tag_form,
                                'subfield'            : self.tmpl_subfields(ln, recid,
                                                                            subfields[0][0], subfields[0][1],
                                                                            tag_field, format_tag, type_table,
                                                                            0, num_field, len_subfields),
                                'print_link_function' : print_link_function}
            except IndexError:
                raise "FIXME: BibEdit does not seem to be able to edit records with controlfields."
            if len_subfields != 1:
                num_value = -1
                for subfield in subfields:
                    num_value += 1
                    if num_value != 0:
                        result += """ <tr>
                                        %s
                                      </tr> """ % self.tmpl_subfields(ln, recid, subfield[0], subfield[1],
                                                                      tag_field, format_tag,
                                                                      type_table, num_value,
                                                                      num_field, len_subfields)
            if add == 1:
                result += """ <tr>
                                %s
                              </tr> """ % self.tmpl_subfields(ln, add=add)
        else:
            #click on "add field" link on the top of index page.
            result = """ <td class="bibEditCellTag">
                           <form action="%(bibediturl)s/index" method="POST">
                             %(input_recid)s
                             %(input_temp)s
                             %(input_ln)s
                             %(input_add)s
                             <b>
                              <a name="add">Tag</a>:
                              <input type="text" name="add_tag"  maxlength="3" size="3" />
                              ind1:
                              <input type="text" name="add_ind1" maxlength="1" size="1" />
                                 ind2:
                                 <input type="text" name="add_ind2" maxlength="1" size="1" />
                               </b>
                         </td> """ % {'bibediturl' : bibediturl,
                                      'input_recid'    : self.tmpl_input('hidden', recid, 'recid'),
                                      'input_temp'     : self.tmpl_input('hidden', 'true', 'temp'),
                                      'input_add'      : self.tmpl_input('hidden', 4, 'add'),
                                      'input_ln'       : self.tmpl_input('hidden', ln, 'ln'),
                                      'recid'          : str(recid),
                                      'ln'             : ln}

            result += "%s" % self.tmpl_subfields(ln, add=add)

        return """ <tr><td></td></tr>
                   <tr>
                     %s
                   </tr> """ % result


    def tmpl_table_footer(self, ln, type_table, add=0):
        """ Return a footer of table. """

        _ = gettext_set_language(ln)

        button  = _("Done")

        if type_table != "record" or add == 3:
            form = self.tmpl_input('submit', button, class_css='formbutton') + "</form>"
        else:
            form = ''

        return """   <tr>
                       <td align="right" colspan="6">
                         %(form)s
                       </td>
                     </tr>
                   </table> """ % {'form' : form}


    def tmpl_subfields(self, ln, recid='', tag_subfield='', value='', tag_field='', format_tag='marc',
                       type_table='', num_value='', num_field='', len_subfields='', add=0):
        """ This function return the content of subfield. """
        _ = gettext_set_language(ln)
        if add == 1 or add == 3:
            print_tag_subfield = " $$ " + self.tmpl_input('text', '', 'add_subcode', 1, 1)
        else:
            if type_table != "record":
                print_tag_subfield = " $$ " + self.tmpl_input('text', tag_subfield,
                                                                    'subcode%s' % str(num_value),
                                                                    1, 1)

            elif format_tag != 's':
                print_tag_subfield = "$$%s" % tag_subfield
            else:
                print_tag_subfield = "%s%s" % (tag_field[:-1], tag_subfield)

                if get_name_tag(print_tag_subfield) != print_tag_subfield:
                    print_tag_subfield = get_name_tag(print_tag_subfield)
                else:
                    print_tag_subfield = "$$%s" % tag_subfield

        value = self.tmpl_clean_value(value, "record")

        print_value       = ''
        print_old_value   = ''
        print_btn         = ''
        print_bgcolor     = ''
        print_old_subcode = ''

        if type_table != "record" or add == 3:

            if add == 1 or add == 3:
                print_value = self.tmpl_input('text', '', 'add_value', size="115%c" % '%')
            else:
                print_old_subcode = self.tmpl_input('hidden', tag_subfield, 'old_subcode%s' % str(num_value))
                print_old_value   = self.tmpl_input('hidden', value, 'old_value%s' % str(num_value))

                if len(value) < 75:
                    print_value = self.tmpl_input('text', value, 'value%s' % str(num_value),
                                                  style="width:100%;")
                else:
                    print_value = '<textarea name="value%(num_value)s" cols="70" rows="5" style="width:100%%;">%(value)s</textarea>'
                    print_value %= {'num_value'   : str(num_value),
                                    'value'       : value}

                if len_subfields > 1:

                    print_btn = "<td>%s</td>" \
                               % self.tmpl_link(ln, '<img border="0" src="%s" alt="%s" />' % (btn_delete_url, _("Delete")),
                                                bibediturl, 'edit',
                                                {'recid'        : str(recid),
                                                 'tag'          : tag_field[:-1]+ tag_subfield,
                                                 'num_field'    : num_field,
                                                 'format_tag'   : format_tag,
                                                 'temp'         : 'true',
                                                 'del_subfield' : 1,
                                                 'num_subfield' : num_value})

        else:
            print_value = value
            print_bgcolor = " background: #FFF;"

        return """ <td style="background: #F5F5F5" class="admintdright">
                     %(print_tag_subfield)s
                     %(print_old_subcode)s
                   </td>
                   <td style="padding: 0px 5px 0px 5px; %(print_bgcolor)s width:700px">
                     <span style="font-size:small;">
                       %(print_value)s
                     </span>
                       %(print_old_value)s
                   </td>
                   %(print_btn)s
                   <td></td> """ % {'print_tag_subfield' : print_tag_subfield,
                                    'print_old_subcode'  : print_old_subcode,
                                    'print_bgcolor'      : print_bgcolor,
                                    'print_value'        : print_value,
                                    'print_old_value'    : print_old_value,
                                    'print_btn'          : print_btn}


    def tmpl_link_function(self, ln, len_subfields, recid, tag, num_field, format_tag):
        """ Print button function to edit and delete information. """
        _ = gettext_set_language(ln)
        btn_edit = self.tmpl_link(ln, '<img style="border:0px" src="%s" alt="%s" />' % (btn_edit_url, _("Edit")),
                                  bibediturl, 'edit',
                                  {'recid'        : str(recid),
                                   'tag'          : tag,
                                   'num_field'    : num_field,
                                   'format_tag'   : format_tag,
                                   'temp'         : 'true'})

        btn_delete = self.tmpl_link(ln, '<img style="border: 0px" src="%s" alt="%s" />' % (btn_delete_url, _("Delete")),
                                    bibediturl, 'index',
                                    {'recid'      : str(recid),
                                     'delete_tag' : tag,
                                     'num_field'  : num_field,
                                     'format_tag' : format_tag,
                                     'temp'       : 'true'})

        return """ <td rowspan="%(len_subfields)s" style="text-align:center;vertical-align:top;">
                     %(btn_edit)s
                   </td>
                   <td rowspan="%(len_subfields)s" style="text-align:center;vertical-align:top;">
                     %(btn_delete)s
                   </td>
               """ % {'len_subfields' : len_subfields,
                      'btn_edit'      : btn_edit,
                      'btn_delete'    : btn_delete}

    def tmpl_clean_value(self, value, format):
        """ This function clean value for HTML interface and inverse. """

        if format != "html":
            value = value.replace('"', '&quot;')
            value = value.replace('<', '&lt;')
            value = value.replace('>', '&gt;')

        else:
            value = value.replace('&quot;', '"')
            value = value.replace('&lt;', '<')
            value = value.replace('&gt;', '>')

        return value


    def tmpl_warning_temp_file(self, ln):
        """ Return a warning message for user who use a temp file. """

        _ = gettext_set_language(ln)

        return """ <span style="color: #000;
                                 background: #fcc;
                                 padding: 1px;
                                 font-weight: bold;
                                 border-spacing: 3px;
                                 border: 2px solid #900;">
                      %(message1)s %(message2)s
                   </span><br/><br/>
               """ % {'message1' : _("Your changes are TEMPORARY."),
                      'message2' : _("To save this record, please click on submit.")}


    def tmpl_record_choice_box(self, ln, message):
        """ Return a little for; for choice a record to edit. """

        _ = gettext_set_language(ln)

        if message == 1:
            result = """ <span class="errorbox">
                            <b>
                               %(message1)s %(message2)s
                             </b>
                         </span><br/><br/>
                     """ % {'message1' : _("This record does not exist."),
                            'message2' : _("Please try another record ID.")}

        elif message == 2:
            result = """ <span class="errorbox">
                             <b>
                               %(message1)s %(message2)s
                             </b>
                          </span><br/><br/>
                      """ % {'message1' : _("This record is currently being edited by another user."),
                             'message2' : _("Please try again later.")}
        elif message == 3:
            result = """ <span class="errorbox">
                             <b>
                               %(message1)s
                             </b>
                          </span><br/><br/>
                      """ % {'message1' : _("Cannot edit deleted record.")}

        else:
            result = ''

        result += """ <form action="%(bibediturl)s/index"  method="POST">
                        %(input_ln)s
                        <span style="background-color: #ddd; padding: 5px;">
                          %(message)s: %(input_recid)s %(input_button)s
                        </span>
                      </form> """ % {'bibediturl' : bibediturl,
                                     'message' : _("Please enter the ID of the record you want to edit"),
                                     'input_ln'       : self.tmpl_input('hidden', ln, 'ln'),
                                     'input_recid'    : self.tmpl_input('text'  , '', 'recid'),
                                     'input_button'   : self.tmpl_input('submit', _("Edit"),
                                                                        class_css='formbutton')}

        return result

    def tmpl_submit(self, ln):
        """ Return a end message of Bibedit. """

        _ = gettext_set_language(ln)
        out =  _("Your modifications have now been submitted. They will be processed as soon as the task queue is empty.") + '<br /><br />'
        out += '<h2>' + _("Edit another record") + '</h2>'
        out += self.tmpl_record_choice_box(ln=ln, message=0)
        return out

    def tmpl_deleted(self, ln, message='', recid='', temp='', format_tag=''):
        """ Return a deleted message of Bibedit. """
        _ = gettext_set_language(ln)
        if message == 1:
            return """ %(message)s
                       <div style="float:left;">
                         <form action="%(bibediturl)s/index?delete=%(recid)s" method="POST">
                           %(input_ln)s
                           %(input_button_yes)s
                         </form>
                       </div>
                       <div style="float:left;">
                         <form action="%(bibediturl)s/index?recid=%(recid)s&temp=%(temp)s&format_tag=%(format_tag)s" method="POST">
                           %(input_ln)s
                           %(input_button_no)s
                         </form>
                       </div>
                   """ % {'message'          : _("Do you really want to delete this record?"),
                          'bibediturl'   : bibediturl,
                          'recid'            : str(recid),
                          'input_ln'         : self.tmpl_input('hidden', ln, 'ln'),
                          'input_button_yes' : self.tmpl_input('submit', _("Yes"), class_css='formbutton'),
                          'input_button_no'  : self.tmpl_input('submit', _("No"),  class_css='formbutton'),
                          'temp'             : temp,
                          'format_tag'       : format_tag}

        else:
            out =   _("The record will be deleted as soon as the task queue is empty.") + '<br /><br />'
            out += '<h2>' + _("Edit another record") + '</h2>'
            out += self.tmpl_record_choice_box(ln=ln, message=0)
            return out

    def tmpl_link(self, ln, text, url, dest, dict_args='', ancre=''):
        """ Return a link. """

        if dict_args == '':
            link_args = ''
        else:
            link_args = '?'
            list_args = dict_args.items()
            for arg in list_args:
                link_args += "%(name)s=%(value)s&amp;" % {'name'  : str(arg[0]),
                                                          'value' : str(arg[1])}
            link_args += "ln=%s" % ln

        if ancre != '':
            ancre = '#' + ancre

        return  '<a href="%(url)s/%(dest)s%(args)s%(ancre)s">%(text)s</a>' % {'text'  : text,
                       'url'   : url,
                       'dest'  : dest,
                       'args'  : link_args,
                       'ancre' : ancre}

    def tmpl_input(self, type_input, value='', name='', maxlength='', size='', class_css='', style=''):
        """ Return a input form. """

        if value     != '':
            value     = 'value="%s"'     % str(value)
        if name      != '':
            name      = 'name="%s"'      % str(name)
        if maxlength != '':
            maxlength = 'maxlength="%s"' % str(maxlength)
        if size      != '':
            size      = 'size="%s"'      % str(size)
        if class_css != '':
            class_css = 'class="%s"'     % str(class_css)
        if style     != '':
            style     = 'style="%s"'     % str(style)

        out = '<input type="%(type)s" %(name)s %(value)s %(size)s %(maxlength)s %(class_css)s %(style)s />'
        out %= {'type'      : type_input,
                'value'     : value,
                'name'      : name,
                'maxlength' : maxlength,
                'size'      : size,
                'class_css' : class_css,
                'style'     : style}
        return out
