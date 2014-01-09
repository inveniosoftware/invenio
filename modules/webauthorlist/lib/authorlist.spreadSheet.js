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
* Variable: SpreadSheet.CSS
* Purpose:  Central enumeration and mapping for the CSS classes used in the 
*           SpreadSheet module. Eases consistent look up and renaming if 
*           required.
*
*/
SpreadSheet.CSS = {
    // General classes
    'SpreadSheet'           : 'SpreadSheet',
    'DataTable'             : 'DataTable',
    
    // Cursor classes
    'Cursor'                : 'Cursor',
    'CursorTop'             : 'CursorTop',
    'CursorRight'           : 'CursorRight',
    'CursorBottom'          : 'CursorBottom',
    'CursorLeft'            : 'CursorLeft',
    'CursorCube'            : 'CursorCube',
    
    // Cell classes
    'Wrapper'               : 'Wrapper',
    'Content'               : 'Content',
    'Clickable'             : 'Clickable',
    'Focus'                 : 'Focus',
    
    // Content class
    'Text'                  : 'Text',
    'Edit'                  : 'Edit',
    'Increment'             : 'Increment',
    'Select'                : 'Select',
    'Checkbox'              : 'Checkbox',
    'TextSelect'            : 'TextSelect',
    'TextSelectText'        : 'TextSelectText',
    'TextSelectSelect'      : 'TextSelectSelect',
    
    'Extendable'            : 'Extendable',
    'Readonly'              : 'Readonly',
    
    // jQuery UI classes
    'Default'               : 'ui-state-default',
    'Active'                : 'ui-state-active',
    'Hover'                 : 'ui-state-hover',
    'Icon'                  : 'ui-icon',
    'Plus'                  : 'ui-icon-plus',
    'Minus'                 : 'ui-icon-minus',
    'Up'                    : 'ui-icon-carat-1-n',
    'Down'                  : 'ui-icon-carat-1-s',
    'Delete'                : 'ui-icon-close',
    'Checked'               : 'ui-icon-check',
    'Unchecked'             : 'ui-icon-closethick'
}









/*
* Function: SpreadSheet.Column
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetColumn instance when called with new, else undefined
*
*/
SpreadSheet.Column = function( oInit ) {
    if ( typeof oInit === 'undefined' ) return this;
    
    // Set the properties of the columns to the passed values or the sane 
    // defaults. DO NOT change their names as they will be passed directly to 
    // the DataTables instance and have to HAVE this FORMAT. For more details 
    // see the jQuery DataTables online documentation.
    
    // objects
    this.oSpreadSheet = oInit.oSpreadSheet;
    
    // strings
    this.sClass = [ oInit.sType, SpreadSheet.CSS.Clickable ].join( ' ' );
    this.sTitle = typeof oInit.title === 'string' ? oInit.title : '';
    this.sType = oInit.sType;
    this.sValue = oInit.value || '';
    this.sWidth = oInit.width || null;
    
    // booleans
    this.bExtendable = oInit.extendable || false;
    this.bProtected = oInit.readonly || false;
    this.bSearchable = typeof oInit.searchable !== 'undefined' ? oInit.searchable : true;
    this.bSortable = typeof oInit.sortable !== 'undefined' ? oInit.sortable : true;
    this.bVisible = typeof oInit.visible !== 'undefined' ? oInit.visible : true;
    
    // callbacks
    var oSort = jQuery.fn.dataTableExt.oSort;    
    oSort[ this.sType + '-asc' ] = this._fnMakeAscendingSorting();
    oSort[ this.sType + '-desc' ] = this._fnMakeDescendingSorting();
    jQuery.fn.dataTableExt.ofnSearch[ this.sType ] = this._fnMakeFilter();
    this._fnRegisterClicks();
}

/*
* Function: fnCompare
* Purpose:  Generic javascript-style compare function that is able to compare 
*           two cells that belong to this column. In case that the column is 
*           of type extendable, we will convert the value of the cell - i.e. 
*           an array to a string first, to allow a more or less meaningful 
*           sorting.
* Input(s): object:oA - the left hand value as string, DOM element or jQuery set
*           object:oA - the right hand value as string, ...
* Returns:  integer:iCompare - the javascript-style comparison value
*
*/
SpreadSheet.Column.prototype.fnCompare = function( oA, oB ) {
    var a = this.fnValue( oA );
    var b = this.fnValue( oB );
    
    if ( this.bExtendable ) {
        a = a.toString();
        b = b.toString();
    }
    
    return a < b ? -1 : ( a > b ? 1 : 0 );
}

/*
* Function: fnCreate
* Purpose:  Creates a new cell of this column with all values set to default.
* Input(s): node:nNode - the node to be serialized
* Returns:  string:sInnerHtml - the serialized html of the node
*
*/
SpreadSheet.Column.prototype.fnCreate = function( oValue ) {
    // Extendable cells expect arrays as value
    if ( this.bExtendable && typeof oValue === 'undefined' ) oValue = [oValue];

    var nWrapper = jQuery( '<div>' ).addClass( SpreadSheet.CSS.Wrapper );
    // Not extendable? then return one cell only
    if ( !this.bExtendable ) {
        var nContent = jQuery( '<div>' ).addClass( SpreadSheet.CSS.Content );
        
        var nCell = this._fnCreateCell( oValue );
        nContent.append( nCell );
        nWrapper.append( nContent );
        
        return this.fnOuterHtml( nWrapper );
    }

    // Is extendable? Some layouting and buttons are required...
    // Create the cell as table. I am scared to say this, but we need it for
    // layouting reasons. For details google for 'input width display block'
    var nTable = jQuery( '<table>' ).addClass( SpreadSheet.CSS.Content );

    for ( var i = 0, iLen = oValue.length; i < iLen; i++ ) {
        // Create the table row    
        var nTableRow = jQuery( '<tr>' ).appendTo( nTable );
        // Create cell content
        var sContent = this._fnCreateCell( oValue[ i ] );
        var nCell = jQuery( '<td>' ).append( sContent ).appendTo( nTableRow );
        // Create buttons
        var nButtons = jQuery( '<td>' ).addClass( SpreadSheet.CSS.Extendable );        
        // Have the add button only in the first row
        if ( i === 0 ) {
            nButtons.append( this._fnCreateExtendable() ).appendTo( nTableRow );
        }
    }
    nWrapper.append( nTable );
    return this.fnOuterHtml( nWrapper );
}

/*
* Function: fnDeleteLine
* Purpose:  Removes a line at the end of the given input cell and saves the 
*           result in the respective DataTable instance. This is only done as 
*           long as there are at least two cells in the table.
* Input(s): node:nCell - the cell to be modified
* Returns:  void
*
*/
SpreadSheet.Column.prototype.fnDeleteLine = function( nCell ) {
    var aoValues = this.fnValue( nCell );
    
    // Can we remove an element - i.e. at least two in there?
    if ( aoValues.length > 1 ) {
        aoValues = aoValues.slice( 0, aoValues.length - 1 );
        this.oSpreadSheet.fnUpdate( nCell, this.fnCreate( aoValues ) );
    }
}

/*
* Function: fnIsDefault
* Purpose:  Checks whether the given value equals to a default cell of this 
*           column.
* Input(s): string:sValue - the value to be checked
* Returns:  boolean:bEqual - truth value indicating equality to the default
*
*/
SpreadSheet.Column.prototype.fnIsDefault = function( sValue ) {
    if ( !this.bExtendable ) return sValue === this.sValue;
    
    for ( var i = 0, iLen = sValue.length; i < iLen; i++ ) {
        if ( sValue[ i ] !== this.sValue ) return false;
    }
    return true;
}

/*
* Function: fnInsertNewLine
* Purpose:  Inserts a new default line at the end of the given cell and saves it
*           in the DataTable instance.
* Input(s): node:nCell - the DOM element or jQuery of the cell to be modified
* Returns:  void
*
*/
SpreadSheet.Column.prototype.fnInsertNewLine = function( nCell ) {
    var aoValues = this.fnValue( nCell );
    
    // Insert a new default value
    aoValues.push( this.sValue );
    this.oSpreadSheet.fnUpdate( nCell, this.fnCreate( aoValues ) );
}

/*
* Function: fnKeyin
* Purpose:  Function to be executed when a cell gets a 'keyin' event. This event
*           is a custom invention to support cell focusing when a user interacts
*           with the sheet using the keyboard.
* Input(s): node:nCell - the cell getting the keyin event
* Returns:  void
*
*/
SpreadSheet.Column.prototype.fnKeyin = function( nCell ) {
    var sInput = [ 'input', this.sType, SpreadSheet.CSS.Text ].join( '.' );
    var nInput = jQuery( nCell ).find( sInput ).last();
    
    nInput.click();
}

/*
* Function: fnKeyout
* Purpose:  Function to be executed when a cell gets a 'keyout' event. It is a
*           custom invention to support cell defocusing when a user interacts
*           with the sheet using the keyboard and is about to leave a cell.
* Input(s): node:nCell - the cell getting the keyout event
* Returns:  void
*
*/
SpreadSheet.Column.prototype.fnKeyout = function( nCell ) {
    var sInput = [ 'input', this.sType, SpreadSheet.CSS.Text ].join( '.' );
    var nInput = jQuery( nCell ).find( sInput );
    
    nInput.blur();
}

/*
* Function: fnOuterHtml
* Purpose:  Transforms a DOM or jQuery node into its serialized HTML version.
* Input(s): node:nNode - the node to be serialized
* Returns:  string:sOuterHtml - the serialized html of the node
*
*/
SpreadSheet.Column.prototype.fnOuterHtml = function( nNode ) {
    var nDummy = jQuery( '<div>' );
    nDummy.append( jQuery( nNode ).clone() );
    
    return nDummy.html();
}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way - 
*           meaning it returns a simple string or in case of an extendable cell 
*           an array with each value.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  string|array string:oValue - the value of the cell
*
*/
SpreadSheet.Column.prototype.fnValue = function( oData ) {
    var anCells = jQuery( 'input.' + SpreadSheet.CSS.Text, jQuery( oData ) );
    
    // Individual cell? A simple val will do - returns the first result
    if ( !this.bExtendable ) {
        return anCells.val();
    }
    
    // Extendable cell? Then we have to get the value of each of the cells
    var aoResults = [];
    anCells.each( function( iIndex, nCell ) {
        aoResults.push( jQuery( nCell ).val() );
    } );
    return aoResults;
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a text input box
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.Column.prototype._fnCreateCell = function( sValue ) {
    if ( typeof sValue === 'undefined' ) sValue = this.sValue;

    var nCell = jQuery( '<input type="text" value="' + sValue + '">' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Text, 
                      SpreadSheet.CSS.Readonly,
                      this.sType ];
                      
    nCell.attr( {
        'class'     : asClasses.join( ' ' ),
        'readonly'  : 'readonly'
    } );
    
    return nCell;
}

/*
* Function: _fnCreateExtendable
* Purpose:  Creates the neat plus button in the end of cell if this column is 
*           marked to be a extendable column (bExtendable = true)
* Input(s): void
* Returns:  node:nExtendable - the node containing the add button
*
*/
SpreadSheet.Column.prototype._fnCreateExtendable = function() {
    var nWrapper = jQuery( '<div>' );

    // Plus
    var nPlus = jQuery( '<span>' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Extendable, 
                      SpreadSheet.CSS.Icon,
                      SpreadSheet.CSS.Plus,
                      this.sType ];
    nPlus.addClass( asClasses.join( ' ' ) );
    
    // Minus
    var nMinus = jQuery( '<span>' );
    asClasses = [ SpreadSheet.CSS.SpreadSheet,
                  SpreadSheet.CSS.Extendable,
                  SpreadSheet.CSS.Icon,
                  SpreadSheet.CSS.Minus,
                  this.sType ];
    nMinus.addClass( asClasses.join( ' ' ) );
    
    // Fill wrapper
    nWrapper.append( nPlus, nMinus );
    return nWrapper;
}

/*
* Function: _fnMakeAscendingSorting
* Purpose:  Constructs a sorting callback for ascending sorting. The ascending 
*           order is equal to the generic sorting order of the fnCompare 
*           function.
* Input(s): void
* Returns:  function:fnAscendingSortingCallback - the sort callback
*
*/
SpreadSheet.Column.prototype._fnMakeAscendingSorting = function() {
    return this.fnCompare.bind( this );
}

/*
* Function: _fnMakeDescendingSorting
* Purpose:  Constructs a sorting callback for descending sorting. The sort order
*           is directly inverse to the generic sort order.
* Input(s): void
* Returns:  function:fnDescendingSortingCallback - the sort callback
*
*/
SpreadSheet.Column.prototype._fnMakeDescendingSorting = function() {
    var fnBoundCompare = this.fnCompare.bind( this );
    return function( a, b ) { return -1 * fnBoundCompare( a, b ); }
}

/*
* Function: _fnMakeFilter
* Purpose:  Constructs a filter callback to be registered with the DataTable 
*           instance to allow searching columns. The callback just basically 
*           parses the value of the column and returns its normalized value.
* Input(s): void
* Returns:  function:fnFilterCallback - the filter callback
*
*/
SpreadSheet.Column.prototype._fnMakeFilter = function() {
    var self = this;
    
    return function( sData ) {
        return self.fnValue( sData ).toString();
    }
}

/*
* Function: _fnRegisterAdd
* Purpose:  Register the callback what will happen if one clicks on the neat add
*           button in a cell. Usually a new default line should appear and the 
*           whole thing shall be saved in the DataTables instance. In almost all 
*           cases this callback is nothing that you would like to overwrite in 
*           your column prototype.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.Column.prototype._fnRegisterAdd = function( sTable, sTd ) {
    var self = this;
    var sAdd = [ 'span', this.sType, SpreadSheet.CSS.Plus ].join( '.' );
    
    jQuery( sTable ).delegate( sAdd, 'click', function( event ) {
        var nCell = jQuery( this ).parents( sTd );
        self.fnInsertNewLine( nCell );
    } );
}

/*
* Function: _fnRegisterBlur
* Purpose:  Registers a cell blur callback. In this case, make all blurred input
*           field readonly again and save the content in the DataTables instance
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.Column.prototype._fnRegisterBlur = function( sTable, sTd ) {
    var self = this;
    var sInput = [ 'input', this.sType, SpreadSheet.CSS.Text ].join( '.' );
    
    jQuery( sTable ).delegate( sInput, 'blur', function( event ) {    
        var nInput = jQuery( this );
        var nCell = nInput.parents( sTd );
        var aoValues = self.fnValue( nCell );
        
        nInput.attr( 'readonly', 'readonly' );
        nInput.addClass( SpreadSheet.CSS.Readonly );
        self.oSpreadSheet.fnUpdate( nCell, self.fnCreate( aoValues ) );
    } );
}

/*
* Function: _fnRegisterClick
* Purpose:  Register the click interaction with a normal column cell. In this 
*           case, we will make the clicked input field writeable and select the 
*           content.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.Column.prototype._fnRegisterClick = function( sTable, sTd ) {
    var self = this;
    var sInput = [ 'input', this.sType, SpreadSheet.CSS.Text ].join( '.' );

    jQuery( sTable ).delegate( sInput, 'click', function( event ) {    
        var nInput = jQuery( this );
        
        nInput.removeAttr( 'readonly' );
        nInput.removeClass( SpreadSheet.CSS.Readonly );
        nInput.focus();
    } );
}

/*
* Function: _fnRegisterClicks
* Purpose:  Register the click event handlers for a cell. The individual calls 
*           for clicking on a the cell itself should be overwritten in other 
*           column types, the plus and minus button interaction however should 
*           be reusable in most of the cases.
* Input(s): void
* Returns:  void
*
*/
SpreadSheet.Column.prototype._fnRegisterClicks = function() {
    if ( this.bProtected ) return;

    var sTable = '#' + this.oSpreadSheet.fnGetId();
    var sTd = [ 'td', this.sType, SpreadSheet.CSS.Clickable ].join( '.' );
    
    // Click on a cell
    this._fnRegisterClick( sTable, sTd );    
    // Blurring a cell
    this._fnRegisterBlur( sTable, sTd );
    // Click on plus
    this._fnRegisterAdd( sTable, sTd );
    // Click on minus
    this._fnRegisterMinus( sTable, sTd );
}

/*
* Function: _fnRegisterMinus
* Purpose:  Register the callback what will happen if one clicks on the neat 
*           minus button in a cell. In this case the last line will be removed 
*           and the new cell shall be saved in the DataTables instance. In 
*           almost all cases this event handler is nothing that you would like 
*           to overwrite in your column prototype.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.Column.prototype._fnRegisterMinus = function( sTable, sTd ) {
    var self = this;
    var sMinus = [ 'span', this.sType, SpreadSheet.CSS.Minus ].join( '.' );
    
    jQuery( sTable ).delegate( sMinus, 'click', function( event ) {
        var nCell = jQuery( this ).parents( sTd );
        self.fnDeleteLine( nCell );
    } );
}









/*
* Function: SpreadSheet.IncrementColumn
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetIncrementColumn instance when called with new
*
*/
SpreadSheet.IncrementColumn = function( oInit ) {
    SpreadSheet.Column.call(this, oInit);
    
    // objects
    this.oSpreadSheet = oInit.oSpreadSheet;
    
    // string
    this.sClass += ' ' + SpreadSheet.CSS.Default;
    this.sWidth = oInit.width || '20px';
    
    // integer
    var value = oInit.value;
    var inc = oInit.increment;    
    this.iValue = typeof value !== 'undefined' ? parseInt( value ) : 1;
    this.iIncrement = typeof inc !== 'undefined' ? parseInt( inc ) : 1;
    
    // booleans
    this.bExtendable = false;
    this.bProtected = true;
}
// Inherit from SpreadSheet.Column
SpreadSheet.IncrementColumn.prototype = new SpreadSheet.Column();
SpreadSheet.IncrementColumn.prototype.constructor = SpreadSheet.IncrementColumn;

/*
* Function: fnIsDefault
* Purpose:  This function will always return true when asked whether it contains
*           a default value as an increment column. The reason for this is, that
*           an increment column does not really contain a default value but is 
*           rather dependent on a concrete attached SpreadSheet instance. So, we
*           basically always answer 'yes, I am containing my default data'
* Input(s): integer:iValue - the value of a cell as integer
* Returns:  boolean:bDefault - always true return value
*
*/
SpreadSheet.IncrementColumn.prototype.fnIsDefault = function( iValue ) {
    return true;
}

// These callbacks have to be overriden to an empty function as they are not 
// required for the increment column
SpreadSheet.IncrementColumn.prototype.fnKeyin = function( nCell ) {}
SpreadSheet.IncrementColumn.prototype.fnKeyout = function( nCell ) {}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way - 
*           meaning it returns the number as an INTEGER that can be found in the
*           cell.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  string|array string:oValue - the value of the cell
*
*/
SpreadSheet.IncrementColumn.prototype.fnValue = function( oData ) {
    var anCells = jQuery( 'div.' + SpreadSheet.CSS.Increment, jQuery( oData ) );
    
    return parseInt( anCells.text() );
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a simple div 
*           containing the number.
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.IncrementColumn.prototype._fnCreateCell = function( iValue ) {
    var nCell = jQuery( '<div>' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Increment,
                      this.sType ];
                      
    if ( typeof iValue === 'undefined' ) {
        iValue = this.iValue;
    } else {
        iValue = this.iValue + iValue * this.iIncrement;
    }
    nCell.text( iValue );
    nCell.addClass( asClasses.join( ' ' ) );
    
    return nCell;
}

// These callbacks are not required for increment columns. We will make sure 
// that no strange things happen by putting empty stubs here.
SpreadSheet.IncrementColumn.prototype._fnRegisterClick = function() {}
SpreadSheet.IncrementColumn.prototype._fnRegisterBlur = function() {}










/*
* Function: SpreadSheet.EditColumn
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetEditColumn instance when called with new; else undefined
*
*/
SpreadSheet.EditColumn = function( oInit ) {
    SpreadSheet.Column.call(this, oInit);
    
    // strings
    this.sTitle = typeof oInit.title === 'string' ? oInit.title : ' ';
    this.sValue = null;
    this.sWidth = oInit.width || '50px';
    
    // booleans
    this.bExtendable = false;
    this.bProtected = true;
    this.bSearchable = false;
    this.bSortable = false;
}
// Inherit from SpreadSheet.Column
SpreadSheet.EditColumn.prototype = new SpreadSheet.Column();
SpreadSheet.EditColumn.prototype.constructor = SpreadSheet.EditColumn;

/*
* Function: fnIsDefault
* Purpose:  This function will always return true when asked whether it contains
*           a default value as an edit column. The reason for this is, that
*           an edit column does not contain any dynamic values
* Input(s): integer:iValue - the value of a cell as integer
* Returns:  boolean:bDefault - always true return value
*
*/
SpreadSheet.EditColumn.prototype.fnIsDefault = function( sValue ) {
    return true;
}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way - 
*           meaning it returns a simple string or in case of an extendable cell 
*           an array with each value.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  string|array string:oValue - the value of the cell
*
*/
SpreadSheet.EditColumn.prototype.fnValue = function( oData ) {
    return '';
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a simple div 
*           containing three buttons up, down and delete
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.EditColumn.prototype._fnCreateCell = function( oValue ) {
    var nCell = jQuery( '<div>' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Edit,
                      this.sType ];
    nCell.addClass( asClasses.join( ' ' ) );
    
    var nUp = jQuery( '<span>' ).addClass( SpreadSheet.CSS.Icon ).addClass( SpreadSheet.CSS.Up );
    var nDown = jQuery( '<span>' ).addClass( SpreadSheet.CSS.Icon ).addClass( SpreadSheet.CSS.Down );
    var nDelete = jQuery( '<span>' ).addClass( SpreadSheet.CSS.Icon ).addClass( SpreadSheet.CSS.Delete );
    
    nCell.append( nUp, nDown, nDelete );
    
    return nCell;
}

/*
* Function: _fnRegisterClick
* Purpose:  Register the click interaction with a normal column cell. In this 
*           case, we will make the clicked input field writeable and select the 
*           content.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.EditColumn.prototype._fnRegisterClick = function( sTable, sTd ) {
    var self = this;
    var sUp = [ 'span', SpreadSheet.CSS.Up ].join( '.' );
    var sDown = [ 'span', SpreadSheet.CSS.Down ].join( '.' );
    var sDelete = [ 'span', SpreadSheet.CSS.Delete ].join( '.' );

    jQuery( sTable ).delegate( sUp, 'click', function( event ) {
        var nCell = jQuery( event.currentTarget ).parents( sTd );
        self.oSpreadSheet.fnExchangeRows( nCell[ 0 ], -1 );
    } );
    
    jQuery( sTable ).delegate( sDown, 'click', function( event ) {
        var nCell = jQuery( event.currentTarget).parents( sTd );
        self.oSpreadSheet.fnExchangeRows( nCell[ 0 ], 1 );
    } );

    jQuery( sTable ).delegate( sDelete, 'click', function( event ) {
        var nCell = jQuery( event.currentTarget ).parents( sTd );
        self.oSpreadSheet.fnDeleteLine( nCell[ 0 ] );
    } );
}









/*
* Function: SpreadSheet.CheckboxColumn
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetCheckboxColumn instance when called with new, 
*           else undefined
*
*/
SpreadSheet.CheckboxColumn = function( oInit ) {
    SpreadSheet.Column.call(this, oInit);
    
    // strings
    if ( typeof oInit.value === 'boolean' ) {
        this.sValue = oInit.value;
    } else if ( typeof oInit.value === 'string' ) {
        this.sValue = oInit.value === 'true' ? true : false;
    } else {
        this.sValue = false;
    }
}
// Inherit from SpreadSheet.Column
SpreadSheet.CheckboxColumn.prototype = new SpreadSheet.Column();
SpreadSheet.CheckboxColumn.prototype.constructor = SpreadSheet.CheckboxColumn;


// Empty stubs, nothing to do here for a checkbox column
SpreadSheet.CheckboxColumn.prototype.fnKeyin = function( nCell ) {}
SpreadSheet.CheckboxColumn.prototype.fnKeyout = function( nCell ) {}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way - 
*           meaning it will return true or false, respectively an array of these
*           values depending on the extendable parameter.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  boolean|array boolean:bValue - the value of the cell
*
*/
SpreadSheet.CheckboxColumn.prototype.fnValue = function( oData ) {
    var anCells = jQuery( 'span.' + SpreadSheet.CSS.Checkbox, jQuery( oData ) );
    
    // Individual cell? A simple val will do - returns the first result
    if ( !this.bExtendable ) {
        return anCells.hasClass( SpreadSheet.CSS.Checked );
    }
    
    // Extendable cell? Then we have to get the value of each of the cells
    var aoResults = [];
    anCells.each( function( iIndex, nCell ) {
        aoResults.push( jQuery( nCell ).hasClass( SpreadSheet.CSS.Checked ) );
    } );
    return aoResults;
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a text input box
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.CheckboxColumn.prototype._fnCreateCell = function( sValue ) {
    if ( typeof sValue === 'undefined' ) sValue = this.sValue;

    var nCell = jQuery( '<span>' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Icon,
                      SpreadSheet.CSS.Checkbox, 
                      this.sType ];
                      
    if ( sValue ) {
        asClasses.push( SpreadSheet.CSS.Checked );
    } else {
        asClasses.push( SpreadSheet.CSS.Unchecked );
    }                          
    nCell.addClass( asClasses.join( ' ' ) );
    
    return nCell;
}

// Checkbox columns do not need a blur call as their value is updated on click
SpreadSheet.CheckboxColumn.prototype._fnRegisterBlur = function( sTable, sTd ) {}

/*
* Function: _fnRegisterClick
* Purpose:  Register the click interaction with a normal column cell. In this 
*           case, we will toggle the symbol of the checkbox on click and save 
*           the new state directly in the DataTables instance.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.CheckboxColumn.prototype._fnRegisterClick = function( sTable, sTd ) {
    var self = this;
    var sBox = [ 'span', this.sType, SpreadSheet.CSS.Checkbox ].join( '.' );

    jQuery( sTable ).delegate( sBox, 'click', function( event ) {    
        var nCheckbox = jQuery( this );
        var nCell = nCheckbox.parents( sTd );
        
        nCheckbox.toggleClass( SpreadSheet.CSS.Checked );
        nCheckbox.toggleClass( SpreadSheet.CSS.Unchecked );
        
        var aoValues = self.fnValue( nCell );
        self.oSpreadSheet.fnUpdate( nCell, self.fnCreate( aoValues ) );
    } );
}









/*
* Function: SpreadSheet.SelectColumn
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetCheckboxColumn instance when called with new, else 
*           undefined
*
*/
SpreadSheet.SelectColumn = function( oInit ) {
    SpreadSheet.Column.call(this, oInit);
    
    // strings
    this.sValue = typeof oInit.value !== 'undefined' ? oInit.value : '';
    
    // objects
    this.aOptions = typeof oInit.options !== 'undefined' ? oInit.options : [];
    if ( jQuery.inArray( this.sValue, this.aOptions ) < 0 ) {
        this.aOptions.unshift( this.sValue );
    }
}
// Inherit from SpreadSheet.Column
SpreadSheet.SelectColumn.prototype = new SpreadSheet.Column();
SpreadSheet.SelectColumn.prototype.constructor = SpreadSheet.SelectColumn;

// Empty stubs here, nothing to do here for selet columns
SpreadSheet.SelectColumn.prototype.fnKeyin = function( nCell ) {}
SpreadSheet.SelectColumn.prototype.fnKeyout = function( nCell ) {}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way. In 
*           this case the string of the currently selected item.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  string|array string:sValue - the value of the cell
*
*/
SpreadSheet.SelectColumn.prototype.fnValue = function( oData ) {
    var anCells = jQuery( 'select', jQuery( oData ) );
    
    // Individual cell? A simple val will do - returns the first result
    if ( !this.bExtendable ) {
        return anCells.val();
    }
    
    // Extendable cell? Then we have to get the value of each of the cells
    var aoResults = [];
    anCells.each( function( iIndex, nCell ) {
        aoResults.push( jQuery( nCell ).val() );
    } );
    return aoResults;
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a text input box
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.SelectColumn.prototype._fnCreateCell = function( sValue ) {
    if ( typeof sValue === 'undefined' ) sValue = this.sValue;

    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Select,
                      this.sType ];
    var nCell = jQuery( '<div>' ).addClass( asClasses.join( ' ' ) );                      
    nCell.authorlist_select( {
        'value'         : sValue,
        'options'       : this.aOptions
    } );
    
    return nCell;
}

// No blur event needed for select columns. The value will be updated on change.
SpreadSheet.SelectColumn.prototype._fnRegisterBlur = function( sTable, sTd ) {}

/*
* Function: _fnRegisterClick
* Purpose:  Register the click interaction with a normal column cell. In this 
*           case, we will save the updated select box in the DataTable instance 
*           as soon as we get the change event of any of the contained select 
*           boxes.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.SelectColumn.prototype._fnRegisterClick = function( sTable, sTd ) {
    var self = this;
    var sDiv = [ 'div', SpreadSheet.CSS.SpreadSheet, 
                  SpreadSheet.CSS.Select, this.sType ].join( '.' );
    var sSelector = [ sTd, sDiv, 'select' ].join( ' ' );

    jQuery( sTable ).delegate( sSelector, 'change', function( event ) {
        var nSelect = jQuery( event.currentTarget );
        var nCell = nSelect.parents( sTd );
        var aoValues = self.fnValue( nCell );
        
        self.oSpreadSheet.fnUpdate( nCell, self.fnCreate( aoValues ) );
    } );
}









/*
* Function: SpreadSheet.TextSelectColumn
* Purpose:  Constructor
* Input(s): object:oInit - Initialization settings for a column
* Returns:  SpreadSheetTextSelectColumn instance when called with new
*
*/
SpreadSheet.TextSelectColumn = function( oInit ) {
    SpreadSheet.Column.call(this, oInit);
    
    // strings
    this.sText = oInit.text || '';
    this.sValue = typeof oInit.value !== 'undefined' ? oInit.value : '';
    this.aOptions = typeof oInit.options !== 'undefined' ? oInit.options : [];
    if ( jQuery.inArray( this.sValue, this.aOptions ) < 0 ) {
        this.aOptions.unshift( this.sValue );
    }
}
// Inherit from SpreadSheet.Column
SpreadSheet.TextSelectColumn.prototype = new SpreadSheet.Column();
SpreadSheet.TextSelectColumn.prototype.constructor = SpreadSheet.TextSelectColumn;

/*
* Function: fnInsertNewLine
* Purpose:  Inserts a new default line at the end of the given cell and saves it
*           in the DataTable instance.
* Input(s): node:nCell - the DOM element or jQuery of the cell to be modified
* Returns:  void
*
*/
SpreadSheet.TextSelectColumn.prototype.fnInsertNewLine = function( nCell ) {
    var aoValues = this.fnValue( nCell );
    
    // Insert a new default value
    aoValues.push( [ this.sText, this.sValue ] );
    this.oSpreadSheet.fnUpdate( nCell, this.fnCreate( aoValues ) );
}

/*
* Function: fnIsDefault
* Purpose:  Checks whether the given value equals to a default cell of this 
*           column.
* Input(s): string:sValue - the value to be checked
* Returns:  boolean:bEqual - truth value indicating equality to the default
*
*/
SpreadSheet.TextSelectColumn.prototype.fnIsDefault = function( asValue ) {
    if ( !this.bExtendable ) return this._fnLineIsDefault( asValue );
    
    for ( var i = 0, iLen = asValue.length; i < iLen; i++ ) {
        if ( !this._fnLineIsDefault( asValue[ i ] ) ) return false;
    }
    return true;
}

/*
* Function: fnValue
* Purpose:  Returns the value of a cell of this column in a processable way - 
*           meaning it returns an array containing first the text and secondly  
*           second position the select value. In case of an extendable cell the 
*           return value will be an array of the previously mentioned arrays.
* Input(s): object:oData - the data of a cell of this column as a string, DOM
*                          element or jQuery set.
* Returns:  array string|array array string:aValue - the value of the cell
*
*/
SpreadSheet.TextSelectColumn.prototype.fnValue = function( oData ) {
    var anInput = jQuery( 'input.' + SpreadSheet.CSS.Text, jQuery( oData ) );
    var anSelect = jQuery( 'select', jQuery( oData ) );
    
    // Individual cell? A simple val will do - returns the first result
    if ( !this.bExtendable ) {
        return [ anInput.val(), anSelect.val() ];
    }
    
    // Extendable cell? Then we have to get the value of each of the cells
    var iLength = Math.min( anInput.length, anSelect.length )
    var aoResults = [];
    for ( var i = 0, iLen = iLength; i < iLen; i++ ) {
        aoResults.push( [ jQuery( anInput[ i ] ).val(),
                          jQuery( anSelect[ i ] ).val() ] );
    }
    
    return aoResults;
}

/*
* Function: _fnCreateCell
* Purpose:  Creates the actual content of the cell in this case a text input box
*           preceded by a select box in the same line.
* Input(s): void
* Returns:  node:nCell - the cell content as a jQuery node
*
*/
SpreadSheet.TextSelectColumn.prototype._fnCreateCell = function( aValue ) {
    if ( typeof aValue === 'undefined' ) aValue = [ this.sText, this.sValue ];

    var nCell = jQuery( '<table>' ).addClass( SpreadSheet.CSS.TextSelect );
    var nRow = jQuery( '<tr>' );
    var nTextCell = jQuery( '<td>' ).addClass( SpreadSheet.CSS.TextSelectText );
    var nSelectCell = jQuery( '<td>' ).addClass( SpreadSheet.CSS.TextSelectSelect );    

    var nInput = jQuery( '<input type="text" value="' + aValue[ 0 ] + '">' );
    var asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                      SpreadSheet.CSS.Text, 
                      SpreadSheet.CSS.Readonly,
                      this.sType ];            
    nInput.attr( {
        'class'     : asClasses.join( ' ' ),
        'readonly'  : 'readonly'
    } );
    
    asClasses = [ SpreadSheet.CSS.SpreadSheet, 
                  SpreadSheet.CSS.Select,
                  this.sType ];
    var nSelect = jQuery( '<div>' ).addClass( asClasses.join( ' ' ) );
    nSelect.authorlist_select( {
        'value'         : aValue[ 1 ],
        'options'       : this.aOptions
    } );
    
    nCell.append( nRow );
    nRow.append( nTextCell, nSelectCell );
    nTextCell.append( nInput );
    nSelectCell.append( nSelect );
    
    return nCell;
}

/*
* Function: _fnLineIsDefault
* Purpose:  Checks whether a single value array contains only default values.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.TextSelectColumn.prototype._fnLineIsDefault = function( asValue ) {
    var asCompare = [ this.sText, this.sValue ];
    
    for ( var i = 0, iLen = asCompare.length; i < iLen; i++ ) {
        if ( asCompare[ i ] !== asValue[ i ] ) return false;
    }    
    return true; 
}

/*
* Function: _fnRegisterClick
* Purpose:  Register the click interaction with a normal column cell. Here we 
*           just reuse the register click calls of the normal text and select 
*           columns as this one here is composed of both.
* Input(s): string:sTable - the own table selector string
*           string:sTd - the own table cell (td) selector string
* Returns:  void
*
*/
SpreadSheet.TextSelectColumn.prototype._fnRegisterClick = function( sTable, sTd ) {
    SpreadSheet.Column.prototype._fnRegisterClick.call( this, sTable, sTd );
    SpreadSheet.SelectColumn.prototype._fnRegisterClick.call( this, sTable, sTd );
}








/*
* Function: SpreadSheet.Cursor
* Purpose:  Constructor
* Input(s): void
* Returns:  SpreadSheet.Cursor instance when called with new, else undefined
*
*/
SpreadSheet.Cursor = function() {
    var bExists = jQuery( '.' + SpreadSheet.CSS.Cursor ).length > 0;

    // There are already cursor elements on the page, so use them as elements
    if ( bExists ) {
        this._nTop      = jQuery( '.' + SpreadSheet.CSS.CursorTop );
        this._nRight    = jQuery( '.' + SpreadSheet.CSS.CursorRight );
        this._nBottom   = jQuery( '.' + SpreadSheet.CSS.CursorBottom );
        this._nLeft     = jQuery( '.' + SpreadSheet.CSS.CursorLeft );
        this._nCube     = jQuery( '.' + SpreadSheet.CSS.CursorCube );
        
    // No cursor elements where found, so we better create some
    } else {
        this._nTop      = jQuery( '<div>' ).addClass( SpreadSheet.CSS.CursorTop );
        this._nRight    = jQuery( '<div>' ).addClass( SpreadSheet.CSS.CursorRight );
        this._nBottom   = jQuery( '<div>' ).addClass( SpreadSheet.CSS.CursorBottom );
        this._nLeft     = jQuery( '<div>' ).addClass( SpreadSheet.CSS.CursorLeft );
        this._nCube     = jQuery( '<div>' ).addClass( SpreadSheet.CSS.CursorCube );
    }
    
    // Helping elements that contains all cursor elements
    this._nAll = jQuery().add( this._nTop ).add( this._nRight )
                         .add( this._nBottom ).add( this._nLeft )
                         .add( this._nCube );
    this._nAll.addClass( SpreadSheet.CSS.Cursor );
    if ( !bExists ) jQuery( 'body' ).append( this._nAll );
}

/*
* Function: fnShow
* Purpose:  Makes all cursor elements visible
* Input(s): void
* Returns:  void
*
*/
SpreadSheet.Cursor.prototype.fnShow = function() {
    this._nAll.show();
}

/*
* Function: fnHide
* Purpose:  Hides all elements of the cursor
* Input(s): void
* Returns:  void
*
*/
SpreadSheet.Cursor.prototype.fnHide = function() {
    this._nAll.hide();
}

/*
* Function: fnPointTo
* Purpose:  Overlays the passed cell with a cursor
* Input(s): node:nCell - the cell to be pointed to
* Returns:  void
*
*/
SpreadSheet.Cursor.prototype.fnPointTo = function( nCell ) {
    nCell = jQuery( nCell );
    
    var iWidth = nCell.width();
    var iHeight = nCell.height();
    var oOffset = nCell.offset();
    
    this._nTop.offset( oOffset ).width( iWidth );
    this._nLeft.offset( oOffset ).height( iHeight );
    
    oOffset.left += iWidth;
    this._nRight.offset( oOffset ).height( iHeight );
    oOffset.left -= iWidth;
    
    oOffset.top += iHeight;
    this._nBottom.offset( oOffset ).width( iWidth );
    oOffset.top -= iHeight;
    
    // Center the small cube on the right lower corner
    oOffset.left += iWidth - this._nCube.width() / 2;
    oOffset.top += iHeight - this._nCube.height() / 2;
    this._nCube.offset( oOffset );
}









/*
* Variable: SpreadSheet.ColumnTypes
* Purpose:  Lookup table to determine the handling prototype for a certain 
*           column type.
*
*/
SpreadSheet.ColumnTypes = {
    'text'                  : SpreadSheet.Column,
    'increment'             : SpreadSheet.IncrementColumn,
    'edit'                  : SpreadSheet.EditColumn,
    'checkbox'              : SpreadSheet.CheckboxColumn,
    'select'                : SpreadSheet.SelectColumn,
    'textselect'            : SpreadSheet.TextSelectColumn,
    
    'default'               : SpreadSheet.Column
}









/*
* Function: SpreadSheet
* Purpose:  Constructor
* Input(s): string:sId - Id of the html element the SpreadSheet will be embedded
*                        into (preferably a div).
*           object:oInit - Object containing initialization settings
* Returns:  SpreadSheet instance when called with new, else undefined
*
*/
function SpreadSheet( sId, oInit ) {
    // Clean the initialization parameters
    this._oInit = this._fnSanitizeParameters( oInit );

    // Find the parent element and assign SpreadSheet elements
    this._nParent = this._fnGetElement( sId );
    this._nParent.addClass( SpreadSheet.CSS.SpreadSheet );

    // Create the table    
    this._nTable = this._fnCreateTable();
    this._nParent.append( this._nTable );
    
    this._oCursor = new SpreadSheet.Cursor();
    
    // Construct the column descriptors
    this._aoColumns = this._fnCreateColumns( this._oInit, this._nTable );
    
    // Register table interaction callbacks
    this._fnRegisterClicks( this._nTable );
    this._fnRegisterKeyboard( this._nTable );
    
    // Create the DataTable instance
    this._oDataTable = this._fnCreateDataTable( this._nTable, this._aoColumns );
}

/*
* Function: fnCreateId
* Purpose:  Generates a unique ID for something. JavaScript is lacking a native 
*           function for this purpose. Instead, we will just use the millis 
*           since the epoch. This approach may theoretically(!) lead to id 
*           collisions. However, in most cases in practice we should have enough
*           time between each generation.
* Input(s): void
* Returns:  integer:id - the generated id
*
*/
SpreadSheet.prototype.fnCreateId = function() {
    return 'sheet-' + jQuery.now();
}

/*
* Function: fnDeleteLine
* Purpose:  Deletes the line that contains the passed cell or the very last row.
*           Updates all incremental columns on the way.
* Input(s): node:nCell - the cell whichs parent row shall be deleted
* Returns:  void
*
*/
SpreadSheet.prototype.fnDeleteLine = function( nCell ) {
    var iItems = this._oDataTable.fnSettings().aoData.length;    
    // Do not allow deletions on the very last row
    if ( iItems <= 1 ) return;

    // Find line to be deleted - i.e. row of cell or very last one
    if ( typeof nCell !== 'undefined' ) {
        var iRow = this._oDataTable.fnGetPosition( nCell )[ 0 ];
    } else {
        var iRow = iItems - 1;
    }
    
    // Delete the row using the DataTable instance
    this._oDataTable.fnDeleteRow( iRow );
    
    // Update the increment columns
    // Iterate over all columns
    for ( var j = 0, jLen = this._aoColumns.length; j < jLen; j++ ) {
        var oColumn = this._aoColumns[ j ];
        
        // Iterate over each row that is an increment column and update it
        if ( ! (oColumn instanceof SpreadSheet.IncrementColumn) ) continue;
        for ( var i = iRow; i < iItems - 1; i++ ) {
            this._oDataTable.fnUpdate( oColumn.fnCreate( i ), i, j, false, false );
        }
    }
    
    this._oDataTable.fnDraw( false );
}

/*
* Function: fnExchangeRows
* Purpose:  Exchanges the row the contains the given cell with the row that has 
*           a relative distance to the selected row having the passed offset.
* Input(s): node:nCell - the cell whichs parent row shall be deleted
            integer:iOffset - the offset
* Returns:  void
*
*/
SpreadSheet.prototype.fnExchangeRows = function( nCell, iOffset ) {
    var iRowA = this._oDataTable.fnGetPosition( nCell )[ 0 ];
    var iRowB = iRowA + iOffset;
    var iItems = this._oDataTable.fnSettings().aoData.length;
    
    if ( iRowB < 0 || iRowB >= iItems ) return;
    
    var asContentA = this._oDataTable.fnGetData( iRowA );
    var asContentB = this._oDataTable.fnGetData( iRowB );
    
    for ( var i = 0, iLen = this._aoColumns.length; i < iLen; i++ ) {
        var oColumn = this._aoColumns[ i ];
    
        if ( ! ( oColumn instanceof SpreadSheet.IncrementColumn ) ) continue;
        var sBuffer = asContentA[ i ];
        asContentA[ i ] = asContentB[ i ];
        asContentB[ i ] = sBuffer;
    }
    this._oDataTable.fnUpdate( asContentA, iRowB, undefined, false, false );
    this._oDataTable.fnUpdate( asContentB, iRowA, undefined, false, true);
}

/*
* Function: fnGetData
* Purpose:  Returns the content of the SpreadSheet in a two-dimensional array. 
*           Each of the inner arrays contains the data of one single row whereas
*           the outer array contains each of the lines. This function auto-
*           matically skips all rows that only contain DEFAULT values and will 
*           NOT include them in the result.
* Input(s): node:nNode - the node to get the id of
* Returns:  stringLsId - the id
*
*/
SpreadSheet.prototype.fnGetData = function() {
    var aasData = this._oDataTable.fnGetData();
    var aaoResult = [];

    for ( var j = 0, jLen = aasData.length; j < jLen; j++ ) {
        var bValid = false;
        var aoResult = [];
                
        for ( var i = 0, iLen = this._aoColumns.length; i < iLen; i++ ) {
            var oColumn = this._aoColumns[ i ];
            var oValue = oColumn.fnValue( aasData[ j ][ i ] );
            
            aoResult.push( oValue );
            bValid = bValid || !oColumn.fnIsDefault( oValue );
        }
        
        if ( bValid ) aaoResult.push( aoResult );
    }
    
    return aaoResult;
}

/*
* Function: fnGetId
* Purpose:  Returns the HTML id of the passed node or the id of the table that 
*           contains the SpreadSheet if argument is undefined
* Input(s): node:nNode - the node to get the id of
* Returns:  stringLsId - the id
*
*/
SpreadSheet.prototype.fnGetId = function( nNode ) {
    if ( typeof nNode === 'undefined' ) nNode = this._nTable;

    return jQuery( nNode ).attr( 'id' );
}

/*
* Function: fnInsertNewLine
* Purpose:  Inserts a new line at the end of the table containing default cells 
*           for each column.
* Input(s): boolean:bRedraw - a flag indicating whether to redraw the table 
                              after inserting the line. Default: true. NOTE:
                              when redraw is true pagination and sorting will be
                              reset immediately.
* Returns:  array string:asCell - an array containing the inserted cells
*
*/
SpreadSheet.prototype.fnInsertNewLine = function( bRedraw ) {
    if ( typeof bRedraw === 'undefined' ) bRedraw = true;
    var asCells = [];
        
    for ( var i = 0, iLen = this._aoColumns.length; i < iLen; i++ ) {
        var oColumn = this._aoColumns[ i ];
        var iLines = this._oDataTable.fnSettings().aoData.length;
        
        if ( oColumn instanceof SpreadSheet.IncrementColumn ) {
            asCells.push( oColumn.fnCreate( iLines ) );
        } else {
            asCells.push( oColumn.fnCreate() );
        }
    }
    this._oDataTable.fnAddData( asCells, bRedraw );
    
    return asCells;
}

/*
* Function: fnLoadData
* Purpose:  Loads initial data for a SpreadSheet. If there is no data given, the
*           function will create one new empty line
* Input(s): object:oInit - SpreadSheet initializer object
* Returns:  void
*
*/
SpreadSheet.prototype.fnLoadData = function( aaoLoad ) {
    // No initial data there to load
    if ( typeof aaoLoad === 'undefined' || aaoLoad.length === 0 ) {
        this.fnInsertNewLine();
        
    // Data found, woohoo, lets rock!
    } else {
        // Iterate over each line to be inserted
        for ( var i = 0, iLen = aaoLoad.length; i < iLen; i++ ) {
            var aoRow = aaoLoad[ i ];
            
            // Iterate over each individual entry in one line
            for ( var j = 0, jLen = aoRow.length; j < jLen; j++ ) {
                var oColumn = this._aoColumns[ j ];
                
                // Normally the indices should be right, but we will take the 
                // safe track and reconstruct them
                if ( oColumn instanceof SpreadSheet.IncrementColumn ) {
                    aoRow[ j ] = oColumn.fnCreate( i );
                // Elsewise we will just construct a normal cell using the data
                } else {
                    aoRow[ j ] = oColumn.fnCreate( aoRow[ j ] );
                }
            }
        }
        
        // Add the whole data to the DataTables instance
        this._oDataTable.fnAddData( aaoLoad );
    }
}

/*
* Function: fnUpdate
* Purpose:  Updates a given cell with the newly passed content. It will be 
*           directly reflected on the underlying DataTable instance, by default
*           without a table redraw to keep the focus and clicks on the table.
* Input(s): node:nCell - the cell to be updated
*           string:sNew - new content as string
*           boolean:bRedraw - parameter telling whether to redraw the table
* Returns:  void
*
*/
SpreadSheet.prototype.fnUpdate = function( nCell, sNew, bRedraw ) {
    if ( typeof bRedraw === 'undefined' ) bRedraw = false;
    nCell = jQuery( nCell )[ 0 ];
    
    var aiPosition = this._oDataTable.fnGetPosition( nCell );
    var iRow = aiPosition[ 0 ];
    var iColumn = aiPosition[ 2 ] ;
    
    try {
        this._oDataTable.fnUpdate( sNew, iRow, iColumn, bRedraw );
    } catch ( error ) {
        this._oDataTable.fnDraw( false );
    }
}

/*
* Function: _fnCreateColumns
* Purpose:  Creates column descriptors from a initialization parameters-like 
*           object as passed to the SpreadSheet constructor for instance.
* Input(s): object:oInit - the initialization parameters passed to the table
* Returns:  array object:aoColumns
*
*/
SpreadSheet.prototype._fnCreateColumns = function( oInit, nTable ) {
    var aoColumns = [];
    var oColumn = null;
    var oColumnType = null;
    var oColumnPrototype = null;    
    var sTableId = this.fnGetId( nTable );
    
    for ( var i = 0, iLen = oInit.columns.length; i < iLen; i++ ) {
        // Get column,its type or default if not present and its prototype
        oColumn = oInit.columns[i];
        oColumn.sType = sTableId + '-' + i;
        oColumn.oSpreadSheet = this;
        
        oColumnType = oColumn.type || 'default';
        oColumnPrototype = SpreadSheet.ColumnTypes[ oColumnType ];
        
        aoColumns.push( new oColumnPrototype( oColumn ) );
    }
    
    return aoColumns;
}

/*
* Function: _fnCreateDataTable
* Purpose:  Initializes the DataTables jQuery plugin and its extra plugin ColVis
* Input(s): node:nTable - the table node in which the DataTable will be embedded
* Returns:  object:oDataTable - the created DataTable object
*
*/

SpreadSheet.prototype._fnCreateDataTable = function( nTable, aoColumns ) {    
    // Create the DataTables instance
    var oDataTable = nTable.dataTable( {
        'bAutoWidth'        : false,
        'bJQueryUI'         : true,
        
        'iDisplayLength'    : 50,
        
        'sDom'              : '<"H"lfr>Ct<"F"ip>',
        'sPaginationType'   : 'full_numbers',
        
        'aoColumns'         : aoColumns,
        'aaSorting'         : this._fnGetInitialSorting( aoColumns ),
        
        // ColVis extra
        'oColVis'           : {
            'activate'      : 'click',
            'buttonText'    : '&nbsp;',
            
            'bRestore'      : true,
            
            'sAlign'        : 'left'
        },
        
        'fnDrawCallback'    : this._fnMakeDrawCallback()
    });
    
    return oDataTable;
}

/*
* Function: _fnCreateTable
* Purpose:  Creates the DOM nodes - i.e. table, thead and tbody and their rows -
*           in which the DataTable instance will be embedded into.
* Input(s): void
* Returns:  node:nTable - the root node of the created table
*
*/
SpreadSheet.prototype._fnCreateTable = function() {
    var aClasses = [ SpreadSheet.CSS.SpreadSheet, SpreadSheet.CSS.DataTable ];

    var nTable = jQuery( '<table>' );
    nTable.attr( {
        'id'    : this.fnCreateId(),
        'class' : aClasses.join( ' ' )
    } );
    var nTableHead = jQuery( '<thead><tr></thead>' );
    var nTableBody = jQuery( '<tbody>' );
    nTable.append( nTableHead, nTableBody );
    
    return nTable;
}

/*
* Function: _fnEnter
* Purpose:  Defines what happens when a person hits the enter button - i.e. move
*           down if another cell is there or introduce a new one first and then 
*           move.
* Input(s): node:nCell - the cell that was focused when the enter key was hit
* Returns:  void
*
*/
SpreadSheet.prototype._fnEnter = function( nCell ) {

    // DataTables and SpreadSheet specific variables
    var oSettings  = this._oDataTable.fnSettings();
    var aiDisplay  = oSettings.aiDisplay;
    var aiPosition = this._oDataTable.fnGetPosition( nCell[ 0 ] );
    var iItems     = oSettings.aoData.length;
    
    // Position
    var iY      = aiPosition[ 0 ];
    var iLookup = aiDisplay[ aiDisplay.indexOf( iY ) + 1 ];
    // Boundary check for the last line
    if ( typeof iLookup === 'undefined' ) this.fnInsertNewLine( false );
    this._fnMoveDown( nCell );
}

/*
* Function: _fnEscape
* Purpose:  Sends a 'Keyout' event to all passed cells
* Input(s): node:nFocus - the nodes
* Returns:  void
*
*/
SpreadSheet.prototype._fnEscape = function( nFocus ) {
    var self = this;
    
    nFocus.each( function( iIndex, nCell ) {
        var iColumn = self._oDataTable.fnGetPosition( nCell )[ 2 ];
        self._aoColumns[ iColumn ].fnKeyout( nCell );
    } );
}

/*
* Function: _fnFocusin
* Purpose:  Add the focus to the passed cell
* Input(s): node:nCell - the cell
* Returns:  void
*
*/
SpreadSheet.prototype._fnFocusin = function( nCell ) {
    var nCell   = jQuery( nCell );
    var nRow    = nCell.parent().children().first();
    var iX      = this._oDataTable.fnGetPosition( nCell[ 0 ] )[ 1 ];
    var nColumn = this._nTable.find( 'th' ).eq( iX );
    
    this._oCursor.fnShow();
    this._oCursor.fnPointTo( nCell );

    nCell.addClass( SpreadSheet.CSS.Focus );
    nRow.addClass( SpreadSheet.CSS.Active );
    nColumn.addClass( SpreadSheet.CSS.Active );
}

/*
* Function: _fnFocusout
* Purpose:  Remove the focus from the one passed cell
* Input(s): node:nCell - the cell
* Returns:  void
*
*/
SpreadSheet.prototype._fnFocusout = function( nCell ) {
    var nCell   = jQuery( nCell );
    var nRow    = nCell.parent().children().first();
    var iX      = this._oDataTable.fnGetPosition( nCell[ 0 ] )[ 1 ];
    var nColumn = this._nTable.find( 'th' ).eq( iX );
    
    this._oCursor.fnHide();
    
    nCell.removeClass( SpreadSheet.CSS.Focus );
    nRow.removeClass( SpreadSheet.CSS.Active );
    nColumn.removeClass( SpreadSheet.CSS.Active );
}

/*
* Function: _fnGetElement
* Purpose:  Get element by id or raises error. Handy for initialization calls to 
            ensure presence of important nodes.
* Input(s): object:oId - Id of the element to get. Should be of type string but 
*                        could be of any type - toString() will be automatically
*                        called in doubt.
* Returns:  node:nElement - The element with the given id.
*
*/
SpreadSheet.prototype._fnGetElement = function( oId ) {
    var nElement = jQuery( '#' + oId );
    if ( nElement.length === 0 ) {
        throw 'Element with Id ' + oId + ' not present.';
    }
    
    return nElement;
}

/*
* Function: _fnGetInitialSorting
* Purpose:  Sets the initial sorting of a DataTables instance onto the first 
*           incremental column or to the very first column, if an incremental 
*           column is not present
* Input(s): object:aoColumns - the columns on which to determine the sorting
* Returns:  array array:asSorting - array representing a DataTable sorting
*
*/
SpreadSheet.prototype._fnGetInitialSorting = function( aoColumns ) {
    for ( var i = 0, iLen = aoColumns.length; i < iLen; i++ ) {
        if ( aoColumns[i] instanceof SpreadSheet.IncrementColumn ) {
            return [[ i, 'asc' ]];
        }
    }
    return [[ 0, 'asc' ]];
}

/*
* Function: _fnMakeDrawCallback
* Purpose:  Returns a callback function for the DataTables fnDrawCallback 
*           option. It is responsible for the positioning of the ColVis button,
*           that can show or hide columns. The position will always be the left 
*           upper corner of the table head.
* Input(s): void
* Returns:  function:fnDrawCallback - the draw callback
*
*/
SpreadSheet.prototype._fnMakeDrawCallback = function() {
    var self = this;

    return function( event ) {
        var nColVisButton = jQuery( 'div.ColVis', event.nTableWrapper );
        var nTableHead = jQuery( 'thead', self._nTable );
        
        nColVisButton.css( 'height', nTableHead.height() + 1 + 'px' );
        nColVisButton.css( 'left', nTableHead.position().left + 'px' );
        if ( !jQuery.browser.mozilla ) {
            nColVisButton.css( 'top', nTableHead.position().top + 'px' );
        } else {
            // Firefox has a different idea of what the top position of this 
            // button is, so we have to move it one pixel up
            nColVisButton.css( 'top', nTableHead.position().top - 1 + 'px' );
        }
    }
}

/*
* Function: _fnMoveDown
* Purpose:  Moves the focus cursor from the passed cell one down. While doing so 
*           it takes into account pagination and out-of-bounds checks for the 
*           very last cell. This call DOES NOT introduce a new line when 
*           reaching the end of the table but will rather refocus on it.
* Input(s): node:nCell - the cell to move up from
* Returns:  void
*
*/
SpreadSheet.prototype._fnMoveDown = function( nCell ) {
    // DataTables and SpreadSheet specific variables
    var oSettings  = this._oDataTable.fnSettings();
    var aoSColumns = this._aoColumns;
    var aiDisplay  = oSettings.aiDisplay;
    var aiPosition = this._oDataTable.fnGetPosition( nCell[ 0 ] );
    var iItems     = oSettings.aoData.length;
    var iEnd       = oSettings._iDisplayEnd;
    
    // Position
    var iX      = aiPosition[ 2 ];
    var iY      = aiPosition[ 0 ];
    var iLookup = aiDisplay[ aiDisplay.indexOf( iY ) + 1 ];
    // Boundary check for the last line
    var iMovedY = typeof iLookup === 'undefined' ? iY : iLookup;
    
    // Change the page to the last one if required
    if ( iMovedY >= iEnd ) this._oDataTable.fnPageChange( 'last' );
    
    // Lookup the column object and the respective row
    var oColumn      = this._aoColumns[ iX ]; 
    var nMovedRow    = jQuery( oSettings.aoData[ iMovedY ].nTr );
    var nMovedCell   = nMovedRow.children().eq( iX );
    
    // Defocus old cell and focus new cell
    oColumn.fnKeyout( nCell );
    this._fnFocusin( nMovedCell );
    oColumn.fnKeyin( nMovedCell );
}

/*
* Function: _fnMoveLeft
* Purpose:  This function gets a cell as an input and moves the focus from it to
*           another cell to the left. While doing so it keeps track of out of 
*           bounds checks, pagination, readonly columns and row skips for the 
*           previously mentioned possible column skips.
* Input(s): node:nTd - the cell
* Returns:  void
*
*/
SpreadSheet.prototype._fnMoveLeft = function( nCell ) {
    // DataTables and SpreadSheet specific variables
    var oSettings  = this._oDataTable.fnSettings();
    var aoDColumns = oSettings.aoColumns;
    var aoSColumns = this._aoColumns;
    var aiDisplay  = oSettings.aiDisplay;
    var aiPosition = this._oDataTable.fnGetPosition( nCell[ 0 ] );
    var iStart     = oSettings._iDisplayStart;
    
    // Position
    var iY      = aiPosition[ 0 ];
    var iX      = aiPosition[ 2 ];    
    var iMovedY = iY
    var iMovedX = iX;
    
    do {
        // Move the hidden x index to the left
        iMovedX--;
        // Out of bounds? Go one line up and to the very last column
        if ( iMovedX < 0 ) {
            var iLookup = aiDisplay[ aiDisplay.indexOf( iMovedY ) - 1 ];        
            iMovedX = aoDColumns.length - 1;
            iMovedY = typeof iLookup === 'undefined' ? -1 : iLookup;
        }
    // As long as the cursor is on a invisible column or a protected -> move!
    } while( !aoDColumns[iMovedX].bVisible || aoSColumns[iMovedX].bProtected );
    
    // Refocus to the very first cell
    if ( iMovedY < 0 ) {
        iMovedY = iY;
        iMovedX = iX;
        
    // Change the page if needed
    } else if ( iMovedY < iStart ) {
        this._oDataTable.fnPageChange( 'previous' );
    }
    
    // Find the column objects and the new cell
    iMovedX          = this._fnToVisibleColumn( iMovedX );
    var oColumn      = this._aoColumns[ iX ];
    var oMovedColumn = this._aoColumns[ iMovedX ];    
    var nMovedRow    = jQuery( oSettings.aoData[ iMovedY ].nTr );
    var nMovedCell   = nMovedRow.children().eq( iMovedX );
    
    // Defocus old cell and focus new cell
    oColumn.fnKeyout( nCell );
    this._fnFocusin( nMovedCell );
    oMovedColumn.fnKeyin( nMovedCell );
}

/*
* Function: _fnMoveRight
* Purpose:  This function gets a cell as an input and moves the focus from it to
*           another cell to the right. While doing so it keeps track of out of 
*           bounds checks, pagination, readonly columns and row skips for the 
*           previously mentioned possible column skips. If the user tabs right 
*           on the very last cells the script will introduce a new line at the 
*           very end and will focus on it.
* Input(s): node:nTd - the cell
* Returns:  void
*
*/
SpreadSheet.prototype._fnMoveRight = function( nCell ) {
    // DataTables and SpreadSheet specific variables   
    var oSettings  = this._oDataTable.fnSettings();
    var aoDColumns = oSettings.aoColumns;
    var aoSColumns = this._aoColumns;
    var aiDisplay  = oSettings.aiDisplay;
    var aiPosition = this._oDataTable.fnGetPosition( nCell[ 0 ] );
    var iEnd       = oSettings._iDisplayEnd;
    var iItems     = oSettings.aoData.length;
    
    // Position
    var iY      = aiPosition[ 0 ];
    var iX      = aiPosition[ 2 ];    
    var iMovedY = iY
    var iMovedX = iX;
    
    do {
        // Move the hidden x index to the right
        iMovedX++;
        // Out of bounds? Go one line down and to the very first column
        if ( iMovedX >= aoDColumns.length ) {
            var iLookup = aiDisplay[ aiDisplay.indexOf( iMovedY ) + 1 ];
            iMovedX = 0;
            iMovedY = typeof iLookup === 'undefined' ? iItems : iLookup;
        }
    // As long as the cursor is on a invisible column or a protected -> move!
    } while( !aoDColumns[iMovedX].bVisible || aoSColumns[iMovedX].bProtected );
    
    if ( iMovedY >= iItems ) this.fnInsertNewLine();
    if ( iMovedY >= iEnd ) this._oDataTable.fnPageChange( 'last' );
    
    // Find the column objects and the new cell
    iMovedX          = this._fnToVisibleColumn( iMovedX );
    var oColumn      = this._aoColumns[ iX ];
    var oMovedColumn = this._aoColumns[ iMovedX ];    
    var nMovedRow    = jQuery( oSettings.aoData[ iMovedY ].nTr );
    var nMovedCell   = nMovedRow.children().eq( iMovedX );
    
    // Defocus old cell and focus new cell
    oColumn.fnKeyout( nCell );
    this._fnFocusin( nMovedCell );
    oMovedColumn.fnKeyin( nMovedCell );
}

/*
* Function: _fnMoveUp
* Purpose:  Moves the focus cursor from the passed cell one up. While doing so 
*           it takes into account pagination and out-of-bounds checks for the 
*           top most cell
* Input(s): node:nCell - the cell to move up from
* Returns:  void
*
*/
SpreadSheet.prototype._fnMoveUp = function( nCell ) {
    // DataTables and SpreadSheet specific variables
    var oSettings  = this._oDataTable.fnSettings();
    var aoSColumns = this._aoColumns;
    var aiDisplay  = oSettings.aiDisplay;
    var aiPosition = this._oDataTable.fnGetPosition( nCell[ 0 ] );
    var iItems     = oSettings.aoData.length;
    var iStart     = oSettings._iDisplayStart;
    
    // Position
    var iX      = aiPosition[ 2 ];
    var iY      = aiPosition[ 0 ];
    var iLookup = aiDisplay[ aiDisplay.indexOf( iY ) - 1 ];
    // Boundary check for the first line
    var iMovedY = typeof iLookup === 'undefined' ? 0 : iLookup;
    
    // Change the page if the y position is out of bounds
    if ( iMovedY < iStart) this._oDataTable.fnPageChange( 'previous' );
    
    // Lookup the column object and the respective row
    var oColumn      = this._aoColumns[ iX ]; 
    var nMovedRow    = jQuery( oSettings.aoData[ iMovedY ].nTr );
    var nMovedCell   = nMovedRow.children().eq( iX );
    
    // Defocus old cell and focus new cell
    oColumn.fnKeyout( nCell );
    this._fnFocusin( nMovedCell );
    oColumn.fnKeyin( nMovedCell );
}

/*
* Function: _fnRegisterClicks
* Purpose:  Register click callbacks on all cells of this table. The callback 
*           itself will just simply forward the click event directly to the 
*           respective column object, after blurring any current focused cell,
*           setting the focus to the clicked cell and looking up the cell in the
*           DataTable.
* Input(s): node:nTable - the jQuery set of the table root node
* Returns:  void
*
*/
SpreadSheet.prototype._fnRegisterClicks = function( nTable ) {
    var self = this;
    // id selector of the passed table
    var sId = '#' + this.fnGetId( nTable );
    // all sub cells that are clickable
    var sTd = ' td.' + SpreadSheet.CSS.Clickable;

    // TODO: rethink me! Click in a cell on an input and then on another input 
    // in the same cell. On the first click I blur and on the second click I 
    // will go into edit mode. You want me to behave like this?
    jQuery( sId ).delegate( sTd, 'focus', function( event ) {
        var iX = self._oDataTable.fnGetPosition( event.currentTarget )[ 1 ];        
        if ( !self._aoColumns[ iX ].bProtected ) {
            self._fnFocusin( event.currentTarget );
        }
    } );
    
    jQuery( sId ).delegate( sTd, 'focusout', function( event ) {
        var iX = self._oDataTable.fnGetPosition( event.currentTarget )[ 1 ];        
        if ( !self._aoColumns[ iX ].bProtected ) {
            self._fnFocusout( event.currentTarget );
        }
    } );
}

/*
* Function: _fnRegisterKeyboard
* Purpose:  Register keyboard callbacks on all cells of this table. The callback 
*           itself will just simply forward the click event directly to the 
*           respective column object, after blurring any current focused cell,
*           setting the focus to the focused cell and looking up the cell in the
*           DataTable.
* Input(s): node:nTable - the jQuery set of the table root node
* Returns:  void
*
*/
SpreadSheet.prototype._fnRegisterKeyboard = function( nTable ) {
    var self = this;

    jQuery( document ).keydown( function( event ) {
        // find focused cells and look up whether they belong to our table
        var nFocus = jQuery( 'td.' + SpreadSheet.CSS.Focus );
        var nTable = nFocus.parents( '#' + self.fnGetId() );
        if ( nTable.length <= 0 ) return;

        // Escape
        if ( event.which == jQuery.ui.keyCode.ESCAPE ) {
            self._fnFocusout( nFocus );
            self._fnEscape( nFocus );
            event.preventDefault();
        //Enter
        } else if ( event.which == jQuery.ui.keyCode.ENTER ) {
            self._fnFocusout( nFocus );
            self._fnEnter( nFocus );
            event.preventDefault();
        // Shift + Tab
        } else if ( event.shiftKey && event.which == jQuery.ui.keyCode.TAB ) {
            self._fnFocusout( nFocus );
            self._fnMoveLeft( nFocus );
            event.preventDefault();
        // Tab
        } else if ( event.which == jQuery.ui.keyCode.TAB ) {
            self._fnFocusout( nFocus );
            self._fnMoveRight( nFocus );
            event.preventDefault();
        // Up arrow
        } else if ( event.which == jQuery.ui.keyCode.UP ) {
            self._fnFocusout( nFocus );
            self._fnMoveUp( nFocus );
            event.preventDefault();
        // Down arrow
        } else if ( event.which == jQuery.ui.keyCode.DOWN ) {
            self._fnFocusout( nFocus );
            self._fnMoveDown( nFocus );
            event.preventDefault();
        }
    } );
}

/*
* Function: _fnSanitizeParameters
* Purpose:  Ensures that the necessary options in the initializer object are set
            and that they are of the right type.
* Input(s): object:oInit - the initializer object to be sanitized.
* Returns:  object:oSanitized - the sanitized version of the passed one.
*
*/
SpreadSheet.prototype._fnSanitizeParameters = function( oInit ) {
    var oSanitized = jQuery.extend( {}, oInit );
    
    oSanitized.columns = oInit.columns || [];
    oSanitized.focus = oInit.focus || null;
    
    return oSanitized;
}

/*
* Function: _fnToVisibleColumn
* Purpose:  Transforms an index into the columns array (that can contain hidden 
            columns) into the respective column index as visually seen.
* Input(s): integer:iColumn - the hidden index
* Returns:  integer:iVisible - the visible index
*
*/
SpreadSheet.prototype._fnToVisibleColumn = function( iColumn ) {
    var aoColumns = this._oDataTable.fnSettings().aoColumns;
    var iVisible = -1;
    
    for ( var i = 0; i <= iColumn; i++ ) {
        if ( aoColumns[ i ].bVisible ) iVisible++;
    }
    
    return iVisible;
}
