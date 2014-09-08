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

var gRecID1 = null;
var gRecID2 = null;
var gRecord2Mode = 'recid'; //'recid', 'file', 'revision'

var gResultListMode = 'search'; //null, 'search', 'revisions'
var gSearchResults = [[], [], []];
var gSearchResultsIndex = -1;
var gRevisions = [[], []];
var gRevisionsIndex = -1;

var gHash;
var gHASH_CHECK_INTERVAL = 150;
var gHashCheckTimerID;
var gMsgTimeout;

$(document).ready( function(){
  initAJAX();
  initPanel();
  initContent();
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
});

function showMessage(msgType, message, timeToHide) {
  hideMessage();
  clearTimeout(gMsgTimeout);
  $('#bibMergeMessage').removeClass();
  if (msgType == 'LoadingMsg') {
    message = message + '  <img src="/img/loading.gif" />';
    $('#bibMergeMessage').addClass('warning');
  }
  else if (msgType == 'OKMsg') {
    $('#bibMergeMessage').addClass('warninggreen');
  }
  else if (msgType == 'ErrorMsg') {
    $('#bibMergeMessage').addClass('warningred');
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

function isValidRecid1(recid) {
  var recnum = parseInt(recid);
  if (isNaN(recnum) || recnum < 1 || recid.indexOf('.')>0)
    return false;
  return true;
}

function getRecid2Mode(recid) {
  if (isValidRecid1(recid))
    return 'recid';
  else if ( isRevisionID(recid) )
    return 'revision';
  else if (recid=='tmp')
    return 'tmpfile';
  else
    return false;
}

function initStateFromHash() {
  if (window.location.hash == gHash)
    return;
  gHash = window.location.hash;
  if (gHash == '') {
    $('#bibMergeContent').html('Select two records to be compared from the side panel.');
    // Disable "Submit" button
    $('#bibMergeBtnSubmit').attr('disabled','disabled');
    return;
  }
  var parsedHash = deserializeHash(gHash);

  if (parsedHash.recid1 && isValidRecid1(parsedHash.recid1)==true && parsedHash.recid2 && getRecid2Mode(parsedHash.recid2)!=false) {
    ajaxGetRecordCompare(parsedHash.recid1, parsedHash.recid2);
    return;
  }
  // if wrong parameters where given in the url:
  $('#bibMergeContent').html('INVALID URL PARAMETERS');
  $('#bibMergeBtnSubmit').attr('disabled','disabled');
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
      record2Mode: gRecord2Mode,
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
      record2Mode: gRecord2Mode,
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
      record2Mode: gRecord2Mode,
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
      record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
    record2Mode: gRecord2Mode,
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
  $('#bibMergeRecInput1').focus();
  $('#bibMergeMessage').hide();
  onclickSelectSearch();
  $('#bibMergeSelectSearch').click(onclickSelectSearch);
  $('#bibMergeSelectDedupe').click(onclickSelectDedupe);
  $('#bibMergeSelectRevisions').click(onclickSelectRevisions);
  $('#bibMergeGetPrev').click(onclickGetPrev);
  $('#bibMergeGetNext').click(onclickGetNext);
  $('#bibMergeBtnCompare').click(compareRecords);
  $('#bibMergeBtnSubmit').click(onclickSubmitButton);
  $('#bibMergeBtnCancel').click(onclickCancelButton);
  $('#bibMergeBtnSearch').click(onclickSearchButton);
  $('#bibMergeRecCopy').click(onclickRecCopy);
  $('#bibMergeRecMerge').click(onclickRecMerge);
  $('#bibMergeRecMergeNC').click(onclickRecMergeNC);
  $('#bibMergeLinkToBibEdit1').click(onclickLinkToBibEdit1);
  $('#bibMergeLinkToBibEdit2').click(onclickLinkToBibEdit2);
  $('.bibMergeMenuSectionHeader').toggle(menuSectionHeaderClose, menuSectionHeaderOpen);
//  $('#bibMergeMethodSelect').change(onchangeMethodSelect);
  onchangeMethodSelect();
  $('#bibMergeSelectListRow select option').live('click', onclickSearchResult);
  // Initialize menu positioning (poll for scrolling).
  setInterval(positionMenu, 250);
  $('#bibMergeRecInput1').keypress( function(event) {
    if (event.keyCode == 13) //on press 'enter'
      $('#bibMergeRecInput2').focus();
  });
  $('#bibMergeRecInput2').keypress( function(event) {
    if (event.keyCode == 13) //on press 'enter'
      compareRecords();
  });
  $('#bibMergeCompare').on('click', compareRecords);
  $('#bibMergeSearchInput').keypress( function(event) {
    if (event.keyCode == 13) //on press 'enter'
      $('#bibMergeBtnSearch').click();
  });
  $('#bibMergeMenuSectionCandidates div.bibMergeMenuSectionHeader').click();
  $('#bibMergeMenuSectionActions div.bibMergeMenuSectionHeader').click();
}
function menuSectionHeaderOpen() {
  $(this).parents('div.bibMergeMenuSection').find('table').show();
  $(this).find('img').attr('src', "/img/bullet_toggle_minus.png");
}
function menuSectionHeaderClose() {
  $(this).parents('div.bibMergeMenuSection').find('table').hide();
  $(this).find('img').attr('src', "/img/bullet_toggle_plus.png");
}

function onclickRecCopy() {
  var answer = confirm("Do you want to replace all fields of record1 with those of record2?");
  if (!answer)
    return false;

  var _data = {
    requestType: 'recCopy',
    recID1: gRecID1,
    recID2: gRecID2,
    record2Mode: gRecord2Mode
  };
  showMessage('LoadingMsg', 'Copying record2 to record1');
  ajaxRequest(_data, function(html){
    $('#bibMergeContent').html(html);
    initFieldGroupHeaders('.bibMergeHeaderFieldnum'); //initialize all of them
  });
  return false;
}
function onclickRecMerge() {
  var answer = confirm("Do you want to merge fields of record1 and record2 into record1?");
  if (!answer)
    return false;

  var _data = {
    requestType: 'recMerge',
    recID1: gRecID1,
    recID2: gRecID2,
    record2Mode: gRecord2Mode
  };
  showMessage('LoadingMsg', 'Merging record2 with record1');
  ajaxRequest(_data, function(html){
    $('#bibMergeContent').html(html);
    initFieldGroupHeaders('.bibMergeHeaderFieldnum'); //initialize all of them
  });
  return false;
}

function onclickRecMergeNC() {
  var answer = confirm("Do you want to merge non-conflicting fields of record1 and record2 into record1?");
  if (!answer)
    return false;

  var _data = {
    requestType: 'recMergeNC',
    recID1: gRecID1,
    recID2: gRecID2,
    record2Mode: gRecord2Mode
  };
  showMessage('LoadingMsg', 'Merging record2 with record1');
  ajaxRequest(_data, function(html){
    $('#bibMergeContent').html(html);
    initFieldGroupHeaders('.bibMergeHeaderFieldnum'); //initialize all of them
  });
  return false;
}

function buildSelectList(mode) {
  var _list = null;
  var _tmp;
  var _optionsHtml = "";
  if (mode=='forSearch') {
    _list = gSearchResults;
    for (var i=0, n=_list[0].length; i<n; i++)
      _optionsHtml += "<option value=\"" + _list[1][i] + "\" title=\"" + _list[2][i] + "\">"+ _list[1][i] + "</option>\n";
  }
  else {
    _list = gRevisions;
    for (var i=0, n=_list[0].length; i<n; i++)
      _optionsHtml += "<option value=\"" + _list[1][i] + "\">" + _list[1][i] + "</option>\n";
  }
  $('#bibMergeSelectListRow select').html(_optionsHtml);
}

function managePrevNextButtons(action) {
  var _index;
  var _list;
  // take values from the correct global variable
  if (gResultListMode == 'search') {
    _index = gSearchResultsIndex;
    _list = gSearchResults[0];
  }
  else if (gResultListMode == 'revisions') {
    _index = gRevisionsIndex;
    _list = gRevisions[0];
  }
  // perform requested action
  if (action == 'hide') {
    $('#bibMergeGetPrev').hide();
    $('#bibMergeResultIndex').hide();
    $('#bibMergeGetNext').hide();
  }
  else if (action == 'show') {
    var _indexstr = '-';
    if (_index >= 0)
      _indexstr = _index+1;
    $('#bibMergeResultIndex').html( _indexstr+'/'+_list.length);

    $('#bibMergeGetPrev').show();
    $('#bibMergeResultIndex').show();
    $('#bibMergeGetNext').show();
  }
  else if (action == 'next') {
    if (_index+1 < _list.length) {
      _index++;
      $('#bibMergeResultIndex').html( _index+1+'/'+_list.length);
      $('#bibMergeRecInput2').val( _list[_index] );
      $('#bibMergeSelectList option:eq('+ _index +')').attr('selected', 'selected');
      compareRecords();
    }
    else
      showMessage('ErrorMsg', 'Reached the end of list of candidate items', 6000);
  }
  else if (action == 'prev') {
    if (_index-1 >= 0) {
      _index--;
      $('#bibMergeResultIndex').html( _index+1+'/'+_list.length);
      $('#bibMergeRecInput2').val( _list[_index] );
      $('#bibMergeSelectList option:eq('+ _index +')').attr('selected', 'selected');
      compareRecords();
    }
    else
      showMessage('ErrorMsg', 'Reached the end of list of candidate items', 6000);
  }
  //update the correct global variable
  if (gResultListMode == 'search')
    gSearchResultsIndex = _index;
  else if (gResultListMode == 'revisions')
    gRevisionsIndex = _index;
}

function ajaxRequestRevisions() {
  var recid = gRecID1;
  if (recid == null)
    if ($('#bibMergeRecInput1').attr('value') != "")
      recid = $('#bibMergeRecInput1').attr('value');
    else {
      showMessage('ErrorMsg', 'Select a record to get the revisions from', 6000);
      return;
    }

  var _data = {
    requestType: 'searchRevisions',
    recID1: recid
  };
  showMessage('LoadingMsg', 'Retrieving revisions...');
  $.ajax({
    data: { jsondata: JSON.stringify(_data) },
    success: function(json){
      if (json['resultCode'] != 0){
        showMessage('ErrorMsg', json['resultText'], 6000);
      }
      else {
        gRevisions = json['results'];
        gRevisionsIndex = -1;
        buildSelectList('forRevisions');
        managePrevNextButtons('show');
        if (gRevisions.length == 0)
          showMessage('ErrorMsg', 'No revisions found', 6000);
        else
          showMessage('OKMsg', json['resultText'], 6000);
      }
    }
  });
}

function onclickSearchButton() {
  var _query = $('#bibMergeSearchInput').attr('value');
  var _data = {
    requestType: 'searchCandidates',
    query: _query
  };
  $.ajax({
    data: {
      jsondata: JSON.stringify(_data)
    },
    dataType: 'json',
    success: function(json) {
      if (json['resultCode'] != 0){
        showMessage('ErrorMsg', json['resultText'], 6000);
      }
      else {
        gSearchResults = json['results'];
        gSearchResultsIndex = -1;
        buildSelectList('forSearch');
        managePrevNextButtons('show');
        if (gSearchResults.length == 0)
          showMessage('ErrorMsg', 'No results found', 6000);
        else
          showMessage('OKMsg', json['resultText'], 6000);
      }
    }
  });
  return false; //for the link not to be followed
}
function onclickGetPrev() {
  managePrevNextButtons('prev');
  return false;
}
function onclickGetNext() {
  managePrevNextButtons('next');
  return false;
}
function onclickSelectSearch() {
  $('.bibMergeSelectListSelected').removeClass();
  $('#bibMergeSelectSearch').addClass('bibMergeSelectListSelected');
  $('#bibMergeSearchRow').show();
  $('#bibMergeSelectListRow').show();
  buildSelectList('forSearch');
  gResultListMode = 'search';
  managePrevNextButtons('show');
  return false;
}
function onclickSelectDedupe() {
  onclickSelectClose();
  notImplemented();
  return false;
}
function onclickSelectRevisions() {
  $('.bibMergeSelectListSelected').removeClass();
  $('#bibMergeSelectRevisions').addClass('bibMergeSelectListSelected');
  $('#bibMergeSearchRow').hide();
  $('#bibMergeSelectListRow').show();
  //if list is empty or first result doesn't start with recid1
  if (gRevisions.length==0 || gRevisions[0].indexOf(gRecID1+'.')==-1) {
    ajaxRequestRevisions();
  }
  buildSelectList('forRevisions');
  gResultListMode = 'revisions';
  managePrevNextButtons('show');
  return false;
}
function onclickSelectClose() {
  $('.bibMergeSelectListSelected').removeClass();
  $('#bibMergeSearchRow').hide();
  $('#bibMergeSelectListRow').hide();
  gResultListMode = null;
  managePrevNextButtons('hide');
  return false;
}

function onclickSearchResult() {
  //find index of selected option
  var _index = 0;
  var currOpt = $(this).prev('option');
  while(currOpt.html()!=null) {
    _index++;
    currOpt = currOpt.prev('option');
  }
  //set the value of record2 input field
  if (gResultListMode == 'search') {
    $('#bibMergeRecInput2').val( gSearchResults[0][_index] );
    gSearchResultsIndex = _index;
  }
  else if (gResultListMode == 'revisions') {
    $('#bibMergeRecInput2').val( gRevisions[0][_index] );
    gRevisionsIndex = _index;
  }
  managePrevNextButtons('show');
  compareRecords();
}

function onchangeMethodSelect() {
  option = $("#bibMergeMethodSelect :selected").val();
  switch(option) {
  case "(none)":
    $("#bibMergeSearchPanel").hide();
    break;
  case "Search":
    $("#bibMergeSearchPanel").show();
    break;
  case "Revisions":
    break;
  }
}
function compareRecords() {
  var recid1 = $('#bibMergeRecInput1').attr('value');
  var recid2 = $('#bibMergeRecInput2').attr('value');
  if (recid2 == "")
    recid2 = 'none';
  ajaxGetRecordCompare(recid1, recid2);
}
function ajaxGetRecordCompare(_recid1, _recid2) {
  // validity check
  if (!isValidRecid1(_recid1)) {
    showMessage('ErrorMsg', 'Invalid record1', 6000);
    return;
  }
  var _mode = getRecid2Mode(_recid2);
  if (_mode == false) {
    showMessage('ErrorMsg', 'Invalid record2', 6000);
    return;
  }
  //ajax request
  var _data = {
    requestType: 'getRecordCompare',
    recID1: _recid1,
    recID2: _recid2,
    record2Mode: _mode
  };
  showMessage('LoadingMsg', 'Please wait...');
  panelDisabled(true);
  ajaxRequest(_data, function(html) {
    $('#bibMergeContent').html(html);
    $('#bibMergeRecInput1').val(_recid1);
    $('#bibMergeRecInput2').val(_recid2);
    changeAndSerializeHash({recid1: _recid1, recid2: _recid2});
    gRecID1 = _recid1;
    gRecID2 = _recid2;
    gRecord2Mode = _mode;
    initFieldGroupHeaders('.bibMergeHeaderFieldnum'); //initialize all of them
    panelDisabled(false);
  });
}
function isRevisionID(str) {
  if (str.indexOf('.') > -1) {
    var _array = str.split('.');
    if (_array.length==2 && !isNaN(_array[0]) && !isNaN(_array[1]) && _array[1].length==14)
      return true;
  }
  return false;
}
function onclickSubmitButton(confirm_p, additional_data) {
  /*
   confirm_p: if false, do not ask user confirmation before submitting
   additional_data: additional data sent to server
   */
  if (typeof(confirm) == 'undefined') {
      confirm_p = true
  }
  var checkbox = $('#bibMergeDupeCheckbox').is(':checked');
  var submit_p = false;

  if (!confirm_p) {
      submit_p = true;
  } else {
      submit_p = displayAlert('confirmSubmit');
  }
  if (submit_p){
      var _data = {
        requestType: 'submit',
        record2Mode: gRecord2Mode,
        recID1: gRecID1,
        recID2: gRecID2
      };
      if (checkbox == true)
        _data['duplicate'] = gRecID2;
      _data['additional_data'] = additional_data;
      showMessage('LoadingMsg', 'Submitting...');
      ajaxRequest(_data, function(html){
        window.location.hash = '';
      });
      if (checkbox == true)
          $('#bibMergeDupeCheckbox').attr('checked', false);
  }
}
function onclickCancelButton() {
  if (displayAlert('confirmCancel')){
    var _data = {
        requestType: 'cancel',
        recID1: gRecID1
    };
    showMessage('LoadingMsg', 'Cancelling...');
    ajaxRequest(_data, function(html){
    window.location.hash = '';
    });
  }
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
  panelDisabled(false);
  $('#bibMergeContent').html('Request completed with status ' + textStatus
   + '\nResult: ' + XHR.responseText
   + '\nError: ' + errorThrown);
}
function getFieldTag(fieldGroupDiv) {
  return fieldGroupDiv.children(":first-child").children(":first-child").text();
}

function onclickLinkToBibEdit1() {
  if (gHash!='' && gRecID1!=null)
    window.location = '/'+ gSITE_RECORD +'/edit/#state=edit&recid='+gRecID1;
  else
    showMessage('ErrorMsg', 'A valid record id must be selected', 6000);
  return false;
}
function onclickLinkToBibEdit2() {
  if (gHash!='' && gRecord2Mode=='recid' && gRecID2!=null)
    window.location = '/'+ gSITE_RECORD +'/edit/#state=edit&recid='+gRecID2;
  else
    showMessage('ErrorMsg', 'A valid record id must be selected', 6000);
  return false;
}

function panelDisabled(disabled) {
  if (disabled == true)
    // Disable all elements except "Compare" button
    $('#bibMergePanel').find('button, optgroup, option, select, textarea').not('#bibMergeCompare').attr('disabled', true);
  else
    $('#bibMergePanel').find('button, optgroup, option, select, textarea').not('#bibMergeCompare').removeAttr('disabled');
}

function displayAlert(msgType) {
   /*
    * Display confirmation pop-up.
    * Could be extended for all kind of alerts
    */
   var msg;
   var popUpType = 'confirm';
   switch(msgType) {
        case 'confirmSubmit':
            msg = 'Submit your changes to this record?\n\n';
            popUpType = 'confirm';
            break;
        case 'confirmCancel':
            msg = 'Discard your changes?\n\n';
            popUpType = 'confirm';
            break;
   }
   if (popUpType == 'confirm')
       return confirm(msg);
}
