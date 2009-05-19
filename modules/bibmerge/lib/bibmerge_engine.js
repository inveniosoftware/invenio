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
  $('.bibMergeFieldGroupRefresh').live('click', onclickFieldGroupRefresh);
  $('.bibMergeFieldGroupDiff').live('click', onclickFieldGroupRefresh);
  $('.bibMergeFieldGroupMerge').live('click', onclickFieldGroupMerge)
  $('.bibMergeFieldGroupMergeNC').live('click', onclickFieldGroupMerge)
  $('.bibMergeFieldReplace').live('click', onclickFieldReplace);
  $('.bibMergeFieldAdd').live('click', onclickFieldAdd);
  $('.bibMergeFieldDelete').live('click', onclickFieldDelete);
  $('.bibMergeFieldMerge').live('click', onclickFieldMerge);
  $('#bibMergeContent a:not([class])').live('click', notImplemented);
}
function onclickFieldMerge() {
  var fieldGroupDiv = $(this).parents('.bibMergeFieldGroupDiv');
  var ftag = getFieldTag(fieldGroupDiv);
  var fieldID1 = $(this).parents('tr').next().children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').next().children('td').eq(3).attr('id');
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
  var fieldID1 = $(this).parents('tr').next().children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').next().children('td').eq(3).attr('id');
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
  var fieldID1 = $(this).parents('tr').next().children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').next().children('td').eq(3).attr('id');
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
  var fieldID1 = $(this).parents('tr').next().children('td').eq(1).attr('id');
  var fieldID2 = $(this).parents('tr').next().children('td').eq(3).attr('id');
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