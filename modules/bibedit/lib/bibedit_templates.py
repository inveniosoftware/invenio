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

# pylint: disable=C0103

"""BibEdit Templates."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_URL
from invenio.messages import gettext_set_language

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
            '          &nbsp;&nbsp;%(imgTemplateRecord)s\n' \
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
            '          <tr>\n' \
            '            <td id="tickets" colspan="4"><!--filled by bibedit_menu.js--></td>\n' \
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
            '                 <div class="bibEditURButtonLayer"><button id="btnUndo">&lt;</button></div>\n' \
            '                 <div id="undoOperationVisualisationField" class="bibEditHiddenElement bibEditURPreviewBox">\n' \
            '                     <div id="undoOperationVisualisationFieldContent"></div>\n' \
            '                 </div>\n' \
            '             </div>' \
            '             <div class="bibEditURDetailsSection" id="bibEditURRedoListLayer">\n' \
            '                 <div class="bibEditURButtonLayer"><button id="btnRedo">&gt;</button></div>' \
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
            '<table class="bibEditMenuMore">\n<tr><td>' \
            '   <div id="bibEditHoldingPenToolbar"> '  \
            '      <div id="bibeditHPChanges"></div>' \
            ' </div> </td></tr></table>' \
            '        </div>\n'  % \
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
            '    <button id="bibEditBibCirculationBtn">' \
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

        return '    %(page_style)s\n' \
            '    <div id="bibEditMenu">\n' \
            '      <div class="bibEditMenuSection">\n' \
            '        %(recordmenu)s\n' \
            '      </div>\n' \
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
                'page_style': page_style(),
                'recordmenu': recordmenu,
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

def page_style():
    """Apply styling for bibedit elements"""
    style = """<style type="text/css">"""
    style += """
                .pagefooter {
                    display: none;
                }

                .revisionLine {
                    font-size:12px;
                    color: rgb(90, 134, 196);
                }

                .floatRight {
                    float: right;
                }

                .floatLeft {
                    float: left;
                }

                #Toptoolbar {
                    overflow: auto;
                }

                #bibEditContent {
                    margin-left: 175px;
                    width: 750px;
                }

                #bibEditContentTable {
                    overflow: auto;
                    border-top:1px solid;
                    border-color: #575757;
                    margin-top: 5px;
                }

                #bibEditMenu {
                    width: 135px;
                    float: left;
                    padding-left: 10px;
                    font-size: 0.8em;
                    z-index:1;
                }

                #bibEditMessage {
                    display: none;
                    margin: 3px 3px 3px 3px;
                    width: 740px;
                }

                .warningMsg{
                    padding: 10px 10px 2px 10px;
                    background-color: #FAD163;
                }

                div.refextracted {
                    line-height:25px;
                }

                #bibEditMenu .bibEditMenuSection {
                    margin-bottom: 10px;
                }

                #bibEditMenu .bibEditMenuSectionHeader {
                    font-weight: bold;
                }

                #bibEditTable {
                    background-color: rgb(255, 255, 255);
                    border: 1px solid #A1A1A1;
                    border-collapse: collapse;
                    width: 100%;
                    table-layout:fixed;
                }

                #bibEditTable td {
                    overflow:hidden;
                    word-wrap: break-word;
                 }

                 #bibEditTable td textarea{
                    max-width: 615px;
                    min-height: 65px;
                    max-height: 600px;
                }

                .bibEditCellFieldTag:focus {
                    outline: none;
                }

                #bibEditMenu .bibEditMenuSection table {
                    width: 100%;
                }

                #bibEditMenu form {
                    margin: 0px;
                }

                #bibEditMenu .bibEditImgExpandMenuSection,
                #bibEditMenu .bibEditImgCompressMenuSection {
                    margin: 0px;
                    text-align: left;
                    vertical-align: bottom;
                }

                #bibEditMenu a, #bibEditMenu button, #bibEditMenu input,
                #bibEditMenu select {
                    font-size: 0.8em;
                }
                #bibEditMenu a, #bibEditMenu button, #bibEditMenu img,
                #bibEditMenu input, #bibEditMenu select {
                    margin: 1px;
                }
                #bibEditMenu button, #bibEditMenu input, #bibEditMenu select  {
                    width: 100%;
                }
                #bibEditMenu .bibEditImgCtrlEnabled {
                    cursor: pointer;
                    opacity: 1.0;
                    vertical-align: bottom;
                }

                #bibEditMenu .bibEditImgCtrlDisabled {
                    cursor: default;
                    opacity: 0.4;
                    vertical-align: bottom;
                }

                .bibEditRevHistoryEntryContent{
                    cursor: pointer;
                }

                @media print {
                    img[id^='btnAddSubfield'] {
                        display:none;
                    }

                    .pagefooter {
                        display: none;
                    }

                    .bibEditVolatileSubfield {
                        display:none;
                    }
                }

                 /* jQuery-UI Theming used for:
                  * - Dialog refextract
                  */

                .dialog-box-centered {
                    margin-top: 300px;
                    text-align: center;
                }

                .dialog-icon {
                    float: left;
                    margin: 12px 7px 10px 0;
                }

                /* jQuery-UI Theming used for:
                 * - Autocomplete menu
                 */

                .ui-autocomplete-loading {
                    background: white url('/img/ui-anim_basic_16x16.gif') right center no-repeat;
                }

                .ui-corner-all {
                    -moz-border-radius: 4px 4px 4px 4px;
                }

                .ui-widget-overlay {
                    -moz-background-clip: border;
                    -moz-background-origin: padding;
                    -moz-background-size: auto auto;
                    background-attachment: scroll;
                    background-position: 50%% 50%%;
                    background-repeat: repeat;
                    background-color: #666666;
                    opacity: 0.5;
                    left: 0;
                    position: absolute;
                    top: 0;
                }

                .ui-widget {
                    font-size: .8em;
                }

                .ui-menu .ui-menu-item a {
                    display: block;
                    line-height: .8;
                    padding: 0.2em 0.4em;
                    text-decoration: none;
                    background-color: white;
                    color: black;
                }

                .ui-menu {
                    list-style: none outside none;
                    margin-left: 1em;
                    padding-left: 1em;
                }

                .ui-autocomplete {
                    cursor: default;
                    width: 300px;
                }

                .ui-dialog-content {
                    background-color: red;
                }

                /* End of jQuery UI Theming */
            """
    style += "</style>"
    return style
