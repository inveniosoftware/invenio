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
 * This is the BibEdit Javascript for handling keyboard shortcuts, here after
 * called hotkeys.
 */

/*
 * Global variables
 */

var gSelectionModeOn = false;

function initHotkeys(){
  /*
   * Initialize all hotkeys.
   */
  // Focus on record selection field.
  $(document).bind('keydown', {combi: 'g', disableInInput: true},
    function(event){
      $('#txtSearchPattern').focus();
      event.preventDefault();
  });
  // Submit record.
  $(document).bind('keydown', {combi: 'shift+s', disableInInput: true},
    function(event){
      $('#btnSubmit').trigger('click');
      event.preventDefault();
  });
  // Cancel editing.
  $(document).bind('keydown', {combi: 'shift+c', disableInInput: true},
    function(event){
      $('#btnCancel').trigger('click');
      event.preventDefault();
  });
  // Delete record.
  $(document).bind('keydown', {combi: 'shift+d', disableInInput: true},
    function(event){
      $('#btnDeleteRecord').trigger('click');
      event.preventDefault();
  });
  // Toggle MARC/human tags.
  $(document).bind('keydown', {combi: 'shift+t', disableInInput: true},
    function(event){
      if (gTagFormat == 'MARC')
	$('#btnHumanTags').trigger('click');
      else if (gTagFormat == 'human')
	$('#btnMARCTags').trigger('click');
      event.preventDefault();
  });
  // Add new field.
  $(document).bind('keydown', {combi: 'a', disableInInput: true},
    function(event){
      $('#btnAddField').trigger('click');
      event.preventDefault();
  });
  // Sort fields.
  $(document).bind('keydown', {combi: 'shift+o', disableInInput: true},
    function(event){
      $('#btnSortFields').trigger('click');
      event.preventDefault();
  });
  // Delete selected (or focused subfield).
  $(document).bind('keydown', {combi: 'del', disableInInput: true},
    function(event){
      onDeleteFields(event);
      event.preventDefault();
  });
  // Delete selected (or focused field).
  $(document).bind('keydown', {combi: 'shift+del', disableInInput: true},
    function(event){
      onDeleteFields(event);
      event.preventDefault();
  });
  // Toggle 'selection mode'.
  $(document).bind('keydown', {combi: 's', disableInInput: true}, onKeyS);
  // Edit focused subfield.
  $(document).bind('keydown', {combi: 'return', disableInInput: true},
		   onKeyReturn);
  // Select focused subfield.
  $(document).bind('keydown', {combi: 'space', disableInInput: true},
		   onKeySpace);
  // Select focused subfields parent field.
  $(document).bind('keydown', {combi: 'shift+space', disableInInput: true},
		   onKeySpace);
  // Move focused subfield up.
  $(document).bind('keydown', {combi: 'ctrl+up', disableInInput: true},
		   onKeyCtrlUp);
  // Move focused subfield down.
  $(document).bind('keydown', {combi: 'ctrl+down', disableInInput: true},
		   onKeyCtrlDown);
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
}

function onKeyS(event){
  /*
   * Handle key 's' (toggle selection mode).
   */
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

function onKeyReturn(event){
  /*
   * Handle key return (edit subfield).
   */
  if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      $('#' + targetID).trigger('dblclick');
      event.preventDefault();
    }
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
	id = (tmpArray.length == 3) ? tmpArray.slice(0, -1).join('_') :
	  tmpArray.join('_');
	$('#boxField_' + id).trigger('click');
      }
      else{
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
  if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      var id = targetID.slice(targetID.indexOf('_')+1);
      $('#btnMoveSubfieldUp_' + id).trigger('click');
      event.preventDefault();
    }
  }
}

function onKeyCtrlDown(event){
  /*
   * Handle key ctrl+down (move subfield down).
   */
  if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      var id = targetID.slice(targetID.indexOf('_')+1);
      $('#btnMoveSubfieldDown_' + id).trigger('click');
      event.preventDefault();
    }
  }
}

function onTriggerFormControl(command, event){
  /*
   * Handle key shortcuts for triggering form controls ('Save', 'Cancel' or
   * 'Clear').
   */
  if (event.target.type == 'textarea'){
    if (command == 'Save'){
      $(event.target).parent().trigger('submit');
      event.preventDefault();
    }
    else if (command == 'Cancel'){
      $(event.target).parent().find('button[type=cancel]').trigger('click');
      event.preventDefault();
    }
  }
  else{
    var rowGroup = $(event.target).closest('tbody')[0];
    if (rowGroup){
      if (rowGroup.id.indexOf('rowGroupAddField')+1){
	$('#btnAddField' + command + '_' + rowGroup.id.slice(
	  rowGroup.id.indexOf('_')+1)).trigger('click');
	event.preventDefault();
      }
      else if (rowGroup.id.indexOf('rowGroup')+1){
	var btnToTrigger = $('#btnAddSubfields' + command + '_' +
			     rowGroup.id.slice(rowGroup.id.indexOf('_')+1));
	if (btnToTrigger.length){
	  $(btnToTrigger).trigger('click');
	  event.preventDefault();
	}
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
      if (rowGroup.id.indexOf('rowGroupAddField')+1)
	var fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	if (!$('#chkAddFieldControlfield_' + fieldID).attr('checked'))
	  btnAddSubfield = $('#btnAddFieldAddSubfield_' + fieldID);
      else if (rowGroup.id.indexOf('rowGroup')+1)
	btnAddSubfield = $('#btnAddSubfield_' + rowGroup.id.slice(
			   rowGroup.id.indexOf('_')+1));
      if (btnAddSubfield.length){
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
	fieldID = rowGroup.id.slice(rowGroup.id.indexOf('_')+1);
	tmpNo = $('#rowGroupAddField_' + fieldID).data('freeSubfieldTmpNo')-1;
	btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	while (!btnRemoveSubfield.length && tmpNo >= 1){
	  tmpNo--;
	  btnRemoveSubfield = $('#btnAddFieldRemove_' + fieldID + '_' + tmpNo);
	}
      }
      else if (rowGroup.id.indexOf('rowGroup')+1){
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