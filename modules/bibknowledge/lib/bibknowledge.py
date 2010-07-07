# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Provide API-callable functions for knowledge base management (using kb's).
"""

from invenio import bibknowledge_dblayer
from invenio.bibformat_config  import CFG_BIBFORMAT_ELEMENTS_PATH
from invenio.config import CFG_WEBDIR
import os
import re
import libxml2
import libxslt

def get_kb_mappings(kb_name="", key="", value="", match_type="s"):
    """Get mappings from kb kb_name. If key given, give only those with
       left side (mapFrom) = key. If value given, give only those with
       right side (mapTo) = value.
       @param kb_name: the name of the kb
       @param key: include only lines matching this on left side in the results
       @param value: include only lines matching this on right side in the results
       @param match_type: s = substring match, e = exact match
       @return a list of mappings
    """
    return bibknowledge_dblayer.get_kb_mappings(kb_name,
                                         keylike=key, valuelike=value,
                                         match_type=match_type)

def get_kb_mapping(kb_name="", key="", value="", match_type="e", default=""):
    """Get one unique mapping. If not found, return default
       @param kb_name: the name of the kb
       @param key: include only lines matching this on left side in the results
       @param value: include only lines matching this on right side in the results
       @param match_type: s = substring match, e = exact match
       @return a mapping
    """
    mappings = bibknowledge_dblayer.get_kb_mappings(kb_name,
                                         keylike=key, valuelike=value,
                                         match_type=match_type)
    if len(mappings) == 0:
        return default
    else:
        return mappings[0]

def add_kb_mapping(kb_name, key, value=""):
    """
    Adds a new mapping to given kb

    @param kb_name: the name of the kb where to insert the new value
    @param key: the key of the mapping
    @param value: the value of the mapping
    """
    bibknowledge_dblayer.add_kb_mapping(kb_name, key, value)

def remove_kb_mapping(kb_name, key):
    """
    Delete an existing kb mapping in kb

    @param kb_name: the name of the kb where to insert the new value
    @param key: the key of the mapping
    """
    bibknowledge_dblayer.remove_kb_mapping(kb_name, key)

def update_kb_mapping(kb_name, old_key, key, value):
    """
    Update an existing kb mapping with key old_key with a new key and value

    @param kb_name: the name of the kb where to insert the new value
    @param old_key: the key of the mapping in the kb
    @param key: the new key of the mapping
    @param value: the new value of the mapping
    """
    #check if this is a KEY change or a VALUE change.
    if (old_key == key):
    #value change, ok to change
        bibknowledge_dblayer.update_kb_mapping(kb_name, old_key, key, value)
    else:
        #you can change a key unless there is already a key like that
        if kb_mapping_exists(kb_name, key):
            pass #no, don't change
        else:
            bibknowledge_dblayer.update_kb_mapping(kb_name, old_key, key, value)

def kb_exists(kb_name):
    """Returns True if a kb with the given name exists
       @param kb_name: the name of the knowledge base
    """
    return bibknowledge_dblayer.kb_exists(kb_name)

def get_kb_name(kb_id):
    """
    Returns the name of the kb given by id
    @param kb_id: the id of the knowledge base
    """
    return bibknowledge_dblayer.get_kb_name(kb_id)

def update_kb_attributes(kb_name, new_name, new_description):
    """
    Updates given kb_name with a new name and new description

    @param kb_name: the name of the kb to update
    @param new_name: the new name for the kb
    @param new_description: the new description for the kb
    """
    bibknowledge_dblayer.update_kb(kb_name, new_name, new_description)

def add_kb(kb_name="Untitled", kb_type=None):
    """
    Adds a new kb in database, and returns its id
    The name of the kb will be 'Untitled#'
    such that it is unique.

    @param kb_name: the name of the kb
    @param kb_type: the type of the kb, incl 'taxonomy' and 'dynamic'.
                   None for typical (leftside-rightside).
    @return the id of the newly created kb
    """
    name = kb_name
    i = 1
    while bibknowledge_dblayer.kb_exists(name):
        name = kb_name + " " + str(i)
        i += 1
    kb_id = bibknowledge_dblayer.add_kb(name, "", kb_type)
    return kb_id

def kb_mapping_exists(kb_name, key):
    """
    Returns the information if a mapping exists.
    @param kb_name: knowledge base name
    @param key: left side (mapFrom)
    """
    return  bibknowledge_dblayer.kb_mapping_exists(kb_name, key)

def delete_kb(kb_name):
    """
    Deletes given kb from database
    @param kb_name: knowledge base name
    """
    bibknowledge_dblayer.delete_kb(kb_name)

def get_kb_id(kb_name):
    """
    Gets the id by name
    @param kb_name knowledge base name
    """
    return bibknowledge_dblayer.get_kb_id(kb_name)

# Knowledge Bases Dependencies
##

def get_elements_that_use_kb(name):
    """
    This routine is obsolete.
    Returns a list of elements that call given kb

    [ {'filename':"filename_1.py"
       'name': "a name"
      },
      ...
    ]

    Returns elements sorted by name
    """

    format_elements = {}
    #Retrieve all elements in files
    files = os.listdir(CFG_BIBFORMAT_ELEMENTS_PATH)
    for filename in files:
        if filename.endswith(".py"):
            path = CFG_BIBFORMAT_ELEMENTS_PATH + os.sep + filename
            formatf = open(path, 'r')
            code = formatf.read()
            formatf.close()
            # Search for use of kb inside code
            kb_pattern = re.compile('''
            (bfo.kb)\s*                #Function call
            \(\s*                      #Opening parenthesis
            [\'"]+                     #Single or double quote
            (?P<kb>%s)                 #kb
            [\'"]+\s*                  #Single or double quote
            ,                          #comma
            ''' % name, re.VERBOSE | re.MULTILINE | re.IGNORECASE)

            result = kb_pattern.search(code)
            if result is not None:
                name = ("".join(filename.split(".")[:-1])).lower()
                if name.startswith("bfe_"):
                    name = name[4:]
                format_elements[name] = {'filename':filename, 'name': name}

    keys = format_elements.keys()
    keys.sort()
    return map(format_elements.get, keys)

###kb functions for export

def get_kbs_info(kbtype="", searchkbname=""):
    """A convenience method that calls dblayer
    @param kbtype: type of kb -- get only kb's of this type
    @param searchkbname: get only kb's where this sting appears in the name
    """
    return bibknowledge_dblayer.get_kbs_info(kbtype, searchkbname)

def get_kba_values(kb_name, searchname="", searchtype="s"):
    """
    Returns an array of values "authority file" type = just values.
    @param kb_name: name of kb
    @param searchname: get these values, according to searchtype
    @param searchtype: s=substring, e=exact
    """
    return bibknowledge_dblayer.get_kba_values(kb_name, searchname, searchtype)

def get_kbr_keys(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """
    Returns an array of keys.
    @param kb_name: the name of the knowledge base
    @param searchkey: search using this key
    @param searchvalue: search using this value
    @param searchtype: s = substring, e=exact
    """
    return bibknowledge_dblayer.get_kbr_keys(kb_name, searchkey,
                                             searchvalue, searchtype)

def get_kbr_values(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """
    Returns an array of keys.
       @param kb_name: the name of the knowledge base
       @param searchkey: search using this key
       @param searchvalue: search using this value
       @param searchtype: s = substring, e=exact
   """
    return bibknowledge_dblayer.get_kbr_values(kb_name, searchkey,
                                               searchvalue, searchtype)

def get_kbr_items(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """
    Returns a list of dictionaries that match the search.
    @param kb_name: the name of the knowledge base
    @param searchkey: search using this key
    @param searchvalue: search using this value
    @param searchtype: s = substring, e=exact
    @return a list of dictionaries [{'key'=>x, 'value'=>y},..]
    """
    return bibknowledge_dblayer.get_kbr_items(kb_name, searchkey,
                                              searchvalue, searchtype)

def get_kbd_values(kbname, searchwith=""):
    """
    To be used by bibedit. Returns a list of values based on a dynamic kb.
    @param kbname: name of the knowledge base
    @param searchwith: a term to search with
    """
    import search_engine

    #first check that the kb in question is dynamic
    kbid = bibknowledge_dblayer.get_kb_id(kbname)
    if not kbid:
        return []
    kbtype = bibknowledge_dblayer.get_kb_type(kbid)
    if not kbtype:
        return []
    if kbtype != 'd':
        return []
    #get the configuration so that we see what the field is
    confdict =  bibknowledge_dblayer.get_kb_dyn_config(kbid)
    if not confdict:
        return []
    if not confdict.has_key('field'):
        return []
    field = confdict['field']
    expression = confdict['expression']
    collection = ""
    if confdict.has_key('collection'):
        collection = confdict['collection']
    reclist = [] #return this
    #see if searchwith is a quoted expression
    if searchwith:
        if not searchwith.startswith("'"):
            searchwith = "'"+searchwith
        if not searchwith.endswith("'"):
            searchwith = searchwith+"'"
    if searchwith and expression:
        if (expression.count('%') > 0) or (expression.endswith(":*")):
            expression = expression.replace("%", searchwith)
            expression = expression.replace(":*", ':'+searchwith)
        else:
            #no %.. just make a combination
            expression = expression + "and "+searchwith
        reclist = search_engine.perform_request_search(p=expression,
                                                       cc=collection)
    else: #either no expr or no searchwith.. but never mind about searchwith
        if expression:
            reclist = search_engine.perform_request_search(p=expression, cc=collection)
        else:
            #make a fake expression so that only records that have this field
            #will be returned
            fake_exp = "/.*/"
            if searchwith:
                fake_exp = searchwith
            reclist = search_engine.perform_request_search(f=field, p=fake_exp, cc=collection)
    if reclist:
        fieldvaluelist = search_engine.get_most_popular_field_values(reclist,
                                                                     field)
        val_list = []
        for f in fieldvaluelist:
            (val, dummy) = f
            #support "starts with",
            #indicated by the * at the end of the searchstring
            if searchwith and (len(searchwith) > 2) and (searchwith[-2] == '*'):
                if (val.startswith(searchwith[1:-3])):
                    val_list.append(val)
            else:
                val_list.append(val)
        return val_list
    return [] #in case nothing worked

def get_kbd_values_for_bibedit(tag, collection="", searchwith=""):
    """
    A specific convenience method: based on a tag and collection, create a temporary dynamic knowledge base
    a return its values.
    Note: the performace of this function is ok compared to a plain
    perform req search / get most popular fields -pair. The overhead is about 5% with large record sets.
    @param tag: the tag like 100__a
    @param collection: collection id
    @param searchwith: the string to search. If empty, match all.
    """
    kb_id = add_kb(kb_name="tmp_dynamic", kb_type='dynamic')
    #get the kb name since it may be catenated by a number
    #in case there are concurrent calls.
    kb_name = get_kb_name(kb_id)
    bibknowledge_dblayer.save_kb_dyn_config(kb_id, tag, collection, searchwith)
    #now, get stuff
    myvalues = get_kbd_values(kb_name, searchwith)
    #the tmp dyn kb is now useless, delete it
    delete_kb(kb_name)
    return myvalues


def get_kbt_items(taxonomyfilename, templatefilename, searchwith=""):
    """
    Get items from taxonomy file using a templatefile. If searchwith is defined,
    return only items that match with it.
    @param taxonomyfilename: full path+name of the RDF file
    @param templatefile: full path+name of the XSLT file
    @param searchwith: a term to search with
    """
    styledoc = libxml2.parseFile(templatefilename)
    style = libxslt.parseStylesheetDoc(styledoc)
    doc = libxml2.parseFile(taxonomyfilename)
    result = style.applyStylesheet(doc, None)
    strres = style.saveResultToString(result)
    style.freeStylesheet()
    doc.freeDoc()
    result.freeDoc()
    ritems = []
    if len(strres) == 0:
        return []
    else:
        lines = strres.split("\n")
        for line in lines:
            if searchwith:
                if line.count(searchwith) > 0:
                    ritems.append(line)
            else:
                if len(line) > 0:
                    ritems.append(line)
    return ritems

def get_kbt_items_for_bibedit(kbtname, tag="", searchwith=""):
    """
    A simplifield, customized version of the function get_kbt_items.
    Traverses an RDF document. By default returns all leaves. If
    tag defined returns the content of that tag.
    If searchwith defined, returns leaves that match it.
    Warning! In order to make this faster, the matching field values
    cannot be multi-line!
    @param kbtname: name of the taxonony kb
    @param tag: name of tag whose content
    @param searchwith: a term to search with
    """
    #get the actual file based on the kbt name
    kb_id = get_kb_id(kbtname)
    if not kb_id:
        return []
    #get the rdf file..
    rdfname = CFG_WEBDIR+"/kbfiles/"+str(kb_id)+".rdf"
    if not os.path.exists(rdfname):
        return []
    #parse the doc with static xslt
    styledoc = libxml2.parseDoc("""
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">

  <xsl:output method="xml" standalone="yes" omit-xml-declaration="yes" indent="no"/>
  <xsl:template match="rdf:RDF">
    <foo><!--just having some tag here speeds up output by 10x-->
    <xsl:apply-templates />
    </foo>
  </xsl:template>

  <xsl:template match="*">
   <!--hi><xsl:value-of select="local-name()"/></hi-->
   <xsl:if test="local-name()='"""+tag+"""'">
     <myout><xsl:value-of select="normalize-space(.)"/></myout>
   </xsl:if>
   <!--traverse down in tree!-->
<xsl:text>
</xsl:text>
   <xsl:apply-templates />
  </xsl:template>

</xsl:stylesheet>
    """)
    style = libxslt.parseStylesheetDoc(styledoc)
    doc = libxml2.parseFile(rdfname)
    result = style.applyStylesheet(doc, None)
    strres = style.saveResultToString(result)
    style.freeStylesheet()
    doc.freeDoc()
    result.freeDoc()
    ritems = []
    if len(strres) == 0:
        return []
    else:
        lines = strres.split("\n")
        for line in lines:
            #take only those with myout..
            if line.count("<myout>") > 0:
                #remove the myout tag..
                line = line[9:]
                line = line[:-8]
                if searchwith:
                    if line.count(searchwith) > 0:
                        ritems.append(line)
                else:
                    ritems.append(line)
    return ritems


if __name__ == "__main__":
    pass
