/*
 * This file is part of Invenio.
 * Copyright (C) 2011, 2012, 2013 CERN.
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
* Function: remove
* Purpose:  Extend the array prototype to remove an element by value
* Input(s): object:value - value to remove
* Returns:  object:removed - the removed element if found or undefined elsewise
*
*/
Array.prototype.remove = function( value ) {
    var index = this.indexOf( value );
    if ( index !== -1 ) return this.splice( index, 1 );
}









/*
* Variable: Authorlist.CSS
* Purpose:  Central enumeration and mapping for the CSS classes used in the 
*           Authorlist prototype. Eases consistent look up and renaming if 
*           required.
*
*/
Authorlist.CSS = {
    // Body classes
    'Active'            : 'ui-state-active',
    'Loading'           : 'AuthorlistLoading',
    'Progress'          : 'AuthorlistProgress',
    

    // Section classes
    'Affiliations'      : 'AuthorlistAffiliations',
    'Authors'           : 'AuthorlistAuthors',
    'Authorlist'        : 'Authorlist',
    'Data'              : 'AuthorlistData',
    'Footnote'          : 'AuthorlistFootnote',
    'FootnoteSymbol'    : 'AuthorlistFootnoteSymbol',
    'Headline'          : 'AuthorlistHeadline',
    'Menu'              : 'AuthorlistMenu',
    'Paper'             : 'AuthorlistPaper',
    'Reference'         : 'AuthorlistReference',
    
    // Input classes
    'Input'             : 'AuthorlistInput',
    'Label'             : 'AuthorlistLabel',
    
    // Button classes
    'Add'               : 'AuthorlistAdd',
    'AddIcon'           : 'ui-icon-plusthick',
    'Back'              : 'AuthorlistBack',
    'BackIcon'          : 'ui-icon-arrowreturnthick-1-w',
    'Button'            : 'AuthorlistButton',
    'ButtonText'        : 'ui-button-text',
    'Delete'            : 'AuthorlistDelete',
    'DeleteIcon'        : 'ui-icon-trash',
    'Export'            : 'AuthorlistExport',
    'ExportXML'         : 'AuthorlistExportXML',
    'ExportElsevier'    : 'AuthorlistExportElsevier',
    'ExportAPS'         : 'AuthorlistExportAPS',
    'ExportIcon'        : 'ui-icon-document',
    'Import'            : 'AuthorlistImport',
    'ImportIcon'        : 'ui-icon-folder-open',
    'ImportXML'         : 'AuthorlistImportXML',
    'Remove'            : 'AuthorlistRemove',
    'RemoveIcon'        : 'ui-icon-minusthick',
    'Save'              : 'AuthorlistSave',
    'SaveIcon'          : 'ui-icon-disk',
    
    // Dialog classes
    'Bullet'            : 'AuthorlistBullet',
    'BulletIcon'        : 'ui-icon-carat-1-e',
    'BulletText'        : 'AuthorlistBulletText',
    'Confirmation'      : 'ui-state-highlight',
    'ConfirmationIcon'  : 'ui-icon-info',
    'ConfirmationTitle' : 'AuthorlistConfirmationTitle',
    'Dialog'            : 'AuthorlistDialog',
    'Error'             : 'ui-state-error',
    'ErrorIcon'         : 'ui-icon-alert',
    'ErrorTitle'        : 'AuthorlistErrorTitle',
    'ErrorMessage'      : 'AuthorlistErrorMessage',
    'Icon'              : 'ui-icon'
}

/*
* Variable: Authorlist.DEFAULT_ERROR
* Purpose:  Default error text for unsuccessful AJAX requests.
*
*/
Authorlist.DEFAULT_ERROR = [ 'Site is currently not reachable',
                             'Please try again later',
                             'Contact the site administrator' ];

/*
* Variable: Authorlist.EMPTY
* Purpose:  RegEx that defines that a field is considered to be empty if it 
*           contains only whitespaces or no characters at all.
*
*/
Authorlist.EMPTY = /^\s*$/;

/*
* Variable: Authorlist.ID
* Purpose:  RegEx that parses the id URL paremeter and groups it
*
*/
Authorlist.ID = /id=([^&$]+)/;

/*
* Variable: Authorlist.Indices
* Purpose:  Names for the indices into the result arrays of the authors and 
*           affiliations .fnGetData() arrays
*
*/
Authorlist.INDICES = {
    'Acronym'         : 2,
    'Address'         : 4,
    'AffiliationName' : 0,
    'Affiliations'    : 6,
    'AuthorName'      : 4,
    'Index'           : 0,
    'Umbrella'        : 3
};

/*
* Variable: Authorlist.URLS
* Purpose:  Sets up a mapping of commonly used URLS for the save and export 
*           functionality.
*
*/
Authorlist.URLS = {
    'AuthorsXML'        : '/authorlist/?state=export&format=authorsxml',
    'ElsevierArticle'   : '/authorlist/?state=export&format=elsevier',
    'APSpaper'          : '/authorlist/?state=export&format=aps',
    'Clone'             : '/authorlist/?state=clone',
    'Delete'            : '/authorlist/?state=delete',
    'Itemize'           : '/authorlist/?state=itemize',
    'Latex'             : '/authorlist/?state=export&format=latex',
    'Load'              : '/authorlist/?state=load',
    'MainPage'          : '/authorlist/',
    'Open'              : '/authorlist/?state=open',
    'Import'            : '/authorlist/?state=import',
    'ImportXML'         : '/authorlist/?state=importxml',
    'Save'              : '/authorlist/?state=save'
};


/*
* Function: Authorlist
* Purpose:  Constructor
* Input(s): string:sId - Id of the html element the Authorlist will be embedded
*                        into (preferably a div).
* Returns:  Authorlist instance when called with new, else undefined
*
*/
function Authorlist( sId ) {
    this._nParent = jQuery( '#' + sId );
    this._nParent.addClass( Authorlist.CSS.Authorlist );

    this._sId = this._fnGetId();

    this._oPaper = this._fnCreatePaper( this._nParent );
    this._oAuthors = this._fnCreateAuthors( this._nParent );
    this._oAffiliations = this._fnCreateAffiliations( this._nParent );
    this._nFootnotes = this._fnCreateFootnotes( this._nParent );
    this._nMenu = this._fnCreateMenu( this._nParent );

    this._fnRetrieve( this._sId );
}

/*
* Function: fnGetData
* Purpose:  Returns the whole content of the authorlist tool as an objects. It 
*           includes the values of the paper information, the author SpreadSheet
*           as well as the ones of the affiliations sheet.
* Input(s): void
* Returns:  object:oResults - the content of the authorlist instance
*
*/
Authorlist.prototype.fnGetData = function() {
    var oResult = this._oPaper.fnGetData();
    oResult.authors = this._oAuthors.fnGetData();
    oResult.affiliations = this._oAffiliations.fnGetData();

    return oResult;
};

/*
* Function: fnLoadData
* Purpose:  Loads a fnGetData()-like object as the preset values.
* Input(s): object:oData - the fnGetData()-like object
* Returns:  void
*

*/
Authorlist.prototype.fnLoadData = function( oData ) {
    this._oPaper.fnLoadData( oData );
    this._oAuthors.fnLoadData( oData.authors );
    this._oAffiliations.fnLoadData( oData.affiliations );
};

/*
* Function: fnValidate
* Purpose:  Returns a list of errors if the entered data in the author list 
*           fields are in valid. This means it checks whether all required 
*           fields are set as well as whether every link string is correct. If
*           so the array with error message is empty.
* Input(s): object:oData - the data of the authorlist as it can be obtained by 
                           the fnGetData() call
* Returns:  array string:asErrors - true if data is sane, else false
*
*/
Authorlist.prototype.fnValidate = function( oData ) {
    var asErrors = [];

    // Paper title
    if ( oData.paper_title.match( Authorlist.EMPTY ) !== null ) {
        asErrors.push( 'Paper title <strong>required</strong>' );
    }
    // Collaboration name
    if ( oData.collaboration.match( Authorlist.EMPTY ) !== null ) {
        asErrors.push( 'Collaboration name <strong>required</strong>' );
    }

    // Validate affiliations and authors
    var aaoAffiliations = oData.affiliations;
    var aaoAuthors = oData.authors;
    var asAcronyms = this._fnValidateAffiliations( aaoAffiliations, asErrors );
    this._fnValidateAuthors( aaoAuthors, asAcronyms, asErrors );
    this._fnValidateUmbrellas( aaoAffiliations, asAcronyms, asErrors );

    return asErrors;
};

/*
* Function: _fnBackToMainPage
* Purpose:  Invoking this function sends the user immediately back to the main 
*           page. All unchanged state is lost.
* Input(s): void
* Returns:  void
*
*/
Authorlist.prototype._fnBackToMainPage = function() {
    this._fnProgress();
    window.location.href = Authorlist.URLS.MainPage;
};

/*
* Function: _fnConfirm
* Purpose:  Opens up a pop-up asking the user to confirm the action. If the user
*           clicks no, nothing happens, otherwise the passed callback is called.
* Input(s): function:fnCallback - the confirmed callback
            string:sMessage - message displayed in the pop-up. If empty,
            displays the default message
* Returns:  void
*
*/
Authorlist.prototype._fnConfirm = function( fnCallback, sMessage ) {
    var nDialog = jQuery( '<div>' );
    var nConfirmation = jQuery( '<p>' );
    var nConfirmationIcon = jQuery( '<span>' );
    var nConfirmationText = jQuery( '<span>' );
    var fnBound = fnCallback.bind( this );

    // Add items to dialog and apply style through classes
    if (sMessage){
        nConfirmationText.html(sMessage);
    } else {
        nConfirmationText.html( 'Are you sure you want to proceed?' );
    }
    nDialog.addClass( Authorlist.CSS.Confirmation );
    nConfirmation.addClass( Authorlist.CSS.ConfirmationTitle );
    nConfirmationIcon.addClass( Authorlist.CSS.Icon );
    nConfirmationIcon.addClass( Authorlist.CSS.ConfirmationIcon );

    // Add elements to the DOM
    nDialog.append( nConfirmation.append(nConfirmationIcon, nConfirmationText));
    nDialog.appendTo( jQuery( 'body' ) );

    // Instantiate a jQuery UI dialog widget
    nDialog.dialog( {
        'resizable'   : false,
//        'title'       : 'Confirm',
        'dialogClass' : Authorlist.CSS.Dialog,
        'minWidth'    : 'auto',
        'width'       : 'auto',
        'minHeight'   : 118,
        'height'      : 118,
        'buttons'     : {
            'Yes' : function() { jQuery( this ).remove(); fnBound(); },
            'No'  : function() { jQuery( this ).remove(); }
        }
    } );
};

/*
* Function: _fnCreateAffiliations
* Purpose:  Creates all DOM-elements required for the affiliations - i.e. the 
*           headline and the wrapping div - embeds a SpreadSheet instance in it 
*           and returns the created object afterwards.
* Input(s): node:nParent - the node where the affiliations will be embedded
* Returns:  object:oAffiliations - the SpreadSheet instance
*
*/
Authorlist.prototype._fnCreateAffiliations = function( nParent ) {
    var nAffiliations = jQuery( '<div>' );
    nAffiliations.attr( 'id', Authorlist.CSS.Affiliations );
    this._fnCreateHeadline( nAffiliations, 'Affiliations' );
    nParent.append( nAffiliations );

    var oAffiliations = new SpreadSheet( Authorlist.CSS.Affiliations, {
        columns : [ {
            'title'       : '',
            'type'        : 'increment',
            'width'       : '2%'
        }, {
            'title'       : 'Edit',
            'type'        : 'edit'
        }, {
            'title'       : 'Acronym (*)',
            'width'       : '12%'
        }, {
            'title'       : 'Umbrella (+)',
            'width'       : '9%'
        }, {
            'title'       : 'Name And Address (*)'
        }, {
            'title'       : 'Domain',
            'width'       : '20%'
        }, {
            'title'       : 'Member',
            'type'        : 'checkbox',
            'value'       : true,
            'width'       : '4%'
        }, {
            'title'       : 'ID',
            'width'       : '9%'
        } ]
    } );

    return oAffiliations;
};

/*
* Function: _fnCreateAuthors
* Purpose:  Creates all DOM-elements required for the authors - i.e. the 
*           headline and the wrapping div - embeds a SpreadSheet instance in it 
*           and returns the created object afterwards.
* Input(s): node:nParent - the node where the authors will be embedded
* Returns:  object:oAffiliations - the SpreadSheet instance
*
*/
Authorlist.prototype._fnCreateAuthors = function( nParent ) {
    var nAuthors = jQuery( '<div>' );
    nAuthors.attr( 'id', Authorlist.CSS.Authors );
    this._fnCreateHeadline( nAuthors, 'Authors' );
    nParent.append( nAuthors );

    var oAuthors = new SpreadSheet( Authorlist.CSS.Authors, {
        columns : [ {
            'title'       : '',
            'type'        : 'increment',
            'width'       : '2%'
        }, {
            'title'       : 'Edit',
            'type'        : 'edit'
        },  {
            'title'       : 'Family Name'
        }, {
            'title'       : 'Given Name'
        }, {
            'title'       : 'Name On Paper (*)'
        }, {
            'title'       : 'Status',
            'type'        : 'select',
            'value'       : '',
            'options'     : ['', 'Deceased']
        }, {
            'title'       : 'Affiliations (*,+)',
            'type'        : 'textselect',
            'value'       : gAuthorlistConfig['AUTHOR_AFFILIATION_TYPE'][0] ? gAuthorlistConfig['AUTHOR_AFFILIATION_TYPE'][0] : 'update config file!',
            'options'     : gAuthorlistConfig['AUTHOR_AFFILIATION_TYPE'],
            'width'       : '25%',
            'extendable'  : true
        }, {
            'title'       : 'Identifiers',
            'type'        : 'textselect',
            'value'       : gAuthorlistConfig['IDENTIFIERS_LIST'][0] ? gAuthorlistConfig['IDENTIFIERS_LIST'][0] : 'update config file!',
            'options'     : gAuthorlistConfig['IDENTIFIERS_LIST'],
            'width'       : '17%',
            'extendable'  : true
        } ]
    } );

    return oAuthors;
};

/*
* Function: _fnCreateButton
* Purpose:  Creates a button in the given parent element with the given label 
*           and - if set - given icon and returns the new button. The button is 
*           a jQuery UI button widget.
* Input(s): node:nParent - the parent element
*           string:sLabel - the button label
*           string:sIcon - a jQuery UI/general CSS icon class
* Returns:  node:nButton - the button widget
*
*/
Authorlist.prototype._fnCreateButton = function( nParent, sLabel, sIcon) {
    var nButton = jQuery( '<button>' ).addClass( Authorlist.CSS.Button );
    nParent.append( nButton );

    nButton.button( {
        'label' : sLabel,
        'icons' : {
            'primary' : sIcon
        }
    } );

    return nButton;
};


/*
* Function: _fnCreateFootnotes
* Purpose:  Creates the small footnotes below the tables
* Input(s): node:nParent - the node to append the footnotes to
* Returns:  void
*
*/
Authorlist.prototype._fnCreateFootnotes = function( nParent ) {
    var nFootnotes = jQuery( '<div>' ).addClass( Authorlist.CSS.Footnote );

    var nRequired       = jQuery( '<div>' );
    var nRequiredSymbol = jQuery( '<span>(*)</span>' );
    var nRequiredText   = jQuery( '<span>Required</span>' );
    nRequired.append( nRequiredSymbol, nRequiredText );

    var nLink       = jQuery( '<div>' );
    var nLinkSymbol = jQuery( '<span>(+)</span>' );
    var nLinkText   = jQuery( '<span>Use an acronym of the affiliations table</span>' );
    nLink.append( nLinkSymbol, nLinkText );

    nRequiredSymbol.addClass( Authorlist.CSS.FootnoteSymbol );
    nLinkSymbol.addClass( Authorlist.CSS.FootnoteSymbol );
    nFootnotes.append( nRequired, nLink );

    nParent.append( nFootnotes );
};

/*
* Function: _fnCreateForm
* Purpose:  Creates a small hidden form to exchange data with the server
* Input(s): node:nParent - the node where the form will be embedded into
* Returns:  node:nForm - the form node
*
*/
Authorlist.prototype._fnCreateForm = function( nParent ) {
    var nForm = jQuery( '<form>' );
    var nField = jQuery( '<input type="hidden">' );

    nField.attr( 'name', 'data' ).addClass( Authorlist.CSS.Data );
    nField.appendTo( nForm );
    nForm.appendTo( nParent );

    return nForm;
};

/*
* Function: _fnCreateHeadline
* Purpose:  Small helper function that will create a generic authorlist headline
* Input(s): node:nParent - the node going to get a headline
*           string:sTitle - the title string
* Returns:  node:nHeadline - the created headline node
*
*/
Authorlist.prototype._fnCreateHeadline = function( nParent, sTitle ) {
    var nHeadline = jQuery( '<h2>' + sTitle + '</h2>' );
    nHeadline.addClass( Authorlist.CSS.Headline );
    nParent.append( nHeadline );

    return nHeadline;
};

/*
* Function: _fnCreateMenu
* Purpose:  Creates a new headline for the menu, creates the buttons and embeds 
*           it into the parent and returns the created node.
* Input(s): node:nParent - where to append the paper information to
* Returns:  node:nMenu - the menu node
*
*/
Authorlist.prototype._fnCreateMenu = function( nParent ) {
    var self = this;

    // Create menu container
    var nMenu = jQuery( '<div>' );
    nMenu.attr( 'id', Authorlist.CSS.Menu );
    nParent.append( nMenu );

    // Create separator
    this._fnCreateHeadline( nMenu, '' );

    // Create buttons
    var nBackButton = this._fnCreateButton( nMenu, 'All Papers', Authorlist.CSS.BackIcon );
    var nSave = this._fnCreateButton( nMenu, 'Save', Authorlist.CSS.SaveIcon );
    var nDeleteButton = this._fnCreateButton( nMenu, 'Delete', Authorlist.CSS.DeleteIcon );
    var nAuthorsXML = this._fnCreateButton( nMenu, 'AuthorsXML', Authorlist.CSS.ExportIcon );
    var nElsevier = this._fnCreateButton( nMenu, 'ElsevierArticle', Authorlist.CSS.ExportIcon );
    var nAPS = this._fnCreateButton( nMenu, 'APSpaper', Authorlist.CSS.ExportIcon );
    var nImport = this._fnCreateButton( nMenu, 'Import', Authorlist.CSS.ImportIcon );
    var nImportXML = this._fnCreateButton( nMenu, 'ImportXML', Authorlist.CSS.ImportIcon );

    // Add classes   
    nBackButton.addClass( Authorlist.CSS.Back );
    nSave.addClass( Authorlist.CSS.Save );
    nDeleteButton.addClass( Authorlist.CSS.Delete );
    nAuthorsXML.addClass( Authorlist.CSS.Export + ' ' + Authorlist.CSS.ExportXML );
    nElsevier.addClass( Authorlist.CSS.Export + ' ' + Authorlist.CSS.ExportElsevier );
    nAPS.addClass( Authorlist.CSS.Export + ' ' + Authorlist.CSS.ExportAPS );
    nImport.addClass( Authorlist.CSS.Import );
    nImportXML.addClass( Authorlist.CSS.ImportXML );

    // Register callbacks for the buttons
    nBackButton.click( function() {
        self._fnBackToMainPage();
    } );

    nSave.click( function( event ) {
        self._fnSave();
    } );

    nDeleteButton.click( function() {
        self._fnConfirm( self._fnDelete );
    } );

    nImport.click( function() {
        self._fnImport('record');
    } );

    nImportXML.click( function() {
        self._fnImport('xml');
    } );

    jQuery( nMenu ).delegate( '.' + Authorlist.CSS.Export, 'click', function() {
        self._fnExport( this );
    } );

    return nMenu;
};

/*
* Function: _fnCreatePaper
* Purpose:  Creates a new headline for the paper information, creates a Paper 
*           objects, embeds it into the parent and returns it.
* Input(s): node:nParent - where to append the paper information to
* Returns:  object:oPaper - the Paper instance.
*
*/
Authorlist.prototype._fnCreatePaper = function( nParent ) {
    var nPaper = jQuery( '<div>' );
    nPaper.attr( 'id', Authorlist.CSS.Paper );
    this._fnCreateHeadline( nPaper, 'Paper' );
    nParent.append( nPaper );

    return new Paper( Authorlist.CSS. Paper );
};

/*
* Function: _fnDelete
* Purpose:  Deletes the currently open sheet completely from the database. There
*           is no backup copy or safety net. Sends the user on success back to 
*           the main page or shows an error on failure.
* Input(s): void
* Returns:  void.
*
*/
Authorlist.prototype._fnDelete = function() {
    var self = this;
    // Indicate that we are working
    this._fnProgress();

    jQuery.ajax( {
        'type'    : 'POST',
        'url'     : Authorlist.URLS.Delete + '&id=' + self._sId,
        'success' : function() {
            // Remove the working status and go back to the main page
            self._fnProgressDone();
            self._fnBackToMainPage();
        },
        'error'   : function() {
            // We are done with progressing and should display some errors.
            var sPreamble = 'An error occured while deleting the sheet:';
            self._fnProgressDone();
            self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
        }
    } );
};

/*
* Function: _fnImport
* Purpose:  Creates generic import Dialog and runs more specific import
* function depending on the source
* Input(s): string source: parameter, specifying what kind of import will be performed
* Returns:  void
*
*/
Authorlist.prototype._fnImport = function(source) {
    var self = this;

    /* Create generic dialog to import data */
    var nDialog = jQuery( '<div title="Import data">' );

    var nConfirmation = jQuery( '<p>' );
    var nConfirmationIcon = jQuery( '<span>' );
    var nConfirmationText = jQuery( '<span>' );
    var nInput = jQuery( '<input>' );

    // Add items to dialog and apply style through classes
    nDialog.addClass( Authorlist.CSS.Confirmation );
    nConfirmation.addClass( Authorlist.CSS.ConfirmationTitle );
    nConfirmationIcon.addClass( Authorlist.CSS.Icon );
    nConfirmationIcon.addClass( Authorlist.CSS.ConfirmationIcon );

    // Add elements to the DOM
    nDialog.append( nConfirmation.append(nConfirmationIcon));

    /* cancel function closes the dialog window */
    var cancel = function() {
            nDialog.dialog("close");
    };
    /* Generic options for dialog widget*/
    var nOptions = {
        'resizable'   : true,
        'dialogClass' : Authorlist.CSS.Dialog,
        'minWidth'    : 300,
        'width'       : 'auto',
        'minHeight'   : 128,
        'height'      : 168,
        'close'       : function (e, ui) {
            nDialog.remove();
        },
        'buttons'     : {
            'Import'  : '',
            /* Import is empty because it's a placeholder (it's a first element
                of buttons so it will be displayed first in the dialog window).
                Later on I connect Import with different functions
            */
            'Cancel'  : cancel
        }
    };

    /* Open different dialog windows depending on the source */
    switch (source) {
    case 'record':
        self._fnImportDialog(nDialog, nOptions);
        break;
    case 'xml':
        self._fnImportXMLDialog(nDialog, nOptions);
        break;
    default:
        /* Something went wrong */
        return;
    }
};

/*
* Function: _fnImportDialog
* Purpose:  Opens a dialog widget for _fnImport function, where user can specify record ID
* Input(s): nDialog: jQuery object
* Input(s): nOptions: JavaScript object
* Returns:  void
*
*/
Authorlist.prototype._fnImportDialog = function(nDialog, nOptions) {
    var self = this;

    // Specify dialog box main text
    var nConfirmationText = jQuery( '<span>' );
    var nInput = jQuery( '<input>' );

    nConfirmationText.html( 'Insert record ID to import from:' );
    nDialog.find('p').append(nConfirmationText);
    nDialog.append('<br />',nInput);
    nDialog.appendTo( jQuery( 'body' ) );

    var getResponse = function(e) {
        self._fnProgress();
        var recordID = nInput.val();
        if (!recordID) {
            // no recordID - do nothing
            self._fnProgressDone();
            return;
        }
        jQuery.ajax( {
            'type'    : 'POST',
            'url'     : Authorlist.URLS.Import + '&importid=' + recordID,
            'data'    : '',
            'success' : function(oData) {
                // Remove the working status
                self._fnProgressDone();
                // If no data was imported, display a warning and do nothing
                if (jQuery.isEmptyObject(oData)) {
                    self._fnShowErrors('This record doesn\'t exist', []);
                } else if (oData.authors.length || oData.affiliations.length)
                {
                    // Display confirmation that previous data will be erased
                    if (self._oAffiliations.fnGetData().length ||
                        self._oAuthors.fnGetData().length ) {
                        var confirmation = "Previous data will be replaced. Are you sure you want to continue ?";
                        self._fnConfirm(function () {
                            self._fnClearTables();
                            return self.fnLoadData(oData);
                        }, confirmation);
                    } else {
                        self._fnClearTables();
                        self.fnLoadData( oData );
                    }
                    nDialog.dialog("close");
                } else {
                    self._fnShowErrors('There is no data to import from this record', []);
                }
            },
            'error'   : function() {
                // We are done with progressing and should display some errors.
                var sPreamble = 'An error occured while importing the record';
                self._fnProgressDone();
                self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
            }
        } );
    };
    // Connect "Import" button with a function
    nOptions.buttons.Import = getResponse;

    // Instantiate a jQuery UI dialog widget
    nDialog.dialog( nOptions );

    /* Import data when ENTER key is pressed*/
    nDialog.keypress(function(e) {
        if (e.keyCode == $.ui.keyCode.ENTER) {
            $(this).parent().find('button:first').click();
        }
    });
};

/*
* Function: _fnImportXMLDialog
* Purpose:  Opens a dialog widget where user can select an XML file to import data
* Input(s): nDialog: jQuery object
* Input(s): nOptions: JavaScript object
* Returns:  void
*
*/
Authorlist.prototype._fnImportXMLDialog = function(nDialog, nOptions) {
    var self = this;

    var nConfirmationText = jQuery( '<span>' );
    // Add items to dialog and apply style through classes
    nConfirmationText.html( 'Select XML file to import from:' );
    nDialog.find('p').append(nConfirmationText);

    var importForm = jQuery('<form method="POST" enctype="multipart/form-data">');
    importForm.append('<input type="file" id="fileselect" name="fileselect" />');
    importForm.attr('action', Authorlist.URLS.Import);

    nDialog.append(importForm);
    importForm.wrap('<p>');
    nDialog.appendTo( jQuery( 'body' ) );

    var importXML = function () {
        self._fnProgress();
        // Stop if input field is empty
        if (!$('#fileselect').val()) {
            self._fnProgressDone();
            return;
        }
        // Create FormData element to send file with ajax
        var formData = new FormData();
        // Grab data from the form
        formData.append('xmlfile', document.getElementById("fileselect").files[0]);
        jQuery.ajax({
            'type'          : 'POST',
            'processData'   : false,
            'contentType'   : false,
            'url'           : Authorlist.URLS.ImportXML,
            'data'          : formData,
            'success' : function(oData) {
                // Remove the working status
                self._fnProgressDone();
                if (jQuery.isEmptyObject(oData) || typeof oData.authors === 'undefined') {
                    var warning = 'There was no data to import from this file. \
                    Please make sure the file meets the requirements of the \
                    specification: http://www.slac.stanford.edu/spires/hepnames/authors_xml';
                    self._fnShowErrors(warning, []);
                    return;
                }
                // Display confirmation, that previous data will be erased
                if (self._oAffiliations.fnGetData().length ||
                    self._oAuthors.fnGetData().length ) {
                    var confirmation = "Previous data will be replaced. Are you sure you want to continue ?";
                    self._fnConfirm(function () {
                        self._fnClearTables();
                        return self.fnLoadData(oData);
                    }, confirmation);
                } else {
                    self._fnClearTables();
                    self.fnLoadData( oData );
                }
                nDialog.dialog("close");
            },
            'error'   : function() {
                // We are done with progressing and should display some errors.
                var sPreamble = 'An error occured while importing the data';
                self._fnProgressDone();
                self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
            }
        });
    };

    // Connect "Import" button with a function
    nOptions.buttons.Import = importXML;

    nDialog.dialog( nOptions );
};

/*
* Function: _fnClearTables
* Purpose:  Clears the Authors and Affiliations tables
* Input(s): void
* Returns:  void
*
*/

Authorlist.prototype._fnClearTables = function() {
    this._oAuthors._oDataTable.fnClearTable();
    this._oAffiliations._oDataTable.fnClearTable();
};


/*
* Function: _fnCleanEmptyAffiliations
* Purpose:  Removes empty affiliations from the data object
* Input(s): object:oData - all the data from the table
* Returns:  void
*
*/
Authorlist.prototype._fnCleanEmptyAffiliations= function( oData ) {
    oData.authors.forEach( function( aoAuthor ) {
        var aasAffiliations = aoAuthor[ Authorlist.INDICES.Affiliations ];
        aasAffiliations.forEach( function( asAffiliation, index ) {
                var sAffName = asAffiliation[ Authorlist.INDICES.AffiliationName ];
                if ( sAffName.match( Authorlist.EMPTY ) ) {
                    aasAffiliations.splice(index, 1);
                }
            } );
    });
}

/*
* Function: _fnExport
* Purpose:  Exports the data of the authorlist instance on the server as long as 
*           there are no errors, which will be displayed in a dialog otherwise.
* Input(s): node:nButton - the pressed export button
* Returns:  void
*
*/
Authorlist.prototype._fnExport = function( nButton ) {
    nButton = jQuery( nButton );

    var oData = this.fnGetData();
    this._fnCleanEmptyAffiliations(oData);
    var asErrors = this.fnValidate( oData );
    var sButtonText = nButton.find( '.' + Authorlist.CSS.ButtonText ).text();
    var sURL = Authorlist.URLS[ sButtonText ];

    // create a form with data in the hidden field, submit it
    // and remove the form from the DOM
    function create_and_submit_form() {
        var nForm = jQuery( '<form>' );
        var nInput = jQuery( '<input name="data" type="hidden">' );
        nForm.attr( 'action', sURL ).attr( 'method', 'POST' );
        nForm.append( nInput );
        nForm.appendTo( jQuery( 'body' ) );

        nInput.val( JSON.stringify( oData ) );
        nForm.submit();
        nForm.remove();
    }

    if ( asErrors.length === 0 ) {
        create_and_submit_form();

    } else {
        this._fnShowErrors( 'The following problems prevent exporting:',
            asErrors, create_and_submit_form);
    }
};

/*
* Function: _fnGetId
* Purpose:  Get the current URL id and returns it, null if not set.
* Input(s): void
* Returns:  string:sId - the current URL id
*
*/
Authorlist.prototype._fnGetId = function() {
    var idMatch = window.location.search.match( Authorlist.ID );
    return idMatch === null ? null : idMatch[ 1 ];
};

Authorlist.prototype._fnProgress = function() {
    var nBody = jQuery( 'body' );
    var nLoading = jQuery( '<div>' );

    nLoading.html( 'Loading...' );
    nLoading.addClass( Authorlist.CSS.Loading );
    nLoading.addClass( Authorlist.CSS.Active );
    nLoading.appendTo( nBody );
    nLoading.css( 'margin-left', -1 * nLoading.outerWidth() / 2 );

    nBody.addClass( Authorlist.CSS.Progress );
};

/*
* Function: _fnProgressDone
* Purpose:  Remove the progressing cursor from the body and the loading bar on 
*           the upper 
* Input(s): string:sId - the paper id to be loaded
* Returns:  void
*
*/
Authorlist.prototype._fnProgressDone = function() {
    var nBody = jQuery( 'body' );

    nBody.removeClass( Authorlist.CSS.Progress );
    nBody.find( '.' + Authorlist.CSS.Loading ).remove();
};

/*
* Function: _fnRetrieve
* Purpose:  Retrieves the data of the given paper id from the server an sets 
*           them on success as the preset values of the table or shows an error 
*           if a failure occures.
* Input(s): string:sId - the paper id to be loaded
* Returns:  void
*
*/
Authorlist.prototype._fnRetrieve = function( sId ) {
    var self = this;
    var sURL = Authorlist.URLS.Load + ( sId !== null ? '&id=' + sId : '');

    this._fnProgress();
    jQuery.ajax( {
        'type'    : 'GET',
        'url'     : sURL,
        'success' : function( oData ) {
            self.fnLoadData( oData );
            self._fnProgressDone();
        },
        'error'   : function() {
            var sPreamble = 'Could not retrieve data from server:';
            self._fnProgressDone();
            self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
        }
    } );
};

/*
* Function: _fnSave
* Purpose:  Saves the data of the authorlist instance on the server as long as 
*           there are no errors, which will be displayed in a dialog otherwise.
* Input(s): void
* Returns:  void
*
*/
Authorlist.prototype._fnSave = function() {
    var oData = this.fnGetData();
    var asErrors = this.fnValidate( oData );
    var self = this;

    // Function responsible for sending ajax request with data
    function send_ajax_request_to_save() {
        sURL = Authorlist.URLS.Save;
        // Append the id of this sheet to the save URL if present
        sURL += self._sId !== null ? '&id=' + self._sId : '';

        self._fnProgress();
        // Post the data to the server and save the new id on success
        jQuery.ajax( {
            'type'    : 'POST',
            'url'     : sURL,
            'data'    : { 'data' : JSON.stringify( oData ) },
            'success' : function( oData ) {
                self._fnProgressDone();
                self._sId = oData.paper_id;
            },
            'error'   : function() {
                var sPreamble = 'Could not save data on the server:';
                self._fnProgressDone();
                self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
            }
        });
    }

    if ( asErrors.length === 0 ) {
        send_ajax_request_to_save();
    } else {
        // Errors ? Show a message but still allow to save data
        this._fnShowErrors( 'The following errors prevent saving:',
            asErrors, send_ajax_request_to_save);
    }
};

/*
* Function: _fnShowErrors
* Purpose:  Opens up a modal dialog box that presents all missing information/
*           errors in the passed asErrors array in a bullet point list.
* Input(s): array string:asErrors - the error messages array
* Input(s): function:fnCallback - if a function is specified, error dialog
                                  window will have a button that allows to
                                  ignore errors and execute thatfunction anyway
* Returns:  void
*
*/
Authorlist.prototype._fnShowErrors = function( sPreamble, asErrors, fnCallback) {
    var nDialog = jQuery( '<div>' );
    var nError = jQuery( '<p>' );
    var nErrorIcon = jQuery( '<span>' );
    var nErrorText = jQuery( '<span>' );
    nErrorText.html( sPreamble );
    // Define button object for jQuery Dialog
    var buttons = {};
    // Check if the callback function is specified
    var callback = '';
    if (typeof fnCallback === 'function') {
        buttons["I know what I'm doing, I want to continue anyway"] = function () {
            fnCallback();
            jQuery( this ).remove();
        };
    }
    // Close button should always exist in the Dialog
    buttons['Close'] = function() { jQuery( this ).remove(); };

    // Add CSS classes
    nDialog.addClass( Authorlist.CSS.Error );
    nError.addClass( Authorlist.CSS.ErrorTitle );
    nErrorIcon.addClass( Authorlist.CSS.Icon ).addClass( Authorlist.CSS.ErrorIcon );
    nDialog.append( nError.append( nErrorIcon, nErrorText ) );

    // Create each individual message
    asErrors.forEach( function( sError ) {
        var nBullet = jQuery( '<p>' );
        var nBulletIcon = jQuery( '<span>' );
        var nBulletText = jQuery( '<span>' + sError + '</span>' );

        nBullet.addClass( Authorlist.CSS.Bullet );
        nBulletIcon.addClass( Authorlist.CSS.Icon );
        nBulletIcon.addClass( Authorlist.CSS.BulletIcon );
        nBulletText.addClass( Authorlist.CSS.BulletText );

        nDialog.append( nBullet.append( nBulletIcon, nBulletText ) );
    } );
    nDialog.appendTo( jQuery( 'body' ) );

    // Instantiate a jQuery UI dialog widget
    nDialog.dialog( {
        'modal'       : true,
        'resizable'   : false,
        'title'       : 'Error',
        'width'       : '33%',
        'maxWidth'    : '50%',
        'dialogClass' : Authorlist.CSS.Dialog,
        'buttons'     : buttons
    } );
};

/*
* Function: _fnValidateAffiliations
* Purpose:  Validates a subset - namely the affiliations - of the whole data of 
*           the fnGetData() call in fnValidate. It makes sure that all acronyms 
*           and names/addresses of an affiliation is set. At the same time it 
*           generates errors messages if this is not the case and appends them 
*           to the passed error messages array.
* Input(s): array array object:aaoAffiliations - the affiliations data entry
*           array string:asErrors - the error messages array
* Returns:  array string:asAcronyms - an array containing the valid affiliation 
                                      acronyms; used in _fnValidateAuthors()
*
*/
Authorlist.prototype._fnValidateAffiliations = function( aaoAffiliations, asErrors ) {
    var asAcronyms = [];
    var asMissingAcronyms = [];
    var asMissingAddresses = [];
    var asDuplicateAcronyms = [];

    aaoAffiliations.forEach( function( aoAffiliation ) {
        var sIndex = aoAffiliation[ Authorlist.INDICES.Index ];
        var sAcronym = aoAffiliation[ Authorlist.INDICES.Acronym ];
        var sAddress = aoAffiliation[ Authorlist.INDICES.Address ];

        // If acronym field is empty save it in missing acronyms, otherwise save 
        // it in present acronyms
        var bAcronymEmpty = sAcronym.match( Authorlist.EMPTY ) !== null;
        if ( bAcronymEmpty ) {
            asMissingAcronyms.push( sIndex );
        } else if ( asAcronyms.indexOf(sAcronym) > -1 ) {
            asDuplicateAcronyms.push ( sAcronym + '(line ' + sIndex + ')' );
        } else {
            asAcronyms.push( sAcronym );
        }

        // If address field is not set remember the index
        var bAddressEmpty = sAddress.match( Authorlist.EMPTY ) !== null;
        if ( bAddressEmpty ) asMissingAddresses.push( sIndex );
    } );

    // Create error messages
    if ( asMissingAcronyms.length > 0 ) {
        var sAcronymsError = 'Affiliation acronym <strong>missing</strong> in line(s): ';
        sAcronymsError += '<strong>' + asMissingAcronyms.join( ', ' ) + '</strong>';
        asErrors.push(  sAcronymsError  );
    }

    if ( asMissingAddresses.length > 0 ) {
        var sAddressesError = 'Affiliation name and address <strong>missing</strong> in line(s): ';
        sAddressesError += '<strong>' + asMissingAddresses.join( ', ' ) + '</strong>';
        asErrors.push( sAddressesError  );
    }

    if ( asDuplicateAcronyms.length > 0 ) {
        var sDuplicateAcronymError = '<strong>Duplicated</strong> acronyms: ';
        sDuplicateAcronymError += '<strong>' + asDuplicateAcronyms.join( ', ' ) + '</strong>';
        asErrors.push( sDuplicateAcronymError  );
    }

    // Return acronyms, which can be used later in the author validation
    return asAcronyms;
};

/*
* Function: _fnValidateAuthors
* Purpose:  Validates a subset - namely the authors - of the whole data of the 
*           fnGetData() call in fnValidate. It makes sure that all paper names 
*           and affiliations are present and linkable. At the same time it 
*           generates errors messages if this is not the case and appends them 
*           to the passed error messages array.
* Input(s): array array object:aaoAuthors - the authors data entry
            array string:asErrors - the error messages array
* Returns:  void
*
*/
Authorlist.prototype._fnValidateAuthors = function( aaoAuthors, asAcronyms, asErrors ) {
    var asMissingNames = [];
    var asUnknownAcronyms = [];
    // Real copy of asAcronyms
    var asUnusedAcronyms = asAcronyms.slice();

    aaoAuthors.forEach( function( aoAuthor ) {
        var sIndex = aoAuthor[ Authorlist.INDICES.Index ];
        var sName = aoAuthor[ Authorlist.INDICES.AuthorName ];
        var aasAffiliations = aoAuthor[ Authorlist.INDICES.Affiliations ];

        // Name is empty? Remember the line
        if ( sName.match( Authorlist.EMPTY ) !== null ) {
            asMissingNames.push( sIndex );
        }

        // An affiliation ancronym could not be found in the affiliations table?
        aasAffiliations.forEach( function( asAffiliation ) {
            var sAffName = asAffiliation[ Authorlist.INDICES.AffiliationName ];
            if ( asAcronyms.indexOf( sAffName ) < 0 ) {
                asUnknownAcronyms.push( sAffName );
            }
            asUnusedAcronyms.remove( sAffName );
        } );
    } );

    // If missing names are present append them to the error messages array
    if ( asMissingNames.length > 0 ) {
        var sNamesError = 'Author paper name <strong>missing</strong> in line(s) ';
        sNamesError += '<strong>' + asMissingNames.join( ', ' ) + '</strong>';
        asErrors.push( sNamesError );
    }

    // If unknown are acronyms were found push them in the error messages array
    if ( asUnknownAcronyms.length > 0 ) {
        var sAcronymsError = '<strong>Unknown</strong> affiliation acronyms: ';
        sAcronymsError += '<strong>' + asUnknownAcronyms.join( ', ' ) + '</strong>';
        asErrors.push( sAcronymsError );
    }

    // Acronyms that are unused in the affiliations table
    if ( asUnusedAcronyms.length > 0 ) {
        var sUnusedError = '<strong>Unused</strong> acronyms: ';
        sUnusedError += '<strong>' + asUnusedAcronyms.join( ', ' ) + '</strong>';
        asErrors.push( sUnusedError );
    }
};

/*
* Function: _fnValidateUmbrellas
* Purpose:  Validates a subset - namely the umbrella organizatons - of the whole
*           data as retrieved by the fnGetData() call in fnValidate. It ensures 
*           that each umbrella acronym is present in the list of all acronyms.
*           Otherwise is generates a error message and appends it to the error 
*           messages array. 
* Input(s): array array object:aaoAffiliations - the affiliations data entry
*           array string:asAcronyms - an array containing all the acronyms in 
*                                     the affiliations table
*           array string:asErrors - the error messages array
* Returns:  void
*
*/
Authorlist.prototype._fnValidateUmbrellas = function( aaoAffiliations, asAcronyms, asErrors ) {
    var asInvalidUmbrellas = [];

    aaoAffiliations.forEach( function( aoAffiliation ) {
        var sIndex = aoAffiliation[ Authorlist.INDICES.Index ];
        var sUmbrella = aoAffiliation[ Authorlist.INDICES.Umbrella ];
        var bNotEmpty = sUmbrella.match( Authorlist.EMPTY ) === null;

        // Umbrella string not empty and not in the acronyms? Record that!
        if ( bNotEmpty && asAcronyms.indexOf( sUmbrella ) < 0 ) {
            asInvalidUmbrellas.push( sIndex );
        }
    } );

    // Invalid umbrellas present? 
    if ( asInvalidUmbrellas.length > 0 ) {
        var sInvalidError = '<strong>Unknown</strong> umbrella organization in line(s): ';
        sInvalidError += '<strong>' + asInvalidUmbrellas.join( ',' ) + '</strong>';
        asErrors.push( sInvalidError );
    }
};









/*

* Variable: AuthorlistIndex.TO_MILLIS
* Purpose:  Factor to convert seconds timestamp to milliseconds
*
*/
AuthorlistIndex.TO_MILLIS = 1000;

/*
* Variable: AuthorlistIndex.CSS
* Purpose:  Central enumeration and mapping for the CSS classes used in the 
*           AuthorlistIndex prototype. Eases consistent look up and renaming if 
*           required.

*
*/
AuthorlistIndex.CSS = {
    'AuthorlistIndex'   : 'AuthorlistIndex',
    'Detail'            : 'AuthorlistIndexDetail',
    'DetailLabel'       : 'AuthorlistIndexDetailLabel',
    'EditLink'          : 'AuthorlistIndexEditLink',
    'Link'              : 'AuthorlistIndexLink',
    'Paper'             : 'AuthorlistIndexPaper',
    'PaperTitle'        : 'AuthorlistIndexPaperTitle',
    'New'               : 'AuthorlistIndexNew',
    'NewIcon'           : 'ui-icon-document',
    'Seperator'         : 'AuthorlistIndexSeperator',
    'Timestamp'         : 'AuthorlistIndexTimestamp',
    'URL'               : 'AuthorlistIndexURL'
};









/*

* Function: AuthorlistIndex
* Purpose:  Constructor
* Input(s): string:sId - Id of the html element the AuthorlistIndex will be 
*                        embedded into (preferably a div).
* Returns:  AuthorlistIndex instance when called with new, else undefined
*

*/
function AuthorlistIndex( sId ) {
    this._nParent = jQuery( '#' + sId );
    this._nParent.addClass( AuthorlistIndex.CSS.AuthorlistIndex );

    this._fnRetrieve( this._nParent );
}

AuthorlistIndex.prototype._fnConfirm = Authorlist.prototype._fnConfirm;
AuthorlistIndex.prototype._fnCreateButton = Authorlist.prototype._fnCreateButton;

/*
* Function: _fnCloneClicked
* Purpose:  Defines the callback for clicking on a clone link on a respective 
*           paper container. Sends a request to the server to clone the paper 
*           and displays it in the list on success or outputs an error.
* Input(s): node:nParent - the paper container of the clicked clone link
*           string:sId - the id of the clicked paper
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnCloneClicked = function( nPaper, sId ) {
    var self = this;

    // Go into progress mode
    this._fnProgress();
    // Make a request to clone the paper and display it, or show errors
    jQuery.ajax( {
        'type'    : 'POST',
        'url'     : Authorlist.URLS.Clone + '&id=' + sId,
        'success' : function( oData ) {
            self._fnProgressDone();
            self._fnDisplayClonedPaper( nPaper, oData );
        },
        'error'   : function() {
            var sPreamble = 'Could not clone paper:';
            self._fnProgressDone();
            self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
        }
    } );
};

/*
* Function: _fnCreatePaper
* Purpose:  Creates a single paper record node based on the data passed in the 
*           oPaper object. 
* Input(s): string:sLabel - label string
*           string:sDetail - the detail string
* Returns:  node:nWrapper - the paper detail node
*
*/
AuthorlistIndex.prototype._fnCreateEditLinks = function( nParent, sId ) {
    var self = this;

    // Clone link
    var nClone = jQuery( '<a>' );
    nClone.html( 'Clone' );
    nClone.addClass( AuthorlistIndex.CSS.EditLink );
    nClone.click( function() { self._fnCloneClicked( nParent, sId ); } );

    // Small cube to separate both links
    var nSeperator = jQuery( '<span>' );
    nSeperator.addClass( AuthorlistIndex.CSS.Seperator );

    // Delete link
    var nDelete = jQuery( '<a>' );
    nDelete.html( 'Delete' );
    nDelete.addClass( AuthorlistIndex.CSS.EditLink );
    nDelete.click( function() { self._fnDeleteClicked( nParent, sId ); } );

    nParent.append( nClone, nSeperator, nDelete );
};

/*
* Function: _fnCreateNewButton
* Purpose:  Creates the new button that allows users to create a new document. 
*           Refers the user to a clean new sheet. The button is placed on the 
*           passed parent element.
* Input(s): node:nParent - the parent node
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnCreateNewButton = function( nParent ) {
    var self = this;
    var nNewButton = this._fnCreateButton( nParent, 'New',
                                           AuthorlistIndex.CSS.NewIcon );

    nNewButton.addClass( AuthorlistIndex.CSS.New );
    nNewButton.click( function() {
        self._fnProgress();
        window.location.href = Authorlist.URLS.Open;
    } );
    nNewButton.appendTo( nParent );
};

/*
* Function: _fnCreatePaper
* Purpose:  Creates a single paper record node based on the data passed in the 
*           oPaper object. 
* Input(s): string:sLabel - label string
*           string:sDetail - the detail string
* Returns:  node:nWrapper - the paper detail node
*
*/
AuthorlistIndex.prototype._fnCreatePaper = function( oPaper ) {
    var self = this;
    var nPaper = jQuery( '<div>' ).addClass( AuthorlistIndex.CSS.Paper );
    var sURL = Authorlist.URLS.Open + '&id=' + oPaper.paper_id;
    var oTime = new Date( oPaper.last_modified * AuthorlistIndex.TO_MILLIS );
    var sTime = oTime.toLocaleDateString() + ' ' + oTime.toLocaleTimeString();
    var sLabel = '';
    var sExperiment;


    // create the link
    var nLink = jQuery( '<a>' );
    nLink.attr( 'href', sURL );
    nLink.html( oPaper.paper_title );
    nLink.addClass( AuthorlistIndex.CSS.PaperTitle );
    nLink.click( function() { self._fnProgress(); } );

    // create the time stamp
    var nTimestamp = jQuery( '<span>' );
    nTimestamp.html( 'Last Modified: ' + sTime );
    nTimestamp.addClass( AuthorlistIndex.CSS.Timestamp );

    // create link label
    var nURL = jQuery( '<span>' );
    nURL.html( sURL );
    nURL.addClass( AuthorlistIndex.CSS.URL );

    // add the information
    nPaper.append( nLink, nTimestamp );

    // present collaboration/experiment number only if present
    if ( oPaper.collaboration ) {
        sLabel = 'Collaboration:';
        sCollaboration = oPaper.collaboration;
        nPaper.append( this._fnCreatePaperDetail( sLabel, sCollaboration ) );
    }
    if ( oPaper.experiment_number ) {
        sLabel = 'Experiment Number:';
        sExperiment = oPaper.experiment_number;
        nPaper.append( this._fnCreatePaperDetail( sLabel, sExperiment ) );
    }
    // if there is no collaboration and experiment number, at least put <br />
    if ( ! oPaper.experiment_number && ! oPaper.experiment_number ) {
        nPaper.append('<br />');
    }

    // add the link as last item
    nPaper.append( nURL );
    this._fnCreateEditLinks( nPaper, oPaper.paper_id );

    return nPaper;
};

/*
* Function: _fnCreatePaperDetail
* Purpose:  Creates a paper detail consisting of a label as defined in the 
*           string sLabel with the values sDetail
* Input(s): string:sLabel - label string
*           string:sDetail - the detail string
* Returns:  node:nWrapper - the paper detail node
*

*/
AuthorlistIndex.prototype._fnCreatePaperDetail = function( sLabel, sDetail ) {
    var nWrapper = jQuery( '<div>' );
    var nLabel = jQuery( '<span>' ).html( sLabel );
    var nDetail = jQuery( '<span>' ).html( sDetail );

    nLabel.addClass( AuthorlistIndex.CSS.DetailLabel );
    nDetail.addClass( AuthorlistIndex.CSS.Detail );
    nWrapper.append( nLabel, nDetail );

    return nWrapper;
};

/*
* Function: _fnDeleteClicked
* Purpose:  Defines the callback for clicking a delete link. On confirmation by 
*           the user a request is sent a request to the server to delete the 
*           paper. Afterwards the paper is removed from the list of all papers. 
*           If an error occurs during the communication an error message is 
*           displayed instead.
* Input(s): node:nParent - the paper container where the delete link was clicked
*           string:sId - the id of the clicked paper
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnDeleteClicked = function( nPaper, sId ) {
    var self = this;

    this._fnConfirm( function() {
        // Go into progress mode
        self._fnProgress();

        // Make request to delete the paper and update view or display errors.
        jQuery.ajax( {
            'type'    : 'POST',
            'url'     : Authorlist.URLS.Delete + '&id=' + sId,
            'success' : function() {
                self._fnProgressDone();
                self._fnRemovePaper( nPaper );
            },
            'error'   : function() {
                var sPreamble = 'Could not delete paper:';
                self._fnProgressDone();
                self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
            }
        } );
    } );
};

/*
* Function: _fnDisplay
* Purpose:  Displays each of the passed papers in the oData object on the 
*           nParent element.
* Input(s): object:oData - the object containing all papers
*           node:nParent - the element to display the papers on
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnDisplay = function( oData, nParent ) {
    var oPapers = oData.data;

    // No records available? Display a short note telling this
    if ( oPapers.length === 0 ) {
        this._fnDisplayEmptyDatabase( nParent );
        return;
    }

    // Records available? Display them
    var nPapers = jQuery( '<div>' );
    for ( var i = 0, iLen = oPapers.length; i < iLen; i++ ) {
        var nPaper = this._fnCreatePaper( oPapers[ i ] );
        nPapers.append( nPaper );
    }
    nPapers.appendTo( nParent );
};

/*
* Function: _fnDisplayClonedPaper
* Purpose:  Displays a new paper that is added to the list of all papers on the 
*           front page
* Input(s): node:nParent - the node containing the to be cloned paper
*           object:oData - the data of the newly cloned paper
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnDisplayClonedPaper = function( nParent, oData ) {
    var nContainer = nParent.parent();
    nContainer.prepend( this._fnCreatePaper( oData ) );
};

/*
* Function: _fnDisplayEmptyDatabase
* Purpose:  Gives a short note to the user that there are no records in the 
*           database and therefore nothing else can be displayed.
* Input(s): node:nParent - the node indicating where to display the message
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnDisplayEmptyDatabase = function( nParent ) {
    var nEmpty = jQuery( '<div>' );

    nEmpty.html( 'No records in the database.' );
    nEmpty.addClass( AuthorlistIndex.CSS.Paper );
    nEmpty.appendTo( nParent );
};

/*
* Functions: _fnProgress and _fnProgressDone
* Purpose:   Method to display standard loading indicators like authorlist does.
*            Look up these methods there please.
*
*/
AuthorlistIndex.prototype._fnProgress = Authorlist.prototype._fnProgress;
AuthorlistIndex.prototype._fnProgressDone = Authorlist.prototype._fnProgressDone;

/*
* Function: _fnRemovePaper
* Purpose:  Removes a paper from the list of all papers on the landing page.
* Input(s): node:nParent - the individual paper container
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnRemovePaper = function( nParent ) {
    var nContainer = nParent.parent();
    nParent.remove();
    var nPapers = nContainer.find('.' + AuthorlistIndex.CSS.Paper);
    // Container becomes empty? Display that there are no records
    if ( nPapers.length === 0 ) {
        this._fnDisplayEmptyDatabase( nContainer );
    }
};

/*
* Function: _fnRetrieve
* Purpose:  Retrieves all available papers from the database and displays them 
*           nicely on the webpage on success.
* Input(s): node:nParent - the parent element where to display the records
* Returns:  void
*
*/
AuthorlistIndex.prototype._fnRetrieve = function( nParent ) {
    var self = this;

    this._fnProgress();
    jQuery.ajax( {
        'type'    : 'GET',
        'url'     : Authorlist.URLS.Itemize,
        'success' : function( oData ) {
            self._fnProgressDone();
            self._fnDisplay( oData, nParent );
            self._fnCreateNewButton( nParent );
        },
        'error'   : function() {
            var sPreamble = 'Cannot display all papers:';
            self._fnProgressDone();
            self._fnShowErrors( sPreamble, Authorlist.DEFAULT_ERROR );
        }
    } );
};

/*
* Function: _fnShowErrors
* Purpose:  Method to display standard errors. We are doing the same as author-
*           list would do here, so please look it up there
*
*/
AuthorlistIndex.prototype._fnShowErrors = Authorlist.prototype._fnShowErrors;









/*
* Function: Paper
* Purpose:  Constructor
* Input(s): string:sId - Id of the html element the Paper will be embedded
*                        into (preferably a div).
* Returns:  Paper instance when called with new, else undefined
*
*/
function Paper( sId ) {
    this._nParent = jQuery( '#' + sId );

    this._nPaper = this._fnCreateInput( 'Paper Title (*)' );
    this._nCollaboration = this._fnCreateInput( 'Collaboration (*)' );
    this._nExperimentNumber = this._fnCreateInput( 'Experiment Number' );
    this._nReference = this._fnCreateInput( 'Reference Id(s)', Authorlist.CSS.Reference + '0' );
    this._fnCreateButtons( this._nReference);

    this._nParent.append( this._nPaper, this._nCollaboration,
                          this._nExperimentNumber, this._nReference );
}

/*
* Function: fnGetData
* Purpose:  Retrieves the paper information in a further processable form. EMPTY
*           lines in the reference ids will NOT BE in the result.
* Input(s): void
* Returns:  object:oResult - an object containing the paper information
*
*/
Paper.prototype.fnGetData = function() {
    var oResult = {};
    var sSelector = '.' + Authorlist.CSS.Input;

    oResult.paper_title = this._nPaper.find( sSelector ).val();
    oResult.collaboration = this._nCollaboration.find( sSelector ).val();
    oResult.experiment_number = this._nExperimentNumber.find( sSelector ).val();
    oResult.reference_ids = [];

    this._nReference.find( sSelector ).each( function( iIndex, nInput ) {
        var sValue = jQuery( nInput ).val();

        // Skip empty elements
        if ( sValue.match( Authorlist.EMPTY ) !== null ) return true;
        oResult.reference_ids.push( sValue );
    } );

    return oResult;
};

/*
* Function: fnLoadData
* Purpose:  Loads data from the passed object (same layout as generated in 
*           fnGetData()) as the preset values
* Input(s): object:oData - the fnGetData()-like load object
* Returns:  void
*
*/
Paper.prototype.fnLoadData = function( oData ) {
    var sSelector = '.' + Authorlist.CSS.Input;

    this._nPaper.find( sSelector ).val( oData.paper_title );
    this._nCollaboration.find( sSelector ).val( oData.collaboration );
    this._nExperimentNumber.find( sSelector ).val( oData.experiment_number );

    var nAddButton = this._nReference.find( '.' + Authorlist.CSS.Add );
    for ( var i = 0, iLen = oData.reference_ids.length; i < iLen; i++ ) {
        if ( i > 0 ) nAddButton.click();

        var nInput = this._nReference.find( sSelector ).eq( i );
        nInput.val( oData.reference_ids[ i ] );
    }
};

/*
* Function: _fnCreateButtons
* Purpose:  Do the same thing as authorlist does here
*
*/
Paper.prototype._fnCreateButton = Authorlist.prototype._fnCreateButton;

/*
* Function: _fnCreateButtons
* Purpose:  Creates the add and remove buttons next to the passed parent and 
*           assigns callbacks to them.
* Input(s): node:nParent - the parent node to which to append the buttons
* Returns:  void
*
*/
Paper.prototype._fnCreateButtons = function( nParent ) {
    // Create button elements
    var nAddButton = this._fnCreateButton( nParent, 'Add', Authorlist.CSS.AddIcon );
    var nRemoveButton = this._fnCreateButton( nParent, 'Remove', Authorlist.CSS.RemoveIcon );

    // Add classes
    nAddButton.addClass( Authorlist.CSS.Add );
    nRemoveButton.addClass( Authorlist.CSS.Remove );

    // Register callbacks for add and remove action
    var self = this;
    nAddButton.click( function() {
        // Just create a new input line with no title
        var iInputs = nParent.find( '.' + Authorlist.CSS.Input ).length;
        nParent.append( self._fnCreateInput ( '', Authorlist.CSS.Reference + iInputs ) );
    } );
    nRemoveButton.click( function() {
        var iInputs = nParent.find( '.' + Authorlist.CSS.Input ).length;

        // Delete the last input as long as there will be one line remaining
        if ( iInputs <= 1 ) return;
        nParent.children().last().remove();
    } );
};


/*
* Function: _fnCreateInput
* Purpose:  Creates a label and input element combination and returns it.
* Input(s): string:sTitle - the title/label string of the field
*           string:sId - the id that the input field will get
* Returns:  node:nWrapper - a element containing the label and input field
*
*/
Paper.prototype._fnCreateInput = function( sTitle, sId ) {
    if ( typeof sId === 'undefined' ) sId = sTitle.replace( / /g, '' );

    var nWrapper = jQuery( '<div>' );
    var nLabel = jQuery( '<label for="' + sId + '">' + sTitle + '</label>' );
    nLabel.addClass( Authorlist.CSS.Label );
    var nInput = jQuery( '<input id="' + sId + '">' );
    nInput.addClass( Authorlist.CSS.Input );

    return nWrapper.append( nLabel, nInput );
};
