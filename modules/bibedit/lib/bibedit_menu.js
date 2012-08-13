/*
 * This file is part of Invenio.
 * Copyright (C) 2009, 2010, 2011 CERN.
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
 * This is the BibEdit Javascript for all functionality directly related to the
 * left hand side menu, including event handlers for most of the buttons.
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
      $('#btnSearch').trigger('click');
      event.preventDefault();
    }
  });
  // Set the status.
  $('#cellIndicator').html(img('/img/circle_green.png'));
  $('#cellStatus').text('Ready');
  // Bind button event handlers.
  $('#imgNewRecord').bind('click', onNewRecordClick);
  $('#imgTemplateRecord').bind('click', onTemplateRecordClick);
  $('#btnSearch').bind('click', onSearchClick);
  $('#btnSubmit').bind('click', onSubmitClick);
  $('#btnCancel').bind('click', onCancelClick);
  $('#btnDeleteRecord').bind('click', onDeleteRecordClick);
  $('#btnMARCTags').bind('click', onMARCTagsClick);
  $('#btnHumanTags').bind('click', onHumanTagsClick);
  $('#btnAddField').bind('click', onAddFieldClick);
  $('#btnDeleteSelected').bind('click', onDeleteClick);
  $('#bibEditMenu .bibEditImgCompressMenuSection').bind('click',
    compressMenuSection);
  // Focus on record selection box.
  $('#txtSearchPattern').focus();
  // Initialise the handlers for undo/redo buttons
  $('#bibEditURUndoListLayer').bind("mouseover", showUndoPreview);
  $('#bibEditURUndoListLayer').bind("mouseout", hideUndoPreview);
  $('#bibEditURRedoListLayer').bind("mouseover", showRedoPreview);
  $('#bibEditURRedoListLayer').bind("mouseout", hideRedoPreview);
  $('#btnUndo').bind('click', onUndo);
  $('#btnRedo').bind('click', onRedo);
  $('#lnkSpecSymbols').bind('click', onLnkSpecialSymbolsClick);
  $('#btnSwitchReadOnly').bind('click', onSwitchReadOnlyMode);
  collapseMenuSections();
}

function expandMenuSection(){
  /*
   * Expand a menu section.
   */
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').show();

  $(this).replaceWith(img('/img/bullet_toggle_minus.png', '',
			  'bibEditImgCompressMenuSection'));
  parent.find('.bibEditImgCompressMenuSection').bind('click',
						     compressMenuSection);
}

function compressMenuSection(){
  /*
   * Compress a menu section.
   */
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').hide();

  $(this).replaceWith(img('/img/bullet_toggle_plus.png', '',
			  'bibEditImgExpandMenuSection'));
  parent.find('.bibEditImgExpandMenuSection').bind('click', expandMenuSection);
}

function activateRecordMenu(){
  /*
   * Activate menu record controls.
   */
  $('#imgCloneRecord').bind('click', onCloneRecordClick).removeClass(
    'bibEditImgCtrlDisabled').addClass('bibEditImgCtrlEnabled');
  $('#btnCancel').removeAttr('disabled');
  $('#btnDeleteRecord').removeAttr('disabled');
  $('#btnAddField').removeAttr('disabled');
}

function deactivateRecordMenu(){
  /*
   * Deactivate menu record controls.
   */
  $('#imgCloneRecord').unbind('click').removeClass(
    'bibEditImgCtrlEnabled').addClass('bibEditImgCtrlDisabled');
  $('#btnSubmit').attr('disabled', 'disabled');
  $('#btnSubmit').css('background-color', '');
  $('#btnCancel').attr('disabled', 'disabled');
  $('#btnDeleteRecord').attr('disabled', 'disabled');
  $('#btnMARCTags').attr('disabled', 'disabled');
  $('#btnHumanTags').attr('disabled', 'disabled');
  $('#btnAddField').attr('disabled', 'disabled');
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

function onSearchClick(event){
  /*
   * Handle 'Search' button (search for records).
   */
  updateStatus('updating');
  var searchPattern = $('#txtSearchPattern').val();
  var searchType = $('#sctSearchType').val();
  if (searchType == 'recID'){
    // Record ID - do some basic validation.
    var searchPatternParts = searchPattern.split(".");
    var recID = parseInt(searchPatternParts[0]);
    var recRev = searchPatternParts[1];

    if (gRecID == recID && recRev == gRecRev){
      // We are already editing this record.
      updateStatus('ready');
      return;
    }
    if (gRecordDirty && gReadOnlyMode == false){
      // Warn of unsubmitted changes.
      if (!displayAlert('confirmLeavingChangedRecord')){
	updateStatus('ready');
	return;
      }
    }
    else if (gRecID && gReadOnlyMode == false)
      // If the record is unchanged, delete the cache.
      createReq({recID: gRecID, requestType: 'deleteRecordCache'});

    gNavigatingRecordSet = false;
    if (isNaN(recID)){
      // Invalid record ID.
      changeAndSerializeHash({state: 'edit', recid: searchPattern});
      cleanUp(true, null, null, true);
      updateStatus('error', gRESULT_CODES[102]);
      updateToolbar(false);
      displayMessage(102);
    }
    else{
      // Get the record.
      if (recRev == undefined){
        $('#txtSearchPattern').val(recID);
        getRecord(recID);
      } else {
        recRev = recRev.replace(/\s+$/, '');
        $('#txtSearchPattern').val(recID + "." + recRev);
        getRecord(recID, recRev);
      }
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

function onGetTicketsSuccess(json){
/*
 * Handle successfull 'getTickets' requests.
 */
  var tickets = json['tickets'];
  if (json['resultCode'] == 31 && json['tickets'] && gRecID){
    $('#tickets').html(tickets);
    $('#lnkNewTicket').bind('click', function(event){
      setTimeout('createReq({recID: gRecID, requestType: "getTickets"},' +
		 'onGetTicketsSuccess)', gTICKET_REFRESH_DELAY);
    });
  }
}

function updateStatus(statusType, reporttext, enableToolbar){
  /*
   * Update status (in the bottom of the menu).
   */
  var image, text;
	gCurrentStatus = statusType;

  if (enableToolbar === undefined) {
    enableToolbar = false;
  }
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
      updateToolbar(enableToolbar);
      image = img('/img/circle_red.png');
      text = reporttext;
      clearTimeout(updateStatus.statusResetTimerID);
      updateStatus.statusResetTimerID = setTimeout('updateStatus("ready")',
				  gSTATUS_ERROR_TIME);
      break;
    default:
      image = '';
      text = '';
      break;
  }
  $('#cellIndicator').html(image);
  $('#cellStatus').html(text);
}

function collapseMenuSections() {
    $('#ImgHistoryMenu').trigger('click');
    $('#ImgViewMenu').trigger('click');
    $('#ImgRecordMenu').trigger('click');
}
