/*
 * This file is part of Invenio.
 * Copyright (C) 2009, 2010, 2011, 2012, 2013 CERN.
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
 *   - queue_request
 *   - save_changes
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
 *   - containsManagedDOI
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
 *   - onPreviewClick
 *   - onCancelClick
 *   - onCloneRecordClick
 *   - onDeleteRecordClick
 *   - onMergeClick
 *   - bindNewRecordHandlers
 *   - cleanUp
 *   - addHandler_autocompleteAffiliations
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
// Submission mode. Possible values are default and textmarc
var gSubmitMode = 'default';

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
var gRecRevisionHistory = [];
var gRecRevisionAuthors = {};
var gUndoList = []; // list of possible undo operations
var gRedoList = []; // list of possible redo operations

// number of bibcirculation copies from the retrieval time
var gPhysCopiesNum = 0;
var gBibCircUrl = null;

var gDisplayBibCircPanel = false;

// KB related variables
var gKBSubject = null;
var gKBInstitution = null;

// Does the record have a PDF attached?
var gRecordHasPDF = false;

// queue with all requests to be sent to server
var gReqQueue = [];

// last checkbox checked
var gLastChecked = null;

// last time a bulk request completed
var gLastRequestCompleted = new Date();

// last checkbox checked
var gLastChecked = null;

// Indicates if profiling is on
var gProfile = false;

// Log of all the actions effectuated by the user
var gActionLog = [];

/*
 * **************************** 2. Initialization ******************************
 */

window.onload = function(){
  if (typeof(jQuery) == 'undefined'){
    alert('ERROR: jQuery not found!\n\n' +
    'The Record Editor requires jQuery, which does not appear to be ' +
    'installed on this server. Please alert your system ' +
    'administrator.\n\nInstructions on how to install jQuery and other ' +
    "required plug-ins can be found in Invenio's INSTALL file.");
    var imgError = document.createElement('img');
    imgError.setAttribute('src', '/img/circle_red.png');
    var txtError = document.createTextNode('jQuery missing');
    var cellIndicator = document.getElementById('cellIndicator');
    cellIndicator.replaceChild(imgError, cellIndicator.firstChild);
    var cellStatus = document.getElementById('cellStatus');
    cellStatus.replaceChild(txtError, cellStatus.firstChild);
  }
};


function resize_content() {
  /*
   * Resize content table to always fit in the avaiable screen and not have two
   * different scroll bars
   */
  var bibedit_table_top = $("#bibEditContentTable").offset().top;
  var bibedit_table_height = Math.round(.93 * ($(window).height() - bibedit_table_top));
  bibedit_table_height = parseInt(bibedit_table_height, 10) + 'px';
  $("#bibEditContentTable").css('height', bibedit_table_height);
}

function init_bibedit() {
  /*
   * Initialize all components.
   */
  initMenu();
  initDialogs();
  initJeditable();
  initAjax();
  initMisc();
  createTopToolbar();
  initStateFromHash();
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
  initHotkeys();
  initClipboardLibrary();
  initClipboard();
  bindFocusHandlers();
  // Modify BibEdit content table height dinamically to avoid going over the
  // viewport
  resize_content();
  $(window).bind('resize', resize_content);
};


function failInReadOnly(){
  /** Function checking if the current BibEdit mode is read-only. In sucha a case, a warning
    dialog is displayed and true returned.
    If bibEdit is in read/write mode, false is returned
   */
  if (gReadOnlyMode === true){
    alert("It is impossible to perform this operation in the Read/Only mode. Please switch to Read-write mode before trying again");
    return true;
  }
  else{
    return false;
  }
}


function initClipboard(){
  // attaching the events -> handlers are stored in bibedit_engine.js file
  $(document).bind("copy", onPerformCopy);
  $(document).bind("paste", onPerformPaste);
}


function initDialogs(){
  /*
   * Overrides _makeDraggable from jQuery UI dialog code in order to allow
   * the dialog go off the viewport
   *
   */
   if (!$.ui.dialog.prototype._makeDraggableBase) {
    $.ui.dialog.prototype._makeDraggableBase = $.ui.dialog.prototype._makeDraggable;
    $.ui.dialog.prototype._makeDraggable = function() {
        this._makeDraggableBase();
        this.uiDialog.draggable("option", "containment", false);
    };
   }
}


/**
 * Error handler when deleting cache of the record
 */
function onDeleteRecordCacheError(XHR, textStatus, errorThrown) {
  console.log("Cannot delete record cache file");
  updateStatus('ready');
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
  window.onbeforeunload = function() {
    if (gRecID && ( gRecordDirty || gReqQueue.length > 0 )) {
      var data = {
        recID: gRecID,
        requestType: 'deactivateRecordCache',
      };

      $.ajaxSetup({async:false});
      queue_request(data);
      save_changes();
      $.ajaxSetup({async:true});

      msg = '******************** WARNING ********************\n' +
            '                  You have unsubmitted changes.\n\n' +
            'You may:\n' +
            ' * Submit (to save your changes permanently)\n      or\n' +
            ' * Cancel (to discard your changes)\n      or\n' +
            ' * Leave (your changes are saved)\n';

      //return msg;
    }
    else {
      createReq({recID: gRecID, requestType: 'deleteRecordCache'},
        function() {}, false, undefined, onDeleteRecordCacheError);
    }
  };

  //Initialising the BibCircualtion integration plugin
  $("#bibEditBibCirculationBtn").bind("click", onBibCirculationBtnClicked);
}


function initJeditable(){
  /*
   * Overwrite Jeditable plugin function to add the autocomplete handler
   * to textboxes corresponding to fields in gTagsToAutocomplete
   */

   $.editable.types['textarea'].element = function(settings, original) {
    var form = this;
    var textarea = $('<textarea />');

    if (settings.rows) {
        textarea.attr('rows', settings.rows);
    } else if (settings.height != "none") {
        textarea.height(settings.height);
    }
    if (settings.cols) {
        textarea.attr('cols', settings.cols);
    } else if (settings.width != "none") {
        textarea.width(settings.width - 6);
    }
    $(this).append(textarea);

    /* original variable is the cell that contains the textbox */
    var cell_id_split = $(original).attr('id').split('_');
    /* Set max amount of characters for the textarea */
    switch (cell_id_split[0]) {
      case 'fieldTag':
        max_char = "5";
        textarea.attr('maxlength', max_char);
        break;
      case 'subfieldTag':
        max_char = "1";
        textarea.attr('maxlength', max_char);
        break;
      default:
        max_char = "";
    }

    /* create subfield id corresponding to original cell */
    cell_id_split[0] = 'subfieldTag';
    var subfield_id = cell_id_split.join('_');

    /* Add autocomplete handler to fields in gTagsToAutocomplete */
    var fieldInfo = $(original).parents("tr").siblings().eq(0).children().eq(1).html();
    if ($.inArray(fieldInfo + $(original).siblings('#' + subfield_id).text(), gTagsToAutocomplete) != -1) {
        addHandler_autocompleteAffiliations(textarea);
    }

    initInputHotkeys(textarea, original);
    return(textarea);
  };

  $.editable.addInputType('textarea_custom', {
    element : $.editable.types.textarea.element,
    plugin  : function(settings, original) {
        $('textarea', this).bind('click', function(e) {
            e.stopPropagation();
        });

        $('textarea', this).bind('keydown', function(e) {
            var TABKEY = 9;
            var RETURNKEY = 13;

            switch (e.keyCode) {
              case RETURNKEY:
                // Just save field content
                e.stopPropagation();
                $(this).blur();
                break;
              case TABKEY:
                // Move between fields
                e.preventDefault();

                $(this).blur();

                var currentElementIndex = $(".tabSwitch:visible").index($(original));
                var step = e.shiftKey ? -1 : 1;
                $(".tabSwitch:visible").eq(currentElementIndex + step).click();
                break;
            }
        });

        $('textarea', this).keyup(function() {
          // Keep the limit of max chars for fields/subfields
          var max = parseInt($(this).attr('maxlength'));
          if( $(this).val().length > max ) {
              $(this).val($(this).val().substr(0, $(this).attr('maxlength')));
          }
        });
    }
  });
}

/*
 * **************************** 3. Ajax ****************************************
 */

function log_action(msg) {
    gActionLog.unshift(msg)
    gActionLog = gActionLog.slice(0, 200);
}

function initAjax(){
  /*
   * Initialize Ajax.
   */
  $.ajaxSetup(
    { cache: false,
      dataType: 'json',
      error: onAjaxError,
      type: 'POST',
      url: '/'+ gSITE_RECORD +'/edit/'
    }
  );
}

function createReq(data, onSuccess, asynchronous, deferred, onError) {
  /*
   * Create Ajax request.
   */
  data.action_log = gActionLog;

  if (typeof onError === "undefined") {
    onError = onAjaxError;
  }

  // Include and increment transaction ID.
  var tID = createReq.transactionID++;
  createReq.transactions[tID] = data['requestType'];
  data.ID = tID;

  // Include cache modification time if we have it.
  if (gCacheMTime) {
    data.cacheMTime = gCacheMTime;
  }

  var formdata = {jsondata: JSON.stringify(data)};
  if (gProfile) {
    formdata.ajaxProfile = true;
  }
  var ajax_options =  {data: formdata,
                      success: function(json) {
                          onAjaxSuccess(json, onSuccess);
                          if (deferred !== undefined) {
                            deferred.resolve(json);
                          }
                          if ( json['profilerStats']) {
                            $("#bibEditContent").after(json['profilerStats']);
                          }
                      },
                      error: onError};

  if (typeof asynchronous !== "undefined") {
    ajax_options.async = asynchronous;
  }

  // Send the request.
  $.ajax(ajax_options).done(function() {
    createReqAjaxDone(data);
  });
}
// Transactions data.
createReq.transactionID = 0;
createReq.transactions = [];

function createReqAjaxDone(data){
/*
 * This function is executed after the ajax request in createReq function was finished
 * data: the data parameter that was send with ajax request
 */
  // If the request was from holding pen, trigger the event to apply holding pen changes
  if (data['requestType'] == 'getHoldingPenUpdates') {
    $.event.trigger('HoldingPenPageLoaded');
  }
}


/**
 * Error handler for AJAX bulk requests
 * @param  {object} data - object describing all operations to be done
 * @return {function}      function to be used as error handler
 */
function onBulkReqError(data) {
  return function (XHR, textStatus, errorThrown) {
            gLastRequestCompleted = new Date();
            console.log("Error while processing:");
            console.log(data);
            updateStatus("ready");
          };
}


function createBulkReq(reqsData, onSuccess, optArgs){
  /* optArgs is a disctionary containning the optional arguments
     possible keys include:
       asynchronous : if the request should be asynchronous
       undoRedo : handler for the undo operation
  */
    // creating a bulk request ... the cache timestamp is not saved

    var data = {'requestType' : 'applyBulkUpdates',
                 'requestsData' : reqsData,
                 'recID' : gRecID};
    if (optArgs.undoRedo != undefined){
        data.undoRedo = optArgs.undoRedo;
    }

    var errorCallback = onBulkReqError(data);

    createReq(data, onSuccess, optArgs.asynchronous, undefined, errorCallback);
}


function onAjaxError(XHR, textStatus, errorThrown){
  /*
   * Handle Ajax request errors.
   */
  console.log('Request completed with status ' + textStatus +
    '\nResult: ' + XHR.responseText +
    '\nError: ' + errorThrown);
  updateStatus('ready');
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
    window.location = recID ? gSITE_URL + '/'+ gSITE_RECORD +'/' + recID + '/edit/'
      : gSITE_URL + '/'+ gSITE_RECORD +'/edit/';
    return;
  }
  else if ($.inArray(resCode, [101, 102, 104, 105, 106, 107, 108, 109, 111]) != -1) {
    cleanUp(!gNavigatingRecordSet, null, null, true, true, false);
    args = [];
    if (resCode == 104) {
      args = json["locked_details"];
    }
    displayMessage(resCode, false, args);
    if (resCode == 107) {
      $('#lnkGetRecord').bind('click', function(event){
        getRecord(recID, undefined, undefined);
        event.preventDefault();
      });
    }
    updateStatus('error', gRESULT_CODES[resCode]);
  }
  else if ($.inArray(resCode, [110, 113]) != -1){
    displayMessage(resCode, true, [json['errors'].toString()]);
    /* Warn the user leaving toolbar active */
    updateStatus('error', gRESULT_CODES[resCode], true);
  }
  else {
    var cacheOutdated = json['cacheOutdated'];
    var requestType = createReq.transactions[json['ID']];
    if (cacheOutdated && requestType == 'submit') {
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
    else {
      if (requestType != 'getRecord') {
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
          activateSubmitButton();
        }
      }
      if (onSuccess) {
        // No critical errors; call onSuccess function.
        onSuccess(json);
      }
    }
  }
}

function queue_request(data) {
  /* Adds the request data to the global request queue for later
  execution */

  if ($('#btnSubmit').is(":disabled")) {
    activateSubmitButton();
  }
  /* Create a deep copy of the data to avoid being manipulated
  by other requests */
  gReqQueue.push(jQuery.extend(true, {}, data));

  var currentDate = new Date();
  var dateDiff = (currentDate - gLastRequestCompleted) / 1000;

  /* Only save the changes if the last request completed more than 5 sec ago */
  if ( gLastRequestCompleted && dateDiff > 5 ) {
    save_changes();
  }
}

function save_changes() {
  /* Sends all pending requests in bulk to the server
  Returns deferred object to be able to notify when saving is done
  */
  var optArgs = {};
  var saveChangesPromise = new $.Deferred();

  if (gReqQueue.length > 0) {
    updateStatus('saving');
    gLastRequestCompleted = null;
    createBulkReq(gReqQueue, function(json) {
      gLastRequestCompleted = new Date();
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
      updateStatus('ready');
      saveChangesPromise.resolve();
    }, optArgs);

    gReqQueue = [];
  }
  else {
    saveChangesPromise.resolve();
  }

  return saveChangesPromise;
}


function resetBibeditState(){
  /* A function clearing the state of the bibEdit (all the panels content)
  */
  gHoldingPenLoadedChanges = {};
  gHoldingPenChanges = [];
  gDisabledHpEntries = {};
  gReadOnlyMode = false;
  gRecRevisionHistory = [];
  gRecRevisionAuthors = {};
  gUndoList = [];
  gRedoList = [];
  gPhysCopiesNum = 0;
  gBibCircUrl = null;
  gManagedDOIs = [];

  clearWarnings();
  updateRevisionsHistory();
  updateUrView();
  updateBibCirculationPanel();
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
  var profile = gHashParsed.profile;
  if (profile) gProfile = true;

  // Find out which internal state the new hash leaves us with
  if ( tmpState && tmpRecID ) {
    // We have both state and record ID.
    if ($.inArray(tmpState, ['edit', 'submit', 'cancel', 'deleteRecord', 'hpapply']) != -1) {
      gState = tmpState;
    }
    else {
      // Invalid state, fail...
      return;
    }
  }
  else if ( tmpState ) {
    // We only have state.
    if ( tmpState == 'edit' ) {
      gState = 'startPage';
    }
    else if ( tmpState == 'newRecord' ) {
      gState = 'newRecord';
    }
    else if ( tmpState == 'search' ) {
      gState = "search";
    }
    else {
      // Invalid state, fail... (all states but 'edit' and 'newRecord' are
      // illegal without record ID).
      return;
    }
  }
  else
    // Invalid hash, fail...
    return;

  if (gState != gPrevState || (gState == 'edit' && parseInt(tmpRecID, 10) != gRecID) || // different record number
    (tmpRecRev != undefined && tmpRecRev != gRecRev) || // different revision
    (tmpRecRev == undefined && gRecRev != gRecLatestRev) || // latest revision requested but another open
    (tmpReadOnlyMode != gReadOnlyMode)){ // switched between read-only and read-write modes

    // We have an actual and legal change of state. Clean up and update the
    // page.
    updateStatus('updating');
    if ( gRecID && !gRecordDirty && !tmpReadOnlyMode ) {
      // If the record is unchanged, delete the cache.
      createReq({recID: gRecID, requestType: 'deleteRecordCache'}, function() {},
                true, undefined, onDeleteRecordCacheError);
    }
    switch (gState) {
      case 'startPage':
        cleanUp(true, '', 'recID', true, true);
        updateStatus('ready');
        break;
      case 'edit':
        var recID = parseInt(tmpRecID, 10);
        if ( isNaN(recID) ) {
          // Invalid record ID.
          cleanUp(true, tmpRecID, 'recID', true);
          displayMessage(102);
          updateStatus('error', gRESULT_CODES[102]);
        }
        else {
          cleanUp(true, recID, 'recID');
          gReadOnlyMode = tmpReadOnlyMode;
            if (tmpRecRev != undefined && tmpRecRev != 0) {
              getRecord(recID, tmpRecRev);
            } else {
              getRecord(recID);
            }
        }
        break;
      case 'hpapply':
        var hpID = parseInt(gHashParsed.hpid, 10);
        var recID = parseInt(tmpRecID, 10);
        if (isNaN(recID) || isNaN(hpID)){
          // Invalid record ID or HoldingPen ID.
          cleanUp(true, tmpRecID, 'recID', true);
          displayMessage(102);
          updateStatus('error', gRESULT_CODES[102]);
        }
        else {
          cleanUp(true, recID, 'recID');
          gReadOnlyMode = tmpReadOnlyMode;
          var hpButton = '#bibeditHPApplyChange' + hpID;
          // after the record is created and all the data on the page is loaded
          // trigger the click on holdingPen button
          $(document).one('HoldingPenPageLoaded', function () {
            $(hpButton).click();
          });
          getRecord(recID);
        }
        break;
      case 'search':
        cleanUp(true, '', null, null, true);
        var search_pattern = gHashParsed.p;
        if ( typeof search_pattern !== "undefined" ) {
          // There is a pattern to seach for
          createReq({requestType: 'searchForRecord', searchType: 'anywhere',
      searchPattern: search_pattern}, onSearchForRecordSuccess);
        }
        updateStatus('ready');
        break;
      case 'newRecord':
        cleanUp(true, '', null, null, true);
        displayNewRecordScreen();
        bindNewRecordHandlers();
        updateStatus('ready');
        break;
      case 'submit':
        cleanUp(true, '', null, true);
        displayMessage(4);
        updateStatus('ready');
        break;
      case 'cancel':
        cleanUp(true, '', null, true, true);
        updateStatus('ready');
        break;
      case 'deleteRecord':
        cleanUp(true, '', null, true);
        displayMessage(10);
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
  log_action("deleteFieldFromTag " + tag + ' ' + fieldPosition)
  var field = gRecord[tag][fieldPosition];
  var fields = gRecord[tag];
  for (var change in gHoldingPenChanges) {
      // If deleted field contains a HP change then mark change as applied or decrease the field position
      if ((gHoldingPenChanges[change]["tag"] == tag)) {  // TODO add indicators
            if (gHoldingPenChanges[change]["field_position"] == fieldPosition) {
              // there are more changes associated with this field ! They are no more correct
              // and should be removed... it is also possible to consider transforming them into add field
              // change, but seems to be an unnecessary effort
              gHoldingPenChanges[change].applied_change = true;
            }
            else if (gHoldingPenChanges[change]["field_position"] > fieldPosition) {
              gHoldingPenChanges[change]["field_position"] -= 1;
            }
        }
  }
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
    record[fieldId] = [newField];
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
   * New data structure is an object with the following levels:
   * -Tag (Object)
   *  -Indicators (Array)
   *     -FieldIndex (Array)
   *       -0-FieldContent (Array)
   *         -SubfieldIndex (Array)
   *           -0-SubfieldTag
   *           -1-SubfieldContent
   *       -1-FieldPosition
   * */
  result = {};
  for (fieldId in record){
    result[fieldId] = {};
    indicesList = []; // a list of all the indices ... utilised later when determining the positions
    for (fieldIndex in record[fieldId]){

      indices =  "";
      if (record[fieldId][fieldIndex][1] == ' '){
        indices += "_";
      }else{
        indices += record[fieldId][fieldIndex][1];
      }

      if (record[fieldId][fieldIndex][2] == ' '){
        indices += "_";
      }else{
        indices += record[fieldId][fieldIndex][2];
      }

      if (result[fieldId][indices] == undefined){
        result[fieldId][indices] = []; // a future list of fields sharing the same indice
        indicesList.push(indices);
      }
      result[fieldId][indices].push([record[fieldId][fieldIndex][0], 0]);
    }

    // now calculating the positions within a field identifier ( utilised on the website )

    position = 0;

    indices = indicesList;
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

/**
 * Function called when we want to find all the pairs of fields having the same content
 * @param  {number} tag
 * @param  {String} indicators
 * @param  {Array} fields1 : fields that belong to the tag+indicator from gRecord
 * @param  {Array} fields2 : fields that belong to the tag+indicator from HP record
 * @return {Dictionary} : includes pairs of the field positions of the same fields found.
 * Key is the position of the 1st field inside the fields1 set and
 * value is the position of the 2nd field inside the fiels2 set.
 */
function findSameFields(tag, indicators, fields1, fields2) {
  /* Iterates over fields1 and searches for same fields inside the 2nd set.
   * In case of volatile fields we create a pair with -1.
   * E.g if first field of fields1 has same structure and content with 3rd field of fields2
   * then we add the pair '0 : 2' to the dictionary.
   * If 2nd field of fields1 is volatile we add the pair '1 : -1' to the dictionary
  */
  var sameFields = {};

  for (var fieldIndex1 in fields1) {
      // check if field contains only volatile fields
      var isVolatile = true;
      for (var sfIndex in fields1[fieldIndex1][0]) {
        if (fields1[fieldIndex1][0][sfIndex][1].substring(0,9) != "VOLATILE:"){
          isVolatile = false;
          break;
        }
      }
      // In case of volatile fields we create a pair with -1, so that the volatile
      // fields are ignored from the comparison algorithm.
      if (isVolatile) {
        sameFields[fieldIndex1] = -1;
      }
      else {
          for (var fieldIndex2 in fields2) {
              // check if field to compare with is already inside sameFields dictionary
              fieldIsPaired = false;
              for (var key in sameFields) {
                if (sameFields[key] == fieldIndex2){
                  fieldIsPaired = true;
                  break;
                }
              }
              if (fieldIsPaired)
                continue;
              var isSame = true;
              // if fields have different amount of subfields are not same
              if ( fields1[fieldIndex1][0].length != fields2[fieldIndex2][0].length ) {
                isSame =false;
                continue;
              }
              for (var sfPos1 in fields1[fieldIndex1][0]) {
                      if (fields2[fieldIndex2][0][sfPos1][0] != fields1[fieldIndex1][0][sfPos1][0] ){
                          isSame = false;
                          break;
                      }
                      if (fields2[fieldIndex2][0][sfPos1][1].toLowerCase() != fields1[fieldIndex1][0][sfPos1][1].toLowerCase() ){
                          isSame = false;
                          break;
                      }
              }
              if (isSame) {
                sameFields[fieldIndex1] = fieldIndex2;
                break;
              }
          }
      }
  }
  return sameFields;
}

/**
 * Function called when we want to compare two different fields
 * @param  {number} tag
 * @param  {String} indicators
 * @param  {number} fieldIndex : the field index of the field1
 * @param  {Array} field1 : field that belongs to gRecord
 * @param  {Array} field2 : field that belongs to HP record
 * @return {List of objects} : Objects repesent a change detected between the 2 records
 */
function compareFields(tag, indicators, fieldIndex, field1, field2){
  /*
   * Compares the structure and content of 2 fields.
   */
  result = [];
  for (var sfIndex in field2){
    if (field1[sfIndex] == undefined){
      //  adding the subfield at the end of the record can be treated in a more graceful manner
      result.push(
          {"change_type" : "subfield_added",
           "tag" : tag,
           "indicators" : indicators,
           "field_position" : fieldIndex,
           "subfield_code" : field2[sfIndex][0],
           "subfield_content" : field2[sfIndex][1]});
    }
    else
    {
      // the subfield exists in both the records
      if (field1[sfIndex][0] != field2[sfIndex][0] || ((field1[sfIndex][0] == field2[sfIndex][0]) &&
         (field1[sfIndex][1].substring(0,9) == "VOLATILE:") && (field2[sfIndex][1].substring(0,9) != "VOLATILE:"))){
      //  Differrent subfield codes: a structural change ... we replace the entire field
        return [{"change_type" : "field_changed",
           "tag" : tag,
           "indicators" : indicators,
           "field_position" : fieldIndex,
           "field_content" : field2}];
      } else
      {
        // in case where gRecord's subfield is normal and HP record's subfield is volatile ignore it
        if ( (field1[sfIndex][1].toLowerCase() != field2[sfIndex][1].toLowerCase()) && (field2[sfIndex][1].substring(0,9) != "VOLATILE:")){
          result.push({"change_type" : "subfield_changed",
            "tag" : tag,
            "indicators" : indicators,
            "field_position" : fieldIndex,
            "field_content" : field2,
            "subfield_position" : sfIndex,
            "subfield_code" : field2[sfIndex][0],
            "subfield_content" : field2[sfIndex][1]});

        }
        // in case where both gRecord's and HP record's subfield is volatile ignore them
        else if ( (field1[sfIndex][1].toLowerCase() == field2[sfIndex][1].toLowerCase()) && (field1[sfIndex][1].substring(0,9) != "VOLATILE:")) {
          result.push({"change_type" : "subfield_same",
            "tag" : tag,
            "indicators" : indicators,
            "field_position" : fieldIndex,
            "subfield_position" : sfIndex,
            "subfield_code" : field2[sfIndex][0],
            "subfield_content" : field2[sfIndex][1]});
        }
      }
    }
  }

  if ( gSHOW_HP_REMOVED_FIELDS == 1) {
    for (sfIndex in field1){
      if (field2[sfIndex] == undefined){
        result.push({"change_type" : "subfield_removed",
                  "tag" : tag,
                  "indicators" : indicators,
                  "field_position" : fieldIndex,
                  "subfield_position" : sfIndex});
      }
    }
  }

  return result;
}

/**
 * Function called when we want to compare the contents of a tag contained in both records
 * @param  {number} tag
 * @param  {String} indicators
 * @param  {Array} fields1 : fields that belong to the tag+indicator from gRecord
 * @param  {Array} fields2 : fields that belong to the tag+indicator from HP record
 * @return {List of objects} : Objects repesent a change detected between the 2 records
 */
function compareTag(tag, indicators, fields1, fields2){
   /* It fully compares the given's tag+indicator's fields from 2 different records
    */
  result = [];

  /* First we find all the pairs of fields containing the same content
   * from the 2 sets of fields.
   */

  var sameFields = findSameFields(tag, indicators, fields1, fields2);

  // Then we call compareFields for every pair of same fields in order to produce the
  // 'same content' changes.
  for (var key in sameFields) {
          if (sameFields[key] != -1)
            result = result.concat(compareFields(tag, indicators, fields1[key][1], fields1[key][0], fields2[sameFields[key]][0]));
  }

  // We iterate over the fields2.
  // If the field is volatile we ignore it.
  // If it is contained inside the sameFields dictionary we have to compare it with the
  // related field from fields1
  // If it is not, we iterate over the fields1 set until we find an available to be compared field
  // (a field that is not contained in the sameFields) and we compare them.
  // If we don't find an available field then we create a change with type "field_added"

  for (var fieldIndex2 in fields2) {
      var isVolatile = true;
      for (var sfIndex in fields2[fieldIndex2][0]) {
        if (fields2[fieldIndex2][0][sfIndex][1].substring(0,9) != "VOLATILE:"){
          isVolatile = false;
          break;
        }
      }
      // if field is volatile ignore it
      if (isVolatile)
        continue;
      var fieldIndex = -1;
      for (var key in sameFields) {
          if (sameFields[key] == fieldIndex2){
            fieldIndex = key;
            break;
          }
      }
      // if field is contained as value in sameFields ignore it
      if (fieldIndex != -1) {
        continue;
      }
      else {
          // try to find an available field to be compared with
          var isCompared = false;
          for (var fieldIndex1 in fields1) {
              if (sameFields[fieldIndex1] == undefined ) {
                  result = result.concat(compareFields(tag, indicators, fields1[fieldIndex1][1], fields1[fieldIndex1][0], fields2[fieldIndex2][0]));
                  isCompared = true;
                  // add this pair to sameFields dictionary in order neither of these fields to be compared with another field in next steps
                  sameFields[fieldIndex1] = fieldIndex2;
                  break;
              }
          }
          if (isCompared == false) {
              result.push({"change_type" : "field_added",
                    "tag" : tag,
                    "indicators" : indicators,
                    "field_content" : fields2[fieldIndex2][0]});
          }
      }
  }
  return result;
}

/**
 * Function called when a HP change set is applied
 * @param  {BibRecord} record1 : gRecord
 * @param  {BibRecord} record2 : Holding Pen record
 * @return {List of objects} : Objects repesent a change detected between the 2 records
 */
function compareRecords(record1, record2){
  /* Compares two bibrecords, producing a list of atom changes that can be displayed
   * to the user if for example applying the Holding Pen change
   * 1) This is more convenient to have a different structure of the storage
   */
  r1 = transformRecord(record1); // gRecord
  r2 = transformRecord(record2); // Holding Pen record
  result = [];

  for (tag in r2){
    if (r1[tag] == undefined){  // if this tag doesn't exist in r1
      for (indicators in r2[tag]){
        for (fieldIndex in r2[tag][indicators]){
          result.push({"change_type" : "field_added",
                        "tag" : tag,
                        "indicators" : indicators,
                        "field_content" : r2[tag][indicators][fieldIndex][0]});


        }
      }
    }
    else
    {
      for (indicators in r2[tag]){
        if (r1[tag][indicators] == undefined){
          for (fieldIndex in r2[tag][indicators]){
            result.push({"change_type" : "field_added",
                         "tag" : tag,
                         "indicators" : indicators,
                         "field_content" : r2[tag][indicators][fieldIndex][0]});


          }
        }
        else{
          result = result.concat(compareTag(tag, indicators,
              r1[tag][indicators], r2[tag][indicators]));
        }
      }

      if ( gSHOW_HP_REMOVED_FIELDS == 1) {
        for (indicators in r1[tag]){
          if (r2[tag][indicators] == undefined){
            for (fieldIndex in r1[tag][indicators]){
              fieldPosition = r1[tag][indicators][fieldIndex][1];
               result.push({"change_type" : "field_removed",
                    "tag" : tag,
                    "field_position" : fieldPosition});
            }

          }
        }
      }

    }
  }

  if ( gSHOW_HP_REMOVED_FIELDS == 1) {
    for (tag in r1){
      if (r2[tag] == undefined){
        for (indicators in r1[tag]){
          for (fieldIndex in r1[tag][indicators])
          {
            // field position has to be calculated here !!!
            fieldPosition = r1[tag][indicators][fieldIndex][1]; // field position inside the mark
            result.push({"change_type" : "field_removed",
                         "tag" : tag,
                         "field_position" : fieldPosition});

          }
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

function containsHPAffectedField(fieldData){
  /*
   * Determine if a field data structure contains affected from HP elements (useful
   * when checking if a deletion command is valid).
   * The data structure must be an object with the following levels
   * - Tag
   *   - Field position
   *     - Subfield index
   */
   // First find all fields and their position containing subfield changed in Holding Pen
  var fieldPositions, subfieldIndexes;
  var hpTags = {};
  for (var changePos in gHoldingPenChanges) {
      var change = gHoldingPenChanges[changePos];
      if ( (change["change_type"] == "field_changed" || change["change_type"] == "subfield_changed") &&
            change["applied_change"] != true ) {
        if ( hpTags[change["tag"]] == undefined ) {
            hpTags[change["tag"]] = [change["field_position"]];
        }
        else {
            hpTags[change["tag"]].push(change["field_position"]);
        }
      }
  }
  // For every field selected to be deleted check if it exists in hpTags dictionary
  for (var type in fieldData) {
    fields = fieldData[type];
    for (var field in fields){
      if ( hpTags[field] != undefined ) {
        var field_positions = hpTags[field];
        subfieldIndexes = fields[field];
        var keys = Object.keys(subfieldIndexes);
        for (var i=0, l=keys.length; i<l; i++){
            for (var j=0, m=field_positions.length; j<m; j++){
                if ( keys[i] == field_positions[j] ) {
                  return field;
                }
            }
        }
      }
    }
  }
  return false;
}

function containsManagedDOI(fieldData){
  /*
   * Determine if a field data structure contains DOIs managed by this
   * site (useful to ask confirmation to the user).
   * The data structure must be an object with the following levels
   * - Tag
   *   - Field position
   *     - Subfield index
   */
    var data_for_fieldtype, tags, y, fields, subfields, subfieldvalue;
    var managed_dois_in_fields = new Array();

    if (typeof gDOILookupField === 'undefined') {
	return false;
    }

    for (var fieldtype in fieldData){
	data_for_fieldtype = fieldData[fieldtype];
	for (var tag in data_for_fieldtype){
	    if (tag == gDOILookupField.substring(0,3)) {
		fieldPositions = data_for_fieldtype[tag];
		for (var fieldPosition in fieldPositions){
		    fields = fieldPositions[fieldPosition];
		    if (fieldtype == 'fields') {
			/* in the case of datafields, ignore info
			 * about indicators & co. Just keep the list
			 * of fields */
			fields = [fields[0]]
		    }
		    for (var subfieldPosition in fields){
			subfields = fields[subfieldPosition]
			if (fieldtype == 'subfields') {
			    subfields = [subfields]
			}
			for (var subfield in subfields) {
			    subfieldcode = subfields[subfield][0]
			    subfieldvalue = subfields[subfield][1]
			    if (subfieldcode == gDOILookupField.substring(5,6) && gManagedDOIs.indexOf(subfieldvalue) != -1) {
				managed_dois_in_fields.push(subfieldvalue)
			    }
			}
		    }
		}
	    }
	}
    }

  if (managed_dois_in_fields.length > 0){
    return managed_dois_in_fields
  } else {
    return false;
  }
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
  return MARC.charAt(5);
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
validMARC.reIndicator1 = /[\da-zA-Z]{1}/;
validMARC.reIndicator2 = /[\da-zA-Z]{1}/;
//validMARC.reSubfieldCode = /[\da-z!&quot;#$%&amp;'()*+,-./:;&lt;=&gt;?{}_^`~\[\]\\]{1}/;
validMARC.reSubfieldCode = /[\da-z!&quot;#$%&amp;'()*+,-.\/:;&lt;=&gt;?{}_^`~\[\]\\]{1}/;

/*
 * **************************** 6. Record UI ***********************************
 */

function onNewRecordClick(event){
  /*
   * Handle 'New' button (new record).
   */
  log_action("onNewRecordClick")
  updateStatus('updating');
  if ( gRecordDirty || gReqQueue.length > 0 ) {
    if (!displayAlert('confirmLeavingChangedRecord')){
      updateStatus('ready');
      event.preventDefault();
      return;
    }
  }
  else {
    // If the record is unchanged, erase the cache.
    if (gReadOnlyMode == false) {
      createReq({recID: gRecID, requestType: 'deleteRecordCache'}, function() {},
                true, undefined, onDeleteRecordCacheError);
    }
  }

  changeAndSerializeHash({state: 'newRecord'});
  cleanUp(true, '');
  displayNewRecordScreen();
  bindNewRecordHandlers();
  updateStatus('ready');
  updateToolbar(false);

  event.preventDefault();
}


function onTemplateRecordClick(event){
    /* Handle 'Template management' button */
    log_action("onTemplateRecordClick");
    var template_window = window.open('/record/edit/templates', '', 'resizeable,scrollbars');
    template_window.document.close(); // needed for chrome and safari
}


/**
 * Error handler when opening a record
 */
function onGetRecordError() {
  var msg = "<em>Error</em>: record cannot be opened. <br /><br /> \
            If the problem persists, contact the site admin."

  displayMessage(undefined, false, [msg]);
  updateStatus("ready");
}


function getRecord(recID, recRev, onSuccess, args){
  /* A function retrieving the bibliographic record, using an AJAX request.
   *
   * recID : the identifier of a record to be retrieved from the server
   * recRev : the revision of the record to be retrieved (0 or undefined
   *          means retrieving the newest version )
   * onSuccess : The callback to be executed upon retrieval. The default
   *             callback loads the retrieved record into the bibEdit user
   *             interface
   */
  log_action("getRecord recid:" + recID + " " + "recRev:" + recRev);
  /* Make sure the record revision exists, otherwise default to current */
  if ($.inArray(recRev, gRecRevisionHistory) === -1) {
    recRev = 0;

  }

  /* If we are changing recids always change to write mode */
  if ( recID != gRecID ) {
    gReadOnlyMode = false;
  }

  if (typeof onSuccess === 'undefined') {
    onSuccess = onGetRecordSuccess;
  }

  if (recRev != undefined && recRev != 0){
    changeAndSerializeHash({state: 'edit', recid: recID, recrev: recRev});
  }
  else{
    changeAndSerializeHash({state: 'edit', recid: recID});
  }

  gRecIDLoading = recID;

  reqData = {recID: recID,
             requestType: 'getRecord',
             deleteRecordCache: getRecord.deleteRecordCache,
             clonedRecord: getRecord.clonedRecord,
             inReadOnlyMode: gReadOnlyMode};

  $.extend(reqData, args);

  if (recRev != undefined && recRev != 0) {
    reqData.recordRevision = recRev;
    if (recRev === gRecLatestRev) {
      reqData.inReadOnlyMode = false;
    }
    else {
      reqData.inReadOnlyMode = true;
    }
  }

  resetBibeditState();
  createReq(reqData, function(json) {
      onSuccess(json);
      // reloading the Holding Pen toolbar
      onHoldingPenPanelRecordIdChanged(recID);
  }, true, undefined, onGetRecordError);

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
  log_action("onGetRecordSuccess");
  cleanUp(!gNavigatingRecordSet);
  // Store record data.
  gRecID = json['recID'];
  gRecIDLoading = null;
  gRecRev = json['recordRevision'];
  gRecRevAuthor = json['revisionAuthor'];
  gPhysCopiesNum = json['numberOfCopies'];
  gBibCircUrl = json['bibCirculationUrl'];
  gDisplayBibCircPanel = json['canRecordHavePhysicalCopies'];
  gRecordHasPDF = json['record_has_pdf']
  gRecordHideAuthors = json['record_hide_authors']
  gManagedDOIs = json['managed_DOIs']

  // Get KB information
  gKBSubject = json['KBSubject'];
  gKBInstitution = json['KBInstitution'];
  var revDt = formatDateTime(getRevisionDate(gRecRev));
  var recordRevInfo = "record revision: " + revDt;
  var revAuthorString = gRecRevAuthor;
  $('.revisionLine').html(recordRevInfo + ' ' + revAuthorString)
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
      $('#bibEditMessage').html('');
      event.preventDefault();
    });
  }

  gHoldingPenChanges = json['pendingHpChanges'];
  gDisabledHpEntries = json['disabledHpChanges'];
  gHoldingPenLoadedChanges = {};

  updateBibCirculationPanel();

  // updating the undo/redo lists
  gUndoList = json['undoList'];
  gRedoList = json['redoList'];
  updateUrView();

  displayRecord();
  // Activate menu record controls.
  activateRecordMenu();

  // the current mode should is indicated by the result from the server
  gReadOnlyMode = (json['inReadOnlyMode'] != undefined) ? json['inReadOnlyMode'] : false;
  gRecLatestRev = (json['lastRevision'] != undefined) ? json['lastRevision'] : null;
  gRecRevisionHistory = (json['revisionsHistory'] != undefined) ? json['revisionsHistory'] : null;
  gRecRevisionAuthors = (json['revisionsAuthors'] != undefined) ? json['revisionsAuthors'] : null;

  if (json["resultCode"] === 103) {
    gReadOnlyMode = true;
    displayMessage(json["resultCode"], true);
  }

  updateInterfaceAccordingToMode();

  if (gRecordDirty){
    activateSubmitButton();
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
  adjustGeneralHPControlsVisibility();
  $("#loadingTickets").show();
  createReq({recID: gRecID, requestType: 'getTickets'}, onGetTicketsSuccess);

  // Refresh top toolbar
  updateToolbar(false);
  updateToolbar(true);
}


function onGetTemplateSuccess(json) {
  onGetRecordSuccess(json);
}


function onSubmitPreviewSuccess(dialogPreview, html_preview){
  /*
   * Confirm whether to submit the record
   *
   * dialog: object containing the different parts of the modal dialog
   * html_preview: a formatted preview of the record content
  */
  log_action("onSubmitPreviewSuccess");
  updateStatus('ready');
  addContentToDialog(dialogPreview, html_preview, "Do you want to submit the record?");
  dialogPreview.dialogDiv.dialog({
        title: "Confirm submit",
        close: function() { updateStatus('ready'); $('#btnSubmit').prop('disabled', false);},
        buttons: {
            "Submit changes": function() {
                        var reqData = {
                                      recID: gRecID,
                                      force: onSubmitClick.force,
                                      requestType: 'submit'
                                      };
                        if (gSubmitMode == "textmarc") {
                          reqData.requestType = 'submittextmarc';
                          reqData.textmarc = $('#textmarc_textbox').val();
                        }
                        createReq(reqData, function(json) {
                            var resCode = json['resultCode'];
                            if (resCode == 115) {
                              // There was a textmarc parsing error
                              displayMessage(resCode, true, json["parse_error"]);
                              updateStatus('ready');
                            }
                            else {
                              // Submission was successful.
                              changeAndSerializeHash({state: 'submit', recid: gRecID});
                              updateStatus('report', gRESULT_CODES[resCode]);
                              cleanUp(!gNavigatingRecordSet, '', null, !gNavigatingRecordSet, false);
                              updateToolbar(false);
                              resetBibeditState();
                              displayMessage(resCode, false, [json['recID'], json["new_cnum"]]);
                              updateStatus('ready');
                            }
                        });
                        $( this ).remove();
                    },
            Cancel: function() {
                        updateStatus('ready');
                        $('#btnSubmit').prop('disabled', false);
                        $( this ).remove();
                    }
    }});
  // Focus on the submit button
  $(dialogPreview.dialogDiv).parent().find('button:nth-child(1)').focus();
}


function saveOpenedFields() {
  /* Performs the following tasks:
   * - Remove volatile content from field templates
   * - Save opened content from field templates
   * - Save opened textareas
   * returns: promise with state of all tasks to perform
   */
  function removeVolatileContentFieldTemplates(removingVolatilePromise) {
    /* Deletes volatile fields from field templates */
    $(".bibEditVolatileSubfield:input").each(function() {
      var deleteButtonSelector = $(this).parent().parent().find('img[id^="btnAddFieldRemove_"]');
      if (deleteButtonSelector.length === 0) {
        /* It is the first element on the field template */
        $(this).parent().parent().find(".bibEditCellAddSubfieldCode").remove();
        $(this).remove();
      }
      else {
        deleteButtonSelector.click();
      }
    });
    removingVolatilePromise.resolve();
  }

  function removeEmptyFieldTemplates(removingEmptyFieldTemplatePromise) {
    var addFieldInterfaceSelector = $("tbody[id^=rowGroupAddField_]");
    addFieldInterfaceSelector.each(function() {
      var addSubfieldSelector = $(this).find(".bibEditCellAddSubfieldCode");
      if (addSubfieldSelector.length === 0) {
        /* All input have been previously removed */
        addFieldInterfaceSelector.remove();
      }
    });
    removingEmptyFieldTemplatePromise.resolve();
  }

  function saveFieldTemplatesContent(savingFieldTemplatesPromise) {
    /* Triggers click event on all open field templates */
    $(".bibEditTxtValue:input:not(.bibEditVolatileSubfield)").trigger($.Event( 'keyup', {which:$.ui.keyCode.ENTER, keyCode:$.ui.keyCode.ENTER}));
    savingFieldTemplatesPromise.resolve();
  }

  function saveOpenedTextareas(savingOpenedTextareasPromise) {
    /* Saves textareas if they are opened */
    $(".edit_area textarea").trigger($.Event( 'keydown', {which:$.ui.keyCode.ENTER, keyCode:$.ui.keyCode.ENTER}));
    savingOpenedTextareasPromise.resolve();
  }

  var removingVolatilePromise = new $.Deferred();
  var removingEmptyFieldTemplatePromise = new $.Deferred();
  var savingFieldTemplatesPromise = new $.Deferred();
  var savingOpenedTextareasPromise = new $.Deferred();

  removeVolatileContentFieldTemplates(removingVolatilePromise);
  removeEmptyFieldTemplates(removingEmptyFieldTemplatePromise);
  saveFieldTemplatesContent(savingFieldTemplatesPromise);
  saveOpenedTextareas(savingOpenedTextareasPromise);

  var savingContent = $.when(removingVolatilePromise,
                             removingEmptyFieldTemplatePromise,
                             savingFieldTemplatesPromise,
                             savingOpenedTextareasPromise);
  return savingContent;
}


function onSubmitClick() {
  /*
   * Handle 'Submit' button (submit record).
   */
  log_action("onSubmitClick");
  $('#btnSubmit').prop('disabled', true);
  save_changes().done(function() {
    updateStatus('updating');
    /* Save all opened fields before submitting */
    var savingOpenedFields = saveOpenedFields(savingOpenedFields);

    savingOpenedFields.done(function() {
      var dialogPreview = createDialog("Loading...", "Retrieving preview...", 750, 700, true, true);

      // Get preview of the record and let the user confirm submit
      getPreview(dialogPreview, onSubmitPreviewSuccess);
    });
  });
}

// Enable this flag to force the next submission even if cache is outdated.
onSubmitClick.force = false;


function onPreviewClick() {
  /*
   * Handle 'Preview' button (preview record).
   */
  log_action("onPreviewClick");
  clearWarnings();
  var reqData = {
              'new_window': true,
              recID: gRecID,
              submitMode: gSubmitMode,
              requestType: 'preview'
              };

  if (gSubmitMode == "textmarc") {
    reqData.textmarc = $("#textmarc_textbox").val();
  }

  save_changes().done(function() {
    var dialogPreview = createDialog("Loading...", "Retrieving preview...", 750, 700, true);
    createReq(reqData, function(json) {
      // Preview was successful.
      $(dialogPreview.dialogDiv).remove();
      var resCode = json['resultCode'];
      if (resCode == 115) {
          // There was a textmarc parsing error
          displayMessage(resCode, true, json["parse_error"]);
          updateStatus('ready');
          return;
      }
      var html_preview = json['html_preview'];
      var preview_window = openCenteredPopup('', 'Record preview', 768, 768);
      if ( preview_window === null ) {
        var msg = "<strong> The preview window cannot be opened.</strong><br />\
                  Your browser might be blocking popups. Check the options and\
                  enable popups for this page.";
        displayMessage(undefined, true, [msg]);
      }
      else {
        preview_window.document.write(html_preview);
        preview_window.document.close(); // needed for chrome and safari
      }
    });
  });
}


function onPrintClick() {
  /*
   * Print page, makes use of special css rules @media print
   */
  // If we are in textarea view, copy the contents to the helper div
  log_action("onPrintClick");
  $('#print_helper').text($('#textmarc_textbox').val());
  $("#bibEditContentTable").css('height', "100%");
  window.print();
  resize_content();
}


function onTextMarcBoxKeyUp() {
  /* Handler for keyup event inside the textmarc editing area */
  gRecordDirty = true;
  activateSubmitButton();
  // Disable keyup event on textarea
  $(this).off("keyup");
}


function onTextMarcClick() {
  /*
  * 1) Send request to server that will return textmarc from the cache content
  * 2) Remove editor table and display content in textbox
  * 3) Activate flag to know we are in text marc mode (for submission)
  */
  log_action("onTextMarcClick");
  $("#img_textmarc").off("click");

  save_changes().done(function() {
    /* Save the content in all textareas that are currently opened before changing
    view mode
    */
    $(".edit_area textarea").trigger($.Event( 'keydown', {which:$.ui.keyCode.ENTER, keyCode:$.ui.keyCode.ENTER}));

    createReq({recID: gRecID, requestType: 'getTextMarc'
         }, function(json) {
          // Request was successful.
          $("#bibEditMessage").empty();

          var textmarc_box = $('<textarea>');
          textmarc_box.attr('id', 'textmarc_textbox');
          textmarc_box.addClass("bibedit_input");
          textmarc_box.html(json['textmarc']);
          $('#bibEditTable').remove();
          $('#bibEditHoldingPenAddedFields').remove();
          $('#bibeditHoldingPenGC').remove();
          $('#bibEditContentTable').append(textmarc_box);

          // Avoids having two different scrollbars
          $('#bibEditContentTable').css('overflow', 'visible');

          // Create an extra div to store the textarea content whenever printing
          var print_helper = $('<div>');
          print_helper.attr('id', 'print_helper');
          $('#bibEditContentTable').append(print_helper);

          // Bind keyup event to textarea to detect when changes have been
          // introduced
          textmarc_box.on("keyup", onTextMarcBoxKeyUp);

          // Disable menu buttons
          deactivateRecordMenu();
          if (gRecordDirty) {
            activateSubmitButton();
          }

          // Disable reference extraction in textmarc mode
          $('#img_run_refextract, #img_extract_free_text').off('click').removeClass(
          'bibEditImgCtrlEnabled').addClass('bibEditImgCtrlDisabled');

          // Empty undo/redo handlers
          gUndoList = []; // list of possible undo operations
          gRedoList = []; // list of possible redo operations
          updateUrView();

          // Disable read/only mode button
          $("#btnSwitchReadOnly").prop('disabled', true);

          // Activate textmarc flag
          gSubmitMode = 'textmarc';

          // Change icon to table view
          $("#img_textmarc").attr('src', '/img/bibedit_tableview.png');
          $("#img_textmarc").attr('id', 'img_tableview');
          $("#img_tableview").off("click").on("click", onTableViewClick);
         });
  });
}


function onTableViewClick() {
  /*
   * 1) Send request to validate textmarc and create a cache file with its
   *    content
   * 2) Get the record from the cache and display it in the table
  */
  log_action("onTableViewClick");
  createReq({recID: gRecID, textmarc: $('#textmarc_textbox').val(),
      requestType: 'getTableView', recordDirty: gRecordDirty
       }, function(json) {
          var resCode = json['resultCode'];
          if (resCode == 115) {
            // There was a textmarc parsing error
            displayMessage(resCode, true, json["parse_error"]);
            updateStatus('ready');
          }
          else if (resCode == 116) {
            // Change to table view was successful
            getRecord(gRecID);
            // Change icon to textmarc view
            $("#img_tableview").attr('src', '/img/bibedit_textmarc.png');
            $("#img_tableview").attr('id', 'img_textmarc');
            $("#img_textmarc").off("click").on("click", onTextMarcClick);

            // Enable back read/only mode button
            $("#btnSwitchReadOnly").prop('disabled', true);

            // Activate default submission flag
            gSubmitMode = 'default';
          }
        });
}


function onOpenPDFClick() {
  /*
   * Create request to retrieve PDF from record and open it in new window
   */
   log_action("onOpenPDFClick");
   createReq({recID: gRecID, requestType: 'get_pdf_url'
       }, function(json){
        // Preview was successful.
        var pdf_url = json['pdf_url'];
        var preview_window = openCenteredPopup(pdf_url);
        if ( preview_window === null ) {
          var msg = "<strong> The preview window cannot be opened.</strong><br />\
                    Your browser might be blocking popups. Check the options and\
                    enable popups for this page.";
          displayMessage(undefined, true, [msg]);
        }
        else {
          preview_window.document.close(); // needed for chrome and safari
        }
       });

}


function getPreview(dialog, onSuccess) {
    /*
     * Get preview to be added to the dialog before submission
     */
    log_action("getPreview");
    clearWarnings();
    var html_preview;
    var reqData = {
                  'new_window': false,
                  recID: gRecID,
                  submitMode: gSubmitMode,
                  requestType: 'preview'
                  };
    if (gSubmitMode == "textmarc") {
      reqData.textmarc = $("#textmarc_textbox").val();
    }
    createReq(reqData, function(json){
       // Preview was successful.
        html_preview = json['html_preview'];
        var resCode = json['resultCode'];
        if (resCode == 115) {
            // There was a parsing error
            displayMessage(resCode, true, json["parse_error"]);
            updateStatus('ready');
            $(dialog.dialogDiv).remove();
            return;
        }
        onSuccess(dialog, html_preview);
       });
}


function onCancelClick(){
  /*
   * Handle 'Cancel' button (cancel editing).
   */
  log_action("onCancelClick");
  updateStatus('updating');
  if (!gRecordDirty || displayAlert('confirmCancel')) {
    createReq({
      recID: gRecID,
      requestType: 'cancel'
    }, function(json) {
      // Cancellation was successful.
      changeAndSerializeHash({
          state: 'cancel',
          recid: gRecID
      });
      cleanUp(!gNavigatingRecordSet, '', null, true, true, false);
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
      holdingPenPanelRemoveEntries();
      // making the changes visible
      updateBibCirculationPanel();
      updateRevisionsHistory();
      updateUrView();
      updateToolbar(false);
      }, false);
  }
  else {
    updateStatus('ready');
  }
}


function onCloneRecordClick() {
  /*
   * Handle 'Clone' button (clone record).
   */
  log_action("onCloneRecordClick");
  updateStatus('updating');
  if (!displayAlert('confirmClone')){
    updateStatus('ready');
    return;
  }
  else if ( !gRecordDirty && gReqQueue.length === 0 ) {
    // If the record is unchanged, erase the cache.
    createReq({recID: gRecID, requestType: 'deleteRecordCache'}, function() {},
              true, undefined, onDeleteRecordCacheError);
  }
  else {
    save_changes();
  }
  createReq({requestType: 'newRecord', newType: 'clone', recID: gRecID},
    function(json){
      var newRecID = json['newRecID'];
      $('#txtSearchPattern').val(newRecID);
      getRecord.clonedRecord = true;
      getRecord(newRecID);
  }, false);
}


function onDeleteRecordClick(){
  /*
   * Handle 'Delete record' button.
   */
  log_action("onDeleteRecordClick");
  if (gPhysCopiesNum > 0){
    displayAlert('errorPhysicalCopiesExist');
    return;
  }
  if (gINTERNAL_DOI_PROTECTION_LEVEL > 0 && gManagedDOIs.length > 0){
      if (gINTERNAL_DOI_PROTECTION_LEVEL == 1){
	  if (!displayAlert('confirmDeleteManagedDOIs', gManagedDOIs)){
	      return;
	  }
      } else if (gINTERNAL_DOI_PROTECTION_LEVEL == 2) {
	  displayAlert('alertDeleteManagedDOIs', gManagedDOIs)
	  updateStatus('ready');
	  return;
      }
  }
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
      updateToolbar(false);
    }, false);
  }
}


function onMergeClick(event){
  /*
   * Handle click on 'Merge' link (to merge outdated cache with current DB
   * version of record).
   */
  log_action("onMergeClick");
  notImplemented(event);

  updateStatus('updating');
  createReq({recID: gRecID, requestType: 'prepareRecordMerge'}, function(json){
    // Null gRecID to avoid warning when leaving page.
    gRecID = null;
    var recID = json['recID'];
    window.location = gSITE_URL + '/'+ gSITE_RECORD +'/merge/#recid1=' + recID + '&recid2=' +
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
    }, false);
    event.preventDefault();
  });
  for (var i=0, n=gRECORD_TEMPLATES.length; i<n; i++)
    $('#lnkNewTemplateRecord_' + i).bind('click', function(event){
      updateStatus('updating');
      var templateNo = this.id.split('_')[1];
      createReq({requestType: 'newRecord', newType: 'template',
	templateFilename: gRECORD_TEMPLATES[templateNo][0]}, function(json){
	     getRecord(json['newRecID'], 0, onGetTemplateSuccess); // recRev = 0 -> current revision
      }, false);
      event.preventDefault();
    });
  //binding import function
  $('#lnkNewTemplateRecordImport_crossref').bind('click', function(event){
      var doiElement = $("#doi_crossref");
      if (!doiElement.val()) {
        //if no DOI specified
        errorDoi(117)
      } else {
        updateStatus('updating');
        createReq({requestType: 'newRecord', newType: 'import', doi: doiElement.val()},function(json){
        if (json['resultCode'] == 7) {
          getRecord(json['newRecID'], 0, onGetTemplateSuccess); // recRev = 0 -> current revision
        } else {
          errorDoi(json['resultCode']);
          updateStatus('error', 'Error !');
        }
        }, false);
      }
      event.preventDefault();
    });
  // bind enter key with "crossref" link clicked
  $('#doi_crossref').bind('keyup', function (e){
    if (e.which == 13){
      $('#lnkNewTemplateRecordImport_crossref').click();
    }
  });
  $('#doi_crossref').one('input propertychange', function (e) {
    $('#doi_crossref_help').html("<span class='help-text'>&nbsp;Press 'Enter' key to import</span>");
  });
}

function errorDoi(code){
  /*
  * Displays a warning message in the import from crossref textbox
  */
  var msg;
  switch(code) {
    case 117:
      msg = "Please input the DOI";
      break;
    case 118:
      msg = "Record with given DOI was not found";
      break;
    case 119:
      msg = "This is not a correct DOI, please correct it";
      break;
    case 120:
      msg = "Crossref account is not set up. Contact the site admin.";
      break;
    default:
      msg = "Error while importing data";
  }
  var warning = '<span class="doiWarning" style="padding-left: 5px; color: #ff0000;">' + msg + '</span>'
  $("#doi_crossref_help").empty().html(warning);
}


function cleanUp(disableRecBrowser, searchPattern, searchType,
     focusOnSearchBox, resetHeadline, updateCache){
  /*
   * Clean up display and data.
   */

   if (typeof updateCache === "undefined") {
    updateCache = true;
   }

  if ( gRecID && updateCache ) {
    if ( gRecordDirty || gReqQueue.length > 0 ) {
      var data = {
          recID: gRecID,
          requestType: 'deactivateRecordCache',
        };
      $.ajaxSetup({async:false});
      queue_request(data);
      save_changes();
      $.ajaxSetup({async:true});
    }
    else {
      createReq({recID: gRecID, requestType: 'deleteRecordCache'},
          function() {}, false, undefined, onDeleteRecordCacheError);
    }
  }

  // Deactivate controls.
  deactivateRecordMenu();
  if (disableRecBrowser){
    disableRecordBrowser();
    gResultSet = null;
    gResultSetIndex = null;
    gNavigatingRecordSet = false;
  }
  // Clear main content area.
  $('#bibeditHoldingPenGC').remove();
  $('#bibEditContentTable').empty();
  $('#bibEditMessage').empty();

  // Clear search area.
  if (typeof(searchPattern) == 'string' || typeof(searchPattern) == 'number')
    $('#txtSearchPattern').val(searchPattern);
  if ($.inArray(searchType, ['recID', 'reportnumber', 'anywhere']) != -1)
    $('#sctSearchType').val(searchPattern);
  if (focusOnSearchBox)
    $('#txtSearchPattern').focus();
  // Clear tickets.
  $('#tickets').empty();
  $('#newTicketDiv').remove();
  $('#rtError').remove();
  // Clear data.
  gRecID = null;
  gRecord = null;
  gTagFormat = null;
  gRecordDirty = false;
  gCacheMTime = null;
  gSelectionMode = false;
  gReadOnlyMode = false;
  gRecordHideAuthors = false;
  $('#btnSwitchReadOnly').html("Read-only");
  gHoldingPenLoadedChanges = null;
  gHoldingPenChanges = null;
  gLastChecked = null;
  gUndoList = [];
  gRedoList = [];
  gBibCircUrl = null;
  gPhysCopiesNum = 0;
  gSubmitMode = "default";
  gManagedDOIs = [];
}


function addHandler_autocompleteAffiliations(tg) {
    /*
     * Add autocomplete handler to a given cell
     */
    /* If gKBInstitution is not defined in the system, do nothing */
    if ($.inArray(gKBInstitution,gAVAILABLE_KBS) == -1)
        return
    $(tg).autocomplete({
    source: function( request, response ) {
                $.getJSON("/kb/export",
                { kbname: gKBInstitution, format: 'jquery', term: request.term},
                response);
    },
    search: function() {
                var term = this.value;
                if (term.length < 3) {
                    return false;
                }
                return true;
    }
    });
}

/*
 * **************************** 7. Editor UI ***********************************
 */

function colorFields(){
  /*
   * Color every other field (rowgroup) gray to increase readability.
   */
  $('#bibEditTable tbody:visible:even').each(function(){
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
  log_action("onMARCTagsClick");
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
  log_action("onHumanTagsClick");
  $(this).unbind('click').attr('disabled', 'disabled');
  createReq({recID: gRecID, requestType: 'changeTagFormat',
       tagFormat: 'human'});
  gTagFormat = 'human';
  updateTags();
  $('#btnMARCTags').bind('click', onMARCTagsClick).removeAttr('disabled');
  event.preventDefault();
}


function onLnkSpecialSymbolsClick(){
    var special_char_list = ['&#192;','&#193;','&#194;','&#195;','&#196;','&#197;',
                            '&#198;','&#199;','&#200;','&#201;','&#202;','&#203;',
                            '&#204;','&#205;','&#206;','&#207;','&#208;','&#209;',
                            '&#210;','&#211;','&#212;','&#213;','&#214;','&#215;',
                            '&#216;','&#217;','&#218;','&#219;','&#220;','&#221;',
                            '&#222;','&#223;','&#224;','&#225;','&#226;','&#227;',
                            '&#228;','&#229;','&#230;','&#231;','&#232;','&#233;',
                            '&#234;','&#235;','&#236;','&#237;','&#238;','&#239;',
                            '&#240;','&#241;','&#242;','&#243;','&#244;','&#245;',
                            '&#246;','&#247;','&#248;','&#249;','&#250;','&#251;',
                            '&#252;','&#253;','&#254;','&#255;'];
    var html_content;
    html_content = '<html><head><title>Special Symbols</title>';
    html_content += '<style type="text/css">';
    html_content += '#char_table_div { padding: 20px 0px 0px 20px; }';
    html_content += '#symbol_table { border: 1px solid black; border-collapse:collapse;}';
    html_content += 'td { border: 1px solid black; padding: 5px 5px 5px 5px;}';
    html_content += '</style>';
    html_content += '</head><body>';
    html_content += '<div id="char_table_div"><table id="symbol_table"><tr>';
    var char_list_length = special_char_list.length;
    for (var i=0; i<char_list_length; i++) {
        html_content += '<td>' + special_char_list[i] + '</td>';
        if ((i+1)%10 == 0) {
            html_content += '</tr><tr>';
        }
    }
    html_content += '</tr></table></div></body></html>';
    var special_char_window = window.open('', '', 'width=310,height=310,resizeable,scrollbars');
    special_char_window.document.write(html_content);
    special_char_window.document.close(); // needed for chrome and safari
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


function onFieldBoxClick(e, box){
  /*
   * Handle field select boxes.
   */
  log_action("onFieldBoxClick " + box);
   if ( !jQuery.contains(document.documentElement, gLastChecked)) {
       gLastChecked = box;
       clickBox(box);
       return;
   }
   if (e.shiftKey) {
   // If shift key is pressed check/uncheck all the select boxes from
   // current clicked select box till the previous clicked select box
     var checkboxes = $('.bibEditBoxField');
     var checked = box.checked;
     var start = checkboxes.index(box);
     var end = checkboxes.index(gLastChecked);
     checkboxes.slice(Math.min(start,end), Math.max(start,end)+ 1).each( function(){
       $(this).prop("checked", checked);
       clickBox(this);
     });
   }
   else {
     clickBox(box);
   }
   gLastChecked = box;
}

function clickBox(box) {
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
  log_action("onSubfieldBoxClick " + box);
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
  /**
   * Purpose: Gather the information about a current form
   * Called when adding x similar fields
   *
   * Input(s): int:fieldTmpNo - temporary number to identify the field being
   * added
   *
   * Returns: [template_num, data]
   * where data is in the same format as the templates data.
   *
  */
  var templateNum = $('#selectAddFieldTemplate_' + fieldTmpNo).attr("value");
  var tag = $("#txtAddFieldTag_" + fieldTmpNo).attr("value");

  // now checking if this is a controlfield ... controlfield if ind1 box is invisible
  if ($("#txtAddFieldInd1_" + fieldTmpNo + ":visible").length == 1){
    var ind1 = $("#txtAddFieldInd1_" + fieldTmpNo).attr("value");
    var ind2 = $("#txtAddFieldInd2_" + fieldTmpNo).attr("value");
    var subfieldTmpNo = $('#rowGroupAddField_' + fieldTmpNo).data('freeSubfieldTmpNo');
    var subfields = [];
    for (i=0; i < subfieldTmpNo; i++){
      var subfieldCode = $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_' + i).attr("value");
      var subfieldValueSelector = $('#txtAddFieldValue_' + fieldTmpNo + '_' + i);
      var subfieldValue = subfieldValueSelector.attr("value");
      if (subfieldValueSelector.hasClass("bibEditVolatileSubfield")) {
        subfieldValue = "VOLATILE:" + subfieldValue;
      }
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
  $('#txtAddFieldValue_' + fieldTmpNo + '_' + subfieldTmpNo).on(
    'focus', function(e){
      if ($(this).hasClass('bibEditVolatileSubfield')){
        $(this).select();
        $(this).removeClass("bibEditVolatileSubfield");
      }
    }
  ).on("mouseup", function(e) { e.preventDefault(); });
  var contentEditorId = '#txtAddFieldValue_' + fieldTmpNo + '_' + subfieldTmpNo;
  $(contentEditorId).bind('keyup', function(e){
    onAddFieldValueKeyPressed(e, jQRowGroupID, fieldTmpNo, subfieldTmpNo);
  });

}


function onAddFieldJumpToNextSubfield(jQRowGroupID, fieldTmpNo, subfieldTmpNo){
  /* Gets all the open text boxes for the current field and submits the changes
   * if it is the last one.
   */
  var fieldOpenInputs = $('input[id^="txtAddFieldValue_' + fieldTmpNo + '"]');

  var currentInputSelector = "#txtAddFieldValue_" + fieldTmpNo + "_" + subfieldTmpNo;
  var currentInput = $(currentInputSelector);
  var currentInputIndex = fieldOpenInputs.index(currentInput);

  if (currentInputIndex === fieldOpenInputs.length-1) {
    addFieldSave(fieldTmpNo);
  }
  else {
    fieldOpenInputs[currentInputIndex+1].focus();
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
  /* Create form to add a new field. If only one field is selected, the
   * new field will be inserted below it. Otherwise, the new field will
   * be inserted in the 3rd position
   */

  // Check if we are in the use case of adding in a specific position
  var selected_fields = getSelectedFields();
  var insert_below_selected = false;
  if (selected_fields != undefined) {
      var count_fields = 0;
      var selected_local_field_pos;
      var selected_tag, selected_ind1, selected_ind2;
      for (var tag in selected_fields.fields) {
          for (var localFieldPos in selected_fields.fields[tag]) {
              count_fields++;
              selected_local_field_pos = localFieldPos;
          }
          selected_tag = tag;
          selected_ind1 = selected_fields.fields[tag][localFieldPos][1];
          selected_ind2 = selected_fields.fields[tag][localFieldPos][2];
      }
      if (count_fields === 1)
          insert_below_selected = true;
  }

  var fieldTmpNo = onAddFieldClick.addFieldFreeTmpNo++;
  var jQRowGroupID = '#rowGroupAddField_' + fieldTmpNo;
  $('#bibEditColFieldTag').css('width', '90px');
  var tbodyElements = $('#bibEditTable tbody');

  // If only one field selected, add below the selected field
  if (insert_below_selected === true) {
      $('#rowGroup' + '_' + selected_tag + '_' + selected_local_field_pos).after(
      createAddFieldForm(fieldTmpNo, initialTemplateNo, selected_tag, selected_ind1, selected_ind2));
      $(jQRowGroupID).data('insertionPoint', parseInt(selected_local_field_pos) + 1);
      $(jQRowGroupID).data('selected_tag', selected_tag);
  }
  else {
      var insertionPoint = (tbodyElements.length >= 4) ? 3 : tbodyElements.length-1;
      $('#bibEditTable tbody').eq(insertionPoint).after(
      createAddFieldForm(fieldTmpNo, initialTemplateNo));
  }

  $(jQRowGroupID).data('freeSubfieldTmpNo', 1);

  // Bind event handlers.
  $('#btnAddFieldAddSubfield_' + fieldTmpNo).bind('click', function(){
    addFieldAddSubfieldEditor(jQRowGroupID, fieldTmpNo, "", "");
  });

  $('#txtAddFieldTag_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  initInputHotkeys('#txtAddFieldTag_' + fieldTmpNo);
  $('#txtAddFieldInd1_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  initInputHotkeys('#txtAddFieldInd1_' + fieldTmpNo);
  $('#txtAddFieldInd2_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  initInputHotkeys('#txtAddFieldInd2_' + fieldTmpNo);
  $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0').bind('keyup', onAddFieldChange);
  initInputHotkeys('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0');
  $('#txtAddFieldValue_' + fieldTmpNo + '_0').bind('keyup', function (e){
    onAddFieldValueKeyPressed(e, jQRowGroupID, fieldTmpNo, 0);
  });
  initInputHotkeys('#txtAddFieldValue_' + fieldTmpNo + '_0');

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
  if (insert_below_selected === true) {
      $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0').focus();
  }
  else {
      $('#txtAddFieldTag_' + fieldTmpNo).focus();
  }
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
  log_action("onAddFieldClick");
  if (failInReadOnly())
    return;
  activateSubmitButton();
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


function onAddFieldChange(event) {
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
            /* Generate ID of the field tag input */
            var fieldTagID = ('#' + $(this).attr('id').replace('SubfieldCode', 'Tag')).split('_');
            fieldTagID.pop();
            fieldTagID = fieldTagID.join('_');
            var fieldTag = $('body').find("#txtAddFieldTag_" + fieldTmpNo).val(),
                fieldInd1 = $('body').find("#txtAddFieldInd1_" + fieldTmpNo).val(),
                fieldInd2 = $('body').find("#txtAddFieldInd2_" + fieldTmpNo).val();
            if (fieldInd1 == '') {
                fieldInd1 = '_';
            }
            if (fieldInd2 == '') {
                fieldInd2 = '_';
            }
            if ($.inArray(fieldTag +  fieldInd1 + fieldInd2 + this.value, gTagsToAutocomplete) != -1) {
                addHandler_autocompleteAffiliations($(this).parent().next().children('input'));
            }
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
  var jQRowGroupID = "#rowGroupAddField_" + fieldTmpNo;
  var controlfield = $(jQRowGroupID).data('isControlfield');
  var tag = $('#txtAddFieldTag_' + fieldTmpNo).val();
  var value = $('#txtAddFieldValue_' + fieldTmpNo + '_0').val();
  var subfields = [], ind1 = ' ', ind2 = ' ';

  // variables used when we are adding a field in a specific position
  var insertPosition = $(jQRowGroupID).data('insertionPoint');
  var selected_tag = $(jQRowGroupID).data('selected_tag');

  if (controlfield) {
    // Controlfield. Validate and prepare to update.
    if (fieldIsProtected(tag)){
      displayAlert('alertAddProtectedField', [tag]);
      updateStatus('ready');
      return;
    }
    if (!validMARC('ControlTag', tag) || value == '') {
      displayAlert('alertCriticalInput');
      updateStatus('ready');
      return;
    }
    var field = [[], ' ', ' ', value, 0];
    var fieldPosition = getFieldPositionInTag(tag, field);
  }
  else {
    // Regular field. Validate and prepare to update.
    ind1 = $('#txtAddFieldInd1_' + fieldTmpNo).val();
    ind1 = (ind1 == '' || ind1 == '_') ? ' ' : ind1;
    ind2 = $('#txtAddFieldInd2_' + fieldTmpNo).val();
    ind2 = (ind2 == '' || ind2 == '_') ? ' ' : ind2;
    var MARC = tag + ind1 + ind2;
    if (fieldIsProtected(MARC)) {
      displayAlert('alertAddProtectedField', [MARC]);
      updateStatus('ready');
      return;
    }
    var validInd1 = (ind1 == ' ' || validMARC('Indicator1', ind1));
    var validInd2 = (ind2 == ' ' || validMARC('Indicator2', ind2));
    if (!validMARC('Tag', tag) || !validInd1 || !validInd2) {
      displayAlert('alertCriticalInput');
      updateStatus('ready');
      return;
    }
    // Collect valid subfields in an array.
    var invalidOrEmptySubfields = false;
     $('#rowGroupAddField_' + fieldTmpNo + ' .bibEditTxtSubfieldCode'
      ).each(function() {
        var subfieldTmpNo = this.id.slice(this.id.lastIndexOf('_')+1);
        var txtValue = $('#txtAddFieldValue_' + fieldTmpNo + '_' +
    subfieldTmpNo);
        var value = $(txtValue).val();
        value = value.replace(/^\s+|\s+$/g,""); // Remove whitespace from the ends of strings
        if (isSubjectSubfield(MARC, this.value)) {
          value = check_subjects_KB(value);
        }
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
    var fieldPosition;
    if ((insertPosition != undefined) && (tag == selected_tag)) {
        fieldPosition = $(jQRowGroupID).data('insertionPoint');
    }
    else {
        fieldPosition = getFieldPositionInTag(tag, field);
    }
  }

  var subfieldsExtended = [];
  /* Loop through all subfields to look for new subfields in the format
   * $$aContent$$bMore content and split them accordingly */
  for (var i=0, n=subfields.length; i<n ;i++) {
      if (valueContainsSubfields(subfields[i][1])) {
          var subfieldsToAdd = new Array(), subfieldCode = subfields[i][0];
          splitContentSubfields(subfields[i][1], subfieldCode, subfieldsToAdd);
          subfieldsExtended.push.apply(subfieldsExtended,subfieldsToAdd);
      }
      else{
          subfieldsExtended.push(subfields[i]);
      }
  }
  if (typeof subfieldsExtended[0] != 'undefined') {
      /* We have split some subfields */
      for (var i=0, n=subfieldsExtended.length; i < n; i++) {
          subfields[i] = subfieldsExtended[i];
      }
  }

  /* If adding a reference, add $$9 CURATOR */
  if (tag == '999') {
      subfields[subfields.length] = new Array('9', 'CURATOR');
  }

  // adding an undo handler
  var undoHandler = prepareUndoHandlerAddField(tag,
                                               ind1,
                                               ind2,
                                               fieldPosition,
                                               subfields,
                                               controlfield,
                                               value);
  addUndoOperation(undoHandler);

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
    value: value,
    undoRedo: undoHandler
  };

  queue_request(data);

  // Continue local updating.
  var fields = gRecord[tag];
  // New field?
  if (!fields) {
    gRecord[tag] = [field];
  }
  else{
    fields.splice(fieldPosition, 0, field);
  }
  // Remove form.
  $('#rowGroupAddField_' + fieldTmpNo).remove();
  if (!$('#bibEditTable > [id^=rowGroupAddField]').length)
      $('#bibEditColFieldTag').css('width', '48px');
  // Redraw all fields with the same tag and recolor the full table.
  redrawFields(tag, true);
  reColorFields();
  // Scroll and color the new field for a short period.
  var rowGroup = $('#rowGroup_' + tag + '_' + fieldPosition);
  var newContent = $('#fieldTag_' + tag + '_' + fieldPosition);
  if (insertPosition === undefined) {
    $(newContent).focus();
  }
  $(rowGroup).effect('highlight', {color: gNEW_CONTENT_COLOR},
         gNEW_CONTENT_COLOR_FADE_DURATION);
}


function onAddSubfieldsClick(img){
  /*
   * Handle 'Add subfield' buttons.
   */
  var fieldID = img.id.slice(img.id.indexOf('_')+1);
  log_action("onAddSubfieldsClick " + fieldID);
  addSubfield(fieldID);
}

function onDOISearchClick(button){
  /*
   * Handle 'Search for DOI' button.
   */
  // gets the doi based from appropriate cell
  log_action("onDOISearchClick");
  var doi = $(button).parent().prev().text();
  createReq({doi: doi, requestType: 'DOISearch'}, function(json)
  {
    if (json['doi_url'] !== undefined) {
      openCenteredPopup(json['doi_url'], "", 768, 768);
    } else {
      alert("DOI not found !");
    }
  }, false);
}


function addSubfield(fieldID, defSubCode, defValue) {
  /* add a subfield based on fieldID, where the first 3 digits are
   * the main tag, followed by _ and the position of the field.
   * defSubCode = the default value for subfield code
  */
  var jQRowGroupID = '#rowGroup_' + fieldID;
  var tmpArray = fieldID.split('_');
  var tag = tmpArray[0];var fieldPosition = tmpArray[1];
  if ($('#rowAddSubfieldsControls_' + fieldID).length == 0){
    // The 'Add subfields' form does not exist for this field.
    $(jQRowGroupID).append(createAddSubfieldsForm(fieldID, defSubCode, defValue));
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
    if (!valid && !$(this).hasClass('bibEditInputError')){
      $(this).addClass('bibEditInputError');
    }
    else if (valid){
      if ($(this).hasClass('bibEditInputError')) {
        $(this).removeClass('bibEditInputError');
      }
      if (event.keyCode != 9 && event.keyCode != 16){
        /* If we are creating a new field present in gTagsToAutocomplete, add autocomplete handler */
        var fieldInfo = $(this).parents("tr").siblings().eq(0).children().eq(1).html();
        if ($.inArray(fieldInfo + this.value, gTagsToAutocomplete) != -1) {
          addHandler_autocompleteAffiliations($(this).parent().next().children('input'));
        }
        $(this).parent().next().children('input').focus();
      }
    }
  }
  else if ($(this).hasClass('bibEditInputError')){
    $(this).removeClass('bibEditInputError');
  }
}


function onAddSubfieldsSave(event, tag, fieldPosition) {
  /*
   * Handle 'Save' button in add subfields form.
   */
  var field = gRecord[tag][fieldPosition];
  var fieldID = tag + '_' + fieldPosition;
  var tag_ind = tag + field[1] + field[2];
  var subfields = [];
  var protectedSubfield = false, invalidOrEmptySubfields = false;
  // Collect valid fields in an array.
  $('#rowGroup_' + fieldID + ' .bibEditTxtSubfieldCode'
   ).each(function(){
     var MARC = getMARC(tag, fieldPosition) + this.value;
     if ($.inArray(MARC, gPROTECTED_FIELDS) != -1) {
       protectedSubfield = MARC;
       return false;
     }
     var subfieldTmpNo = this.id.slice(this.id.lastIndexOf('_') + 1);
     var txtValue = $('#txtAddSubfieldsValue_' + fieldID + '_' +
       subfieldTmpNo);
     var value = $(txtValue).val();
     /* Check if we need to transform automatically the value (in the case
        of a subject subfield)
     */
     if (isSubjectSubfield(tag_ind, this.value)) {
      value = check_subjects_KB(value);
     }
     if (!$(this).hasClass('bibEditInputError') && this.value != ''
         && !$(txtValue).hasClass('bibEditInputError') && value != '')
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

  /* Check if $$9 CURATOR is present */
  var iscurated = false;
  if (tag === "999") {
    current_field_subfields = field[0];
    for (var i = 0, j = current_field_subfields.length; i < j; i++) {
        if (current_field_subfields[i][0] == "9" && current_field_subfields[i][1] == "CURATOR") {
            iscurated = true;
        }
    }
  }
  if (!subfields.length == 0) {
      /* Loop through all subfields to look for new subfields in the format
       * $$aContent$$bMore content and split them accordingly */
      var subfieldsExtended = [];
      for (var i=0, j=subfields.length; i < j; i++) {
          if (valueContainsSubfields(subfields[i][1])) {
              var subfieldsToAdd = new Array(), subfieldCode = subfields[i][0];
              splitContentSubfields(subfields[i][1], subfieldCode, subfieldsToAdd);
              subfieldsExtended.push.apply(subfieldsExtended,subfieldsToAdd);
          }
          else{
              subfieldsExtended.push(subfields[i]);
          }
      }
      if (typeof subfieldsExtended[0] != 'undefined') {
          /* We have split some subfields */
          for (var i=0, j=subfieldsExtended.length; i < j; i++) {
              subfields[i] = subfieldsExtended[i];
          }
      }
      if (tag === "999" && !iscurated) {
        subfields.push(new Array('9', 'CURATOR'));
      }
      // creating the undo/redo handler
      var urHandler = prepareUndoHandlerAddSubfields(tag, fieldPosition, subfields);
      addUndoOperation(urHandler);
      // Create Ajax request
      var data = {
        recID: gRecID,
        requestType: 'addSubfields',
        tag: tag,
        fieldPosition: fieldPosition,
        subfields: subfields,
        undoRedo: urHandler
      };

      queue_request(data);

      // Continue local updating
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
      for (var changePos in gHoldingPenChanges) {
          var change = gHoldingPenChanges[changePos];
          if ( change["tag"] == tag && change["field_position"] == fieldPosition ) {// TODO: add indicators?
            addChangeControl(changePos,true);
          }
      }
  } else {
    // No valid fields were submitted.
    $('#rowAddSubfields_' + fieldID + '_' + 0).nextAll().andSelf().remove();
    updateStatus('ready');
  }
}


function convertFieldIntoEditable(cell, shouldSelect){
  // chacking if the clicked field is still present int the DOM structure ... if not, we have just removed the element
  if ($(cell).parent().parent().parent()[0] == undefined){
    return;
  }
  // first we have to detach all exisiting editables ... which means detaching the event
  editEvent = 'customclick';
  $(cell).unbind(editEvent);

  /*
    This binding allows to wait if other textarea is opened before
    opening the new one. In this way we can jump from one field to the
    other without the new one being closed.
  */
  $(cell).unbind('click').bind('click', function(event) {
    var self = this;

    function trigger_click() {
      $(self).trigger('customclick');
    }

    if ($(".edit_area textarea").length > 0) {
      $(".edit_area textarea").parent().submit(function() {
        setTimeout(trigger_click, 30);
      });
    } else {
      trigger_click();
    }
  });

  $(cell).editable(
    /* function to send edited content to */
    function(value) {
      newVal = onEditableCellChange(value, this);
      if (typeof newVal === "undefined") {
        /* content could not be changed, keep old value */
        var tmpArray = this.id.split('_');
        var tag = tmpArray[1],
            fieldPosition = tmpArray[2],
            subfieldIndex = tmpArray[3];
        var field = gRecord[tag][fieldPosition];
        return field[0][subfieldIndex][1];
      }
      if (newVal.substring(0,9) == "VOLATILE:"){
        $(cell).addClass("bibEditVolatileSubfield");
        newVal = newVal.substring(9);
        if (!shouldSelect) {
          // the field should start selecting all the content upon the click
          // because it is VOLATILE
          convertFieldIntoEditable(cell, true);
        }
      }
      else{
        $(cell).removeClass("bibEditVolatileSubfield");
        if (shouldSelect){
          // this is not a volatile field any more - clicking should not
          // select all the content inside.
          convertFieldIntoEditable(cell, false);
        }
      }
      return newVal;
    },
    /* start of jEditable options */
    {
      type: 'textarea_custom',
      callback: function(data, settings){
        /* Function to run after submitting edited content */
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
      data: function() {
        // Get the real content from the record structure (instead of
        // from the view, where HTML entities are escaped).
        var tmpArray = this.id.split('_');
        var tag = tmpArray[1], fieldPosition = tmpArray[2],
        subfieldIndex = tmpArray[3];
        var field = gRecord[tag][fieldPosition];
        var tmpResult = "";
        if (tmpArray[0] == 'fieldTag'){
            var ind1 = (field[1] == " ") ? "_" : field[1];
            var ind2 = (field[2] == " ") ? "_" : field[2];
            tmpResult = tag + ind1 + ind2;
        }
        else if (subfieldIndex == undefined){
          // Controlfield
          tmpResult = field[3];
        }
        else if (tmpArray[0] == 'subfieldTag'){
            tmpResult = field[0][subfieldIndex][0];
        }
        else {
            tmpResult = field[0][subfieldIndex][1];
        }
        if (tmpResult.substring(0,9) == "VOLATILE:"){
          tmpResult = tmpResult.substring(9);
        }
        return tmpResult;

      },
      placeholder: '',
      onblur: 'submit',
      select: shouldSelect
    });
}


function onContentClick(event, cell) {
  /*
   * Handle click on editable content fields.
   */
  function open_field() {
    /*
      Converts <td> element into editable object the first time click
      is triggered
    */
    var shouldSelect = false;
    // Check if subfield is volatile subfield from a template
    if ( $(cell).hasClass('bibEditVolatileSubfield') ) {
      shouldSelect = true;
    }
    if (!$(cell).hasClass('edit_area')) {
      $(cell).addClass('edit_area').removeAttr('onclick');
      convertFieldIntoEditable(cell, shouldSelect);
      $(cell).trigger('click');
    }
  }
  if ( ($(event.target).parent().hasClass('bibeditHPCorrection') && !$(event.target).parent().hasClass('bibeditHPSame'))
        || ($(event.target).hasClass('bibeditHPCorrection') && !$(event.target).hasClass('bibeditHPSame')) ) {
    return false;
  }
  if ($(".edit_area textarea").length > 0) {
    /* There is another textarea open, wait for it to close */
    $(".edit_area textarea").parent().submit(function() {
       setTimeout(open_field, 30);
    });
  } else {
    open_field();
  }
}


function getUpdateSubfieldValueRequestData(tag, fieldPosition, subfieldIndex,
        subfieldCode, value, changeNo, undoDescriptor, modifySubfieldCode){
  var requestType;
  if (modifySubfieldCode == true) {
      requestType = 'modifySubfieldTag';
  }
  else {
      requestType = 'modifyContent';
  }
  var data = {
    recID: gRecID,
    requestType: requestType,
    tag: tag,
    fieldPosition: fieldPosition,
    subfieldIndex: subfieldIndex,
    subfieldCode: subfieldCode,
    value: value
  };
  if (changeNo != undefined && changeNo != -1){
    data.hpChanges = {toDisable: [changeNo]};
  }
  if (undoDescriptor != undefined && undoDescriptor != null){
    data.undoRedo = undoDescriptor;
  }
  return data;
}


function updateSubfieldValue(tag, fieldPosition, subfieldIndex, subfieldCode,
                            value, consumedChange, undoDescriptor,
                            modifySubfieldCode){
  // Create Ajax request for simple updating the subfield value
  if (consumedChange == undefined || consumedChange == null){
    consumedChange = -1;
  }

  var data = getUpdateSubfieldValueRequestData(tag,
                                               fieldPosition,
                                               subfieldIndex,
                                               subfieldCode,
                                               value,
                                               consumedChange,
                                               undoDescriptor,
                                               modifySubfieldCode);

  queue_request(data);
}

function getBulkUpdateSubfieldContentRequestData(tag, fieldPosition,
                                                 subfieldIndex, subfieldCode,
                                                 value, consumedChange,
                                                 undoDescriptor, subfieldsToAdd) {
    /*
     *Purpose: prepare data to be included in the request for a bulk update
     *         of the subfield content
     *
     *Return: object: Array of changes to be applied
     *
     */
    var changesAdd = [];

    var data = getUpdateSubfieldValueRequestData(tag,
                                                 fieldPosition,
                                                 subfieldIndex,
                                                 subfieldCode,
                                                 value,
                                                 consumedChange,
                                                 null,
                                                 false);
    changesAdd.push(data);

    data = {
      recID: gRecID,
      requestType: 'addSubfields',
      tag: tag,
      fieldPosition: fieldPosition,
      subfields: subfieldsToAdd
    };
    changesAdd.push(data);

    return changesAdd;
}


function bulkUpdateSubfieldContent(tag, fieldPosition, subfieldIndex, subfieldCode,
                            value, consumedChange, undoDescriptor, subfieldsToAdd, subfields_offset) {
    /*
     *Purpose: perform request for a bulk update as the user introduced in the content
     *         field multiple subfields to be added in the form $$aTest$$bAnother
     *
     *Input(s): string:tag - Field tag to be updated
     *          int:fieldPosition - position of the field with regard to the rest
     *                              of fields with the same tag
     *          int:subfieldIndex - position of the subfield with regard to the
     *                              other subfields in that field instance
     *          string:subfieldCode - Code of the subfield that is being modified
     *          string:value - old value present in the subfield
     *          consumedChange - undefined behaviour
     *          object:undoDescriptor - undo operations relative to the update
     *                                  action
     *          object:subfieldsToAdd - array containing subfields to add)
     *
     */
    if (consumedChange == undefined || consumedChange == null){
        consumedChange = -1;
    }

    var data = getBulkUpdateSubfieldContentRequestData(tag,
                                               fieldPosition,
                                               subfieldIndex,
                                               subfieldCode,
                                               value,
                                               consumedChange,
                                               undoDescriptor,
                                               subfieldsToAdd,
                                               subfields_offset);

    var bulk_data = {'requestType' : 'applyBulkUpdates',
                     'requestsData' : data,
                     'recID' : gRecID};
    bulk_data.undoRedo = undoDescriptor;

    queue_request(bulk_data);
}


function updateFieldTag(oldTag, newTag, oldInd1, oldInd2, ind1, ind2, fieldPosition,
                        consumedChange, undoDescriptor){
  // Create Ajax request for simple updating the subfield value
  if (consumedChange == undefined || consumedChange == null){
      consumedChange = -1;
  }
  var data = getUpdateFieldTagRequestData(oldTag,
                                          oldInd1,
                                          oldInd2,
                                          newTag,
                                          ind1,
                                          ind2,
                                          fieldPosition,
                                          consumedChange,
                                          undoDescriptor);

  queue_request(data);
}


function getUpdateFieldTagRequestData(oldTag, oldInd1, oldInd2, newTag, ind1, ind2,
                                      fieldPosition, changeNo, undoDescriptor){
  var data = {
    recID: gRecID,
    requestType: "modifyFieldTag",
    fieldPosition: fieldPosition,
    oldTag: oldTag,
    newTag: newTag,
    ind1: ind1,
    ind2: ind2,
    oldInd1: oldInd1,
    oldInd2: oldInd2
  };
  if (changeNo != undefined && changeNo != -1){
    data.hpChanges = {toDisable: [changeNo]};
  }
  if (undoDescriptor != undefined && undoDescriptor != null){
    data.undoRedo = undoDescriptor;
  }

  return data;
}

/*call autosuggest, get the values, suggest them to the user*/
/*this is typically called when autosuggest key is pressed*/
function onAutosuggest(event) {
  var mytarget = event.target;
  if (event.srcElement) mytarget = event.srcElement;/*fix for IE*/
  var myparent = mytarget.parentNode;
  var mygrandparent = myparent.parentNode;
  var parentid = myparent.id;
  var value = mytarget.value;
  var mylen = value.length;
  var replacement = ""; //used by autocomplete
  var tmpArray = mygrandparent.id.split('_');
  /*ids for autosuggest/autocomplete html elements*/
  var content_id = 'content_'+tmpArray[1]+'_'+tmpArray[2]+'_'+tmpArray[3];
  var autosuggest_id = 'autosuggest_'+tmpArray[1]+'_'+tmpArray[2]+'_'+tmpArray[3];
  var select_id = 'select_'+tmpArray[1]+'_'+tmpArray[2]+'_'+tmpArray[3];
  var maintag = tmpArray[1], fieldPosition = tmpArray[2],
	  subfieldIndex = tmpArray[3];
  var field = gRecord[maintag][fieldPosition];
  var subfieldcode = field[0][subfieldIndex][0];
  var subtag1 = field[1];
  var subtag2 = field[2];
  //check if this an autosuggest or autocomplete field.
  var fullcode = getMARC(maintag, fieldPosition, subfieldIndex);
  var reqtype = ""; //autosuggest or autocomplete, according to tag..
  for (var i=0;i<gAUTOSUGGEST_TAGS.length;i++) {if (fullcode == gAUTOSUGGEST_TAGS[i]) {reqtype = "autosuggest"}}
  for (var i=0;i<gAUTOCOMPLETE_TAGS.length;i++) {if (fullcode == gAUTOCOMPLETE_TAGS[i]) {reqtype = "autocomplete"}}
  if (fullcode == gKEYWORD_TAG) {reqtype = "autokeyword"}
  if (reqtype == "") {
    return;
  }

  // Create Ajax request.
  var data = {
    recID: gRecID,
    maintag: maintag,
    subtag1: subtag1,
    subtag2: subtag2,
    subfieldcode: subfieldcode,
    requestType: reqtype,
    value: value
  }; //reqtype is autosuggest, autocomplete or autokeyword
  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']]);
    suggestions = json[reqtype];
    if (reqtype == 'autocomplete') {
        if ((suggestions != null) && (suggestions.length > 0)) {
            //put the first one "here"
            replacement = suggestions[0];
            var myelement = document.getElementById(mygrandparent.id);
            if (myelement != null) {
               //put in the the gRecord
               gRecord[maintag][fieldPosition][0][subfieldIndex][1] = replacement;
               mytarget.value = replacement;
            }
            //for the rest, create new subfields
            for (var i=1, n=suggestions.length; i < n; i++) {
                var valuein = suggestions[i];
                var addhereID = maintag+"_"+fieldPosition; //an id to indicate where the new subfield goes
                addSubfield(addhereID, subfieldcode, valuein);
            }
        } else { //autocomplete, nothing found
            alert("No suggestions for your search term "+value);
        }
    } //autocomplete
    if ((reqtype == 'autosuggest') || (reqtype == 'autokeyword')) {
        if ((suggestions != null) && (suggestions.length > 0)) {
            /*put the suggestions in the div autosuggest_xxxx*/
            //make a nice box..
            mysel = '<table width="400" border="0"><tr><td><span class="bibeditscrollArea"><ul>';
            //create the select items..
            for (var i=0, n=suggestions.length; i < n; i++) {
               tmpid = select_id+"-"+suggestions[i];
               mysel = mysel +'<li onClick="onAutosuggestSelect(\''+tmpid+'\');">'+suggestions[i]+"</li>";
            }
            mysel = mysel+"</ul></td>"
            //add a stylish close link in case the user does not find
            //the value among the suggestions
            mysel = mysel + "<td><form><input type='button' value='close' onClick='onAutosuggestSelect(\""+select_id+"-"+'\");></form></td>';
            mysel = mysel+"</tr></table>";
            //for (var i=0;i<suggestions.length;i++) { mysel = mysel + +suggestions[i]+ " "; }
            autosugg_in = document.getElementById(autosuggest_id);
            if (autosugg_in != null) {autosugg_in.innerHTML = mysel;}
         } else { //there were no suggestions
             alert("No suggestions for your search term "+value);
         }
    } //autosuggest
  }, false); /*NB! This function is called synchronously.*/
} //onAutoSuggest


/*put the content of the autosuggest select into the field where autoselect was lauched*/
function onAutosuggestSelect(selectidandselval) {
  /*first take the selectid. It is the string before the first hyphen*/
  var tmpArray = selectidandselval.split('-');
  var selectid = tmpArray[0];
  var selval =  tmpArray[1];
  /*generate the content element id and autosuggest element id from the selectid*/
  var tmpArray = selectid.split('_');
  var content_id = 'content_'+tmpArray[1]+'_'+tmpArray[2]+'_'+tmpArray[3];
  var autosuggest_id = 'autosuggest_'+tmpArray[1]+'_'+tmpArray[2]+'_'+tmpArray[3];
  var content_t = document.getElementById(content_id); //table
  var content = null; //the actual text
  //this is interesting, since if the user is browsing the list of selections by mouse,
  //the autogrown form has disapperaed and there is only the table left.. so check..
  if (content_t.innerHTML.indexOf("<form>") ==0) {
     var content_f = null; //form
     var content_ta = null; //textarea
     if (content_t) {
         content_f = content_t.firstChild; //form is the sub-elem of table
     }
     if (content_f) {
         content_ta = content_f.firstChild; //textarea is the sub-elem of form
     }
     if (!(content_ta)) {return;}
     content = content_ta;
  } else {
     content = content_t;
  }
  /*put value in place*/
  if (selval) {
      content.innerHTML = selval;
      content.value = selval;
  }
  /*remove autosuggest box*/
  var autosugg_in = document.getElementById(autosuggest_id);
  autosugg_in.innerHTML = "";
}

function check_subjects_KB(value) {
    /*
     * Query Subjects KB to look for a match
     */
    /* If KB is not defined in the system, just return value*/
    if ($.inArray(gKBSubject,gAVAILABLE_KBS) == -1)
        return value;
    var response='';
    $.ajaxSetup({async:false});
    $.getJSON("/kb/export",
             { kbname: gKBSubject, format: 'json', searchkey: value},
             function(data) {if (data[0]) {response = data[0].label;}}
             );
    $.ajaxSetup({async:true});
    if (response) {
        return response;
    }
    return value;
}


function onMoveSubfieldClick(type, tag, fieldPosition, subfieldIndex){
  /*
   * Handle subfield moving arrows.
   */
  log_action("onMoveSubfieldClick " + type + ' ' + tag);
  if (failInReadOnly()){
    return;
  }

  // Check if moving is possible
  if (type == 'up') {
    if ( (parseInt(subfieldIndex) - 1 )< 0) {
      updateStatus('ready', '');
      return;
    }
  }
  else {
    if ((parseInt(subfieldIndex) + 1) >= gRecord[tag][fieldPosition][0].length) {
      updateStatus('ready', '');
      return;
    }
  }
  // creating the undoRedo Hanglers
  var undoHandler = prepareUndoHandlerMoveSubfields(tag, parseInt(fieldPosition), parseInt(subfieldIndex), type);
  addUndoOperation(undoHandler);

  var ajaxData = performMoveSubfield(tag, fieldPosition, subfieldIndex, type, undoHandler);

  queue_request(ajaxData);
}


function onDeleteClick(event){
  /*
   * Handle 'Delete selected' button or delete hotkeys.
   */
  log_action("onDeleteClick");
  if (failInReadOnly()){
    return;
  }
  var toDelete = getSelectedFields();
  // Assert that no protected fields are scheduled for deletion.
  var protectedField = containsProtectedField(toDelete);
  var affectedField = containsHPAffectedField(toDelete);

  if (affectedField){
    displayAlert('alertDeleteHPAffectedField', [affectedField]);
    updateStatus('ready');
    return;
  }
  if (protectedField){
    displayAlert('alertDeleteProtectedField', [protectedField]);
    updateStatus('ready');
    return;
  }
  // Special care must be taken when deleting DOIs we manage
  if (gINTERNAL_DOI_PROTECTION_LEVEL > 0){
      var managedDOIField = containsManagedDOI(toDelete);
      if (managedDOIField && gINTERNAL_DOI_PROTECTION_LEVEL == 1){
	  if (!displayAlert('confirmDeleteManagedDOIsField', [managedDOIField])){
	      updateStatus('ready');
	      return;
	  }
      } else if (managedDOIField && gINTERNAL_DOI_PROTECTION_LEVEL == 2) {
	  displayAlert('alertDeleteManagedDOIsField', [managedDOIField])
	  updateStatus('ready');
	  return;
      }
  }
  // register the undo Handler
  var urHandler = prepareUndoHandlerDeleteFields(toDelete);
  addUndoOperation(urHandler);
  var ajaxData = deleteFields(toDelete, urHandler);

  // Disable the delete button
  $('#btnDeleteSelected').attr('disabled', 'disabled');

  queue_request(ajaxData);
}


function onMoveFieldUp(tag, fieldPosition) {
  if (failInReadOnly()){
    return;
  }
  log_action('onMoveFieldUp ' + tag + ' ' + fieldPosition)
  fieldPosition = parseInt(fieldPosition);
  var thisField = gRecord[tag][fieldPosition];
  if (fieldPosition > 0) {
    var prevField = gRecord[tag][fieldPosition-1];
    // check if the previous field has the same indicators
    if ( cmpFields(thisField, prevField) == 0 ) {
      var undoHandler = prepareUndoHandlerMoveField(tag, fieldPosition, "up");
      addUndoOperation(undoHandler);
      var ajaxData = performMoveField(tag, fieldPosition, "up", undoHandler);
      queue_request(ajaxData);
    }
  }
}


function onMoveFieldDown(tag, fieldPosition) {
  if (failInReadOnly()){
    return;
  }
  log_action('onMoveFieldDown ' + tag + ' ' + fieldPosition)
  fieldPosition = parseInt(fieldPosition);
  var thisField = gRecord[tag][fieldPosition];
  if (fieldPosition < gRecord[tag].length-1) {
    var nextField = gRecord[tag][fieldPosition+1];
    // check if the next field has the same indicators
    if ( cmpFields(thisField, nextField) == 0 ) {
      var undoHandler = prepareUndoHandlerMoveField(tag, fieldPosition, "down");
      addUndoOperation(undoHandler);
      var ajaxData = performMoveField(tag, fieldPosition, "down", undoHandler);
      queue_request(ajaxData);
    }
  }
}


function updateInterfaceAccordingToMode(){
  /* updates the user interface (in particular the activity of menu buttons)
     accordingly to the surrent operation mode of BibEdit.
   */
  // updating the switch button caption
  if (gReadOnlyMode){
    deactivateRecordMenu();
    $('#btnSwitchReadOnly').html("R/W");
  } else {
    activateRecordMenu();
    $('#btnSwitchReadOnly').html("Read-only");
  }
}


function switchToReadOnlyMode(){
  // Moving to the read only mode with BibEdit

  if (gRecordDirty == true){
    alert("Please submit the record or cancel your changes before going to the read-only mode ");
    return false;
  }
  log_action("switchToReadOnlyMode");
  gReadOnlyMode = true;
  createReq({recID: gRecID, requestType: 'deleteRecordCache'}, function() {},
            true, undefined, onDeleteRecordCacheError);
  gCacheMTime = 0;

  updateInterfaceAccordingToMode();
}


function canSwitchToReadWriteMode(){
  /*A function determining if at current moment, it is possible to switch to the read/write mode*/
  // If the revision is not the newest -> return false
  if (!(gRecRev === gRecLatestRev)) {
    return false;
  }
  else {
    return true;
  }
}


function switchToReadWriteMode(){
  // swtching to a normal editing mode of BibEdit
  if (!canSwitchToReadWriteMode()){
    alert("Only the latest revision can be edited");
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
    //document.location = "/"+ gSITE_RECORD +"/merge/#recid1=" + gRecID + "&recid2=" + gRecID + "." + revisionId;
    var comparisonUrl = "/"+ gSITE_RECORD +"/edit/compare_revisions?recid=" +
      gRecID + "&rev1=" + gRecRev + "&rev2=" + revisionId;
    var newWindow = window.open(comparisonUrl);
    newWindow.focus();
    return false;
  };
}


function onRevertClick(revisionId){
  /*
   * Handle 'Revert' button (submit record).
   */
  log_action("onRevertClick " + revisionId);
  updateStatus('updating');
  if (displayAlert('confirmRevert')){
    createReq({recID: gRecID, revId: revisionId, lastRevId: gRecLatestRev, requestType: 'revert',
         force: onSubmitClick.force}, function(json){
      // Submission was successful.
      changeAndSerializeHash({state: 'submit', recid: gRecID});
      var resCode = json['resultCode'];
      cleanUp(!gNavigatingRecordSet, '', null, true);
      // clear the list of record revisions
      resetBibeditState();
      displayMessage(resCode, false, [json['recID']]);
      updateToolbar(false);
      updateStatus('report', gRESULT_CODES[resCode]);
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

  $("#bibEditRevisionsHistory").html(result);
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


function encodeXml(str){
    var resultString = "";
    for (var i=0, n=str.length; i<n; i++){
        var c = str.charAt(i);
        switch (c){
        case '<':
            resultString += "&lt;";
            break;
        case '>':
            resultString += "&gt;";
            break;
        case '&':
            resultString += "&amp;";
            break;
        case '"':
            resultString += "&quot;";
            break;
        case "'":
            resultString += "&apos;";
            break;
        default:
            resultString += c;
        }
    }
    return resultString;
}

function getSelectionMarcXml(){
  /*Gets the MARC XML of the current editor selection*/

  var checkedFieldBoxes = $('input[class="bibEditBoxField"]:checked'); // interesting only for the controlfields
                                                                       //  where no subfields are
  var checkedSubfieldBoxes = $('input[class="bibEditBoxSubfield"]:checked');

  // now constructing the interesting data

  var selectionNormal = {}; // a dictionary of identifiers taht have appeared already

  var selectionControlFields = [];

  var selectedFields = []; // a list of fields already selected
  var currentField = null; // a curently edited field

  // Collect subfields to be deleted in toDelete.
  var normalFieldsXml = "";
  var controlFieldsXml = "";

  $(checkedSubfieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2], subfieldIndex = tmpArray[3];
    if (currentField == null || currentField.tag != tag || currentField.position != fieldPosition){
      if (currentField != null){
        var newPos = selectedFields.length;
        selectedFields[newPos] = currentField;
        normalFieldsXml += "</datafield>"
      }
      // creating an empty field
      currentField={};
      currentField.subfields = [];
      currentField.tag = tag;
      currentField.position = fieldPosition;
      currentField.ind1 = gRecord[tag][fieldPosition][1];
      currentField.ind2 = gRecord[tag][fieldPosition][2];
      currentField.isControlField = false;
      selectionNormal[tag] = true;
      normalFieldsXml += "<datafield tag=\"" + currentField.tag + "\" ind1=\"" +
          currentField.ind1 + "\" ind2=\"" + currentField.ind2 + "\">";
    }

    // appending a current subfield
    var newPos = currentField.subfields.length;
    subfield = gRecord[tag][fieldPosition][0][subfieldIndex];
    currentField.subfields[newPos] = subfield;
      normalFieldsXml += "<subfield code=\"" + subfield[0] + "\">" + encodeXml(subfield[1]) + "</subfield>";
  });

  if (currentField != null){
    var newPos = selectedFields.length;
    selectedFields[newPos] = currentField;
    normalFieldsXml += "</datafield>";
  }

  // now extending by the control fields (they did not appear earlier)
  $(checkedFieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2];
    if (selectionNormal[tag] == undefined){
       // we have a control field ! otherwise, the field has been already utilised
      currentField = {};
      currentField.tag = tag;
      currentField.value = gRecord[tag][fieldPosition][3]
      var newPos = selectionControlFields.length;
      selectionControlFields[newPos] = currentField;
      controlFieldsXml += "<controlfield tag=\"" + currentField.tag + "\">" + currentField.value+ "</controlfield>";
    }
  });

  return "<record>" + controlFieldsXml + normalFieldsXml + "</record>";

}


function onPerformCopy(){
  /** The handler performing the copy operation
   */
  log_action("onPerformCopy");
  if (document.activeElement.type == "textarea" || document.activeElement.type == "text"){
    /*we do not want to perform this in case we are in an ordinary text area*/
    return;
  }
  var valueToCopy = getSelectionMarcXml();
  clipboardCopyValue(valueToCopy);
}


function onPerformPaste(){
  /* Performing the paste operation -> retriexing the MARC XML from the clipboard,
     decoding and applying the code to the

     According to the default behaviour, the fields are appended as last of the same kind
   */
  log_action("onPerformPaste");
  if (!gRecord) {
    return;
  }

  if (document.activeElement.type == "textarea" || document.activeElement.type == "text"){
    /*we do not want to perform this in case we are in an ordinary text area*/
    return;
  }

  var clipboardContent = clipboardPasteValue();
  if (!clipboardContent) {
    return;
  }

  var record = null;
  try {
    record = decodeMarcXMLRecord(clipboardContent);
  } catch (err) {
    alert("Error when parsing XML occured ... " + err.mesage);
  }

  var changesAdd = []; // the ajax requests for all the fields
  var undoHandlers = [];

  for (tag in record){
    if (gRecord[tag] == undefined){
      gRecord[tag] = [];
    }
    // now appending the fields
    for (fieldInd in record[tag]){
      newPos = gRecord[tag].length;
      gRecord[tag][newPos] = record[tag][fieldInd];
      // enqueue ajax add field request

      isControlfield = record[tag][fieldInd][0].length == 0;
      ind1 = record[tag][fieldInd][1];
      ind2 = record[tag][fieldInd][2];
      subfields = record[tag][fieldInd][0];
      value: record[tag][fieldInd][3]; // in case of a control field

      changesAdd.push({
        recID: gRecID,
        requestType: "addField",
        controlfield : isControlfield,
        fieldPosition : newPos,
        tag: tag,
        ind1: record[tag][fieldInd][1],
        ind2: record[tag][fieldInd][2],
        subfields: record[tag][fieldInd][0],
        value: record[tag][fieldInd][3]
      });

      undoHandler = prepareUndoHandlerAddField(
          tag, ind1, ind2, newPos, subfields, isControlfield, value);
      undoHandlers.push(undoHandler);
    }
  }

  undoHandlers.reverse();
  var undoHandler = prepareUndoHandlerBulkOperation(undoHandlers, "paste");
  addUndoOperation(undoHandler);
  // now sending the Ajax Request
  var optArgs = {
      undoRedo: undoHandler
  };

  createBulkReq(changesAdd, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']])}, optArgs);

  // tags have to be redrawn in the increasing order

  tags = [];
  for (tag in record){
    tags.push(tag);
  }
  tags.sort();
  for (tagInd in tags){
      redrawFields(tags[tagInd], true);
  }
  reColorFields();
}


function addUndoOperation(operation){
  gUndoList.push(operation);
  invalidateRedo();
  updateUrView();
}


function invalidateRedo(){
  /** Invalidates the redo list - after some modification*/
  gRedoList = [];
}


function adjustUndoRedoBtnsActivity(){
  /** Making the undo/redo buttons active/inactive according to the needs
   */
  if (gUndoList.length > 0){
    $("#btnUndo").addAttribute("disabled", "");
  }
  else{
    $("#btnUndo").removeAttr("disabled");
  }

  if (gRedoList.length > 0){
    $("#btnRedo").addAttribute("disabled", "");
  }
  else{
    $("#btnRedo").removeAttr("disabled");
  }
}


function undoMany(number){
  /** A function undoing many operations from the undo list

      Arguments:
        number: number of operations to undo
   */

  var undoOperations = []
  for (i=0;i<number;i++){
    undoOperations.push(getUndoOperation());
  }
  performUndoOperations(undoOperations);
  updateUrView();
}


function prepareUndoHandlerEmpty(){
  /** Creating an empty undo/redo handler - might be useful in some cases
      when undo operation is required but should not be registered
  */
  return {
    operation_type: "no_operation"
  };
}


function prepareUndoHandlerAddField(tag, ind1, ind2, fieldPosition, subfields,
                                    isControlField, value ){
  /** A function creating an undo handler for the operation of affing a new
      field

    Arguments:
      tag:            tag of the field
      ind1:           first indicator (a single character string)
      ind2:           second indicator (a single character string)
      fieldPosition:  a position of the field among other fields with the same
                      tag and possibly different indicators)
      subFields:      a list of fields subfields. each subfield is decribed by
                      a pair: [code, value]
      isControlField: a boolean value indicating if the field is a control field
      value:          a value of a control field. (important in case of passing
                      iscontrolField equal true)
  */

  var result = {};
  result.operation_type = "add_field";
  result.newSubfields = subfields;
  result.tag = tag;
  result.ind1 = ind1;
  result.ind2 = ind2;
  result.fieldPosition = fieldPosition;
  result.isControlField = isControlField;
  if (isControlField){
    // value == false means that we are dealing with a control field
    result.value = value;
  } else{
    result.subfields = subfields;
  }

  return result;
}


function prepareUndoHandlerVisualizeChangeset(changesetNumber, changesListBefore, changesListAfter){
  var result = {};
  result.operation_type = "visualize_hp_changeset";
  result.changesetNumber = changesetNumber;
  result.oldChangesList = changesListBefore;
  result.newChangesList = changesListAfter;
  return result;
}


function prepareUndoHandlerApplyHPChange(changeHandler, changeNo){
  /** changeHandler - handler to the original undo/redo handler associated with the action
   */
  var result = {};
  result.operation_type = "apply_hp_change";
  result.handler = changeHandler;
  result.changeNo = changeNo;
  result.changeType = gHoldingPenChanges[changeNo].change_type;
  return result;
}


function prepareUndoHandlerApplyHPChanges(changeHandlers, changesBefore){
  /** Producing the undo/redo handler associated with application of
      more than one HoldingPen change

      Arguments:
        changeHandlers - a list od undo/redo handlers associated with subsequent changes.
        changesBefore = a list of Holding Pen changes before the operation
   */

  var result = {};
  result.operation_type = "apply_hp_changes";
  result.handlers = changeHandlers;
  result.changesBefore = changesBefore;
  return result;
}


function prepareUndoHandlerRemoveAllHPChanges(hpChanges){
  /** A function preparing the undo handler associated with the
      removal of all the Holding Pen changes present in teh interface */
  var result = {};
  result.operation_type = "remove_all_hp_changes";
  result.old_changes_list = hpChanges;
  return result;
}

function prepareUndoHandlerBulkOperation(undoHandlers, handlerTitle){
  /*
    Preparing an und/redo handler allowing to treat the bulk operations
    ( like for example in case of pasting fields )
    arguments:
      undoHandlers : handlers of separate operations from the bulk
      handlerTitle : a message to be displayed in the undo menu
  */
  var result = {};

  result.operation_type = "bulk_operation";
  result.handlers = undoHandlers;
  result.title = handlerTitle;

  return result;
}


function urPerformAddSubfields(tag, fieldPosition, subfields, isUndo){
    var ajaxData = {
      recID: gRecID,
      requestType: 'addSubfields',
      tag: tag,
      fieldPosition: fieldPosition,
      subfields: subfields,
      undoRedo: (isUndo ? "undo": "redo")
    };

    gRecord[tag][fieldPosition][0] = gRecord[tag][fieldPosition][0].concat(subfields);
    redrawFields(tag, true);
    reColorFields();

    return ajaxData;
}


function performModifyHPChanges(changesList, isUndo){
  /** Undoing or redoing the operation of modifying the changeset
   */
  // first local updates
  gHoldingPenChanges = changesList;
  refreshChangesControls();
  var result = prepareOtherUpdateRequest(isUndo);
  result.undoRedo = isUndo ? "undo" : "redo";
  result.hpChanges = {toOverride: changesList};
  return result;
}


function hideUndoPreview(){
  $("#undoOperationVisualisationField").addClass("bibEditHiddenElement");
  // clearing the selection !
  $(".bibEditURDescEntrySelected").removeClass("bibEditURDescEntrySelected");
}


function getRedoOperation(){
  // getting the operation to be redoed
  currentElement = gRedoList[0];
  gRedoList.splice(0, 1);
  gUndoList.push(currentElement);
  return currentElement;
}


function getUndoOperation(){
  // getting the operation to be undoe
  currentElement = gUndoList[gUndoList.length - 1];
  gUndoList.splice(gUndoList.length - 1, 1);
  gRedoList.splice(0, 0, currentElement);
  return currentElement;
}


function setAllUnselected(){
  // make all the fields and subfields deselected
  setSelectionStatusAll(false);
}


function setSelectionStatusAll(status){
  // Changing the selection status for all the fields
  subfieldBoxes = $('.bibEditBoxSubfield');
  subfieldBoxes.each(function(e){
    if (subfieldBoxes[e].checked != status){
      subfieldBoxes[e].click();
    }
  });
}


function prepareApplyAllHPChangesHandler(){
    // a container for many undo/redo operations in the same time
    throw 'To implement';
}


/*** Handlers for specific operations*/

function renderURList(list, idPrefix, isInverted){
  // rendering the view of undo/redo list into a human-readible HTML
  // list -> an undo or redo list
  // idPrefix -> te prefix of the DOM identifier

  var result = "";
  var isPair = false;
  var helperCnt = 0;

  var iterationBeginning = list.length - 1;
  var iterationJump = -1;
  var iterationEnd = -1;

  if (isInverted === true){
    iterationBeginning = 0;
    iterationJump = 1;
    iterationEnd = list.length;
  }

  for (entryInd = iterationBeginning ; entryInd != iterationEnd ; entryInd += iterationJump){
      result += "<div class=\"" + (isPair ? "bibEditURPairRow" : "bibEditUROddRow" )+ " bibEditURDescEntry\" id=\"" + idPrefix + "_" + helperCnt + "\">";
      result += getHumanReadableUREntry(list[entryInd]);
      result += "</div>";
      isPair = ! isPair;
      helperCnt += 1;
  }
  result += "";
  return result;
}


function prepareApplyHPChangeHandler(){
    // A handler for HoldingPen change application/rejection
    throw 'to implement';
}


function processURUntil(entry){
  // Executing the bulk undo/redo
  var idParts = $(entry).attr("id").split("_");
  var index = parseInt(idParts[1]);

  if (idParts[0] == "undo"){
    undoMany(index+1);
  }
  else{
    redoMany(index+1);
  }
}


function prepareUndoHandlerChangeSubfield (tag, fieldPos, subfieldPos, oldVal,
         newVal, oldCode, newCode, operation_type) {
  var result = {};
  result.operation_type = operation_type;
  result.tag = tag;
  result.oldVal = oldVal;
  result.newVal = newVal;
  result.oldCode = oldCode;
  result.newCode = newCode;
  result.fieldPos = fieldPos;
  result.subfieldPos = subfieldPos;
  return result;
}


function prepareUndoHandlerChangeFieldCode(oldTag, oldInd1, oldInd2, newTag, newInd1,
                                           newInd2, fieldPos, operation_type){
  var result = {};
  result.operation_type = operation_type;
  result.oldTag = oldTag;
  result.oldInd1 = oldInd1;
  result.oldInd2 = oldInd2;
  result.newTag = newTag;
  result.ind1 = newInd1;
  result.ind2 = newInd2;
  result.fieldPos = fieldPos;

  if (gRecord[newTag] == undefined) {
      result.newFieldPos = 0;
  }
  else {
      result.newFieldPos = gRecord[newTag].length;
  }

  return result;
}


function setAllSelected(){
  // make all the fields and subfields selected
  setSelectionStatusAll(true);
}


function showUndoPreview(){
  $("#undoOperationVisualisationField").removeClass("bibEditHiddenElement");
}


function prepareUndoHandlerMoveSubfields(tag, fieldPosition, subfieldPosition, direction){
  var result = {};
  result.operation_type = "move_subfield";
  result.tag = tag;
  result.field_position = fieldPosition;
  result.subfield_position = subfieldPosition;
  result.direction = direction;
  return result;
}
// Handlers to implement:


function setFieldUnselected(tag, fieldPos){
  // unselect a given field
  setSelectionStatusField(tag, fieldPos, false);
}


function urPerformRemoveField(tag, position, isUndo){
  var toDeleteData = {};
  var toDeleteTmp = {};
  toDeleteTmp[position] = [];
  toDeleteData[tag] =  toDeleteTmp;

  // first preparing the data of Ajax request

  var ajaxData = {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDeleteData,
    undoRedo: (isUndo ? "undo": "redo")
  };

  // updating the local model
  gRecord[tag].splice(position,1);
  if (gRecord[tag] == []){
    gRecord[tag] = undefined;
  }
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function prepareOtherUpdateRequest(isUndo){
  return {
    requestType : 'otherUpdateRequest',
    recID : gRecID,
      undoRedo: ((isUndo === true) ? "undo" : "redo"),
    hpChanges: {}
  };
}


function performUndoApplyHpChanges(subRequests, oldChanges){
  /**
   Arguemnts:
     subRequests - subrequests performing the appropriate undo operations
   */

  // removing all teh undo/redo informations as they should be passed globally
  for (ind in subRequests){
      subRequests[ind].undoRedo = undefined;
  }
//  var gHoldingPenChanges
  return {
    requestType: 'applyBulkUpdates',
    undoRedo: "undo",
    requestsData: subRequests,
    hpChanges: {toOverride: oldChanges}
  };
}


function performBulkOperation(subHandlers, isUndo){
  /**
   return the bulk operation
   Arguments:
     subReqs : requests performing the sub-operations
     isUndo - is current request undo or redo ?
   */
  var subReqs = [];
  if (isUndo === true){
    subReqs = preparePerformUndoOperations(subHandlers);
  } else {
    // We can not simply assign and revers as the original would be modified
    var handlers = [];
    for (handlerInd = subHandlers.length -1; handlerInd >= 0; handlerInd--){
      handlers.push(subHandlers[handlerInd]);
    }
    subReqs = preparePerformRedoOperations(handlers);
  }

  for (ind in subReqs){
    subReqs[ind].undoRedo = undefined;
  }

  return {
    requestType: 'applyBulkUpdates',
    undoRedo: (isUndo === true ? "undo" : "redo"),
    requestsData: subReqs,
    hpChanges: {}
  };
}


function preparePerformRedoOperations(operations){
  /** Redos an operation passed as an argument */
  var ajaxRequestsData = [];
  for (operationInd in operations){
    var operation = operations[operationInd];
    var ajaxData = {};
    var isMultiple = false; // is the current decription a list of descriptors ?
    switch (operation.operation_type){
    case "no_operation":
      ajaxData = prepareOtherUpdateRequest(false);
      break;
    case "change_content":
      ajaxData = urPerformChangeSubfieldContent(operation.tag,
                                     operation.fieldPos,
                                     operation.subfieldPos,
                                     operation.newCode,
                                     operation.newVal,
                                     false);
      break;
    case "change_subfield_code":
      ajaxData = urPerformChangeSubfieldCode(operation.tag,
                                     operation.fieldPos,
                                     operation.subfieldPos,
                                     operation.newCode,
                                     operation.newVal,
                                     false);
      break;
    case "change_field_code":
        ajaxData = urPerformChangeFieldCode(operation.newTag,
                                            operation.ind1,
                                            operation.ind2,
                                            operation.oldTag,
                                            operation.oldInd1,
                                            operation.oldInd2,
                                            operation.fieldPos,
                                            false);
      break;
    case "add_field":
      ajaxData = urPerformAddField(operation.isControlField,
                        operation.fieldPosition,
                        operation.tag,
                        operation.ind1,
                        operation.ind2,
                        operation.subfields,
                        operation.value,
                        false);
      break;
     case "add_subfields":
       ajaxData = urPerformAddSubfields(operation.tag,
                             operation.fieldPosition,
                             operation.newSubfields,
                             false);
       break;

    case "delete_fields":
      ajaxData = urPerformDeletePositionedFieldsSubfields(operation.toDelete, false);
      break;

    case "move_field":
      ajaxData = performMoveField(operation.tag, operation.field_position, operation.direction , false);
      break;
    case "move_subfield":
      ajaxData = performMoveSubfield(operation.tag, operation.field_position, operation.subfield_position, operation.direction, false);
      break;
    case "bulk_operation":
      ajaxData = performBulkOperation(operation.handlers, false);
      break;
    case "apply_hp_change":
      removeViewedChange(operation.changeNo); // we redo the change application so the change itself gets removed
      ajaxData = preparePerformRedoOperations([operation.handler]);
      ajaxData[0].hpChange = {};
      ajaxData[0].hpChange.toDisable = [operation.changeNo]; // reactivate this change
      isMultiple = true;
      break;

    case "apply_hp_changes":
      // in this case many changes are applied at once and the list of changes is completely overriden
      ajaxData = performUndoApplyHpChanges();
    case "change_field":
      ajaxData = urPerformChangeField(operation.tag, operation.fieldPos,
                                      operation.newInd1, operation.newInd2,
                                      operation.newSubfields,
                                      operation.newIsControlField,
                                      operation.oldValue , false);
      break;
    case "visualize_hp_changeset":
      ajaxData = prepareVisualizeChangeset(operation.changesetNumber,
        operation.newChangesList, "redo");
      break;
    case "remove_all_hp_changes":
      ajaxData = performModifyHPChanges([], false);
      break;

    default:
      alert("Error: wrong operation to redo");
      break;
    }
    // now dealing with the results
    if (isMultiple){
      // in this case we have to merge lists rather than include inside
      for (elInd in ajaxData){
        ajaxRequestsData.push(ajaxData[elInd]);
      }
    }
    else{
      ajaxRequestsData.push(ajaxData);
    }
  }
  return ajaxRequestsData;
}


function performRedoOperations(operations){
  ajaxRequestsData = preparePerformRedoOperations(operations);
  // now submitting the bulk request
  var optArgs = {
//      undoRedo: "redo"
  };

  var bulk_data = {'requestType' : 'applyBulkUpdates',
                 'requestsData' : ajaxRequestsData,
                 'recID' : gRecID};

  queue_request(bulk_data);
}


function prepareUndoHandlerDeleteFields(toDelete){
  /*Creating Undo/Redo handler for the operation of removal of fields and/or subfields
    Arguments: toDelete - indicates fields and subfields scheduled to be deleted.
      this argument should have a following structure:
      {
        "fields" : { tag: {fieldsPosition: field_structure_similar_to_on_from_gRecord}}
        "subfields" : {tag: { fieldPosition: { subfieldPosition: [code, value]}}}
      }
  */
  var result = {};
  result.operation_type = "delete_fields";
  result.toDelete = toDelete;
  return result;
}


function setSubfieldUnselected(tag, fieldPos, subfieldPos){
 // unseelcting a subfield
  setSelectionStatusSubfield(tag, fieldPos, subfieldPos, false);
}


function prepareUndoHandlerAddSubfields(tag, fieldPosition, subfields){
  /**
    tag : tag of the field inside which the fields should be added
    fieldPosition: position of the field
    subfields: new subfields to be added. This argument should be a list
      of lists representing a single subfield. Each subfield is represented
      by a list, containing 2 elements. [subfield_code, subfield_value]
  */
  var result = {};
  result.operation_type = "add_subfields";
  result.tag = tag;
  result.fieldPosition = fieldPosition;
  result.newSubfields = subfields;
  return result;
}


function setFieldSelected(tag, fieldPos){
  // select a given field
  setSelectionStatusField(tag, fieldPos, true);
}


function redoMany(number){
  // redoing an indicated number of operations
  var redoOperations = [];
  for (i=0;i<number;i++){
    redoOperations.push(getRedoOperation());
  }
  performRedoOperations(redoOperations);
  updateUrView();
}


function urPerformAddField(controlfield, fieldPosition, tag, ind1, ind2, subfields, value, isUndo){
  var ajaxData = {
    recID: gRecID,
    requestType: 'addField',
    controlfield: controlfield,
    fieldPosition: fieldPosition,
    tag: tag,
    ind1: ind1,
    ind2: ind2,
    subfields: subfields,
    value: value,
    undoRedo: (isUndo? "undo": "redo")
  };

  // updating the local situation
  if (gRecord[tag] == undefined){
    gRecord[tag] = [];
  }
  var newField = [(controlfield ? [] : subfields), ind1, ind2,
                  (controlfield ? value: ""), 0];
  gRecord[tag].splice(fieldPosition, 0, newField);
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function urPerformRemoveSubfields(tag, fieldPosition, subfields, isUndo){
  var toDelete = {};
  toDelete[tag] = {};
  toDelete[tag][fieldPosition] = []
  var startingPosition = gRecord[tag][fieldPosition][0].length - subfields.length;
  for (var i=startingPosition, n=gRecord[tag][fieldPosition][0].length; i<n ; i++){
    toDelete[tag][fieldPosition].push(i);
  }

  var ajaxData = {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    undoRedo: (isUndo ? "undo": "redo")
  };

  // modifying the client-side interface
  gRecord[tag][fieldPosition][0].splice( gRecord[tag][fieldPosition][0].length - subfields.length, subfields.length);
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function updateUrView(){
  /*Updating the information box in the bibEdit menu
    (What are the current undo/redo handlers*/
  $('#undoOperationVisualisationFieldContent')[0].innerHTML = (gUndoList.length == 0) ? "(empty)" :
        renderURList(gUndoList, "undo");
//        gUndoList[gUndoList.length - 1].operation_type;
  $('#redoOperationVisualisationFieldContent')[0].innerHTML = (gRedoList.length == 0) ? "(empty)" :
        renderURList(gRedoList, "redo", true);

  // now attaching the events ... the function is uniform for all the elements present inside the document

    var urEntries = $('.bibEditURDescEntry');
    urEntries.each(function(index){
        $(urEntries[index]).bind("mouseover", function (e){
          $(urEntries[index]).find(".bibEditURDescEntryDetails").removeClass("bibEditHiddenElement");
            urMarkSelectedUntil(urEntries[index]);
        });
        $(urEntries[index]).bind("mouseout", function(e){
          $(urEntries[index]).find(".bibEditURDescEntryDetails").addClass("bibEditHiddenElement");
        });
        $(urEntries[index]).bind("click", function(e){
            processURUntil(urEntries[index]);
        });
    });
}


function performMoveSubfield(tag, fieldPosition, subfieldIndex, direction, undoRedo){
  var newSubfieldIndex = parseInt(subfieldIndex) + (direction == "up" ? -1 : 1);
  var fieldID = tag + '_' + fieldPosition;
  var field = gRecord[tag][fieldPosition];
  var subfields = field[0];

  // Create Ajax request.
  var ajaxData = {
    recID: gRecID,
    requestType: 'moveSubfield',
    tag: tag,
    fieldPosition: fieldPosition,
    subfieldIndex: subfieldIndex,
    newSubfieldIndex: newSubfieldIndex,
    undoRedo: (undoRedo == true) ?  "undo" : ((undoRedo == false) ?  "redo" : undoRedo)
  };

  // Continue local updating.
  var subfieldToSwap = subfields[newSubfieldIndex];
  subfields[newSubfieldIndex] = subfields[subfieldIndex];
  subfields[subfieldIndex] = subfieldToSwap;
  var rowGroup = $('#rowGroup_' + fieldID);
  var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
  $(rowGroup).replaceWith(createField(tag, field, fieldPosition));
  if (coloredRowGroup)
    $('#rowGroup_' + fieldID).addClass('bibEditFieldColored');

  // taking care of having only the new subfield position selected
  setAllUnselected();
  setSubfieldSelected(tag, fieldPosition, newSubfieldIndex);

  return ajaxData;
}


function onRedo(evt){
  log_action("redo");
  if (gRedoList.length <= 0){
    alert("No Redo operations to process");
    return;
  }
  redoMany(1);
}

// functions related to the automatic field selection/unseletion

function hideRedoPreview(){
  $("#redoOperationVisualisationField").addClass("bibEditHiddenElement");
  // clearing the selection !
  $(".bibEditURDescEntrySelected").removeClass("bibEditURDescEntrySelected");
}


function urPerformAddPositionedFieldsSubfields(toAdd, isUndo){
  return createFields(toAdd, isUndo);
}


function setSubfieldSelected(tag, fieldPos, subfieldPos){
  // selecting a subfield
  setSelectionStatusSubfield(tag, fieldPos, subfieldPos, true);
}


function getHumanReadableUREntry(handler){
  // rendering a human readable description of an undo/redo operation
  // handler : the u/r handler to render
  var operationDescription;

  switch (handler.operation_type){
    case "move_field":
      operationDescription = "move field";
      break;
    case "move_field":
      operationDescription = "change field";
      break;
    case "move_subfield":
      operationDescription = "move subfield";
      break;
    case "change_content":
      operationDescription = "edit subfield";
      break;
    case "change_subfield_code":
      operationDescription = "edit subfield code";
      break;
    case "change_field_code":
      operationDescription = "edit field code";
      break;
    case "add_field":
      operationDescription = "add field";
      break;
    case "add_subfields":
      operationDescription = "add field";
      break;
    case "delete_fields":
      operationDescription = "delete";
      break;
    case "bulk_operation":
      operationDescription = handler.title;
      break;
    case "apply_hp_change":
      operationDescription = "holding pen";
      break;
    case "visualize_hp_changeset":
      operationDescription = "show changes";
      break;
    case "remove_all_hp_changes":
      operationDescription = "remove changes";
      break;
    default:
      operationDescription = "unknown operation";
      break;
  }

  // now rendering parameters of the handler
  var readableDescriptors = {
    'tag' : 'tag',
    'operation_type' : false,
    'field_position' : false,
    'subfield_position' : false,
    'subfieldPos' : false,
    'newVal' : 'new value',
    'oldVal' : 'old value',
    'fieldPos' : false,
    'toDelete' : false,
    'handlers' : false,
    'newFieldPos' : false
  };

  var handlerDetails = '<table>';

  for (characteristic in handler){
    if (readableDescriptors[characteristic] != false){
      var characteristicString = characteristic;
      if (readableDescriptors[characteristic] != undefined){
          characteristicString = readableDescriptors[characteristic];
      }
      handlerDetails += '<tr><td class="bibEditURDescChar">'
        + characteristicString + ':</td><td>' + handler[characteristic]  + '</td></tr>';
    }
  }

  handlerDetails += '</table>';
  // now generating the final result
  return '<div class="bibEditURDescHeader">'
    + operationDescription + '</div><div class="bibEditURDescEntryDetails bibEditHiddenElement">'
    + handlerDetails + '</div>';
}


function urMarkSelectedUntil(entry){
    // marking all the detailed entries, until a given one as selected
    //  these entries have the same prefix but a smaller number
    var identifierParts = $(entry).attr("id").split("_");
    var position = parseInt(identifierParts[1]);
    var potentialElements = $(".bibEditURDescEntry");
    potentialElements.each(function(index){
        var curIdentifierParts = $(potentialElements[index]).attr("id").split("_");
        if ((curIdentifierParts[0] == identifierParts[0]) && (parseInt(curIdentifierParts[1]) <= position)){
           $(potentialElements[index]).addClass("bibEditURDescEntrySelected");
        }
        else {
           $(potentialElements[index]).removeClass("bibEditURDescEntrySelected");
        }
    });
}


function onUndo(evt){
  log_action("undo");
  if (gUndoList.length <= 0){
    alert("No Undo operations to process");
    return;
  }
  undoMany(1);
}


function preparePerformUndoOperations(operations){
  /** Undos an operation passed as an argument */
  var ajaxRequestsData = [];
  for (operationInd in operations){
    var operation = operations[operationInd];
    var action = null;
    var actionData = null;
    var ajaxData = {};
    var isMultiple = false; // is the current oepration handler a list
      // of operations rather than a single op ?

    switch (operation.operation_type){
    case "no_operation":
      ajaxData = prepareOtherUpdateRequest(true);
      break;
    case "change_content":
      ajaxData = urPerformChangeSubfieldContent(operation.tag,
                                                operation.fieldPos,
                                                operation.subfieldPos,
                                                operation.oldCode,
                                                operation.oldVal,
                                                true);
      break;
    case "change_subfield_code":
      ajaxData = urPerformChangeSubfieldCode(operation.tag,
                                             operation.fieldPos,
                                             operation.subfieldPos,
                                             operation.oldCode,
                                             operation.oldVal,
                                             true);
      break;
    case "change_field_code":
      ajaxData = urPerformChangeFieldCode(operation.oldTag,
                                          operation.oldInd1,
                                          operation.oldInd2,
                                          operation.newTag,
                                          operation.ind1,
                                          operation.ind2,
                                          operation.newFieldPos,
                                          true);
      break;
    case "add_field":
      ajaxData = urPerformRemoveField(operation.tag,
                                      operation.fieldPosition,
                                      true);
      break;
    case "add_subfields":
      ajaxData = urPerformRemoveSubfields(operation.tag,
                                          operation.fieldPosition,
                                          operation.newSubfields,
                                          true);
      break;

    case "delete_fields":
      ajaxData = urPerformAddPositionedFieldsSubfields(operation.toDelete, true);
      break;

    case "move_field":
      var newDirection = "up";
      var newPosition = operation.field_position + 1;
      if (operation.direction == "up"){
        newDirection = "down";
        newPosition = operation.field_position - 1;
      }

      ajaxData = performMoveField(operation.tag, newPosition, newDirection, true);
      break;
    case "move_subfield":

      var newDirection = "up";
      var newPosition = operation.subfield_position + 1;
      if (operation.direction == "up"){
        newDirection = "down";
        newPosition = operation.subfield_position - 1;
      }
      ajaxData = performMoveSubfield(operation.tag, operation.field_position,
        newPosition, newDirection, true);
      break;
    case "bulk_operation":
      ajaxData = performBulkOperation(operation.handlers, true);
      break;
    case "apply_hp_change":
      ajaxData = preparePerformUndoOperations([operation.handler]);
      ajaxData[0]["hpChange"] = {};
      ajaxData[0]["hpChange"]["toEnable"] = [operation.changeNo]; // reactivate
      isMultiple = true;
      revertViewedChange(operation.changeNo);
      break;
    case "visualize_hp_changeset":
      ajaxData = prepareUndoVisualizeChangeset(operation.changesetNumber,
        operation.oldChangesList);
      break;
    case "change_field":
      ajaxData = urPerformChangeField(operation.tag, operation.fieldPos,
                                      operation.oldInd1, operation.oldInd2,
                                      operation.oldSubfields,
                                      operation.oldIsControlField,
                                      operation.oldValue , true);
      break;
    case "remove_all_hp_changes":
      ajaxData = performModifyHPChanges(operation.old_changes_list, true);
      break;
    default:
      alert("Error: wrong operation to undo");
    }

    if (isMultiple){
      // in this case we have to merge lists rather than include inside
      for (elInd in ajaxData){
        ajaxRequestsData.push(ajaxData[elInd]);
      }
    }
    else{
      ajaxRequestsData.push(ajaxData);
    }
  }

  return ajaxRequestsData;
}


function performUndoOperations(operations){
  var ajaxRequestsData = preparePerformUndoOperations(operations);
  // now submitting the ajax request
  var optArgs={
//    undoRedo: "undo"
  };

  var bulk_data = {'requestType' : 'applyBulkUpdates',
               'requestsData' : ajaxRequestsData,
               'recID' : gRecID};

  queue_request(bulk_data);
}


function prepareUndoHandlerMoveField(tag, fieldPosition, direction){
  var result = {};
  result.tag = tag;
  result.operation_type = "move_field";
  result.field_position = fieldPosition;
  result.direction = direction;
  return result;
}


function prepareUndoHandlerChangeField(tag, fieldPos,
  oldInd1, oldInd2, oldSubfields, oldIsControlField, oldValue,
  newInd1, newInd2, newSubfields, newIsControlField, newValue){
  /** Function building a handler allowing to undo the operation of
      changing the field structure.

      Changing can happen only if tag and position remain the same,
      Otherwise we deal with removal and adding of a field

      Arguments:
        tag - tag of a field
        fieldPos - position of a field

        oldInd1, oldInd2 - indices of the old field
        oldSubfields - subfields present int the old structure
        oldIsControlField - a boolean value indicating if the field
                            is a control field
        oldValue - a value before change in case of field being a control field.
                   if the field is normal field, this should be equal ""

        newInd1, newInd2, newSubfields, newIsControlField, newValue -
           Similar parameters describing new structure of a field
  */
  var result = {};
  result.operation_type = "change_field";
  result.tag = tag;
  result.fieldPos = fieldPos;
  result.oldInd1 = oldInd1;
  result.oldInd2 = oldInd2;
  result.oldSubfields = oldSubfields;
  result.oldIsControlField = oldIsControlField;
  result.oldValue = oldValue;
  result.newInd1 = newInd1;
  result.newInd2 = newInd2;
  result.newSubfields = newSubfields;
  result.newIsControlField = newIsControlField;
  result.newValue = newValue;

  return result;
}

function showRedoPreview(){
  $("#redoOperationVisualisationField").removeClass("bibEditHiddenElement");
}


function deleteFields(toDeleteStruct, undoRedo){
  // a function deleting the specified fields on both client and server sides
  //
  // toDeleteFields : a structure describing fields and subfields to delete
  //   this structure is the same as for the function createFields

  var toDelete = {};

  // first we convert the data into a different format, loosing the informations about
  //   subfields of entirely removed fields

  // first the entirely deleted fields
  for (tag in toDeleteStruct.fields){
    if (toDelete[tag] == undefined){
      toDelete[tag] = {};
    }
    for (fieldPos in toDeleteStruct.fields[tag]){
      toDelete[tag][fieldPos] = [];
    }
  }

  for (tag in toDeleteStruct.subfields){
    if (toDelete[tag] == undefined){
      toDelete[tag] = {};
    }
    for (fieldPos in toDeleteStruct.subfields[tag]){
      toDelete[tag][fieldPos] = [];
      for (subfieldPos in toDeleteStruct.subfields[tag][fieldPos]){
        toDelete[tag][fieldPos].push(subfieldPos);
      }
    }
  }

  var tagsToRedraw = [];

  // reColorTable is true if any field are completely deleted.
  var reColorTable = false;

  // first we have to encode all the data in a single dictionary

  // Create Ajax request.
  var ajaxData = {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    undoRedo: (undoRedo == true) ? "undo" : ((undoRedo == false) ? "redo" : undoRedo)
  };

  // Continue local updating.
  // Parse data structure and delete accordingly in record.
  var fieldsToDelete, subfieldIndexesToDelete, field, subfields, subfieldIndex;
  for (var tag in toDelete) {
    tagsToRedraw.push(tag);
    fieldsToDelete = toDelete[tag];
    // The fields should be treated in the decreasing order (during the removal, indices may change)
    traversingOrder = [];
    for (fieldPosition in fieldsToDelete) {
      traversingOrder.push(fieldPosition);
    }
    // normal sorting will do this in a lexycographical order ! (problems if > 10 subfields
    // function provided, allows sorting in the reversed order
    var traversingOrder = traversingOrder.sort(function(a, b){
      return b - a;
    });

    for (var fieldInd in traversingOrder) {
      var fieldPosition = traversingOrder[fieldInd];
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
        for (var j = subfieldIndexesToDelete.length - 1; j >= 0; j--){
          for (var change in gHoldingPenChanges) {
              if ((gHoldingPenChanges[change]["tag"] == tag) && (gHoldingPenChanges[change]["field_position"] == fieldPosition)) {  // TODO add indicators
                    if (gHoldingPenChanges[change]["subfield_position"] == subfieldIndexesToDelete[j]) {
                      // there are more changes associated with this field ! They are no more correct
                      // and should be removed... it is also possible to consider transforming them into add field
                      // change, but seems to be an unnecessary effort
                      gHoldingPenChanges[change].applied_change = true;
                    }
                    else if (gHoldingPenChanges[change]["subfield_position"] > subfieldIndexesToDelete[j]) {
                      gHoldingPenChanges[change]["subfield_position"] -= 1;
                    }
                }
          }
          subfields.splice(subfieldIndexesToDelete[j], 1);
        }
      }
    }
  }

  // If entire fields has been deleted, redraw all fields with the same tag
  // and recolor the full table.
  for (tag in tagsToRedraw) {
      redrawFields(tagsToRedraw[tag], true);
  }
  reColorFields();

  return ajaxData;
}


function getSelectedFields(){
  /** Function returning a list of selected fields
    Returns all the fields and subfields that are slected.
    The structure of a result is following:
    {
      "fields" : { tag: {fieldsPosition: field_structure_similar_to_on_from_gRecord}}
      "subfields" : {tag: { fieldPosition: { subfieldPosition: [code, value]}}}
    }
  */
  var selectedFields = {};
  var selectedSubfields = {};

  var checkedFieldBoxes = $('input[class="bibEditBoxField"]:checked');
  var checkedSubfieldBoxes = $('input[class="bibEditBoxSubfield"]:checked');

  if (!checkedFieldBoxes.length && !checkedSubfieldBoxes.length)
    // No fields selected
    return;

  // Collect fields to be deleted in toDelete.
  $(checkedFieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2];
    if (!selectedFields[tag]) {
      selectedFields[tag] = {};
    }
    selectedFields[tag][fieldPosition] = gRecord[tag][fieldPosition];
  });

  // Collect subfields to be deleted in toDelete.
  $(checkedSubfieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2], subfieldIndex = tmpArray[3];
    if (selectedFields[tag] == undefined || selectedFields[tag][fieldPosition] == undefined){
      // this field has not been selected entirely, we can proceed with processing subfield slection
      if (!selectedSubfields[tag]) {
        selectedSubfields[tag] = {};
        selectedSubfields[tag][fieldPosition] = {};
        selectedSubfields[tag][fieldPosition][subfieldIndex] =
          gRecord[tag][fieldPosition][0][subfieldIndex];
      }
      else {
        if (!selectedSubfields[tag][fieldPosition])
          selectedSubfields[tag][fieldPosition] = {};
        selectedSubfields[tag][fieldPosition][subfieldIndex] =
          gRecord[tag][fieldPosition][0][subfieldIndex];
      }
    } else {
      // this subfield is a part of entirely selected field... we have already included the information about subfields
    }
  });
  var result={};
  result.fields = selectedFields;
  result.subfields = selectedSubfields;
  return result;
}


function urPerformChangeSubfieldContent(tag, fieldPos, subfieldPos, code, val, isUndo){
  // changing the server side model
  var ajaxData = {
    recID: gRecID,
    requestType: 'modifyContent',
    tag: tag,
    fieldPosition: fieldPos,
    subfieldIndex: subfieldPos,
    subfieldCode: code,
    value: val,
    undoRedo: (isUndo ? "undo": "redo")
  };

  // changing the model
  gRecord[tag][fieldPos][0][subfieldPos][0] = code;
  gRecord[tag][fieldPos][0][subfieldPos][1] = val;

  // changing the display .... what if being edited right now ?
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function urPerformChangeSubfieldCode(tag, fieldPos, subfieldPos, code, val, isUndo){
  // changing the server side model
  var ajaxData = {
    recID: gRecID,
    requestType: 'modifySubfieldTag',
    tag: tag,
    fieldPosition: fieldPos,
    subfieldIndex: subfieldPos,
    subfieldCode: code,
    value: val,
    undoRedo: (isUndo ? "undo": "redo")
  };

  gRecord[tag][fieldPos][0][subfieldPos][0] = code;
  gRecord[tag][fieldPos][0][subfieldPos][1] = val;

  // changing the display .... what if being edited right now ?
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function urPerformChangeFieldCode(oldTag, oldInd1, oldInd2, newTag, ind1, ind2,
                                  fieldPos, isUndo){
  // changing the server side model
  var ajaxData = {
    recID: gRecID,
    requestType: 'modifyFieldTag',
    oldTag: newTag,
    oldInd1: ind1,
    oldInd2: ind2,
    newTag: oldTag,
    fieldPosition: fieldPos,
    ind1: oldInd1,
    ind2: oldInd2,
    undoRedo: (isUndo ? "undo": "redo")
  };

  // updating the local model
  var currentField = gRecord[newTag][fieldPos];
  currentField[1] = oldInd1;
  currentField[2] = oldInd2;
  gRecord[newTag].splice(fieldPos,1);
  if (gRecord[newTag].length == 0){
      delete gRecord[newTag];
  }
  var fieldNewPos;
  if (gRecord[oldTag] == undefined) {
      fieldNewPos = 0;
      gRecord[oldTag] = [];
      gRecord[oldTag][fieldNewPos] = currentField;
  }
  else {
      fieldNewPos = gRecord[oldTag].length;
      gRecord[oldTag].splice(fieldNewPos, 0, currentField);
  }
  // changing the display .... what if being edited right now ?
  redrawFields(newTag, true);
  redrawFields(oldTag, true);
  reColorFields();

  return ajaxData;
}


function performChangeField(tag, fieldPos, ind1, ind2, subFields, isControlfield,
  value, undoRedo){
  /** Function changing the field structure and generating an appropriate AJAX
      request handler
      Arguments:
        tag, fieldPos, ind1, ind2, subFields, isControlfield, value - standard
          values describing a field. tag, fieldPos are used to locate the field
          instance (which has to exist) and its content is modified accordingly.
        undoRedo - a undoRedo Handler or one of the words "undo"/"redo"
   */
  var ajaxData = {
    recID: gRecID,
    requestType: "modifyField",
    controlfield : isControlfield,
    fieldPosition : fieldPos,
    ind1: ind1,
    ind2: ind2,
    tag: tag,
    subFields: subFields,
    undoRedo : undoRedo,
    hpChanges: {}
  }

  // local changes
  gRecord[tag][fieldPos][0] = subFields;
  gRecord[tag][fieldPos][1] = ind1;
  gRecord[tag][fieldPos][2] = ind2;
  gRecord[tag][fieldPos][3] = value;
  redrawFields(tag, true);
  reColorFields();

  return ajaxData;
}


function urPerformChangeField(tag, fieldPos, ind1, ind2, subFields,
  isControlfield, value, isUndo){
  /**
   */
  return performChangeField(tag, fieldPos, ind1, ind2, subFields,
    isControlfield, value, (isUndo ? "undo" : "redo"));
}


function performMoveField(tag, oldFieldPosition, direction, undoRedo){
  var newFieldPosition = oldFieldPosition + (direction == "up" ? -1 : 1);
  // Create Ajax request.
  var ajaxData = {
    recID: gRecID,
    requestType: 'moveField',
    tag: tag,
    fieldPosition: oldFieldPosition,
    direction: direction,
    undoRedo: (undoRedo == true) ? "undo" : ((undoRedo == false) ? "redo" : undoRedo)
  };

  //continue updating locally
  var currentField = gRecord[tag][oldFieldPosition];
  gRecord[tag][oldFieldPosition] = gRecord[tag][newFieldPosition];
  gRecord[tag][newFieldPosition] = currentField;

  $('tbody#rowGroup_'+tag+'_'+(newFieldPosition)).replaceWith(
      createField(tag, gRecord[tag][newFieldPosition], newFieldPosition));
  $('tbody#rowGroup_'+tag+'_'+oldFieldPosition).replaceWith(
      createField(tag, gRecord[tag][oldFieldPosition], oldFieldPosition));

  reColorFields();

  // Now taking care of having the new field selected and the rest unselected
  setAllUnselected();
  setFieldSelected(tag, newFieldPosition);
//$('#boxField_'+tag+'_'+(newFieldPosition)).click();
  return ajaxData;
}


function setSelectionStatusField(tag, fieldPos, status){
  var fieldCheckbox = $('#boxField_' + tag + '_' + fieldPos);
  var subfieldCheckboxes = $('#rowGroup_' + tag + '_' + fieldPos + ' .bibEditBoxSubfield');

  fieldCheckbox.each(function(ind){
      if (fieldCheckbox[ind].checked != status)
      {
          fieldCheckbox[ind].click();
      }
  });
}


function urPerformDeletePositionedFieldsSubfields(toDelete, isUndo){
  return deleteFields(toDelete, isUndo);
}

/** General Undo/Redo treatment lists */

function setSelectionStatusSubfield(tag, fieldPos, subfieldPos, status){
  var subfieldCheckbox = $('#boxSubfield_' + tag + '_' + fieldPos + '_' + subfieldPos);
  if (subfieldCheckbox[0].checked != status)
  {
      subfieldCheckbox[0].click();
  }
}


function createFields(toCreateFields, isUndo){
  // a function adding fields.
  // toCreateFields : a structure describing fields and subfields to create
  //   this structure is the same as for the function deleteFields

  // 1) Preparing the AJAX request
  var tagsToRedraw = {};
  var ajaxData = {
    recID: gRecID,
    requestType: 'addFieldsSubfieldsOnPositions',
    fieldsToAdd: toCreateFields.fields,
    subfieldsToAdd: toCreateFields.subfields
  };

  if (isUndo != undefined){
    ajaxData['undoRedo'] = (isUndo ? "undo": "redo");
  }

  // 2) local processing -> creating the fields locally
  //   - first creating the missing fields so all the subsequent field indices are correcr
  for (tag in toCreateFields.fields){
    if (gRecord[tag] == undefined){
      gRecord[tag] = [];
    }
    tagsToRedraw[tag] = true;
    var fieldIndices = [];
    for (fieldPos in toCreateFields.fields[tag]){
      fieldIndices.push(fieldPos);
    }
    fieldIndices.sort(); // we have to add fields in the increasing order
      for (indInd in fieldIndices){
        var fieldIndexToAdd = fieldIndices[indInd]; // index of the field index to add in the indices array
        var newField = toCreateFields.fields[tag][fieldIndexToAdd];
        gRecord[tag].splice(fieldIndexToAdd, 0, newField);
      }
  }

  //   - now appending the remaining subfields

  for (tag in toCreateFields.subfields){
    tagsToRedraw[tag] = true;
    for (fieldPos in toCreateFields.subfields[tag]){
      var subfieldPositions = [];
      for (subfieldPos in toCreateFields.subfields[tag][fieldPos]){
        subfieldPositions.push(subfieldPos);
      }
      subfieldPositions.sort();
      for (subfieldInd in subfieldPositions){
        subfieldPosition = subfieldPositions[subfieldInd];
        gRecord[tag][fieldPos][0].splice(
          subfieldPosition, 0,
          toCreateFields.subfields[tag][fieldPos][subfieldPosition]);
      }
    }
  }

  // - redrawint the affected tags

  for (tag in tagsToRedraw){
   redrawFields(tag, true);
  }
  reColorFields();

  return ajaxData;
}


/* Bibcirculation Panel functions */

function isBibCirculationPanelNecessary(){
  /** A function checking if the BibCirculation connectivity panel should
      be displayed. This information is derieved from the state of the record.
      Returns true or false
  */

  if (gRecID === null){
    return false;
  }

  // only if the record is saved and exists in the database and belongs
  // to a particular colelction
  return gDisplayBibCircPanel;
}


function updateBibCirculationPanel(){
  /** Updates the BibCirculation panel contents and visibility
  */
  if (gDisplayBibCircPanel === false){
    // in case, the panel is present, should be hidden
    $("#bibEditBibCircConnection").addClass("bibEditHiddenElement");
  }
  else {
    // the panel must be present - we have to show it
    $(".bibEditBibCircConnection").removeClass("bibEditHiddenElement");
  }

  var interfaceElement = $("#bibEditBibCircConnection");
  if (isBibCirculationPanelNecessary()){
    interfaceElement.removeClass("bibEditHiddenElement");
  } else {
    interfaceElement.addClass("bibEditHiddenElement");
  }

  // updating the content
  var copiesCountElement = $('#bibEditBibCirculationCopies');
  copiesCountElement.attr("innerHTML", gPhysCopiesNum);
}


function bibCircIntGetEditCopyUrl(recId){
  /**A function returning the address under which, the edition of a
      given record is possible
  */

//  return "/admin/bibcirculation/bibcirculationadmin.py/get_item_details?recid=" + recId;
  return gBibCircUrl;
}


function onBibCirculationBtnClicked(e){
  /** A function redirecting the user to the BibCiculation web interface
  */
  var link = bibCircIntGetEditCopyUrl(gRecID);
  window.open(link);
}



/* ---- Helper functions for adding subfields into the subfield content ---- */

function valueContainsSubfields(value) {
    /*
     * Purpose: Check if value has subfields inside. E.g. test$$xAnother test
     *
     * Input(s): string:value - value introduced into the subfield
     *
     * Returns: boolean - true (subfields inside), false (no subfields)
     */
    var regExp = new RegExp(".*\\$\\$[0-9a-zA-Z].*");
    return regExp.test(value);
}


function splitContentSubfields(value, subfieldCode, subfieldsToAdd, isSubject) {
    /*
     * Purpose: split content into pairs subfield index - subfield value
     *
     * Input(s): string:value - value introduced into the subfield
     *           Array:subfieldsToAdd - will contain all subfields extracted
     *
     */
    var splitValue = value.split('$$');
    subfieldsToAdd.push(new Array(subfieldCode, splitValue[0]));
    for (var i=1, n=splitValue.length; i<n; i++) {
        var subfieldValue = splitValue[i].substring(1);
        if (isSubject) {
          subfieldValue = check_subjects_KB(subfieldValue);
        }
        subfieldsToAdd.push(new Array(splitValue[i][0], subfieldValue));
    }
}


/* ---- All functions related to change in an editable area ---- */


function is_reference_manually_curated(field) {
  /*
   * Checks if the given field has a subfield with code 9 and content
   * CURATOR. Used to check if a reference is manually curated
   */
    for (var i=0, n=field[0].length; i < n; i++) {
        if (field[0][i][0] == '9' && field[0][i][1] == "CURATOR")
            return true;
    }
    return false;
}


/**
 * Checks if the field being edited is a subject field
 * @param  {String}  tag_ind
 * @param  {String}  subfield_code
 * @return {Boolean}
 */
function isSubjectSubfield(tag_ind, subfield_code) {
  return (tag_ind === "65017" && subfield_code === "a")
}


/**
 * Helper function to clean the content inputed by a user in a cell
 * @param  {String} value
 * @return {String}
 */
function sanitize_value(value) {
  value = value.replace(/\n/g, ' '); // Replace newlines with spaces.
  value = value.replace(/^\s+|\s+$/g,""); // Remove whitespace from the ends of strings
  return value;
}


/**
 * Function called when a field tag is changed
 * @param  {String} value
 * @param  {Object} cell
 * @return {String}
 */
function onFieldTagChange(value, cell) {
    log_action("onFieldTagChange " + value);

    function updateModel() {
        var currentField = gRecord[oldTag][cell.fieldPosition];
        currentField[1] = newInd1;
        currentField[2] = newInd2;
        gRecord[oldTag].splice(cell.fieldPosition,1);
        if (gRecord[oldTag].length == 0){
            delete gRecord[oldTag];
        }
        var fieldNewPos;
        if (gRecord[newTag] == undefined) {
            fieldNewPos = 0;
            gRecord[newTag] = [];
            gRecord[newTag][fieldNewPos] = currentField;
        }
        else {
            fieldNewPos = gRecord[newTag].length;
            gRecord[newTag].splice(fieldNewPos, 0, currentField);
        }

    }

    function redrawTags() {
        redrawFields(oldTag, true);
        redrawFields(newTag, true);
        reColorFields();
    }

    var old_value = cell.tag_ind;

    if (old_value.replace(/_/g, " ") === value.replace(/_/g, " ")) {
        return value;
    }

    /* Create undo/redo handler */
    var oldTag = old_value.substring(0,3),
        oldInd1 = old_value.substring(3,4),
        oldInd2 = old_value.substring(4,5),
        newTag = value.substring(0,3),
        newInd1 = value.substring(3,4),
        newInd2 = value.substring(4,5),
        operation_type = "change_field_code";

    urHandler = prepareUndoHandlerChangeFieldCode(oldTag,
                                                oldInd1,
                                                oldInd2,
                                                newTag,
                                                newInd1,
                                                newInd2,
                                                cell.fieldPosition,
                                                operation_type);
    addUndoOperation(urHandler);

    /* Send AJAX request */
    updateFieldTag(oldTag, newTag, oldInd1, oldInd2, newInd1, newInd2,
                    cell.fieldPosition, null, urHandler);

    /* Update client side model */
    updateModel();
    redrawTags();
    highlight_change(cell, value);

    return value;
}


/**
 * Function called when a subfield code is changed
 * @param  {String} value
 * @param  {Object} cell
 * @return {Object}
 */
function onSubfieldCodeChange(value, cell) {
  log_action("onSubfieldCodeChange " + value);

  function updateModel() {
    subfield_instance[0] = value;
  }

  var field_instance = gRecord[cell.tag][cell.fieldPosition];
  var subfield_instance = field_instance[0][cell.subfieldIndex];

  if (subfield_instance[0] == value) {
    return value;
  }

  var old_subfield_code = subfield_instance[0]; // get old subfield code from gRecord
  var operation_type = "change_subfield_code";
  urHandler = prepareUndoHandlerChangeSubfield(cell.tag,
                                               cell.fieldPosition,
                                               cell.subfieldIndex,
                                               subfield_instance[1],
                                               subfield_instance[1],
                                               old_subfield_code,
                                               value,
                                               operation_type);
  addUndoOperation(urHandler);

  updateSubfieldValue(cell.tag, cell.fieldPosition, cell.subfieldIndex, value,
                      subfield_instance[1], null, urHandler, true);

  updateModel();

  highlight_change(cell, value);

  return value;
}


/**
 * Function called when a subfield value is changed
 * @param  {String} value
 * @param  {Object} cell
 * @return {String}
 */
function onContentChange(value, cell) {
  log_action("onContentChange " + value);

  function redrawTags() {
    redrawFieldPosition(cell.tag, cell.fieldPosition);
    reColorFields();
  }

  function updateModel() {
    subfield_instance[1] = value;
    field_instance[0].push.apply(field_instance[0], subfieldsToAdd);
  }

  /* Get field instance to be updated from global variable gRecord */
  var field_instance = gRecord[cell.tag][cell.fieldPosition];
  var subfield_instance = field_instance[0][cell.subfieldIndex];

  /* Nothing has changed, return */
  if (subfield_instance[1] === value) {
    return value;
  }

  var isSubject = isSubjectSubfield(cell.tag_ind, subfield_instance[0]);
  var subfieldsToAdd = [],
      bulkOperation = false;
  var old_subfield_code = subfield_instance[0];
  var old_subfield_value = subfield_instance[1];

  /* Check if there are subfields inside of the content value
  * e.g 999C5 $$mThis a test$$hThis is a second subfield */
  if (valueContainsSubfields(value)) {
    bulkOperation = true;
    splitContentSubfields(value, old_subfield_code, subfieldsToAdd, isSubject);

    value = subfieldsToAdd[0][1];
    subfieldsToAdd = subfieldsToAdd.slice(1);
  }
  else {
    /* If editing subject field, check KB */
    if (isSubject) {
      value = check_subjects_KB(value);
    }
  }

  /* If editing a reference, add curator subfield */
  if (cell.tag_ind == '999C5' && !is_reference_manually_curated(field_instance)) {
    bulkOperation = true;
    subfieldsToAdd.push(new Array('9', 'CURATOR'));
  }

  if (bulkOperation) {
    /* Prepare  undo handlers to modify subfield content and to
     * add new subfields */
    var undoHandlers = [];
    undoHandlers.push(prepareUndoHandlerChangeSubfield(cell.tag,
                                             cell.fieldPosition,
                                             cell.subfieldIndex,
                                             old_subfield_value,
                                             value,
                                             subfield_instance[0],
                                             subfield_instance[0],
                                             "change_content"));

    undoHandlers.push(prepareUndoHandlerAddSubfields(cell.tag,
                                                     cell.fieldPosition,
                                                     subfieldsToAdd));

    urHandler = prepareUndoHandlerBulkOperation(undoHandlers, "addSubfields");
    addUndoOperation(urHandler);

    bulkUpdateSubfieldContent(cell.tag, cell.fieldPosition, cell.subfieldIndex, subfield_instance[0], value, null,
                              urHandler, subfieldsToAdd);

    updateModel();
    redrawTags();
  }
  else {
    operation_type = "change_content";
    urHandler = prepareUndoHandlerChangeSubfield(cell.tag,
                                                 cell.fieldPosition,
                                                 cell.subfieldIndex,
                                                 old_subfield_value,
                                                 value,
                                                 old_subfield_code,
                                                 old_subfield_code,
                                                 operation_type);
    addUndoOperation(urHandler);

    updateSubfieldValue(cell.tag, cell.fieldPosition, cell.subfieldIndex, old_subfield_code,
                        value, null, urHandler);
    updateModel();
  }

  highlight_change(cell, value);

  return value;

}


/**
 * Extracts all the relevant info from the cell object
 * @param  {Object} th
 * @return {Object}
 */
function get_cell_info(th) {
  var cell = {};
  var tmpArray = th.id.split('_');

  cell.type = tmpArray[0];
  cell.tag = tmpArray[1];
  cell.fieldPosition = tmpArray[2];
  cell.subfieldIndex = tmpArray[3];

  var field_instance = gRecord[cell.tag][cell.fieldPosition];
  cell.tag_ind = cell.tag + field_instance[1] + field_instance[2];

  return cell;
}


/**
 * Highlights the content changed on BibEdit's edit table
 * @param  {Object} cell
 * @param  {String} value
 */
function highlight_change(cell, value) {
  var selector;
  switch (cell.type) {
    case 'subfieldTag':
      selector = '#subfieldTag_' + cell.tag + '_' + cell.fieldPosition +
        '_' + cell.subfieldIndex;
      break;
    case 'fieldTag':
      var newTag = value.substring(0,3);
      var newFieldPos;
      if (gRecord[newTag].length === 1) {
        newFieldPos = 0;
      }
      else {
        newFieldPos = gRecord[newTag].length - 1;
      }
      selector = '#fieldTag_' +  newTag +  '_' + newFieldPos;
      $(selector).focus();
      break;
    case 'content':
      selector = '#content_' + cell.tag + '_' + cell.fieldPosition +
        '_' + cell.subfieldIndex;
      break;
    default:
      return;
  }

  setTimeout('$("' + selector + '").effect("highlight", {color: gNEW_CONTENT_COLOR}, ' +
      'gNEW_CONTENT_COLOR_FADE_DURATION)', gNEW_CONTENT_HIGHLIGHT_DELAY);
}


/**
 * Function called when an editable cell (using jEditable plugin) changes value
 * @param  {String} value
 * @param  {Object} th
 * @return {String}
 */
function onEditableCellChange(value, th) {
    if (failInReadOnly()) {
        return;
    }

    value = sanitize_value(value);

    /* return an object with all the info we need */
    var cell = get_cell_info(th);

    switch (cell.type) {
    case 'subfieldTag':
        /* A subfield code has been changed */
        value = onSubfieldCodeChange(value, cell);
        break;
    case 'fieldTag':
        /* A field tag has been changed */
        value = onFieldTagChange(value, cell);
        break;
    case 'content':
        /* A subfield value has been changed */
        value = onContentChange(value, cell);
        break;
    default:
        // something unwanted happened, do nothing
        return value;
    }

    if ($(th).hasClass("affiliation-guess")) {
      $(th).removeClass("affiliation-guess");
    }

    return escapeHTML(value);
}


/******************** Functions specific to display modes ********************/
/*****************************************************************************/

function onfocusreference(check_box) {
  log_action("onfocusreference");

  var $reference_checkbox = $("#focuson_references");

  /* For cases when we call the function without click on the interface */
  if ( check_box === true ) {
    $reference_checkbox.prop("checked", !$reference_checkbox.prop("checked"));
  }

  if ( $reference_checkbox.prop("checked") === true ) {
    $.each(gDisplayReferenceTags, function() {
      $("tbody[id^='rowGroup_" + this + "']").show();
    });
  }
  else {
    $.each(gDisplayReferenceTags, function() {
      $("tbody[id^='rowGroup_" + this + "']").hide();
    });
  }
  reColorFields();
}


function onfocusauthor(check_box) {
  log_action("onfocusauthor");

  if (gRecordHideAuthors) {
    gRecordHideAuthors = false;
    $("#bibEditContentTable").empty();
    displayRecord();
  }

  var $author_checkbox = $("#focuson_authors");

  /* For cases when we call the function without click on the interface */
  if ( check_box === true ) {
    $author_checkbox.prop("checked", !$author_checkbox.prop("checked"));
  }

  if ($author_checkbox.prop("checked") === true) {
    $.each(gDisplayAuthorTags, function() {
      $("tbody[id^='rowGroup_" + this + "']").show();
    });
  }
  else {
    $.each(gDisplayAuthorTags, function() {
      $("tbody[id^='rowGroup_" + this + "']").hide();
    });
  }
  reColorFields();
}


function onfocusother(check_box) {
  log_action("onfocusother");

  var $others_checkbox = $("#focuson_others");

  /* For cases when we call the function without click on the interface */
  if ( check_box === true ) {
    $others_checkbox.prop("checked", !$others_checkbox.prop("checked"));
  }

  var tags = [];
  tags = tags.concat(gDisplayReferenceTags, gDisplayAuthorTags);

  var myselector = $();
  $.each(tags, function() {
    myselector = myselector.add("tbody[id^='rowGroup_" + this + "']");
  });

  if ($others_checkbox.prop("checked") === true) {
    $("tbody:[id^='rowGroup_']").not(myselector).show();
  }
  else {
    $("tbody:[id^='rowGroup_']").not(myselector).hide();
  }
  reColorFields();
}

function onfocuscurator(check_box) {
  log_action("onfocuscurator");

  var $curator_checkbox = $("#focuson_curator");

  if ( $curator_checkbox.length === 0 ) {
    return;
  }

  /* For cases when we call the function without click on the interface */
  if ( check_box === true ) {
    $curator_checkbox.prop("checked", !$curator_checkbox.prop("checked"));
  }

  $("#focuson_references").prop("checked", true);
  $("#focuson_authors").prop("checked", true);
  $("#focuson_others").prop("checked", true);
  onfocusreference();
  onfocusother();
  onfocusauthor();

  if ( $curator_checkbox.prop("checked") === true ) {
    $.each(gExcludeCuratorTags, function() {
      $("tbody[id^='rowGroup_" + this + "']").hide();
    });
  }
  reColorFields();
}


function displayAllTagsCheckboxes() {
  $("#focuson_references").prop("checked", true);
  $("#focuson_authors").prop("checked", true);
  $("#focuson_others").prop("checked", true);
}


function getUnmarkedTags() {
  return $("#focuson_list input:checkbox:not(:checked)");
}


function setUnmarkedTags(tags) {
  $.each(tags, function() {
    this.click();
  })
}


function bindFocusHandlers() {
  $("#focuson_references").on("click", onfocusreference);
  $("#focuson_authors").on("click", onfocusauthor);
  $("#focuson_others").on("click", onfocusother);
  $("#focuson_curator").on("click", onfocuscurator);
}


function displayOnlyAuthors() {
  $("#focuson_references").prop("checked", false);
  $("#focuson_authors").prop("checked", true);
  $("#focuson_others").prop("checked", false);
  $("#focuson_curator").prop("checked", false);
  onfocusreference();
  onfocusother();
  onfocusauthor();
}


function displayOnlyReferences() {
  $("#focuson_references").prop("checked", true);
  $("#focuson_authors").prop("checked", false);
  $("#focuson_others").prop("checked", false);
  $("#focuson_curator").prop("checked", false);
  onfocusreference();
  onfocusother();
  onfocusauthor();
}


function displayOnlyOthers() {
  $("#focuson_references").prop("checked", false);
  $("#focuson_authors").prop("checked", false);
  $("#focuson_others").prop("checked", true);
  $("#focuson_curator").prop("checked", false);
  onfocusreference();
  onfocusother();
  onfocusauthor();
}

function displayOnlyCurator() {
  $("#focuson_references").prop("checked", true);
  $("#focuson_authors").prop("checked", true);
  $("#focuson_others").prop("checked", true);
  $("#focuson_curator").prop("checked", true);
  onfocusreference();
  onfocusother();
  onfocusauthor();
  onfocuscurator();
}

function displayAll() {
  displayAllTagsCheckboxes();
  onfocusreference();
  onfocusother();
  onfocusauthor();
}

/*************** Functions related to affiliation guess ***************/

function onGuessAffiliations() {
  log_action("onGuessAffiliations");

  var reqData = {
              recID: gRecID,
              requestType: 'guessAffiliations'
              };

  save_changes().done(function() {
    createReq(reqData, function(json) {
      var subfields_to_add = json['subfieldsToAdd'];
      var new_affiliations = false;

      if ( subfields_to_add['100'][0] && subfields_to_add['100'][0].length > 0 ) {
        new_affiliations = true;
        for ( field_pos in subfields_to_add['100'] ) {
          for ( var subfield_index in subfields_to_add['100'][field_pos] ) {
            gRecord['100'][field_pos][0].push(subfields_to_add['100'][field_pos][subfield_index]);
          }
          redrawFieldPosition('100', field_pos);
          for (var i=0; i < subfields_to_add['100'][field_pos].length; i++ ) {
            var field_selector = "#content_" + "100_" +  String(field_pos) + "_" + String(gRecord['100'][field_pos][0].length - i - 1);
            $(field_selector).addClass('affiliation-guess');
          }
        }
      }
      if ( subfields_to_add['700'][0] && subfields_to_add['700'][0].length > 0 ) {
        new_affiliations = true;
        for ( field_pos in subfields_to_add['700'] ) {
          for ( var subfield_index in subfields_to_add['700'][field_pos] ) {
            gRecord['700'][field_pos][0].push(subfields_to_add['700'][field_pos][subfield_index]);
          }
          redrawFieldPosition('700', field_pos);
          for (var i=0; i < subfields_to_add['700'][field_pos].length; i++ ) {
            var field_selector = "#content_" + "700_" +  String(field_pos) + "_" + String(gRecord['700'][field_pos][0].length - i - 1);
            $(field_selector).addClass('affiliation-guess');
          }
        }
      }

      if ( new_affiliations ) {
        activateSubmitButton();
        reColorFields();
      }
    });
  });
}
