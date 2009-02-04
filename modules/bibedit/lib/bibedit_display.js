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
      '<col span="1" id="bibEditColSubfieldArrows" />' +
      '<col span="1" class="bibEditColFieldBox" />' +
      '<col span="1" id="bibEditColSubfieldTag" />' +
      '<col span="1" />' +
      '<col span="1" id="bibEditColSubfieldAdd" />' +
      // Create a dummy row to hack layout in like FF..
      '<tbody style="border: 0px;">' +
	'<tr>' +
	  '<td style="padding: 0px; max-width: 14px;"></td>' +
	  '<td style="padding: 0px; max-width: 100px;"></td>' +
	  '<td style="padding: 0px; max-width: 38px;"></td>' +
	  '<td style="padding: 0px; max-width: 14px;"></td>' +
	  '<td style="padding: 0px; max-width: 80px;"></td>' +
	  '<td style="padding: 0px"></td>' +
	  '<td style="padding: 0px; max-width: 16px;"></td>' +
	'</tr>' +
      '</tbody>';
  var tags = getTagsSorted();
  var tag, fields, field;
  // For each controlfield, create row.
  for (var i=0, n=tags.length; i<n; i++){
    tag = tags[i];
    // If not controlfield, move on.
    if (tag > 9)
      break;
    fields = gRecord[tag];
    for (var j=0, m=fields.length; j<m; j++)
      table += createControlField(tag, fields[j]);
  }
  // For each instance of each field, create row(s).
  for (n=tags.length; i<n; i++){
    tag = tags[i];
    fields = gRecord[tag];
    for (var j=0, m=fields.length; j<m; j++){
      table += createField(tag, fields[j]);
    }
  }
  // Close and display table.
  table += '</table>';
  $('#bibEditContent').append(table);
  colorFields();
}

function createControlField(tag, field){
  /*
   * Create control field row.
   */
  var fieldID = tag + '_' + field[4];
  var cellContentClass = ' class="bibEditCellContentProtected"',
    evtContentClick = '';

  if (!fieldIsProtected(tag)){
    cellContentClass = '';
    evtContentClick = 'ondblclick="onContentClick(this)" ';
  }

  return '' +
    '<tbody id="rowGroup_' + fieldID + '">' +
      '<tr id="row_' + fieldID + '" >' +
        '<td class="bibEditCellField">' +
	  input('checkbox', 'boxField_' + fieldID, 'bibEditBoxField', '',
			 'onclick', 'onFieldBoxClick(this)') +
	'</td>' +
        '<td id="fieldTag_' + fieldID + '" class="bibEditCellFieldTag">' +
	  getFieldTag(tag) +
	'</td>' +
        '<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td ' + evtContentClick + 'id="content_' + fieldID + '" colspan="2"' +
	  cellContentClass + '>' +
	  escapeHTML(field[3]) +
	'</td>' +
      '</tr>' +
    '</tbody>';
}

function createField(tag, field){
  /*
   * Create field row(s).
   */
  var subfields = field[0], ind1 = field[1], ind2 = field[2],
    fieldNumber = field[4];
  var fieldID = tag + '_' + fieldNumber;
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
    fieldTagToPrint = '', btnMoveSubfieldUp = '', btnMoveSubfieldDown = '',
    cellContentClass = ' class="bibEditCellContentProtected"',
    evtContentClick = '';
  if (!protectedField){
    // Enable features for unprotected fields.
    btnMoveSubfieldUp = img('/img/arrow_up2.png', 'Move subfield up',
      'btnMoveSubfieldUp_' + subfieldID, 'bibEditBtnMoveSubfieldUp', 'onclick',
      'onMoveSubfieldClick(this)');
    btnMoveSubfieldDown = img('/img/arrow_down2.png', 'Move subfield down',
      'btnMoveSubfieldDown_' + subfieldID, 'bibEditBtnMoveSubfieldDown',
      'onclick', 'onMoveSubfieldClick(this)');
    if (!protectedSubfield){
      cellContentClass = '';
      evtContentClick = 'ondblclick="onContentClick(this)" ';
    }
  }
  var boxSubfield = input('checkbox', 'boxSubfield_' + subfieldID,
    'bibEditBoxSubfield', '', 'onclick', 'onSubfieldBoxClick(this)');
  var subfieldTagToPrint = getSubfieldTag(MARC);
  var btnAddSubfield = '';
  // If first subfield, add tag and selection box, remove up arrow.
  if (subfieldIndex == 0){
    boxField = input('checkbox', 'boxField_' + fieldID, 'bibEditBoxField', '',
		     'onclick', 'onFieldBoxClick(this)');
    cellFieldTagAttrs = 'id="fieldTag_' + fieldID +
      '" class="bibEditCellFieldTag"';
    fieldTagToPrint = getFieldTag(MARC);
    btnMoveSubfieldUp = '';
  }
  // If last subfield, remove down arrow, add 'Add subfield' button.
  if (subfieldIndex == subfieldsLength - 1){
    btnMoveSubfieldDown = '';
    if (!protectedField)
      btnAddSubfield = img('/img/add.png', 'Add subfield', 'btnAddSubfield_' +
			   fieldID, '', 'onclick', 'onAddSubfieldsClick(this)');
  }
  return '' +
    '<tr id="row_' + subfieldID + '">' +
      '<td class="bibEditCellField">' + boxField + '</td>' +
      '<td ' + cellFieldTagAttrs  + '>' + fieldTagToPrint + '</td>' +
      '<td class="bibEditCellSubfield">' +
	btnMoveSubfieldUp + btnMoveSubfieldDown +
      '</td>' +
      '<td class="bibEditCellSubfield">' + boxSubfield + '</td>' +
      '<td id="subfieldTag_' + subfieldID +
	'" class="bibEditCellSubfieldTag">' +
	subfieldTagToPrint +
      '</td>' +
      '<td ' + evtContentClick + 'id="content_' + subfieldID + '"' +
	cellContentClass + '>' +
	subfieldValue +
      '</td>' +
      '<td class="bibEditCellAddSubfields">' + btnAddSubfield + '</td>' +
    '</tr>';
}

function createAddFieldRowGroup(fieldTmpNo){
  /*
   * Create an 'Add field' rowgroup.
   */
  return '' +
    '<tbody id="rowGroupAddField_' + fieldTmpNo + '">' +
      '<tr>' +
	'<td></td>' +
	'<td><b>New</b></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td>' +
	  'Controlfield ' + input('checkbox', 'chkAddFieldControlfield_' +
				 fieldTmpNo) +
        '</td>' +
	'<td>' +
	  img('/img/add.png', 'Add subfield', 'btnAddFieldAddSubfield_' +
	      fieldTmpNo) +
	'</td>' +
      '</tr>' +
    createAddFieldRow(fieldTmpNo, 0) +
      '<tr>' +
	'<td>' +
	  input('hidden', 'hdnAddFieldFreeSubfieldTmpNo_' + fieldTmpNo, '', 1) +
	'</td>' +
	'<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td></td>' +
	'<td>' +
	  button('btnAddFieldSave_' + fieldTmpNo, 'bibEditBtnBold', 'Save') +
	  button('btnAddFieldCancel_' + fieldTmpNo, '', 'Cancel') +
	  button('btnAddFieldClear_' + fieldTmpNo, 'bibEditBtnClear', 'Clear') +
	'</td>' +
	'<td></td>' +
      '</tr>' +
    '</tbody>';
}

function createAddFieldRow(fieldTmpNo, subfieldTmpNo){
  /*
   * Create a row in the 'Add field' rowgroup.
   */
  var txtAddFieldSubfieldCode = '', txtAddFieldInd1 = '', txtAddFieldInd2 = '',
    btnAddFieldRemove = '';
  if (subfieldTmpNo == 0){
    txtAddFieldSubfieldCode = inputText('txtAddFieldTag_' + fieldTmpNo,
				'bibEditTxtTag', '', 3);
    txtAddFieldInd1 = inputText('txtAddFieldInd1_' + fieldTmpNo,
				'bibEditTxtInd', '', 1);
    txtAddFieldInd2 = inputText('txtAddFieldInd2_' + fieldTmpNo,
				'bibEditTxtInd', '', 1);
  }
  else
    btnAddFieldRemove = img('/img/delete.png', 'Remove subfield',
      'btnAddFieldRemove_' + fieldTmpNo + '_' + subfieldTmpNo);
  return '' +
    '<tr id="rowAddField_' + fieldTmpNo + '_' + subfieldTmpNo + '">' +
      '<td></td>' +
      '<td>' +
	txtAddFieldSubfieldCode + txtAddFieldInd1 + txtAddFieldInd2 +
      '</td>' +
      '<td></td>' +
      '<td></td>' +
      '<td class="bibEditCellAddSubfieldCode">' +
	inputText('txtAddFieldSubfieldCode_' + fieldTmpNo + '_' +
		  subfieldTmpNo, 'bibEditTxtSubfieldCode', 1, 1) +
      '</td>' +
      '<td>' +
	inputText('txtAddFieldValue_' + fieldTmpNo + '_' +
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
      '<td>' +
	input('hidden', 'hdnAddSubfieldsFreeTmpNo_' + fieldID, '', 1) +
      '</td>' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td>' +
	button('btnAddSubfieldsSave_' + fieldID, 'bibEditBtnBold', 'Save') +
        button('btnAddSubfieldsCancel_' + fieldID, '', 'Cancel') +
        button('btnAddSubfieldsClear_' + fieldID, 'bibEditBtnClear', 'Clear') +
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
    'Remove subfield', 'btnAddSubfieldsRemove_' + subfieldID);
  return '' +
    '<tr id="rowAddSubfields_' + subfieldID + '">' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td></td>' +
      '<td class="bibEditCellAddSubfieldCode">' +
	inputText('txtAddSubfieldsCode_' + subfieldID,
		  'bibEditTxtSubfieldCode', 1, 1) +
      '</td>' +
      '<td>' +
	inputText('txtAddSubfieldsValue_' + subfieldID, 'bibEditTxtValue') +
      '</td>' +
      '<td>' + btnRemove + '</td>' +
    '</tr>';
}

function displayMessage(msgType){
  /*
   * Display confirmation message in the main work area.
   */
  $('#bibEditContent').empty();
  var msg;
  switch (msgType){
    case 'Confirm: Submitted':
      msg = 'Your modifications have now been submitted. ' +
	'They will be processed as soon as the task queue is empty.';
      break;
    case 'Confirm: Deleted':
      msg = 'The record will be deleted as soon as the task queue is empty.';
      break;
    case 'Error: Non-existent record':
      msg = 'This record does not exist. Please try another record ID.';
      break;
    case 'Error: Locked record - by user':
      msg = 'This record is currently being edited by another user. Please ' +
	      'try again later.';
      break;
    case 'Error: Locked record - by queue':
      msg = 'This record cannot be safely edited at the moment. Please ' +
	      'try again in a few minutes.';
      break;
    case 'Error: Deleted record':
      msg = 'Cannot edit deleted record.';
      break;
    case 'Error: Permission denied':
      msg = 'Could not access record. Permission denied.';
    default:
      msg = msgType;
  }
  $('#bibEditContent').append('<span id="bibEditMessage">' + msg + '</span>');
}

function displayAlert(alertType, msgType, ready, arg){
  /*
   * Display pop-up message.
   */
  var msg;
  switch (msgType){
    case 'warningInvalidOrEmptyInput':
      msg =  'WARNING: Some subfields contain invalid MARC or are empty. \n' +
	'Click Cancel to go back and correct. \n' +
	'Click OK to ignore and continue (only valid subfields will be saved).';
      break;
    case 'errorCriticalInput':
      msg = 'ERROR: Your input had critical errors. Please go back and ' +
	'correct any fields with invalid MARC (red border) or fields that ' +
	'should not be empty.';
      break;
    case 'errorAddProtectedField':
      msg = 'ERROR: Cannot add protected field ' + arg + '.';
      break;
    case 'errorAddProtectedSubfield':
      msg = 'ERROR: Cannot add protected subfield ' + arg + '.';
      break;
    case 'errorDeleteProtectedField':
      msg = 'ERROR: Cannot delete protected field ' + arg + '.';
      break;
    default:
      msg = msgType;
  }
  var answer = true;
  if (alertType == 'confirm')
    answer = confirm(msg);
  else
    alert(msg);
  if (ready)
    updateStatus('ready');
  return answer;
}

function button(id, _class, value, event, handler){
  /*
   * Create a button tag with specified attributes.
   */
  id = id ? 'id="' + id + '" ' : '';
  _class = _class ? 'class="' + _class + '" ' : '';
  value = (value != undefined) ? value : '';
  event = event ? event + '="' + handler + '" ' : '';
  return '<button ' + id + _class + event + '>' + value + '</button>';
}

function img(src, title, id, _class, event, handler){
  /*
   * Create an image tag with specified attributes.
   */
  src = 'src="' + src + '" ';
  title = title ? 'title="' + title + '" ' : '';
  id = id ? 'id="' + id + '" ' : '';
  _class =  _class ? 'class="' + _class + '" ' : '';
  event =  event ? event + '="' + handler + '" ' : '';
  return '<img ' + src + title + id + _class + event + '/>';
}

function input(type, id, _class, value, event, handler, size, maxlength){
  /*
   * Create an input tag with specified attributes.
   */
  type = 'type="' + type + '" ';
  id = id ? 'id="' + id + '" ' : '';
  _class = _class ? 'class="' + _class + '" ' : '';
  value = (value != undefined) ? 'value="' + value + '" ' : '';
  event = event ? event + '="' + handler + '" ' : '';
  size = size ? 'size="' + size + '" ' : '';
  maxlength = maxlength ? 'maxlength="' + maxlength + '" ' : '';
  return '<input ' + type + id + _class + value + event + size +
    maxlength + '/>';
}

function inputText(id, _class, size, maxlength, value, event, handler){
  /*
   * Create a text input tag with specified attributes.
   */
  var type = 'type="text" ';
  id = id ? 'id="' + id + '" ' : '';
  _class = _class ? 'class="' + _class + '" ' : '';
  size = size ? 'size="' + size + '" ' : '';
  maxlength = maxlength ? 'maxlength="' + maxlength + '" ' : '';
  // name = name ? 'name="' + name + '" ' : '';
  value = value ? 'value="' + value + '" ' : '';
  event = event ? event + '="' + handler + '" ' : '';
  return '<input ' + type + id + _class + size + maxlength + value +
    event +  '/>';
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
