# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Provide API-callable functions for knowledge base management."""

import json
import os
import re
import warnings

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.collections.models import Collection
from invenio.utils.memoise import Memoise

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from . import models

processor_type = 0
try:
    from lxml import etree
    processor_type = 1
except ImportError:
    try:
        import libxml2
        import libxslt
        processor_type = 2
    except ImportError:
        pass


def get_kb_by_slug(slug):
    """Return the knwKB object with given slug.

    :param slug: slug of knowledge
    :return: knowledge's object
    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.
    """
    return models.KnwKB.query.filter_by(slug=slug).one()


def get_kb_by_id(kb_id):
    """Return the knwKB object with given id.

    :param kb_id: id of knowledge
    :return: knowledge's object
    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.
    """
    return models.KnwKB.query.filter_by(id=kb_id).one()


def get_kb_id(kb_name):
    """Get the id by name.

    :param kb_name: knowledge base name
    """
    warnings.warn("The method get_kb_id(kb_name) is deprecated! "
                  "Use instead get_kb_by_id()'",
                  DeprecationWarning)
    return get_kb_by_id(kb_name).id


def get_kb_by_name(kb_name):
    """Return the knwKB object with given name.

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.
    """
    return models.KnwKB.query.filter_by(name=kb_name).one()


def get_all_kb_names():
    """Return all knowledge base names.

    :return: list of names
    """
    return [row.name for row in models.KnwKB.query.all()]

get_kb_by_name_memoised = Memoise(get_kb_by_name)


def query_get_kb_by_type(kbtype):
    """Return a query to filter kb by type.

    :param kbtype: type to filter (e.g: taxonomy)
    :return: query to filter kb
    """
    return models.KnwKB.query.filter_by(
        kbtype=models.KnwKB.KNWKB_TYPES[kbtype])


def query_kb_mappings(kbid, sortby="to", key="", value="",
                      match_type="s"):
    """Return a list of all mappings from the given kb, ordered by key.

    If key given, give only those with left side (mapFrom) = key.
    If value given, give only those with right side (mapTo) = value.

    :param kb_name: knowledge base name. if "", return all
    :param sortby: the sorting criteria ('from' or 'to')
    :param key: return only entries where key matches this
    :param value: return only entries where value matches this
    :param match_type: s=substring, e=exact, sw=startswith
    """
    return models.KnwKBRVAL.query_kb_mappings(kbid, sortby, key,
                                              value, match_type)


def get_kb_mappings(kb_name="", key="", value="", match_type="s", sortby="to",
                    limit=None):
    """Return a list of all mappings from the given kb, ordered by key.

    If key given, give only those with left side (mapFrom) = key.
    If value given, give only those with right side (mapTo) = value.

    :param kb_name: knowledge base name. if "", return all
    :param sortby: the sorting criteria ('from' or 'to')
    :param key: return only entries where key matches this
    :param value: return only entries where value matches this
    :param limit: return only X number of entries
    :return: list of knowledge converted in dictionary
    """
    # query
    query = db.session.query(models.KnwKBRVAL).join(models.KnwKB)
    # filter
    if kb_name:
        query = query.filter(models.KnwKB.name == kb_name)
    if len(key) > 0:
        if match_type == "s":
            key = "%"+key+"%"
    else:
        key = '%'
    if len(value) > 0:
        if match_type == "s":
            value = "%"+value+"%"
    else:
        value = '%'
    query = query.filter(
        models.KnwKBRVAL.m_key.like(key),
        models.KnwKBRVAL.m_value.like(value))
    # order by
    if sortby == "from":
        query = query.order_by(models.KnwKBRVAL.m_key)
    else:
        query = query.order_by(models.KnwKBRVAL.m_value)
    if limit:
        query = query.limit(limit)
    # return results
    return [kbv.to_dict() for (kbv) in query.all()]


def get_kb_mapping(kb_name="", key="", value="", match_type="e", default="",
                   limit=None):
    """Get one unique mapping. If not found, return default.

    :param kb_name: the name of the kb
    :param key: include only lines matching this on left side in the results
    :param value: include only lines matching this on right side in the results
    :param match_type: s = substring match, e = exact match
    :param default: default value if no mapping is found
    :return: a mapping
    """
    mappings = get_kb_mappings(kb_name, key=key, value=value,
                               match_type=match_type, limit=limit)

    if len(mappings) == 0:
        return default
    else:
        return mappings[0]


@session_manager
def add_kb_mapping(kb_name, key, value=""):
    """Add a new mapping to given kb.

    :param kb_name: the name of the kb where to insert the new value
    :param key: the key of the mapping
    :param value: the value of the mapping
    """
    kb = get_kb_by_name(kb_name)
    if key in kb.kbrvals:
        # update
        kb.kbrvals[key].m_value = value
    else:
        # insert
        kb.kbrvals.set(models.KnwKBRVAL(m_key=key, m_value=value))


@session_manager
def remove_kb_mapping(kb_name, key):
    """Delete an existing kb mapping in kb.

    :param kb_name: the name of the kb where to insert the new value
    :param key: the key of the mapping
    """
    kb = get_kb_by_name(kb_name)
    del kb.kbrvals[key]


@session_manager
def update_kb_mapping(kb_name, old_key, key, value):
    """Update an existing kb mapping with key old_key with a new key and value.

    :param kb_name: the name of the kb where to insert the new value
    :param old_key: the key of the mapping in the kb
    :param key: the new key of the mapping
    :param value: the new value of the mapping
    """
    db.session.query(models.KnwKBRVAL).join(models.KnwKB) \
        .filter(models.KnwKB.name == kb_name,
                models.KnwKBRVAL.m_key == old_key) \
        .update({"m_key": key, "m_value": value}, synchronize_session=False)


def get_kb_mappings_json(kb_name="", key="", value="", match_type="s",
                         limit=None):
    """Get leftside/rightside mappings from kb kb_name formatted as json dict.

    If key given, give only those with left side (mapFrom) = key.
    If value given, give only those with right side (mapTo) = value.

    :param kb_name: the name of the kb
    :param key: include only lines matching this on left side in the results
    :param value: include only lines matching this on right side in the results
    :param match_type: s = substring match, e = exact match
    :param limit: maximum number of results to return (are ALL if set to None)
    :return: a list of mappings
    """
    mappings = get_kb_mappings(kb_name, key, value, match_type)
    ret = []
    if limit is None:
        limit = len(mappings)
    for m in mappings[:limit]:
        label = m['value'] or m['key']
        value = m['key'] or m['value']
        ret.append({'label': label, 'value': value})
    return json.dumps(ret)


def get_kb_mappings_embedded_json(kb_name="", key="", value="",
                                  match_type="s", limit=None):
    """Get leftside/rightside mappings from kb kb_name formatted as json dict.

    The rightside is actually considered as a json string and hence embedded
    within the final result.

    If key given, give only those with left side (mapFrom) = key.
    If value given, give only those with right side (mapTo) = value.

    :param kb_name: the name of the kb
    :param key: include only lines matching this on left side in the results
    :param value: include only lines matching this on right side in the results
    :param match_type: s = substring match, e = exact match
    :param limit: maximum number of results to return (are ALL if set to None)
    :return: a list of mappings
    """
    mappings = get_kb_mappings(kb_name, key, value, match_type)
    ret = []
    if limit is None:
        limit = len(mappings)
    for m in mappings[:limit]:
        label = m['value'] or m['key']
        value = m['key'] or m['value']
        ret.append({'label': label, 'value': json.loads(value)})
    return json.dumps(ret)


def kb_exists(kb_name):
    """Return True if a kb with the given name exists.

    :param kb_name: the name of the knowledge base
    :return: True if kb exists
    """
    return models.KnwKB.exists(kb_name)


def get_kb_name(kb_id):
    """Return the name of the kb given by id.

    :param kb_id: the id of the knowledge base
    """
    return get_kb_by_id(kb_id).name


@session_manager
def update_kb_attributes(kb_name, new_name, new_description=''):
    """Update kb kb_name with a new name and (optionally) description.

    :param kb_name: the name of the kb to update
    :param new_name: the new name for the kb
    :param new_description: the new description for the kb
    """
    models.KnwKB.query.filter_by(name=kb_name) \
        .update({"name": new_name, "description": new_description})


def add_kb(kb_name=u"Untitled", kb_type=None, tries=10):
    """Add a new kb in database, return the id.

    Add a new kb in database, and returns its id
    The name of the kb will be 'Untitled#'
    such that it is unique.

    :param kb_name: the name of the kb
    :param kb_type: the type of the kb, incl 'taxonomy' and 'dynamic'.
                   None for typical (leftside-rightside).
    :param tries: exit after <n> retry
    :return: the id of the newly created kb
    """
    created = False
    name = kb_name
    i = 0
    while(i < tries and created is False):
        try:
            kb = models.KnwKB(name=name, description="", kbtype=kb_type)
            created = True
            db.session.add(kb)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # get the highest id to calculate the new name
            result = db.session.execute(
                db.select([models.KnwKB.id])
                .order_by(db.desc(models.KnwKB.id))
                .limit(1)).first()
            index = result[0] + 1 if result is not None else 1
            name = kb_name + " " + str(index)
            i = i + 1
            created = False
        except Exception:
            db.session.rollback()
            raise

    if created is False:
        # TODO raise the right exception
        raise Exception(_("Can't create knowledge base \"%(name)s\".\n"
                          "Probabily the server is busy! "
                          "Try again later.", name=kb_name))

    return kb.id


def add_dynamic_kb(kbname, tag, collection="", searchwith=""):
    """A convenience method."""
    kb_id = add_kb(kb_name=kbname, kb_type='dynamic')
    save_kb_dyn_config(kb_id, tag, searchwith, collection)
    return kb_id


def save_kb_dyn_config(kb_id, field, expression, collection=None):
    """Save a dynamic knowledge base configuration.

    :param kb_id: the id
    :param field: the field where values are extracted
    :param expression: ..using this expression
    :param collection: ..in a certain collection (default is all)
    """
    # check that collection exists
    if collection:
        collection = Collection.query.filter_by(name=collection).one()

    kb = get_kb_by_id(kb_id)
    kb.set_dyn_config(field, expression, collection)


def kb_mapping_exists(kb_name, key):
    """Return the information if a mapping exists.

    :param kb_name: knowledge base name
    :param key: left side (mapFrom)
    """
    try:
        kb = get_kb_by_name(kb_name)
    except NoResultFound:
        return False
    return key in kb.kbrvals


@session_manager
def delete_kb(kb_name):
    """Delete given kb from database.

    :param kb_name: knowledge base name
    """
    db.session.delete(models.KnwKB.query.filter_by(
        name=kb_name).one())


# Knowledge Bases Dependencies
#


def get_elements_that_use_kb(name):
    """Return a list of elements that call given kb.

    WARNING: this routine is obsolete.

    .. code-block:: python

        [
         {
          'filename':"filename_1.py",
          'name': "a name"
         },
         ..
        ]

    :return: elements sorted by name
    """
    # FIXME remove the obsolete function
    warnings.warn("The method 'get_elements_that_use_kb(name) is obsolete!'",
                  DeprecationWarning)

    format_elements = {}
    # Retrieve all elements in files
    from invenio.modules.formatter.engine \
        import TEMPLATE_CONTEXT_FUNCTIONS_CACHE
    for element in TEMPLATE_CONTEXT_FUNCTIONS_CACHE \
            .bibformat_elements().values():
        path = element.__file__
        filename = os.path.basename(element.__file__)
        if filename.endswith(".py"):
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
                format_elements[name] = {'filename': filename,
                                         'name': name}

    keys = format_elements.keys()
    keys.sort()
    return map(format_elements.get, keys)

# kb functions for export


def get_kbs_info(kbtype="", searchkbname=""):
    """A convenience method.

    :param kbtype: type of kb -- get only kb's of this type
    :param searchkbname: get only kb's where this sting appears in the name
    """
    # query + order by
    query = models.KnwKB.query.order_by(
        models.KnwKB.name)
    # filters
    if kbtype:
        query = query.filter_by(kbtype=kbtype)
    if searchkbname:
        query = query.filter_by(name=searchkbname)

    return [row.to_dict() for row in query.all()]


def get_kba_values(kb_name, searchname="", searchtype="s"):
    """Return an array of values "authority file" type = just values.

    :param kb_name: name of kb
    :param searchname: get these values, according to searchtype
    :param searchtype: s=substring, e=exact, , sw=startswith
    """
    if searchtype == 's' and searchname:
        searchname = '%'+searchname+'%'
    if searchtype == 'sw' and searchname:  # startswith
        searchname = searchname+'%'

    if not searchname:
        searchname = '%'

    query = db.session.query(models.KnwKBRVAL).join(models.KnwKB) \
        .filter(models.KnwKBRVAL.m_value.like(searchname),
                models.KnwKB.name.like(kb_name))

    return [(k.m_value,) for k in query.all()]


def get_kbr_keys(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Return an array of keys.

    :param kb_name: the name of the knowledge base
    :param searchkey: search using this key
    :param searchvalue: search using this value
    :param searchtype: s = substring, e=exact
    """
    if searchtype == 's' and searchkey:
        searchkey = '%'+searchkey+'%'
    if searchtype == 's' and searchvalue:
        searchvalue = '%'+searchvalue+'%'
    if searchtype == 'sw' and searchvalue:  # startswith
        searchvalue = searchvalue+'%'
    if not searchvalue:
        searchvalue = '%'
    if not searchkey:
        searchkey = '%'

    query = db.session.query(models.KnwKBRVAL).join(models.KnwKB) \
        .filter(models.KnwKBRVAL.m_key.like(searchkey),
                models.KnwKBRVAL.m_value.like(searchvalue),
                models.KnwKB.name.like(kb_name))

    return [(k.m_key,) for k in query.all()]


def get_kbr_values(kb_name, searchkey="", searchvalue="", searchtype='s',
                   use_memoise=False):
    """Return a tuple of values from key-value mapping kb.

    :param kb_name:     the name of the knowledge base
    :param searchkey:   search using this key
    :param searchvalue: search using this value
    :param searchtype:  s=substring; e=exact
    :param use_memoise: can we memoise while doing lookups?
    :type use_memoise:  bool
    """
    try:
        if use_memoise:
            kb = get_kb_by_name_memoised(kb_name)
        else:
            kb = get_kb_by_name(kb_name)
    except NoResultFound:
        return []
    return list(kb.get_kbr_values(searchkey, searchvalue, searchtype))


def get_kbr_items(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Return a list of dictionaries that match the search.

    :param kb_name: the name of the knowledge base
    :param searchkey: search using this key
    :param searchvalue: search using this value
    :param searchtype: s = substring, e=exact
    :return: a list of dictionaries [{'key'=>x, 'value'=>y},..]
    """
    kb = get_kb_by_name(kb_name)
    return kb.get_kbr_items(searchkey, searchvalue, searchtype)


def get_kbd_values(kbname, searchwith=""):
    """Return a list of values by searching a dynamic kb.

    :param kbname:     name of the knowledge base
    :param searchwith: a term to search with
    :return: list of values
    """
    kb = get_kb_by_name(kbname)
    kbid = kb.id
    if not kbid:
        return []
    kbtype = kb.kbtype
    if not kbtype:
        return []
    if kbtype != 'd':
        return []
    return get_kbd_values_by_def(kb.kbdefs.to_dict(), searchwith)


def get_kbd_values_by_def(confdict, searchwith=""):
    """Return a list of values by searching a dynamic kb.

    :param confdict: dictionary with keys "field", "expression"
        and "collection" name
    :param searchwith: a term to search with
    :return: list of values
    """
    from invenio.legacy import search_engine

    # get the configuration so that we see what the field is
    if not confdict:
        return []
    if 'field' not in confdict:
        return []
    field = confdict['field']
    expression = confdict['expression']
    collection = ""
    if 'collection' in confdict:
        collection = confdict['collection']
    reclist = []  # return this
    if searchwith and expression:
        if (expression.count('%') > 0):
            expression = expression.replace("%", searchwith)
            reclist = search_engine.perform_request_search(p=expression,
                                                           cc=collection)
        else:
            # no %.. just make a combination
            expression = expression + " and " + searchwith
            reclist = search_engine.perform_request_search(p=expression,
                                                           cc=collection)
    else:  # either no expr or no searchwith.. but never mind about searchwith
        if expression:  # in this case: only expression
            reclist = search_engine.perform_request_search(p=expression,
                                                           cc=collection)
        else:
            # make a fake expression so that only records that have this field
            # will be returned
            fake_exp = "/.*/"
            if searchwith:
                fake_exp = searchwith
            reclist = search_engine.perform_request_search(f=field, p=fake_exp,
                                                           cc=collection)
    if reclist:
        return [val for (val, dummy) in
                search_engine.get_most_popular_field_values(reclist, field)]
    return []  # in case nothing worked


def get_kbd_values_json(kbname, searchwith=""):
    """Return values from searching a dynamic kb as a json-formatted string.

    This IS probably the method you want.

    :param kbname:     name of the knowledge base
    :param searchwith: a term to search with
    """
    res = get_kbd_values(kbname, searchwith)
    return json.dumps(res)


def get_kbd_values_for_bibedit(tag, collection="", searchwith="",
                               expression=""):
    """Get list of kbd values for bibedit.

    Example1: tag=100__a : return values of 100__a
    Example2: tag=100__a, searchwith=Jill: return values of 100__a that match
    with Jill
    Example3: tag=100__a, searchwith=Ellis, expression="700__a:*%*:
    return values of 100__a for which Ellis matches some 700__a

    Note: the performace of this function is ok compared to a plain
          perform_request_search / get most popular fields -pair.
          The overhead is about 5% with large record sets;
          the lookups are the xpensive part.

    :param tag:        the tag like 100__a
    :param collection: collection id
    :param searchwith: the string to search. If empty, match all.
    :param expression: the search expression for perform_request_search;
                       if present, '%' is substituted with /searcwith/.
                       If absent, /searchwith/ is searched for in /tag/.
    """
    return get_kbd_values_by_def(dict(
        field=tag, expression=expression, collection=collection
    ), searchwith)


def get_kbt_items(taxonomyfilename, templatefilename, searchwith=""):
    """
    Get items from taxonomy file using a templatefile.

    If searchwith is defined, return only items that match with it.
    :param taxonomyfilename: full path+name of the RDF file
    :param templatefile: full path+name of the XSLT file
    :param searchwith: a term to search with
    """
    if processor_type == 1:
        # lxml
        doc = etree.XML(taxonomyfilename)
        styledoc = etree.XML(templatefilename)
        style = etree.XSLT(styledoc)
        result = style(doc)
        strres = str(result)
        del result
        del style
        del styledoc
        del doc
    elif processor_type == 2:
        # libxml2 & libxslt
        styledoc = libxml2.parseFile(templatefilename)
        style = libxslt.parseStylesheetDoc(styledoc)
        doc = libxml2.parseFile(taxonomyfilename)
        result = style.applyStylesheet(doc, None)
        strres = style.saveResultToString(result)
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()
    else:
        # no xml parser found
        strres = ""

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
    """A simplifield, customized version of the function get_kbt_items.

    Traverses an RDF document. By default returns all leaves. If
    tag defined returns the content of that tag.
    If searchwith defined, returns leaves that match it.
    Warning! In order to make this faster, the matching field values
    cannot be multi-line!

    :param kbtname: name of the taxonony kb
    :param tag: name of tag whose content
    :param searchwith: a term to search with
    """
    # get the actual file based on the kbt name
    kb = get_kb_by_name(kbtname)
    kb_id = kb.id
    if not kb_id:
        return []
    # get the rdf file..
    rdfname = cfg['CFG_WEBDIR'] + "/kbfiles/" + str(kb_id) + ".rdf"
    if not os.path.exists(rdfname):
        return []

    xsl = """\
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">

  <xsl:output method="xml" standalone="yes"
    omit-xml-declaration="yes" indent="no"/>
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

</xsl:stylesheet>"""

    if processor_type == 1:
        styledoc = etree.XML(xsl)
        style = etree.XSLT(styledoc)
        doc = etree.parse(open(rdfname, 'r'))
        strres = str(style(doc))

    elif processor_type == 2:
        styledoc = libxml2.parseDoc(xsl)
        style = libxslt.parseStylesheetDoc(styledoc)
        doc = libxml2.parseFile(rdfname)
        result = style.applyStylesheet(doc, None)
        strres = style.saveResultToString(result)
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()

    else:
        # no xml parser found
        strres = ""

    ritems = []
    if len(strres) == 0:
        return []
    else:
        lines = strres.split("\n")
        for line in lines:
            # take only those with myout..
            if line.count("<myout>") > 0:
                # remove the myout tag..
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
