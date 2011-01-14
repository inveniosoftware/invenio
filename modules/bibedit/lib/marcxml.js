/*
 * This file is part of Invenio.
 * Copyright (C) 2010, 2011 CERN.
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


/* A file contatining fuctions treating the MARC XML on the client side. */




function decodeMarcXMLRecord(marcXml){
  /*Function taking the MARC XML representation of a recoprd and producing
    a record encoded in the JavaScript data types */
  var xmlStructureException = "Wrong structure of teh input XML";
  var resultRecord = {};

  if (window.DOMParser)
  {
    parser=new DOMParser();
    xmlDoc=parser.parseFromString(marcXml, "text/xml");
  }else{
    // Internet Explorer
    xmlDoc=new ActiveXObject("Microsoft.XMLDOM");
    xmlDoc.async="false";
    xmlDoc.loadXML(marcXml);
  }

  if (xmlDoc.documentElement.nodeName == "parsererror"){
    throw xmlStructureException;
  }

  fields = xmlDoc.firstChild.childNodes;

  for (fieldId=0; fieldId < fields.length; fieldId++ ){
    field = fields[fieldId];

    // first parsing the attributes
    var tag = field.getAttribute("tag");

    if (tag == null){
      throw xmlStructureException;
    }

    var resultField = [[], "", "", "", 0];

    // treating the field itself
    if (field.localName == "datafield"){
      // a normal data field
      // generating the subfields based on the child elements
      var ind1 = field.getAttribute("ind1");
      var ind2 = field.getAttribute("ind2");
      if (ind1 == null || ind2 == null){
        throw xmlStructureException;
      }

      var resultSubfields = [];
      var subfields = field.childNodes;
      for (subfieldId = 0; subfieldId < subfields.length; subfieldId++){
        subfield = subfields[subfieldId];
        code = subfield.getAttribute("code");
        if (code == null){
          throw xmlStructureException;
        }
        value = subfield.textContent;
        pos = resultSubfields.length;
        resultSubfields[pos] = [code, value];
      }

      resultField[0] = resultSubfields;
      resultField[1] = ind1;
      resultField[2] = ind2;

    } else {
      if (field.localName == "controlfield"){
        // a control field
        resultField[3] = field.textContent;
      }
      else{
        throw xmlStructureException;
      }
    }
    // now appending the field to the result
    if (resultRecord[tag] == undefined){
      resultRecord[tag] = [];
    }
    var newPos = resultRecord[tag].length;
    resultRecord[tag][newPos] = resultField;
  }

  return resultRecord;
}
