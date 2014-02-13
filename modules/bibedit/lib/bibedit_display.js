/*
 * This file is part of Invenio.
 * Copyright (C) 2009, 2010, 2011, 2012 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/*
 * This is the BibEdit Javascript for generation of webpage elements and HTML.
 */

function displayRecord() {
    /*
     * Create the main content table.
     */

    // Every time we display the table, mark all checkboxes to show/hide
    // specific tags
    displayAllTagsCheckboxes();

    if (gRecordHideAuthors) {
        $("#focuson_authors").prop("checked", false)
    }

    var table = '' + '<table id="bibEditTable">' +
        '<col span="1" class="bibEditColFieldBox"/>' +
        '<col span="1" id="bibEditColFieldTag"/>' +
        '<col span="1" class="bibEditColFieldBox" />' +
        '<col span="1" id="bibEditColSubfieldTag" />' +
        '<col span="1" />' +
        '<col span="1" id="bibEditColSubfieldAdd" />' +
        // Create a dummy row to hack layout in like FF..
        '<tbody style="border: 0px;">' + '<tr>' +
        '<td style="padding: 0px; max-width: 14px;"></td>' +
        '<td style="padding: 0px; max-width: 100px;"></td>' +
        '<td style="padding: 0px; max-width: 14px;"></td>' +
        '<td style="padding: 0px; max-width: 80px;"></td>' +
        '<td style="padding: 0px"></td>' +
        '<td style="padding: 0px; max-width: 16px;"></td>' +
        '</tr>' +
        '</tbody>';

    var tags = getTagsSorted(),
        tag, fields;

    // For each controlfield, create row.
    for (var i = 0, n = tags.length; i < n; i++) {
        tag = tags[i];
        // If not controlfield, move on.
        if (!validMARC.reControlTag.test(tag)) {
            break;
        }
        fields = gRecord[tag];
        for (var j = 0, m = fields.length; j < m; j++) {
            table += createControlField(tag, fields[j], j);
        }
    }

    // For each instance of each field, create row(s).
    for (n = tags.length; i < n; i++) {
        tag = tags[i];
        if ( $.inArray(tag, gDisplayAuthorTags) !== -1 && gRecordHideAuthors ) {
            continue;
        }
        fields = gRecord[tag];
        for (var j = 0, m = fields.length; j < m; j++) {
            table += createField(tag, fields[j], j);
        }
    }

    // Close and display table.
    table += '</table>';
    $('#bibEditContentTable').css('overflow', 'auto');
    $('#bibEditContentTable').append(table);

    // now displaying the remaining controls
    for (changeNr in gHoldingPenChanges) {
        addChangeControl(changeNr, false);
    }
    colorFields();
}

function createControlField(tag, field, fieldPosition) {
    /*
     * Create control field row.
     */
    var fieldID = tag + '_' + fieldPosition;
    var cellContentClass = 'class="bibEditCellContentProtected" ';
    if (!fieldIsProtected(tag)) cellContentClass = '';

    return '<tbody id="rowGroup_' + fieldID + '">' +
        '<tr id="row_' + fieldID + '" >' +
            '<td class="bibEditCellField">' +
            '</td>' +
            '<td id="fieldTag_' + fieldID +
                '" class="bibEditCellFieldTag">' + getFieldTag(tag) + '</td>' +
            '<td></td>' + '<td></td>' +
            '<td id="content_' + fieldID + '" ' + cellContentClass +
                'colspan="2" tabindex="0">' + escapeHTML(field[3]) +
            '</td>' +
        '</tr>' +
        '</tbody>';
}

function createField(tag, field, fieldPosition) {
    /*
     * Create field row(s).
     */
    var subfields = field[0],
        ind1 = field[1],
        ind2 = field[2];
    var fieldID = tag + '_' + fieldPosition;
    ind1 = (ind1 != ' ' && ind1 != '') ? ind1 : '_';
    ind2 = (ind2 != ' ' && ind2 != '') ? ind2 : '_';
    var protectedField = fieldIsProtected(tag + ind1 + ind2);
    var subfieldsLength = subfields.length;
    var result = '<tbody ' + 'id="rowGroup_' + fieldID + '">';
    for (var i = 0, n = subfields.length; i < n; i++) {
        var subfield = subfields[i];
        result += createRow(tag, ind1, ind2, subfield[0],
            escapeHTML(subfield[1]), fieldID, i, subfieldsLength,
            protectedField);
    }
    return result + '</tbody>';
}

function createRow(tag, ind1, ind2, subfieldCode, subfieldValue, fieldID,
                   subfieldIndex, subfieldsLength, protectedField) {
    /*
     * Create single row (not controlfield).
     */
    var MARC = tag + ind1 + ind2 + subfieldCode;
    var protectedSubfield = (protectedField) ? true : fieldIsProtected(MARC);
    var subfieldID = fieldID + '_' + subfieldIndex;
    var boxField = '',
        cellFieldTagAttrs = 'class="bibEditCellField"',
        fieldTagToPrint = '',
        cellContentClass = 'bibEditCellContentProtected',
        cellContentTitle = '',
        cellContentOnClick = '';
    var autosuggestkeypress = "";
    var autosuggest = false;
    var autocomplete = false;
    var autokeyword = false;
    for (var i = 0, n = gAUTOSUGGEST_TAGS.length; i < n; i++) {
        if (MARC == gAUTOSUGGEST_TAGS[i]) {
            autosuggest = true;
        }
    }
    for (var i = 0, n = gAUTOCOMPLETE_TAGS.length; i < n; i++) {
        if (MARC == gAUTOCOMPLETE_TAGS[i]) {
            autocomplete = true;
        }
    }
    if (MARC == gKEYWORD_TAG) {
        autokeyword = true;
    }
    if (!protectedField) {
        // Enable features for unprotected fields.
        if (!protectedSubfield) {
            cellContentClass = 'bibEditCellContent';
            cellTabSwitch = ' tabSwitch';
            cellContentTitle = 'title="Click to edit" ';
            if (autosuggest || autokeyword) {
                cellContentTitle = 'title="Click to edit (suggest values: ctrl-shift-a) " ';
            }
            if (autocomplete) {
                cellContentTitle = 'title="Click to edit (complete values: ctrl-shift-a) " ';
            }
            cellContentOnClick = 'onclick="onContentClick(event, this)" ';
        }
    }
    cellContentAdditionalClass = "";
    if (subfieldValue.substring(0, 9) == "VOLATILE:") {
        subfieldValue = subfieldValue.substring(9);
        cellContentAdditionalClass += " bibEditVolatileSubfield";
    }
    var boxSubfield = input('checkbox', 'boxSubfield_' + subfieldID, 'bibEditBoxSubfield', {
        onclick: 'onSubfieldBoxClick(this)',
        tabindex: -1
    });
    var subfieldTagToPrint = getSubfieldTag(MARC);
    var btnAddSubfield = '';
    // If first subfield, add tag and selection box, remove up arrow.
    if (subfieldIndex == 0) {
        boxField = input('checkbox', 'boxField_' + fieldID, 'bibEditBoxField', {
            onclick: 'onFieldBoxClick(event, this)',
            tabindex: -1
        });
        cellFieldTagAttrs = 'id="fieldTag_' + fieldID +
            '" class="bibEditCellFieldTag ' + cellContentClass + '" ' +
            cellContentTitle + cellContentOnClick + 'tabindex="0" ';
        fieldTagToPrint = getFieldTag(MARC);
    }
    // If last subfield, remove down arrow, add 'Add subfield' button.
    if (subfieldIndex == subfieldsLength - 1) {
        if (!protectedField) btnAddSubfield = img('/img/add.png',
                                                  'btnAddSubfield_' + fieldID,
                                                  '', {
                                            title: 'Add subfield',
                                            onclick: 'onAddSubfieldsClick(this)'
                                            });
    }
    var btnDOISearch = '';
    if (typeof gDOILookupField !== 'undefined') {
        // check if it's the DOI field
        if (tag == gDOILookupField.substring(0,3) &&
            ind1 == gDOILookupField.substring(3,4) &&
            ind2 == gDOILookupField.substring(4,5)  &&
            subfieldCode == gDOILookupField.substring(5,6)) {
            btnDOISearch = img('/img/search.png',
                'btnSearchDOI_' + fieldID,
                '', {
                    title: 'Search for DOI in dx.doi.org',
                    onclick: "onDOISearchClick(this)"
                });
        }
    }

    myelement = '' +
        '<tr id="row_' + subfieldID + '">' +
            '<td class="bibEditCellField">' + boxField + '</td>' + '<td ' +
                cellFieldTagAttrs + '>' + fieldTagToPrint +
            '</td>' +
            '<td class="bibEditCellSubfield">' + boxSubfield +
            '</td>' +
            '<td id="subfieldTag_' + subfieldID +
                '" class="bibEditCellSubfieldTag ' + cellContentClass + '" ' +
                cellContentTitle + cellContentOnClick + 'tabindex="0">' +
                subfieldTagToPrint +
            '</td>' +
            '<td id="content_' + subfieldID + '" class="' + cellContentClass +
                cellContentAdditionalClass + cellTabSwitch + '" ' + cellContentTitle +
                autosuggestkeypress + cellContentOnClick + 'tabindex="0">' +
                subfieldValue +
            '</td>' +
            '<td class="bibEditCellAddSubfields">' + btnAddSubfield +
            btnDOISearch + '</td>' +
        '</tr>'; /* add a place where the autosuggest box goes, if needed */
    if (autosuggest || autokeyword) {
        myelement = myelement +
            '<tr><td></td><td></td><td></td><td></td>\
            <td tabindex="0" id="autosuggest_' +
            subfieldID + '">' + '<td></td></td></tr>';
    }
    return myelement;
}

function redrawFields(tag, skipAddFileds) {
    /*
     * Redraw all fields for a given tag.
     * skipAddFileds - forces to skip drawing the controls corresponding to the
     * change of adding a field
     *
     * WARNING: if we have added two (or more) fields with completely
     * new tags a, b where a > b in the lexicographical order, redrawFields(b)
     * has to be executed before redrawFields(a)
     */
    var rowGroup = $('#rowGroup_' + tag + '_0'),
        prevRowGroup;
    if (rowGroup.length) {
        // Remove the fields from view.
        prevRowGroup = rowGroup.prev();
        prevRowGroup.nextAll('[id^=rowGroup_' + tag + ']').remove();
    } else {
        // New tag. Determine previous sibling.
        var prevTag = getPreviousTag(tag);
        var lastIndex = gRecord[prevTag].length - 1;
        prevRowGroup = $('#rowGroup_' + prevTag + '_' + lastIndex);
    }

    // Redraw all fields and append to table.
    if (gRecord[tag]) {
        var fields = gRecord[tag];
        var result = '',
            i, n;
        if (validMARC.reControlTag.test(tag)) {
            for (i = 0, n = fields.length; i < n; i++) {
                result += createControlField(tag, fields[i], i);
            }
        } else {
            for (i = 0, n = fields.length; i < n; i++) {
                result += createField(tag, fields[i], i);
            }
        }
        prevRowGroup.after(result);
    }

    // Now redraw all the Holding Pen changes connected controls
    for (changeNr in gHoldingPenChanges) {
        if (gHoldingPenChanges[changeNr]["tag"] == tag && gHoldingPenChanges[changeNr]["applied_change"] != true ) {
            addChangeControl(changeNr, skipAddFileds);
        }
    }
}

function redrawFieldPosition(tag, fieldPosition) {
    /*
        Redraws only the field indicated by fieldPosition
    */
    var currentFieldSelector = $("#rowGroup_"  + tag + "_" + fieldPosition);
    currentFieldSelector.after(
    createField(tag, gRecord[tag][fieldPosition], fieldPosition));
    currentFieldSelector.remove();
}

/// The Holding Pen changes connected functions
/// rendering the field content

function removeAddFieldControl(changeNo) {
    /** A function removing the interface element associated with the Add Field
      Holding Pen change

      Arguments:
        changeNo: a number of the change, the control is associated with
   */
    $("#changeBox_" + changeNo).remove();
    if ( $('#bibEditHoldingPenAddedFields').find('.bibeditHPCorrection').length < 1 ) {
         $('#bibEditHoldingPenAddedFields').remove();
    }
}

/// generating the changes controls

function getApplyChangeButton(functionName, changeNo){
  /*Returning the HTML code of the Apply change button
   * functionName - the name of the function called when the button is clicked
   *                The function has to take one argument being the number of the
   *                change
   * changeNo - the number of the change the button is associated with
   */

  return "<button title='Apply' onClick=\"return " + functionName + "(" + changeNo + ");\"><img src=\"/img/wsignout.gif\"></img></button>";
}

function getRejectChangeButton(changeNo){
  /*The button allowing to reject the change - and remove the control from the user interface*/
  result = "<button title='Discard' onClick=\"onRejectChangeClicked(" +
      changeNo + ");\"><img src=\"/img/iconcross2.gif\"></img></button>";
  return result;
}

function getAddInsteadOfChangeButton(functionName, changeNo){
  /*The button allowing to reject the change - and remove the control from the user interface*/
  result = "<button title='Add changes as a new field' onClick=\"" + functionName + "(" +
      changeNo + ");\"><img src=\"/img/plus_orange.png\"></img></button>";
  return result;
}

function addSubfieldChangedControl(changeNo) {
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    sfPos = gHoldingPenChanges[changeNo]["subfield_position"];
    content = gHoldingPenChanges[changeNo]["subfield_content"];

    applyButton = getApplyChangeButton("applySubfieldChanged", changeNo);
    rejectButton = getRejectChangeButton(changeNo);
    // apply the change as if it was adding the subfield ( the data is the same)
    addButton = getAddInsteadOfChangeButton("applyFieldAdded", changeNo);
    /* adds a control allowing to change the subfield content */

    newel = "<div class=\"bibeditHPCorrection\"><span>" + content +
        "</span>&nbsp;&nbsp;" +
        "<div class=\"HPCorrectionButtonWrapper\">" +
        applyButton +
        rejectButton +
        addButton +
        "</div>" +
        "</div>";

    $("#content_" + fieldId + "_" + fieldPos + "_" + sfPos).append(newel);
}

function addSubfieldSameControl(changeNo) {
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    sfPos = gHoldingPenChanges[changeNo]["subfield_position"];
    content = "Same content";

    newel = "<div class=\"bibeditHPCorrection bibeditHPSame\"><span>" + content +
        "</span>&nbsp;&nbsp;" +
        "</div>";

    $("#content_" + fieldId + "_" + fieldPos + "_" + sfPos).append(newel);
}

function addSubfieldAddedControl(changeNo) {
    /* adds a control allowing to add a new subfield using the holding pen */
    fieldId = gHoldingPenChanges[changeNo].tag;
    fieldPos = gHoldingPenChanges[changeNo].field_position;
    subfieldCode = gHoldingPenChanges[changeNo].subfield_code;
    subfieldContent = gHoldingPenChanges[changeNo].subfield_content;

    applyButton = getApplyChangeButton("applySubfieldAdded", changeNo);
    rejectButton = getRejectChangeButton(changeNo);

    subfieldPreview = "$$" + subfieldCode + "&nbsp;&nbsp;&nbsp;" +
        subfieldContent;
    newel = "<tr><td></td><td></td><td></td><td></td><td>" +
        "<div class=\"bibeditHPCorrection\"><span>Subfield added: " +
        subfieldPreview + "</span>" + "<div>" + "<div class=\"HPCorrectionButtonWrapper\">" + applyButton + rejectButton + "</div>" +
        "</div></div></td><td></td></tr>";

    $("#rowGroup_" + fieldId + "_" + fieldPos).append(newel);
}

function addSubfieldRemovedControl(changeNo) {
    /* adds a control allowing to apply the change of removing the subfield  */
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    sfPos = gHoldingPenChanges[changeNo]["subfield_position"];

    applyButton = getApplyChangeButton("applySubfieldRemoved", changeNo);
    rejectButton = getRejectChangeButton(changeNo);

    newel = "<div class=\"bibeditHPCorrection\"><span>" +
        "The subfield has been removed " + "</span>" + "<div class=\"HPCorrectionButtonWrapper\">" + applyButton +
        rejectButton + "</div>" + "</div>";
    $("#content_" + fieldId + "_" + fieldPos + "_" + sfPos).append(newel);
}

function addFieldRemovedControl(changeNo) {
    /* adds a control allowing the change of removing the Field */
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];

    applyButton = getApplyChangeButton("applyFieldRemoved", changeNo);
    rejectButton = getRejectChangeButton(changeNo);

    newel = "<tr><td></td><td></td><td></td><td></td><td>" +
        "<div class=\"bibeditHPCorrection\">" +
        "Field has been removed in the Holding Pen. " + "<div class=\"HPCorrectionButtonWrapper\">" + applyButton +
        rejectButton + "</div>" + "</div></td><td></td></tr>";

    $("#rowGroup_" + fieldId + "_" + fieldPos).append(newel);
}

function addFieldChangedControl(changeNo) {
    /* adds a control allowing the change of removing the Field */

    fieldId = gHoldingPenChanges[changeNo]["tag"];
    indicators = gHoldingPenChanges[changeNo]["indicators"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    fieldContent = gHoldingPenChanges[changeNo]["field_content"];

    applyButton = getApplyChangeButton("applyFieldChanged", changeNo);
    rejectButton = getRejectChangeButton(changeNo);
    addButton = getAddInsteadOfChangeButton("applyFieldAdded", changeNo);

    fieldPreview = createFieldPreview(fieldId, indicators, fieldContent);

    newel = "<tr><td></td><td></td><td></td><td></td><td>" +
    "<div class=\"bibeditHPCorrection\">" +
    "Field structure has changed. New value: " + fieldPreview + "<br>" +
    "<div class=\"HPCorrectionButtonWrapper\">" + applyButton + rejectButton + addButton + "</div>" + "</div></td><td></td></tr>";

    $("#rowGroup_" + fieldId + "_" + fieldPos).append(newel);
}


function addFieldAddedControl(changeNo) {
    /* adds a control allowing the change of adding the Field */

    fieldId = gHoldingPenChanges[changeNo]["tag"];
    indicators = gHoldingPenChanges[changeNo]["indicators"];
    field = gHoldingPenChanges[changeNo]["field_content"];
    fieldContent = createFieldPreview(fieldId, indicators, field);
    //fieldContent = returnASummaryOfTheField(fieldId, field);
    applyButton = getApplyChangeButton("applyFieldAdded", changeNo);
    rejectButton = getRejectChangeButton(changeNo);

    content = "<div style=\"clear:both;\"></div><div class=\"bibeditHPCorrection\" id=\"changeBox_" + changeNo +
        "\">" + "<div>A field has been added in the Holding Pen entry </div> " +
        "<div>" + fieldContent + "</div>" + "<div>" + "<div class=\"HPCorrectionButtonWrapper\">" + applyButton +
        rejectButton + "</div>" + "</div></div>";

    if ( $('#bibEditHoldingPenAddedFields').length < 1 ) {
      var addedFiedsDivHtml = "<div id=\"bibEditHoldingPenAddedFields\"><div id=\"bibEditHoldingPenAddedFieldsLabel\">" +
      "<strong>Added fields in Holding Pen</div></strong></div>";
      $("#bibEditContentTable").append(addedFiedsDivHtml);
    }

    $('#bibEditHoldingPenAddedFields').append(content);
}

function removeAllChangeControls() {
    /** Removing all the change controls from the interface
     */
    $(".bibeditHPCorrection").remove();
    $('#bibEditHoldingPenAddedFields').remove();
}

function addChangeControl(changeNum, skipAddedField) {
    /** creates a web controls responsible for applying a particular change
      changeNum is the number of the change - it is the same as the index
      in gHoldingPenChanges global array */

    if (gHoldingPenChanges[changeNum].applied_change === true) {
        return;
    }
    changeType = gHoldingPenChanges[changeNum]["change_type"];
    if (changeType == "field_added" && skipAddedField != true && $("#changeBox_" + changeNum).length < 1 ) {
        addFieldAddedControl(changeNum);
    }
    if (changeType == "subfield_changed") {
        addSubfieldChangedControl(changeNum);
    }
    if (changeType == "subfield_removed") {
        addSubfieldRemovedControl(changeNum);
    }
    if (changeType == "subfield_same") {
        addSubfieldSameControl(changeNum);
    }
    if (changeType == "subfield_added") {
        addSubfieldAddedControl(changeNum);
    }
    if (changeType == "field_removed") {
        addFieldRemovedControl(changeNum);
    }
    if (changeType == "field_changed") {
        addFieldChangedControl(changeNum);
    }
}

/// the functions for creating the previews

function createFieldPreviewCore(tag, indicators, subfields) {
    /* A function creating a HTML preview of the record part */

    headerData = tag + indicators + "&nbsp;&nbsp;&nbsp;";
    var result = "";

    for (subfield in subfields) {
        if (subfields[subfield][1].substring(0,9) != "VOLATILE:") {
            result += "<tr><td>" + headerData +
                "</td><td>$$" + subfields[subfield][0] +
                "&nbsp;&nbsp;&nbsp;</td><td>" + subfields[subfield][1] +
                "</td></tr>";
            headerData = "";
        }
    }
    return result;
}

function createFieldPreview(tag, indicators, subfields) {
    /* Creating a preview of a single field */
    return "<table class=\"bibeditHPFieldPreview\" >" + createFieldPreviewCore(tag, indicators, subfields) +
        "</table>";
}

function createRecordPreview(recordData) {
    /* A function creating a preview of the record */

    // 1) sorting Tags
    unsortedTags = [];
    for (tag in recordData) {
        unsortedTags.push(tag);
    }
    tags = unsortedTags.sort();

    result = "<table>";
    for (tagIndex in tags) {
        tag = tags[tagIndex];
        // now we have to sort the fields by the indicators
        unsortedIndicators = [];
        indicatorLists = {};

        for (field in recordData[tag]) {
            indicators = (recordData[tag][field][1] == ' ' ? '_' :
                recordData[tag][field][1]) + (recordData[tag][field][2] == ' ' ?
                '_' : recordData[tag][field][2]);
            if (indicatorLists[indicators] == undefined) {
                indicatorLists[indicators] = [];
                unsortedIndicators.push(indicators);
            }
            indicatorLists[indicators].push(field);
        }
        sortedIndicators = unsortedIndicators.sort();

        // traversing all the fields in previously indicated order
        for (indicatorsInd in sortedIndicators) {
            indicators = sortedIndicators[indicatorsInd];
            for (fieldInd in indicatorLists[indicators]) {
                field = indicatorLists[indicators][fieldInd];
                var isVolatile = true;
                for (var sfPos in recordData[tag][field][0] ) {
                   if (recordData[tag][field][0][sfPos][1].substring(0,9) != "VOLATILE:"){
                     isVolatile = false;
                     break;
                   }
                }
                if (!isVolatile) {
                result += createFieldPreviewCore(tag, indicators,
                                                 recordData[tag][field][0]);
                }
            }
        }
    }
    result += "</table>";
    return result;
}

/// the entries on the left, in the panel

function createHoldingPenChangePreview(record) {
    /** A function creating the content
     *
     *  Parameters:
     *     record - A content of the record that should be previewed
     */

    return "<button onClick=\"onToggleDetailsVisibility(" +
            changesetNumber + ");\">Hide preview</button><br>" +
            createRecordPreview(record) +
            "<button onClick=\"onToggleDetailsVisibility(" +
            changesetNumber + ");\">Hide preview</button><br>";
}


function createHoldingPenPanelEntry(changesetNumber, changesetDatetime){
   /**
   * A function creating the panel entry describing one changeset
   * Parameters:
   *
   *    changesetNumber - the internal changeset number ( from the Holding Pen )
   *    changesetDatetime - the data of harvesting the changeset
   *
   * Returns: The HTML code of the control
   */

    manipulationControlsSection = //"<div class=\"bibeditHPEntryControlsPanel\">" +
        button("<img src=\"/img/add.png\">",
            id = ("bibeditHPApplyChange" + changesetNumber),
            _class = "bibeditHPControl",
            attrs = {
              "onClick" :
                ("return holdingPenPanelApplyChangeSet("+ changesetNumber + ");"),
              "title" : "Apply Holding Pen changes"
            }) +
        button("<img src=\"/img/delete.png\">",
            id = ("bibeditHPRemoveChange" + changesetNumber),
            _class = "bibeditHPControl",
            attrs = {
              "onClick" :
                ("return holdingPenPanelRemoveChangeSet("+ changesetNumber + ");"),
                "title" : "Remove Holding Pen changes"
            });
        //"</div>";

    numberSection = "<div class=\"bibeditHPEntryNumber\"></div>";

    datetimeSection = "<div class=\"bibeditHPEntryDateSection\">" + changesetDatetime + "</div>";

    previewOpener = "<div id=\"holdingPenToggleDetailsVisibility_" + changesetNumber +
                  "\" onClick=\"onToggleDetailsVisibility(" + changesetNumber +
                  ");\" class=\"bibeditHPDetailsOpener\"><img src=\"/img/magnifying_plus.png\"></div>";

    previewLayer = "<div class=\"bibeditHPContentPreviewBox bibeditHPHiddenElement\" id=\"holdingPenPreview_" + changesetNumber + "\">" +
      "Loading... <br>"  +
      "<br><button onClick=\"onToggleDetailsVisibility(" + changesetNumber + ");\">Hide preview</button></div>"; // a toggle button ;

    previewSection = previewOpener + previewLayer

    result =   "<div class=\"bibeditHPPanelEntry\" id=\"bibeditHoldingPenPanelEntry_" + changesetNumber + "\">" +
      "<div class=\"bibeditHPEntryCol1\">" +
      "<div class=\"bibeditHPEntryRow1\">" + datetimeSection + "</div>" +
          "<div class=\"bibeditHPEntryRow2\">" + previewSection + "</div>" +
      "</div><div class=\"bibeditHPEntryCol2\">"+ manipulationControlsSection + "</div>" +
          "</div>";

    return result;
}

function createGeneralControlsPanel() {
    /* Generating a panel that allows to perform global operations on
     * the previewed changes
     */
    result = "<div id=\"bibeditHoldingPenGC\">";
    result += "<button onClick=\"onAcceptAllChanges();\">Apply all the changes</button>";
    result += "<button onClick=\"onRejectAllChanges();\"> Reject all the changes</button>";
    result += "<button id=\"acceptReferences\" onClick=\"onAcceptAllReferences();\"> Apply all references</button>";
    result += "</div>";

    return result;
}

/// end of the Holding Pen Connected functions

function getToolbarButtonSet() {
    /*
     * Returns an object defining the available buttons
     */
    var toolbar_button_set = {
        /* title  id  path  position  requires_pdf  callback*/
        'Preview record': ['img_preview', '/img/document-preview.png',
                           'right', false, onPreviewClick],
        'Open PDF file': ['img_open_pdf', '/img/application_pdf.png',
                          'right', true, onOpenPDFClick],
        'Print page': ['img_print', '/img/document-print.png', 'right',
                        false, onPrintClick],
        'Text marc': ['img_textmarc', '/img/bibedit_textmarc.png', 'right',
                        false, onTextMarcClick],
        'Run reference extractor on this record': ['img_run_refextract',
                                                   '/img/ref_extract.png',
                                                   'left', true,
                                                   refextract.onRefExtractClick],
        'Extract references from text': ['img_extract_free_text',
                                         '/img/edit-paste.png', 'left',
                                         false, refextract.onRefExtractFreeTextClick],
        'Extract references from URL': ['img_extract_ref_url',
                                         '/img/bibedit_extract_url.png', 'left',
                                         false, refextract.onRefExtractURLClick]
    };

    return toolbar_button_set;
}

function createTopToolbar() { /* Generate BibEdit top toolbar */

    $('.headline_div').remove();

    var classMap = {
        'right': 'floatRight',
        'left': 'floatLeft'
    };

    var icon_height = 48,
        icon_width = 48;

    var toolbar_button_set = getToolbarButtonSet();

    $.each(toolbar_button_set, function(title, contents) {
        var id = contents[0];
        var url = contents[1];
        var pos = contents[2];

        var imghtml = '<img id="' + id + '" ' +
            'class="bibEditImgCtrlDisabled" ' + 'src="' + url + '" ' +
            'width="' + icon_width + 'px" ' + 'height="' +
            icon_height + 'px" ' + 'title="' + title + '" />';
        var iconhtml = '<div class="' + classMap[pos] + '">' +
            imghtml + '</div>';

        $('#Toptoolbar').append(iconhtml);
    });
}

function restartTextMarcViewIcon() {
    /*
    Change view icon to the default textmarc
    */
    $("#img_tableview").attr('src', '/img/bibedit_textmarc.png');
    $("#img_tableview").attr('id', 'img_textmarc');
}

function updateToolbar(enable) {
    /* Activate or deactivate buttons present in BibEdit's top toolbar */
    restartTextMarcViewIcon();

                        /* turn this .....         into this */
    var before_after = ['bibEditImgCtrlDisabled', 'bibEditImgCtrlEnabled'];
    if (!enable) before_after.reverse();

    var before = before_after[0];
    var after = before_after[1];

    var toolbar_button_set = getToolbarButtonSet();
    $.each(toolbar_button_set, function(title, contents) {
        var sel = '#' + contents[0];
        var requires_pdf = contents[3];
        var fn = contents[4];
        if (enable && requires_pdf && !gRecordHasPDF) { /* Skip iteration */
            return true;
        }
        $(sel).removeClass(before).addClass(after);
        if (enable) {
            $(sel).off('click').on('click', fn);
        }
        else {
            $(sel).off('click');
        }
    });
}

function createAddFieldForm(fieldTmpNo, fieldTemplateNo, def_field_tag,
                            def_ind1, def_ind2) {
    /*
     * Create an 'Add field' form.
     * fieldTmpNo - temporary field number
     * fieldTemplateNo - a number of template that should be selected by default
     */

    fieldTemplatesData = []
    for (templatePos in fieldTemplates) {
        fieldTemplatesData.push({
            "value": templatePos,
            "description": fieldTemplates[templatePos].name
        });
    }

    return '' + '<tbody id="rowGroupAddField_' + fieldTmpNo + '">' + '<tr>' +
        '<td></td>' + '<td><b>New</b></td>' + '<td></td>' + '<td></td>' +
        '<td><div class="bibEditAddFieldManipulationsBar">' +
        '<div class="bibEditAddFieldFormSelectTemplate">Add field: ' +
        select('selectAddFieldTemplate_' + fieldTmpNo,
            fieldTemplatesData, fieldTemplateNo) +
        '</div><div class="bibEditAddFieldFormCreateSimilar"> Add ' +
        input('text', 'selectAddFieldTemplateTimes_' + fieldTmpNo,
            "addFieldAddSimilarInput", {
                "maxlength": 4,
                "size": 1
        }) + button('similar', 'selectAddSimilarFields_' + fieldTmpNo, "", {}) +
        '</div></div></td>' + '<td>' +
        img('/img/add.png', 'btnAddFieldAddSubfield_' + fieldTmpNo, '', {
            title: 'Add subfield'
        }) + '</td>' + '</tr>' +
        createAddFieldRow(fieldTmpNo, 0, "", "", def_field_tag, def_ind1,
            def_ind2) +
        // adding a row used to insert at the end without repositioning the tag and indicators
        '<tr>' + '<td></td>' + '<td></td>' + '<td></td>' + '<td></td>' +
        '<td>' + '</td>' + '<td></td>' + '</tr>' + '</tbody>';
}

function createAddFieldRow(fieldTmpNo, subfieldTmpNo, defaultCode, defaultValue, def_field_tag, def_ind1, def_ind2) {
    /*
     * Create a row in the 'Add field' form.
     * optional parameters:
     *   defaultCode - the subfield code displayed by default
     *   defaultValue - the subfield value displayed by default
     */
    var fieldCode = "";
    var fieldValue = "";
    if (defaultCode != undefined && defaultCode != " ") {
        fieldCode = defaultCode;
    }
    if (defaultValue != undefined && defaultValue != " ") {
        fieldValue = defaultValue;
    }

    var isVolatile = (defaultValue != undefined && defaultValue.substring(0, 9) == "VOLATILE:");
    var additionalClass = "";
    if (isVolatile) {
        additionalClass = " bibEditVolatileSubfield";
        fieldValue = fieldValue.substring(9);
    }

    var txtAddFieldTag = '',
        txtAddFieldInd1 = '',
        txtAddFieldInd2 = '',
        btnAddFieldRemove = '';
    if (subfieldTmpNo == 0) {
        txtAddFieldTag = input('text', 'txtAddFieldTag_' + fieldTmpNo,
            'bibEditTxtTag', { maxlength: 3 }, def_field_tag);
        txtAddFieldInd1 = input('text', 'txtAddFieldInd1_' + fieldTmpNo,
            'bibEditTxtInd', { maxlength: 1 }, def_ind1);
        txtAddFieldInd2 = input('text', 'txtAddFieldInd2_' + fieldTmpNo,
            'bibEditTxtInd', { maxlength: 1 }, def_ind2);
    }
    else {
        btnAddFieldRemove = img('/img/delete.png', 'btnAddFieldRemove_' +
        fieldTmpNo + '_' + subfieldTmpNo, '', {
            title: 'Remove subfield'
        });
    }
    return '' + '<tr id="rowAddField_' + fieldTmpNo + '_' + subfieldTmpNo +
        '">' + '<td></td>' + '<td>' + txtAddFieldTag + txtAddFieldInd1 +
        txtAddFieldInd2 + '</td>' + '<td></td>' +
        '<td class="bibEditCellAddSubfieldCode">' +
        input('text', 'txtAddFieldSubfieldCode_' + fieldTmpNo + '_' +
            subfieldTmpNo, 'bibEditTxtSubfieldCode', {
                maxlength: 1,
                value: fieldCode
        }) + '</td>' + '<td>' + input('text', 'txtAddFieldValue_' + fieldTmpNo +
        '_' + subfieldTmpNo, 'bibEditTxtValue' + additionalClass, {
            value: fieldValue}) + '</td>' + '<td>' + btnAddFieldRemove +
        '</td>' + '</tr>';
}

function createAddSubfieldsForm(fieldID, defSubCode, defValue) {
    /*
     * Create an 'Add subfields' form.
     */
    return createAddSubfieldsRow(fieldID, 0, defSubCode, defValue) +
        '<tr id="rowAddSubfieldsControls_' + fieldID + '">' + '<td></td>' +
        '<td></td>' + '<td></td>' + '<td></td>' + '<td>' + '</td>' +
        '<td></td>' + '</tr>';
}

function createAddSubfieldsRow(fieldID, subfieldTmpNo, defSubCode, defValue) {
    /*
     * Create a row in the 'Add subfields' form.
     */
    var subfieldID = fieldID + '_' + subfieldTmpNo;
    var btnRemove = (subfieldTmpNo == 0) ? '' : img('/img/delete.png', 'btnAddSubfieldsRemove_' + subfieldID, '', {
        title: 'Remove subfield'
    });
    return '' + '<tr id="rowAddSubfields_' + subfieldID + '">' + '<td></td>' +
        '<td></td>' + '<td></td>' + '<td class="bibEditCellAddSubfieldCode">' +
        input('text', 'txtAddSubfieldsCode_' +
            subfieldID, 'bibEditTxtSubfieldCode', { maxlength: 1 }, defSubCode) +
            '</td>' + '<td>' + input('text', 'txtAddSubfieldsValue_' +
                subfieldID, 'bibEditTxtValue', {}, defValue) + '</td>' +
            '<td>' + btnRemove + '</td>' + '</tr>';
}

function displayMessage(msgCode, keepContent, args) {
    /*
     * Display message in the main work area. Messages codes returned from the
     * server (positive integers) are as specified in the BibEdit configuration.
     */
    var msg;
    switch (msgCode) {
    case -1:
        msg = 'Search term did not match any records.';
        break;
    case 0:
        msg = 'A server error has occurred. Please contact your system ' +
            'administrator.<br />';
        break;
    case 4:
        msg = 'Your modifications have now been submitted. ' +
              'They will be processed as soon as the task queue is empty.<br />';

        if (typeof args !== 'undefined') {
            if (typeof args[0] !== "undefined") {
                msg += 'Changes will be visible in ' + '<a href="' + gSITE_URL + '/record/' +
                    args[0] + '" target="_blank">' + gSITE_URL + '/record/' + args[0] + "</a><br />";
            }
            if (typeof args[1] !== 'undefined') {
                msg += '<br /><strong>The conference cnum is ' + args[1] + '</strong>';
            }
        }
        break;
    case 10:
        msg = 'The record will be deleted as soon as the task queue is empty.';
        break;
    case 101:
        msg = 'Could not access record. Permission denied.';
        break;
    case 102:
        msg = 'This record does not exist. Please try another record ID.';
        break;
    case 103:
        msg = 'The record is marked as deleted. It is possible to ' +
            'browse the history on the left menu';
        break;
    case 104:
        var name = args.name,
            email = args.email,
            locked_since = args.locked_since;
        name = (name) ? name : "";
        email = (email) ? email : "";
        locked_since = (locked_since) ? locked_since : "";
        msg = 'This record is being edited by user ' + '<strong>' + name +
              ' (' + email + ') ' + "</strong>" + 'since ' + "<strong>" +
              locked_since + "</strong>" + '. Please try again later.';
        break;
    case 105:
        msg = 'Changes to this record are currently being processed. Please ' +
            'try again in a few minutes.';
        break;
    case 106:
        msg = 'A server error has occured. You may have lost your changes to ' +
            'this record.<br />' + 'Error code: <b>' + msgCode +
            '</b> (missing cache file)';
        break;
    case 107:
        msg = 'It appears that you have opened this record in another editor, ' +
            'perhaps in a different window or on a different computer. ' +
            'A record can only be edited in one place at the time.<br /><br />' +
            'Do you want to ' +
            '<b><a href="#"id="lnkGetRecord">reopen the record</a></b> here? ';
        break;
    case 108:
        msg = 'Could not find record template file. Please notify your ' +
            'system administrator.';
        break;
    case 109:
        msg = 'The record template file is invalid. Please notify your ' +
            'system administrator';
        break;
    case 110:
        msg = 'The record contains invalid content. Remove the invalid ' +
            'content and resubmit the record.<br />' +
            'Errors: <b>' + args[0] + '</b><br /><br />';
        break;
    case 111:
        msg = 'A server error has occurred. Try reopening the record. ' +
            'If the problem persists, please contact your system ' +
            'administrator.<br />';
        break;
    case 113:
        msg = 'An error ocurred during the upload simulation: <br /><br />' +
            args[0] + '<br />';
        break;
    case 115:
        msg = 'An error ocurred while parsing the textmarc content: <br /><br />' +
            'Line: ' + args[0] + '<br /><br />' +
            '<strong>' + args[1] + '</strong>' + '<br /><br />' +
            args[2] + '<br />';
        break;
    default:
        if ( args[0] ) {
            msg = args[0];
        }
        else {
            msg = 'Result code: <strong>' + msgCode + '</strong>';
        }
    }
    if (!keepContent) {
        clearWarnings();
        $('#bibEditContentTable').empty();
        $('#bibEditMessage').html('<div class="warningMsg">' + msg +
                                       '</div>').slideDown('slow');
    } else {
        $('#bibEditMessage').html('<div class="warningMsg">' + msg +
                                  '</div>').slideDown('slow');
    }
}


function displayNewRecordScreen() {
  /*
   * Display options for creating a new record: An empty record or a template
   * selected from a list of templates.
   */
  var msg = '<div style="margin-top:25px">Create a new record selecting one of the options below:</div>';
  msg += '<ul><li style="padding-bottom: 20px;">' +
    '<a href="#" id="lnkNewEmptyRecord"><b>Empty record</b></a></li>' +
    '<li style="padding-bottom: 10px;">Use record template:' +
    '<table>';
  var templatesCount = gRECORD_TEMPLATES.length;
  if (!templatesCount)
    msg += '<tr><td style="padding-left: 10px;">No record templates found' +
      '</td></tr>';
  else{
    for (var i=0, n=templatesCount; i<n; i++)
      msg += '<tr style="border-width: 1px;">' +
  '<td style="padding-left: 10px; padding-right: 10px;">' +
  '<a href="#" id="lnkNewTemplateRecord_' + i + '"><b>' +
  gRECORD_TEMPLATES[i][1] + '</b></a></td>' +
  '<td style="padding-left: 10px; padding-right: 10px;">' +
  '<td>' + gRECORD_TEMPLATES[i][2] + '</td></tr>';
  }
  msg += '</table></li>';
  //Create another list for data imported from other sources (e.g. crossref)
  msg += '<li style="padding-bottom: 10px;">Import data from:' +
    '<table><tr style="border-width: 1px;">' +
    '<td style="padding-left: 10px; padding-right: 10px;">' +
    '<a href="#" id="lnkNewTemplateRecordImport_crossref"><b>Crossref</b></a></td>' +
    '<td style="padding-left: 10px; padding-right: 10px;">' +
    '<td><input id="doi_crossref" style="width:200px" type="text" placeholder="Input the DOI of the publication" /><div style="display:inline;" id="doi_crossref_help"></div></td></tr>' +
    '</table></li>';
  $('#bibEditContentTable').html(msg);
}


function displayCacheOutdatedScreen(requestType) {
    /*
     * Display options to resolve the outdated cache scenario (DB record updated
     * during editing). Options differ depending on wether the situation was
     * discovered when fetching or when submitting the record.
     */
    $('#bibEditMessage').html('');
    var recordURL = gSITE_URL + '/' + gSITE_RECORD + '/' + gRecID + '/';
    var viewMARCURL = recordURL + '?of=hm';
    var viewMARCXMLURL = recordURL + '?of=xm';
    var msg = '';
    if (requestType == 'submit') {
        msg = '<div class="warningMsg">' +
            'Someone has changed this record while you were editing. ' +
            'You can:<br /><ul>' + '<li>View (<b><a href="' + recordURL +
                '" target="_blank">HTML</a></b>,' + ' <b><a href="' +
                viewMARCURL + '" target="_blank">MARC</a></b>,' +
                '<b><a href="' + viewMARCXMLURL +
                '" target="_blank">MARCXML</a></b>' +
                ') the latest version</li>' +
            '<li><a href="#" id="lnkMergeCache"><b>Merge</b></a> your changes ' +
            'with the latest version by using the merge interface</li>' +
            '<li><a href="#" id="lnkForceSubmit"><b>Force your changes</b></a> ' +
            '(<b>Warning: </b>overwrites the latest version)</li>' +
            '<li><a href="#" id="lnkDiscardChanges"><b>Discard your changes</b></a> ' +
            '(keep the latest version)</li>' + '</ul></div>';
    }
    else if (requestType == 'getRecord') {
        msg = '<div class="warningMsg">' +
            'You have unsubmitted changes to this record, but someone has ' +
            'changed the record while you were editing. You can:<br /><ul>' +
            '<li>View (<b><a href="' + recordURL +
                '" target="_blank">HTML</a></b>,' + ' <b><a href="' +
                viewMARCURL + '" target="_blank">MARC</a></b>,' +
                ' <b><a href="' + viewMARCXMLURL +
                '" target="_blank">MARCXML</a></b>' +
                ') the latest version</li>' +
            '<li><a href="#" id="lnkMergeCache"><b>Merge</b></a> your changes ' +
                'with the latest version by using the merge interface' +
            '</li>' +
            '<li><a href="#" id="lnkDiscardChanges"><b>Get the latest version' +
                '</b></a> (<b>Warning: </b>discards your changes)' +
            '</li>' +
            '<li>Keep editing. When submitting you will be offered to overwrite ' +
                'the latest version. Click <a href="#" id="lnkRemoveMsg">here' +
                '</a> to remove this message.' +
            '</li>' +
            '</ul></div>';
    }

    $('#bibEditMessage').html(msg).slideDown("slow");
}

function displayAlert(msgType, args) {
    /*
     * Display pop-up of type alert or confirm.
     * args can be an array with additional arguments.
     */
    var msg;
    var popUpType = 'alert';
    switch (msgType) {
    case 'confirmClone':
        msg = 'Clone this record?\n\n';
        popUpType = 'confirm';
        break;
    case 'confirmSubmit':
        msg = 'Submit your changes to this record?\n\n';
        popUpType = 'confirm';
        break;
    case 'confirmRevert':
        msg = 'Are you sure, you want to revert to this record revision?\n\n';
        popUpType = 'confirm';
        break;
    case 'confirmCancel':
        msg = 'You have unsubmitted changes to this record.\n\n' +
            'Discard your changes?';
        popUpType = 'confirm';
        break;
    case 'confirmDeleteRecord':
        msg = 'Really delete this record?\n\n';
        popUpType = 'confirm';
        break;
    case 'confirmInvalidOrEmptyInput':
        msg = 'WARNING: Some subfields contain invalid MARC or are empty. \n' +
            'Click Cancel to go back and correct. \n' +
            'Click OK to ignore and continue (only valid subfields will be saved).';
        popUpType = 'confirm';
        break;
    case 'confirmLeavingChangedRecord':
        msg = '******************** WARNING ********************\n' +
            '                  You have unsubmitted changes.\n\n' +
            'You may:\n' +
            ' * Submit (to save your changes permanently)\n      or\n' +
            ' * Cancel (to discard your changes)\n      or\n' +
            ' * Leave (your changes are saved)\n';
        popUpType = 'confirm';
        break;
    case 'alertCriticalInput':
        msg = 'ERROR: Your input had critical errors. Please go back and ' +
            'correct any fields with invalid MARC (red border) or fields that ' +
            'should not be empty.';
        break;
    case 'alertAddProtectedField':
        msg = 'ERROR: Cannot add protected field ' + args[0] + '.';
        break;
    case 'alertAddProtectedSubfield':
        msg = 'ERROR: Cannot add protected subfield ' + args[0] + '.';
        break;
    case 'alertEmptySubfieldsList':
        msg = "The field has to contain at least one non-empty subfield.";
        break;
    case 'alertDeleteProtectedField':
        msg = 'ERROR: Cannot delete protected field ' + args[0] + '.';
        break;
    case 'alertDeleteHPAffectedField':
        msg = 'Field ' + args[0] + ' cannot be deleted.\n' +
        'It contains subfield changed in Holding Pen\'s record and an action should be taken first';
        break;
    case 'errorPhysicalCopiesExist':
        msg = "ERROR: Cannot delete record when physical copies exist. " +
            "First remove the copies in the BibCirculation module and then try again";
        break;
    case 'confirmDeleteManagedDOIs':
        msg = '******************** WARNING ********************\n' +
            'You are about to delete a record that contain DOI(s) managed by the system:\n' +
	    args.join('\n') + '\n' +
            'Are you really sure you want to delete this record?'
        popUpType = 'confirm';
        break;
    case 'alertDeleteManagedDOIs':
        msg = 'ERROR: Cannot delete a record that contains DOI(s) managed by the system:\n' +
	    args.join('\n');
        break;
    case 'confirmDeleteManagedDOIsField':
        msg = '******************** WARNING ********************\n' +
            'You are about to delete a field that contain DOI(s) managed by the system:\n' +
	    args.join('\n') + '\n' +
            'Are you really sure you want to delete this field?'
        popUpType = 'confirm';
        break;
    case 'alertDeleteManagedDOIsField':
        msg = 'ERROR: Cannot delete field(s) that contain DOI(s) managed by the system:\n' +
	    args.join('\n');
        break;
    default:
        msg = msgType;
    }
    if (popUpType == 'confirm') return confirm(msg);
    else alert(msg);
}

function notImplemented(event) {
    /*
     * Handle unimplemented function.
     */
    alert('Sorry, this function is not implemented yet!');
    event.preventDefault();
}

function button(value, id, _class, attrs) {
    /*
     * Create a button tag with specified attributes.
     */
    value = (value != undefined) ? value : '';
    id = id ? 'id="' + id + '" ' : '';
    _class = _class ? 'class="' + _class + '" ' : '';
    var strAttrs = '';
    for (var attr in attrs) {
        strAttrs += attr + '="' + attrs[attr] + '" ';
    }
    return '<button ' + id + _class + strAttrs + '>' + value + '</button>';
}

function img(src, id, _class, attrs) {
    /*
     * Create an image tag with specified attributes.
     */
    src = 'src="' + src + '" ';
    id = id ? 'id="' + id + '" ' : '';
    _class = _class ? 'class="' + _class + '" ' : '';
    var strAttrs = '';
    for (var attr in attrs) {
        strAttrs += attr + '="' + attrs[attr] + '" ';
    }
    return '<img ' + src + id + _class + strAttrs + '/>';
}

function input(type, id, _class, attrs, defvalue) {
    /*
     * Create an input tag with specified attributes.
     */
    type = 'type="' + type + '" ';
    id = id ? 'id="' + id + '" ' : '';
    _class = _class ? 'class="' + _class + '" ' : '';
    var strAttrs = '';
    for (var attr in attrs) {
        strAttrs += attr + '="' + attrs[attr] + '" ';
    }
    myval = '';
    if ((defvalue != null) && (defvalue != "")) {
        myval = ' value="' + defvalue + '" ';
    }
    return '<input ' + type + id + _class + strAttrs + myval + '/>';
}

function select(id, options, selectedOption) {
    /*
     * Create the select input -> it has a different structure than most of the
     * inputs
     * options: a list of options appearing under the same id. Each option is a
     *          dictionary describing the value associated and the description
     *          a sample entry of the options :
     *          {value: "1", description: "option1"}
     */

    optionsHTML = "";

    for (optionNr in options) {
        optionsHTML += "<option value=\"" + options[optionNr].value + "\"";
        if (selectedOption == options[optionNr].value) {
            optionsHTML += " selected";
        }
        optionsHTML += ">" + options[optionNr].description + "</option>";
    }
    return "<select id=\"" + id + "\">" + optionsHTML + "</select>";

}

function getRevisionDate(revisionTs) {
    var result = {};
    result.year = revisionTs.substr(0, 4);
    result.month = revisionTs.substr(4, 2);
    result.day = revisionTs.substr(6, 2);
    result.hour = revisionTs.substr(8, 2);
    result.minute = revisionTs.substr(10, 2);
    result.second = revisionTs.substr(12, 2);
    return result;
}

function formatDateTime(dt) {
    return dt.year + '.' + dt.month + '.' + dt.day + ' ' + dt.hour + ':' +
        dt.minute + ':' + dt.second;
}

function displayRevisionHistoryEntry(recId, revisionId) {
    var entryClass = (revisionId == gRecRev) ? "bibEditRevHistorySelectedEntry" : "bibEditRevHistoryEntry";
    var timeString = formatDateTime(getRevisionDate(revisionId));

    /* Define icons per row */
    var mergeImgId = 'imgMergeWithNewest_' + revisionId;
    var compareImgId = 'imgCompareWithCurrent_' + revisionId;
    var revertImgId = 'imgRevert_' + revisionId;
    var checkImgId = 'imgCheck_' + revisionId;
    var checkImg = img('/img/eye.png', checkImgId, 'bibEditRevHistoryLinkImg', {
        'title': 'Show record revision on Editor'
    })

    var mergeUrl = '/' + gSITE_RECORD + '/merge#recid1=' + recId + '&recid2=' +
                    recId + '.' + revisionId;
    var mergeWithNewestControl = '<a href="' + mergeUrl +
        '" title="Merge with the newest revision" class="bibEditRevHistoryLink">' +
        img('/img/merge-small.png', mergeImgId, 'bibEditRevHistoryLinkImg') +
        '</a>';

    var compareWithCurrentControl = '<a href="#" title="Compare with currently \
        viewed version" class="bibEditRevHistoryLink">' +
        img('/img/compare.png', compareImgId, 'bibEditRevHistoryLinkImg') +
        '</a>';

    var revertToRevisionControl = '<a href="#" title="Revert to this revision" \
        class="bibEditRevHistoryLink">' +
        img('/img/replace.png', revertImgId, 'bibEditRevHistoryLinkImg') +
        '</a>';

    var resultHTML = '<div class="' + entryClass + '">\n' +
        '<div class="bibEditRevHistoryEntryContent" id="bibEditRevHistoryEntry_' +
        revisionId + '">' + checkImg + timeString +
        '</div><div class="bibEditRevHistoryEntryControls">' +
        '<div>' + mergeWithNewestControl +
        compareWithCurrentControl + revertToRevisionControl +
        "</div></div></div>\n";

    return {
        "HTML": resultHTML,
        "compareImgId": compareImgId,
        "revertImgId": revertImgId
    };
}


function escapeHTML(value) {
    /*
     * Replace special characters '&', '<' and '>' with HTML-safe sequences.
     * This functions is called on content before displaying it.
     */
    value = value.replace(/&/g, '&amp;'); // Must be done first!
    value = value.replace(/</g, '&lt;');
    value = value.replace(/>/g, '&gt;');
    return value;
}

/*
 * ************ Functions related to Template interface ****************
 */

function createTemplateList() {
    /*
     * Display list of templates available with their description and links to
     * edit them.
     */
    var msg = '';
    var templatesCount = gRECORD_TEMPLATES.length;
    if (!templatesCount) msg += '<tr><td style="padding-left: 10px;">No record templates found' +
                                '</td></tr>';
    else {
        for (var i = 0, n = templatesCount; i < n; i++) {
            msg += '<tr style="border-width: 1px;">' +
                '<td style="padding-left: 10px; padding-right: 10px;">' +
                '<a href="#" id="lnkEditTemplateRecord_' + i +
                '" title="Click to edit"><b>' + gRECORD_TEMPLATES[i][1] +
                '</b></a></td>' +
                '<td style="padding-left: 10px; padding-right: 10px;">' +
                '<td>' + gRECORD_TEMPLATES[i][2] +
                '</td> <td>&nbsp;&nbsp;&nbsp;<i>Last modified (' +
                gRECORD_TEMPLATES[i][3] + ')</i></td></tr><br />';
        }
    }
    msg += '</table></li>';
    $('#bibEditTemplateList').html(msg);
}

/*
 * **************************** Functions related to jquery UI dialog ****************************************
 */

function createDialog(title, content, height, width, loading, modal) {
    /* Creates a jQuery UI dialog
     *
     * title: string, title displayed on top of the dialog
     * LoadingText: string, text displayed above the loading bar
     * heigth: int, height of the dialog
     * width: int, width of the dialog
     *
     */
    var dialog = {
        dialogDiv: $('<div>'),
        contentParagraph: $('<p>'),
        contentSpan: $('<span>'),
        iconSpan: $('<span>')
    };
    var dialogDiv = dialog.dialogDiv;
    var contentParagraph = dialog.contentParagraph;
    var contentSpan = dialog.contentSpan;
    var iconSpan = dialog.iconSpan;
    if (loading === true) {
        contentParagraph.addClass('dialog-box-centered');
        contentSpan.html(content +
                         "<br /><br /> <img src='/img/ajax-loader.gif'>");
    } else {
        contentSpan.html(content);
    }
    dialogDiv.append(contentParagraph.append(contentSpan));
    dialogDiv.appendTo($('body'));
    dialog_options = {}
    dialog_options.title = title;
    dialog_options.resizeable = false;
    dialog_options.height = height;
    dialog_options.width = width;
    if (modal == true) {
        dialog_options.modal = true;
    }

    dialogDiv.dialog(dialog_options);

    return dialog;
}

function addContentToDialog(dialog, html_content, alertText) {
    /* Modify internal content of a jQuery UI dialog
     *
     * dialog: object containing different parts of the dialog
     * (see createDialog())
     * html_content: string, main text of the dialog
     * alertText: string, text besides the alert icon
     *
     */
    dialog.iconSpan.addClass('ui-icon').addClass('ui-icon-alert').addClass('dialog-icon');
    dialog.contentParagraph.before(dialog.iconSpan);
    dialog.contentParagraph.removeClass('dialog-box-centered');
    dialog.contentSpan.html("<strong>" + alertText + "</strong>\n\
                    <br /><br />" + html_content);
}

function openCenteredPopup(pageURL, title, w, h) { /* Opens a centered popup */
    var targetWindow;
    if (w === undefined || h === undefined) {
        targetWindow = window.open(pageURL, title, 'resizeable,scrollbars');
    } else {
        var left = (screen.width / 2) - (w / 2);
        var top = (screen.height / 2) - (h / 2);
        targetWindow = window.open(pageURL, title, 'width=' + w +
            ',height=' + h + ',top=' + top + ',left=' + left +
            ',resizeable,scrollbars');
    }
    return targetWindow;
}

function clearWarnings() {
    /* Removes all messages present on the top warning area */
    $('#bibEditMessage').empty();
}
