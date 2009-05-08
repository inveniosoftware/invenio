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

# pylint: disable-msg=C0103

"""BibEdit Templates."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL

class Template:

    """BibEdit Templates Class."""

    def __init__(self):
        """Initialize."""
        pass

    def menu(self):
        """Create the menu."""

        imgExpandMenuSection = img('/img/bullet_toggle_plus.png',
                            'bibEditImgExpandMenuSection')

        recordmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgExpandMenuSection)sRecord\n' \
            '        </div>\n' \
            '        <table>\n' \
            '          <col width="28px">\n' \
            '          <col width="40px">\n' \
            '          <col width="40px">\n' \
            '          <col width="28px">\n' \
            '          <tr>\n' \
            '            <td colspan="2">\n' \
            '              <form onsubmit="return false;">\n' \
            '                %(txtSearchPattern)s\n' \
            '              </form>\n' \
            '            <td colspan="2">\n' \
            '              %(sctSearchType)s\n' \
            '            </td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="4">%(btnSearch)s</td>\n' \
            '          </tr>\n' \
            '          <tr id="rowRecordBrowser" style="display: none">\n' \
            '            <td>%(btnPrev)s</td>\n' \
            '            <td id="cellRecordNo" colspan="2"\n' \
            '              style="text-align: center">1/1</td>\n' \
            '            <td>%(btnNext)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="2">%(btnSubmit)s</td>\n' \
            '            <td colspan="2">%(btnCancel)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="2">%(tickets)s</td>\n' \
            '            <td id="tickets" colspan="2"></td>\n' \
            '            </td>\n' \
            '          </tr>\n' \
            '          <tr class="bibEditMenuMore">\n' \
            '            <td colspan="4">%(btnDeleteRecord)s</td>\n' \
            '            </td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'imgExpandMenuSection': imgExpandMenuSection,
            'txtSearchPattern': inp('text', id='txtSearchPattern'),
            'sctSearchType': '<select id="sctSearchType">\n' \
            '                <option value="recID">Rec ID</option>\n' \
            '                <option value="reportnumber">Rep No</option>\n' \
            '                <option value="anywhere">Anywhere</option>\n' \
            '              </select>',
            'btnSearch': button('button', 'Search', 'bibEditBtnBold',
                                         id='btnSearch'),
            'btnPrev': button('button', '&lt;', id='btnPrev', disabled='disabled'),
            'btnNext': button('button', '&gt;', id='btnNext', disabled='disabled'),
            'btnSubmit': button('button', 'Submit', 'bibEditBtnBold',
                                id='btnSubmit', disabled='disabled'),
            'btnCancel': button('button', 'Cancel', id='btnCancel',
                                disabled='disabled'),
            'tickets': "Tickets",
            'imgDeleteRecord': img('/img/trash.png'),
            'btnDeleteRecord': button('button', 'Delete record',
                id='btnDeleteRecord', disabled='disabled')
            }

        viewmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgExpandMenuSection)sView\n' \
            '        </div>\n' \
            '        <table>\n' \
            '          <col width="68px">\n' \
            '          <col width="68px">\n' \
            '          <tr class="bibEditMenuMore">\n' \
            '            <td>%(btnTagMARC)s</td>\n' \
            '            <td>%(btnTagNames)s</td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'imgExpandMenuSection': imgExpandMenuSection,
            'btnTagMARC': button('button', 'MARC', id='btnMARCTags',
                                 disabled='disabled'),
            'btnTagNames': button('button', 'Human', id='btnHumanTags',
                                  disabled='disabled')
            }

        fieldmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgExpandMenuSection)sFields\n' \
            '        </div>\n' \
            '        <table class="bibEditMenuMore">\n' \
            '          <tr>\n' \
            '            <td>%(imgAddField)s</td>\n' \
            '            <td>%(btnAddField)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td>%(imgSortFields)s</td>\n' \
            '            <td>%(btnSortFields)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td>%(imgDeleteSelected)s</td>\n' \
            '            <td>%(btnDeleteSelected)s</td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'imgExpandMenuSection': imgExpandMenuSection,
            'imgAddField': img('/img/table_row_insert.png'),
            'btnAddField': button('button', 'Add', id='btnAddField',
                                  disabled='disabled'),
            'imgSortFields': img('/img/table_sort.png'),
            'btnSortFields': button('button', 'Sort', id='btnSortFields',
                                    disabled='disabled'),
            'imgDeleteSelected': img('/img/table_row_delete.png'),
            'btnDeleteSelected': button('button', 'Delete selected',
                id='btnDeleteSelected', disabled='disabled')}

        statusarea = '<table>\n' \
            '          <tr>\n' \
            '            <td id="cellIndicator">%(imgIndicator)s</td>\n' \
            '            <td id="cellStatus">%(lblChecking)s</td>\n' \
            '         </table>' % {
            'imgIndicator': img('/img/indicator.gif'),
            'lblChecking': 'Checking status' + '...'
            }

        lnkhelp = img('/img/help.png', '', style='vertical-align: bottom') + \
            link('Help', href='#', onclick='window.open(' \
            '\'%s/help/admin/bibedit-admin-guide#2\', \'\', \'width=640,' \
            'height=600,left=150,top=150,resizable=yes,scrollbars=yes\');' \
            'return false;' % CFG_SITE_URL)

        return '    <div id="bibEditMenu">\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(recordmenu)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(viewmenu)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(fieldmenu)s\n' \
            '      </div>\n' \
            '      <div id="bibEditMenuSection">\n' \
            '        %(statusarea)s\n' \
            '      </div>\n' \
            '      <div id="bibEditMenuSection" align="right">\n' \
            '        %(lnkhelp)s\n' \
            '      </div>\n' \
            '    </div>\n' % {
                'recordmenu': recordmenu,
                'viewmenu': viewmenu,
                'fieldmenu': fieldmenu,
                'statusarea': statusarea,
                'lnkhelp': lnkhelp
                }

def img(src, _class='', **kargs):
    """Create an HTML <img> element."""
    src = 'src="%s" ' % src
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<img %s%s%s/>' % (src, _class, args)

def inp(_type, _class='', **kargs):
    """Create an HTML <input> element."""
    _type = 'type="%s" ' % _type
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<input %s%s%s/>' % (_type, _class, args)

def button(_type, value, _class='', **kargs):
    """Create an HTML <button> element."""
    _type = 'type="%s" ' % _type
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<button %s%s%s>%s</button>' % (_type, _class, args, value)

def link(value, _class='', **kargs):
    """Create an HTML <a> (link) element."""
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<a %s%s>%s</a>' % (_class, args, value)
