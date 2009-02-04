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

"""CDS Invenio BibEdit Templates."""

__revision__ = "$Id$"


class Template:

    """BibEdit Templates Class."""

    def __init__(self):
        """Initialize."""
        pass

    def menu(self, recid=None):
        """ Create the menu."""
        if recid == None:
            recid = ''

        recordmenu = '<div class="bibEditMenuSectionHeader">Record</div>\n' \
            '        <table>\n' \
            '          <col width="20px">\n' \
            '          <col width="48px">\n' \
            '          <col width="68px">\n' \
            '          <tr>\n' \
            '            <td colspan="2">\n' \
            '              <form onsubmit="return false;">\n' \
            '                %(txtSelectRecord)s\n' \
            '              </form>\n' \
            '            </td>\n' \
            '            <td>%(btnGetRecord)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="2" align="right">%(btnSubmit)s</td>\n' \
            '            <td>%(btnCancel)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td align="bottom">%(imgDeleteRecord)s</td>\n' \
            '            <td colspan="2" align="bottom">\n' \
            '              %(btnDeleteRecord)s\n' \
            '            </td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="3" style="font-size: 0.8em;">\n' \
            '              %(lblShow)s:\n' \
            '            </td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="2" align="right">%(btnTagMARC)s</td>\n' \
            '            <td>%(btnTagNames)s</td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'txtSelectRecord': inp('text', value=recid, id='txtSelectRecord',
                                   maxlength=8),
            'btnGetRecord': button('button', 'Get', id='btnGetRecord'),
            'btnSubmit': button('button', 'Submit', 'bibEditBtnBold',
                                id='btnSubmit', disabled='disabled'),
            'btnCancel': button('button', 'Cancel', id='btnCancel',
                                disabled='disabled'),
            'imgDeleteRecord': img('/img/trash.png'),
            'btnDeleteRecord': button('button', 'Delete record',
                id='btnDeleteRecord', disabled='disabled'),
            'lblShow': 'Display',
            'btnTagMARC': link('MARC', id='lnkMARCTags'),
            'btnTagNames': link('Human', id='lnkHumanTags')
            }

        fieldmenu = '<div class="bibEditMenuSectionHeader">Fields</div>\n' \
            '        <table>\n' \
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
            'imgAddField': img('/img/add.png'),
            'btnAddField': button('button', 'Add', id='btnAddField',
                                  disabled='disabled'),
            'imgSortFields': img('/img/sort_asc.png'),
            'btnSortFields': button('button', 'Sort', id='btnSortFields',
                                    disabled='disabled'),
            'imgDeleteSelected': img('/img/delete.png'),
            'btnDeleteSelected': button('button', 'Delete selected',
                id='btnDeleteSelected', disabled='disabled')
            }

        statusarea = '<table>\n' \
            '          <tr>\n' \
            '            <td id="cellIndicator">%(imgIndicator)s</td>\n' \
            '            <td id="cellStatus">%(lblChecking)s</td>\n' \
            '         </table>' % {
            'imgIndicator': img('/img/indicator.gif'),
            'lblChecking': 'Checking status' + '...'
            }

        return '    <div id="bibEditMenu">\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(recordmenu)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(fieldmenu)s\n' \
            '      </div>\n' \
            '      <div id="bibEditMenuSection">\n' \
            '        %(statusarea)s\n' \
            '      </div>\n' \
            '    </div>\n' % {
                'recordmenu': recordmenu,
                'fieldmenu': fieldmenu,
                'statusarea': statusarea
                }

def img(src, _class='', **kargs):
    """Create a HTML <img> element."""
    src = 'src="%s" ' % src
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<img %s%s%s/>' % (src, _class, args)

def inp(_type, _class='', **kargs):
    """Create a HTML <input> element."""
    _type = 'type="%s" ' % _type
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<input %s%s%s/>' % (_type, _class, args)

def button(_type, value, _class='', **kargs):
    """Create a HTML <button> element."""
    _type = 'type="%s" ' % _type
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<button %s%s%s>%s</button>' % (_type, _class, args, value)

def link(value, _class='', **kargs):
    """Create a HTML <a> (link) element."""
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<a %s%s>%s</a>' % (_class, args, value)
