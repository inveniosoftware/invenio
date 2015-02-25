# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio Multiple Record Editor Templates."""

__revision__ = "$Id$"

import cgi

from invenio.config import CFG_SITE_URL, CFG_BIBEDITMULTI_LIMIT_INSTANT_PROCESSING,\
                           CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING,\
                           CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING_TIME,\
                           CFG_SITE_ADMIN_EMAIL, \
                           CFG_SITE_RECORD
from invenio.base.i18n import gettext_set_language
from invenio.utils.url import auto_version_url


class Template:

    """MultiEdit Templates Class."""

    def __init__(self):
        """Initialize."""
        pass

    def styles(self):
        """Defines the local CSS styles"""

        styles = """
<style type="text/css">

select[disabled] {
    color: #696969;
    background: #d3d3d3;
}

select {
    border: solid 1px #000000;
    font-family: Arial, Sans-Serif;
    font-size: 15px;
}

input[type="text"]{
    border: solid 1px #000000;
    font-family: Arial, Sans-Serif;
    font-size: 15px;
}

.actOnFieldLink{
    font-family: Arial, Sans-Serif;
    color: blue;
    font-size: 12px;
    cursor: pointer;
}

div .pagebody td{
    font-family: Arial, Sans-Serif;
    font-size: 16px;
}

.txtTag {
    width: 34px;
}

.txtInd {
    width: 14px;
}

.txtSubfieldCode {
    width: 14px;
}

.txtValue {
    width: 200px;
}

.pagebody td .beforeValueInput, span.beforeValueInput{
    color: green;
    font-size: 12px;
    text-align: center;
    text-transform: uppercase;
}

.textBoxConditionSubfield {
    width: 14px;
}

.textBoxValue{
    margin-right: 1px;
    margin-bottom: 1px;
}

.additionalValueParametersTmp{
    display: none;
}

.msg {
    color:red;
    background-color: #E0ECFF;
    font-style: italic;
}

.tagTableRow {
    background-color: #E0ECFF;
}

.subfieldTableRow {

}

.colFieldTag {
    width: 80px;
}

.colSubfieldCode {
    width: 28px;
}

.colDeleteButton {
    width: 17px;
}

.colActionType{
    width: 150px;
    color: Green;
}

.colAddButton {
    width: 95px;
}

.linkButton {
    text-decoration: underline;
    color: Blue;
    cursor: pointer;
}

.buttonNewField{
    cursor: pointer;
}

.buttonNewSubfield{
    cursor: pointer;
}

.buttonNewValue{
    cursor: pointer;
}

.buttonDeleteValue{
    cursor: pointer;
}

.buttonDeleteField{
    cursor: pointer;
}

.buttonDeleteSubfield{
    cursor: pointer
}
.formbutton{
    cursor: pointer;
}

.buttonGoToFirstPage{
    cursor: pointer;
}

.buttonGoToPreviousPage{
    cursor: pointer;
}

.buttonGoToNextPage{
    cursor: pointer;
}

div .boxContainer{
    margin-left: 20px;
    text-align: left;
    width: 550px;
}

div .boxleft {
    float: left;
    width: 150px;
    padding-top: 3px;
}

div .boxleft_2 {
    float: left;
    width: 400px;
    padding-top: 3px;
}

#actionsDisplayArea {
    border: solid #C3D9FF;
}

#actionsDisplayArea .header {
    background-color: #C3D9FF;
}

.clean-ok {
    border:solid 1px #349534;
    background:#C9FFCA;
    color:#008000;
    font-size:14px;
    font-weight:bold;
    padding:4px;
    text-align:center;
}

.clean-error {
    border:solid 1px #CC0000;
    background:#F7CBCA;
    color:#CC0000;
    font-size:14px;
    font-weight:bold;
    padding:4px;
    text-align:center;
}

.clean-error ul {
    text-align:left;
}

.modify-list{
    border:solid 1px #0033cc;
    background:#e0ecff;
    color:#000000;
    font-size:14px;
    font-weight:bold;
    padding:4px;
    text-align:left;
}

.inputValueGrey{
    color:#000000;
}

.buttonDisabled{
    background:grey;
}

.multiedit_field_deleted {
    color:red;
    text-decoration:line-through;
}

.multiedit_field_modified {
    color:green;
}

.multiedit_loading {
    font-size:12px;
}

</style>
        """
        return styles

    def page_contents(self, language, collections):
        """Returns HTML representing the MultiEdit page"""

        _ = gettext_set_language(language)

        page_html = """\
<div class="pagebody">
<input type="hidden" value="%(language)s" id="language">

<table width="100%%" cellspacing="6" border="0">
<tr>
    <td>
        <b>%(text_choose_search_criteria)s</b> %(text_search_criteria_explanation)s
    </td>
</tr>
<tr>
    <td>
    <div class="boxContainer">
        <div class="boxleft">
            <b>%(text_search_criteria)s:</b>
        </div>
        <div class="boxleft_2">
            <input type="text" placeholder='Use default search engine syntax' id="textBoxSearchCriteria"  size="60"> <br />
        </div>
    </div>
    <div class="boxContainer">
        <div class="boxleft">
            <b>%(text_filter_collection)s:&nbsp;</b>
        </div>
        <div class="boxleft_2">
            %(collections)s <br />
        </div>
    </div>
    <div class="boxContainer">
        <div class="boxleft">
            <b>%(text_output_tags)s:</b>
        </div>
        <div class="boxleft_2">
            <div><input class="inputValueGrey" type="text" id="textBoxOutputTags" value="All tags" size="28">&nbsp;&nbsp;<i>Ex. 100, 700</i><br/></div>
        </div>
    </div>
    <div class="boxContainer">
        <div class="boxleft">
            <input id="buttonTestSearch" value="%(text_test_search)s" type="submit" class="formbutton"></button>
        </div>
    </div>
    </td>
</tr>
<tr/>
<tr/>
<tr>
    <td align="center">
        %(actions_definition_html)s
     </td>
</tr>
<tr>
    <td>
        <div class="boxContainer">
            <div class="boxleft">
                <input id="buttonPreviewResults" value="%(text_preview_results)s" type="button" class="formbutton"></button>
            </div>
            <div class="boxleft_2">
                <input id="buttonSubmitChanges" value="%(text_submit_changes)s" type="button" class="formbutton"></button>
            </div>
        </div>
    </td>
</tr>

</table>

<br/>
<div id="info_area"></div>
<div id="preview_area"></div>

</div>

        """% {"language" : language,
             "text_test_search" : _("Search"),
             "text_search_criteria" : _("Search criteria"),
             "text_output_tags" : _("Output tags"),
             "text_filter_collection": _("Filter collection"),
             "text_choose_search_criteria" : _("1. Choose search criteria"),
             "text_search_criteria_explanation" : _("""Specify the criteria you'd like to use for filtering records that will be changed. Use "Search" to see which records would have been filtered using these criteria."""),
             "actions_definition_html" : self._get_actions_definition_html(language),
             "text_preview_results" : _("Preview results"),
             "text_submit_changes" : _("Apply changes"),
             "collections" : self._get_collections(collections),
             }

        return page_html

    def _get_collections(self, collections):
        """ Returns html select for collections"""
        html = "<select id=\"collection\" onChange=\"onSelectCollectionChange(event);\">"
        for collection_name in collections:
            html += '<option value="%(collection_name)s"">%(collection_name)s</option>' % {'collection_name': cgi.escape(collection_name)}
        html += "</select>"
        return html

    def _get_actions_definition_html(self, language):
        """Returns the html for definition of actions"""
        _ = gettext_set_language(language)

        html = """
<!-- Area for displaying actions to the users -->

<table id="actionsDisplayArea"  width="100%%" cellspacing="0" >
<col class="colDeleteButton"/>
<col class="colFieldTag"/>
<col class="colDeleteButton"/>
<col class="colSubfieldCode"/>
<col class="colActionType"/>
<col/>
<col class="colAddButton"/>

<tbody><tr class="header"><td colspan="7">
    <b>%(text_define_changes)s</b> %(text_define_changes_explanation)s
</td><tr></tbody>

<tbody class="lastRow" valign="middle"><tr><td colspan="7" align="left">
    <img src="%(site_url)s/img/add.png" class="buttonNewField" alt="Add new"/>
    <span class="buttonNewField linkButton">%(text_define_field)s</span>
</td></tr></tbody>

</table>


<!-- Templates for displaying of actions -->

<table id="displayTemplates" width="100%%" cellspacing="0">
<col class="colDeleteButton"/>
<col class="colFieldTag"/>
<col class="colDeleteButton"/>
<col class="colSubfieldCode"/>
<col class="colActionType"/>
<col/>
<col class="colAddButton"/>

    <!-- Templates for fields -->

<tbody class="templateNewField">
    <tr class="tagTableRow">
        <td/>
        <td>%(text_field)s</td>
        <td /><td colspan="4" />
    </tr>
    <tr class="tagTableRow">
        <td />
        <td>
        <input class="textBoxFieldTag txtTag" type="Text" maxlength="3" /><input class="textBoxFieldInd1 txtInd" type="Text" maxlength="1" /><input class="textBoxFieldInd2 txtInd" type="text" maxlength="1" />
        </td>
        <td />
        <td />
        <td>
        <select class="fieldActionType" onchange="onFieldActionTypeChange(this);">
        <option value="%(text_select_action)s">%(text_select_action)s</option>
        <option value="0">%(text_add_field)s</option>
        <option value="1">%(text_delete_field)s</option>
        <option value="2">%(text_update_field)s</option>
        </select>
        </td>
        <td/>
        <td/>
    </tr>
    <tr class="tagTableRow"><td /><td /><td /><td /><td>&nbsp;</td><td/><td/></tr>
    </tbody>

<tr class="tagTableRow"><td /><td /><td>&nbsp;</td><td /><td colspan="2">
        <input value="%(text_save)s" type="button" id="buttonSaveNewField" class="formbutton"/>
        <input value="%(text_cancel)s" type="button" id="buttonCancelNewField" class="formbutton"/>
    </td><td/></tr>


<tbody class="templateDisplayField" valign="middle">
    <tr class="tagTableRow">
        <td><img src="%(site_url)s/img/delete.png" class="buttonDeleteField" alt="Delete"/></td>
        <td>
            <strong>
                <span class="tag"></span><span class="ind1"></span><span class="ind2"></span>
            </strong>
        </td>
        <td />
        <td />
        <td><span class="action colActionType"></span></td>
        <td class="conditionParametersDisplay">
            <span class="conditionParametersDisplay"><strong> %(text_with_condition)s</strong></span>
            <input id="textBoxConditionSubfieldDisplay" class="txtValue textBoxConditionSubfield conditionSubfieldParameters" type="text" maxlength="1"/>

            <span class="conditionExact conditionParametersDisplay"></span>
            <input id="textBoxConditionFieldDisplay" class="txtValue textBoxCondition conditionParametersDisplay" type="text"/>
        </td>
        <td>
            <img src="%(site_url)s/img/add.png" class="buttonNewSubfield" alt="Add new"/>
            <span class="buttonNewSubfield linkButton">%(text_define_subfield)s</span>
        </td>
        <td />
    </tr>
    <tr class="conditionParameters">
        <td /> <td /> <td /> <td /><td colspan="3">%(text_condition_subfield_delete)s
        <input id="textBoxConditionSubfield" class="txtValue textBoxConditionSubfield" type="text" maxlength="1"/>
        <select class="selectConditionExactMatch">
            <option value="0">%(text_equal_to)s</option>
            <option value="1">%(text_contains)s</option>
            <option value="2">%(text_not_exists)s</option>
        </select>
        <input id="textBoxCondition" class="txtValue textBoxCondition" type="text" placeholder="%(text_condition)s"/>
        </td>
    </tr>
    <tr class="conditionActOnFields">
        <td /><td /><td /><td />
        <td colspan="3">
            <span class="actOnFieldLink" id="actOnFieldsDelete"><u>%(text_filter_fields)s</u></span>
        </td>
    </tr>
    <tr class="conditionActOnFieldsSave">
        <td /><td /><td /><td /><td>
            <input value="%(text_save)s" type="button" id="buttonSaveNewFieldCondition" class="formbutton"/>
            <input value="%(text_cancel)s" type="button" id="buttonCancelFieldCondition" class="formbutton">
        </td>
    </tr>
</tbody>

    <!-- Templates for subfields -->

<tbody class="templateDisplaySubfield">
<tr class="subfieldTableRow">
    <td />
    <td />
    <td><img src="%(site_url)s/img/delete.png" class="buttonDeleteSubfield" alt="Delete" /></td>
    <td>$$<span class="subfieldCode">a</span></td>
    <td>
        <span class="action colActionType">%(text_replace_text)s</span>&nbsp;
    </td>
    <td>
        <input id="textBoxValueDisplay" class="txtValue textBoxValue valueParameters" type="text"/>
        <span class="additionalValueParameters">
            <span class="beforeValueInput"> %(text_or)s </span>
            <input id="textBoxValueDisplay" class="txtValue textBoxValue valueParameters" type="text"/>
        </span>

        <span class="newValueParameters"><span class="beforeValueInput"> %(text_with)s </span></span>
        <input id="textBoxNewValueDisplay" class="txtValue textBoxNewValue newValueParameters" type="text" value="%(text_new_value)s"/>

        <span class="conditionParameters"><strong> %(text_with_condition)s</strong></span>
        <input id="textBoxConditionSubfieldDisplay" class="txtValue textBoxConditionSubfield conditionSubfieldParameters" type="text" maxlength="1"/>

        <span class="conditionExact conditionParameters"></span>
        <input id="textBoxConditionDisplay" class="txtValue textBoxCondition conditionParameters" type="text"/>

    </td>
    <td/>
</tr>
</tbody>


<tbody class="templateNewSubfield">
    <tr>
        <td />
        <td />
        <td />
        <td><input class="txtSubfieldCode textBoxSubfieldCode" type="text" maxlength="1"/></td>
        <td>
            <select class="subfieldActionType">
                <option value="0">%(text_add_subfield)s</option>
                <option value="1">%(text_delete_subfield)s</option>
                <option value="2">%(text_replace_content)s</option>
                <option value="3">%(text_replace_text)s</option>
            </select>
        </td>
    </tr>
    <tr class="valueParameters">
        <td /><td /><td /><td />
        <td>
            <input id="textBoxValue" class="txtValue textBoxValue" type="text" placeholder="%(text_value)s"/>
        </td>
        <td class="buttonCell">
            <img src="%(site_url)s/img/add.png" class="buttonNewValue" alt="Add new value"/>
            <span class="buttonNewValue linkButton">%(text_add_value)s</span>
        </td>
    </tr>
    <tr class="additionalValueParametersTmp">
        <td /><td /><td /><td class="beforeValueInput">OR</td >
        <td>
            <input id="textBoxValue" class="txtValue textBoxValue" type="text" placeholder="%(text_value)s"/>
        </td>
        <td class="buttonCell">
            <img src="%(site_url)s/img/delete.png" class="buttonDeleteValue" alt="Delete this condition value"/>
            <span class="buttonDeleteValue linkButton">%(text_delete_value)s</span>
        </td>
    </tr>
    <tr class="newValueParameters">
        <td /><td /><td /><td class="beforeValueInput">WITH</td>
        <td colspan="3">
            <input id="textBoxNewValue" class="txtValue textBoxNewValue" type="text" placeholder="%(text_new_value)s"/>
        </td>
    </tr>
    <tr class="conditionParameters">
        <td /> <td /> <td /> <td /><td colspan="3">%(text_condition_subfield)s
        <input class="txtValue textBoxConditionSubfield" type="text" maxlength="1"/>
        <select class="selectConditionExactMatch">
            <option value="0">%(text_equal_to)s</option>
            <option value="1">%(text_contains)s</option>
            <option value="2">%(text_not_exists)s</option>
        </select>
        <input id="textBoxCondition" class="txtValue textBoxCondition" type="text" placeholder="%(text_condition)s"/>
        </td>
    </tr>
    <tr class="conditionActOnFields">
        <td /><td /><td /><td />
        <td colspan="3">
            <span class="actOnFieldLink" id="actOnFields"><u>%(text_filter_fields)s</u></span>
        </td>
    </tr>
    <tr>
        <td /><td /><td /><td /><td>
            <input value="%(text_save)s" type="button" id="buttonSaveNewSubfield" class="formbutton"/>
            <input value="%(text_cancel)s" type="button" id="buttonCancelNewSubfield" class="formbutton">
        </td>
    </tr>
</tbody>

<tbody class="templateMsg">
    <tr>
        <td colspan="100"><span class="msg"></span></td>
        <td/>
        <td/>
        <td/>
        <td/>
        <td/>
        <td/>
    </tr>
</tbody>

</table>

        """% {"site_url" : CFG_SITE_URL,
              "text_define_changes" : _("2. Define changes"),
              "text_define_changes_explanation" : _("Specify fields and their subfields that should be changed in every record matching the search criteria."),
              "text_define_field" : _("Define new field action"),
              "text_define_subfield" : _("Define new subfield action"),
              "text_add_value" : _("Add new condition value"),
              "text_delete_value" : _("Remove this condition value"),
              "text_field" : _("Field"),
              "text_select_action" : _("Select action"),
              "text_add_field" : _("Add field"),
              "text_delete_field" : _("Delete field"),
              "text_update_field" : _("Update field"),
              "text_add_subfield" : _("Add subfield"),
              "text_delete_subfield" : _("Delete subfield"),
              "text_save" : _("Save"),
              "text_cancel" : _("Cancel"),
              "text_replace_text" : _("Replace substring"),
              "text_replace_content" : _("Replace full content"),
              "text_or" : _("or"),
              "text_with" : _("with"),
              "text_with_condition": _("when subfield $$"),
              "text_new_value" : _("new value"),
              "text_equal_to" : _("is equal to"),
              "text_contains" : _("contains"),
              "text_not_exists" : _("does not exist"),
              "text_condition" : _("condition"),
              "text_condition_subfield" : _("when other subfield"),
              "text_condition_subfield_delete" : _("when subfield"),
              "text_filter_fields": _("Apply only to specific field instances"),
              "text_value" : _("value")
             }
        return html

    def detailed_record(self, record_content, language):
        """Returns formated content of a detailed record

        @param record_content: content of the record to be displayed
        @param language: language used to display the content
        """
        _ = gettext_set_language(language)

        result = """
        <table class="searchresultsbox">
            <tr>
                <td class="searchresultsboxheader">
                    <span class="buttonBackToResults linkButton"><b><< %(text_back_to_results)s </b></span>
                </td>
                <td class="searchresultsboxheader" style="text-align: right;">
                    <span class="buttonOutputFormatMARC  linkButton">MARC</span>,
                    <span class="buttonOutputFormatHTMLBrief  linkButton">HTML Brief</span>,
                    <span class="buttonOutputFormatHTMLDetailed linkButton">HTML Detailed</span>
                </td>
            </tr>
        </table>

        %(record_content)s

        """% {"record_content" : record_content,
             "text_back_to_results" : _("Back to Results")
             }

        return result

    def info_box(self, language, total_modifications):
        """Returns list with a summary of the number of modifications
           made to records

           @param language: language used to display the content
           @param total_modifications: list of modifications to records, fields
                                      and subfields
        """
        _ = gettext_set_language(language)

        modifications_html = " "
        if total_modifications:
            modification_display_list= """<ul>
                                              <li>Records: %(records_modified)s</li>
                                              <li>Fields: %(fields_modified)s</li>
                                              <li>Subfields: %(subfields_modified)s</li>
                                          </ul>
                                       """ % {
                                              "records_modified": str(total_modifications[0]),
                                              "fields_modified": str(total_modifications[1]),
                                              "subfields_modified": str(total_modifications[2])
                                             }
            modifications_html = """<div class="modify-list"> %(modify_text)s <br /> %(modification_display)s </div>
                                """ % {"modify_text": "The actions defined will affect:",
                                       "modification_display": modification_display_list}

        return modifications_html

    def tmpl_locked_record_list(self, language, locked_records):
        """Returns list of records currently locked in the bibsched queue
        """
        _ = gettext_set_language(language)

        locked_msg = _("WARNING: The following records are pending execution\
                        in the task queue.\
                        If you proceed with the changes, the modifications made\
                        with other tool (e.g. BibEdit) to these records will\
                        be lost")

        locked_list = ["<ul>"]
        for recid in locked_records:
            locked_list.append("<li><a href=%s  target='_blank'>%s</a></li>" % (CFG_SITE_URL + "/record/" + str(recid), recid))

        return ("<div class='clean-error'>" + locked_msg + "<br />" +
                '\n'.join(locked_list) + "</div>")

    def _build_navigation_image(self, class_name, image_file_name, alt_text):
        """Creates html for image from the page navigation line """
        navigation_image = '<img border="0" class="%(class)s" alt="%(alt)s" src="%(site_url)s/img/%(image_file_name)s"/>' % {
                "class" : class_name,
                "alt" : alt_text,
                "site_url" : CFG_SITE_URL,
                "image_file_name" : image_file_name
            }
        return navigation_image

    def _search_results_header(self, number_of_records, current_page, records_per_page, language, output_format):
        """Returns header of the search results"""

        _ = gettext_set_language(language)

        first_page_button = self._build_navigation_image("buttonGoToFirstPage", "sb.gif", _("begin"))
        previous_page_button = self._build_navigation_image("buttonGoToPreviousPage", "sp.gif", _("previous"))
        next_page_button = self._build_navigation_image("buttonGoToNextPage", "sn.gif", _("next"))
        #for now we don't have last page button.
        last_page_button = ""#self._build_navigation_image("buttonGoToLastPage", "se.gif", _("end"))

        first_record_on_page = (current_page-1)*records_per_page + 1
        last_record_on_page = first_record_on_page + records_per_page - 1
        if last_record_on_page > number_of_records:
            last_record_on_page = number_of_records

        last_page_number = number_of_records/records_per_page+1

        if current_page == 1:
            previous_page_button = ""
        if current_page < 2:
            first_page_button = ""
        if current_page == last_page_number:
            next_page_button = ""
            last_page_button = ""

        user_warning = ""
        if number_of_records > CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING:
            user_warning = """<div class="clean-error">%(warning_msg)s</div>
                           """ % {"warning_msg": "Due to the amount of records to be modified, you need 'superadmin' rights to send the modifications. If it is not the case, your changes will be saved once you click the 'Apply Changes' button and you will be able to contact the admin to apply them"
                                 }
        header = """
        %(user_warning)s
        <table class="searchresultsbox">
            <tr><td class="searchresultsboxheader">
                <strong>%(number_of_records)s</strong> %(text_records_found)s
                %(first_page_button)s %(previous_page_button)s

                %(first_record_on_page)s - %(last_record_on_page)s

                %(next_page_button)s %(last_page_button)s
            </td>
            <td class="searchresultsboxheader" style="text-align: right;">
            Output format: <select name="view_format" onchange="onSelectOutputFormatChange(this.value)">
                <option value="Marc" %(marc_selected)s>MARC</option>
                <option value="HTML Brief" %(brief_selected)s>HTML Brief</option>
                </select>
            </td>
            </tr>
        </table>

        """ % {"user_warning": user_warning,
               "number_of_records" : number_of_records,
               "text_records_found" : _("records found"),
               "first_page_button" : first_page_button,
               "previous_page_button" : previous_page_button,
               "next_page_button" : next_page_button,
               "last_page_button" : last_page_button,
               "first_record_on_page" : first_record_on_page,
               "last_record_on_page" : last_record_on_page,
               "marc_selected": output_format == "hm" and "SELECTED" or "",
               "brief_selected": output_format == "hb" and "SELECTED" or ""
            }

        return header


    def search_results(self, records, number_of_records, current_page, records_per_page, language, output_format, checked_records):
        """Retrurns the content of search resutls.

        @param records: list records to be displayed in the results.
        Contains tuples (record_id, formated_record)
            record_id - identifier of the record
            formated_record - content for the record ready for display

        @param language: language used to display the content
        """
        _ = gettext_set_language(language)

        result = " "

        for (record_id, record) in records:
            result += """
            <span class="resultItem" id="recordid_%(record_id)s">
            <div class="divRecordCheckbox">
            <input type="checkbox" name="recordCheckbox" class="recordCheckbox" value="%(record_id)s"
            """ % {"record_id": record_id,
                  }
            if record_id in checked_records:
                result += ' checked="checked"'
            result += """
            /></div>
            <div class="divRecordPreview">
            %(record)s
            </div>
            </span><br><hr>
            """ % {"record": record}

        result_header = self._search_results_header(number_of_records = number_of_records,
                                                    current_page = current_page,
                                                    records_per_page = records_per_page,
                                                    language = language,
                                                    output_format=output_format)
        result = result_header + result + result_header

        return result

    def scripts(self):
        """Returns the scripts that should be imported."""

        scripts = [
            "vendors/json2/json2.js",
            "js/bibeditmulti.js"
        ]

        result = ""
        for script in scripts:
            result += '<script type="text/javascript" src="%s/%s">' \
            '</script>\n' % (CFG_SITE_URL, auto_version_url(script))

        return result

    def changes_applied(self, status, file_path):
        """ returns html message when changes sent to server """

        if status == 0:
            body = """
                   <div class="clean-ok"><div>Changes have been sent to the server. It will take some time before they are applied. You can <a href=%s/%s/multiedit>reset </a> the editor.</div>
                   """ % (CFG_SITE_URL, CFG_SITE_RECORD)
        elif status in [1, 2]:
            body = """
                   <div class="clean-ok">You are submitting a file that manipulates more than %s records. Your job will therefore be processed only during <strong>%s</strong>. <br /><br />
            If you are not happy about this, please contact %s, quoting your file <strong>%s</strong> <br /><br />
            You can <a href=%s/%s/multiedit>reset</a> the editor.</div>
                   """ % (CFG_BIBEDITMULTI_LIMIT_INSTANT_PROCESSING,
                          CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING_TIME,
                          CFG_SITE_ADMIN_EMAIL,
                          file_path,
                          CFG_SITE_URL,
                          CFG_SITE_RECORD)
        else:
            body = """
                   <div class="clean-error">Sorry, you are submitting a file that manipulates more than %s records. You don't have enough rights for this.
                   <br /> <br />
                   If you are not happy about this, please contact %s, quoting your file %s <br /><br />
                   You can <a href=%s/%s/multiedit>reset</a> the editor.</div>
                   """ % (CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING,
                          CFG_SITE_ADMIN_EMAIL,
                          file_path,
                          CFG_SITE_URL,
                          CFG_SITE_RECORD)
        return body

