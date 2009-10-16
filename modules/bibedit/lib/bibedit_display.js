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
 * This is the BibEdit Javascript for generation of webpage elements and HTML.
 */

function displayRecord(){
  /*
   * Create the main content table.
   */
  var table = '' +
    '<table id="bibEditTable">' +
      '<col span="1" class="bibEditColFieldBox"/>' +
      '<col span="1" id="bibEditColFieldTag"/>' +
      '<col span="1" class="bibEditColFieldBox" />' +
      '<col span="1" id="bibEditColSubfieldTag" />' +
      '<col span="1" />' +
      '<col span="1" id="bibEditColSubfieldAdd" />' +
      // Create a dummy row to hack layout in like FF..
      '<tbody style="border: 0px;">' +
	'<tr>' +
	  '<td style="padding: 0px; max-width: 14px;"></td>' +
	  '<td style="padding: 0px; max-width: 100px;"></td>' +
	  '<td style="padding: 0px; max-width: 14px;"></td>' +
	  '<td style="padding: 0px; max-width: 80px;"></td>' +
	  '<td style="padding: 0px"></td>' +
	  '<td style="padding: 0px; max-width: 16px;"></td>' +
	'</tr>' +
      '</tbody>';
  var tags = getTagsSorted(), tag, fields;
  // For each controlfield, create row.
  for (var i=0, n=tags.length; i<n; i++){
    tag = tags[i];
    // If not controlfield, move on.
    if (!validMARC.reControlTag.test(tag))
      break;
    fields = gRecord[tag];
    for (var j=0, m=fields.length; j<m; j++)
      table += createControlField(tag, fields[j], j);
  }
  // For each instance of each field, create row(s).
  for (n=tags.length; i<n; i++){
    tag = tags[i];
    fields = gRecord[tag];
    for (var j=0, m=fields.length; j<m; j++){
      table += createField(tag, fields[j], j);
    }
  }
  // Close and display table.
  table += '</table>';
  $('#bibEditContent').append(table);
  colorFields();
}

function createControlField(tag, field, fieldPosition){
  /*
   * Create control field row.
   */
  var fieldID = tag + '_' + fieldPosition;
  var cellContentClass = 'class="bibEditCellContentProtected" ';
  if (!fieldIsProtected(tag))
    cellContentClass = '';

  return '' +
    '<tbody id="rowGroup_' + fieldID + '">' +
      '<tr id="row_' + fieldID + '" >' +
        '<td class="bibEditCellField">' +
	  input('checkbox', 'boxField_' + fieldID, 'bibEditBoxField',
	    {onclick: 'onFieldBoxClick(this)', tabindex: -1}) +
	'</td>' +
        '<td id="fieldTag_' + fieldID + '" class="bibEditCellFieldTag">' +
	  getFieldTag(tag) +
	'</td>' +
	'<td></td>' +
	'<td></td>' +
	'<td id="content_' + fieldID + '" ' + cellContentClass +
	  'colspan="2" tabindex="0">' + escapeHTML(field[3]) +
	'</td>' +
      '</tr>' +
    '</tbody>';
}

function createField(tag, field, fieldPosition){
  /*
   * Create field row(s).
   */
  var subfields = field[0], ind1 = field[1], ind2 = field[2];
  var fieldID = tag + '_' + fieldPosition;
  ind1 = (ind1 != ' ' && ind1 != '') ? ind1 : '_';
  ind2 = (ind2 != ' ' && ind2 != '') ? ind2 : '_';
  var protectedField = fieldIsProtected(tag + ind1 + ind2);
  var subfieldsLength = subfields.length;
  var result = '<tbody ' + 'id="rowGroup_' + fieldID + '">';
  for (var i=0, n=subfields.length; i<n; i++){
    var subfield = subfields[i];
    result += createRow(tag, ind1, ind2, subfield[0], escapeHTML(subfield[1]),
			fieldID, i, subfieldsLength, protectedField);
  }
  return result + '</tbody>';
}

function createRow(tag, ind1, ind2, subfieldCode, subfieldValue, fieldID,
		   subfieldIndex, subfieldsLength, protectedField){
  /*
   * Create single row (not controlfield).
   */
  var MARC = tag + ind1 + ind2 + subfieldCode;
  var protectedSubfield = (protectedField) ? true : fieldIsProtected(MARC);
  var subfieldID = fieldID + '_' + subfieldIndex;
  var boxField = '', cellFieldTagAttrs = 'class="bibEditCellField"',
    fieldTagToPrint = '',
  cellContentClass = 'bibEditCellContentProtected',
  cellContentTitle='',
  cellContentOnClick = '';
  if (!protectedField){
    // Enable features for unprotected fields.
    if (!protectedSubfield){
      cellContentClass = 'bibEditCellContent';
      cellContentTitle = 'title="Click to edit" ';
      cellContentOnClick = 'onclick="onContentClick(this)" ';
    }
  }
  cellContentAdditionalClass = "";
  if (subfieldValue.substring(0,9) == "VOLATILE:"){
    subfieldValue = subfieldValue.substring(9);
    cellContentAdditionalClass += " bibEditVolatileSubfield";
  }
  var boxSubfield = input('checkbox', 'boxSubfield_' + subfieldID,
    'bibEditBoxSubfield', {onclick: 'onSubfieldBoxClick(this)', tabindex: -1});
  var subfieldTagToPrint = getSubfieldTag(MARC);
  var btnAddSubfield = '';
  // If first subfield, add tag and selection box, remove up arrow.
  if (subfieldIndex == 0){
    boxField = input('checkbox', 'boxField_' + fieldID, 'bibEditBoxField',
      {onclick: 'onFieldBoxClick(this)', tabindex: -1});
    cellFieldTagAttrs = 'id="fieldTag_' + fieldID +
      '" class="bibEditCellFieldTag"';
    fieldTagToPrint = getFieldTag(MARC);
  }
  // If last subfield, remove down arrow, add 'Add subfield' button.
  if (subfieldIndex == subfieldsLength - 1){
    if (!protectedField)
      btnAddSubfield = img('/img/add.png', 'btnAddSubfield_' + fieldID, '',
      {title: 'Add subfield', onclick: 'onAddSubfieldsClick(this)'});
  }
  return '' +
    '<tr id="row_' + subfieldID + '">' +
      '<td class="bibEditCellField">' + boxField + '</td>' +
      '<td ' + cellFieldTagAttrs  + '>' + fieldTagToPrint + '</td>' +
      '<td class="bibEditCellSubfield">' + boxSubfield + '</td>' +
      '<td id="subfieldTag_' + subfieldID +
	'" class="bibEditCellSubfieldTag">' +
	subfieldTagToPrint +
      '</td>' +
      '<td id="content_' + subfieldID + '" class="' + cellContentClass + cellContentAdditionalClass+ '" ' +
	cellContentTitle + cellContentOnClick + 'tabindex="0">' +
	subfieldValue +
      '</td>' +
      '<td class="bibEditCellAddSubfields">' + btnAddSubfield + '</td>' +
    '</tr>';
}

function redrawFields(tag){
  /*
   * Redraw all fields for a given tag.
   */
  var rowGroup = $('#rowGroup_' + tag + '_0'), prevRowGroup;
  if (rowGroup.length){
    // Remove the fields from view.
    prevRowGroup = rowGroup.prev();
    prevRowGroup.nextAll('[id^=rowGroup_' + tag + ']').remove();
  }
  else{
    // New tag. Determine previous sibling.
    var prevTag = getPreviousTag(tag);
    prevRowGroup = $('#rowGroup_' + prevTag + '_0');
  }

  // Redraw all fields and append to table.
  if (gRecord[tag]){
    var fields = gRecord[tag];
    var result = '', i, n;
    if (validMARC.reControlTag.test(tag)){
      for (i=0, n=fields.length; i<n; i++)
        result += createControlField(tag, fields[i], i);
    }
    else{
      for (i=0, n=fields.length; i<n; i++)
        result += createField(tag, fields[i], i);
    }
    prevRowGroup.after(result);
  }
}

function createAddFieldForm(fieldTmpNo){
  /*
   * Create an 'Add field' form.
   */
  return '' +
    '<tbody id="rowGroupAddField_' + fieldTmpNo + '">' +
      '<tr>' +
	'<td></td>' +
	'<td><b>New</b></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td>' +
	  'Controlfield ' + input('checkbox', 'chkAddFieldControlfield_' +
				 fieldTmpNo) +
        '</td>' +
	'<td>' +
	  img('/img/add.png', 'btnAddFieldAddSubfield_' + fieldTmpNo, '', {
	    title: 'Add subfield'}) +
	'</td>' +
      '</tr>' +
      createAddFieldRow(fieldTmpNo, 0) +
      '<tr>' +
	'<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td>' +
	  button('Save', 'btnAddFieldSave_' + fieldTmpNo, 'bibEditBtnBold') +
	  button('Cancel', 'btnAddFieldCancel_' + fieldTmpNo, '') +
	  button('Clear', 'btnAddFieldClear_' + fieldTmpNo, 'bibEditBtnClear') +
	'</td>' +
	'<td></td>' +
      '</tr>' +
    '</tbody>';
}

function createAddFieldRow(fieldTmpNo, subfieldTmpNo){
  /*
   * Create a row in the 'Add field' form.
   */
  var txtAddFieldTag = '', txtAddFieldInd1 = '', txtAddFieldInd2 = '',
    btnAddFieldRemove = '';
  if (subfieldTmpNo == 0){
    txtAddFieldTag = input('text', 'txtAddFieldTag_' + fieldTmpNo,
				    'bibEditTxtTag', {maxlength: 3});
    txtAddFieldInd1 = input('text', 'txtAddFieldInd1_' + fieldTmpNo,
			    'bibEditTxtInd', {maxlength: 1});
    txtAddFieldInd2 = input('text', 'txtAddFieldInd2_' + fieldTmpNo,
			    'bibEditTxtInd', {maxlength: 1});
  }
  else
    btnAddFieldRemove = img('/img/delete.png', 'btnAddFieldRemove_' +
      fieldTmpNo + '_' + subfieldTmpNo, '', {title: 'Remove subfield'});
  return '' +
    '<tr id="rowAddField_' + fieldTmpNo + '_' + subfieldTmpNo + '">' +
      '<td></td>' +
      '<td>' +
	txtAddFieldTag + txtAddFieldInd1 + txtAddFieldInd2 +
      '</td>' +
      '<td></td>' +
      '<td class="bibEditCellAddSubfieldCode">' +
	input('text', 'txtAddFieldSubfieldCode_' + fieldTmpNo + '_' +
	  subfieldTmpNo, 'bibEditTxtSubfieldCode', {maxlength: 1}) +
      '</td>' +
      '<td>' +
	input('text', 'txtAddFieldValue_' + fieldTmpNo + '_' +
		  subfieldTmpNo, 'bibEditTxtValue') +
      '</td>' +
      '<td>' + btnAddFieldRemove + '</td>' +
    '</tr>';
}

function createAddSubfieldsForm(fieldID){
  /*
   * Create an 'Add subfields' form.
   */
  return '' +
    createAddSubfieldsRow(fieldID, 0) +
    '<tr id="rowAddSubfieldsControls_' + fieldID + '">' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td>' +
	button('Save', 'btnAddSubfieldsSave_' + fieldID, 'bibEditBtnBold') +
	button('Cancel', 'btnAddSubfieldsCancel_' + fieldID, '') +
	button('Clear', 'btnAddSubfieldsClear_' + fieldID, 'bibEditBtnClear') +
      '</td>' +
      '<td></td>' +
    '</tr>';
}

function createAddSubfieldsRow(fieldID, subfieldTmpNo){
  /*
   * Create a row in the 'Add subfields' form.
   */
  var subfieldID = fieldID + '_' + subfieldTmpNo;
  var btnRemove = (subfieldTmpNo == 0) ? '' : img('/img/delete.png',
    'btnAddSubfieldsRemove_' + subfieldID, '', {title: 'Remove subfield'});
  return '' +
    '<tr id="rowAddSubfields_' + subfieldID + '">' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td class="bibEditCellAddSubfieldCode">' +
	input('text', 'txtAddSubfieldsCode_' + subfieldID,
	      'bibEditTxtSubfieldCode', {maxlength: 1}) +
      '</td>' +
      '<td>' +
	input('text', 'txtAddSubfieldsValue_' + subfieldID, 'bibEditTxtValue') +
      '</td>' +
      '<td>' + btnRemove + '</td>' +
    '</tr>';
}

function displayMessage(msgCode, keepContent, args){
  /*
   * Display message in the main work area. Messages codes returned from the
   * server (positive integers) are as specified in the BibEdit configuration.
   */
  var msg;
  switch (msgCode){
    case -1:
      msg = 'Search term did not match any records.';
      break;
    case 0:
      msg = 'A server error has occured. Please contact your system ' +
	'administrator.<br />' +
	'Error code: <b>' + msgCode + '</b>';
      break;
    case 4:
      msg = 'Your modifications have now been submitted. ' +
	'They will be processed as soon as the task queue is empty.';
      break;
    case 6:
      msg = 'The record will be deleted as soon as the task queue is empty.';
      break;
    case 101:
      msg = 'Could not access record. Permission denied.';
      break;
    case 102:
      msg = 'This record does not exist. Please try another record ID.';
      break;
    case 103:
      msg = 'Cannot edit deleted record.';
      break;
    case 104:
      msg = 'This record is currently being edited by another user. Please ' +
	'try again later.';
      break;
    case 105:
      msg = 'This record cannot be safely edited at the moment. Please ' +
	'try again in a few minutes.';
      break;
    case 106:
      msg = 'A server error has occured. You may have lost your changes to ' +
	'this record.<br />' +
	'Error code: <b>' + msgCode + '</b> (missing cache file)';
      break;
    case 107:
      msg = 'It appears that you have opened this record in another editor, ' +
	'perhaps in a different window or on a different computer. A record ' +
	'can only be edited in one place at the time.<br />' +
	'Do you want to ' +
	'<b><a href="#"id="lnkGetRecord">reopen the record</a></b> here?';
	break;
    case 108:
      msg = 'Could not find record template file. Please notify your system ' +
	'administrator.';
      break;
    case 109:
      msg = 'The record template file is invalid. Please notify your system ' +
	'administrator';
      break;
    case 110:
      msg = 'The record contains invalid content. Remove the invalid content ' +
	'and resubmit the record.<br />' +
	'Errors: <b>' + args[0] + '</b><br /><br />';
      break;
    default:
      msg = 'Result code: <b>' + msgCode + '</b>';
  }
  if (!keepContent)
    $('#bibEditContent').html('<div id="bibEditMessage">' + msg + '</div>');
  else
    $('#bibEditContent').prepend('<div id="bibEditMessage">' + msg + '</div>');
}

function displayNewRecordScreen(){
  /*
   * Display options for creating a new record: An empty record or a template
   * selected from a list of templates.
   */
  var msg = '<ul><li style="padding-bottom: 20px;">' +
    '<a href="#" id="lnkNewEmptyRecord"><b>Empty record</b></a></li>' +
    '<li style="padding-bottom: 10px;">Use record template:' +
    '<table>';
  var templatesCount = gRECORD_TEMPLATES.length;
  if (!templatesCount)
    msg += '<tr><td style="padding-left: 10px;">No record templates found' +
      '</td></tr>';
  else{
    for (var i=0, n=templatesCount; i<n; i++)
      msg += '<tr style="border-width: 1px;">' +
	'<td style="padding-left: 10px; padding-right: 10px;">' +
	'<a href="#" id="lnkNewTemplateRecord_' + i + '"><b>' +
	gRECORD_TEMPLATES[i][1] + '</b></a></td>' +
	'<td style="padding-left: 10px; padding-right: 10px;">' +
	'<td>' + gRECORD_TEMPLATES[i][2] + '</td></tr>';
  }
  msg += '</table></li>';
  $('#bibEditContent').html(msg);
}

function displayCacheOutdatedScreen(requestType){
  /*
   * Display options to resolve the outdated cache scenario (DB record updated
   * during editing). Options differ depending on wether the situation was
   * discovered when fetching or when submitting the record.
   */
  $('#bibEditMessage').remove();
  var recordURL = gSITE_URL + '/record/' + gRecID + '/';
  var viewMARCURL = recordURL + '?of=hm';
  var viewMARCXMLURL = recordURL + '?of=xm';
  var msg = '';
  if (requestType == 'submit')
    msg = 'Someone has changed this record while you were editing. ' +
      'You can:<br /><ul>' +
      '<li>View (<b><a href="' + recordURL + '" target="_blank">HTML</a></b>,' +
      ' <b><a href="' + viewMARCURL + '" target="_blank">MARC</a></b>,' +
      ' <b><a href="' + viewMARCXMLURL + '" target="_blank">MARCXML</a></b>' +
    ') the latest version</li>' +
    '<li><a href="#" id="lnkMergeCache"><b>Merge</b></a> your changes ' +
    'with the latest version by using the merge interface</li>' +
    '<li><a href="#" id="lnkForceSubmit"><b>Force your changes</b></a> ' +
    '(<b>Warning: </b>overwrites the latest version)</li>' +
    '<li><a href="#" id="lnkDiscardChanges><b>Discard your changes</b></a> ' +
    '(keep the latest version)</li>' +
    '</ul>';
  else if (requestType == 'getRecord')
    msg = 'You have unsubmitted changes to this record, but someone has ' +
      'changed the record while you were editing. You can:<br /><ul>' +
      '<li>View (<b><a href="' + recordURL + '" target="_blank">HTML</a></b>,' +
      ' <b><a href="' + viewMARCURL + '" target="_blank">MARC</a></b>,' +
      ' <b><a href="' + viewMARCXMLURL + '" target="_blank">MARCXML</a></b>' +
      ') the latest version</li>' +
      '<li><a href="#" id="lnkMergeCache"><b>Merge</b></a> your changes ' +
      'with the latest version by using the merge interface</li>' +
      '<li><a href="#" id="lnkDiscardChanges"><b>Get the latest version' +
      '</b></a> (<b>Warning: </b>discards your changes)</li>' +
      '<li>Keep editing. When submitting you will be offered to overwrite ' +
      'the latest version. Click <a href="#" id="lnkRemoveMsg">here' +
      '</a> to remove this message.</li>' +
      '</ul>';
  $('#bibEditContent').prepend('<div id="bibEditMessage">' + msg + '</div>');
}

function displayAlert(msgType, args){
  /*
   * Display pop-up of type alert or confirm.
   * args can be an array with additional arguments.
   */
  var msg;
  var popUpType = 'alert';
  switch (msgType){
    case 'confirmClone':
      msg = 'Clone this record?\n\n';
      popUpType = 'confirm';
      break;
    case 'confirmSubmit':
      msg = 'Submit your changes to this record?\n\n';
      popUpType = 'confirm';
      break;
    case 'confirmCancel':
      msg = 'You have unsubmitted changes to this record.\n\n' +
	'Discard your changes?';
      popUpType = 'confirm';
      break;
    case 'confirmDeleteRecord':
      msg = 'Really delete this record?\n\n';
      popUpType = 'confirm';
      break;
    case 'confirmInvalidOrEmptyInput':
      msg =  'WARNING: Some subfields contain invalid MARC or are empty. \n' +
	'Click Cancel to go back and correct. \n' +
	'Click OK to ignore and continue (only valid subfields will be saved).';
      popUpType = 'confirm';
      break;
    case 'confirmLeavingChangedRecord':
      msg = '******************** WARNING ********************\n' +
	'                  You have unsubmitted changes.\n\n' +
	'You should go back to the record and click either:\n' +
	' * Submit (to save your changes permanently)\n      or\n' +
	' * Cancel (to discard your changes)\n\n' +
	'Press OK to continue, or Cancel to stay on the current record.';
      popUpType = 'confirm';
      break;
    case 'alertCriticalInput':
      msg = 'ERROR: Your input had critical errors. Please go back and ' +
	'correct any fields with invalid MARC (red border) or fields that ' +
	'should not be empty.';
      break;
    case 'alertAddProtectedField':
      msg = 'ERROR: Cannot add protected field ' + args[0] + '.';
      break;
    case 'alertAddProtectedSubfield':
      msg = 'ERROR: Cannot add protected subfield ' + args[0] + '.';
      break;
    case 'alertDeleteProtectedField':
      msg = 'ERROR: Cannot delete protected field ' + args[0] + '.';
      break;
    default:
      msg = msgType;
  }
  if (popUpType == 'confirm')
    return confirm(msg);
  else
    alert(msg);
}

function notImplemented(event){
  /*
   * Handle unimplemented function.
   */
  alert('Sorry, this function is not implemented yet!');
  event.preventDefault();
}

function button(value, id, _class, attrs){
  /*
   * Create a button tag with specified attributes.
   */
  value = (value != undefined) ? value : '';
  id = id ? 'id="' + id + '" ' : '';
  _class = _class ? 'class="' + _class + '" ' : '';
  var strAttrs = '';
  for (var attr in attrs){
    strAttrs += attr + '="' + attrs[attr] + '" ';
  }
  return '<button ' + id + _class + strAttrs + '>' + value + '</button>';
}

function img(src, id, _class, attrs){
  /*
   * Create an image tag with specified attributes.
   */
  src = 'src="' + src + '" ';
  id = id ? 'id="' + id + '" ' : '';
  _class =  _class ? 'class="' + _class + '" ' : '';
  var strAttrs = '';
  for (var attr in attrs){
    strAttrs += attr + '="' + attrs[attr] + '" ';
  }
  return '<img ' + src + id + _class + strAttrs + '/>';
}

function input(type, id, _class, attrs){
  /*
   * Create an input tag with specified attributes.
   */
  type = 'type="' + type + '" ';
  id = id ? 'id="' + id + '" ' : '';
  _class = _class ? 'class="' + _class + '" ' : '';
  var strAttrs = '';
  for (var attr in attrs){
    strAttrs += attr + '="' + attrs[attr] + '" ';
  }
  return '<input ' + type + id + _class + strAttrs + '/>';
}

function escapeHTML(value){
  /*
   * Replace special characters '&', '<' and '>' with HTML-safe sequences.
   * This functions is called on content before displaying it.
   */
  value = value.replace(/&/g, '&amp;'); // Must be done first!
  value = value.replace(/</g, '&lt;');
  value = value.replace(/>/g, '&gt;');
  return value;
}
