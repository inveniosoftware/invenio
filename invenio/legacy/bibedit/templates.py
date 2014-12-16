## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

# pylint: disable=C0103

"""BibEdit Templates."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL, CFG_INSPIRE_SITE
from invenio.base.i18n import gettext_set_language

from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM

try:
    BIBCATALOG_SYSTEM.ticket_search(0)
    CFG_CAN_SEARCH_FOR_TICKET = True
except NotImplementedError:
    CFG_CAN_SEARCH_FOR_TICKET = False

class Template:

    """BibEdit Templates Class."""

    def __init__(self):
        """Initialize."""
        pass

    def menu(self):
        """Create the menu."""

        recordmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sRecord\n' \
            '          %(imgNewRecord)s\n' \
            '          %(imgCloneRecord)s\n' \
            '          %(imgTemplateRecord)s\n' \
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
            '            <td colspan="2">%(sctSearchType)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="4">%(btnSearch)s</td>\n' \
            '          </tr>\n' \
            '          <tr id="rowRecordBrowser" style="display: none">\n' \
            '            <td>%(btnPrev)s</td>\n' \
            '            <td colspan="2" id="cellRecordNo"\n' \
            '              style="text-align: center">1/1</td>\n' \
            '            <td>%(btnNext)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td colspan="2">%(btnSubmit)s</td>\n' \
            '            <td colspan="2">%(btnCancel)s</td>\n' \
            '          </tr>\n' \
            '          <tr class="bibEditMenuMore">\n' \
            '            <td>%(imgDeleteRecord)s</td>\n' \
            '            <td colspan="3">%(btnDeleteRecord)s</td>\n' \
            '          </tr>\n' \
            '          <tr class="bibEditmenuMore">\n' \
            '            <td>Switch to:</td>\n' \
            '            <td colspan="3">%(btnSwitchReadOnly)s</td>\n' \
            '          </tr>' \
            '        </table>' % {
            'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgRecordMenu'),
            'imgNewRecord': img('/img/table.png', 'bibEditImgCtrlEnabled',
                                id='imgNewRecord', title='New record'), \
            'imgCloneRecord': img('/img/table_multiple.png',
                'bibEditImgCtrlDisabled', id='imgCloneRecord',
                title='Clone record'), \
            'imgTemplateRecord': img('/img/page_edit.png',
                'bibEditImgCtrlEnabled', id='imgTemplateRecord',
                title='Manage templates'), \
            'txtSearchPattern': inp('text', id='txtSearchPattern'), \
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
            'imgDeleteRecord': img('/img/table_delete.png'),
            'btnDeleteRecord': button('button', 'Delete',
                id='btnDeleteRecord', disabled='disabled'),
            'btnSwitchReadOnly' : button('button', 'Read-only',
                                         id='btnSwitchReadOnly')
            }

        if CFG_CAN_SEARCH_FOR_TICKET:
            ticketsmenu = '<div class="bibEditMenuSectionHeader">\n' \
                '          %(imgCompressMenuSection)sTickets\n' \
                '          </div>\n' \
                '          <div id="loadingTickets">\n' \
                '          %(imgTicketsLoader)s\n<span>loading...</span>' \
                '          </div>\n' \
                '          <div class="bibEditTicketsMenuSection">\n' \
                '          <table class="bibEditMenuMore">\n' \
                '            <col width="136px">\n' \
                '            <tr class="bibEditMenuMore">\n' \
                '              <td id="tickets"></td>'\
                '            </tr>\n' \
                '          </table>\n' \
                '        </div>\n' % {
                'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                        'bibEditImgCompressMenuSection', id='ImgTicketsMenu'),
                'imgTicketsLoader': img('/img/indicator.gif',
                                'bibEditImgTicketsLoader', id='ImgTicketsLoader')
                }
        else:
            ticketsmenu = ''

        fieldmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sFields\n' \
            '        </div>\n' \
            '        <table class="bibEditMenuMore">\n' \
            '          <col width="28px">\n' \
            '          <col>\n' \
            '          <tr>\n' \
            '            <td>%(imgAddField)s</td>\n' \
            '            <td>%(btnAddField)s</td>\n' \
            '          </tr>\n' \
            '          <tr>\n' \
            '            <td>%(imgDeleteSelected)s</td>\n' \
            '            <td>%(btnDeleteSelected)s</td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgFieldMenu'),
            'imgAddField': img('/img/table_row_insert.png'),
            'btnAddField': button('button', 'Add', id='btnAddField',
                                  disabled='disabled'),
            'imgDeleteSelected': img('/img/table_row_delete.png'),
            'btnDeleteSelected': button('button', 'Delete selected',
                id='btnDeleteSelected', disabled='disabled')}

        viewmenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sView\n' \
            '        </div>\n' \
            '        <table>\n' \
            '          <col width="68px">\n' \
            '          <col width="68px">\n' \
            '          <tr class="bibEditMenuMore">\n' \
            '            <td>%(btnTagMARC)s</td>\n' \
            '            <td>%(btnTagNames)s</td>\n' \
            '          </tr>\n' \
            '        </table>' % {
            'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgViewMenu'),
            'btnTagMARC': button('button', 'MARC', id='btnMARCTags',
                                 disabled='disabled'),
            'btnTagNames': button('button', 'Human', id='btnHumanTags',
                                  disabled='disabled')
            }

        historymenu = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sHistory\n' \
            '        </div>\n' \
            '        <div class="bibEditRevHistoryMenuSection">\n' \
            '          <table>\n' \
            '            <col width="136px">\n' \
            '            <tr class="bibEditMenuMore">\n' \
            '              <td id="bibEditRevisionsHistory"></td>'\
            '            </tr>\n' \
            '          </table>\n' \
            '        </div>\n'% {
            'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgHistoryMenu')
            }

        undoredosection =  '<div class="bibEditMenuSectionHeader">\n' \
            '            %(imgCompressMenuSection)sUndo/Redo\n' \
            '          </div>\n<table>' \
            '          <tr class="bibEditMenuMore"><td>' \
            '          <div class="bibEditURMenuSection">\n' \
            '             <div class="bibEditURDetailsSection" id="bibEditURUndoListLayer">\n' \
            '                 <div class="bibEditURButtonLayer"><button id="btnUndo" class="menu-btn">&lt;</button></div>\n' \
            '                 <div id="undoOperationVisualisationField" class="bibEditHiddenElement bibEditURPreviewBox">\n' \
            '                     <div id="undoOperationVisualisationFieldContent"></div>\n' \
            '                 </div>\n' \
            '             </div>' \
            '             <div class="bibEditURDetailsSection" id="bibEditURRedoListLayer">\n' \
            '                 <div class="bibEditURButtonLayer"><button id="btnRedo" class="menu-btn">&gt;</button></div>' \
            '                 <div id="redoOperationVisualisationField" class="bibEditHiddenElement bibEditURPreviewBox">\n' \
            '                     <div id="redoOperationVisualisationFieldContent"></div>' \
            '                 </div>\n' \
            '             </div>\n' \
            '          </div></td></tr></table>\n' % { \
            'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgUndoRedoMenu') }

        statusarea = '<table>\n' \
            '          <tr>\n' \
            '            <td id="cellIndicator">%(imgIndicator)s</td>\n' \
            '            <td id="cellStatus">%(lblChecking)s</td>\n' \
            '         </table>' % {
            'imgIndicator': img('/img/indicator.gif'),
            'lblChecking': 'Checking status' + '...'
            }

        holdingpenpanel = '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sHolding Pen\n' \
            '</div><table class="bibEditMenuMore">\n<tr><td>' \
            '   <div id="bibEditHoldingPenToolbar"> '  \
            '      <div id="bibeditHPChanges"></div>' \
            ' </div> </td></tr></table>' % \
            { 'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgHoldingPenMenu') }

        bibcirculationpanel = \
            '      <div class="bibEditMenuSection" ' \
            ' id="bibEditBibCircConnection">\n' \
            '<div class="bibEditMenuSectionHeader">\n' \
            '          %(imgCompressMenuSection)sPhysical Copies\n' \
            '    <table class="bibEditMenuMore">\n<tr><td ' \
            ' class="bibEditBibCircPanel">' \
            '    Number of copies: ' \
            '       <div id="bibEditBibCirculationCopies">0</div><br/>' \
            '    <button id="bibEditBibCirculationBtn" class="menu-btn">' \
            'Edit physical copies</button>' \
            ' </td></tr></table></div></div>' \
            % {
               'imgCompressMenuSection': img('/img/bullet_toggle_minus.png',
                            'bibEditImgCompressMenuSection', id='ImgBibCirculationMenu')
              }

        lnkSpecialChar = link('Special symbols', href='#', id='lnkSpecSymbols')

        lnkhelp = img('/img/help.png', '', style='vertical-align: bottom') + \
            link('Help', href='#', onclick='window.open(' \
            '\'%s/help/admin/bibedit-admin-guide#2\', \'\', \'width=640,' \
            'height=600,left=150,top=150,resizable=yes,scrollbars=yes\');' \
            'return false;' % CFG_SITE_URL)

        return '    <div id="bibEditMenu">\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(recordmenu)s\n' \
            '      </div>\n' \
            '       <div class="bibEditMenuSection">\n' \
            '         %(ticketsmenu)s\n' \
            '       </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(fieldmenu)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(viewmenu)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '         %(holdingpenpanel)s\n'\
            '      </div>'\
            '      <div class="bibEditMenuSection">\n' \
            '        %(undoredosection)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(historymenu)s\n' \
            '      </div>\n' \
            '        %(circulationmenu)s\n' \
            '      <div id="bibEditMenuSection">\n' \
            '        %(statusarea)s\n' \
            '      </div>\n' \
            '      <div class="bibEditMenuSection" align="right">\n' \
            '        %(lnkSpecialChar)s %(lnkhelp)s\n' \
            '      </div>\n' \
            '    </div>\n' % {
                'recordmenu': recordmenu,
                'ticketsmenu': ticketsmenu,
                'viewmenu': viewmenu,
                'fieldmenu': fieldmenu,
                'statusarea': statusarea,
                'lnkhelp': lnkhelp,
                'lnkSpecialChar': lnkSpecialChar,
                'holdingpenpanel': holdingpenpanel,
                'historymenu': historymenu,
                'undoredosection': undoredosection,
                'circulationmenu': bibcirculationpanel
                }

    def history_comparebox(self, ln, revdate, revdate_cmp, person1, person2, comparison):
        """ Display the bibedit history comparison box. """
        _ = gettext_set_language(ln)
        title = '<b>%(comp)s</b><br /><span class="diff_field_added">\
        %(rev)s %(revdate)s %(person1)s</span><br /><span class="diff_field_deleted">\
        %(rev)s %(revdate_cmp)s %(person2)s</span>' % {
            'comp': _('Comparison of:'),
            'rev': _('Revision'),
            'revdate': revdate,
            'revdate_cmp': revdate_cmp,
            'person1': person1 and 'by ' + person1 or '',
            'person2': person2 and 'by ' + person2 or ''}
        return '''
       <div class="bibEditHistCompare">
         <p>%s</p>
         <p>
           %s
         </p>
       </div>''' % (title, comparison)

    def focuson(self):
        """ Returns the html of the display options box on the left panel. """

        curator_display_html = ""
        if CFG_INSPIRE_SITE:
            curator_display_html = """
            <hr>
            <li>
                <input type="checkbox" name="curator" id="focuson_curator" value="curator"/>
                <label for="focuson_curator">Curator view</label>
            </li>
            """

        html = """
        <div id='display_div'>
            <strong>Display</strong> <br />
            <ul id='focuson_list' class='list-plain'>
                <li>
                    <input type="checkbox" name="references" id="focuson_references" value="references" checked/>
                    <label for="focuson_references">References</label>
                </li>
                <li>
                    <input type="checkbox" name="authors" id="focuson_authors" value="authors" checked/>
                    <label for="focuson_authors">Authors</label>
                </li>
                <li>
                    <input type="checkbox" name="others" id="focuson_others" value="others" checked/>
                    <label for="focuson_others">Others</label>
                </li>
                %(curator_display_html)s
            </ul>
        </div>
        """ % {
            'curator_display_html' : curator_display_html
        }

        return html

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

def button(_type, value, _class="", **kargs):
    """Create an HTML <button> element."""
    _type = 'type="%s" ' % _type
    class_result = "class='menu-btn "
    if _class:
        class_result += "%s' " % _class
    else:
        class_result += "'"
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<button %s%s%s>%s</button>' % (_type, class_result, args, value)

def link(value, _class='', **kargs):
    """Create an HTML <a> (link) element."""
    if _class:
        _class = 'class="%s" ' % _class
    args = ''
    for karg in kargs:
        args += '%s="%s" ' % (karg, kargs[karg])
    return '<a %s%s>%s</a>' % (_class, args, value)
