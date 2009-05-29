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

var gRecID1 = null;
var gRecID2 = null;
var gSelectedSubfield = null;
var gSelectRecordMode = 0; //O:simple, 1:search, 2:revisions

var gSearchResults = null;
var gSearchResultsIndex = 0;

var gHash;
var gHASH_CHECK_INTERVAL = 150;
var gHashCheckTimerID;
var gMsgTimeout;

$(document).ready( function(){
  initAJAX();
  initPanel();
  initContent();
//  initStateFromHash();
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
//  defaultBehaviour();
//  $(document).bind('keydow.parent()n', 'Ctrl+f1', copySubfield);
//  $(document).bind('keydown', 'Ctrl+f2', pasteSubfield);
});

function showMessage(msgType, message, timeToHide) {
  hideMessage();
  clearTimeout(gMsgTimeout);
  $('#bibMergeMessage').removeClass();
  if (msgType == 'LoadingMsg') {
    message = message + '  <img src="/img/loading.gif" />';
  }
  else if (msgType == 'OKMsg') {
    $('#bibMergeMessage').addClass('bibMergeMessageOK');
  }
  else if (msgType == 'ErrorMsg') {
    $('#bibMergeMessage').addClass('bibMergeMessageError');
  }
  //$('#bibMergeMessage').html(message).show('drop','',500);
  $('#bibMergeMessage').html(message).show();
  //hide the message after some milliseconds if the parameter is set
  if (typeof(timeToHide) != 'undefined')
  	 hideMessage(timeToHide);
}

function hideMessage(timeout) {
  if (typeof(timeout) != 'undefined') { //check if parameter was defined
    gMsgTimeout = setTimeout(function(){
      $('#bibMergeMessage').removeClass().hide().fadeOut();
    }, timeout);
  }
  else  //if parameter 'timeout' not set, then hide without delay
    $('#bibMergeMessage').removeClass().hide().fadeOut();
}

function isValidRecid(recid) {
  var recnum = parseInt(recid);
  if (isNaN(recnum) || recnum < 1)
    return false;
  return true;
}

function initStateFromHash() {
  if (window.location.hash == gHash)
    return;
  gHash = window.location.hash;
  if (gHash == '') {
    $('#bibMergeContent').html('Select two records to be compared from the side panel.');
    return;
  }
  var parsedHash = deserializeHash(gHash);

  if (parsedHash.recid1 && isValidRecid(parsedHash.recid1)==true && parsedHash.recid2 && isValidRecid(parsedHash.recid2)==true) {
    ajaxGetRecordCompare(parsedHash.recid1, parsedHash.recid2);
    //ajaxGetRecordsFullHtml(parsedHash.recid1, parsedHash.recid2);
    return;
  }
  // if wrong parameters where given in the url:
  $('#bibMergeContent').html('INVALID URL PARAMETERS');
}

function deserializeHash(aHash) {
  var hashElements = {};
  var args = aHash.slice(1).split('&');
  var tmpArray;
  for (var i=0, n=args.length; i<n; i++){
    tmpArray = args[i].split('=');
    if (tmpArray.length == 2)
      hashElements[tmpArray[0]] = tmpArray[1];
  }
  return hashElements;
}

function changeAndSerializeHash(updateData) {
  clearTimeout(gHashCheckTimerID);
  gHash = '#';
  for (var key in updateData)
    gHash += key.toString() + '=' + updateData[key].toString() + '&';
  gHash = gHash.slice(0, -1);
  window.location.hash = gHash;
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
}

function initContent() {
  initFieldGroupHeaders(".bibMergeHeaderFieldnum"); //initialize all of them
  $('#bibMergeContent a').live('click', resetDiffs);
  $('.bibMergeFieldGroupRefresh').live('click', onclickFieldGroupRefresh);
  //$('.bibMergeFieldGroupDiff').live('click', onclickFieldGroupRefresh);
  $('.bibMergeFieldGroupMerge').live('click', onclickFieldGroupMerge)
  $('.bibMergeFieldGroupMergeNC').live('click', onclickFieldGroupMerge)
  $('.bibMergeFieldReplace').live('click', onclickFieldReplace);
  $('.bibMergeFieldAdd').live('click', onclickFieldAdd);
  $('.bibMergeFieldDelete').live('click', onclickFieldDelete);
  $('.bibMergeFieldMerge').live('click', onclickFieldMerge);
  $('.bibMergeSubfieldDelete').live('click', onclickSubfieldDelete);
  $('.bibMergeSubfieldReplace').live('click', onclickSubfieldReplace);
  $('.bibMergeSubfieldAdd').live('click', onclickSubfieldAdd);
  $('.bibMergeFieldGroupDiff').live('click', onclickSubfieldDiff);
  $('#bibMergeContent a:not([class])').live('click', notImplemented);
}
function resetDiffs() {
  $('#bibMergeContent td:has(span.bibMergeDiffSpanSame, span.bibMergeDiffSpanIns, span.bibMergeDiffSpanDel, span.bibMergeDiffSpanSub, )').each(function (i) {
    var subfield_value = $(this).text();
    $(this).html( subfield_value );
  });
}
function getSubfieldInfo(subfield) {
  var sfinfo = {}; //result
  sfinfo.sfindex1 = -1;
  sfinfo.sfindex2 = -1;
  sfinfo.subfield_lines = 0;
  var currTR = subfield.parents('tr');
  var currSF1id = currTR.children('td').eq(1).attr('id');
  while(!currSF1id) {
    sfinfo.subfield_lines++;
    if ( currTR.children('td').eq(1).text() != '')
      sfinfo.sfindex1++;
    if ( currTR.children('td').eq(3).text() != '')
      sfinfo.sfindex2++;
    currTR = currTR.prev('tr');
    currSF1id = currTR.children('td').eq(1).attr('id');
  }
  sfinfo.field1id = currSF1id;
  sfinfo.field2id = currTR.children('td').eq(3).attr('id');
  sfinfo.numOfSubfields1 = sfinfo.sfindex1 + 1;
  sfinfo.numOfSubfields2 = sfinfo.sfindex2 + 1;

  currTR = subfield.parents('tr');
  currTR = currTR.next('tr');
  while( currTR.size() > 0 && !currTR.children('td').eq(1).attr('id')) {
    sfinfo.subfield_lines++;
    if ( currTR.children('td').eq(1).text() != '')
      sfinfo.numOfSubfields1++;
    if ( currTR.children('td').eq(3).text() != '')
      sfinfo.numOfSubfields2++;
    currTR = currTR.next('tr');
  }
  return sfinfo;
}
function onclickSubfieldDiff() {
  var sfinfo = getSubfieldInfo( $(this) );
  var currTR = $(this).parents('tr'); //the current row of the table
  var value1 = currTR.children('td').eq(1).text();
  var value2 = currTR.children('td').eq(3).text();
  //if one of the subfields is empty
  if (value1 == '' || value2 == '')
    showMessage('ErrorMsg', 'One of the subfields is missing, no difference to show', 6000);
  else if (value1 == value2)
    showMessage('OKMsg', 'Subfields are identical, no difference to show', 6000);
  else {
    //ajax request to get the diffed row from server side
    var _data = {
      requestType: 'diffSubfield',
      recID1: gRecID1,
      recID2: gRecID2,
      fieldCode1: sfinfo.field1id,
      fieldCode2: sfinfo.field2id,
      sfindex1: sfinfo.sfindex1,
      sfindex2: sfinfo.sfindex2
    };
    showMessage('LoadingMsg', 'Diffing subfields...');
    ajaxRequest(_data, function(html){
      var prevTR = currTR.prev('tr');
      currTR.remove();
      prevTR.after(html);
    });
  }
  return false;
}
function onclickSubfieldDelete() {
  var sfinfo = getSubfieldInfo( $(this) );
  var currTR = $(this).parents('tr');
  if (currTR.children('td').eq(1).text() == '') { //if subfield1 is empty
    showMessage('ErrorMsg', 'Cannot delete subfield that doesn\'t exist', 6000);
    return false;
  }
  if (sfinfo.numOfSubfields1 == 1) //if field has one subfield, then delete field
    $("td#"+ sfinfo.field1id +" a.bibMergeFieldDelete").click();
  else {
    //ajax request to delete subfield on the server side
    var _data = {
      requestType: 'deleteSubfield',
      recID1: gRecID1,
      recID2: gRecID2,
      fieldCode1: sfinfo.field1id,
      fieldCode2: sfinfo.field2id,
      sfindex1: sfinfo.sfindex1,
      sfindex2: sfinfo.sfindex2
    };
    showMessage('LoadingMsg', 'Deleting subfield...');
    ajaxRequest(_data, function(html){} );
    //perform deletion on the client side
    if (currTR.children('td').eq(3).text() == '') //if subfield2 is empty
      currTR.remove();
    else
      currTR.children('td').eq(1).empty();
    currTR.children('td.bibMergeCellSimilarityGreen').attr('class', 'bibMergeCellSimilarityRed');
  }
  return false;
}
function onclickSubfieldReplace() {
  var sfinfo = getSubfieldInfo( $(this) );
  var currTR = $(this).parents('tr');
  if (currTR.children('td').eq(3).text() == '') { //if subfield2 is empty
    showMessage('ErrorMsg', 'Cannot replace subfield with one that doesn\'t exist', 6000);
    return false;
  }
  if (currTR.children('td').eq(1).text() != '') { //if subfield1 is not empty
    //ajax request to replace subfield on the server side
    var _data = {
      requestType: 'replaceSubfield',
      recID1: gRecID1,
      recID2: gRecID2,
      fieldCode1: sfinfo.field1id,
      fieldCode2: sfinfo.field2id,
      sfindex1: sfinfo.sfindex1,
      sfindex2: sfinfo.sfindex2
    };
    showMessage('LoadingMsg', 'Replacing subfield...');
    ajaxRequest(_data, function(html){} );
    //perform replacement on the client side
    currTR.children('td').eq(1).text( currTR.children('td').eq(3).text() );
    currTR.children('td.bibMergeCellSimilarityRed').attr('class', 'bibMergeCellSimilarityGreen');
    return false;
  }
  else {
    currTR.children('td').eq(2).children('a.bibMergeSubfieldAdd').click();
  }
  return false;
}
function onclickSubfieldAdd() {
  var sfinfo = getSubfieldInfo( $(this) );
  var currTR = $(this).parents('tr');
  if (currTR.children('td').eq(3).text() == '') { //if subfield2 is empty
    showMessage('ErrorMsg', 'Cannot add subfield that doesn\'t exist', 6000);
    return false;
  }
  if (sfinfo.numOfSubfields1 == 0) {//field1 doesn't exist
    showMessage('ErrorMsg', 'Field in the first record doesn\'t exist. Use Add Field instead which creates a new field', 8000);
  }
  else {
    if (currTR.children('td').eq(1).text() == '') //if subfield1 is empty
      sfinfo.sfindex1++;  //insertion should be before the next subfield that exists

    //ajax add subfield before sfindex1 on the server side
    var _data = {
      requestType: 'addSubfield',
      recID1: gRecID1,
      recID2: gRecID2,
      fieldCode1: sfinfo.field1id,
      fieldCode2: sfinfo.field2id,
      sfindex1: sfinfo.sfindex1,
      sfindex2: sfinfo.sfindex2
    };
    showMessage('LoadingMsg', 'Adding subfield...');
    ajaxRequest(_data, function(html){} );
    //perform addition of subfield on the client side
    if (currTR.children('td').eq(1).text() != '') { //if subfield1 is not empty
      //create another subfield line
      currTR.after( "<tr>"+ currTR.html() +"</tr>" );
      currTR.next('tr').children('td').eq(3).empty();
      currTR.next('tr').children('td.bibMergeCellSimilarityGreen').attr('class', 'bibMergeCellSimilarityRed');
    }
    currTR.children('td').eq(1).text( currTR.children('td').eq(3).text() ); //replace value
    currTR.children('td.bibMergeCellSimilarityRed').attr('class', 'bibMergeCellSimilarityGreen');
  }
  return false;
}
function onclickFieldMerge() {
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var fieldID1 = $(this).parents('tr').children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').children('td').eq(3).attr('id');
  var _data = {
    requestType: 'mergeField',
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag,
    fieldCode1: fieldID1,
    fieldCode2: fieldID2
  };
  showMessage('LoadingMsg', 'Merging Field...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    if (html != '') {
      prevDiv.after(html);
      initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
    }
  });
  return false;
}
function onclickFieldDelete() {
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var fieldID1 = $(this).parents('tr').children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').children('td').eq(3).attr('id');
  var _data = {
    requestType: 'deleteField',
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag,
    fieldCode1: fieldID1,
    fieldCode2: fieldID2
  };
  showMessage('LoadingMsg', 'Deleting Field...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    if (html != '') {
      prevDiv.after(html);
      initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
    }
  });
  return false;
}
function onclickFieldAdd() {
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var fieldID1 = $(this).parents('tr').children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').children('td').eq(3).attr('id');
  var _data = {
    requestType: 'addField',
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag,
    fieldCode1: fieldID1,
    fieldCode2: fieldID2
  };
  showMessage('LoadingMsg', 'Adding Field...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    //fieldGroupsOfTag.hide('drop','',500);
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    prevDiv.after(html);
    initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
  });
  return false;
}
function onclickFieldReplace() {
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var fieldID1 = $(this).parents('tr').children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').children('td').eq(3).attr('id');
  var _data = {
    requestType: 'replaceField',
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag,
    fieldCode1: fieldID1,
    fieldCode2: fieldID2
  };
  showMessage('LoadingMsg', 'Replacing Field...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    //fieldGroupsOfTag.hide('drop','',500);
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    prevDiv.after(html);
    initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
  });
  return false;
}
function onclickFieldGroupMerge() {
  var mergeType; //merging mode
  if ( $(this).hasClass('bibMergeFieldGroupMergeNC') )
    mergeType = 'mergeNCFieldGroup';
  else
    mergeType = 'mergeFieldGroup';
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var _data = {
    requestType: mergeType,
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag
  };
  showMessage('LoadingMsg', 'Merging...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    //fieldGroupsOfTag.hide('drop','',500);
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    prevDiv.after(html);
    initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
  });
  return false;
}
function onclickFieldGroupRefresh() {
  var refType;
  if ( $(this).hasClass('bibMergeFieldGroupDiff') )
    refType = 'getFieldGroupDiff';
  else
    refType = 'getFieldGroup';
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var _data = {
    requestType: refType,
    recID1: gRecID1,
    recID2: gRecID2,
    fieldTag: ftag
  };
  showMessage('LoadingMsg', 'Please wait...');
  ajaxRequest(_data, function(html) {
    var fnum = ftag.substring(0,3);
    var fieldGroupsOfTag = $("div.bibMergeFieldGroupDiv[id*='-"+fnum+"']");
    //fieldGroupsOfTag.hide('drop','',500);
    var prevDiv = fieldGroupsOfTag.eq(0).prev('.bibMergeFieldGroupDiv');
    fieldGroupsOfTag.remove();
    prevDiv.after(html);
    initFieldGroupHeaders("div.bibMergeFieldGroupDiv[id*='-"+fnum+"'] .bibMergeHeaderFieldnum");
  });
  return false;
}
function initFieldGroupHeaders(selector) {
  $(selector).toggle(
    function() {
      $(this).parents(".bibMergeFieldGroupDiv").find(".bibMergeFieldTable").hide();
      return false; },
    function() {
      $(this).parents(".bibMergeFieldGroupDiv").find(".bibMergeFieldTable").show();
      return false;
    }
  );
}

function initPanel() {
  //deactivatePanel();
  $('#bibMergeMessage').hide();
  $('#bibMergeSearchPanel').hide();
  $('#bibMergeBtnCompare').click(onclickCompareButton);
  $('#bibMergeBtnSubmit').click(onclickSubmitButton);
  $('#bibMergeBtnCancel').click(onclickCancelButton);
  $('#bibMergeBtnSearch').click(onclickSearchButton);
  $('#bibMergeMethodSelect').change(onchangeMethodSelect);
  onchangeMethodSelect();
  $('#bibMergeSelectList option').live('click', onclickSearchResult);
  // Initialize menu positioning (poll for scrolling).
  setInterval(positionMenu, 250);
}

function onclickSearchResult() {
  var rec = $(this).val(); //get recid from option tag
  $('#bibMergeRecInput2').val(rec);
}

function onchangeMethodSelect() {
  option = $("#bibMergeMethodSelect :selected").val();
  switch(option) {
  case "(none)":
    //ajaxGetRecordsFullHtml();
    $("#bibMergeSearchPanel").hide();
    break;
  case "Search":
    $("#bibMergeSearchPanel").show();
    break;
  case "Revisions":
    break;
  }
}
function onclickCompareButton() {
  option = $("#bibMergeMethodSelect :selected").val();
  switch(option) {
  case "(none)":
  case "Search":
    var recid1 = $('#bibMergeRecInput1').attr('value');
    var recid2 = $('#bibMergeRecInput2').attr('value');
    ajaxGetRecordCompare(recid1, recid2);
    //ajaxGetRecordsFullHtml(recid1, recid2);
    break;
  case "Revisions":
    break;
  }
}
function onclickSubmitButton() {
  var _data = {
    requestType: 'submit',
    recID1: gRecID1,
    recID2: gRecID2
  };
  showMessage('LoadingMsg', 'Submitting...');
  ajaxRequest(_data, function(html){ } );
}
function onclickCancelButton() {
  var _data = {
    requestType: 'cancel',
    recID1: gRecID1,
    recID2: gRecID2
  };
  showMessage('LoadingMsg', 'Cancelling...');
  ajaxRequest(_data, function(html){
    window.location.hash = '';
  });
}
function ajaxRequest(data, onSuccessFunc){
  /* Create Ajax request. */
  $.ajax({
    data: { jsondata: JSON.stringify(data) },
    success: function(json){
      if (json['resultCode'] != 0){
        showMessage('ErrorMsg', json['resultText'], 6000);
      }
      else {
        onSuccessFunc(json['resultHtml']);
        showMessage('OKMsg', json['resultText'], 6000);
      }
    }
  });
}
function ajaxGetRecordCompare(_recid1, _recid2) {
  var _data = {
    requestType: 'getRecordCompare',
    recID1: _recid1,
    recID2: _recid2
  };
  showMessage('LoadingMsg', 'Please wait...');
  ajaxRequest(_data, function(html) {
    $('#bibMergeContent').html(html);
    $('#bibMergeRecInput1').val(_recid1);
    $('#bibMergeRecInput2').val(_recid2);
    changeAndSerializeHash({recid1: _recid1, recid2: _recid2});
    gRecID1 = _recid1;
    gRecID2 = _recid2;
    initFieldGroupHeaders(".bibMergeHeaderFieldnum"); //initialize all of them
  });
}

function onclickSearchButton() {
  var _query = $('#bibMergeSearchInput').attr('value');
  var _data = {
    requestType: 'searchCanditates',
    query: _query
  };
  $.ajax({
    data: {
      jsondata: JSON.stringify(_data)
    },
    dataType: 'json',
    success: function(json) {
      if (json['resultsLen'] == 0)
        showMessage('ErrorMsg', "Search: No matches found.", 6000);
      else if (json['resultsLen'] <= json['resultsMaxLen']) {
        $('#bibMergeSelectList').html( json['results'] );
        showMessage('OKMsg', "Search: " + json['resultsLen'] + " results found.", 6000);
      }
      else
        showMessage('ErrorMsg', "Search: Too many results found.", 6000);
    }
  });
  return false; //for the link not to be followed
}

function initAJAX() {
  $.ajaxSetup(
    { cache: false,
      dataType: 'json',
      error: onError,
      type: 'POST'
    }
  );
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
      $('#bibMergePanel').animate({
	'top': 220 - newYscroll}, 'fast');
    // If scroll distance has crossed 200px, fix menu 50px from top.
    else if (positionMenu.yScroll < 200 && newYscroll > 200)
      $('#bibMergePanel').animate({
	'top': 50}, 'fast');
    positionMenu.yScroll = newYscroll;
  }
}
// Last Y-scroll value
positionMenu.yScroll = 0;

function notImplemented() {
  showMessage('ErrorMsg', 'Please ask the developer to hurry up and implement this feature!', 6000);
  return false;
}

function onError(XHR, textStatus, errorThrown) {
  $('#bibMergeContent').html('Request completed with status ' + textStatus
   + '\nResult: ' + XHR.responseText
   + '\nError: ' + errorThrown);
}
function getFieldTag(fieldGroupDiv) {
	return fieldGroupDiv.children(":first-child").children(":first-child").text();
}
