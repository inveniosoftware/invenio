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

from invenio.bibeditold_dblayer import get_name_tag, get_tag_name, \
    marc_to_split_tag, split_tag_to_marc
from invenio.config import CFG_SITE_URL
from invenio.messages import gettext_set_language

## Link of edit, move up and delete button:
btn_delete_url = CFG_SITE_URL + "/img/iconcross.gif"
btn_moveup_url = CFG_SITE_URL + "/img/arrow_up.gif"
btn_movedown_url = CFG_SITE_URL + "/img/arrow_down.gif"
btn_edit_url   = CFG_SITE_URL + "/img/iconpen.gif"
bibediturl = "%s/admin/bibedit/bibeditadmin.py" % CFG_SITE_URL


class Template:

    def clean_value(self, value, format):
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

    def confirm(self, ln, message='', recid='', format_tag='', revid='', revdate=''):
        """ Ask for confirmation of or confirm some critical action. """
        _ = gettext_set_language(ln)
        if message == 'delete':
            return """ %(message)s
                       <div style="float:left;">
                         <form action="%(bibediturl)s/index?delete=%(recid)s" method="POST">
                           %(input_ln)s
                           %(input_button_yes)s
                         </form>
                       </div>
                       <div style="float:left;">
                         <form action="%(bibediturl)s/index?recid=%(recid)s&format_tag=%(format_tag)s" method="POST">
                           %(input_ln)s
                           %(input_button_no)s
                         </form>
                       </div>
                   """ % {'message'          : _("Do you really want to delete this record?"),
                          'bibediturl'   : bibediturl,
                          'recid'            : str(recid),
                          'input_ln'         : self.input('hidden', ln, 'ln'),
                          'input_button_yes' : self.input('submit', _("Yes"), class_css='formbutton'),
                          'input_button_no'  : self.input('submit', _("No"),  class_css='formbutton'),
                          'format_tag'       : format_tag}
        if message == 'revert':
            question = _('Do you really want to revert to revision %(revdate)s of record #%(recid)s?'
                        ) % {'revdate': revdate,
                             'recid': recid}
            warning_1 = _('The current version will be replaced with a copy of revision %(revdate)s'
                        ) % {'revdate': revdate}
            warning_2 = _('You will also lose any unsubmitted changes for this record!')
            return """ %(question)s<br />
                        <b>%(warning_1)s</b><br />
                        <b>%(warning_2)s</b><br /><br />
                       <div style="float:left;">
                         <form action="%(bibediturl)s/history?recid=%(recid)s&revid=%(revid)s&action=confirm_revert" method="POST">
                           %(input_ln)s
                           %(input_button_yes)s
                         </form>
                       </div>
                       <div style="float:left;">
                         <form action="%(bibediturl)s/history?recid=%(recid)s&revid=%(revid)s&format_tag=%(format_tag)s" method="POST">
                           %(input_ln)s
                           %(input_button_no)s
                         </form>
                       </div>
                   """ % {'question'        : question,
                          'warning_1'       : warning_1,
                          'warning_2'       : warning_2,
                          'bibediturl'      : bibediturl,
                          'revid'           : revid,
                          'recid'           : recid,
                          'input_ln'        : self.input('hidden', ln, 'ln'),
                          'input_button_yes': self.input('submit', _("Yes"), class_css='formbutton'),
                          'input_button_no' : self.input('submit', _("No"),  class_css='formbutton'),
                          'format_tag'      : format_tag}

    def input(self, type_input, value='', name='', maxlength='', size='', class_css='', style=''):
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

    def link(self, ln, text, url, dest, dict_args='', ancre=''):
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

    def record_choice_box(self, ln, msgid):
        """Return the 'main page' with the record selection box, and an optional message."""
        _ = gettext_set_language(ln)

        result = ''
        if msgid:
            messages = (_('This record does not exist. Please try another record '
                          'ID.'),
                        _('Cannot edit deleted record."'),
                        _('This record is currently being edited by another '
                          'user. Please try again later.'),
                        _('The record is locked because of unfinished upload '
                          'tasks. Please try again in a few minutes.'),
                        _('Your modifications have now been submitted. They will '
                          'be processed as soon as the task queue is empty.'),
                        _('The record will be deleted as soon as the task queue '
                          'is empty.'))

            message = messages[msgid-1]
            if msgid < 5:
                result += """ <span class="errorbox">
                                 <b>
                                   %(message)s
                                 </b>
                              </span><br/><br/>
                          """ % {'message' : message}
            else:
                header = _("Edit another record")
                result += '''%s<br /><br />
                <h2>%s</h2>''' % (message, header)

        input_button_history = '<input type="submit" name="view_history" value="View history" class="formbutton">'
        result += """ <form name="selectForm" action="%(bibediturl)s/index"  method="POST">
                        %(input_ln)s
                        <span style="background-color: #ddd; padding: 5px;">
                          %(message)s: %(input_recid)s %(input_button_edit)s %(input_button_history)s
                        </span>
                      </form> """ % {'bibediturl' : bibediturl,
                                     'message' : _("Please enter the ID of the record you want to edit"),
                                     'input_ln'             : self.input('hidden', ln, 'ln'),
                                     'input_recid'          : self.input('text'  , '', 'recid'),
                                     'input_button_edit'    : self.input('submit', _("Edit"),
                                                                        class_css='formbutton'),
                                     'input_button_history' : input_button_history}
        return result

    def subfields(self, ln, recid='', tag_subfield='', value='', tag_field='', format_tag='marc',
                       type_table='', num_value='', num_field='', len_subfields='', add=0):
        """ This function return the content of subfield. """
        _ = gettext_set_language(ln)
        if add == 1 or add == 3:
            print_tag_subfield = " $$ " + self.input('text', '', 'add_subcode', 1, 1)
        else:
            if type_table != "record":
                print_tag_subfield = " $$ " + self.input('text', tag_subfield,
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

        value = self.clean_value(value, "record")

        print_value       = ''
        print_old_value   = ''
        print_btn         = ''
        print_bgcolor     = ''
        print_old_subcode = ''

        if type_table != "record" or add == 3:

            if add == 1 or add == 3:
                print_value = self.input('text', '', 'add_value', size="115%c" % '%')
            else:
                print_old_subcode = self.input('hidden', tag_subfield, 'old_subcode%s' % str(num_value))
                print_old_value   = self.input('hidden', value, 'old_value%s' % str(num_value))

                if len(value) < 75:
                    print_value = self.input('text', value, 'value%s' % str(num_value),
                                                  style="width:100%;")
                else:
                    print_value = '<textarea name="value%(num_value)s" cols="70" rows="5" style="width:100%%;">%(value)s</textarea>'
                    print_value %= {'num_value'   : str(num_value),
                                    'value'       : value}

                if len_subfields > 1:

                    print_btn = "<td>%s</td>" \
                               % self.link(ln, '<img border="0" src="%s" alt="%s" />' % (btn_delete_url, _("Delete")),
                                                bibediturl, 'edit',
                                                {'recid'        : str(recid),
                                                 'tag'          : tag_field[:-1]+ tag_subfield,
                                                 'num_field'    : num_field,
                                                 'format_tag'   : format_tag,
                                                 'act_subfield' : 'delete', #delete
                                                 'num_subfield' : num_value})
                    if num_value > 0:
                        print_btn += "<td>%s</td>" \
                               % self.link(ln, '<img border="0" src="%s" alt="%s" />' % (btn_moveup_url, _("Move up")),
                                                bibediturl, 'edit',
                                                {'recid'        : str(recid),
                                                 'tag'          : tag_field[:-1]+ tag_subfield,
                                                 'num_field'    : num_field,
                                                 'format_tag'   : format_tag,
                                                 'act_subfield' : 'move_up', #move up
                                                 'num_subfield' : num_value})
                    else:
                        print_btn += "<td> </td>"
                    if num_value < len_subfields-1:
                        print_btn += "<td>%s</td>" \
                               % self.link(ln, '<img border="0" src="%s" alt="%s" />' % (btn_movedown_url, _("Move down")),
                                                bibediturl, 'edit',
                                                {'recid'        : str(recid),
                                                 'tag'          : tag_field[:-1]+ tag_subfield,
                                                 'num_field'    : num_field,
                                                 'format_tag'   : format_tag,
                                                 'act_subfield' : 'move_down',
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

    def editor_table_header(self, ln, type_table, recid, tmp, format_tag='marc',
                          tag='', num_field=None, add=0, revisions=0):
        """ Return the Header of table. """

        _ = gettext_set_language(ln)

        (tag, ind1, ind2, junk) = marc_to_split_tag(tag)
        tag = tag + ind1 + ind2 + "%"

        if type_table != "record":

            if add == 1:
                print_input_add_form = self.input('hidden', 2, 'add')
            else:
                print_input_add_form = ''

            print_action_add_subfield = print_input_add_form + self.input('hidden', str(num_field), 'num_field')

            print_action_edit_100 = print_input_add_form + self.input('hidden', str(num_field), 'num_field')

            if add != 1:
                link_add_subfields = self.link(ln, _("Add Subfield"), bibediturl, 'edit',
                                                    {'recid'      : str(recid),
                                                     'tag'        : tag[:3],
                                                     'num_field'  : str(num_field),
                                                     'format_tag' : format_tag,
                                                     'add'        : 1})

                link_edit_100 = ""
                print_action_edit_100 = ""

                #tag[:3] == 100x is never true, of course. This functionality TBD
                #and will be used in enrichment editing
                if str(tag[:3]) == "100x": #FIXME
                    link_edit_100 = self.link(
                        ln, _("Edit institute"), bibediturl, 'edit',
                        {'recid'      : str(recid),
                         'tag'        : tag[:3],
                         'num_field'  : str(num_field),
                         'format_tag' : format_tag,
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

            formcontents = """ <form action="%(bibediturl)s/%(link_form)s" method="POST">
                           %(input_recid)s
                           %(input_ln)s
                         <div class="bibEditCellRight" style="font-weight: normal;">
                           %(print_action_add_subfield)s
                           %(print_action_edit_100)s
                         </div>
                     """ % {'bibediturl'            : bibediturl,
                            'input_recid'               : self.input('hidden', recid,  'recid'),
                            'input_ln'                  : self.input('hidden', ln,     'ln'),
                            'link_form'                 : link_form,
                            'print_action_add_subfield' : print_action_add_subfield,
                            'print_action_edit_100' : print_action_edit_100}
            result = formcontents
        else:
            link_submit         = ''
            link_add_field      = self.link(ln, _("Add Field"), bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'tag'        : tag[:3],
                                                  'format_tag' : format_tag,
                                                  'add'        : 3}, 'add') + " | "

            link_diplay_verbose = self.link(ln, _("Verbose"), bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'format_tag' : 's'})

            link_diplay_marc    = self.link(ln, "MARC", bibediturl, 'index',
                                                 {'recid'      : str(recid),
                                                  'format_tag' : 'marc'})

            if tmp and add != 3:
                link_submit = self.link(ln, _("Submit"), bibediturl, 'submit', {'recid' : str(recid)}) + " | "

            if add == 3:
                link_add_field = ''
                result = ''
            else:
                link_cancel = self.link(ln, _("Cancel"), bibediturl, 'index', {'cancel' : str(recid)})

                link_delete = self.link(ln, _("Delete"), bibediturl, 'index', {'delete' : str(recid),
                                                                                        'confirm_delete' :1})

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

        history_link = ''
        if revisions:
            history_dest = 'history?ln=%s&recid=%s&format_tag=%s' % (
                ln, recid, format_tag)
            if revisions == 1:
                history_link_text = _('(%s previous revision)') % revisions
            else:
                history_link_text = _('(%s previous revisions)') % revisions
            history_link = self.link(ln, history_link_text, bibediturl, history_dest)

        return """ <table class="bibEditTable">
                     <tr>
                       <th colspan="6">
                         %(record)s #%(recid)s %(history_link)s
                         %(result)s
                         %(num_field)s
                       </th>
                     </tr> """ % {'record' : _("Record"),
                                  'recid'  : str(recid),
                                  'history_link': history_link,
                                  'result' : result,
                                  'num_field': self.input('hidden', str(num_field), 'num_field')}


    def editor_table_value(self, ln, recid, tag, field, format_tag, type_table, add, form_add=0):
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
                print_link_function = self.editor_link_function(ln, len_subfields, recid, tag, num_field, format_tag)
                print_tag_form = ''
            else:
                print_link_function = ''
                if add == 1:
                    print_tag_form = self.input('hidden', get_tag_name(print_tag_field), 'tag')
                else:
                    print_tag_form = self.input('hidden', get_tag_name(print_tag_field), 'edit_tag')
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
                                'subfield'            : self.subfields(ln, recid,
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
                                      </tr> """ % self.subfields(ln, recid, subfield[0], subfield[1],
                                                                      tag_field, format_tag,
                                                                      type_table, num_value,
                                                                      num_field, len_subfields)
            if add == 1:
                result += """ <tr>
                                %s
                              </tr> """ % self.subfields(ln, add=add)
        else:
            #click on "add field" link on the top of index page.
            result = """ <td class="bibEditCellTag">
                           <form action="%(bibediturl)s/index" method="GET">
                             %(input_recid)s
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
                                      'input_recid'    : self.input('hidden', recid, 'recid'),
                                      'input_add'      : self.input('hidden', 4, 'add'),
                                      'input_ln'       : self.input('hidden', ln, 'ln'),
                                      'recid'          : str(recid),
                                      'ln'             : ln}

            result += "%s" % self.subfields(ln, add=add)

        return """ <tr><td></td></tr>
                   <tr>
                     %s
                   </tr> """ % result


    def editor_table_footer(self, ln, type_table, add=0, another=0):
        """ Return a footer of table. """

        _ = gettext_set_language(ln)

        dbutton  = _("Done")
        abutton = _("Add another subfield")

        if type_table != "record" or add == 3:
            #add a done button and 'add another subfield' button in the form
            form = self.input('submit', dbutton, class_css='formbutton') + "<br/>"
            if another:
                form += self.input('submit', abutton, 'addanother', class_css='formbutton') + "<br>"
                form += _("Tags and values should be filled before pressing Done or Add another subfield")
            form += "</form>"

        else:
            form = ''

        return """   <tr>
                       <td align="right" colspan="6">
                         %(form)s
                       </td>
                     </tr>
                   </table> """ % {'form' : form}

    def editor_link_function(self, ln, len_subfields, recid, tag, num_field, format_tag):
        """ Print button function to edit and delete information. """
        _ = gettext_set_language(ln)
        btn_edit = self.link(ln, '<img style="border:0px" src="%s" alt="%s" />' % (btn_edit_url, _("Edit")),
                                  bibediturl, 'edit',
                                  {'recid'        : str(recid),
                                   'tag'          : tag,
                                   'num_field'    : num_field,
                                   'format_tag'   : format_tag})

        btn_delete = self.link(ln, '<img style="border: 0px" src="%s" alt="%s" />' % (btn_delete_url, _("Delete")),
                                    bibediturl, 'index',
                                    {'recid'      : str(recid),
                                     'delete_tag' : tag,
                                     'num_field'  : num_field,
                                     'format_tag' : format_tag})

        return """ <td rowspan="%(len_subfields)s" style="text-align:center;vertical-align:top;">
                     %(btn_edit)s
                   </td>
                   <td rowspan="%(len_subfields)s" style="text-align:center;vertical-align:top;">
                     %(btn_delete)s
                   </td>
               """ % {'len_subfields' : len_subfields,
                      'btn_edit'      : btn_edit,
                      'btn_delete'    : btn_delete}

    def editor_warning_temp_file(self, ln):
        """ Return a warning message for user who use a tmp file. """

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

    def history_container(self, part):
        """ Display the bibedit history page container. """
        if part == 'header':
            out = '''
     <div>'''
        if part == 'footer':
            out = '''
     </div>
     '''
        return out

    def history_viewbox(self, ln, part, current=None, recid=None,
                             revid=None, revdate=None):
        """ Display the bibedit history viewbox. """
        _ = gettext_set_language(ln)
        if part == 'header':
            title = _("Revision %(revdate)s"
                      ) % {'revdate': revdate}
            if current:
                parant = _('current version')
            else:
                text = _('revert to this revision')
                dest = '''history?recid=%(recid)s&revid=%(revid)s&action=revert''' % {
                    'recid': recid,
                    'revid': revid}
                parant = self.link(ln, text, bibediturl, dest)
            out = '''
       <div class="bibEditHistView">
         <table class="bibEditTable">
           <th colspan="4">
             %s (%s)
           </th>''' % (title, parant)
        elif part == 'footer':
            out = '''
           <tr>
             <td align="right" colspan="6">
             </td>
           </tr>
         </table>
       </div>'''
        return out

    def history_revision(self, ln, recid, format_tag, revision):
        """ Display the content of a record in the bibedit history. """
        out = ''
        keys = revision.keys()
        keys.sort()

        for tag in keys:

            fields = revision.get(str(tag), "empty")

            if fields != "empty":
                for field in fields:
                    if field[0]: # Only display if has subfield(s)
                        out += self.history_table_value(ln, recid,
                            format_tag, tag, field)
        return out

    def history_table_value(self, ln, recid, format_tag, tag, field):
        """ Return a field to print in table, like editor_table_value, but
            without the edit and delete buttons."""
        #FIXME: We should refactor to get a more generic printing of these fields.
        type_table = 'record'

        subfields = field[0]
        num_field = field[4]
        tag_field = split_tag_to_marc(tag, field[1], field[2])
        print_tag_field = tag_field[:-1]
        len_subfields = len(subfields)
        try:
            result = """
             <td rowspan="%(len_subfields)s" class="bibEditCellTag">
               %(print_tag_field)s
             </td>
             %(subfield)s
                     """ % {'len_subfields'       : len_subfields,
                            'print_tag_field'     : print_tag_field,
                            'subfield'            : self.subfields(ln, recid,
                                                                        subfields[0][0], subfields[0][1],
                                                                        tag_field, format_tag, type_table,
                                                                        0, num_field, len_subfields)}
        except IndexError:
            raise "FIXME: BibEdit does not seem to be able to edit records with controlfields."
        if len_subfields != 1:
            num_value = -1
            for subfield in subfields:
                num_value += 1
                if num_value != 0:
                    result += """
           <tr>
             %s
           </tr>""" % self.subfields(ln, recid, subfield[0], subfield[1],
                                                                  tag_field, format_tag,
                                                                  type_table, num_value,
                                                                  num_field, len_subfields)
        return """
           <tr>
             <td>
             </td>
           </tr>
           <tr>
             %s
           </tr> """ % result

    def history_comparebox(self, ln, revdate, revdate_cmp, comparison):
        """ Display the bibedit history comparison box. """
        _ = gettext_set_language(ln)
        title = '<b>%(comp)s</b><br />%(rev)s %(revdate)s<br />%(rev)s %(revdate_cmp)s' % {
            'comp': _('Comparison of:'),
            'rev': _('Revision'),
            'revdate': revdate,
            'revdate_cmp': revdate_cmp}
        return '''
       <div class="bibEditHistCompare">
         <p>%s</p>
         <p>
           %s
         </p>
       </div>''' % (title, comparison)

    def history_forms(self, ln, recid, revids, revdates, page_type, revid,
        format_tag, revid_cmp=None):
        """ Display the bibedit history option forms. """
        _ = gettext_set_language(ln)
        # Hidden input fields
        input_ln = self.input('hidden', value=ln, name='ln')
        input_recid = self.input('hidden', value=recid, name='recid')
        input_format_tag = self.input('hidden', value=format_tag, name='format_tag')
        input_compare = self.input('hidden', value='compare', name='action')
        input_revert = self.input('hidden', value='revert', name='action')

        # Buttons
        edit_button = _("Edit current version")
        view_button = _("View revision")
        compare_button = _("Compare revisions")
        revert_button = _("Revert to revision")
        back_button = _("Back to bibedit")
        input_edit_submit = self.input('submit', edit_button, class_css='formbutton', style='width: 200px;')
        input_view_submit = self.input('submit', view_button, class_css='formbutton', style='width: 200px; margin-top: 20px;')
        input_compare_submit = self.input('submit', compare_button, class_css='formbutton', style='width: 200px; margin-top: 20px;')
        input_revert_submit = self.input('submit', revert_button, class_css='formbutton', style='width: 200px; margin-top: 20px;')
        input_back_submit = self.input('submit', back_button, class_css='formbutton', style='width: 200px; margin-top: 30px;')

        # Option lists
        optlist = self.history_select(revids, revdates)
        optlist_revert = self.history_select(revids[1:], revdates[1:])
        if page_type == 'view':
            optlist_view = self.history_select(revids, revdates, revid)
        else:
            optlist_view = optlist

        if page_type == 'compare':
            optlist_cmp1 = self.history_select(revids, revdates, revid)
            optlist_cmp2 = self.history_select(revids, revdates, revid_cmp)
        else:
            optlist_cmp1 = optlist_cmp2 = optlist

        default_actionurl = bibediturl + '/history'

#        edit_form = self.history_form(bibediturl + '/index', input_edit_submit,
#            hidden_fields=(input_ln, input_recid, input_format_tag))
        edit_form = self.history_form(CFG_SITE_URL + '/record/' + str(recid) +
            '/edit/', input_edit_submit)
        view_form = self.history_form(default_actionurl, input_view_submit,
            ('revid',), (optlist_view,), (input_ln, input_recid,
                                          input_format_tag))
        compare_form = self.history_form(default_actionurl, input_compare_submit,
            ('revid', 'revid_cmp'), (optlist_cmp1, optlist_cmp2), (input_ln,
            input_recid, input_format_tag, input_compare))
        revert_form = self.history_form(default_actionurl, input_revert_submit,
            ('revid',), (optlist_revert,), (input_ln, input_recid,
                                            input_format_tag, input_revert))
#        back_form = self.history_form(bibediturl + '/index', input_back_submit,
#            hidden_fields=(input_ln,))
        back_form = self.history_form(CFG_SITE_URL + '/edit/', input_back_submit)


        return '''
       <div class="bibEditHistForm">
         <table>
           %(edit_form)s
           %(view_form)s
           %(compare_form)s
           %(revert_form)s
           %(back_form)s
         </table>
       </div>''' % {
            'edit_form': edit_form,
            'view_form': view_form,
            'compare_form': compare_form,
            'revert_form': revert_form,
            'back_form': back_form}

    def history_form(self, actionurl, submit_button, select_names=None,
                     optlists=None, hidden_fields=None):
        """
        Display a bibedit history option form with specified parameters.
        """
        form = '<form action="%s" method="post">' % actionurl
        button = '''<tr>
             <td>
               %s
             </td>
           </tr>
           ''' % submit_button
        selects = ''
        if select_names:
            for i in range(len(select_names)):
                selects += '''<tr>
             <td>
               <select style="width: 200px; margin-top: 5px;" name=%s>
                 %s
               </select>
             </td>
           </tr>
           ''' % (select_names[i], optlists[i])
        hiddens = ''
        if hidden_fields:
            for i in range(len(hidden_fields)):
                hiddens += '''<tr>
             <td>
               %s
             </td>
           </tr>
           ''' % (hidden_fields[i])
        return '''%(form)s
           %(button)s
           %(selects)s
           %(hiddens)s
           </form>''' % {
                               'form': form,
                               'button': button,
                               'selects': selects,
                               'hiddens': hiddens}

    def history_select(self, revids, revdates, preselect=None):
        """ Create bibedit history options. """
        out = '''<option value=""></option>'''
        for i in range(len(revids)):
            if revids[i] == preselect:
                out += '''
                 <option selected value="%(revid)s">%(revdate)s</option>''' % {
                   'revid': revids[i],
                   'revdate': revdates[i]}
            else:
                out += '''
                 <option value="%(revid)s">%(revdate)s</option>''' % {
                   'revid': revids[i],
                   'revdate': revdates[i]}
        return out
