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

/*
 * This is the BibEdit Javascript for all functionality directly related to the
 * left hand side menu, including event handlers for the controls.
 */

function initMenu(){
  /*
   * Initialize menu.
   */
  // Make sure the menu is in it's initial state.
  deactivateRecordMenu();
  $('#txtSearchPattern').val('');
  // Submit get request on enter.
  $('#txtSearchPattern, #sctSearchType').bind('keypress', function(event){
    if (event.keyCode == 13){
      $('#btnSearch').click();
      event.preventDefault();
    }
  });
  // Set the status.
  $('#cellIndicator').html(img('/img/circle_green'));
  $('#cellStatus').text('Ready');
  // Bind button event handlers.
  $('#lnkNewRecord').bind('click', onNewRecordClick);
  $('#btnSearch').bind('click', onSearchClick);
  $('#btnSubmit').bind('click', onSubmitClick);
  $('#btnCancel').bind('click', onCancelClick);
  $('#btnCloneRecord').bind('click', onCloneRecordClick);
  $('#btnDeleteRecord').bind('click', onDeleteRecordClick);
  $('#btnMARCTags').bind('click', onMARCTagsClick);
  $('#btnHumanTags').bind('click', onHumanTagsClick);
  $('#btnAddField').bind('click', onAddFieldClick);
  $('#btnDeleteSelected').bind('click', onDeleteClick);
  $('#bibEditMenu .bibEditImgExpandMenuSection').bind('click',
    expandMenuSection);
  // Focus on record selection box.
  $('#txtSearchPattern').focus();
  // Initialize menu positioning (poll for scrolling).
  setInterval(positionMenu, gCHECK_SCROLL_INTERVAL);
}

function positionMenu(){
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
// Last Y-scroll value
positionMenu.yScroll = 0;

function expandMenuSection(){
  /*
   * Expand a menu section.
   */
  var currentMenuHeight = $('#bibEditMenu').height();
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').show();

  // Expand content spaceholder accordingly.
  var deltaMenuHeight = $('#bibEditMenu').height() - currentMenuHeight;
  var currentSpacerHeight = parseInt($('#bibEditContent').css(
			      'min-height').slice(0, -2));
  $('#bibEditContent').css('min-height',
    (currentSpacerHeight + deltaMenuHeight) + 'px');

  $(this).replaceWith(img('/img/bullet_toggle_minus.png', '',
			  'bibEditImgCompressMenuSection'));
  parent.find('.bibEditImgCompressMenuSection').bind('click',
						     compressMenuSection);
}

function compressMenuSection(){
  /*
   * Compress a menu section.
   */
  var currentMenuHeight = $('#bibEditMenu').height();
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').hide();

  // Reduce content spaceholder accordingly.
  var deltaMenuHeight = $('#bibEditMenu').height() - currentMenuHeight;
  var currentSpacerHeight = parseInt($('#bibEditContent').css(
			      'min-height').slice(0, -2));
  $('#bibEditContent').css('min-height',
    (currentSpacerHeight + deltaMenuHeight) + 'px');

  $(this).replaceWith(img('/img/bullet_toggle_plus.png', '',
			  'bibEditImgExpandMenuSection'));
  parent.find('.bibEditImgExpandMenuSection').bind('click', expandMenuSection);
}

function activateRecordMenu(){
  /*
   * Activate menu record controls.
   */
  $('#btnCancel').removeAttr('disabled');
  $('#btnDeleteRecord').removeAttr('disabled');
  $('#btnAddField').removeAttr('disabled');
  $('#btnCloneRecord').removeAttr('disabled');
  $('#btnDeleteSelected').removeAttr('disabled');
}

function deactivateRecordMenu(){
  /*
   * Deactivate menu record controls.
   */
  $('#btnSubmit').attr('disabled', 'disabled');
  $('#btnSubmit').css('background-color', '');
  $('#btnCancel').attr('disabled', 'disabled');
  $('#btnDeleteRecord').attr('disabled', 'disabled');
  $('#btnMARCTags').attr('disabled', 'disabled');
  $('#btnHumanTags').attr('disabled', 'disabled');
  $('#btnAddField').attr('disabled', 'disabled');
  $('#btnCloneRecord').attr('disabled', 'disabled');
  $('#btnDeleteSelected').attr('disabled', 'disabled');
}

function disableRecordBrowser(){
  /*
   * Disable and hide the menu record browser.
   */
  if ($('#rowRecordBrowser').css('display') != 'none'){
    $('#btnNext').unbind('click').attr('disabled', 'disabled');
    $('#btnPrev').unbind('click').attr('disabled', 'disabled');
    $('#rowRecordBrowser').hide();
  }
}

function updateStatus(statusType, reporttext){
  /*
   * Update status (in the bottom of the menu).
   */
  var image, text;
  switch (statusType){
    case 'ready':
      image = img('/img/circle_green.png');
      text = 'Ready';
      break;
    case 'updating':
      image = img('/img/indicator.gif');
      text = 'Updating...';
      break;
    // Generic report. Resets to 'Ready' after timeout.
    case 'report':
      image = img('/img/circle_green.png');
      text = reporttext;
      clearTimeout(updateStatus.statusResetTimerID);
      updateStatus.statusResetTimerID = setTimeout('updateStatus("ready")',
				  gSTATUS_INFO_TIME);
      break;
    case 'error':
      image = img('/img/circle_red.png');
      text = reporttext;
      clearTimeout(updateStatus.statusResetTimerID);
      updateStatus.statusResetTimerID = setTimeout('updateStatus("ready")',
				  gSTATUS_ERROR_TIME);
      break;
    default:
      image = '';
      text = '';
  }
  $('#cellIndicator').html(image);
  $('#cellStatus').html(text);
}

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
    createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  changeAndSerializeHash({state: 'newRecord'});
  cleanUp(true, '');
  $('.headline').text('BibEdit: Create new record');
  displayNewRecordList();
  bindNewRecordHandlers();
  updateStatus('ready');
  event.preventDefault();
}

function onSearchClick(event){
  /*
   * Handle 'Search' button (search for records).
   */
  updateStatus('updating');
  var searchPattern = $('#txtSearchPattern').val();
  var searchType = $('#sctSearchType').val();
  if (searchType == 'recID'){
    // Record ID - do some basic validation.
    var recID = parseInt(searchPattern);
    if (gRecID == recID){
      // We are already editing this record.
      updateStatus('ready');
      return;
    }
    if (gRecordDirty){
      // Warn of unsubmitted changes.
      if (!displayAlert('confirmLeavingChangedRecord')){
	updateStatus('ready');
	return;
      }
    }
    else if (gRecID)
      // If the record is unchanged, delete the cache.
      createReq({recID: gRecID, requestType: 'deleteRecordCache'});
    gNavigatingRecordSet = false;
    if (isNaN(recID)){
      // Invalid record ID.
      changeAndSerializeHash({state: 'edit', recid: searchPattern});
      cleanUp(true, null, null, true);
      updateStatus('error', gRESULT_CODES[102]);
      $('.headline').text('BibEdit: Record #' + searchPattern);
      displayMessage(102);
    }
    else{
      // Get the record.
      $('#txtSearchPattern').val(recID);
      getRecord(recID);
    }
  }
  else if (searchPattern.replace(/\s*/g, '')){
    // Custom search.
    if (gRecordDirty){
      // Warn of unsubmitted changes.
      if (!displayAlert('confirmLeavingChangedRecord')){
	updateStatus('ready');
	return;
      }
    }
    else if (gRecID)
      // If the record is unchanged, delete the cache.
      createReq({recID: gRecID, requestType: 'deleteRecordCache'});
    gNavigatingRecordSet = false;
    createReq({requestType: 'searchForRecord', searchType: searchType,
      searchPattern: searchPattern}, onSearchForRecordSuccess);
  }
}

function onSearchForRecordSuccess(json){
  /*
   * Handle successfull 'searchForRecord' requests (custom search).
   */
  gResultSet = json['resultSet'];
  if (gResultSet.length == 0){
    // Search yielded no results.
    changeAndSerializeHash({state: 'edit'});
    cleanUp(true, null, null, true, true);
    updateStatus('report', gRESULT_CODES[json['resultCode']]);
    displayMessage(-1);
  }
  else{
    if (gResultSet.length > 1){
      // Multiple results. Show record browser.
      gNavigatingRecordSet = true;
      var recordCount = gResultSet.length;
      $('#cellRecordNo').text(1 + ' / ' + recordCount);
      $('#btnPrev').attr('disabled', 'disabled');
      $('#btnNext').bind('click', onNextRecordClick).removeAttr('disabled');
      $('#rowRecordBrowser').show();
    }
    gResultSetIndex = 0;
    getRecord(gResultSet[0]);
  }
}

function getRecord(recID){
  /*
   * Get a record.
   */
  // Temporary store the record ID by attaching it to the onGetRecordSuccess
  // function.
  changeAndSerializeHash({state: 'edit', recid: recID});
  createReq({recID: recID, requestType: 'getRecord', deleteRecordCache:
	     getRecord.deleteRecordCache}, onGetRecordSuccess);
  getRecord.deleteRecordCache = false;
}
// Enable this flag to delete any existing cache before fetching next record.
getRecord.deleteRecordCache = false;


function onGetRecordSuccess(json){
  /*
   * Handle successfull 'getRecord' requests.
   */
  cleanUp(!gNavigatingRecordSet);
  // Store record data.
  gRecID = json['recID'];
  $('.headline').html(
    'BibEdit: Record #' + gRecID +
    '<a href="' + gHistoryURL + '?recid=' + gRecID +
    '" style="margin-left: 5px; font-size: 0.5em; color: #36c;">' +
    '(view history)' +
    '</a>').css('white-space', 'nowrap');
  gRecord = json['record'];
  gTagFormat = json['tagFormat'];
  gRecordDirty = json['cacheDirty'];
  gCacheMTime = json['cacheMTime'];
  if (json['cacheOutdated']){
    // User had an existing outdated cache.
    displayCacheOutdatedOptions('getRecord');
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
  // Display record.
  displayRecord();
  // Activate menu record controls.
  activateRecordMenu();
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
  tickets = json['tickets'];
  $('#tickets').html(tickets);
  updateStatus('report', gRESULT_CODES[json['resultCode']]);
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
	       });
    onSubmitClick.force = false;
  }
  else
    updateStatus('ready');
}
// Enable this flag to force the next submission even if cache is outdated.
onSubmitClick.force = false;

function onCancelClick(){
  /*
   * Handle 'Cancel' button (cancel editing).
   */
  updateStatus('updating');
  if (!gRecordDirty || displayAlert('confirmCancel')){
    createReq({recID: gRecID, requestType: 'cancel'}, function(json){
      // Cancellation was successful.
      changeAndSerializeHash({state: 'cancel', recid: gRecID});
      cleanUp(!gNavigatingRecordSet, '', null, true, true);
      updateStatus('report', gRESULT_CODES[json['resultCode']]);
    });
  }
  else
    updateStatus('ready');
}

function onCloneRecordClick(){
  /*
   * Handle 'Clone' button (clone record).
   */
  updateStatus('updating');
  if (gRecordDirty){
    if (!displayAlert('confirmLeavingChangedRecord')){
      updateStatus('ready');
      return;
    }
  }
  else
    // If the record is unchanged, erase the cache.
    createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  createReq({requestType: 'newRecord', newType: 'clone', recIDToClone: gRecID},
	    function(json){
    getRecord(json['recID']);
  });
}

function onNextRecordClick(){
  /*
   * Handle click on the 'Next' button in the record browser.
   */
  updateStatus('updating');
  if (gRecordDirty){
    if (!displayAlert('confirmLeavingChangedRecord')){
      updateStatus('ready');
      return;
    }
  }
  else
    // If the record is unchanged, erase the cache.
    createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  var recordCount = gResultSet.length;
  var prevIndex = gResultSetIndex++;
  var currentIndex = prevIndex + 1;
  if (currentIndex == recordCount-1)
    $(this).unbind('click').attr('disabled', 'disabled');
  if (prevIndex == 0)
    $('#btnPrev').bind('click', onPrevRecordClick).removeAttr('disabled');
  $('#cellRecordNo').text((currentIndex+1) + ' / ' + recordCount);
  getRecord(gResultSet[currentIndex]);
}

function onPrevRecordClick(){
  /*
   * Handle click on the 'Previous' button in the record browser.
   */
  updateStatus('updating');
  if (gRecordDirty){
    if (!displayAlert('confirmLeavingChangedRecord')){
      updateStatus('ready');
      return;
    }
  }
  else
    // If the record is unchanged, erase the cache.
    createReq({recID: gRecID, requestType: 'deleteRecordCache'});
  var recordCount = gResultSet.length;
  var prevIndex = gResultSetIndex--;
  var currentIndex = prevIndex - 1;
  if (currentIndex == 0)
    $(this).unbind('click').attr('disabled', 'disabled');
  if (prevIndex == recordCount-1)
    $('#btnNext').bind('click', onNextRecordClick).removeAttr('disabled');
  $('#cellRecordNo').text((currentIndex+1) + ' / ' + recordCount);
  getRecord(gResultSet[currentIndex]);
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
      updateStatus('report', gRESULT_CODES[resCode]);
      displayMessage(resCode);
    });
  }
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

function onAddFieldClick(){
  /*
   * Handle 'Add field' button.
   */
  // Create form and scroll close to the top of the table.
  $(document).scrollTop(0);
  var fieldTmpNo = onAddFieldClick.addFieldFreeTmpNo++;
  var jQRowGroupID = '#rowGroupAddField_' + fieldTmpNo;
  $('#bibEditColFieldTag').css('width', '90px');
  var tbodyElements = $('#bibEditTable tbody');
  var insertionPoint = (tbodyElements.length >= 4) ? 3 : tbodyElements.length-1;
  $('#bibEditTable tbody').eq(insertionPoint).after(
    createAddFieldForm(fieldTmpNo));
  $(jQRowGroupID).data('freeSubfieldTmpNo', 1);

  // Bind event handlers.
  $('#chkAddFieldControlfield_' + fieldTmpNo).bind('click',
    onAddFieldControlfieldClick);
  $('#btnAddFieldAddSubfield_' + fieldTmpNo).bind('click', function(){
    var subfieldTmpNo = $(jQRowGroupID).data('freeSubfieldTmpNo');
    $(jQRowGroupID).data('freeSubfieldTmpNo', subfieldTmpNo+1);
    var addFieldRows = $(jQRowGroupID + ' tr');
    $(addFieldRows).eq(addFieldRows.length-1).before(createAddFieldRow(
      fieldTmpNo, subfieldTmpNo));
    $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_' + subfieldTmpNo).bind(
      'keyup', onAddFieldChange);
    $('#btnAddFieldRemove_' + fieldTmpNo + '_' + subfieldTmpNo).bind('click',
      function(){
	$('#rowAddField_' + this.id.slice(this.id.indexOf('_')+1)).remove();
      });
  });
  $('#txtAddFieldTag_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldInd1_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldInd2_' + fieldTmpNo).bind('keyup', onAddFieldChange);
  $('#txtAddFieldSubfieldCode_' + fieldTmpNo + '_0').bind('keyup',
							  onAddFieldChange);
  $('#btnAddFieldSave_' + fieldTmpNo).bind('click', onAddFieldSave);
  $('#btnAddFieldCancel_' + fieldTmpNo).bind('click', function(){
    $(jQRowGroupID).remove();
    if (!$('#bibEditTable > [id^=rowGroupAddField]').length)
      $('#bibEditColFieldTag').css('width', '48px');
    reColorFields();
  });
  $('#btnAddFieldClear_' + fieldTmpNo).bind('click', function(){
    $(jQRowGroupID + ' input[type="text"]').val(''
      ).removeClass('bibEditInputError');
    $('#txtAddFieldTag_' + fieldTmpNo).focus();
  });

  reColorFields();
  $('#txtAddFieldTag_' + fieldTmpNo).focus();
  // Color the new form for a short period.
  $(jQRowGroupID).effect('highlight', {color: gNEW_ADD_FIELD_FORM_COLOR},
    gNEW_ADD_FIELD_FORM_COLOR_FADE_DURATION);
}
// Incrementing temporary field numbers.
onAddFieldClick.addFieldFreeTmpNo = 100000;

function onAddFieldControlfieldClick(){
  /*
   * Handle 'Controlfield' checkbox in add field form.
   */
  var fieldTmpNo = this.id.split('_')[1];

  // Remove any extra rows.
  var addFieldRows = $('#rowGroupAddField_' + fieldTmpNo + ' tr');
  $(addFieldRows).slice(2, addFieldRows.length-1).remove();

  // Clear all fields.
  var addFieldTextInput = $('#rowGroupAddField_' + fieldTmpNo +
			    ' input[type=text]');
  $(addFieldTextInput).val('').removeClass('bibEditInputError');

  // Toggle hidden fields.
  var elems = $('#txtAddFieldInd1_' + fieldTmpNo + ', #txtAddFieldInd2_' +
    fieldTmpNo + ', #txtAddFieldSubfieldCode_' + fieldTmpNo + '_0,' +
    '#btnAddFieldAddSubfield_' + fieldTmpNo).toggle();

  $('#txtAddFieldTag_' + fieldTmpNo).focus();
}

function onAddFieldChange(){
  /*
   * Validate MARC and add or remove error class.
   */
  if (this.value.length == this.maxLength){
    var fieldTmpNo = this.id.split('_')[1];
    var fieldType;
    if (this.id.indexOf('Tag') != -1)
      fieldType = ($('#chkAddFieldControlfield_' + fieldTmpNo).attr('checked')
		  ) ? 'ControlTag' : 'Tag';
    else if (this.id.indexOf('Ind') != -1)
      fieldType = 'Indicator';
    else
      fieldType = 'SubfieldCode';

    var valid = (fieldType == 'Indicator' && (this.value == '_'
					      || this.value == ' '))
                 || validMARC(fieldType, this.value);
    if (!valid && !$(this).hasClass('bibEditInputError'))
      $(this).addClass('bibEditInputError');
    else if (valid && $(this).hasClass('bibEditInputError'))
      $(this).removeClass('bibEditInputError');
  }
  else if ($(this).hasClass('bibEditInputError'))
    $(this).removeClass('bibEditInputError');
}

function onAddFieldSave(event){
  /*
   * Handle 'Save' button in add field form.
   */
  updateStatus('updating');
  var fieldTmpNo = this.id.split('_')[1];
  var controlfield = $('#chkAddFieldControlfield_' + fieldTmpNo).attr(
		       'checked');
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
    var fieldPosition = determineNewFieldPosition(tag, field);
  }
  else{
    // Regular field. Validate and prepare to update.
    ind1 = $('#txtAddFieldInd1_' + fieldTmpNo).val();
    ind1 = (ind1 == '' || ind1 == ' ') ? '_' : ind1;
    ind2 = $('#txtAddFieldInd2_' + fieldTmpNo).val();
    ind2 = (ind2 == '' || ind2 == ' ') ? '_' : ind2;
    var MARC = tag + ind1 + ind2;
    if (fieldIsProtected(MARC)){
      displayAlert('alertAddProtectedField', [MARC]);
      updateStatus('ready');
      return;
    }
    var validInd1 = (ind1 == '_' || validMARC('Indicator', ind1));
    var validInd2 = (ind2 == '_' || validMARC('Indicator', ind2));
    if (!validMARC('Tag', tag)
	|| !(ind1 == '_' || validMARC('Indicator', ind1))
	|| !(ind2 == '_' || validMARC('Indicator', ind2))){
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
        if (!$(this).hasClass('bibEditInputError')
	  && this.value != ''
	  && !$(txtValue).hasClass('bibEditInputError')
	  && value != '')
            subfields.push([this.value, value]);
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
    var field = [subfields, ind1, ind2, '', 0];
    var fieldPosition = determineNewFieldPosition(tag, field);
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
  $(rowGroup).effect('highlight', {color: gNEW_FIELDS_COLOR},
		     gNEW_FIELDS_COLOR_FADE_DURATION);
}

function onDeleteClick(event){
  /*
   * Handle 'Delete selected' button or delete hotkeys.
   */
  updateStatus('updating');
  var toDelete = {};
  // Collect and remove all marked fields.
  var checkedFieldBoxes = $('input[class="bibEditBoxField"]:checked');
  $(checkedFieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2];
    if (!toDelete[tag]){
      toDelete[tag] = {};
    }
    toDelete[tag][fieldPosition] = [];
  });
  // Collect subfields to be deleted in a datastructure.
  var checkedSubfieldBoxes = $('input[class="bibEditBoxSubfield"]:checked');
  $(checkedSubfieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldPosition = tmpArray[2],
      subfieldIndex = tmpArray[3];
    if (!toDelete[tag]){
      toDelete[tag] = {};
      toDelete[tag][fieldPosition] = [subfieldIndex];
    }
    else{
      if (!toDelete[tag][fieldPosition])
	toDelete[tag][fieldPosition] = [subfieldIndex];
      else if (toDelete[tag][fieldPosition].length == 0)
	// Entire field scheduled for the deletion.
	return;
      else
	toDelete[tag][fieldPosition].push(subfieldIndex);
    }
  });
  var fieldsDeleted = Boolean(checkedFieldBoxes.length);

  if (!fieldsDeleted && !checkedSubfieldBoxes.length){
    // No field/subfields selected.
    if (event.type == 'keydown' && event.target.nodeName == 'TD'){
      // Delete focused field/subfield.
      var targetID = event.target.id;
      var tmpArray = targetID.split('_');
      if (tmpArray[0] == 'content'){
	var tag = tmpArray[1], fieldPosition = tmpArray[2],
	  subfieldIndex = tmpArray[3];
	toDelete[tag] = {};
	if (event.shiftKey){
	  toDelete[tag][fieldPosition] = [];
	  fieldsDeleted = true;
	}
	else
	  toDelete[tag][fieldPosition] = [subfieldIndex];
      }
    }
    else{
      // Not a valid deletion event.
      updateStatus('ready');
      return;
    }
  }

  // Assert that no protected fields are scheduled for deletion.
  var protectedField = containsProtectedField(toDelete);
  if (protectedField){
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

  /* Continue local updating.
  Parse datastructure and delete accordingly in record, then redraw
  fields that had subfields deleted. */
  var fieldsToDelete, subfieldIndexesToDelete, field, subfields,
    subfieldIndex;
  var tagsToRedraw = [];
  for (var tag in toDelete){
    fieldsToDelete = toDelete[tag];
    for (var fieldPosition in fieldsToDelete){
      var fieldID = tag + '_' + fieldPosition;
      subfieldIndexesToDelete = fieldsToDelete[fieldPosition];
      if (subfieldIndexesToDelete.length == 0){
	deleteFieldFromTag(tag, fieldPosition);
	tagsToRedraw[tag] = true;
	// $('#rowGroup_' + fieldID).remove();
      }
      else{
	subfieldIndexesToDelete.sort();
	field = gRecord[tag][fieldPosition];
	subfields = field[0];
	for (var j=subfieldIndexesToDelete.length-1; j>=0; j--)
	  subfields.splice(subfieldIndexesToDelete[j], 1);
	var rowGroup = $('#rowGroup_' + fieldID);
	if (!fieldsDeleted){
	  // Color and redraw the field, if it won't be done later.
	  var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
	  $(rowGroup).replaceWith(createField(tag, field));
	  if (coloredRowGroup)
	    $('#rowGroup_' + fieldID).addClass( 'bibEditFieldColored');
	}
	else if (!tagsToRedraw.tag)
	  // Redraw the field if it won't be done later.
	  $(rowGroup).replaceWith(createField(tag, field));
      }
    }
  }
  if (fieldsDeleted)
    // If entire fields has been deleted, redraw all fields with the same tag
    // and recolor the full table.
    for (tag in tagsToRedraw)
      redrawFields(tag);
    reColorFields();
}