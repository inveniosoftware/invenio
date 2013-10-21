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
  $('#bibEditMenu .bibEditMenuSectionHeader').bind('click',
    toggleMenuSection);
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

function toggleMenuSection() {
  /*
   * Toggle a menu section.
   */
   var $el = $(this).children('img:first-child');
  if($el.hasClass("bibEditImgCompressMenuSection")){
    $el.compressMenuSection();
  }
  else if($el.hasClass("bibEditImgExpandMenuSection")){
    $el.expandMenuSection();
  }
}

$.fn.expandMenuSection = function() {
  /*
   * Expand a menu section.
   */
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').show();

  $(this).replaceWith(img('/img/bullet_toggle_minus.png', '',
        'bibEditImgCompressMenuSection'));
};

$.fn.compressMenuSection = function() {
  var parent = $(this).parent();
  parent.closest('.bibEditMenuSection').find('.bibEditMenuMore').hide();

  $(this).replaceWith(img('/img/bullet_toggle_plus.png', '',
       'bibEditImgExpandMenuSection'));
};

function activateRecordMenu(){
  /*
   * Activate menu record controls.
   */
  if (!$('#imgCloneRecord').hasClass('bibEditImgCtrlEnabled')) {
    $('#imgCloneRecord').on('click', onCloneRecordClick).removeClass(
    'bibEditImgCtrlDisabled').addClass('bibEditImgCtrlEnabled');
  }
  $('#btnCancel').removeAttr('disabled');
  $('#btnDeleteRecord').removeAttr('disabled');
  $('#btnAddField').removeAttr('disabled');
}

function deactivateRecordMenu(){
  /*
   * Deactivate menu record controls.
   */
  if (!$('#imgCloneRecord').hasClass('bibEditImgCtrlDisabled')) {
    $('#imgCloneRecord').off('click').removeClass(
    'bibEditImgCtrlEnabled').addClass('bibEditImgCtrlDisabled');
  }
  $('#btnSubmit').attr('disabled', 'disabled');
  $('#btnSubmit').css('background-color', '');
  $('#btnCancel').attr('disabled', 'disabled');
  $('#btnDeleteRecord').attr('disabled', 'disabled');
  $('#btnMARCTags').attr('disabled', 'disabled');
  $('#btnHumanTags').attr('disabled', 'disabled');
  $('#btnAddField').attr('disabled', 'disabled');
  $('#btnDeleteSelected').attr('disabled', 'disabled');
}

function activateSubmitButton() {
  /*
   * Enables the submission of the record
   */
  $('#btnSubmit').removeAttr('disabled');
  $('#btnSubmit').css('background-color', 'lightgreen');
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

function onSearchClick(event) {
  /*
   * Handle 'Search' button (search for records).
   */
  updateStatus('updating');

  var searchPattern = $('#txtSearchPattern').val();
  log_action("onSearchClick " + searchPattern);

  var searchType = $('#sctSearchType').val();

  if ( searchType == 'recID' ) {
    // Record ID - do some basic validation.
    var searchPatternParts = searchPattern.split(".");
    var recID = parseInt(searchPatternParts[0], 10);
    var recRev = searchPatternParts[1];

    if ( gRecID == recID ) {
      if ( !recRev || ( recRev == gRecRev ) ) {
        // We are already editing this record.
        updateStatus('ready');
        return;
      }
    }

    if ( gRecordDirty || gReqQueue.length > 0 ) {
      // Warn of unsubmitted changes.
      if (!displayAlert('confirmLeavingChangedRecord')){
        updateStatus('ready');
        return;
      }
    }

    gNavigatingRecordSet = false;
    if ( isNaN(recID) ) {
      // Invalid record ID.
      changeAndSerializeHash({state: 'edit', recid: searchPattern});
      cleanUp(true, null, null, true);
      updateStatus('error', gRESULT_CODES[102]);
      updateToolbar(false);
      displayMessage(102);
    }
    else {
      // Get the record.
      if (recRev == undefined) {
        $('#txtSearchPattern').val(recID);
        getRecord(recID);
      }
      else {
        recRev = recRev.replace(/\s+$/, '');
        $('#txtSearchPattern').val(recID + "." + recRev);
        getRecord(recID, recRev);
      }
    }
  }
  else if (searchPattern.replace(/\s*/g, '')) {
    // Custom search.
    if ( gRecordDirty || gReqQueue.length > 0 ) {
      // Warn of unsubmitted changes.
      if (!displayAlert('confirmLeavingChangedRecord')){
        updateStatus('ready');
        return;
      }
    }
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
  if (gResultSet.length == 0) {
    cleanUp(true, null, null, true, true);
    // Search yielded no results.
    changeAndSerializeHash({state: 'edit'});
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
  log_action("onNextRecordClick");
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
  log_action("onPrevRecordClick");
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

function ticketToHtml(ticket, index) {
  /*
   * Creates the html code for a ticket.
   */
  var html = '<div class=ticket id=ticket'+ ticket.id +' >\
                  <div class=ticketDetails>\
                      <a href="'+ ticket.url +'" title="View ticket on RT site"\
                          class="bibEditRTTicketLink" target="_blank" >\
                          See in RT\
                      </a>\
                      <span class="ticketSpan">#'+ (index+1).toString() +'</br>' +
                        ticket.date + '</br>' + ticket.queue +
                     '</span></br>\
                  </div>\
                  <div class=ajaxLoader >\
                      <img class=ajaxLoader src="/img/indicator.gif">\
                      <span class=ajaxLoader > processing ticket</span>\
                  </div>\
                  <div class=ticketButtons >\
                      <a href="#" title="Preview ticket details" class="bibEditPreviewTicketLink" >\
                          <img src="/img/magnifying_plus.png" class="bibEditPreviewTicketLinkImg">\
                      </a>\
                      <a href="'+ ticket.close_url +'" title="Resolve ticket" class="bibEditCloseTicketLink" >\
                          <img src="/img/aid_check.png" class="bibEditCloseTicketLinkImg">\
                      </a>\
                      <div class=bibeditTicketPreviewBox >\
                          <div id=previewBoxTriangle ></div>\
                          <a class=closePreviewBox href="#" >close</a>\
                          <p>\
                              <h2>Title</h2><hr>'+ ticket.subject +'<br/><br/>\
                              <h2>Description</h2><hr>'+ ticket.text +'</br>\
                          </p>\
                      </div>\
                  </div>\
              </div>';
  return html;
}

function addErrorMsg(ticketID, msg) {
  /*
   * Adds an error message to the ticket details div.
   */
   $("#ticket" + ticketID + " .ticketSpan").after('<br/><span class="ticketErrorMsg">' + msg + '<span/>');
}

function removeTicketError(ticketID) {
  /*
   * Removes an existing error message from the ticket details div.
   */
  if($("#ticket" + ticketID + " .ticketErrorMsg").length > 0 ){
     $("#ticket" + ticketID + " .ticketErrorMsg").remove();
     $("#ticket" + ticketID + " .ticketSpan").next().remove();
 }
}

function rtConnectionError(msg) {
  $("#tickets").children().remove();
  $("#newTicketDiv").remove();
  $(".bibEditTicketsMenuSection").append('<div id="rtError" class="bibEditMenuMore"><span class="ticketErrorMsg" >' +
     msg + '</span></br><a href="#" id="retryRtConnection">Retry</a></div>');
  $("#retryRtConnection").on('click', function(){
    $("#rtError").remove();
    $("#loadingTickets").show();
    createReq({recID: gRecID, requestType: 'getTickets'}, onGetTicketsSuccess);
  });
}

function onGetTicketsSuccess(json) {
/*
 * Handle successfull 'getTickets' requests.
 */
  // clean tickets area
  $('#tickets').empty();
  $('#newTicketDiv').remove();
  $('#rtError').remove();

  $("#loadingTickets").hide();
  var tickets = json['tickets'];
  if (json['resultCode'] == 31 && json['tickets'] && gRecID) {
     for(var i=0; i < tickets.length; i++) {
       var ticket = tickets[i];
       $('#tickets').append(ticketToHtml(ticket, i));
    }
    // new ticket link
    $('.bibEditTicketsMenuSection').append('<div id="newTicketDiv" class="bibEditMenuMore"><a id=newTicketLink href="#" \
                                               target="_blank" title="Create new ticket">[new ticket]</a>\
                                            <select id="queue" name="queue" >\
                                               <option value="0">in Queue:</option>\
                                            </select></div>');
    // produce html for every queue
    var queues = json['queues'];
    for(var i=0; i < queues.length; i++) {
      var queue = queues[i];
      $('#queue').append('<option value="'+ queue.id + '">' + queue.name + '</option>');
    }
    // new ticket link
    $("#newTicketLink").on('click', function(event) {
      if ($("#queue").val() == 0) {
        if ($("#queueError").length <= 0) {
            $("#queue").after('<span id="queueError">\
                                 Please select a queue\
                               </span>')
        }
        event.preventDefault();
      }
      else {
        $("#queueError").remove();
        var href = gBIBCATALOG_SYSTEM_RT_URL +'/Ticket/Create.html?Queue=' + $("#queue").val();
        $(this).attr("href", href);
      }
    });
    // preview link
    $(".ticketButtons .bibEditPreviewTicketLink").on('click',function(event) {
      if ($(this).siblings(".bibeditTicketPreviewBox").is(":visible")) {
         $(".bibeditTicketPreviewBox:visible").hide();
      }
      else {
        $(".bibeditTicketPreviewBox:visible").hide();
        $(this).siblings(".bibeditTicketPreviewBox").show();
      }
      event.preventDefault();
    });
    // preview box close link
    $(".closePreviewBox").on('click',function(event) {
       $(this).parent().hide();
       event.preventDefault();
    });
    // closeTicket link
    $(".ticketButtons .bibEditCloseTicketLink").on('click',function(event) {
       var ticketId = $(this).parent().parent().attr('id').substring(6);// e.g ticket195561
       $(this).siblings(".bibeditTicketPreviewBox").hide();
       $("#ticket" + ticketId).children().hide();
       $("#ticket" + ticketId).children(".ajaxLoader").children().show();
       $("#ticket" + ticketId).children(".ajaxLoader").show();
       var errorCallback = onCloseTicketError(ticketId);
       createReq({recID: gRecID, ticketid:ticketId, requestType: 'closeTicket'}, onCloseTicketSuccess,
                  undefined, undefined, errorCallback);
       event.preventDefault();
    });
    // closeTicket link
    $(".ticketButtons .bibEditCloseTicketLink").on('click',function(event) {
       var ticketId = $(this).parent().parent().attr('id').substring(6);// e.g ticket195561
       $(this).siblings(".bibeditTicketPreviewBox").hide();
       $("#ticket" + ticketId).children().hide();
       $("#ticket" + ticketId).children(".ajaxLoader").children().show();
       $("#ticket" + ticketId).children(".ajaxLoader").show();
       var errorCallback = onCloseTicketError(ticketId);
       createReq({recID: gRecID, ticketid:ticketId, requestType: 'closeTicket'}, onCloseTicketSuccess,
                  undefined, undefined, errorCallback);
       event.preventDefault();
    });
  }
  else if(json['resultCode'] == 125) {
    rtConnectionError(json['tickets']);
  }
}

function onCloseTicketSuccess(json) {
/*
 * Handle successfull 'closeTicket' requests.
 */
 var ticketID = json['ticketid'];
 //stop ajaxloader
 $("#ticket" + ticketID).children(".ajaxLoader").hide();
 removeTicketError(ticketID);
 if (json['ticket_closed_code'] == 121 && json['ticket_closed_description'] && gRecID) {
    $("#ticket" + ticketID + " .ticketSpan").children("br:first-child").before(' resolved');
    $("#ticket" + ticketID + " .ticketSpan").addClass("ticketResolved");
    // undo link
    var link = '<a href="#" title="Open ticket" class ="openTicketLink" id="openTicket' + ticketID + '" >Undo</a>';
    $("#ticket" + ticketID + " .ticketSpan").after(link);
    $("#openTicket" + ticketID).on('click', function(event) {
         var ticketId = $(this).attr('id').substring(10);//e.g openTicket195561
         $("#ticket" + ticketID).children().hide();
         $("#ticket" + ticketID).children(".ajaxLoader").children().show();
         $("#ticket" + ticketID).children(".ajaxLoader").show();
         var errorCallback = onOpenTicketError(ticketId);
          createReq({recID: gRecID, ticketid:ticketId, requestType: 'openTicket'}, onOpenTicketSuccess,
                    undefined, undefined, onOpenTicketError);
         event.preventDefault();
    });
    $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
    $("#ticket" + ticketID + " .ticketButtons").hide();
 }
 else {
    if (json['ticket_closed_code'] == 125) {
       $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
       rtConnectionError(json['ticket_closed_description']);
    }
    else {
        $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
        addErrorMsg(ticketID, json['ticket_closed_description']);
    }
 }
}

function onCloseTicketError(ticketid) {
  /*
   * Handle failed 'closeTicket' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var ticketID = ticketid;
      //stop ajaxloader
      $("#ticket" + ticketID).children(".ajaxLoader").hide();
      removeTicketError(ticketID);
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
        addErrorMsg(ticketID, 'Error occured.Try again');
    };
}

function onOpenTicketSuccess(json) {
/*
 * Handle successfull 'openTicket' requests.
 */
 var ticketID = json['ticketid'];
 //stop ajaxloader
 $("#ticket" + ticketID).children(".ajaxLoader").hide();
 removeTicketError(ticketID);
 if (json['ticket_opened_code'] == 123 && json['ticket_opened_description'] && gRecID) {
    var span_html = $("#ticket" + ticketID +" .ticketSpan").html();
    $("#ticket" + ticketID + " .ticketSpan").html(span_html.split(" resolved").join(""));// remove resolved
    $("#ticket" + ticketID + " .ticketSpan").removeClass("ticketResolved");
    $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
    $("#openTicket" + ticketID).remove();
 }
 else {
    if(json['ticket_opened_code'] == 125) {
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      rtConnectionError(json['ticket_opened_description']);
    }
    else {
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      addErrorMsg(ticketID, json['ticket_opened_description']);
    }
 }
}

function onOpenTicketError(ticketid) {
/*
 * Handle failed 'openTicket' requests.
 */
    return function (XHR, textStatus, errorThrown) {
      var ticketID = ticketid;
      $("#ticket" + ticketID).children(".ajaxLoader").hide();
      removeTicketError(ticketID);
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      addErrorMsg(ticketID, 'Error occured.Try again');
    };
}

function onCloseTicketSuccess(json) {
/*
 * Handle successfull 'closeTicket' requests.
 */
 var ticketID = json['ticketid'];
 //stop ajaxloader
 $("#ticket" + ticketID).children(".ajaxLoader").hide();
 removeTicketError(ticketID);
 if (json['ticket_closed_code'] == 121 && json['ticket_closed_description'] && gRecID) {
    $("#ticket" + ticketID + " .ticketSpan").children("br:first-child").before(' resolved');
    $("#ticket" + ticketID + " .ticketSpan").addClass("ticketResolved");
    // undo link
    var link = '<a href="#" title="Open ticket" class ="openTicketLink" id="openTicket' + ticketID + '" >Undo</a>';
    $("#ticket" + ticketID + " .ticketSpan").after(link);
    $("#openTicket" + ticketID).on('click', function(event) {
         var ticketId = $(this).attr('id').substring(10);//e.g openTicket195561
         $("#ticket" + ticketID).children().hide();
         $("#ticket" + ticketID).children(".ajaxLoader").children().show();
         $("#ticket" + ticketID).children(".ajaxLoader").show();
         var errorCallback = onOpenTicketError(ticketId);
          createReq({recID: gRecID, ticketid:ticketId, requestType: 'openTicket'}, onOpenTicketSuccess,
                    undefined, undefined, onOpenTicketError);
         event.preventDefault();
    });
    $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
    $("#ticket" + ticketID + " .ticketButtons").hide();
 }
 else {
    if (json['ticket_closed_code'] == 125) {
       $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
       rtConnectionError(json['ticket_closed_description']);
    }
    else {
        $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
        addErrorMsg(ticketID, json['ticket_closed_description']);
    }
 }
}

function onCloseTicketError(ticketid) {
  /*
   * Handle failed 'closeTicket' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var ticketID = ticketid;
      //stop ajaxloader
      $("#ticket" + ticketID).children(".ajaxLoader").hide();
      removeTicketError(ticketID);
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
        addErrorMsg(ticketID, 'Error occured.Try again');
    };
}

function onOpenTicketSuccess(json) {
/*
 * Handle successfull 'openTicket' requests.
 */
 var ticketID = json['ticketid'];
 //stop ajaxloader
 $("#ticket" + ticketID).children(".ajaxLoader").hide();
 removeTicketError(ticketID);
 if (json['ticket_opened_code'] == 123 && json['ticket_opened_description'] && gRecID) {
    var span_html = $("#ticket" + ticketID +" .ticketSpan").html();
    $("#ticket" + ticketID + " .ticketSpan").html(span_html.split(" resolved").join(""));// remove resolved
    $("#ticket" + ticketID + " .ticketSpan").removeClass("ticketResolved");
    $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
    $("#openTicket" + ticketID).remove();
 }
 else {
    if(json['ticket_opened_code'] == 125) {
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      rtConnectionError(json['ticket_opened_description']);
    }
    else {
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      addErrorMsg(ticketID, json['ticket_opened_description']);
    }
 }
}

function onOpenTicketError(ticketid) {
/*
 * Handle failed 'openTicket' requests.
 */
    return function (XHR, textStatus, errorThrown) {
      var ticketID = ticketid;
      $("#ticket" + ticketID).children(".ajaxLoader").hide();
      removeTicketError(ticketID);
      $("#ticket" + ticketID).children(":not(.ajaxLoader)").show();
      addErrorMsg(ticketID, 'Error occured.Try again');
    };
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
    case 'saving':
        image = img('/img/indicator.gif');
        text = 'Saving changes...';
        break;
      // Generic report. Resets to 'Ready' after timeout.
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
    $('#ImgBibCirculationMenu').trigger('click');
}
