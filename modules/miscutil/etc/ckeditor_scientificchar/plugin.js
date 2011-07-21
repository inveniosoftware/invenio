/*
 * This file is part of Invenio.
 * Copyright (C) 2011 CERN.
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
/**
 * @file Scientific Character plugin
 * Inspired by the 'specialchar' plugin from Frederico Knabben <http://ckeditor.com/>
 */

CKEDITOR.plugins.add( 'scientificchar',
{
    // List of available localizations.
    availableLangs : { en:1, fr:1 },

    init : function( editor )
    {
	var pluginName = 'scientificchar',
	plugin = this;

	// Register the dialog.
	CKEDITOR.dialog.add( pluginName, this.path + 'dialogs/scientificchar.js' );

	editor.addCommand( pluginName,
			   {
			       exec : function()
			       {
				   var langCode = editor.langCode;
				   langCode = plugin.availableLangs[ langCode ] ? langCode : 'en';

				   CKEDITOR.scriptLoader.load(
				       CKEDITOR.getUrl( plugin.path + 'lang/' + langCode + '.js' ),
				       function()
				       {
					   //editor.lang.scientificChar = plugin.langEntries[ langCode ];
					   editor.openDialog( pluginName );
				       });
			       },
			       modes : { wysiwyg:1 },
			       canUndo : false
			   });

	// Register the toolbar button.
	editor.ui.addButton( 'ScientificChar',
			     {
				 label : 'Scientific Characters',//editor.lang.scientificChar.toolbar,
				 command : pluginName,
				 icon : this.path + 'ScientificChar.gif'
			     });
    }
} );

/**
  * The list of special characters visible in Special Character dialog.
  * @type Array
  * @example
  * config.scientificChars = [ '&quot;', '&rsquo;', [ '&custom;', 'Custom label' ] ];
  * config.scientificChars = config.scientificChars.concat( [ '&quot;', [ '&rsquo;', 'Custom label' ] ] );
  */
CKEDITOR.config.scientificChars =
	[
	"&fnof;","&Alpha;","&Beta;","&Gamma;","&Delta;","&Epsilon;","&Zeta;","&Eta;","&Theta;","&Iota;","&Kappa;","&Lambda;","&Mu;","&Nu;","&Xi;","&Omicron;","&Pi;","&Rho;","&Sigma;","&Tau;","&Upsilon;","&Phi;","&Chi;","&Psi;","&Omega;","&alpha;","&beta;","&gamma;","&delta;","&epsilon;","&zeta;","&eta;","&theta;","&iota;","&kappa;","&lambda;","&mu;","&nu;","&xi;","&omicron;","&pi;","&rho;","&sigmaf;","&sigma;","&tau;","&upsilon;","&phi;","&chi;","&psi;","&omega;","&thetasym;","&upsih;","&piv;","&bull;","&hellip;","&prime;","&Prime;","&oline;","&frasl;","&weierp;","&image;","&real;","&alefsym;","&larr;","&uarr;","&rarr;","&darr;","&harr;","&crarr;","&lArr;","&uArr;","&rArr;","&dArr;","&hArr;","&forall;","&part;","&exist;","&empty;","&nabla;","&isin;","&notin;","&ni;","&prod;","&sum;","&minus;","&lowast;","&radic;","&prop;","&infin;","&ang;","&and;","&or;","&cap;","&cup;","&int;","&there4;","&sim;","&cong;","&asymp;","&ne;","&equiv;","&le;","&ge;","&sub;","&sup;","&nsub;","&sube;","&supe;","&oplus;","&otimes;","&perp;","&sdot;","&lceil;","&rceil;","&lfloor;","&rfloor;","&lang;","&rang;","&loz;"
	];