// JS QuickTags version 1.2
//
// Copyright (c) 2002-2005 Alex King
// http://www.alexking.org/
//
// Licensed under the LGPL license
// http://www.gnu.org/copyleft/lesser.html
//
// **********************************************************************
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
// **********************************************************************
//
// This JavaScript will insert the tags below at the cursor position in IE and 
// Gecko-based browsers (Mozilla, Camino, Firefox, Netscape). For browsers that 
// do not support inserting at the cursor position (Safari, OmniWeb) it appends
// the tags to the end of the content.
//
// The variable 'edCanvas' must be defined as the <textarea> element you want 
// to be editing in. See the accompanying 'index.html' page for an example.

var edButtons = new Array();
var edLinks = new Array();
var edOpenTags = new Array();

function edButton(id, display, tagStart, tagEnd, access, open) {
	this.id = id;				// used to name the toolbar button
	this.display = display;		// label on button
	this.tagStart = tagStart; 	// open tag
	this.tagEnd = tagEnd;		// close tag
	this.access = access;			// set to -1 if tag does not need to be closed
	this.open = open;			// set to -1 if tag does not need to be closed
}

edButtons.push(
	new edButton(
		'ed_bold'
		,'B'
		,'<strong>'
		,'</strong>'
		,'b'
	)
);

edButtons.push(
	new edButton(
		'ed_italic'
		,'I'
		,'<em>'
		,'</em>'
		,'i'
	)
);

edButtons.push(
	new edButton(
		'ed_link'
		,'Link'
		,''
		,'</a>'
		,'a'
	)
); // special case

edButtons.push(
	new edButton(
		'ed_ext_link'
		,'Ext. Link'
		,''
		,'</a>'
		,'e'
	)
); // special case

edButtons.push(
	new edButton(
		'ed_img'
		,'IMG'
		,''
		,''
		,'m'
		,-1
	)
); // special case

edButtons.push(
	new edButton(
		'ed_ul'
		,'UL'
		,'<ul>\n'
		,'</ul>\n\n'
		,'u'
	)
);

edButtons.push(
	new edButton(
		'ed_ol'
		,'OL'
		,'<ol>\n'
		,'</ol>\n\n'
		,'o'
	)
);

edButtons.push(
	new edButton(
		'ed_li'
		,'LI'
		,'\t<li>'
		,'</li>\n'
		,'l'
	)
);

edButtons.push(
	new edButton(
		'ed_p'
		,'P'
		,'<p>'
		,'</p>\n\n'
		,'p'
	)
);

var extendedStart = edButtons.length;

// below here are the extended buttons

edButtons.push(
	new edButton(
		'ed_h1'
		,'H1'
		,'<h1>'
		,'</h1>\n\n'
		,'1'
	)
);

edButtons.push(
	new edButton(
		'ed_h2'
		,'H2'
		,'<h2>'
		,'</h2>\n\n'
		,'2'
	)
);

edButtons.push(
	new edButton(
		'ed_h3'
		,'H3'
		,'<h3>'
		,'</h3>\n\n'
		,'3'
	)
);

edButtons.push(
	new edButton(
		'ed_h4'
		,'H4'
		,'<h4>'
		,'</h4>\n\n'
		,'4'
	)
);

edButtons.push(
	new edButton(
		'ed_block'
		,'B-QUOTE'
		,'<blockquote>'
		,'</blockquote>'
		,'q'
	)
);

edButtons.push(
	new edButton(
		'ed_code'
		,'CODE'
		,'<code>'
		,'</code>'
		,'c'
	)
);

edButtons.push(
	new edButton(
		'ed_pre'
		,'PRE'
		,'<pre>'
		,'</pre>'
	)
);

edButtons.push(
	new edButton(
		'ed_dl'
		,'DL'
		,'<dl>\n'
		,'</dl>\n\n'
	)
);

edButtons.push(
	new edButton(
		'ed_dt'
		,'DT'
		,'\t<dt>'
		,'</dt>\n'
	)
);

edButtons.push(
	new edButton(
		'ed_dd'
		,'DD'
		,'\t<dd>'
		,'</dd>\n'
	)
);

edButtons.push(
	new edButton(
		'ed_table'
		,'TABLE'
		,'<table>\n<tbody>'
		,'</tbody>\n</table>\n'
	)
);

edButtons.push(
	new edButton(
		'ed_tr'
		,'TR'
		,'\t<tr>\n'
		,'\n\t</tr>\n'
	)
);

edButtons.push(
	new edButton(
		'ed_td'
		,'TD'
		,'\t\t<td>'
		,'</td>\n'
	)
);

edButtons.push(
	new edButton(
		'ed_under'
		,'U'
		,'<u>'
		,'</u>'
	)
);

edButtons.push(
	new edButton(
		'ed_strike'
		,'S'
		,'<s>'
		,'</s>'
	)
);

edButtons.push(
	new edButton(
		'ed_nobr'
		,'NOBR'
		,'<nobr>'
		,'</nobr>'
	)
);

edButtons.push(
	new edButton(
		'ed_footnote'
		,'Footnote'
		,''
		,''
		,'f'
	)
);

function edLink(display, URL, newWin) {
	this.display = display;
	this.URL = URL;
	if (!newWin) {
		newWin = 0;
	}
	this.newWin = newWin;
}


edLinks[edLinks.length] = new edLink('alexking.org'
                                    ,'http://www.alexking.org/'
                                    );

function edShowButton(button, i) {
	if (button.access) {
		var accesskey = ' accesskey = "' + button.access + '"'
	}
	else {
		var accesskey = '';
	}
	switch (button.id) {
		case 'ed_img':
			document.write('<input type="button" id="' + button.id + '" ' + accesskey + ' class="ed_button" onclick="edInsertImage(edCanvas);" value="' + button.display + '" />');
			break;
		case 'ed_link':
			document.write('<input type="button" id="' + button.id + '" ' + accesskey + ' class="ed_button" onclick="edInsertLink(edCanvas, ' + i + ');" value="' + button.display + '" />');
			break;
		case 'ed_ext_link':
			document.write('<input type="button" id="' + button.id + '" ' + accesskey + ' class="ed_button" onclick="edInsertExtLink(edCanvas, ' + i + ');" value="' + button.display + '" />');
			break;
		case 'ed_footnote':
			document.write('<input type="button" id="' + button.id + '" ' + accesskey + ' class="ed_button" onclick="edInsertFootnote(edCanvas);" value="' + button.display + '" />');
			break;
		default:
			document.write('<input type="button" id="' + button.id + '" ' + accesskey + ' class="ed_button" onclick="edInsertTag(edCanvas, ' + i + ');" value="' + button.display + '"  />');
			break;
	}
}

function edShowLinks() {
	var tempStr = '<select onchange="edQuickLink(this.options[this.selectedIndex].value, this);"><option value="-1" selected>(Quick Links)</option>';
	for (i = 0; i < edLinks.length; i++) {
		tempStr += '<option value="' + i + '">' + edLinks[i].display + '</option>';
	}
	tempStr += '</select>';
	document.write(tempStr);
}

function edAddTag(button) {
	if (edButtons[button].tagEnd != '') {
		edOpenTags[edOpenTags.length] = button;
		document.getElementById(edButtons[button].id).value = '/' + document.getElementById(edButtons[button].id).value;
	}
}

function edRemoveTag(button) {
	for (i = 0; i < edOpenTags.length; i++) {
		if (edOpenTags[i] == button) {
			edOpenTags.splice(i, 1);
			document.getElementById(edButtons[button].id).value = 		document.getElementById(edButtons[button].id).value.replace('/', '');
		}
	}
}

function edCheckOpenTags(button) {
	var tag = 0;
	for (i = 0; i < edOpenTags.length; i++) {
		if (edOpenTags[i] == button) {
			tag++;
		}
	}
	if (tag > 0) {
		return true; // tag found
	}
	else {
		return false; // tag not found
	}
}	

function edCloseAllTags() {
	var count = edOpenTags.length;
	for (o = 0; o < count; o++) {
		edInsertTag(edCanvas, edOpenTags[edOpenTags.length - 1]);
	}
}

function edQuickLink(i, thisSelect) {
	if (i > -1) {
		var newWin = '';
		if (edLinks[i].newWin == 1) {
			newWin = ' target="_blank"';
		}
		var tempStr = '<a href="' + edLinks[i].URL + '"' + newWin + '>' 
		            + edLinks[i].display
		            + '</a>';
		thisSelect.selectedIndex = 0;
		edInsertContent(edCanvas, tempStr);
	}
	else {
		thisSelect.selectedIndex = 0;
	}
}

function edSpell(myField, docurl) {
	var word = '';
	if (document.selection) {
		myField.focus();
	    var sel = document.selection.createRange();
		if (sel.text.length > 0) {
			word = sel.text;
		}
	}
	else if (myField.selectionStart || myField.selectionStart == '0') {
		var startPos = myField.selectionStart;
		var endPos = myField.selectionEnd;
		if (startPos != endPos) {
			word = myField.value.substring(startPos, endPos);
		}
	}
	if (word == '') {
		word = prompt('Enter a format element name to look up:', '');
	}
	if (word != '') {
           word = word.replace( /^\s+/g, "" ); // remove leading white space

           var words = new Array(); 
           words = word.split(' ');
           word = words[0] // take only element name
           if (word.substring(0,1) == '<'){ // remove start of tag
                word = word.substring(1,word.length)
           }
           if (word.substring(0,4).toLowerCase() == 'bfe_'){ // remove bfe_
                word = word.substring(4,word.length)
           }
           word = word.toUpperCase() //use upper case
           window.open(docurl +'#'+ escape(word));
	}
}

function edToolbar(docurl) {
	document.write('<div id="ed_toolbar"><span>');
	for (i = 0; i < extendedStart; i++) {
		edShowButton(edButtons[i], i);
	}
	if (edShowExtraCookie()) {
		document.write(
			'<input type="button" id="ed_close" class="ed_button" onclick="edCloseAllTags();" value="Close Tags" />'
			+ '<input type="button" id="ed_spell" class="ed_button" onclick="edSpell(edCanvas,\''+ docurl+'\');" value="Element Doc" />'
			+ '<input type="button" id="ed_extra_show" class="ed_button" onclick="edShowExtra()" value="&raquo;" style="visibility: hidden;" />'
			+ '</span><br />'
			+ '<span id="ed_extra_buttons">'
			+ '<input type="button" id="ed_extra_hide" class="ed_button" onclick="edHideExtra();" value="&laquo;" />'
		);
	}
	else {
		document.write(
			'<input type="button" id="ed_close" class="ed_button" onclick="edCloseAllTags();" value="Close Tags" />'
			+ '<input type="button" id="ed_spell" class="ed_button" onclick="edSpell(edCanvas,\''+ docurl+'\');" value="Element Doc" />'
			+ '<input type="button" id="ed_extra_show" class="ed_button" onclick="edShowExtra()" value="&raquo;" />'
			+ '</span><br />'
			+ '<span id="ed_extra_buttons" style="display: none;">'
			+ '<input type="button" id="ed_extra_hide" class="ed_button" onclick="edHideExtra();" value="&laquo;" />'
		);
	}
	for (i = extendedStart; i < edButtons.length; i++) {
		edShowButton(edButtons[i], i);
	}
	document.write('</span>');
//	edShowLinks();
	document.write('</div>');
}

function edShowExtra() {
	document.getElementById('ed_extra_show').style.visibility = 'hidden';
	document.getElementById('ed_extra_buttons').style.display = 'block';
	edSetCookie(
		'js_quicktags_extra'
		, 'show'
		, new Date("December 31, 2100")
	);
}

function edHideExtra() {
	document.getElementById('ed_extra_buttons').style.display = 'none';
	document.getElementById('ed_extra_show').style.visibility = 'visible';
	edSetCookie(
		'js_quicktags_extra'
		, 'hide'
		, new Date("December 31, 2100")
	);
}

// insertion code

function edInsertTag(myField, i) {
	//IE support
	if (document.selection) {
		myField.focus();
	    sel = document.selection.createRange();
		if (sel.text.length > 0) {
			sel.text = edButtons[i].tagStart + sel.text + edButtons[i].tagEnd;
		}
		else {
			if (!edCheckOpenTags(i) || edButtons[i].tagEnd == '') {
				sel.text = edButtons[i].tagStart;
				edAddTag(i);
			}
			else {
				sel.text = edButtons[i].tagEnd;
				edRemoveTag(i);
			}
		}
		myField.focus();
	}
	//MOZILLA/NETSCAPE support
	else if (myField.selectionStart || myField.selectionStart == '0') {
		var startPos = myField.selectionStart;
		var endPos = myField.selectionEnd;
		var cursorPos = endPos;
		var scrollTop = myField.scrollTop;
		if (startPos != endPos) {
			myField.value = myField.value.substring(0, startPos)
			              + edButtons[i].tagStart
			              + myField.value.substring(startPos, endPos) 
			              + edButtons[i].tagEnd
			              + myField.value.substring(endPos, myField.value.length);
			cursorPos += edButtons[i].tagStart.length + edButtons[i].tagEnd.length;
		}
		else {
			if (!edCheckOpenTags(i) || edButtons[i].tagEnd == '') {
				myField.value = myField.value.substring(0, startPos) 
				              + edButtons[i].tagStart
				              + myField.value.substring(endPos, myField.value.length);
				edAddTag(i);
				cursorPos = startPos + edButtons[i].tagStart.length;
			}
			else {
				myField.value = myField.value.substring(0, startPos) 
				              + edButtons[i].tagEnd
				              + myField.value.substring(endPos, myField.value.length);
				edRemoveTag(i);
				cursorPos = startPos + edButtons[i].tagEnd.length;
			}
		}
		myField.focus();
		myField.selectionStart = cursorPos;
		myField.selectionEnd = cursorPos;
		myField.scrollTop = scrollTop;
	}
	else {
		if (!edCheckOpenTags(i) || edButtons[i].tagEnd == '') {
			myField.value += edButtons[i].tagStart;
			edAddTag(i);
		}
		else {
			myField.value += edButtons[i].tagEnd;
			edRemoveTag(i);
		}
		myField.focus();
	}
}

function edInsertContent(myField, myValue) {
	//IE support
	if (document.selection) {
		myField.focus();
		sel = document.selection.createRange();
		sel.text = myValue;
		myField.focus();
	}
	//MOZILLA/NETSCAPE support
	else if (myField.selectionStart || myField.selectionStart == '0') {
		var startPos = myField.selectionStart;
		var endPos = myField.selectionEnd;
		var scrollTop = myField.scrollTop;
		myField.value = myField.value.substring(0, startPos)
		              + myValue 
                      + myField.value.substring(endPos, myField.value.length);
		myField.focus();
		myField.selectionStart = startPos + myValue.length;
		myField.selectionEnd = startPos + myValue.length;
		myField.scrollTop = scrollTop;
	} else {
		myField.value += myValue;
		myField.focus();
	}
}

function edInsertLink(myField, i, defaultValue) {
	if (!defaultValue) {
		defaultValue = 'http://';
	}
	if (!edCheckOpenTags(i)) {
		var URL = prompt('Enter the URL' ,defaultValue);
		if (URL) {
			edButtons[i].tagStart = '<a href="' + URL + '">';
			edInsertTag(myField, i);
		}
	}
	else {
		edInsertTag(myField, i);
	}
}

function edInsertExtLink(myField, i, defaultValue) {
	if (!defaultValue) {
		defaultValue = 'http://';
	}
	if (!edCheckOpenTags(i)) {
		var URL = prompt('Enter the URL' ,defaultValue);
		if (URL) {
			edButtons[i].tagStart = '<a href="' + URL + '" rel="external">';
			edInsertTag(myField, i);
		}
	}
	else {
		edInsertTag(myField, i);
	}
}

function edInsertImage(myField) {
	var myValue = prompt('Enter the URL of the image', 'http://');
	if (myValue) {
		myValue = '<img src="' 
				+ myValue 
				+ '" alt="' + prompt('Enter a description of the image', '') 
				+ '" />';
		edInsertContent(myField, myValue);
	}
}

function edInsertFootnote(myField) {
	var note = prompt('Enter the footnote:', '');
	if (!note || note == '') {
		return false;
	}
	var now = new Date;
	var fnId = 'fn' + now.getTime();
	var fnStart = edCanvas.value.indexOf('<ol class="footnotes">');
	if (fnStart != -1) {
		var fnStr1 = edCanvas.value.substring(0, fnStart)
		var fnStr2 = edCanvas.value.substring(fnStart, edCanvas.value.length)
		var count = countInstances(fnStr2, '<li id="') + 1;
	}
	else {
		var count = 1;
	}
	var count = '<sup><a href="#' + fnId + 'n" id="' + fnId + '" class="footnote">' + count + '</a></sup>';
	edInsertContent(edCanvas, count);
	if (fnStart != -1) {
		fnStr1 = edCanvas.value.substring(0, fnStart + count.length)
		fnStr2 = edCanvas.value.substring(fnStart + count.length, edCanvas.value.length)
	}
	else {
		var fnStr1 = edCanvas.value;
		var fnStr2 = "\n\n" + '<ol class="footnotes">' + "\n"
		           + '</ol>' + "\n";
	}
	var footnote = '	<li id="' + fnId + 'n">' + note + ' [<a href="#' + fnId + '">back</a>]</li>' + "\n"
				 + '</ol>';
	edCanvas.value = fnStr1 + fnStr2.replace('</ol>', footnote);
}

function countInstances(string, substr) {
	var count = string.split(substr);
	return count.length - 1;
}

function edSetCookie(name, value, expires, path, domain) {
	document.cookie= name + "=" + escape(value) +
		((expires) ? "; expires=" + expires.toGMTString() : "") +
		((path) ? "; path=" + path : "") +
		((domain) ? "; domain=" + domain : "");
}

function edShowExtraCookie() {
	var cookies = document.cookie.split(';');
	for (var i=0;i < cookies.length; i++) {
		var cookieData = cookies[i];
		while (cookieData.charAt(0) ==' ') {
			cookieData = cookieData.substring(1, cookieData.length);
		}
		if (cookieData.indexOf('js_quicktags_extra') == 0) {
			if (cookieData.substring(19, cookieData.length) == 'show') {
				return true;
			}
			else {
				return false;
			}
		}
	}
	return false;
}
