/*
 * This file is part of Invenio.
 * Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
 * This is the BibEdit Javascript for handling keyboard shortcuts, here after
 * called hotkeys.
 */

/*
 * Global variables
 */

var gSelectionModeOn = false;
var gReady = true;

function initHotkeys(){
  /*
   * Initialize all hotkeys.
   */
  // New record.
  $(document).bind('keydown', {combi: 'shift+n', disableInInput: true},
    function(event){
      $('#imgNewRecord').trigger('click');
      event.preventDefault();
  });
    // Clone record.
  $(document).bind('keydown', {combi: 'shift+l', disableInInput: true},
    function(event){
      var imgCloneRecord = $('#imgCloneRecord');
      if (!imgCloneRecord.hasClass('bibEditImgFaded')){
	imgCloneRecord.trigger('click');
	event.preventDefault();
      }
  });
  // Focus on record selection field.
  $(document).bind('keydown', {combi: 'g', disableInInput: true},
    function(event){
      $('#txtSearchPattern').focus();
      event.preventDefault();
  });
  // Previous record.
  $(document).bind('keydown', {combi: 'ctrl+right', disableInInput: true},
    function(event){
      var btnNext = $('#btnNext');
      if (!btnNext.attr('disabled')){
	btnNext.trigger('click');
	event.preventDefault();
      }
  });
  // Next record.
  $(document).bind('keydown', {combi: 'ctrl+left', disableInInput: true},
    function(event){
      var btnPrev = $('#btnPrev');
      if (!btnPrev.attr('disabled')){
	btnPrev.trigger('click');
	event.preventDefault();
      }
  });
  // Submit record.
  $(document).bind('keydown', {combi: 'shift+s', disableInInput: true},
    function(event){
      var btnSubmit = $('#btnSubmit');
      if (!btnSubmit.attr('disabled')){
	btnSubmit.trigger('click');
	event.preventDefault();
      }
  });
  // Cancel editing.
  $(document).bind('keydown', {combi: 'shift+c', disableInInput: true},
    function(event){
      var btnCancel = $('#btnCancel');
      if (!btnCancel.attr('disabled')){
	btnCancel.trigger('click');
	event.preventDefault();
      }
  });
  // Delete record.
  $(document).bind('keydown', {combi: 'shift+d', disableInInput: true},
    function(event){
      var btnDeleteRecord = $('#btnDeleteRecord');
      if (!btnDeleteRecord.attr('disabled')){
	btnDeleteRecord.trigger('click');
	event.preventDefault();
      }
  });
  // Toggle MARC/human tags.
  $(document).bind('keydown', {combi: 'shift+t', disableInInput: true},
    function(event){
      if (gTagFormat == 'MARC'){
	var btnHumanTags = $('#btnHumanTags');
	if (!btnHumanTags.attr('disabled')){
	  btnHumanTags.trigger('click');
	  event.preventDefault();
	}
      }
      else if (gTagFormat == 'human'){
	var btnMARCTags = $('#btnMARCTags');
	if (!btnMARCTags.attr('disabled')){
	  btnMARCTags.trigger('click');
	  event.preventDefault();
	}
      }
  });
  // Add new field.
  $(document).bind('keydown', {combi: 'a', disableInInput: true},
    function(event){
      var btnAddField = $('#btnAddField');
      if (!btnAddField.attr('disabled')){
	btnAddField.trigger('click');
	event.preventDefault();
      }
  });
  // Delete selected field(s).
  $(document).bind('keydown', {combi: 'del', disableInInput: true},
    function(event){
      var btnDeleteSelected = $('#btnDeleteSelected');
      if (!btnDeleteSelected.attr('disabled')){
	onDeleteClick(event);
	event.preventDefault();
      }
  });

  // Toggle 'selection mode'.
  $(document).bind('keydown', {combi: 's', disableInInput: true}, onKeyS);
  // Edit focused subfield.
  $(document).bind('keydown', {combi: 'return'},
		   onKeyReturn);
  // Save content and jump to next content field.
  $(document).bind('keydown', {combi: 'tab'},
		   onKeyTab);

  // Lauch autosuggest
  $(document).bind('keydown', {combi: 'ctrl+shift+a'}, function (event)  { onAutosuggest(event); } );
  $(document).bind('keydown', {combi: 'ctrl+9'}, function (event)  { onAutosuggest(event); } );

  // Save content and jump to previous content field.
  $(document).bind('keydown', {combi: 'shift+tab'},
		   onKeyTab);
  // Select focused subfield.
  $(document).bind('keydown', {combi: 'space', disableInInput: true},
		   onKeySpace);
  // Select focused subfields parent field.
  $(document).bind('keydown', {combi: 'shift+space', disableInInput: true},
		   onKeySpace);
  // Move selected field/subfield up.
  $(document).bind('keydown', {combi: 'ctrl+up'}, onKeyCtrlUp);
  // Move selected field/subfield down.
  $(document).bind('keydown', {combi: 'ctrl+down'}, onKeyCtrlDown);
  // Save content in current form.
  $(document).bind('keydown', 'ctrl+shift+s', function(event){
    onTriggerFormControl('Save', event);
  });
  // Cancel current form.
  $(document).bind('keydown', 'ctrl+shift+c', function(event){
    onTriggerFormControl('Cancel', event);
  });
  // Clear current form.
  $(document).bind('keydown', 'ctrl+shift+x', function(event){
    onTriggerFormControl('Clear', event);
  });
  // Add subfield in form.
  $(document).bind('keydown', {combi: 'ctrl+shift+e'}, onKeyCtrlShiftE);
  // Remove subfield from form.
  $(document).bind('keydown', {combi: 'ctrl+shift+d'}, onKeyCtrlShiftD);
  // Binding the undo/redo operations

  $(document).bind('keydown', {combi: 'ctrl+shift+z'}, onUndo);
  $(document).bind('keydown', {combi: 'ctrl+shift+y'}, onRedo);
}

function onKeyS(event){
  /*
   * Handle key 's' (toggle selection mode).
   */
  if (gRecID){
    if (gSelectionModeOn){
      $('#bibEditTable').unbind('mouseover.selection');
      gSelectionModeOn = false;
      updateStatus('report', 'Selection mode: Off');
    }
    else{
      $('#bibEditTable').bind('mouseover.selection', function(event){
	var targetID = event.target.id;
	if (targetID.slice(0, targetID.indexOf('_')) == 'content' &&
	    !$(event.target).hasClass('bibEditSelected'))
	  onKeySpace(event);
      });
      gSelectionModeOn = true;
      updateStatus('report', 'Selection mode: On');
    }
    if (!event.isDefaultPrevented())
      event.preventDefault();
  }
}

function onKeyReturn(event){
  /*
   * Handle key return (edit subfield).
   */
  if (event.target.nodeName == 'TEXTAREA'){
    $(event.target).parent().submit();
    event.preventDefault();
  }
  else if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      $('#' + targetID).trigger('click');
      event.preventDefault();
    }
  }
}

function onKeyTab(event){
  /*
   * Handle key tab (save content and jump to next content field).
   */
  if (event.target.nodeName == 'TEXTAREA'){
    var contentCells = $('.bibEditCellContent');
    var cell = $(event.target).parent().parent();
    var foo = $(event.target).parent();
    foo.submit();
    if (!event.shiftKey)
      $(contentCells).eq($(contentCells).index(cell)+1).trigger('click');
    else
      $(contentCells).eq($(contentCells).index(cell)-1).trigger('click');
    event.preventDefault();
  }
}

function onKeySpace(event){
  /*
   * Handle key space/shift+space (edit subfield/field).
   */
  if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      var id = targetID.slice(targetID.indexOf('_')+1);
      var tmpArray = id.split('_');
      if (event.shiftKey){
	// Shift is pressed. Select the full field.
	id = (tmpArray.length == 3) ? tmpArray.slice(0, -1).join('_') :
	  tmpArray.join('_');
	$('#boxField_' + id).trigger('click');
      }
      else{
	// Just select the subfield itself.
	if (tmpArray.length == 3)
	  $('#boxSubfield_' + id).trigger('click');
	else
	  $('#boxField_' + id).trigger('click');
      }
      event.preventDefault();
    }
  }
}

function onKeyCtrlUp(event){
  /*
   * Handle key ctrl+up (move subfield up).
   */
  if (gReady==false)
    return;
  gReady = false;
  // check if we want to move a field or subfield
  var selectedFields = $('#bibEditTable tbody.bibEditSelected');
  var selectedSubfields = $('#bibEditTable td.bibEditSelected');
  //move unique selected field
  if (selectedFields.length == 1) {
    var targetID = selectedFields.eq(0).attr('id');
    var targetInfo = targetID.split('_');
    var tag = targetInfo[1], fieldPos = targetInfo[2];
    onMoveFieldUp(tag, fieldPos);
  }
  else if (selectedSubfields.length == 1){// move subfield
    var targetID = selectedSubfields.eq(0).attr('id');
    var tmpArray = targetID.split('_');
    if (tmpArray[0] == 'content'){
      var tag = tmpArray[1], fieldPos = tmpArray[2], subfieldIndex = tmpArray[3];
      onMoveSubfieldClick('up', tag, fieldPos, subfieldIndex);
    }
  }
  event.preventDefault();
  gReady = true;
}

function onKeyCtrlDown(event){
  /*
   * Handle key ctrl+down (move subfield down).
   */
  if (gReady==false)
    return;
  gReady = false;
  // check if we want to move a field or subfield
  var selectedFields = $('#bibEditTable tbody.bibEditSelected');
  var selectedSubfields = $('#bibEditTable td.bibEditSelected');
  //move unique selected field
  if (selectedFields.length == 1) {
    var targetID = selectedFields.eq(0).attr('id');
    var targetInfo = targetID.split('_');
    var tag = targetInfo[1], fieldPos = targetInfo[2];
    onMoveFieldDown(tag, fieldPos);
  }
  else if (selectedSubfields.length == 1){// move subfield
    var targetID = selectedSubfields.eq(0).attr('id');
    var tmpArray = targetID.split('_');
    if (tmpArray[0] == 'content'){
      var tag = tmpArray[1], fieldPos = tmpArray[2], subfieldIndex = tmpArray[3];
      onMoveSubfieldClick('down', tag, fieldPos, subfieldIndex);
    }
  }
  event.preventDefault();
  gReady = true;
}

function onTriggerFormControl(command, event){
  /*
   * Handle key shortcuts for triggering form controls ('Save', 'Cancel' or
   * 'Clear').
   */
  var rowGroup = $(event.target).closest('tbody')[0];
  if (rowGroup){
    if (rowGroup.id.indexOf('rowGroupAddField')+1){
      // Click corresponding button in 'Add field' form.
      $('#btnAddField' + command + '_' + rowGroup.id.slice(
	rowGroup.id.indexOf('_')+1)).trigger('click');
      event.preventDefault();
    }
    else if (rowGroup.id.indexOf('rowGroup')+1){
      // Click corresponding button in 'Add subfields' form.
      var btnToTrigger = $('#btnAddSubfields' + command + '_' +
			   rowGroup.id.slice(rowGroup.id.indexOf('_')+1));
      if (btnToTrigger.length){
	$(btnToTrigger).trigger('click');
	event.preventDefault();
      }
    }
  }
}

function onKeyCtrlShiftE(event){
  /*
   * Handle key 'Ctrl+Shift+e' (add subfield to form).
   */
  var nodeName = event.target.nodeName;
  if (nodeName == 'TD' || nodeName == 'INPUT' || nodeName == 'BUTTON' ||
      nodeName == 'TEXTAREA'){
    var rowGroup = $(event.target).closest('tbody')[0];
    if (rowGroup){
      var btnAddSubfield;
      if (rowGroup.id.indexOf('rowGroupAddField')+1){
	// Add extra subfield to 'Add field' form.
	var fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	if (!$('#chkAddFieldControlfield_' + fieldID).attr('checked'))
	  btnAddSubfield = $('#btnAddFieldAddSubfield_' + fieldID);
      }
      else if (rowGroup.id.indexOf('rowGroup')+1)
	// Add extra subfield to 'Add subfields' form.
	btnAddSubfield = $('#btnAddSubfield_' + rowGroup.id.slice(
			   rowGroup.id.indexOf('_')+1));
      if (btnAddSubfield){
	$(btnAddSubfield).trigger('click');
	event.preventDefault();
      }
    }
  }
}

function onKeyCtrlShiftD(event){
  /*
   * Handle key 'Ctrl+Shift+d' (remove subfield from form).
   */
  var nodeName = event.target.nodeName;
  if (nodeName == 'TD' || nodeName == 'INPUT' || nodeName == 'BUTTON' ||
      nodeName == 'TEXTAREA'){
    var rowGroup = $(event.target).closest('tbody')[0];
    if (rowGroup){
      var fieldID, tmpNo, btnRemoveSubfield;
      if (rowGroup.id.indexOf('rowGroupAddField')+1){
	// Remove extra subfield from 'Add field' form.
	fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	tmpNo = $('#rowGroupAddField_' + fieldID).data('freeSubfieldTmpNo')-1;
	btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	while (!btnRemoveSubfield.length && tmpNo >= 1){
	  tmpNo--;
	  btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	}
      }
      else if (rowGroup.id.indexOf('rowGroup')+1){
	// Remove extra subfield from 'Add subfields' form.
      	fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	tmpNo = $('#rowGroup_' + fieldID).data('freeSubfieldTmpNo')-1;
	btnRemoveSubfield = $('#btnAddSubfieldsRemove_' + fieldID + '_' +
			      tmpNo);
	while (!btnRemoveSubfield.length && tmpNo > 1){
	  tmpNo--;
	  btnRemoveSubfield = $('#btnAddSubfieldsRemove_' + fieldID + '_' +
				tmpNo);
	}
      }
      if (btnRemoveSubfield.length){
	$(btnRemoveSubfield).trigger('click');
	event.preventDefault();
      }
    }
  }
}
