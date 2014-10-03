/*
 * This file is part of Invenio.
 * Copyright (C) 2012 CERN.
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
 * Module with all functions related to refextract and BibEdit
 */

 var refextract = (function() {

	var dialogReferences;

	function updateDialogLoading(title) {
		/* Creates a loading dialog
			@param title: title to be displayed on the dialog
		*/
		if (typeof dialogReferences !== "undefined") {
			dialogReferences.dialogDiv.remove();
		}
		dialogReferences = createDialog(title, "Loading...", 750, 700, true);
	}

	function updateDialogRefextractResult(json) {
		/* Receives JSON from the server and either:
			- Shows an error dialog with the error message
			- Updates the client representation of the record, updates the cache
			  file on the server and displays the new record on the interface
		*/
	    var bibrecord = json['ref_bibrecord'];
	    var textmarc = json['ref_textmarc'];
	    var xmlrecord = json['ref_xmlrecord'];
	    if (!xmlrecord) {
			dialogReferences.dialogDiv.remove();
			dialogReferences = createDialog("Error", json["ref_msg"]);
			dialogReferences.dialogDiv.dialog({
				buttons: {
					"Accept" : function() {
						$( this ).remove();
					}
				}
			});
		}
		/* References were extracted */
		else {
			addContentToDialog(dialogReferences, textmarc, "Do you want to apply the following references?");
			dialogReferences.dialogDiv.dialog({
				title: "Apply references",
				buttons: {
					"Apply references": function() {
						/* Update global record with the updated version */
						gRecord = bibrecord;
						/* Update cache in the server to have the updated record */
						createReq({recID: gRecID, recXML: xmlrecord, requestType: 'updateCacheRef'});
						/* Redraw whole content table and enable submit button */
						$('#bibEditTable').remove();
						var unmarked_tags = getUnmarkedTags();
						displayRecord();
						setUnmarkedTags(unmarked_tags);
						activateSubmitButton();
						$( this ).remove();
						},
					Cancel: function() {
						$( this ).remove();
					}
				}
			});
		}
	}

	function request_extract_from_url(url) {
		/* create a request to extract references from the given URL
			return: promise object to be resolved when request completes
		*/
		var requestExtractPromise = new $.Deferred();

		createReq({ recID: gRecID,
					url: url,
					requestType: 'refextracturl'},
					function(json) { requestExtractPromise.resolve(json); });

		return requestExtractPromise;
	}

	function request_extract_from_text(txt) {
		/* create a request to extract references from the given text
			return: promise object to be resolved when request completes
		*/
		var requestExtractPromise = new $.Deferred();

		createReq({ recID: gRecID,
					requestType: 'refextract',
					txt: txt },
					function(json) { requestExtractPromise.resolve(json); });

		return requestExtractPromise;
	}

	function request_extract_from_pdf() {
		/* create a request to extract references from the PDF attached to the
		   record

			return: promise object to be resolved when request completes
		*/
		var requestExtractPromise = new $.Deferred();

		createReq({ recID: gRecID,
					requestType: 'refextract'},
					function(json) { requestExtractPromise.resolve(json); });

		return requestExtractPromise;
	}

	function onRefExtractClick() {
		/*
		* Handle click on refextract from PDF button
		*
		*/
		log_action("onRefExtractClick");

		save_changes().done(function() {
			var loading_title = "Extracting references from PDF";
			updateDialogLoading(loading_title);

			var extract_from_pdf_promise = request_extract_from_pdf();
			extract_from_pdf_promise.done(updateDialogRefextractResult);
		});
	}

	function onRefExtractURLClick() {
		/*
		* Handle click on refextract from URL button
		*
		*/
		log_action("onRefExtractURLClick");
		save_changes().done(function() {
			var dialogContent = '<input type="text" id="input_extract_url" class="bibedit_input" placeholder="URL to extract references">';
			dialogReferences = createDialog("Extract references from URL", dialogContent, 200, 500);
			dialogReferences.contentParagraph.addClass('dialog-box-centered-no-margin');
			dialogReferences.dialogDiv.dialog({
				buttons: {
					"Extract references": function() {
						url = $("#input_extract_url").val();
						if (url === "") {
							return;
						}
						var loading_title = "Extracting references from URL";
						updateDialogLoading(loading_title);
						var extract_from_url_promise = request_extract_from_url(url);
						extract_from_url_promise.done(updateDialogRefextractResult);

					},
					Cancel: function() {
						$( this ).remove();
					}
			}});
		});
	}

	function onRefExtractFreeTextClick() {
		/*
		* Handler for free text refextract button. Allows to paste references
		* and process them using refextract on the server side.
		*/
		log_action("onRefExtractFreeTextClick");
		save_changes().done(function() {
			/* Create the modal dialog that will contain the references */
			var dialogContent = "Paste your references:<br/><textarea id='reffreetext' class='bibedit_input'></textarea>"
			dialogReferences = createDialog("Paste references", dialogContent, 750, 700);
			dialogReferences.dialogDiv.dialog({
				buttons: {
					"Extract references": function() {
						var textReferences = $('#reffreetext').val();
						if (textReferences === "") {
							return;
						}
						var loading_title = "Extracting references from text";
						updateDialogLoading(loading_title);
						var extract_from_text_promise = request_extract_from_text(textReferences);
						extract_from_text_promise.done(updateDialogRefextractResult);
					},
					Cancel: function() {
						$( this ).remove();
					}
				}
			});
		});
	}

	/* Public methods */
	return {
		onRefExtractURLClick: onRefExtractURLClick,
		onRefExtractFreeTextClick: onRefExtractFreeTextClick,
		onRefExtractClick: onRefExtractClick
	};

 })();