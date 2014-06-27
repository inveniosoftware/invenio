/*
 * This file is part of Invenio.
 * Copyright (C) 2009, 2010, 2011 CERN.
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
 * Client side code related to hepnames update form
 */


//add a new row to the table
var rest = '.stanford.edu';
var goesto= 'slaclib2';
var goesalso='hepnames';
var place = '@slac';
var occcnt=1;
function OnSubmitCheck() {
	goestov=goesalso;
	goestov+=place;
	goestov+=rest;
	document.getElementById('formcont').value=goestov;
	var emx = emailCheck();
	var sbx = checksp();
	if((emx == false) || (sbx == false)) { return false; }
	return true;
}
function tmai() {
	goestov='mailto:';
	goestov+=goesalso;
	goestov+=place;
	goestov+=rest;
	location.href=goestov;
}
function copyem(){
	document.getElementById('email').value=document.getElementById('username').value
}
function addRow()
{
	//add a row to the rows collection and get a reference to the newly added row
	var tbl = document.getElementById("tblGrid");
	var lastRow = tbl.rows.length;
	var newRow = document.getElementById("tblGrid").insertRow(lastRow);
	var tempvar;
	occcnt++;
	//add 3 cells (<td>) to the new row and set the innerHTML to contain text boxes
	oCell = newRow.insertCell(0);
	oCell.innerHTML= "&nbsp;";
	var oCell = newRow.insertCell(1);
	tempvar = "<input name='aff.str' type='hidden'><input type='text' name='inst";
	tempvar += occcnt;
	tempvar +="' size='35'>";
	oCell.innerHTML = tempvar;
	oCell = newRow.insertCell(2);
	tempvar = "<select name='rank";
	tempvar += occcnt;
	tempvar += "'><option value=''> </option>";
	tempvar += "<option value='SENIOR'>Senior(permanent)</option>";
	tempvar += "<option value='JUNIOR'>Junior(leads to Senior)</option>";
	tempvar += "<option value='STAFF'>Staff(non-research)</option> <option value='VISITOR'>Visitor</option>";
	tempvar += "<option value='PD'>PostDoc</option><option value='PHD'>PhD</option>";
	tempvar += "<option value='MAS'>Masters</option><option value='UG'>Undergrad</option></select>";
	oCell.innerHTML = tempvar;
	oCell = newRow.insertCell(3);
	tempvar = "<input type='text' name='sy";
	tempvar += occcnt;
	tempvar += "' size='4'> &nbsp;&nbsp; <input type='text' name='ey";
	tempvar += occcnt;
	tempvar += "' size='4'>";
	oCell.innerHTML= tempvar;
	oCell = newRow.insertCell(4);
	tempvar = "<input type='CHECKBOX' value='Y' name='current";
	tempvar += occcnt;tempvar +="'> &nbsp;&nbsp; <input type='button' class='formbutton' value='Delete row' onclick='removeRow(this);'/>";
	oCell.innerHTML = tempvar;
}
//deletes the specified row from the table
function removeRow(src)
{
	var oRow = src.parentNode.parentNode;
	//once the row reference is obtained, delete it passing in its rowIndex
	document.getElementById("tblGrid").deleteRow(oRow.rowIndex);
}
function checksp()
{
	alertmsg = document.getElementById('beatspam').value
	alertmsg += ', '
	alertmsg += document.getElementById('imgval').value
	if(document.getElementById('beatspam').value != document.getElementById('imgval').value)
	{
		alert('Please select number of People in the image')
		return false;
	}
	goestovar = goesto;
	goestovar += place;
	goestovar += rest;
	document.getElementById('tofield').value = goestovar;
}
function emailCheck () {
	var emailStr=document.getElementById('username').value;
	var checkTLD=1;
	var knownDomsPat=/^(com|net|org|edu|int|mil|gov|arpa|biz|aero|name|coop|info|pro|museum)$/;
	var emailPat=/^(.+)@(.+)$/;
	var specialChars="\\(\\)><@,;:\\\\\\\"\\.\\[\\]";
	/* The following string represents the range of characters allowed in a
	username or domainname.  It really states which chars arent allowed.*/
	var validChars="\[^\\s" + specialChars + "\]";
	/* The following pattern applies if the "user" is a quoted string (in
		which case, there are no rules about which characters are allowed
		and which arent; anything goes).  E.g. "jiminy cricket"@disney.com
		is a legal e-mail address. */
		var quotedUser="(\"[^\"]*\")";
		/* The following pattern applies for domains that are IP addresses,
		rather than symbolic names.  E.g. joe@[123.124.233.4] is a legal
		e-mail address. NOTE: The square brackets are required. */
		var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/;
		/* The following string represents an atom (basically a series of non-special characters.) */
		var atom=validChars + '+';
		/* The following string represents one word in the typical username.
		For example, in john.doe@somewhere.com, john and doe are words.
		Basically, a word is either an atom or quoted string. */
		var word="(" + atom + "|" + quotedUser + ")";
		// The following pattern describes the structure of the user
		var userPat=new RegExp("^" + word + "(\\." + word + ")*$");
		/* The following pattern describes the structure of a normal symbolic domain */
		var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$");
		/* Finally, lets start trying to figure out if the supplied address is valid. */
		/* Begin with the coarse pattern to simply break up user@domain into
		different pieces that are easy to analyze. */
		var matchArray=emailStr.match(emailPat);
		if (matchArray==null) {
			/* Too many/few @s or something; basically, this address doesnt
			even fit the general mould of a valid e-mail address. */
			alert("Email address seems incorrect (check @ and .'s)");
			return false;
		}
		var user=matchArray[1];
		var domain=matchArray[2];
		// Start by checking that only basic ASCII characters are in the strings (0-127).
		for (i=0; i<user.length; i++) {
			if (user.charCodeAt(i)>127) {
				alert("Ths username contains invalid characters.");
				return false;
			}
		}
		for (i=0; i<domain.length; i++) {
			if (domain.charCodeAt(i)>127) {
				alert("Ths domain name contains invalid characters.");
				return false;
			}
		}
		// See if "user" is valid
		if (user.match(userPat)==null) {
			// user is not valid
			alert("The username doesnt seem to be valid.");
			return false;
		}
		/* if the e-mail address is at an IP address (as opposed to a symbolic
			host name) make sure the IP address is valid. */
			var IPArray=domain.match(ipDomainPat);
			if (IPArray!=null) {
				// this is an IP address
				for (var i=1;i<=4;i++) {
					if (IPArray[i]>255) {
						alert("Destination IP address is invalid!");
						return false;
					}
				}
				return true;
			}
			// Domain is symbolic name.  Check if itsvalid.
			var atomPat=new RegExp("^" + atom + "$");
			var domArr=domain.split(".");
			var len=domArr.length;
			for (i=0;i<len;i++) {
				if (domArr[i].search(atomPat)==-1) {
					alert("The domain name does not seem to be valid.");
					return false;
				}
			}
			/* domain name seems valid, but now make sure that it ends in a
			known top-level domain (like com, edu, gov) or a two-letter word,
			representing country (uk, nl), and that theresahostnamepreceding
			the domain or country. */
			if (checkTLD && domArr[domArr.length-1].length!=2 &&
				domArr[domArr.length-1].search(knownDomsPat)==-1) {
					alert("The address must end in a well-known domain or two letter " + "country.");
					return false;
				}
				// Make sure theresahostnameprecedingthedomain.
				if (len<2) {
					alert("This address is missing a hostname!");
					return false;
				}
				// If weve gotten this far, everythingsvalid!
				return true;
}
