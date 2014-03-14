/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011 CERN.
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
 *    showHoldingPenChangesetPreview
 *    onHoldingPenPreviewDataRetreived
 *    onToggleDetailsVisibility
 *    enableChangesetControls
 *    disableChangesetControls
 *    visualizeRetrievedChangeset
 *
 * Treatment of the changes previewed in the editor
 *    onHoldingPenChangesetRetrieved
 *    holdingPenPanelApplyChangeSet
 *    visualizeRetrievedChangeset
 *    removeViewedChange
 *    addGeneralControls
 *    onRejectChangeClicked
 *    onAcceptAllChanges
 *    prepareRemoveAllAppliedChanges
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
  createReq({recID: recordId, requestType: 'getHoldingPenUpdates'}, holdingPenPanelSetChanges);
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
   *	This function can be utilised as a Javascript callback
   *
   *	Parameter:
   *  data - The dictionary containing a 'changes' key under which, a list
   *         of changes is stored
   */
  if (data.recID == gRecID || data.recID == gRecIDLoading) {
    holdingPenPanelRemoveEntries();
    for (var i = 0, n=data['changes'].length; i < n; i++) {
      holdingPenPanelAddEntry(data['changes'][i]);
    }
    adjustHPChangesetsActivity();
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


function holdingPenPanelRemoveChangeSet(changesNum){
  /** Function removing a partivular changeset from the panel in the menu
   *
   * Parameters:
   *    changesetNum: the internal Holding Pen changeset identifier
   */

  // removing the control
  holdingPenPanelRemoveEntry(changesNum);

  // now removing the changeset from the database
  // This is an operation that can not be undoed !
  // TODO: if there is a necessity, undoing should be implemented
  var undoHandler = 0;

  var data = {
    recID: gRecID,
    requestType: "deleteHoldingPenChangeset",
    changesetNumber : changesNum,
    undoRedo : undoHandler
  };

  createReq(data, function(json){
    updateStatus('report', gRESULT_CODES[json['resultCode']]);});
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
      // start prealoading the data that will be filled into the
      // preview box
      createReq({
        changesetNumber: changesetNumber,
        requestType: 'getHoldingPenUpdateDetails',
        recID: gRecID
      }, onHoldingPenPreviewDataRetreived);
    }
    else {
      // showing the preview based on the precached data
      showHoldingPenChangesetPreview(gHoldingPenLoadedChanges[changesetNumber]);
    }

    // Making the DOM layers visible

    $(detailsSelector).removeClass(hidingClass);
    $(togglingSelector + ' img').attr('src','/img/magnifying_minus.png');

  }
  else {
    // The changes preview was visible until now - time to hide it
    $(detailsSelector).addClass(hidingClass);
    $(togglingSelector + ' img').attr('src','/img/magnifying_plus.png');
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


function adjustHPChangesetsActivity(){
  $(".bibeditHPPanelEntry").removeClass("bibeditHPPanelEntryDisabled");
  $(".bibeditHPControl").removeClass('bibEditImgCtrlDisabled').addClass("bibEditImgCtrlEnabled").removeAttr("disabled");

  // disabling the changes that have
  for (changesetId in gDisabledHpEntries){
    if (gDisabledHpEntries[changesetId] === true){
      markHpChangesetAsInactive(changesetId);
    }
  }
}

function prepareUndoVisualizeChangeset(changesetNumber, changesBefore){
  /** Preparing the Ajax request data undoing the visualise data request
   */
  // this is handler for undoing the visualization of preloaded Holding Pen changes
  var tagsToRedraw = {};
  var addFieldChangesToRemove = {};
  var addFieldChangesToDraw = {};

  for (changeInd in gHoldingPenChanges){
    tagsToRedraw[gHoldingPenChanges[changeInd].tag] = true;
    if (gHoldingPenChanges[changeInd].change_type == "field_added"){
      addFieldChangesToRemove[changeInd] = true;
    }
  }

  gHoldingPenChanges = changesBefore;

  for (changeInd in gHoldingPenChanges){
    tagsToRedraw[gHoldingPenChanges[changeInd].tag] = true;
    if (gHoldingPenChanges[changeInd].change_type == "field_added"){
      // the changes that are not displayed at the moment but should be
      if (gHoldingPenChanges[changeInd].applied_change !== true){
        addFieldChangesToDraw[changeInd] = true;
      }
    }
  }

  gDisabledHpEntries[changesetNumber] = false;

  // now updating the interface
  for (tag in tagsToRedraw){
    redrawFields(tag, true);
  }
  for (changeNo in addFieldChangesToRemove){
    removeAddFieldControl(changeNo);
  }
  for (changeNo in addFieldChangesToDraw){
      addFieldAddedControl(changeNo);
  }

  // removing all the field_added changes
  adjustGeneralHPControlsVisibility();
  adjustHPChangesetsActivity();
  reColorFields();
  var ajaxData = {
    hpChanges: {
	toOverride: changesBefore,
        changesetsToActivate: [changesetNumber]
      },
    requestType: 'otherUpdateRequest',
    recID: gRecID,
    undoRedo: "undo"
  };
  return ajaxData;
}

function visualizeRetrievedChangeset(changesetNumber, newRecordData, isRedo){
  // first checking if there are already some changes loaded -> if so, wait
  var canPass = true;
  for (ind in gHoldingPenChanges){
    if (gHoldingPenChanges[ind].applied_change !== true){ // undefined or false
      canPass = false;
    }
  }

  if (canPass) {
    var oldChangesList = gHoldingPenChanges;
    // we want to get rid of some changes that are obviously invalid,
    // such as removal of the record number
    var newChangesList = filterChanges(compareRecords(gRecord, newRecordData));

    var undoRedo = 0;
    if (isRedo === true){
      // this operation can be performed only on redo or as a genuine operation !
      undoRedo = "redo";
    } else {
      undoRedo = prepareUndoHandlerVisualizeChangeset(changesetNumber,
        oldChangesList, newChangesList);
      addUndoOperation(undoRedo);
    }

    var ajaxData = prepareVisualizeChangeset(changesetNumber, newChangesList,
      undoRedo);

    createReq(ajaxData,
      function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']]);
      });
  } else {
    alert("Please process the changes already visualised in the interface");
    enableChangesetControls(changesetNumber);
  }
}

function prepareVisualizeChangeset(changesetNumber, newChangesList, undoHandler){
  /** Makes the retrieved changeset visible in the main BibEdit editor
   *
   * Parameters:
   *	changesetNumber: the internal Holding Pen number of the changeset
   *    newRecordData: the value of a record after changing
   *    undoHandler: the handler passed directly throught the AJAX call
   */


  gHoldingPenChanges = [];

  $("#holdingPenPreview_" + changesetNumber).remove();

  // add the added fiels div
  if ( $('#bibEditHoldingPenAddedFields').length < 1 ) {
      var addedFiedsDivHtml = "<div id=\"bibEditHoldingPenAddedFields\"><div id=\"bibEditHoldingPenAddedFieldsLabel\">" +
      "<strong>Added fields in Holding Pen</div></strong></div>";
      $("#bibEditContentTable").append(addedFiedsDivHtml);
  }

  var showAddedFields = false;
  // now producing the controls allowing to apply the change
  for (change in newChangesList) {
    changePos = gHoldingPenChanges.length;
    gHoldingPenChanges[changePos] = newChangesList[change];
    if ( newChangesList[change]['change_type'] == "field_added" ) {
      showAddedFields =true;
    }
    addChangeControl(changePos);
  }

  if ( showAddedFields == false ) {
    $('#bibEditHoldingPenAddedFields').remove();
  }

  gDisabledHpEntries[changesetNumber] = true;
  adjustHPChangesetsActivity();
  adjustGeneralHPControlsVisibility();
  return {
    hpChanges: {
      toOverride: gHoldingPenChanges,
      changesetsToDeactivate : [changesetNumber]
    },
    requestType: 'otherUpdateRequest',
    recID: gRecID,
    undoRedo: undoHandler
  };
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
   *      (initialises the retrieving if necessary)
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
        requestType: 'getHoldingPenUpdateDetails',
        recID: gRecID},
        onHoldingPenChangesetRetrieved);
  }else
  {
    // we can apply the changes directly without waiting for them to be retrieved
    visualizeRetrievedChangeset(changesNum, gHoldingPenLoadedChanges[changesNum]);
  }
}


/** Functions performing the client-side of applying a change and creating an appropriate AJAX request data
 *  The client side operations consist of modifying the client-side model
 *
 *  Each of these functions takes exactly one parameter being the client-side identifier of the change
 *  and in the same time, the index in global gHoldingPenChanges array
 */

function prepareHPFieldChangedUndoHandler(changeNo){
    var tag = gHoldingPenChanges[changeNo].tag;
  var fieldPos = gHoldingPenChanges[changeNo].field_position;

  var oldInd1 = gRecord[tag][fieldPos][1];
  var oldInd2 = gRecord[tag][fieldPos][2];
  var oldSubfields = gRecord[tag][fieldPos][0];
  var oldIsControlField = gRecord[tag][fieldPos][3] != "";
    var oldValue = gRecord[tag][fieldPos][3];

  var newInd1 = gHoldingPenChanges[changeNo].indicators[0];
  var newInd2 = gHoldingPenChanges[changeNo].indicators[1];
  var newSubfields = gHoldingPenChanges[changeNo].field_content;
  var newIsControlField = false;
  var newValue = "";

  var origHandler =  prepareUndoHandlerChangeField(tag, fieldPos,
                                                       oldInd1, oldInd2,
                                                       oldSubfields, oldIsControlField,
                                                       oldValue, newInd1,
                                                       newInd2, newSubfields,
                                                       newIsControlField, newValue);

  return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function prepareHPSubfieldRemovedUndoHandler(changeNo){
  var tag = gHoldingPenChanges[changeNo].tag;
  var fieldPos = gHoldingPenChanges[changeNo].field_position;
  var sfPos = gHoldingPenChanges[changeNo].subfield_position;

  var toDelete = {};
  var sfToDelete = {};

  sfToDelete[tag] = {};
  sfToDelete[tag][fieldPos] = {};
  sfToDelete[tag][fieldPos][sfPos] = gRecord[tag][fieldPos][0][sfPos];

  toDelete.fields = {};
  toDelete.subfields = sfToDelete;

  var origHandler = prepareUndoHandlerDeleteFields(toDelete);
  return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function prepareSubfieldRemovedRequest(changeNo){
  var fieldId = gHoldingPenChanges[changeNo].tag;
  var fieldPos = gHoldingPenChanges[changeNo].field_position;
  var sfPos = gHoldingPenChanges[changeNo].subfield_position;

  var toDelete = {};
  toDelete[fieldId] = {};
  toDelete[fieldId][fieldPos] = [sfPos];

  gRecord[fieldId][fieldPos][0].splice(sfPos, 1);
  redrawFields(fieldId, true);

  return {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    hpChanges: { toDisable : [changeNo] }
  };
}

function prepareHPFieldRemovedUndoHandler(changeNo){
  var tag = gHoldingPenChanges[changeNo].tag;
  var fieldPos = gHoldingPenChanges[changeNo].field_position;

  var toDelete = {};
  var fToDelete = {};
  fToDelete[tag] = {};
  fToDelete[tag][fieldPos] = gRecord[tag][fieldPos];

  toDelete.subfields = {};
  toDelete.fields = fToDelete;
  var origHandler = prepareUndoHandlerDeleteFields(toDelete);
  return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function prepareFieldRemovedRequest(changeNo){
  var fieldId = gHoldingPenChanges[changeNo]["tag"];
  var fieldPos = gHoldingPenChanges[changeNo]["field_position"];

  var toDelete = {};
  toDelete[fieldId] = {};
  toDelete[fieldId][fieldPos] = [];


  gRecord[fieldId].splice(fieldPos, 1);
  redrawFields(fieldId, true);

  return {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete,
    hpChanges: {toDisable : [changeNo]}
  };
}

function prepareHPSubfieldAddedUndoHandler(changeNo){
  var tag = gHoldingPenChanges[changeNo]["tag"];
  var fieldPos = gHoldingPenChanges[changeNo]["field_position"];
  var sfCode = gHoldingPenChanges[changeNo]["subfield_code"];
  var sfValue = gHoldingPenChanges[changeNo]["subfield_content"];
  var subfields =  [[sfCode, sfValue]];
  var origHandler = prepareUndoHandlerAddSubfields(tag, fieldPos, subfields);
  return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function prepareSubfieldAddedRequest(changeNo){
  var fieldId = gHoldingPenChanges[changeNo]["tag"];
  var indicators = gHoldingPenChanges[changeNo]["indicators"];
  var fieldPos = gHoldingPenChanges[changeNo]["field_position"];
  var sfType = gHoldingPenChanges[changeNo]["subfield_code"];
  var content = gHoldingPenChanges[changeNo]["subfield_content"];

  gRecord[fieldId][fieldPos][0].push([sfType, content]);

  return {
    recID: gRecID,
    requestType: 'addSubfields',
    tag: fieldId,
    fieldPosition: fieldPos,
    subfields: [[sfType, content]],
    hpChanges: {toDisable: [changeNo]}

  };
}

function prepareFieldChangedRequest(changeNumber, undoHandler){
  var change = gHoldingPenChanges[changeNumber];

  var tag = change.tag;
  var indicators = change.indicators;
  var ind1 = (indicators[0] == '_') ? ' ' : indicators[0];
  var ind2 = (indicators[1] == '_') ? ' ' : indicators[1];
  var fieldPos = change.field_position;
  var subFields = change.field_content;

  return performChangeField(tag, fieldPos, ind1, ind2, subFields, false, "", undoHandler);
}

function getFullFieldContentFromHPChange(changeNo){
  /** An auxiliary function allowing us to obrain a full record
      content based on the HP change entry.
      The record content might be retrieved from the following
      types of Holdin Pen changes:
        subfield_changed: a field containing all the new content
        field_changed:    a field containing all the new content
        field_added:      a field containing all the new content

      Arguemnts:
        changeNo: a number of the change which we are considering

      Result:
        An object containing following properties:
        tag :           a tag of the field
        ind1, ind2 :    indicators of the field
        isControlField: a boolean value indicating if the resulting
                        field is a Control Field
        value:          a value in case of dealing with a Control
                        Field
       an empty object is returned in case of passing unsupported
       type of Holding Pen change
   */

  var chT = gHoldingPenChanges[changeNo]["change_type"];
  if (chT != "subfield_changed" && chT != "field_added" &&
      chT != "field_changed"){
      return {};
  }

  var indicators = gHoldingPenChanges[changeNo]["indicators"];
  var result = {};

  result.tag = gHoldingPenChanges[changeNo].tag;
  result.ind1 = (indicators[0] == '_') ? " " : indicators[0];
  result.ind2 = (indicators[1] == '_') ? " " : indicators[1];

  if (chT == "field_added" || chT == "field_changed" || chT == "subfield_changed"){
    result.subfields = subfields = gHoldingPenChanges[changeNo].
      field_content;
  }
  result.isControlField = false;
  result.value = "";

  return result;
}


function prepareHPFieldAddedUndoHandler(changeNo, fieldPos){
  /** A function creating the Undo/Redo handler for applying a
      change consisting of adding a new field. This handler can be
      only created after the field is really added

      Arguments:
        changeNo: a number of the Holding Pen Change
        fieldPos: a position on which the field has been inserted.
   */
  var r = getFullFieldContentFromHPChange(changeNo);

  var origHandler = prepareUndoHandlerAddField(r.tag, r.ind1, r.ind2,
                                               fieldPos, r.subfields,
                                               r.isControlField, r.value);
  return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function prepareFieldAddedRequest(changeNo){
  /** A function preparing the request of adding a new field,
      based on the HoldingPen change. This function can be used
      with following change types:
        subfield_changed : in the case when we want to add new
                           field instead of getting modifying
                           the existing content
        field_changed :    In the case when we want to add a new
                           field instead of modifying the existing
                           structure
        field_added :      the most regular case of adding a new field

      Arguments:
        changeNo: a number of the change associated with the request that
                  is being created.
      Result:
        A complete AJAX data related to adding a field based on a
        Holding Pen change
   */

  var r = getFullFieldContentFromHPChange(changeNo);

  var position = insertFieldToRecord(gRecord, r.tag, r.ind1, r.ind2, r.subfields);

  return {
    recID: gRecID,
    requestType: "addField",
    controlfield : r.isControlField,
    fieldPosition : position,
    tag: r.tag,
    ind1: r.ind1,
    ind2: r.ind2,
    subfields: r.subfields,
    value: r.value,
    hpChanges: {toDisable: [changeNo]}
  };
}

function prepareSubfieldChangedRequest(changeNo){
  /** a wrapper around getUpdateSubfieldValueRequestData, providing the values
   from the change*/
  var tag = gHoldingPenChanges[changeNo].tag;
  var fieldPosition = gHoldingPenChanges[changeNo].field_position;
  var subfieldIndex = gHoldingPenChanges[changeNo].subfield_position;
  var subfieldCode = gRecord[tag][fieldPosition][0][subfieldIndex][0];
  var value = gHoldingPenChanges[changeNo].subfield_content;

  gRecord[tag][fieldPosition][0][subfieldIndex][1] = value;

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
    var tag = gHoldingPenChanges[changeNo].tag;
    var fieldPos = gHoldingPenChanges[changeNo].field_position;
    var sfPos = gHoldingPenChanges[changeNo].subfield_position;
    var content = gHoldingPenChanges[changeNo].subfield_content;
    var sfCode = gRecord[tag][fieldPos][0][sfPos][0];
    var oldContent = gRecord[tag][fieldPos][0][sfPos][1];
    gRecord[tag][fieldPos][0][sfPos][1] = content; // changing the local copy

    var modificationUndoHandler = prepareUndoHandlerChangeSubfield(tag, fieldPos,
      sfPos, oldContent, content, sfCode, sfCode, "change_content");
    var undoHandler = prepareUndoHandlerApplyHPChange(modificationUndoHandler, changeNo);

    addUndoOperation(undoHandler);

    updateSubfieldValue(tag, fieldPos, sfPos, gRecord[tag][fieldPos][0][sfPos][0],
      content, changeNo, undoHandler);

    removeViewedChange(changeNo);
  }
}

function applySubfieldRemoved(changeNo){
  /** Function applying the change of removing the subfield */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    var undoHandler = prepareHPSubfieldRemovedUndoHandler(changeNo);
    var data = prepareSubfieldRemovedRequest(changeNo);
    data.undoRedo = undoHandler;
    addUndoOperation(data.undoRedo);
    removeViewedChange(changeNo);

    queue_request(data);
  }
}

function applyFieldRemoved(changeNo){
  /** Function applying the change of removing the field */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    var fieldId = gHoldingPenChanges[changeNo]["tag"];
    var indicators = gHoldingPenChanges[changeNo]["indicators"];
    var fieldPos = gHoldingPenChanges[changeNo]["field_position"];
    var undoHandler = prepareHPFieldRemovedUndoHandler(changeNo);
    var data = prepareFieldRemovedRequest(changeNo);
    data.undoRedo = undoHandler;
    addUndoOperation(undoHandler);

    queue_request(data);

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
            gHoldingPenChanges[change].applied_change = true;
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
    var undoHandler = prepareHPSubfieldAddedUndoHandler(changeNo);
    var data = prepareSubfieldAddedRequest(changeNo);
    data.undoRedo = undoHandler;
    addUndoOperation(undoHandler);
    queue_request(data);

    removeViewedChange(changeNo); // automatic redrawing !
  }
}

function applyFieldChanged(changeNumber){
  /** Function applying the change of changing the field content */
  if (failInReadOnly()){
    return;
  }
  if (gCurrentStatus == "ready") {
    var undoHandler =  prepareHPFieldChangedUndoHandler(changeNumber);
    addUndoOperation(undoHandler);
    var data = prepareFieldChangedRequest(changeNumber, undoHandler);

    queue_request(data);

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
    var undoHandler = prepareHPFieldAddedUndoHandler(changeNo, data.fieldPosition);
    addUndoOperation(undoHandler);
    data.undoRedo = undoHandler;

    queue_request(data);
    // now adding appropriate controls to the interface
    removeViewedChange(changeNo);
    redrawFields(fieldId, true);
    reColorFields();

    // if there is a volatile field with same tag and indicators with the field added should be deleted(replaced)
    // TODO check for indicators
    var isVolatile = true;
    for (var fPos in gRecord[data.tag]) {
      for (var sfPos in gRecord[data.tag][fPos][0]) {
        if (gRecord[data.tag][fPos][0][sfPos][1].substring(0,9) != "VOLATILE:"){
          isVolatile = false;
          break;
        }
      }
      if (isVolatile) {
        var fieldToDelete = {};
        fieldToDelete[data.tag] = {};
        fieldToDelete[data.tag][fPos] = gRecord[data.tag][fPos];
        var toDelete = {};
        toDelete.fields = fieldToDelete;
        toDelete.subfields = {};
        var urHandler = prepareUndoHandlerDeleteFields(toDelete);
        addUndoOperation(urHandler);
        var ajaxData = deleteFields(toDelete, urHandler);
        queue_request(ajaxData);
      }
    }

  }
}

/*** Manipulations on changes previewed in the editor */

function updateInterfaceAfterChangeModification(changeNo){
  tag = gHoldingPenChanges[changeNo]["tag"];
  redrawFields(tag, true); // redraw the controls - skipping the field added controls

  reColorFields();
  // in case of add_field change being reactivated/activated, we have to display the interface
  if (gHoldingPenChanges[changeNo].change_type == "field_added"){
    if (gHoldingPenChanges[changeNo].applied_change == undefined ||
        gHoldingPenChanges[changeNo].applied_change !== true){
      addFieldAddedControl(changeNo);
    } else {
      // in case of the add_field action, the controls have to be removed in a different manner -
      // they are not part of the main table
      removeAddFieldControl(changeNo);
    }
  }
  adjustGeneralHPControlsVisibility();
}

function revertViewedChange(changeNo){
  /** Reverts a Holding Pen change that has been marked as removed before
      Parameters:
         changeNo - The change index in local changes array
         changeType - type of a current change (to override)
   */
  gHoldingPenChanges[changeNo].applied_change = false;
  updateInterfaceAfterChangeModification(changeNo);
  adjustGeneralHPControlsVisibility();
}


function removeViewedChange(changeNo){
  /** Function removing the control of a given change
   *
   *  Parameters:
   *     changeNo - a client-side identifier of the change
   */

  gHoldingPenChanges[changeNo].applied_change = true;
  updateInterfaceAfterChangeModification(changeNo);
}

function addGeneralControls(){
   /** If necessary, creates the panel containing the general controls that allow
    * to accept or reject all teh viewed changes
    */
  if ($("#bibeditHoldingPenGC").length == 0 || $("#acceptReferences").length == 0){
    $("#bibeditHoldingPenGC").remove();
    panel = createGeneralControlsPanel();
    $("#bibEditContentTable").before(panel);
  }
}


function adjustGeneralHPControlsVisibility(){
  /** Function adjusting the visibility of the general Holding Pen changes bar.
      This bar is responsible of applying or rejecting all the visualized
      changes at once */
  var shouldDisplay = false;
  var shouldDisplayRefs = false;
  for (changeInd in gHoldingPenChanges){
    var changeTag = gHoldingPenChanges[changeInd].tag;
    var changeIndicators = gHoldingPenChanges[changeInd].indicators;
    var changeType = gHoldingPenChanges[changeInd].change_type;

    if (gHoldingPenChanges[changeInd].applied_change !== true &&
        changeType !== "subfield_same"){
      shouldDisplay = true;
    }
    if ( (changeType == "field_added" || changeType == "subfield_changed" ||
        changeType == "subfield_added" || changeType == "field_changed" ) &&
        gHoldingPenChanges[changeInd].applied_change !== true && changeTag == "999" &&
              changeIndicators == "C5" ){
      shouldDisplayRefs = true;
    }
  }
  if (shouldDisplay){
    addGeneralControls();
    if (!shouldDisplayRefs){
        $("#acceptReferences").remove();
    }
  } else {
    $("#bibeditHoldingPenGC").remove();
  }
}

function adjustReferenceHPControlsVisibility(){
  /** Function adjusting the visibility of the Holding Pen apply all references button.
      This bar is responsible of applying or rejecting all the visualized reference
      changes at once */
  var shouldDisplay = false;
  for (changeInd in gHoldingPenChanges){
    var changeTag = gHoldingPenChanges[changeInd].tag;
    var changeIndicators = gHoldingPenChanges[changeInd].indicators;
    var changeType = gHoldingPenChanges[changeInd].change_type;
    if ( (changeType == "field_added" || changeType == "subfield_changed" ||
        changeType == "subfield_added" || changeType == "field_changed" ) &&
        gHoldingPenChanges[changeInd].applied_change !== true && changeTag == "999" &&
              changeIndicators == "C5" ){
      shouldDisplay = true;
    }
  }
  if (shouldDisplay){
    addGeneralControls();
  } else {
    $("#acceptReferences").remove();
  }
}

function refreshChangesControls(){
  /** Redrawing all the changes controls
   */
  removeAllChangeControls();

  var tagsToRedraw = {};
  for (changeInd in gHoldingPenChanges){
    if (gHoldingPenChanges[changeInd].applied_change !== true){
      addChangeControl(changeInd, true);
      tagsToRedraw[gHoldingPenChanges[changeInd].tag] = true;
    }
  }

  for (tag in tagsToRedraw){
    redrawFields(tag, true);
  }

  reColorFields();
  adjustHPChangesetsActivity();
  adjustGeneralHPControlsVisibility();
}

function prepareHPRejectChangeUndoHandler(changeNo){
  var origHandler = prepareUndoHandlerEmpty();
    return prepareUndoHandlerApplyHPChange(origHandler, changeNo);
}

function onRejectChangeClicked(changeNo){
  /** An event handler fired when user requests to reject the change that has been proposed
   * by the user interface*/
  var undoHandler = prepareHPRejectChangeUndoHandler(changeNo);
  addUndoOperation(undoHandler);
  removeViewedChange(changeNo);
  var data = {
    requestType : "otherUpdateRequest",
    hpChanges : { toDisable: [changeNo]},
    recID : gRecID,
    undoRedo: undoHandler
  };

  queue_request(data);
}


function aggregateHoldingPenChanges(){
  /** Fuction aggregating the Holding Pen changes in different catheegories.
      Returns an object with following fuields:
        changesAddModify : a list of numbers of changes of modification or adding fields
	changesRemoveField : a list of numbers of changes of field removal
	changesRemoveSubfield : a list of numbers of changes of subfield removal
   */
  var result = {};
  result.changesAddModify= [];
  result.changesRemoveField = [];
  result.changesRemoveSubfield = [];

  for (changeNum in gHoldingPenChanges){
    changeNumInt = parseInt(changeNum);
    changeType = gHoldingPenChanges[changeNum].change_type;
    if (gHoldingPenChanges[changeNum].applied_change == undefined ||
        gHoldingPenChanges[changeNum].applied_change !== true) {
        if ( changeType == "field_added" || changeType == "subfield_changed" ||
          changeType == "subfield_added" || changeType == "field_changed"){
          result.changesAddModify.push(changeNumInt);
        }
        if ( changeType == "field_removed"){
          result.changesRemoveField.push(changeNumInt);
        }
        if ( changeType == "subfield_removed"){
          result.changesRemoveSubfield.push(changeNumInt);
        }
    }
  }

  return result;
}

function aggregateHoldingPenReferenceChanges(){
  /** Fuction aggregating the Holding Pen Reference changes in different categories.
      Returns an object with following fields:
        changesAddModify : a list of numbers of changes of modification or adding fields
   */
  var result = {};
  result.changesAddModify= [];

  for (changeNum in gHoldingPenChanges){
    changeNumInt = parseInt(changeNum);
    changeType = gHoldingPenChanges[changeNum].change_type;
    changeTag = gHoldingPenChanges[changeNum].tag;
    changeIndicators = gHoldingPenChanges[changeNum].indicators;
    if (gHoldingPenChanges[changeNum].applied_change == undefined ||
        gHoldingPenChanges[changeNum].applied_change !== true) {
        if ( (changeType == "field_added" || changeType == "subfield_changed" ||
              changeType == "subfield_added" || changeType == "field_changed") && changeTag == "999" &&
              changeIndicators == "C5" ){
                  result.changesAddModify.push(changeNumInt);
        }
    }
  }

  return result;
}

function acceptAddModifyChanges(changeNumbers){
  /** A helper function. Applies a list of add/modify Holding Pen changes
      Returns an object with the following subfields
        ajaxData : a list of Ajax requests data
        undoHandlers : a list of undo handlers
        tagsToRedraw : a dictionary of tags affected by the changes and
                    needing to be redrawn. Every entry is of the form
                    "tag" : true
   */

  var result = {};
  result.ajaxData = [];
  result.undoHandlers = [];
  result.tagsToRedraw = {};

  for (changePos in changeNumbers)
  {
    var changeNum = changeNumbers[changePos];
    var changeType = gHoldingPenChanges[changeNum].change_type;
    result.tagsToRedraw[gHoldingPenChanges[changeNum].tag] = true;
    if ( changeType == "field_added"){
      var changeData = prepareFieldAddedRequest(changeNum);
      var undoHandler = prepareHPFieldAddedUndoHandler(changeNum, changeData.fieldPosition);
      result.ajaxData.push(changeData);
      result.undoHandlers.push(undoHandler);
    }

    if (changeType == "subfield_changed"){
      var tag = gHoldingPenChanges[changeNum].tag;
      var fieldPos = gHoldingPenChanges[changeNum].field_position;
      var sfPos = gHoldingPenChanges[changeNum].subfield_position;
      var content = gHoldingPenChanges[changeNum].subfield_content;
      var sfCode = gRecord[tag][fieldPos][0][sfPos][0];
      var oldContent = gRecord[tag][fieldPos][0][sfPos][1];

      var modificationUndoHandler = prepareUndoHandlerChangeSubfield(tag,
        fieldPos, sfPos, oldContent, content, sfCode, sfCode, "change_content");
      var undoHandler = prepareUndoHandlerApplyHPChange(modificationUndoHandler,
							changeNum);

      var changeData = prepareSubfieldChangedRequest(changeNum);
      result.ajaxData.push(changeData);
      result.undoHandlers.push(undoHandler);
    }

    if ( changeType == "subfield_added"){
      var undoHandler = prepareHPSubfieldAddedUndoHandler(changeNum);
      var changeData = prepareSubfieldAddedRequest(changeNum);
      result.undoHandlers.push(undoHandler);
      result.ajaxData.push(changeData);
    }

    if ( changeType == "field_changed"){
      var undoHandler = prepareHPFieldChangedUndoHandler(changeNum);
      var changeData = prepareFieldChangedRequest(changeNum, 0);
      result.undoHandlers.push(undoHandler);
      result.ajaxData.push(changeData);
    }
  }

  return result;
}

function acceptRemoveFieldChanges(changeNumbers){
  /** A function applying all the field removal changes.
      Returns an object having the following subfields:
      ajaxData: a list of ajax objects
      undoHandlers: a list of undo handlers associated with the removals
      tagsToRedraw: a dictionary of tags affected by the changes and
                    needing to be redrawn. Every entry is of the form
                    "tag" : true
   */
  var result = {};
  result.ajaxData = [];
  result.undoHandlers = [];
  result.tagsToRedraw = {};

  /** First we have to sort the removals in the order of descending indices
      in order to make subsequent removals harmless to each other */

  var changesRemoveFieldNumbersSorted = changeNumbers.sort(
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
      });

  /** Now we can proceed with applying the changes in a given order */

  for (changePos in changesRemoveFieldNumbersSorted){
    var changeNum = changesRemoveFieldNumbersSorted[changePos];
    var undoHandler = prepareHPFieldRemovedUndoHandler(changeNum);
    var changeData = prepareFieldRemovedRequest(changeNum);
    result.tagsToRedraw[gHoldingPenChanges[changeNum].tag] = true;
    result.undoHandlers.push(undoHandler);
    result.ajaxData.push(changeData);
  }

  return result;
}

function acceptRemoveSubfieldChanges(changeNumbers){
  /** A function applying all the subfield removal changes.
      Returns an object having the following subfields:
      ajaxData: a list of ajax objects
      undoHandlers: a list of undo handlers associated with the removals
      tagsToRedraw: a dictionary of tags affected by the changes and
                    needing to be redrawn. Every entry is of the form
                    "tag" : true
   */
  var result = {};
  result.undoHandlers = [];
  result.ajaxData = [];
  result.tagsToRedraw = {};

  /** First we sort all the changes by the decreasing subfield index in order
      to make the subsequent changes harmless to each other. Subfield positions
      associated with the changes not being applied yet, should be always valid,
      which means that every time we have to remove a subfield with the highest
      index */
  var changesRemoveSubfieldNumbersSorted = changeNumbers.sort(
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
      });

  /** Now we can proceed with the removals in the appropriate order*/
  for (changePos in changesRemoveSubfieldNumbersSorted){
    var changeNum = changesRemoveSubfieldNumbersSorted[changePos];
    var undoHandler = prepareHPSubfieldRemovedUndoHandler(changeNum);
    var changeData = prepareSubfieldRemovedRequest(changeNum);
    undoHandlers.push(undoHandler);
    changesRemove.push(changeData);
    result.tagsToRedraw[gHoldingPenChanges[changeNum].tag] = true;
  }

  return result;
}

function onAcceptAllChanges(){
  /** Applying all the changes visualised in the editor.
   */

  save_changes().done(function() {

      /** Changes have to be ordered by their type. First we process the
          modifications of the content and adding new fields and subfields.
          Such changes do not modify the numeration of other fields/subfields
          and so, the indices of fields/subfields stored in other changes
          remain valid */

      var chNumbers = aggregateHoldingPenChanges();

      /** First we add the addField requests, as they do not change the numbers
          of existing fields and subields. Subsequents field/subfield removals
          will be possible. An opposite order (first removals and then adding,
          would break the record structure */

      var resAddUpdate = acceptAddModifyChanges(chNumbers.changesAddModify);

      /** Next we can proceed with the subfields removal. Application of such
          changes implies modification of the subfield indices. Field positions
          remain untouched  */
      var resRemoveSubfields = acceptRemoveSubfieldChanges(
            chNumbers.changesRemoveSubfield);

      /** Finally, we can proceed with removal of the fields. Doing so, changes
          the field numbers */
      var resRemoveFields = acceptRemoveFieldChanges(
             chNumbers.changesRemoveField);

      /** Now we remove all the changes visulaized in the interface */
      var removeAllChangesUndoHandler = prepareUndoHandlerRemoveAllHPChanges(
                                      gHoldingPenChanges);
      var removeAllChangesAjaxData = prepareRemoveAllAppliedChanges();

      /** updating the user interface after all the changes being finished in the
          cliens side model */
      var collectiveTagsToRedraw = {};
      for (tag in resAddUpdate.tagsToRedraw){
        collectiveTagsToRedraw[tag] = true;
      }
      for (tag in resRemoveFields.tagsToRedraw){
        collectiveTagsToRedraw[tag] = true;
      }
      for (tag in resRemoveSubfields.tagsToRedraw){
        collectiveTagsToRedraw[tag] = true;
      }
      for (tag in collectiveTagsToRedraw){
        redrawFields(tag);
      }

      adjustGeneralHPControlsVisibility();
      reColorFields();

      /** At this point, all the changes to the browser interface are finished.
          The only remaining activity is combining the AJAX request into one big,
          preparing the bulk undo/redo handler and passing the request to the
          server side of BibEdit  */

      var collectiveAjaxData = resAddUpdate.ajaxData.concat(
        resRemoveSubfields.ajaxData.concat(
        resRemoveFields.ajaxData.concat(
        [removeAllChangesAjaxData])));

      var collectiveUndoHandlers = resAddUpdate.undoHandlers.concat(
        resRemoveSubfields.undoHandlers.concat(
        resRemoveFields.undoHandlers.concat(
          [removeAllChangesUndoHandler])));
      collectiveUndoHandlers.reverse();

      var finalUndoHandler = prepareUndoHandlerBulkOperation(collectiveUndoHandlers,
        "apply all changes");
      addUndoOperation(finalUndoHandler);

      var optArgs = {
          undoRedo: finalUndoHandler
      };

      createBulkReq(collectiveAjaxData, function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']])
      }, optArgs);
  });
}

function onAcceptAllReferences(){
  /** Applying all the changes visualised in the editor.
   */

  save_changes().done(function() {
      /** Changes have to be ordered by their type. First we process the
          modifications of the content and adding new fields and subfields.
          Such changes do not modify the numeration of other fields/subfields
          and so, the indices of fields/subfields stored in other changes
          remain valid */

      var chNumbers = aggregateHoldingPenReferenceChanges();

      /** First we add the addField requests, as they do not change the numbers
          of existing fields and subields. Subsequents field/subfield removals
          will be possible. An opposite order (first removals and then adding,
          would break the record structure */

      var resAddUpdate = acceptAddModifyChanges(chNumbers.changesAddModify);

      /** Now we remove all the changes visulaized in the interface */
      var removeAllChangesUndoHandler = prepareUndoHandlerBulkOperation(resAddUpdate.undoHandlers,
                                         'apply all references');
      for (var i in chNumbers.changesAddModify) {
        removeViewedChange(chNumbers.changesAddModify[i]);
      }
      /** updating the user interface after all the changes being finished in the
          cliens side model */
      var collectiveTagsToRedraw = {};
      for (tag in resAddUpdate.tagsToRedraw){
        collectiveTagsToRedraw[tag] = true;
      }
      for (tag in collectiveTagsToRedraw){
        redrawFields(tag, true);
      }

      adjustGeneralHPControlsVisibility();
      // adjustReferenceHPControlsVisibility();
      reColorFields();

      /** At this point, all the changes to the browser interface are finished.
          The only remaining activity is combining the AJAX request into one big,
          preparing the bulk undo/redo handler and passing the request to the
          server side of BibEdit  */

      var collectiveAjaxData = resAddUpdate.ajaxData;

      removeAllChangesUndoHandler.handlers.reverse();
      var collectiveUndoHandlers = [removeAllChangesUndoHandler];
      // var collectiveUndoHandlers = resAddUpdate.undoHandlers.concat([removeAllChangesUndoHandler]);
      collectiveUndoHandlers.reverse();

      var finalUndoHandler = prepareUndoHandlerBulkOperation(collectiveUndoHandlers,
                   "apply all reference's changes");
      addUndoOperation(finalUndoHandler);

      var optArgs = {
          undoRedo: finalUndoHandler
      };

      createBulkReq(collectiveAjaxData, function(json){
        updateStatus('report', gRESULT_CODES[json['resultCode']])
      }, optArgs);
  });
}


function prepareRemoveAllAppliedChanges(){
  /**Removing all the changes together with their user interface controls.
     in order to avoid multiple redrawing of the same fields, the changes are
     groupped by the tag (because the tag is drawn at once)
     the requests for adding the changes are treated separately */

  gHoldingPenChanges = [];
  removeAllChangeControls();
  return {recID: gRecID, requestType: "otherUpdateRequest",
          hpChanges: {toOverride : []}};
}


function onRejectAllChanges(){
  /** Rejecting all the considered changes*/
  save_changes().done(function() {
      var undoHandler = prepareUndoHandlerRemoveAllHPChanges(gHoldingPenChanges);
      addUndoOperation(undoHandler);
      var ajaxData = prepareRemoveAllAppliedChanges();
      ajaxData.undoRedo = undoHandler;
      queue_request(ajaxData);
      adjustGeneralHPControlsVisibility();
      reColorFields();
  });
}
