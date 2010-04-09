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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/* A Javascript module performing all the operations related to the
 * HoldingPen BibEdit integration
 * The functions include
 *
 * General event handlers
 *    onHoldingPenPanelRecordIdChanged
 *
 * Treatment of the left menu panel
 *    holdingPenPanelAddEntry
 *    holdingPenPanelSetChanges
 *    holdingPenPanelRemoveEntry
 *    holdingPenPanelRemoveChangeSet
 *    holdingPenPanelRemoveEntries
 *
 * The chqngeset preview window
 * 	  showHoldingPenChangesetPreview
 * 	  onHoldingPenPreviewDataRetreived
 *    onToggleDetailsVisibility
 *    enableChangesetControls
 *    disableChangesetControls
 *    visualizeRetrievedChangeset
 *
 * Treatment of the changes previewed in the editor
 * 	  onHoldingPenChangesetRetrieved
 *    holdingPenPanelApplyChangeSet
 *    visualizeRetrievedChangeset
 *    removeViewedChange
 *    addGeneralControls
 *    onRejectChangeClicked
 *    onAcceptAllChanges
 *    removeAllAppliedChanges
 *    onRejectAllChanges
 *
 * Preparing the AJAX requests and changing the interface
 *    prepareSubfieldRemovedRequest
 *    prepareFieldRemovedRequest
 *    prepareSubfieldAddedRequest
 *    prepareFieldChangedRequest
 *    prepareFieldAddedRequest
 *    prepareSubfieldChangedRequest
 *
 * Functions performing the entire process of applying a change
 *    applySubfieldChanged
 *    applySubfieldRemoved
 *    applyFieldRemoved
 *    applySubfieldAdded
 *    applyFieldChanged
 *    applyFieldAdded
 */

function onHoldingPenPanelRecordIdChanged(recordId){
  /** function that should be called when the edited record identifier changed
   * the functionality consists of reloading the entries using the Ajax call
   */
  holdingPenPanelRemoveEntries();
  createReq({recID: recordId, requestType: 'getHoldingPenUpdates'}, holdingPenPanelSetChanges)
}


/**          Holding Pen menu panel         */


function holdingPenPanelAddEntry(entry){
  /** A function adding a holding pen entry to the interface and connecting appropriate
   * events with it
   *
   * Parameter:
   *    entry - a holding Pen entry descriptor being a tuple
   *            (changeset_number, changeset_datetime)
   */
  changesetNumber = entry[0];
  changesetDatetime = entry[1];
  isChangesetProcessed = entry[2]; // if the entry has been already processed
  entry = createHoldingPenPanelEntry(changesetNumber, changesetDatetime);
  $(entry).appendTo("#bibeditHPChanges");
}

function holdingPenPanelSetChanges(data){
  /** Setting the Holding Pen panel content.
   * 	This function cqn be utilised as a Javascript callback
   *
   * 	Parameter:
   *  data - The dictionary containing a 'changes' key under which, a list
   *         of changes is stored
   */
  if (data.recID == gRecID || data.recID == gRecIDLoading) {
    holdingPenPanelRemoveEntries();

    for (var i = 0; i < data['changes'].length; i++) {
      holdingPenPanelAddEntry(data['changes'][i]);
    }
  }
}


function holdingPenPanelRemoveEntry(changesNum){
  /** Function removing an entry representing a Holding Pen changeset
   *  from the Holding Pen BibEdit menu panel
   *
   *  Parameters:
   *      changesNum - a Holding Pen changeset identifier
   */
  $('#bibeditHoldingPenPanelEntry_' + changesNum).remove();
}

function holdingPenPanelDisableChangeSet(changesNum){
  gDisabledHpEntries[changesNum] = true;
  disableProcessedChanges();

  // now removing the changeset from the database
  var data = {
      recID: gRecID,
      requestType: "desactivateHoldingPenChangeset",
      desactivatedChangeset : changesNum
  }
  createReq(data, function(json){updateStatus('report', gRESULT_CODES[json['resultCode']])}, false);
}

function holdingPenPanelRemoveChangeSet(changesNum){
  /** Function removing a partivular changeset from the panel in the menu
   *
   * Parameters:
   *    changesetNum: the internal Holding Pen changeset identifier
   */

  // removing the control
  holdingPenPanelRemoveEntry(changesNum)

  // now removing the changeset from the database
  var data = {
      recID: gRecID,
      requestType: "deleteHoldingPenChangeset",
      changesetNumber : changesNum
  }

  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']])});
}

function holdingPenPanelRemoveEntries(){
  /** Function that removes all the entries from the Holding Pen panel
   */
  $("#bibeditHPChanges").empty();
}

/*** Functions dealing with the changeset preview */

function showHoldingPenChangesetPreview(changesetNumber, record){
  /** Function rendering the changeset preview
   *
   * Parameters:
   *    changesetNumber - the internal Holding Pen identifier of the changeset
   *    record - the object representing the record after changes
   */
  newContent = createHoldingPenChangePreview(record);
  previewBoxId = "holdingPenPreview_" + changesetNumber;
  previewBoxSelector = "#" + previewBoxId;

  $(previewBoxSelector).html(newContent);
}

function onHoldingPenPreviewDataRetreived(json){
  /** An event-handler function utilised executed when the data of a
   *  particular changeset arrived, ready to be previewed
   *
   *  Parameters:
   *     json: a dictionary describing the retrieved changeset.
   *           Must contain the following keys:
   *              'record' : a new record value
   *              'changeset_number' : the number of the changeset
   *              		downloded
   */
  changesetNumber = json['changeset_number'];
  record = json['record'];

  showHoldingPenChangesetPreview(changesetNumber, record);
  gHoldingPenLoadedChanges[changesetNumber] = record;
}

function onToggleDetailsVisibility(changesetNumber){
  /** Changes the visibility of the change preview. Initialises
   * dowloading the changeset data if necessary
   *
   * Parameters:
   *    changesetNumber - the number of the HoldingPen changeset
   */
  hidingClass = 'bibeditHPHiddenElement';
  detailsSelector = "#holdingPenPreview_" + changesetNumber;
  togglingSelector = "#holdingPenToggleDetailsVisibility_" + changesetNumber;

  if ($(detailsSelector).hasClass(hidingClass)) {
    // showing the details -> the preview used to be closed

    if (gHoldingPenLoadedChanges[changesetNumber] == undefined) {
      // start prealoading the data that will be fileld into the
      // preview box
      createReq({
        changesetNumber: changesetNumber,
        requestType: 'getHoldingPenUpdateDetails'
      }, onHoldingPenPreviewDataRetreived)
    }
    else {
      // showing the preview based on the precached data
      showHoldingPenChangesetPreview(gHoldingPenLoadedChanges[changesetNumber]);
    }

    // Making the DOM layers visible

    $(detailsSelector).removeClass(hidingClass);
    $(togglingSelector).text('-');

  }
  else {
    // The changes preview was visible until now - time to hide it
    $(detailsSelector).addClass(hidingClass);
    $(togglingSelector).text('+');
  }
}

function enableChangesetControls(changesetNum){
  $("#bibeditHPRemoveChange" + changesetNum).removeClass('bibEditImgCtrlDisabled').addClass('bibEditImgCtrlEnabled').removeAttr("disabled");
  $("#bibeditHPApplyChange" + changesetNum).removeClass('bibEditImgCtrlDisabled').addClass('bibEditImgCtrlEnabled').removeAttr("disabled");
}

function disableChangesetControls(changesetNum){
  $("#bibeditHPRemoveChange" + changesetNum).removeClass('bibEditImgCtrlEnabled').addClass('bibEditImgCtrlDisabled').attr("disabled", "disabled");
  $("#bibeditHPApplyChange" + changesetNum).removeClass('bibEditImgCtrlEnabled').addClass('bibEditImgCtrlDisabled').attr("disabled", "disabled");
}


function markHpChangesetAsInactive(changesetId){
  $("#bibeditHoldingPenPanelEntry_" + changesetId).addClass("bibeditHPPanelEntryDisabled");
  disableChangesetControls(changesetId);
}

function disableProcessedChanges(){
  // disabling the changes that have
  for (changesetId in gDisabledHpEntries){
    markHpChangesetAsInactive(changesetId);
  }
}

function visualizeRetrievedChangeset(changesetNumber, newRecordData){
  /** Makes the retrieved changeset visible in the main BibEdit editor
   *
   * Parameters:
   * 	  changesetNumber: the internal Holding Pen number of the changeset
   *    newRecordData: the value of a record after changing
   */

  // first checking if there are already some changes loaded -> if so, wait
  canPass = true;
  for (ind in gHoldingPenChanges){
    if (gHoldingPenChanges[ind].change_type != "applied_change"){
      canPass = false;
    }
  }

  if (canPass) {
    // if we can pass, it means thqat all the changes have been already processed.
    // we remove the changes list for the performance reason
    gHoldingPenChanges = [];
    $("#holdingPenPreview_" + changesetNumber).remove();
    //	 we want to get rid of some changes that are obviously irrelevant
    //	    -> such as removal of the record number
      comp = filterChanges(compareRecords(gRecord, newRecordData));
      // now producing the controls allowing to apply the change
      for (change in comp) {
        changePos = gHoldingPenChanges.length;
        gHoldingPenChanges[changePos] = comp[change];

        addChangeControl(changePos);
      }
      addGeneralControls();
      holdingPenPanelDisableChangeSet(changesetNumber);
    // now updating the serverside list
    createReq({
      newChanges: gHoldingPenChanges,
      requestType: 'overrideChangesList',
      recID: gRecID},
      function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']]);
      });

  } else {
    alert("Please process the changes already visualised in the interface");
    // enabling the controls
    enableChangesetControls(changesetNumber);
  }
}

/**     Treatment of the changesets applied to the main editor */


function onHoldingPenChangesetRetrieved(json){
  /** An event-havdler executed when a changeset intended to be applied
   * is retrieved
   *
   * Parameters:
   *    json - The response code. A dictionary. it has to contain following
   *           keys:
   *               'record' - a new record object
   *               'changeset_number' - an internal HoldingPen identifier of
   *                                    the changeset
   */

  newRecordData = json['record'];
  changesNumber = json['changeset_number'];
  // processing added and modified fields
  visualizeRetrievedChangeset(changesNumber, newRecordData);
  gHoldingPenLoadedChanges[changesNumber] = newRecordData;
}

function holdingPenPanelApplyChangeSet(changesNum){
  /** Applies the changeset of given number to the record
   * 	   (initialises the retrieving if necessary)
   *
   * applying a changeset consists of adding the proposal
   * buttons in appropriate fields and removing the Holding Pen entry
   */
  if (failInReadOnly()){
    return;
  }
  disableChangesetControls(changesNum);
  if (gHoldingPenLoadedChanges[changesNum] == undefined){
    createReq({
      changesetNumber: changesNum,
      requestType: 'getHoldingPenUpdateDetails'},
      onHoldingPenChangesetRetrieved);
  }else
  {
    // we can apply the changes directly without wawiting for them to be retrieved
    visualizeRetrievedChangeset(changesNum, gHoldingPenLoadedChanges[changesNum]);
  }
}


/** Functions performing the client-side of applying a change and creating an appropriate AJAX request data
 *  The client side operations consist of modifying the client-side model
 *
 *  Each of these functions takes exactly one parameter being the client-side identifier of the change
 *  and in the same time, the index in global gHoldingPenChanges array
 */

function prepareSubfieldRemovedRequest(changeNo){
  fieldId = gHoldingPenChanges[changeNo]["tag"];
  fieldPos = gHoldingPenChanges[changeNo]["field_position"];
  sfPos = gHoldingPenChanges[changeNo]["subfield_position"];

  toDelete = {};
  toDelete[fieldId] = {};
  toDelete[fieldId][fieldPos] = [sfPos];

  gRecord[fieldId][fieldPos][0].splice(sfPos, 1);

  return {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    changeApplied: changeNo
  };
}

function prepareFieldRemovedRequest(changeNo){
  fieldId = gHoldingPenChanges[changeNo]["tag"];
  indicators = gHoldingPenChanges[changeNo]["indicators"];
  fieldPos = gHoldingPenChanges[changeNo]["field_position"];

  toDelete = {};
  toDelete[fieldId] = {};
  toDelete[fieldId][fieldPos] = [];

  gRecord[fieldId].splice(fieldPos, 1);

  return {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    changeApplied: changeNo
  };
}

function prepareSubfieldAddedRequest(changeNo){
  fieldId = gHoldingPenChanges[changeNo]["tag"];
  indicators = gHoldingPenChanges[changeNo]["indicators"];
  fieldPos = gHoldingPenChanges[changeNo]["field_position"];
  sfType = gHoldingPenChanges[changeNo]["subfield_code"];
  content = gHoldingPenChanges[changeNo]["subfield_content"];

  gRecord[fieldId][fieldPos][0].push([sfType, content]);

  return {
    recID: gRecID,
    requestType: 'addSubfields',
    tag: fieldId,
    fieldPosition: fieldPos,
    subfields: [[sfType, content]],
    changeApplied: changeNo

  };
}

function prepareFieldChangedRequest(changeNumber){
  change = gHoldingPenChanges[changeNumber];
  tag = change["tag"];
  indicators = change["indicators"];
  ind1 = (indicators[0] == '_') ? ' ' : indicators[0];
  ind2 = (indicators[1] == '_') ? ' ' : indicators[1];
  fieldPos = change["field_position"];
  subFields = change["field_content"];
  gRecord[tag][fieldPos][0] = subFields;
  return {
    recID: gRecID,
    requestType: "modifyField",
    controlfield : false,
    fieldPosition : fieldPos,
    ind1: ind1,
    ind2: ind2,
    tag: tag,
    subFields: subFields,
    changeApplied: changeNumber
  }
}

function prepareFieldAddedRequest(changeNo){
  var fieldId = gHoldingPenChanges[changeNo]["tag"];
  var indicators = gHoldingPenChanges[changeNo]["indicators"];
  if (gHoldingPenChanges[changeNo]["change_type"] == "subfield_changed"){
    /** preparing the request in case we want to add a new field instead of
        changing the content of existing one
    */
    var subFieldsData = [[gHoldingPenChanges[changeNo]["subfield_code"],
                      gHoldingPenChanges[changeNo]["subfield_content"]]]
  } else{
    // A regular case -> field added or field modified change
    var subFieldsData = gHoldingPenChanges[changeNo]["field_content"];
  }

  indic1 = (indicators[0] == '_') ? " " : indicators[0];
  indic2 = (indicators[1] == '_') ? " " : indicators[1];

  position = insertFieldToRecord(gRecord, fieldId, indic1, indic2, subFieldsData);

  return {
    recID: gRecID,
    requestType: "addField",
    controlfield : false,
    fieldPosition : position,
    tag: fieldId,
    ind1: indic1,
    ind2: indic2,
    subfields: subFieldsData,
    value: '',
    changeApplied: changeNo
  };
}

function prepareSubfieldChangedRequest(changeNo){
  /** a wrapper around getUpdateSubfieldValueRequestData, providing the values
   from the change*/
  tag = gHoldingPenChanges[changeNo].tag;
  fieldPosition = gHoldingPenChanges[changeNo].field_position;
  subfieldIndex = gHoldingPenChanges[changeNo].subfield_position;
  subfieldCode = gRecord[tag][fieldPosition][0][subfieldIndex][0];
  value = gHoldingPenChanges[changeNo].subfield_content;

  gRecord[tag][fieldPosition][0][subfieldIndex][1] = value; // changing the local copy

  return getUpdateSubfieldValueRequestData(tag, fieldPosition,
                                           subfieldIndex, subfieldCode, value, changeNo);
}

/*** A set of functions applying differend kinds of changes
 *   All the functions obtain the identifier of a change ( NOT from the HoldingPen but one generated
 *   on the client side, that is the index in gHoldingPenChanges global Javascript array )
 */

function applySubfieldChanged(changeNo){
  /** Function applying the change of changing the subfield content  */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    sfPos = gHoldingPenChanges[changeNo]["subfield_position"];
    content = gHoldingPenChanges[changeNo]["subfield_content"];
    gRecord[fieldId][fieldPos][0][sfPos][1] = content; // changing the local copy
    updateSubfieldValue(fieldId, fieldPos, sfPos, gRecord[fieldId][fieldPos][0][sfPos][0], content, changeNo);

    removeViewedChange(changeNo);
  }
}

function applySubfieldRemoved(changeNo){
  /** Function applying the change of removing the subfield */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    data = prepareSubfieldRemovedRequest(changeNo);
    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
    });

    removeViewedChange(changeNo);
  }
}

function applyFieldRemoved(changeNo){
  /** Function applying the change of removing the field */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    fieldId = gHoldingPenChanges[changeNo]["tag"];
    indicators = gHoldingPenChanges[changeNo]["indicators"];
    fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    data = prepareFieldRemovedRequest(changeNo);

    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
    });

    // now the position of the fields has changed. We have to fix all teh references inside the gHoldingPenChanges
      for (change in gHoldingPenChanges) {
        if ((gHoldingPenChanges[change]["tag"] == fieldId) &&
        (gHoldingPenChanges[change]["indicators"] == indicators)) {
          if (gHoldingPenChanges[change]["field_position"] > fieldPos) {
            gHoldingPenChanges[change]["field_position"] -= 1;
          }
          if (gHoldingPenChanges[change]["field_position"] == fieldPos) {
            // there are more changes associated with this field ! They are no more correct
            // and should be removed... it is also possible to consider transforming them into add field
            // change, but seems to be an unnecessary effort
            gHoldingPenChanges[change]["change_type"] = "applied_change";
          }
        }
      }

      removeViewedChange(changeNo); // includes redrawing the controls
    }
}

function applySubfieldAdded(changeNo){
  /** Function applying the change of adding the subfield */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    data = prepareSubfieldAddedRequest(changeNo);
    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']])
    });

    removeViewedChange(changeNo); // automatic redrawing !
  }
}

function applyFieldChanged(changeNumber){
  /** Function applying the change of changing the field content */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    data = prepareFieldChangedRequest(changeNumber);
    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']])
    });

    removeViewedChange(changeNumber); // redrawing included in this call
    }
}

function applyFieldAdded(changeNo){
  /** Function applying the change of adding the field */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    var data = prepareFieldAddedRequest(changeNo);

    createReq(data, function(json){
      updateStatus('report', gRESULT_CODES[json['resultCode']])
    });
    // now adding appropriate controls to the interface
    removeViewedChange(changeNo);
    //redrawFields(fieldId);
  }
}

/*** Manipulations on changes previewed in the editor */

function removeViewedChange(changeNo){
  /** Function removing the control of a given change
   *
   *  Parameters:
   *     changeNo - a client-side identifier of the change
   */

  tag = gHoldingPenChanges[changeNo]["tag"];
  // gHoldingPenChanges.splice(changeNo, 1); // <- we can not simply remove it from the
                                             //    gHoldingPenChanges array because all the indices
                                             //    would move and a lot of work would have to be done!

  // marking the change as already processed
  gHoldingPenChanges[changeNo]["change_type"] = "applied_change";
  redrawFields(tag, true); // redraw the controls - skipping the field added controls
  // in case of the add_field action, the controls have to be removed in a different manner -
  // they are not part of the main table
  $("#changeBox_" + changeNo).remove(); // if there are no such boxes, the left side will be empty !
  reColorFields();
}

function addGeneralControls(){
   /** If necessary, creates the panel containing the general controls that allow
    * to accept or reject all teh viewed changes
    */
  if ($("#bibeditHoldingPenGC").length == 0){
    panel = createGeneralControlsPanel();
    $("#bibEditContent").prepend(panel);
  }
}

function onRejectChangeClicked(changeNo){
  /** An event handler fired when user requests to reject the change that has been proposed
   * by the user interface*/
  removeViewedChange(changeNo);
  createReq({
    requestType : "removeChange",
    changeApplied : changeNo,
    recID : gRecID
  }, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']])
  });
}

function onAcceptAllChanges(){
  /** Applying all the changes visualised in the editor
   */

  // the changes have to be ordered by their type firstly, we treat the
  // modifications of the content and adding new fields ( they do not change the
  // numeration of other fields and so, do not require to renumerate existing changes

  // first we collect only the change numbers because
  // preparing the requests causes the modifications of the content

  changesAddModifyNumbers= [];
  changesRemoveFieldNumbers = [];
  changesRemoveSubfieldNumbers = [];

  for (changeNum in gHoldingPenChanges){
    changeType = gHoldingPenChanges[changeNum].change_type;
    if ( changeType == "field_added"){
      changesAddModifyNumbers.push(changeNum);
    }
    if ( changeType == "subfield_changed"){
      changesAddModifyNumbers.push(changeNum);
    }
    if ( changeType == "subfield_added"){
      changesAddModifyNumbers.push(changeNum);
    }
    if ( changeType == "field_changed"){
      changesAddModifyNumbers.push(changeNum);
    }
    // in case of removals we have to take care that each field/subfield
    // is removed exactly once - otherwise it will cause an error

    if ( changeType == "field_removed"){
      changesRemoveFieldNumbers.push(changeNum);
    }
    if ( changeType == "subfield_removed"){
      changesRemoveSubfieldNumbers.push(changeNum);
    }
  }

  changesRemoveFieldNumbers = [];
  changesRemoveSubfieldNumbers = [];

  // now sorting the removals in the removals in an non-invasive manner
  //   - the removals of the fields have to be performed starting from the end
  //     until the beginning. The same stands for the subfields

  changesRemoveSubfieldNumbersSorted = changesRemoveSubfieldNumbers.sort(
      function (a, b){
        val1 = gHoldingPenChanges[a].subfield_position;
        val2 = gHoldingPenChanges[b].subfield_position;
        if (val1 < val2) return 1;
        else{
          if (val1 == val2)
            return 0;
          else
            return -1;
        }
      }
      );

  changesRemoveFieldNumbersSorted = changesRemoveFieldNumbers.sort(
      function (a, b){
        val1 = gHoldingPenChanges[a].field_position;
        val2 = gHoldingPenChanges[b].field_position;
        if (val1 < val2) return 1;
        else{
          if (val1 == val2)
            return 0;
          else
            return -1;
        }
      }
      );


  // now generating the requests data
  changesAddModify = [];

  for (changePos in changesAddModifyNumbers)
  {
    changeNum = changesAddModifyNumbers[changePos];
    changeType = gHoldingPenChanges[changeNum].change_type;
    if ( changeType == "field_added"){
      changeData = prepareFieldAddedRequest(changeNum);
      changesAddModify.push(changeData);
    }
    if ( changeType == "subfield_changed"){
      changeData = prepareSubfieldChangedRequest(changeNum);
      changesAddModify.push(changeData);
    }

    if ( changeType == "subfield_added"){
      changeData = prepareSubfieldAddedRequest(changeNum);
      changesAddModify.push(changeData);
    }

    if ( changeType == "field_changed"){
      changeData = prepareFieldChangedRequest(changeNum);
      changesAddModify.push(changeData);
    }
  }

  // Preparing the bulk AJAX request data for the removals

  changesRemove = [];

  for (changePos in changesRemoveSubfieldNumbersSorted){
    changeNum = changesRemoveSubfieldNumbersSorted[changePos];
    changeData = prepareSubfieldRemovedRequest(changeNum);
    changesRemove.push(changeData);
  }

  for (changePos in changesRemoveFieldNumbersSorted){
    changeNum = changesRemoveFieldNumbersSorted[changePos];
    changeData = prepareFieldRemovedRequest(changeNum);
    changesRemove.push(changeData);
  }

  // now making the AJAX request comprising all the changes data at once

  var data = {
      recID: gRecID,
      requestType: "applyBulkUpdates",
      value: [changesAddModify, changesRemove]
  }

  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']])});

  removeAllAppliedChanges();
  reColorFields();
}

function removeAllAppliedChanges(){
  /**removing all the changes together with theirt controls...

   in order to avoid multiple
   redrawing of the same fields, the changes are groupped by the tag (because the tag is drawn at once)
   the requests for adding the changes are treated separately
   */

  changesByTag = {}

  for (changeId in gHoldingPenChanges){
    change = gHoldingPenChanges[changeId];
    if (change.change_type != "change_applied") {
      if (change.change_type == "field_added") {
        removeAddFieldControl(changeId);
      }

      if (changesByTag[change.tag] == undefined) {
        changesByTag[change.tag] = 1;
      }
    }
  }

  gHoldingPenChanges = [];
  // now making the request to the server -> removing the server-side list
  // redrawing every modified tag
  createReq({recID: gRecID, requestType: "overrideChangesList", newChanges: []}, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']])});

  for (modifiedTag in changesByTag){
    redrawFields(modifiedTag);
  }
}

function onRejectAllChanges(){
  /*Rejecting all the considered changes*/
  removeAllAppliedChanges();
  reColorFields();
}
