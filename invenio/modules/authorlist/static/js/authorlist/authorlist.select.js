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

( function( jQuery ) {
    AuthorlistSelectCSS = {
        'Select'        : 'AuthorlistSelect',
        'Text'          : 'AuthorlistText',
        'Icon'          : 'AuthorlistIcon ui-icon ui-icon-triangle-1-s'
    }

    jQuery.fn.extend( {
        authorlist_select : function( oSettings ) {
            return this.each( function() {            
                var nText = jQuery( '<span>' );
                nText.addClass( AuthorlistSelectCSS.Text );
                
                var nIcon = jQuery( '<span>' );
                nIcon.addClass( AuthorlistSelectCSS.Icon );
                
                var nSelect = jQuery( '<select>' );
                nSelect.addClass( AuthorlistSelectCSS.Select );
                nSelect.css( 'opacity', 0 );
                
                var aOptions = oSettings.options;
                for ( var i = 0, iLen = aOptions.length; i < iLen; i++ ) {
                    var sOption = aOptions[i];
                    var sSelected = sOption == oSettings.value ? ' selected' : '';
                    var nOption = jQuery( '<option' + sSelected + '>' );
                    
                    nOption.text( sOption );
                    if ( sOption == oSettings.value ) {
                        nText.text( sOption );
                    }
                    nSelect.append( nOption );
                }
                
                var self = jQuery( this );
                self.append( nText, nIcon, nSelect );
            } );
        }
    } );
    
    jQuery( 'select.' + AuthorlistSelectCSS.Select ).live( 'change', function( event ) {
        var nSelect = jQuery( event.target );
        var nText = nSelect.siblings( 'span.' + AuthorlistSelectCSS.Text );
        
        nText.text( jQuery( ':selected', nSelect ).val() );
    } );
} )( jQuery );
