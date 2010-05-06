/*
 * This file is part of CDS Invenio.
 * Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 2009 CERN.
 *
 * CDS Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * CDS Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.  See1 the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/*
 * This is the main BibEdit Javascript.
 */

/* ************************* Table of contents ********************************
 *
 * 1. Global variables
 *
 * 2. Initialization
 *   - $()
 *   - initJeditable
 *   - initMisc
 *
 * 3. Ajax
 *   - initAjax
 *   - createReq
 *   - onAjaxError
 *   - onAjaxSuccess
 *
 * 4. Hash management
 *   - initStateFromHash
 *   - deserializeHash
 *   - changeAndSerializeHash
 *
 * 5. Data logic
 *   - getTagsSorted
 *   - getFieldPositionInTag
 *   - getPreviousTag
 *   - deleteFieldFromTag
 *   - cmpFields
 *   - fieldIsProtected
 *   - containsProtected
 *   - getMARC
 *   - getFieldTag
 *   - getSubfieldTag
 *   - validMARC
 *
 * 6. Record UI
 *   - onNewRecordClick
 *   - getRecord
 *   - onGetRecordSuccess
 *   - onSubmitClick
 *   - onCancelClick
 *   - onCloneRecordClick
 *   - onDeleteRecordClick
 *   - onMergeClick
 *   - bindNewRecordHandlers
 *   - cleanUp
 *   - positionBibEditPanel
 *
 * 7. Editor UI
 *   - colorFields
 *   - reColorFields
 *   - onMARCTagsClick
 *   - onHumanTagsClick
 *   - updateTags
 *   - onFieldBoxClick
 *   - onSubfieldBoxClick
 *   - onAddFieldClick
 *   - onAddFieldControlfieldClick
 *   - onAddFieldChange
 *   - onAddFieldSave
 *   - onAddSubfieldsClick
 *   - onAddSubfieldsChange
 *   - onAddSubfieldsSave
 *   - onDoubleClick
 *   - onContentChange
 *   - onMoveSubfieldClick
 *   - onDeleteClick
 */



/*
 * **************************** 1. Global variables ****************************
 */

// Record data
var gRecID = null;
var gRecIDLoading = null;
var gRecRev = null;
var gRecRevAuthor = null;
var gRecLatestRev = null;
var gRecord = null;
// Search results (record IDs)
var gResultSet = null;
// Current index in the result set
var gResultSetIndex = null;
// Tag format.
var gTagFormat = null;
// Has the record been modified?
var gRecordDirty = false;
// Last recorded cache modification time
var gCacheMTime = null;

// Are we navigating a set of records?
var gNavigatingRecordSet = false;

// The current hash (fragment part of the URL).
var gHash;
// The current hash deserialized to an object.
var gHashParsed;
// Hash check timer ID.
var gHashCheckTimerID;
// The previous and current state (this is not exactly the same as the state
// parameter, but an internal state control mechanism).
var gPrevState;
var gState;
// A current status
var gCurrentStatus;

// a global array of visible changes associated with a currently viewed record
// This array is cleared always when a new changes set is applied... then it is used
// for redrawing the change fields
// The index in this array is used when referring to a particular change [ like finding an appropriate box]

var gHoldingPenChanges = [];

// A global variable used to avoid multiple retrieving of the same changes stored in the Holding Pen
// this is the dictionary indexed by the HoldingPen entry identifiers and containing the javascript objects
// representing the records
// due to this mechanism, applying previously previewed changes, as well as previewing the change for the
// second time, can be made much faster
var gHoldingPenLoadedChanges = {};

// The changes that have been somehow processed and should not be displayed as already processed

var gDisabledHpEntries = {};

// is the read-only mode enabled ?
var gReadOnlyMode = false;

// revisions history
var gRecRevisionHistory = []
/*
 * **************************** 2. Initialization ******************************
 */

window.onload = function(){
  if (typeof(jQuery) == 'undefined'){
    alert('ERROR: jQuery not found!\n\n' +
    'The Record Editor requires jQuery, which does not appear to be ' +
    'installed on this server. Please alert your system ' +
    'administrator.\n\nInstructions on how to install jQuery and other ' +
    'required plug-ins can be found in CDS-Invenio\'s INSTALL file.');
    var imgError = document.createElement('img');
    imgError.setAttribute('src', '/img/circle_red.png');
    var txtError = document.createTextNode('jQuery missing');
    var cellIndicator = document.getElementById('cellIndicator');
    cellIndicator.replaceChild(imgError, cellIndicator.firstChild);
    var cellStatus = document.getElementById('cellStatus');
    cellStatus.replaceChild(txtError, cellStatus.firstChild);
  }
};

$(function(){
  /*
   * Initialize all components.
   */
  initMenu();
  initJeditable();
  initAjax();
  initMisc();
  initStateFromHash();
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
  initHotkeys();
});


function failInReadOnly(){
  /** Function checking if the current BibEdit mode is read-only. In sucha a case, a warning
    dialog is displayed and true returned.
    If bibEdit is in read/write mode, false is returned
   */
  if (gReadOnlyMode == true){
    alert("It is impossible to perform this operation in the Read/Only mode. Please switch to Read-write mode before trying again");
    return true;
  }
  else{
    return false;
  }
}

function initJeditable(){
  /* Initialize Jeditable with the Autogrow extension. Used for in-place
   * content editing.
   */
  $.editable.addInputType('autogrow', {
    element: function(settings, original){
      var textarea = $('<textarea>');
      if (settings.rows)
        textarea.attr('rows', settings.rows);
      else
        textarea.height(settings.height);
      if (settings.cols)
        textarea.attr('cols', settings.cols);
      else
        textarea.width(settings.width);
      $(this).append(textarea);
      return(textarea);
    },
    plugin: function(settings, original){
      $('textarea', this).autogrow(settings.autogrow);
    }
  });
}

function initMisc(){
  /*
   * Miscellaneous initialization operations.
   */
  // CERN allows for capital MARC indicators.
  if (gCERN_SITE){
    validMARC.reIndicator1 = /[\dA-Za-z]{1}/;
    validMARC.reIndicator2 = /[\dA-Za-z]{1}/;
  }

  // Warn user if BibEdit is being closed while a record is open.
  window.onbeforeunload = function(){
    if (gRecID && gRecordDirty)
      return '******************** WARNING ********************\n' +
  '                  You have unsubmitted changes.\n\n' +
  'You should go back to the page and click either:\n' +
  ' * Submit (to save your changes permanently)\n      or\n' +
  ' * Cancel (to discard your changes)';
  }
}


/*
 * **************************** 3. Ajax ****************************************
 */

function initAjax(){
  /*
   * Initialize Ajax.
   */
  $.ajaxSetup(
    { cache: false,
      dataType: 'json',
      error: onAjaxError,
      type: 'POST',
      url: '/record/edit/'
    }
  );
}

function createReq(data, onSuccess, asynchronous){
  /*
   * Create Ajax request.
   */
  if (asynchronous == undefined)
    asynchronous = true;
  // Include and increment transaction ID.
  var tID = createReq.transactionID++;
  createReq.transactions[tID] = data['requestType'];
  data.ID = tID;
  // Include cache modification time if we have it.
  if (gCacheMTime)
    data.cacheMTime = gCacheMTime;
  // Send the request.
  $.ajax({ data: { jsondata: JSON.stringify(data) },
           success: function(json){
                      onAjaxSuccess(json, onSuccess);
                    },
           async: asynchronous
  });
}
// Transactions data.
createReq.transactionID = 0;
createReq.transactions = [];

function onAjaxError(XHR, textStatus, errorThrown){
  /*
   * Handle Ajax request errors.
   */
  alert('Request completed with status ' + textStatus
  + '\nResult: ' + XHR.responseText
  + '\nError: ' + errorThrown);
}

function onAjaxSuccess(json, onSuccess){
  /*
   * Handle server response to Ajax requests, in particular error situations.
   * See BibEdit config for result codes.
   * If a function onSuccess is specified this will be called in the end,
   * if no error was encountered.
   */
  var resCode = json['resultCode'];
  var recID = json['recID'];
  if (resCode == 100){
    // User's session has timed out.
    gRecID = null;
    gRecIDLoading = null;
    window.location = recID ? gSITE_URL + '/record/' + recID + '/edit/'
      : gSITE_URL + '/record/edit/';
    return;
  }
  else if ($.inArray(resCode, [101, 102, 103, 104, 105, 106, 107, 108, 109])
     != -1){
    cleanUp(!gNavigatingRecordSet, null, null, true, true);
    if ($.inArray(resCode, [108, 109]) == -1)
      $('.headline').text('Record Editor: Record #' + recID);
    displayMessage(resCode);
    if (resCode == 107)
      $('#lnkGetRecord').bind('click', function(event){
        getRecord(recID);
        event.preventDefault();
      });
    updateStatus('error', gRESULT_CODES[resCode]);
  }
  else if (resCode == 110){
    displayMessage(resCode, true, [json['errors'].toString()]);
    $(document).scrollTop(0);
    updateStatus('error', gRESULT_CODES[resCode]);
  }
  else{
    var cacheOutdated = json['cacheOutdated'];
    var requestType = createReq.transactions[json['ID']];
    if (cacheOutdated && requestType == 'submit'){
      // User wants to submit, but cache is outdated. Outdated means that the
      // DB version of the record has changed after the cache was created.
      displayCacheOutdatedScreen(requestType);
      $('#lnkMergeCache').bind('click', onMergeClick);
      $('#lnkForceSubmit').bind('click', function(event){
  onSubmitClick.force = true;
  onSubmitClick();
  event.preventDefault();
      });
      $('#lnkDiscardChanges').bind('click', function(event){
  onCancelClick();
  event.preventDefault();
      });
      updateStatus('error', 'Error: Record cache is outdated');
    }
    else{
      if (requestType != 'getRecord'){
  // On getRecord requests the below actions will be performed in
  // onGetRecordSuccess (after cleanup).
  var cacheMTime = json['cacheMTime'];
  if (cacheMTime)
    // Store new cache modification time.
    gCacheMTime = cacheMTime;
  var cacheDirty = json['cacheDirty'];
  if (cacheDirty){
    // Cache is dirty. Enable submit button.
    gRecordDirty = cacheDirty;
    $('#btnSubmit').removeAttr('disabled');
    $('#btnSubmit').css('background-color', 'lightgreen');
  }
      }
      if (onSuccess)
  // No critical errors; call onSuccess function.
  onSuccess(json);
    }
  }
}

function resetBibeditState(){
  /** A function clearing the state of the bibEdit (all the panels content)
  */
  gHoldingPenLoadedChanges = {};
  gHoldingPenChanges = [];
  gDisabledHpEntries = {};
  gReadOnlyMode = false;
  gRecRevisionHistory = [];

  updateRevisionsHistory();
  updateInterfaceAccordingToMode();
  updateRevisionsHistory();
  holdingPenPanelRemoveEntries();
}

/*
 * **************************** 4. Hash management *****************************
 */

function initStateFromHash(){
  /*
   * Initialize or update page state from hash.
   * Any program functions changing the hash should use changeAndSerializeHash()
   * which circumvents this function, meaning this function should only run on
   * page load and when browser navigation buttons (ie. Back and Forward) are
   * clicked. Any invalid hashes entered by the user will be ignored.
   */
  if (window.location.hash == gHash)
    // Hash is the same as last time we checked, do nothing.
    return;

  gHash = window.location.hash;
  gHashParsed = deserializeHash(gHash);
  gPrevState = gState;
  var tmpState = gHashParsed.state;
  var tmpRecID = gHashParsed.recid;
  var tmpRecRev = gHashParsed.recrev;
  var tmpReadOnlyMode = gHashParsed.romode;

  // Find out which internal state the new hash leaves us with
  if (tmpState && tmpRecID){
    // We have both state and record ID.
    if ($.inArray(tmpState, ['edit', 'submit', 'cancel', 'deleteRecord']) != -1)
  gState = tmpState;
    else
      // Invalid state, fail...
      return;
  }
  else if (tmpState){
    // We only have state.
    if (tmpState == 'edit')
      gState = 'startPage';
    else if (tmpState == 'newRecord')
      gState = 'newRecord';
    else
      // Invalid state, fail... (all states but 'edit' and 'newRecord' are
      // illegal without record ID).
      return;
  }
  else
    // Invalid hash, fail...
    return;

  if (gState != gPrevState
    || (gState == 'edit' && parseInt(tmpRecID) != gRecID) || // different record number
    (tmpRecRev != undefined && tmpRecRev != gRecRev) // different revision
    || (tmpRecRev == undefined && gRecRev != gRecLatestRev) // latest revision requested but another open
    || (tmpReadOnlyMode != gReadOnlyMode)){ // switched between read-only and read-write modes

    // We have an actual and legal change of state. Clean up and update the
    // page.
    updateStatus('updating');
    if (gRecID && !gRecordDirty && !tmpReadOnlyMode)
      // If the record is unchanged, delete the cache.
      createReq({recID: gRecID, requestType: 'deleteRecordCache'});
    switch (gState){
      case 'startPage':
        cleanUp(true, '', 'recID', true, true);
        updateStatus('ready');
        break;
      case 'edit':
        var recID = parseInt(tmpRecID);
        if (isNaN(recID)){
          // Invalid record ID.
          cleanUp(true, tmpRecID, 'recID', true);
          $('.headline').text('Record Editor: Record #' + tmpRecID);
          displayMessage(102);
          updateStatus('error', gRESULT_CODES[102]);
        }
        else{
          cleanUp(true, recID, 'recID');
          gReadOnlyMode = tmpReadOnlyMode;
            if (tmpRecRev != undefined && tmpRecRev != 0){
              getRecord(recID, tmpRecRev);
            } else {
              getRecord(recID);
            }
        }
      break;
    case 'newRecord':
      cleanUp(true, '', null, null, true);
      $('.headline').text('Record Editor: Create new record');
      displayNewRecordScreen();
      bindNewRecordHandlers();
      updateStatus('ready');
      break;
    case 'submit':
      cleanUp(true, '', null, true);
      $('.headline').text('Record Editor: Record #' + tmpRecID);
      displayMessage(4);
      updateStatus('ready');
      break;
    case 'cancel':
      cleanUp(true, '', null, true, true);
      updateStatus('ready');
      break;
    case 'deleteRecord':
      cleanUp(true, '', null, true);
      $('.headline').text('Record Editor: Record #' + tmpRecID);
      displayMessage(6);
      updateStatus('ready');
        break;
    }
  }
  else
  // What changed was not of interest, continue as if nothing happened.
    return;
}

function deserializeHash(aHash){
  /*
   * Deserializes a string (given as parameter or taken from the window object)
   * into the hash object.
   */
  if (aHash == undefined){
    aHash = window.location.hash;
  }
  var hash = {};
  var args = aHash.slice(1).split('&');
  var tmpArray;
  for (var i=0, n=args.length; i<n; i++){
    tmpArray = args[i].split('=');
    if (tmpArray.length == 2)
      hash[tmpArray[0]] = tmpArray[1];
  }
  return hash;
}

function changeAndSerializeHash(updateData){
  /*
   * Change the hash object to use the data from the object given as parameter.
   * Then update the hash accordingly, WITHOUT invoking initStateFromHash().
   */
  clearTimeout(gHashCheckTimerID);
  gHashParsed = {};
  for (var key in updateData){
    gHashParsed[key.toString()] = updateData[key].toString();
  }
  gHash = '#';
  for (key in gHashParsed){
    gHash += key + '=' + gHashParsed[key] + '&';
  }
  gHash = gHash.slice(0, -1);
  gState = gHashParsed.state;
  window.location.hash = gHash;
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
}


/*
 * **************************** 5. Data logic **********************************
 */

function getTagsSorted(){
  /*
   * Return field tags in sorted order.
   */
  var tags = [];
  for (var tag in gRecord){
    tags.push(tag);
  }
  return tags.sort();
}

function getFieldPositionInTag(tag, field){
  /*
   * Determine the local (in tag) position of a new field.
   */
  var fields = gRecord[tag];
  if (fields){
    var fieldLength = fields.length, i = 0;
    while (i < fieldLength && cmpFields(field, fields[i]) != -1)
      i++;
    return i;
  }
  else
    return 0;
}

function getPreviousTag(tag){
  /*
   * Determine the previous tag in the record (if the given tag is the first
   * tag, 0 will be returned).
   */
  var tags = getTagsSorted();
  var tagPos = $.inArray(tag, tags);
  if (tagPos == -1){
    tags.push(tag);
    tags.sort();
    tagPos = $.inArray(tag, tags);
  }
  if (tagPos > 0)
    return tags[tagPos-1];
  return 0;
}

function deleteFieldFromTag(tag, fieldPosition){
  /*
   * Delete a specified field.
   */
  var field = gRecord[tag][fieldPosition];
  var fields = gRecord[tag];
  fields.splice($.inArray(field, fields), 1);
  // If last field, delete tag.
  if (fields.length == 0){
    delete gRecord[tag];
  }
}

function cmpFields(field1, field2){
  /*
   * Compare fields by indicators (tag assumed equal).
   */
  if (field1[1].toLowerCase() > field2[1].toLowerCase())
    return 1;
  else if (field1[1].toLowerCase() < field2[1].toLowerCase())
    return -1;
  else if (field1[2].toLowerCase() > field2[2].toLowerCase())
    return 1;
  else if (field1[2].toLowerCase() < field2[2].toLowerCase())
    return -1;
  return 0;
}

function insertFieldToRecord(record, fieldId, ind1, ind2, subFields){
  /**Inserting a new field on the client side and returning the position of the newly created field*/
  newField = [subFields, ind1, ind2, '', 0];
  if (record[fieldId] == undefined){
    record[fieldId] = [newField]
    return 0;
  } else {
    record[fieldId].push(newField);
    return (record[fieldId].length-1);
  }
}

function transformRecord(record){
  /**Transforming a bibrecord to a form that is easier to compare that is a dictionary
   * field identifier -> field indices -> fields list -> [subfields list, position in the record]
   *
   * The data is enriched with the positions inside the record in a following manner:
   * each field consists of:
   * */
  result = {};
  for (fieldId in record){
    result[fieldId] = {}
    indicesList = []; // a list of all the indices ... utilised later when determining the positions
    for (fieldIndex in record[fieldId]){

      indices =  "";
      if (record[fieldId][fieldIndex][1] == ' '){
        indices += "_";
      }else{
        indices += record[fieldId][fieldIndex][1]
      }

      if (record[fieldId][fieldIndex][2] == ' '){
        indices += "_";
      }else{
        indices += record[fieldId][fieldIndex][2]
      }

      if (result[fieldId][indices] == undefined){
        result[fieldId][indices] = []; // a future list of fields sharing the same indice
        indicesList.push(indices);
      }
      result[fieldId][indices].push([record[fieldId][fieldIndex][0], 0]);
    }

    // now calculating the positions within a field identifier ( utilised on the website )

    position = 0;

    indices = indicesList.sort();
    for (i in indices){
      for (fieldInd in result[fieldId][indices[i]]){
        result[fieldId][indices[i]][fieldInd][1] = position;
        position ++;
      }
    }
  }

    return result;
}

function filterChanges(changeset){
  /*Filtering the changes list -> removing the changes related to the fields
   * that should never be changed */
  unchangableTags = {"001" : true}; // a dictionary of the fields that should not be modified
  result = [];
  for (changeInd in changeset){
    change = changeset[changeInd];
    if ((change.tag == undefined) || (!(change.tag in unchangableTags))){
      result.push(change);
    }
  }
  return result;
}

///// Functions generating easy to display changes list

function compareFields(fieldId, indicators, fieldPos, field1, field2){
  result = [];
  for (sfPos in field2){
    if (field1[sfPos] == undefined){
      //  adding the subfield at the end of the record can be treated in a more graceful manner
      result.push(
          {"change_type" : "subfield_added",
           "tag" : fieldId,
           "indicators" : indicators,
           "field_position" : fieldPos,
           "subfield_code" : field2[sfPos][0],
           "subfield_content" : field2[sfPos][1]});
    }
    else
    {
      // the subfield exists in both the records
      if (field1[sfPos][0] != field2[sfPos][0]){
      //  a structural change ... we replace the entire field
        return [{"change_type" : "field_changed",
           "tag" : fieldId,
           "indicators" : indicators,
           "field_position" : fieldPos,
           "field_content" : field2}];
      } else
      {
        if (field1[sfPos][1] != field2[sfPos][1]){
          result.push({"change_type" : "subfield_changed",
            "tag" : fieldId,
            "indicators" : indicators,
            "field_position" : fieldPos,
            "subfield_position" : sfPos,
            "subfield_code" : field2[sfPos][0],
            "subfield_content" : field2[sfPos][1]});

        }
      }
    }
  }

  for (sfPos in field1){
    if (field2[sfPos] == undefined){
      result.push({ "change_type" : "subfield_removed",
                "tag" : fieldId,
                "indicators" : indicators,
                "field_position" : fieldPos,
                "subfield_position" : sfPos});
        // removing the subfields from the end can be treated in a more graceful manner
    }
  }

  return result;
}

function compareIndicators(fieldId, indicators, fields1, fields2){
   /*a helper function allowing to compare inside one indicator
    * excluded from compareRecords for the code clarity reason*/
  result = []
  for (fieldPos in fields2){
    if (fields1[fieldPos] == undefined){
      result.push({ "change_type" : "field_added",
                  "tag" : fieldId,
                  "indicators" : indicators,
                  "field_content" : fields2[fieldPos][0]});
    } else { // comparing the content of the subfields
      result = result.concat(compareFields(fieldId, indicators, fields1[fieldPos][1], fields1[fieldPos][0], fields2[fieldPos][0]));
    }
  }

  for (fieldPos in fields1){
    if (fields2[fieldPos] == undefined){
      fieldPosition = fields1[fieldPos][1];
      result.push({"change_type" : "field_removed",
             "tag" : fieldId,
             "indicators" : indicators,
             "field_position" : fieldPosition});
    }
  }
  return result;
}

function compareRecords(record1, record2){
  /*Compares two bibrecords, producing a list of atom changes that can be displayed
   * to the user if for example applying the Holding Pen change*/
   // 1) This is more convenient to have a different structure of the storage
  r1 = transformRecord(record1);
  r2 = transformRecord(record2);
  result = [];

  for (fieldId in r2){
    if (r1[fieldId] == undefined){
      for (indicators in r2[fieldId]){
        for (field in r2[fieldId][indicators]){
          result.push({ "change_type" : "field_added",
                        "tag" : fieldId,
                        "indicators" : indicators,
                        "field_content" : r2[fieldId][indicators][field][0]});


        }
      }
    }
    else
    {
      for (indicators in r2[fieldId]){
        if (r1[fieldId][indicators] == undefined){
          for (field in r2[fieldId][indicators]){
            result.push({"change_type" : "field_added",
                         "tag" : fieldId,
                         "indicators" : indicators,
                         "field_content" : r2[fieldId][indicators][field][0]});


          }
        }
        else{
          result = result.concat(compareIndicators(fieldId, indicators,
              r1[fieldId][indicators], r2[fieldId][indicators]));
        }
      }

      for (indicators in r1[fieldId]){
        if (r2[fieldId][indicators] == undefined){
          for (fieldInd in r1[fieldId][indicators]){
            fieldPosition = r1[fieldId][indicators][fieldInd][1];
            result.push({ "change_type" : "field_removed",
                 "tag" : fieldId,
                 "field_position" : fieldPosition});
          }

        }
      }

    }
  }

  for (fieldId in r1){
    if (r2[fieldId] == undefined){
      for (indicators in r1[fieldId]){
        for (field in r1[fieldId][indicators])
        {
          // field position has to be calculated here !!!
          fieldPosition = r1[fieldId][indicators][field][1]; // field position inside the mark
          result.push({"change_type" : "field_removed",
                       "tag" : fieldId,
                       "field_position" : fieldPosition});

        }
      }
    }
  }
  return result;
}

function fieldIsProtected(MARC){
  /*
   * Determine if a MARC field is protected or part of a protected group of
   * fields.
   */
  do{
    var i = MARC.length - 1;
    if ($.inArray(MARC, gPROTECTED_FIELDS) != -1)
      return true;
    MARC = MARC.substr(0, i);
    i--;
  }
  while (i >= 1)
  return false;
}

function containsProtectedField(fieldData){
  /*
   * Determine if a field data structure contains protected elements (useful
   * when checking if a deletion command is valid).
   * The data structure must be an object with the following levels
   * - Tag
   *   - Field position
   *     - Subfield index
   */
  var fieldPositions, subfieldIndexes, MARC;
  for (var tag in fieldData){
    fieldPositions = fieldData[tag];
    for (var fieldPosition in fieldPositions){
      subfieldIndexes = fieldPositions[fieldPosition];
      if (subfieldIndexes.length == 0){
  MARC = getMARC(tag, fieldPosition);
  if (fieldIsProtected(MARC))
    return MARC;
  }
      else{
  for (var i=0, n=subfieldIndexes.length; i<n; i++){
    MARC = getMARC(tag, fieldPosition, subfieldIndexes[i]);
    if (fieldIsProtected(MARC))
      return MARC;
  }
      }
    }
  }
  return false;
}

function getMARC(tag, fieldPosition, subfieldIndex){
  /*
   * Return the MARC representation of a field or a subfield.
   */
  var field = gRecord[tag][fieldPosition];
  var ind1, ind2;
  if (validMARC.reControlTag.test(tag))
    ind1 = '', ind2 = '';
  else{
    ind1 = (field[1] == ' ' || !field[1]) ? '_' : field[1];
    ind2 = (field[2] == ' ' || !field[2]) ? '_' : field[2];
  }
  if (subfieldIndex == undefined)
    return tag + ind1 + ind2;
  else
    return tag + ind1 + ind2 + field[0][subfieldIndex][0];
}

function getFieldTag(MARC){
  /*
   * Get the tag name of a field in format as specified by gTagFormat.
   */
  MARC = MARC.substr(0, 5);
  if (gTagFormat == 'human'){
    var tagName = gTAG_NAMES[MARC];
    if (tagName != undefined)
      // Direct hit. Return it.
      return tagName;
    else{
      // Start looking for wildcard hits.
      if (MARC.length == 3){
  // Controlfield
  tagName = gTAG_NAMES[MARC.substr(0, 2) + '%'];
  if (tagName != undefined && tagName != MARC + 'x')
    return tagName;
      }
      else{
  // Regular field, try finding wildcard hit by shortening expression
  // gradually. Ignores wildcards which gives values like '27x'.
  var term = MARC + '%', i = 5;
  do{
    tagName = gTAG_NAMES[term];
    if (tagName != undefined){
      if (tagName != MARC.substr(0, i) + 'x')
        return tagName;
      break;
    }
    i--;
    term = MARC.substr(0, i) + '%';
  }
  while (i >= 3)
      }
    }
  }
  return MARC;
}

function getSubfieldTag(MARC){
  /*
   * Get the tag name of a subfield in format as specified by gTagFormat.
   */
  if (gTagFormat == 'human'){
    var subfieldName = gTAG_NAMES[MARC];
      if (subfieldName != undefined)
  return subfieldName;
  }
  return '$$' + MARC.charAt(5);
}

function validMARC(datatype, value){
  /*
   * Validate a value of given datatype according to the MARC standard. The
   * value should be restricted/extended to it's expected size before being
   * passed to this function.
   * Datatype can be 'ControlTag', 'Tag', 'Indicator' or 'SubfieldCode'.
   * Returns a boolean.
   */
  return eval('validMARC.re' + datatype + '.test(value)');
}
// MARC validation REs
validMARC.reControlTag = /00[1-9A-Za-z]{1}/;
validMARC.reTag = /(0([1-9A-Z][0-9A-Z])|0([1-9a-z][0-9a-z]))|(([1-9A-Z][0-9A-Z]{2})|([1-9a-z][0-9a-z]{2}))/;
validMARC.reIndicator1 = /[\da-z]{1}/;
validMARC.reIndicator2 = /[\da-z]{1}/;
validMARC.reSubfieldCode = /[\da-z!&quot;#$%&amp;'()*+,-./:;&lt;=&gt;?{}_^`~\[\]\\]{1}/;


/*
 * **************************** 6. Record UI ***********************************
 */

function onNewRecordClick(event){
  /*
   * Handle 'New' button (new record).
   */
  updateStatus('updating');
  if (gRecordDirty){
    if (!displayAlert('confirmLeavingChangedRecord')){
      updateStatus('ready');
      event.preventDefault();
      return;
    }
  }
  else
    // If the record is unchanged, erase the cache.
    if (gReadOnlyMode == false)
      createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  changeAndSerializeHash({state: 'newRecord'});
  cleanUp(true, '');
  $('.headline').text('Record Editor: Create new record');
  displayNewRecordScreen();
  bindNewRecordHandlers();
  updateStatus('ready');
  event.preventDefault();
}

function getRecord(recID, recRev, onSuccess){
  /* A function retrieving the bibliographic record, using an AJAX request.
   *
   * recID : the identifier of a record to be retrieved from the server
   * recRev : the revision of the record to be retrieved (0 or undefined
   *          means retrieving the newest version )
   * onSuccess : The callback to be executed upon retrieval. The default
   *             callback loads the retrieved record into the bibEdit user
   *             interface
   */

  // Temporary store the record ID by attaching it to the onGetRecordSuccess
  // function.
  if (onSuccess == undefined)
    onSuccess = onGetRecordSuccess;
  if (recRev != undefined && recRev != 0){
    changeAndSerializeHash({state: 'edit', recid: recID, recrev: recRev});
  }
  else{
    changeAndSerializeHash({state: 'edit', recid: recID});
  }

  gRecIDLoading = recID;

  reqData = {recID: recID,
             requestType: 'getRecord',
             deleteRecordCache:
             getRecord.deleteRecordCache,
             clonedRecord: getRecord.clonedRecord,
             inReadOnlyMode: gReadOnlyMode};

  if (recRev != undefined && recRev != 0){
    reqData.recordRevision = recRev;
    reqData.inReadOnlyMode = true;
  }

  resetBibeditState();
  createReq(reqData, onSuccess);

  onHoldingPenPanelRecordIdChanged(recID) // reloading the Holding Pen toolbar
  getRecord.deleteRecordCache = false;
  getRecord.clonedRecord = false;
}
// Enable this flag to delete any existing cache before fetching next record.
getRecord.deleteRecordCache = false;
// Enable this flag to tell that we are fetching a record that has just been
// cloned (enables proper feedback, highlighting).
getRecord.clonedRecord = false;


function onGetRecordSuccess(json){
  /*
   * Handle successfull 'getRecord' requests.
   */
  cleanUp(!gNavigatingRecordSet);
  // Store record data.
  gRecID = json['recID'];
  gRecIDLoading = null;
  gRecRev = json['recordRevision'];
  gRecRevAuthor = json['revisionAuthor'];

  var revDt = formatDateTime(getRevisionDate(gRecRev));
  var recordRevInfo = "record revision: " + revDt;
  var revAuthorString = gRecRevAuthor;

  $('.headline').html(
    'Record Editor: Record #<span id="spnRecID">' + gRecID + '</span>' +
    '<div style="margin-left: 5px; font-size: 0.5em; color: #36c;">' +
    recordRevInfo + ' ' + revAuthorString + '</div>').css('white-space', 'nowrap');
  gRecord = json['record'];
  gTagFormat = json['tagFormat'];
  gRecordDirty = json['cacheDirty'];
  gCacheMTime = json['cacheMTime'];

  if (json['cacheOutdated']){
    // User had an existing outdated cache.
    displayCacheOutdatedScreen('getRecord');
    $('#lnkMergeCache').bind('click', onMergeClick);
    $('#lnkDiscardChanges').bind('click', function(event){
      getRecord.deleteRecordCache = true;
      getRecord(gRecID);
      event.preventDefault();
    });
    $('#lnkRemoveMsg').bind('click', function(event){
      $('#bibEditMessage').remove();
      event.preventDefault();
    });
  }

  gHoldingPenChanges = json['pendingHpChanges'];
  gDisabledHpEntries = json['disabledHpChanges'];
  gHoldingPenLoadedChanges = {};

  disableProcessedChanges();

  // Display record.
  displayRecord();
  // Activate menu record controls.
  activateRecordMenu();
  // the current mode should is indicated by the result from the server
  gReadOnlyMode = (json['inReadOnlyMode'] != undefined) ? json['inReadOnlyMode'] : false;
  gRecLatestRev = (json['latestRevision'] != undefined) ? json['latestRevision'] : null;
  gRecRevisionHistory = (json['revisionsHistory'] != undefined) ? json['revisionsHistory'] : null;

  updateInterfaceAccordingToMode();

  if (gRecordDirty){
    $('#btnSubmit').removeAttr('disabled');
    $('#btnSubmit').css('background-color', 'lightgreen');
  }
  if (gTagFormat == 'MARC')
    $('#btnHumanTags').bind('click', onHumanTagsClick).removeAttr('disabled');
  else
    $('#btnMARCTags').bind('click', onMARCTagsClick).removeAttr('disabled');
  // Unfocus record selection field (to facilitate hotkeys).
  $('#txtSearchPattern').blur();
  if (json['resultCode'] == 9)
    $('#spnRecID').effect('highlight', {color: gCLONED_RECORD_COLOR},
      gCLONED_RECORD_COLOR_FADE_DURATION);
  updateStatus('report', gRESULT_CODES[json['resultCode']]);
  updateRevisionsHistory();
  createReq({recID: gRecID, requestType: 'getTickets'}, onGetTicketsSuccess);

}

function onGetTemplateSuccess(json) {
  onGetRecordSuccess(json);
}

function onSubmitClick(){
  /*
   * Handle 'Submit' button (submit record).
   */
  updateStatus('updating');
  if (displayAlert('confirmSubmit')){
    createReq({recID: gRecID, requestType: 'submit',
         force: onSubmitClick.force}, function(json){
       // Submission was successful.
      changeAndSerializeHash({state: 'submit', recid: gRecID});
      var resCode = json['resultCode'];
      cleanUp(!gNavigatingRecordSet, '', null, true);
      updateStatus('report', gRESULT_CODES[resCode]);
      displayMessage(resCode);
      resetBibeditState()
    });
    onSubmitClick.force = false;
  }
  else
    updateStatus('ready');
  holdingPenPanelRemoveEntries(); // clearing the holding pen entries list
}

// Enable this flag to force the next submission even if cache is outdated.
onSubmitClick.force = false;

function onCancelClick(){
  /*
   * Handle 'Cancel' button (cancel editing).
   */
  updateStatus('updating');
  if (!gRecordDirty || displayAlert('confirmCancel')) {
  createReq({
    recID: gRecID,
    requestType: 'cancel'
  }, function(json){
    // Cancellation was successful.
      changeAndSerializeHash({
          state: 'cancel',
          recid: gRecID
        });
        cleanUp(!gNavigatingRecordSet, '', null, true, true);
        updateStatus('report', gRESULT_CODES[json['resultCode']]);
      });
      holdingPenPanelRemoveEntries();
    }
    else {
      updateStatus('ready');
    }
}

function onCloneRecordClick(){
  /*
   * Handle 'Clone' button (clone record).
   */
  updateStatus('updating');
  if (!displayAlert('confirmClone')){
    updateStatus('ready');
    return;
  }
  else if (!gRecordDirty)
    // If the record is unchanged, erase the cache.
    createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  createReq({requestType: 'newRecord', newType: 'clone', recID: gRecID},
    function(json){
      var newRecID = json['newRecID'];
      $('#txtSearchPattern').val(newRecID);
      getRecord.clonedRecord = true;
      getRecord(newRecID);
  });
}

function onDeleteRecordClick(){
  /*
   * Handle 'Delete record' button.
   */
  if (displayAlert('confirmDeleteRecord')){
    updateStatus('updating');
    createReq({recID: gRecID, requestType: 'deleteRecord'}, function(json){
      // Record deletion was successful.
      changeAndSerializeHash({state: 'deleteRecord', recid: gRecID});
      cleanUp(!gNavigatingRecordSet, '', null, true);
      var resCode = json['resultCode'];
      // now cleaning the interface - removing holding pen entries and record history
      resetBibeditState();
      updateStatus('report', gRESULT_CODES[resCode]);
      displayMessage(resCode);
    });
  }
}

function onMergeClick(event){
  /*
   * Handle click on 'Merge' link (to merge outdated cache with current DB
   * version of record).
   */
  notImplemented(event);

  updateStatus('updating');
  createReq({recID: gRecID, requestType: 'prepareRecordMerge'}, function(json){
    // Null gRecID to avoid warning when leaving page.
    gRecID = null;
    var recID = json['recID'];
    window.location = gSITE_URL + '/record/merge/#recid1=' + recID + '&recid2=' +
      'tmp';
  });
  event.preventDefault();
}

function bindNewRecordHandlers(){
  /*
   * Bind event handlers to links on 'Create new record' page.
   */
  $('#lnkNewEmptyRecord').bind('click', function(event){
    updateStatus('updating');
    createReq({requestType: 'newRecord', newType: 'empty'}, function(json){
      getRecord(json['newRecID']);
    });
    event.preventDefault();
  });
  for (var i=0, n=gRECORD_TEMPLATES.length; i<n; i++)
    $('#lnkNewTemplateRecord_' + i).bind('click', function(event){
      updateStatus('updating');
      var templateNo = this.id.split('_')[1];
      createReq({requestType: 'newRecord', newType: 'template',
	templateFilename: gRECORD_TEMPLATES[templateNo][0]}, function(json){
	  getRecord(json['newRecID'], 0, onGetTemplateSuccess); // recRev = 0 -> current revision
      });
      event.preventDefault();
    });
}

function cleanUp(disableRecBrowser, searchPattern, searchType,
     focusOnSearchBox, resetHeadline){
  /*
   * Clean up display and data.
   */
  // Deactivate controls.
  deactivateRecordMenu();
  if (disableRecBrowser){
    disableRecordBrowser();
    gResultSet = null;
    gResultSetIndex = null;
    gNavigatingRecordSet = false;
  }
  // Clear main content area.
  if (resetHeadline)
    $('.headline').text('Record Editor');
  $('#bibEditContent').empty();
  // Clear search area.
  if (typeof(searchPattern) == 'string' || typeof(searchPattern) == 'number')
    $('#txtSearchPattern').val(searchPattern);
  if ($.inArray(searchType, ['recID', 'reportnumber', 'anywhere']) != -1)
    $('#sctSearchType').val(searchPattern);
  if (focusOnSearchBox)
    $('#txtSearchPattern').focus();
  // Clear tickets.
  $('#tickets').empty();
  // Clear data.
  gRecID = null;
  gRecord = null;
  gTagFormat = null;
  gRecordDirty = false;
  gCacheMTime = null;
  gSelectionMode = false;
  gReadOnlyMode = false;
  gHoldingPenLoadedChanges = null;
  gHoldingPenChanges = null;
}

function positionBibEditPanel(minimalPosition){
    /*
     * Dynamically position menu based on vertical scroll distance.
     */
    var newYscroll = $(document).scrollTop();
    // Only care if there has been some major scrolling.
    if (Math.abs(newYscroll - positionMenu.yScroll) > 10){
      // If scroll distance is less then 200px, position menu in sufficient
      // distance from header.
      if (newYscroll < 200)
        $('#bibEditMenu').animate({
    'top': 220 - newYscroll}, 'fast');
      // If scroll distance has crossed 200px, fix menu 50px from top.
      else if (positionMenu.yScroll < 200 && newYscroll > 200)
        $('#bibEditMenu').animate({
    'top': 50}, 'fast');
      positionMenu.yScroll = newYscroll;
    }
  }
/*
 * **************************** 7. Editor UI ***********************************
 */

function colorFields(){
  /*
   * Color every other field (rowgroup) gray to increase readability.
   */
  $('#bibEditTable tbody:even').each(function(){
    $(this).addClass('bibEditFieldColored');
  });
}

function reColorFields(){
  /*
   * Update coloring by removing existing, then recolor.
   */
  $('#bibEditTable tbody').each(function(){
    $(this).removeClass('bibEditFieldColored');
  });
  colorFields();
}

function onMARCTagsClick(event){
  /*
   * Handle 'MARC' link (MARC tags).
   */
  $(this).unbind('click').attr('disabled', 'disabled');
  createReq({recID: gRecID, requestType: 'changeTagFormat', tagFormat: 'MARC'});
  gTagFormat = 'MARC';
  updateTags();
  $('#btnHumanTags').bind('click', onHumanTagsClick).removeAttr('disabled');
  event.preventDefault();
}

function onHumanTagsClick(event){
  /*
   * Handle 'Human' link (Human tags).
   */
  $(this).unbind('click').attr('disabled', 'disabled');
  createReq({recID: gRecID, requestType: 'changeTagFormat',
       tagFormat: 'human'});
  gTagFormat = 'human';
  updateTags();
  $('#btnMARCTags').bind('click', onMARCTagsClick).removeAttr('disabled');
  event.preventDefault();
}

function updateTags(){
  /*
   * Check and update all tags (also subfield codes) against the currently
   * selected tag format.
   */
  $('.bibEditCellFieldTag').each(function(){
    var currentTag = $(this).text();
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2];
    var newTag = getFieldTag(getMARC(tag, fieldPosition));
    if (newTag != currentTag)
      $(this).text(newTag);
  });
  $('.bibEditCellSubfieldTag').each(function(){
    var currentTag = $(this).text();
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2],
      subfieldIndex = tmpArray[3];
    var newTag = getSubfieldTag(getMARC(tag, fieldPosition, subfieldIndex));
    if (newTag != currentTag)
      $(this).text(newTag);
  });
}

function onFieldBoxClick(box){
  /*
   * Handle field select boxes.
   */
  // Check/uncheck all subfield boxes, add/remove selected class.
  var rowGroup = $('#rowGroup_' + box.id.slice(box.id.indexOf('_')+1));
  if (box.checked){
    $(rowGroup).find('td[id^=content]').andSelf().addClass('bibEditSelected');
    if (gReadOnlyMode == false){
      $('#btnDeleteSelected').removeAttr('disabled');
    }
  }
  else{
    $(rowGroup).find('td[id^=content]').andSelf().removeClass(
      'bibEditSelected');
    if (!$('.bibEditSelected').length)
      // Nothing is selected, disable "Delete selected"-button.
      $('#btnDeleteSelected').attr('disabled', 'disabled');
  }
  $(rowGroup).find('input[type="checkbox"]').attr('checked', box.checked);
}

function onSubfieldBoxClick(box){
  /*
   * Handle subfield select boxes.
   */
  var tmpArray = box.id.split('_');
  var tag = tmpArray[1], fieldPosition = tmpArray[2],
    subfieldIndex = tmpArray[3];
  var fieldID = tag + '_' + fieldPosition;
  var subfieldID = fieldID + '_' + subfieldIndex;
  // If uncheck, uncheck field box and remove selected class.
  if (!box.checked){
    $('#content_' + subfieldID).removeClass('bibEditSelected');
    $('#boxField_' + fieldID).attr('checked', false);
    $('#rowGroup_' + fieldID).removeClass('bibEditSelected');
    if (!$('.bibEditSelected').length)
      // Nothing is selected, disable "Delete selected"-button.
      $('#btnDeleteSelected').attr('disabled', 'disabled');
  }
  // If check and all other subfield boxes checked, check field box, add
  // selected class.
  else{
    $('#content_' + subfieldID).addClass('bibEditSelected');
    var field = gRecord[tag][fieldPosition];
    if (field[0].length == $(
      '#rowGroup_' + fieldID + ' input[type=checkbox]' +
      '[class=bibEditBoxSubfield]:checked').length){
      $('#boxField_' + fieldID).attr('checked', true);
      $('#rowGroup_' + fieldID).addClass('bibEditSelected');
    }
    $('#btnDeleteSelected').removeAttr('disabled');
  }
}

function addFieldGatherInformations(fieldTmpNo){
  /** Gathering the information about a current form
      returns [template_num, data]
      This funcion saves the state of a form -> saving the template name and values only would
      not be enough. we want to know what has been modified in last-chosen template !
      data is in the same format as teh templates data.
  */
  var templateNum = $('#selectAddFieldTemplate_' + fieldTmpNo).attr("value");
  var tag = $("#txtAddFieldTag_" + fieldTmpNo).attr("value");

  // now checking if this is a controlfield ... controlfield if ind1 box is invisible
  if ($("#txtAddFieldInd1_" + fieldTmpNo + ":visible").length == 1){
    var ind1 = $("#txtAddFieldInd1_" + fieldTmpNo).attr("value");
    var ind2 = $("#txtAddFieldInd2_" + fieldTmpNo).attr("value");
    var subfieldTmpNo = $('#rowGroupAddField_' + fieldTmpNo).data('freeSubfieldTmpNo');
    var subfields = [];
    for (i=0;i<subfieldTmpNo;i++){
      var subfieldCode = $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_' + i).attr("value");
      var subfieldValue = $('#txtAddFieldValue_' + fieldTmpNo + '_' + i).attr("value");
      subfields.push([subfieldCode, subfieldValue]);
    }

    data = {
      "name": "nonexisting template - values taken from the field",
      "description": "The description of a template",
      "tag" : tag,
      "ind1" : ind1,
      "ind2" : ind2,
      "subfields" : subfields,
      "isControlfield" : false
    };
  } else {
    cfValue = $("#txtAddFieldValue_" + fieldTmpNo + "_0").attr("value");
    data = {
      "name": "nonexisting template - values taken from the field",
      "description": "The description of a template",
      "tag" : tag,
      "value" : cfValue,
      "isControlfield" : true
    }
  }

  return [templateNum, data];
}

function addFieldAddSubfieldEditor(jQRowGroupID, fieldTmpNo, defaultCode, defaultValue){
  /**
     Adding a subfield input control into the editor
     optional parameters:

     defaultCode - the subfield code that will be displayed
     defaultValue - the value that will be displayed by default in the editor
  */
  var subfieldTmpNo = $(jQRowGroupID).data('freeSubfieldTmpNo');
  $(jQRowGroupID).data('freeSubfieldTmpNo', subfieldTmpNo+1);

  var addFieldRows = $(jQRowGroupID + ' tr');

  $(addFieldRows).eq(addFieldRows.length-1).before(createAddFieldRow(
    fieldTmpNo, subfieldTmpNo, defaultCode, defaultValue));
  $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_' + subfieldTmpNo).bind(
    'keyup', onAddFieldChange);
  $('#btnAddFieldRemove_' + fieldTmpNo + '_' + subfieldTmpNo).bind('click', function(){
    $('#rowAddField_' + this.id.slice(this.id.indexOf('_')+1)).remove();
  });
  $('#txtAddFieldValue_' + fieldTmpNo + '_' + subfieldTmpNo).bind(
    'focus', function(){
      if ($(this).hasClass('bibEditVolatileSubfield')){
        $(this).select();
        $(this).removeClass("bibEditVolatileSubfield");
      }
    });
  var contentEditorId = '#txtAddFieldValue_' + fieldTmpNo + '_' + subfieldTmpNo;
  $(contentEditorId).bind('keyup', function(e){
    onAddFieldValueKeyPressed(e, jQRowGroupID, fieldTmpNo, subfieldTmpNo);
  });

}

function onAddFieldJumpToNextSubfield(jQRowGroupID, fieldTmpNo, subfieldTmpNo){
  // checking, how many subfields are there and if last, submitting the form
  var numberOfSubfields = $(jQRowGroupID).data('freeSubfieldTmpNo');
  if (subfieldTmpNo < (numberOfSubfields - 1)){
    var elementCode = "#txtAddFieldSubfieldCode_" + fieldTmpNo + "_" + (subfieldTmpNo + 1);
    $(elementCode)[0].focus();
  }
  else{
//    alert("submitting the form cause the last one has been left");
    addFieldSave(fieldTmpNo);
  }
}

function applyFieldTemplate(jQRowGroupID, formData, fieldTmpNo){
  /** A function that applies a template
      formNo is the number of addfield form that is treated at teh moment
      formData is the data of the field template
  */

  // first cleaning the existing fields

  $(jQRowGroupID).data('isControlfield', formData.isControlfield);
  if (formData.isControlfield){
    changeFieldToControlfield(fieldTmpNo);
    $("#txtAddFieldTag_" + fieldTmpNo).attr("value", formData.tag);
    $("#txtAddFieldInd1_" + fieldTmpNo).attr("value", '');
    $("#txtAddFieldInd2_" + fieldTmpNo).attr("value", '');
    $("#txtAddFieldValue_" + fieldTmpNo + "_0").attr("value", formData.value);
  }
  else
  {
    changeFieldToDatafield(fieldTmpNo);
    var subfieldTmpNo = $(jQRowGroupID).data('freeSubfieldTmpNo');
    $(jQRowGroupID).data('freeSubfieldTmpNo', 0);

    for (i=subfieldTmpNo-1; i>=0; i--){
      $('#rowAddField_' + fieldTmpNo + '_' + i).remove();
    }

    for (subfieldInd in formData.subfields){
      subfield = formData.subfields[subfieldInd];
      addFieldAddSubfieldEditor(jQRowGroupID, fieldTmpNo, subfield[0], subfield[1]);
    }

    // now changing the main field properties
    $("#txtAddFieldTag_" + fieldTmpNo).attr("value", formData.tag);
    $("#txtAddFieldInd1_" + fieldTmpNo).attr("value", formData.ind1);
    $("#txtAddFieldInd2_" + fieldTmpNo).attr("value", formData.ind2);
  }
}

function createAddFieldInterface(initialContent, initialTemplateNo){
  // Create form and scroll close to the top of the table.
  $(document).scrollTop(0);
  var fieldTmpNo = onAddFieldClick.addFieldFreeTmpNo++;
  var jQRowGroupID = '#rowGroupAddField_' + fieldTmpNo;
  $('#bibEditColFieldTag').css('width', '90px');
  var tbodyElements = $('#bibEditTable tbody');
  var insertionPoint = (tbodyElements.length >= 4) ? 3 : tbodyElements.length-1;
  $('#bibEditTable tbody').eq(insertionPoint).after(
    createAddFieldForm(fieldTmpNo, initialTemplateNo));
  $(jQRowGroupID).data('freeSubfieldTmpNo', 1);

  // Bind event handlers.
  $('#btnAddFieldAddSubfield_' + fieldTmpNo).bind('click', function(){
    addFieldAddSubfieldEditor(jQRowGroupID, fieldTmpNo, "", "");
  });
  $('#txtAddFieldTag_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldInd1_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldInd2_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0').bind('keyup',
							  onAddFieldChange);
  $('#txtAddFieldValue_' + fieldTmpNo + '_0').bind('keyup', function (e){
    onAddFieldValueKeyPressed(e, jQRowGroupID, fieldTmpNo, 0);
  });

  $('#selectAddFieldTemplate_' + fieldTmpNo).bind('change', function(e){
      value = $('#selectAddFieldTemplate_' + fieldTmpNo).attr("value");
      applyFieldTemplate(jQRowGroupID, fieldTemplates[value], fieldTmpNo);
  });
  $('#selectAddSimilarFields_' + fieldTmpNo).bind('click', function(e){
    var data = addFieldGatherInformations(fieldTmpNo);
    var numRepetitions = parseInt($('#selectAddFieldTemplateTimes_' + fieldTmpNo).attr('value'));
    for (var i=0; i< numRepetitions; i++){
      createAddFieldInterface(data[1], data[0]);
    }
  });

  if (initialContent != undefined){
    applyFieldTemplate(jQRowGroupID, initialContent , fieldTmpNo);
  }else{
    $(jQRowGroupID).data('isControlfield', false);
  }

  reColorFields();
  $('#txtAddFieldTag_' + fieldTmpNo).focus();
  // Color the new form for a short period.
  $(jQRowGroupID).effect('highlight', {color: gNEW_ADD_FIELD_FORM_COLOR},
    gNEW_ADD_FIELD_FORM_COLOR_FADE_DURATION);

}

function onAddSubfieldValueKeyPressed(e, tag, fieldPosition, subfieldPosition){
  if (e.which == 13){
    // enter key pressed.
    var subfieldsNum = $('#rowGroup_' + tag + '_' + fieldPosition + ' .bibEditTxtSubfieldCode').length;
    if (subfieldPosition < (subfieldsNum - 1)){
      //jump to the next field
      $('#txtAddSubfieldsCode_' + tag + '_' + fieldPosition + '_' + (subfieldPosition + 1))[0].focus();
    } else {
      onAddSubfieldsSave(e, tag, fieldPosition);
    }
  }
  if (e.which == 27){
    // escape key pressed
    $('#rowAddSubfields_' + tag + '_' + fieldPosition + '_' + 0).nextAll().andSelf().remove();
  }
}

function onAddFieldValueKeyPressed(e, jQRowGroupID, fieldTmpNo, subfieldInd){
  if (e.which == 13){
    // enter key pressed
    onAddFieldJumpToNextSubfield(jQRowGroupID, fieldTmpNo, subfieldInd);
  }
  if (e.which == 27){
    // escape key pressed
    $(jQRowGroupID).remove();
    if (!$('#bibEditTable > [id^=rowGroupAddField]').length)
      $('#bibEditColFieldTag').css('width', '48px');
    reColorFields();
  }
}
function onAddFieldClick(){
  /*
   * Handle 'Add field' button.
   */
  if (failInReadOnly())
    return;
  createAddFieldInterface();
}

// Incrementing temporary field numbers.
onAddFieldClick.addFieldFreeTmpNo = 100000;

function changeFieldToControlfield(fieldTmpNo){
  /**
     Switching the field to be a control field
   */

  // removing additional entries
  var addFieldRows = $('#rowGroupAddField_' + fieldTmpNo + ' tr');
  $(addFieldRows).slice(2, addFieldRows.length-1).remove();

  // Clear all fields.
  var addFieldTextInput = $('#rowGroupAddField_' + fieldTmpNo +
          ' input[type=text]');
  $(addFieldTextInput).val('').removeClass('bibEditInputError');

  // Toggle hidden fields.
  var elems = $('#txtAddFieldInd1_' + fieldTmpNo + ', #txtAddFieldInd2_' +
    fieldTmpNo + ', #txtAddFieldSubfieldCode_' + fieldTmpNo + '_0,' +
    '#btnAddFieldAddSubfield_' + fieldTmpNo).hide();

  $('#txtAddFieldTag_' + fieldTmpNo).focus();
}

function changeFieldToDatafield(fieldTmpNo){
  /**
     Switching the field to be a datafield
   */
  // making the elements visible
  var elems = $('#txtAddFieldInd1_' + fieldTmpNo + ', #txtAddFieldInd2_' +
    fieldTmpNo + ', #txtAddFieldSubfieldCode_' + fieldTmpNo + '_0,' +
    '#btnAddFieldAddSubfield_' + fieldTmpNo).show();

  $('#txtAddFieldTag_' + fieldTmpNo).focus();
}

function onAddFieldChange(event){
  /*
   * Validate MARC and add or remove error class.
   */

  // first handling the case of escape key, which is a little different that others
  var fieldTmpNo = this.id.split('_')[1];

  if (event.which == 27){
    // escape key pressed
    var jQRowGroupID = "#rowGroupAddField_" + fieldTmpNo;
    $(jQRowGroupID).remove();
    if (!$('#bibEditTable > [id^=rowGroupAddField]').length)
      $('#bibEditColFieldTag').css('width', '48px');
    reColorFields();
  }
  else if (this.value.length == this.maxLength){
    var fieldType;
    if (this.id.indexOf('Tag') != -1){
      var jQRowGroupID = "#rowGroupAddField_" + fieldTmpNo;
      fieldType = ($(jQRowGroupID).data('isControlfield')) ? 'ControlTag' : 'Tag';
    }
    else if (this.id.indexOf('Ind1') != -1)
      fieldType = 'Indicator1';
    else if (this.id.indexOf('Ind2') != -1)
      fieldType = 'Indicator2';
    else
      fieldType = 'SubfieldCode';

    var valid = (((fieldType == 'Indicator1' || fieldType == 'Indicator2')
      && (this.value == '_' || this.value == ' '))
     || validMARC(fieldType, this.value));
    if (!valid && !$(this).hasClass('bibEditInputError'))
      $(this).addClass('bibEditInputError');
    else if (valid){
      if ($(this).hasClass('bibEditInputError'))
  $(this).removeClass('bibEditInputError');
      if (event.keyCode != 9 && event.keyCode != 16){
	switch(fieldType){
	  case 'ControlTag':
	    $(this).parent().nextAll().eq(3).children('input').focus();
	    break;
	  case 'Tag':
	  case 'Indicator1':
	    $(this).next().focus();
	    break;
	  case 'Indicator2':
          // in case the indicator is present, we can be sure this is not a control field... so we can safely jump to the subfield code input
          $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0')[0].focus();
	    break;
	  case 'SubfieldCode':
	    $(this).parent().next().children('input').focus();
	    break;
	  default:
	    ;
	}
      }
    }
  }
  else if ($(this).hasClass('bibEditInputError'))
    $(this).removeClass('bibEditInputError');
}

function onAddFieldSave(event){
  var fieldTmpNo = this.id.split('_')[1];
  addFieldSave(fieldTmpNo);
}

function addFieldSave(fieldTmpNo)
{
  /*
   * Handle 'Save' button in add field form.
   */
  updateStatus('updating');

  var jQRowGroupID = "#rowGroupAddField_" + fieldTmpNo;
  var controlfield = $(jQRowGroupID).data('isControlfield');
  var tag = $('#txtAddFieldTag_' + fieldTmpNo).val();
  var value = $('#txtAddFieldValue_' + fieldTmpNo + '_0').val();
  var subfields = [], ind1 = ' ', ind2 = ' ';

  if (controlfield){
    // Controlfield. Validate and prepare to update.
    if (fieldIsProtected(tag)){
      displayAlert('alertAddProtectedField', [tag]);
      updateStatus('ready');
      return;
    }
    if (!validMARC('ControlTag', tag) || value == ''){
      displayAlert('alertCriticalInput');
      updateStatus('ready');
      return;
    }
    var field = [[], ' ', ' ', value, 0];
    var fieldPosition = getFieldPositionInTag(tag, field);
  }
  else{
    // Regular field. Validate and prepare to update.
    ind1 = $('#txtAddFieldInd1_' + fieldTmpNo).val();
    ind1 = (ind1 == '' || ind1 == '_') ? ' ' : ind1;
    ind2 = $('#txtAddFieldInd2_' + fieldTmpNo).val();
    ind2 = (ind2 == '' || ind2 == '_') ? ' ' : ind2;
    var MARC = tag + ind1 + ind2;
    if (fieldIsProtected(MARC)){
      displayAlert('alertAddProtectedField', [MARC]);
      updateStatus('ready');
      return;
    }
    var validInd1 = (ind1 == ' ' || validMARC('Indicator1', ind1));
    var validInd2 = (ind2 == ' ' || validMARC('Indicator2', ind2));
    if (!validMARC('Tag', tag)
  || !validInd1
  || !validInd2){
      displayAlert('alertCriticalInput');
      updateStatus('ready');
      return;
    }
    // Collect valid subfields in an array.
    var invalidOrEmptySubfields = false;
     $('#rowGroupAddField_' + fieldTmpNo + ' .bibEditTxtSubfieldCode'
      ).each(function(){
        var subfieldTmpNo = this.id.slice(this.id.lastIndexOf('_')+1);
        var txtValue = $('#txtAddFieldValue_' + fieldTmpNo + '_' +
    subfieldTmpNo);
        var value = $(txtValue).val();
        var isStillVolatile = txtValue.hasClass('bibEditVolatileSubfield');

        if (!$(this).hasClass('bibEditInputError')
          && this.value != ''
	  && !$(txtValue).hasClass('bibEditInputError')
          && value != ''){
            if (!isStillVolatile){
              subfields.push([this.value, value]);
            }
        }
        else
          invalidOrEmptySubfields = true;
      });

    if (invalidOrEmptySubfields){
      if (!subfields.length){
  // No valid subfields.
  displayAlert('alertCriticalInput');
  updateStatus('ready');
  return;
      }
      else if (!displayAlert('confirmInvalidOrEmptyInput')){
  updateStatus('ready');
  return;
      }
    }

    if (subfields[0] == undefined){
      displayAlert('alertEmptySubfieldsList');
      return;
    }
    var field = [subfields, ind1, ind2, '', 0];
    var fieldPosition = getFieldPositionInTag(tag, field);
  }

  // Create Ajax request.
  var data = {
    recID: gRecID,
    requestType: 'addField',
    controlfield: controlfield,
    fieldPosition: fieldPosition,
    tag: tag,
    ind1: ind1,
    ind2: ind2,
    subfields: subfields,
    value: value
  };
  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']]);
  });

  // Continue local updating.
  var fields = gRecord[tag];
  // New field?
  if (!fields)
    gRecord[tag] = [field];
  else{
    fields.splice(fieldPosition, 0, field);
  }
  // Remove form.
  $('#rowGroupAddField_' + fieldTmpNo).remove();
  if (!$('#bibEditTable > [id^=rowGroupAddField]').length)
      $('#bibEditColFieldTag').css('width', '48px');
  // Redraw all fields with the same tag and recolor the full table.
  redrawFields(tag);
  reColorFields();
  // Scroll to and color the new field for a short period.
  var rowGroup = $('#rowGroup_' + tag + '_' + fieldPosition);
  $(document).scrollTop($(rowGroup).position().top - $(window).height()*0.5);
  $(rowGroup).effect('highlight', {color: gNEW_CONTENT_COLOR},
         gNEW_CONTENT_COLOR_FADE_DURATION);
}


function onAddSubfieldsClick(img){
  /*
   * Handle 'Add subfield' buttons.
   */
  var fieldID = img.id.slice(img.id.indexOf('_')+1);
  var jQRowGroupID = '#rowGroup_' + fieldID;
  var tmpArray = fieldID.split('_');
  var tag = tmpArray[0]; var fieldPosition = tmpArray[1];
  if ($('#rowAddSubfieldsControls_' + fieldID).length == 0){
    // The 'Add subfields' form does not exist for this field.
    $(jQRowGroupID).append(createAddSubfieldsForm(fieldID));
    $(jQRowGroupID).data('freeSubfieldTmpNo', 1);
    $('#txtAddSubfieldsCode_' + fieldID + '_' + 0).bind('keyup',
      onAddSubfieldsChange);
    $('#txtAddSubfieldsValue_' + fieldID + '_0').bind('keyup', function (e){
      onAddSubfieldValueKeyPressed(e, tag, fieldPosition, 0);
    });
    $('#txtAddSubfieldsCode_' + fieldID + '_' + 0).focus();
  }
  else{
    // The 'Add subfields' form exist for this field. Just add another row.
    var subfieldTmpNo = $(jQRowGroupID).data('freeSubfieldTmpNo');
    $(jQRowGroupID).data('freeSubfieldTmpNo', subfieldTmpNo+1);
    var subfieldTmpID = fieldID + '_' + subfieldTmpNo;
    $('#rowAddSubfieldsControls_' + fieldID).before(
      createAddSubfieldsRow(fieldID, subfieldTmpNo));
    $('#txtAddSubfieldsCode_' + subfieldTmpID).bind('keyup',
      onAddSubfieldsChange);
    $('#btnAddSubfieldsRemove_' + subfieldTmpID).bind('click', function(){
      $('#rowAddSubfields_' + subfieldTmpID).remove();
    });
    $('#txtAddSubfieldsValue_' + subfieldTmpID).bind('keyup', function (e){
      onAddSubfieldValueKeyPressed(e, tag, fieldPosition, subfieldTmpNo);
    });
  }
}

function onAddSubfieldsChange(event){
  /*
   * Validate subfield code and add or remove error class.
   */
  if (this.value.length == 1){
    var valid = validMARC('SubfieldCode', this.value);
    if (!valid && !$(this).hasClass('bibEditInputError'))
      $(this).addClass('bibEditInputError');
    else if (valid){
      if ($(this).hasClass('bibEditInputError'))
  $(this).removeClass('bibEditInputError');
      if (event.keyCode != 9 && event.keyCode != 16){
  $(this).parent().next().children('input').focus();
      }
    }
  }
  else if ($(this).hasClass('bibEditInputError'))
    $(this).removeClass('bibEditInputError');
}

function onAddSubfieldsSave(event, tag, fieldPosition){
  /*
   * Handle 'Save' button in add subfields form.
   */
  updateStatus('updating');

//  var tmpArray = this.id.split('_');
//  var tag = tmpArray[1], fieldPosition = tmpArray[2];
  var fieldID = tag + '_' + fieldPosition;
  var subfields = [];
  var protectedSubfield = false, invalidOrEmptySubfields = false;
  // Collect valid fields in an array.
  $('#rowGroup_' + fieldID + ' .bibEditTxtSubfieldCode'
   ).each(function(){
     var MARC = getMARC(tag, fieldPosition) + this.value;
     if ($.inArray(MARC, gPROTECTED_FIELDS) != -1){
       protectedSubfield = MARC;
       return false;
     }
     var subfieldTmpNo = this.id.slice(this.id.lastIndexOf('_')+1);
     var txtValue = $('#txtAddSubfieldsValue_' + fieldID + '_' +
       subfieldTmpNo);
     var value = $(txtValue).val();
     if (!$(this).hasClass('bibEditInputError')
   && this.value != ''
   && !$(txtValue).hasClass('bibEditInputError')
   && value != '')
       subfields.push([this.value, value]);
     else
       invalidOrEmptySubfields = true;
  });

  // Report problems, like protected, empty or invalid fields.
  if (protectedSubfield){
    displayAlert('alertAddProtectedSubfield');
    updateStatus('ready');
    return;
  }
  if (invalidOrEmptySubfields && !displayAlert('confirmInvalidOrEmptyInput')){
    updateStatus('ready');
    return;
  }

  if (!subfields.length == 0){
    // Create Ajax request
    var data = {
      recID: gRecID,
      requestType: 'addSubfields',
      tag: tag,
      fieldPosition: fieldPosition,
      subfields: subfields
    };
    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
    });

    // Continue local updating
    var field = gRecord[tag][fieldPosition];
    field[0] = field[0].concat(subfields);
    var rowGroup  = $('#rowGroup_' + fieldID);
    var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
    $(rowGroup).replaceWith(createField(tag, field, fieldPosition));
    if (coloredRowGroup)
      $('#rowGroup_' + fieldID).addClass('bibEditFieldColored');

    // Color the new fields for a short period.
    var rows = $('#rowGroup_' + fieldID + ' tr');
    $(rows).slice(rows.length - subfields.length).effect('highlight', {
      color: gNEW_CONTENT_COLOR}, gNEW_CONTENT_COLOR_FADE_DURATION);
  }
  else{
    // No valid fields were submitted.
    $('#rowAddSubfields_' + fieldID + '_' + 0).nextAll().andSelf().remove();
    updateStatus('ready');
  }
}

function convertFieldIntoEditable(cell, shouldSelect){
  // first we have to detach all exisiting editables ... which means detaching the event
  editEvent = 'click';
  $(cell).unbind(editEvent);

  $(cell).editable(
    function(value){
      newVal = onContentChange(value, this);
      if (newVal.substring(0,9) == "VOLATILE:"){
        $(cell).addClass("bibEditVolatileSubfield");
        newVal = newVal.substring(9);
        $(cell).addClass("bibEditVolatileSubfield");
        if (!shouldSelect){
          // the field should start selcting all the content upon the click
          convertFieldIntoEditable(cell, true);
        }
      }
      else{
        $(cell).removeClass("bibEditVolatileSubfield");
        if (shouldSelect){
          // this is a volatile field any more - clicking should not
          // select all the content inside.
          convertFieldIntoEditable(cell, false);
        }
      }

      return newVal;
    }, {
      type: 'autogrow',
      callback: function(data, settings){
        // TODO : CHECK THIS FUNCTION AFTER MERGING !!!!
        var tmpArray = this.id.split('_');
        var tag = tmpArray[1], fieldPosition = tmpArray[2],
        subfieldIndex = tmpArray[3];

        for (changeNum in gHoldingPenChanges){
          change =  gHoldingPenChanges[changeNum];
          if (change.tag == tag &&
              change.field_position == fieldPosition &&
              change.subfield_position != undefined &&
              change.subfield_position == subfieldIndex){
              addChangeControl(changeNum, true);
          }
        }
      },
      event: editEvent,
      data: function(){
        // Get the real content from the record structure (instead of
        // from the view, where HTML entities are escaped).
        var tmpArray = this.id.split('_');
        var tag = tmpArray[1], fieldPosition = tmpArray[2],
        subfieldIndex = tmpArray[3];
        var field = gRecord[tag][fieldPosition];
        var tmpResult = "";
        if (subfieldIndex == undefined)
          // Controlfield
          tmpResult = field[3];
        else
          tmpResult = field[0][subfieldIndex][1];
        if (tmpResult.substring(0,9) == "VOLATILE:"){
          tmpResult = tmpResult.substring(9);
        }
        return tmpResult;
      },
      placeholder: '',
      width: '100%',
      onblur: 'submit',
      select: shouldSelect,
      autogrow: {
        lineHeight: 16,
        minHeight: 36
      }
    });
}

function onContentClick(cell){
  /*
   * Handle click on editable content fields.
   */
  // Check if subfield is volatile subfield from a template
  var shouldSelect = false;
  if ( $(cell).hasClass('bibEditVolatileSubfield') ){
    shouldSelect = true;
  }
  if (!$(cell).hasClass('edit_area')){
    $(cell).addClass('edit_area').removeAttr('onclick');
    convertFieldIntoEditable(cell, shouldSelect);
    $(cell).trigger('click');
  }
}

function getUpdateSubfieldValueRequestData(tag, fieldPosition, subfieldIndex, subfieldCode, value, changeNo){
  var data = {
    recID: gRecID,
    requestType: 'modifyContent',
    tag: tag,
    fieldPosition: fieldPosition,
    subfieldIndex: subfieldIndex,
    subfieldCode: subfieldCode,
    value: value,
  };
  if (changeNo != undefined){
    data.changeApplied = changeNo;
  }
  return data;
}

function updateSubfieldValue(tag, fieldPosition, subfieldIndex, subfieldCode, value, consumedChange){
  updateStatus('updating');
  // Create Ajax request.
  if (consumedChange == undefined){
    consumedChange = -1;
  }
  var data =  getUpdateSubfieldValueRequestData(tag,
                          fieldPosition,
                          subfieldIndex,
                          subfieldCode,
                          value);

  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']]);
  });
}

function onContentChange(value, th){
  /*
   * Handle 'Save' button in editable content fields.
   */
  if (failInReadOnly()){
    return;
  }
  var tmpArray = th.id.split('_');
  var tag = tmpArray[1], fieldPosition = tmpArray[2], subfieldIndex = tmpArray[3];
  var field = gRecord[tag][fieldPosition];
  value = value.replace(/\n/g, ' '); // Replace newlines with spaces.
  if (subfieldIndex == undefined){
    // Controlfield
    if (field[3] == value)
      return escapeHTML(value);
    field[3] = value;
    subfieldIndex = null;
    var subfieldCode = null;
  }
  else{
    if (field[0][subfieldIndex][1] == value)
      return escapeHTML(value);
    // Regular field
    field[0][subfieldIndex][1] = value;
    var subfieldCode = field[0][subfieldIndex][0];
  }

  updateSubfieldValue(tag, fieldPosition, subfieldIndex, subfieldCode, value);

  setTimeout('$("#content_' + tag + '_' + fieldPosition + '_' + subfieldIndex +
      '").effect("highlight", {color: gNEW_CONTENT_COLOR}, ' +
      'gNEW_CONTENT_COLOR_FADE_DURATION)', gNEW_CONTENT_HIGHLIGHT_DELAY);
  // Return escaped value to display.
  return escapeHTML(value);
}

function onMoveSubfieldClick(type, tag, fieldPosition, subfieldIndex){
  /*
   * Handle subfield moving arrows.
   */
  if (failInReadOnly()){
    return;
  }
  updateStatus('updating');
  var fieldID = tag + '_' + fieldPosition;
  var field = gRecord[tag][fieldPosition];
  var subfields = field[0];
  var newSubfieldIndex;
  // Check if moving is possible
  if (type == 'up') {
    newSubfieldIndex = parseInt(subfieldIndex) - 1;
    if (newSubfieldIndex < 0) {
      updateStatus('ready', '');
      return;
    }
  }
  else {
    newSubfieldIndex = parseInt(subfieldIndex) + 1;
    if (newSubfieldIndex >= gRecord[tag][fieldPosition][0].length) {
      updateStatus('ready', '');
      return;
    }
  }
  // Create Ajax request.
  var data = {
    recID: gRecID,
    requestType: 'moveSubfield',
    tag: tag,
    fieldPosition: fieldPosition,
    subfieldIndex: subfieldIndex,
    newSubfieldIndex: newSubfieldIndex
  };
  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']]);
  }, false);
  // Continue local updating.
  var subfieldToSwap = subfields[newSubfieldIndex];
  subfields[newSubfieldIndex] = subfields[subfieldIndex];
  subfields[subfieldIndex] = subfieldToSwap;
  var rowGroup = $('#rowGroup_' + fieldID);
  var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
  $(rowGroup).replaceWith(createField(tag, field, fieldPosition));
  if (coloredRowGroup)
    $('#rowGroup_' + fieldID).addClass('bibEditFieldColored');
  $('#boxSubfield_'+fieldID+'_'+newSubfieldIndex).click();
}

function onDeleteClick(event){
  /*
   * Handle 'Delete selected' button or delete hotkeys.
   */
  // Find all checked checkboxes.
  if (failInReadOnly()){
    return;
  }
  var checkedFieldBoxes = $('input[class="bibEditBoxField"]:checked');
  var checkedSubfieldBoxes = $('input[class="bibEditBoxSubfield"]:checked');
  if (!checkedFieldBoxes.length && !checkedSubfieldBoxes.length)
    // No fields selected for deletion.
    return;
  updateStatus('updating');
  // toDelete is the complete datastructure of fields and subfields to delete.
  var toDelete = {};
  // tagsToRedraw is a list of tags that needs to be redrawn (to update element
  // IDs).
  var tagsToRedraw = [];
  // reColorTable is true if any field are completely deleted.
  var reColorTable = false;
  // Collect fields to be deleted in toDelete.
  $(checkedFieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2];
    if (!toDelete[tag]) {
      toDelete[tag] = {};
    }
    toDelete[tag][fieldPosition] = [];
    tagsToRedraw[tag] = true;
    reColorTable = true;
  });
  // Collect subfields to be deleted in toDelete.
  $(checkedSubfieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2], subfieldIndex = tmpArray[3];
    if (!toDelete[tag]) {
      toDelete[tag] = {};
      toDelete[tag][fieldPosition] = [subfieldIndex];
    }
    else {
      if (!toDelete[tag][fieldPosition])
        toDelete[tag][fieldPosition] = [subfieldIndex];
      else
        if (toDelete[tag][fieldPosition].length == 0)
          // Entire field scheduled for the deletion.
          return;
        else
          toDelete[tag][fieldPosition].push(subfieldIndex);
    }
  });

  // Assert that no protected fields are scheduled for deletion.
  var protectedField = containsProtectedField(toDelete);
  if (protectedField) {
    displayAlert('alertDeleteProtectedField', [protectedField]);
    updateStatus('ready');
    return;
    }

    // Create Ajax request.
    var data = {
  recID: gRecID,
  requestType: 'deleteFields',
  toDelete: toDelete
    };
    createReq(data, function(json){
  updateStatus('report', gRESULT_CODES[json['resultCode']]);
    });

  // Continue local updating.
  // Parse datastructure and delete accordingly in record.
  var fieldsToDelete, subfieldIndexesToDelete, field, subfields, subfieldIndex;
  for (var tag in toDelete) {
    fieldsToDelete = toDelete[tag];
    // The fields should be treated in the decreasing order (during the removal, indices may change)
    traversingOrder = [];
    for (fieldPosition in fieldsToDelete) {
      traversingOrder.push(fieldPosition);
    }
    // normal sorting will do this in a lexycographical order ! (problems if > 10 subfields
    // function provided, allows sorting in the reversed order
    traversingOrder = traversingOrder.sort(function(a, b){
      return b - a;
    });
    for (var fieldInd in traversingOrder) {
      fieldPosition = traversingOrder[fieldInd];
      var fieldID = tag + '_' + fieldPosition;
      subfieldIndexesToDelete = fieldsToDelete[fieldPosition];
      if (subfieldIndexesToDelete.length == 0)
        deleteFieldFromTag(tag, fieldPosition);
      else {
        // normal sorting will do this in a lexycographical order ! (problems if > 10 subfields
        subfieldIndexesToDelete.sort(function(a, b){
          return a - b;
        });
        field = gRecord[tag][fieldPosition];
        subfields = field[0];
        for (var j = subfieldIndexesToDelete.length - 1; j >= 0; j--)
          subfields.splice(subfieldIndexesToDelete[j], 1);
        var rowGroup = $('#rowGroup_' + fieldID);
      }
    }
  }

  // If entire fields has been deleted, redraw all fields with the same tag
  // and recolor the full table.
  for (tag in tagsToRedraw)
      redrawFields(tag);
  reColorFields();
}

function onMoveFieldUp(tag, fieldPosition) {
  if (failInReadOnly()){
    return;
  }
  fieldPosition = parseInt(fieldPosition);
  var thisField = gRecord[tag][fieldPosition];
  if (fieldPosition > 0) {
    var prevField = gRecord[tag][fieldPosition-1];
    // check if the previous field has the same indicators
    if ( cmpFields(thisField, prevField) == 0 ) {
      // Create Ajax request.
      var data = {
        recID: gRecID,
        requestType: 'moveField',
        tag: tag,
        fieldPosition: fieldPosition,
        direction: 'up'
      };
      createReq(data, function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']]);
      }, false);
      //continue updating locally
      gRecord[tag][fieldPosition] = prevField;
      gRecord[tag][fieldPosition-1] = thisField;
      $('tbody#rowGroup_'+tag+'_'+(fieldPosition-1)).replaceWith( createField(tag, thisField, fieldPosition-1) );
      $('tbody#rowGroup_'+tag+'_'+fieldPosition).replaceWith( createField(tag, prevField, fieldPosition) );
      reColorFields();
      $('#boxField_'+tag+'_'+(fieldPosition-1)).click();
    }
  }
}

function onMoveFieldDown(tag, fieldPosition) {
  if (failInReadOnly()){
    return;
  }
  fieldPosition = parseInt(fieldPosition);
  var thisField = gRecord[tag][fieldPosition];
  if (fieldPosition < gRecord[tag].length-1) {
    var nextField = gRecord[tag][fieldPosition+1];
    // check if the next field has the same indicators
    if ( cmpFields(thisField, nextField) == 0 ) {
      // Create Ajax request.
      var data = {
        recID: gRecID,
        requestType: 'moveField',
        tag: tag,
        fieldPosition: fieldPosition,
        direction: 'down'
      };
      createReq(data, function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']]);
      }, false);
      //continue updating locally
      gRecord[tag][fieldPosition] = nextField;
      gRecord[tag][fieldPosition+1] = thisField;
      $('tbody#rowGroup_'+tag+'_'+(fieldPosition+1)).replaceWith( createField(tag, thisField, fieldPosition+1) );
      $('tbody#rowGroup_'+tag+'_'+fieldPosition).replaceWith( createField(tag, nextField, fieldPosition) );
      reColorFields();
      $('#boxField_'+tag+'_'+(fieldPosition+1)).click();
    }
  }
}

// read-only mode related function

function updateInterfaceAccordingToMode(){
  /* updates the user interface (in particular the activity of menu buttons)
     accordingly to the surrent operation mode of BibEdit.
   */
  // updating the switch button caption
  if (gReadOnlyMode){
    deactivateRecordMenu();
    $('#btnSwitchReadOnly').attr("innerHTML", "R/W");
  } else {
    activateRecordMenu();
    $('#btnSwitchReadOnly').attr("innerHTML", "Read-only");
  }
}

function switchToReadOnlyMode(){
  // Moving to the read only mode with BibEdit

  if (gRecordDirty == true){
    alert("Please submit the record or cancel your changes before going to the read-only mode ");
    return false;
  }
  gReadOnlyMode = true;
  createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  gCacheMTime = 0;

  updateInterfaceAccordingToMode();
}

function canSwitchToReadWriteMode(){
  /*A function determining if at current moment, it is possible to switch to the read/write mode*/
  // If the revision is not the newest -> return false
  return true;
}

function switchToReadWriteMode(){
  // swtching to a normal editing mode of BibEdit
  if (!canSwitchToReadWriteMode()){
    alert("It is not possible to switch to the editing mode at the moment");
    return false;
  }

  gReadOnlyMode = false;
  // reading the record as if it was just opened
  getRecord(gRecID);
  updateInterfaceAccordingToMode();
}


function onSwitchReadOnlyMode(){
  // an event habdler being executed when user clicks on the switch to read only mode button
  if (gReadOnlyMode){
    switchToReadWriteMode();
  } else {
    switchToReadOnlyMode();
  }
}


// functions handling the revisions history

function getCompareClickedHandler(revisionId){
  return function(e){
    //document.location = "/record/merge/#recid1=" + gRecID + "&recid2=" + gRecID + "." + revisionId;
    comparisonUrl = "/record/edit/compare_revisions?recid=" +
      gRecID + "&rev1=" + gRecRev + "&rev2=" + revisionId;
    newWindow = window.open(comparisonUrl);
    newWindow.focus();
    return false;
  };
}

function onRevertClick(revisionId){
  /*
   * Handle 'Revert' button (submit record).
   */
  updateStatus('updating');
  if (displayAlert('confirmRevert')){
    createReq({recID: gRecID, revId: revisionId, requestType: 'revert',
         force: onSubmitClick.force}, function(json){
    // Submission was successful.
      changeAndSerializeHash({state: 'submit', recid: gRecID});
      var resCode = json['resultCode'];
      cleanUp(!gNavigatingRecordSet, '', null, true);
      updateStatus('report', gRESULT_CODES[resCode]);
      displayMessage(resCode);
      // clear the list of record revisions
      resetBibeditState()
    });
    onSubmitClick.force = false;
  }
  else
    updateStatus('ready');
  holdingPenPanelRemoveEntries(); // clearing the holding pen entries list
}

function getRevertClickedHandler(revisionId){
  return function(e){
      onRevertClick(revisionId);
      return false;
  };
}

function updateRevisionsHistory(){
  if (gRecRevisionHistory == null){
      return;
  }

  var result = "";
  var results = [];
  for (revInd in  gRecRevisionHistory){
    tmpResult = displayRevisionHistoryEntry(gRecID, gRecRevisionHistory[revInd]);
    tmpResult["revisionID"] = gRecRevisionHistory[revInd];
    results.push(tmpResult);
    result += tmpResult["HTML"];
  }

  $("#bibEditRevisionsHistory").attr("innerHTML", result);
  $(".bibEditRevHistoryEntryContent").bind("click", function(evt){
    var revision = $(this)[0].id.split("_")[1];
    updateStatus('updating');
    getRecord(gRecID, revision);
  });

  /*Attaching the actions on user interface*/
  for (resultInd in results){
    result = results[resultInd];
    $('#' + result['compareImgId']).bind("click", getCompareClickedHandler(result["revisionID"]));
    $('#' + result['revertImgId']).bind("click", getRevertClickedHandler(result["revisionID"]));
  }
}
