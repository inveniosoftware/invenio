# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Database access related functions for BibKnowledge.
"""

__revision__ = "$Id$"

from invenio.ext.sqlalchemy import db
from invenio.utils.memoise import Memoise
from .models import KnwKB, KnwKBRVAL, KnwKBDDEF
from invenio.modules.search.models import Collection


def get_kbs_info(kbtypeparam="", searchkbname=""):
    """Returns all kbs as list of dictionaries {id, name, description, kbtype}
       If the KB is dynamic, the dynamic kb key are added in the dict.
    """
    out = []
    res = KnwKB.query.order_by(KnwKB.name).all()

    for row in res:
        doappend = 1  # by default
        kbid = row.id
        name = row.name
        kbtype = row.kbtype
        dynres = {}
        if kbtype == 'd':
            # get the dynamic config
            dynres = get_kb_dyn_config(kbid)
        if kbtypeparam:
            doappend = 0
            if (kbtype == kbtypeparam):
                doappend = 1
        if searchkbname:
            doappend = 0
            if (name == searchkbname):
                doappend = 1
        if doappend:
            mydict = row.to_dict()
            mydict.update(dynres)
            out.append(mydict)
    return out


def get_all_kb_names():
    """
    Returns all knowledge base names.

    :return list of names
    """
    out = []
    res = KnwKB.query.all()
    for row in res:
        out.append(row.name)
    return out


def get_kb_id(kb_name):
    """
    Returns the id of the kb with given name.

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.

    :return integer
    """
    kb = KnwKB.query.filter_by(name=kb_name).first()
    return kb.id if kb is not None else None


get_kb_id_memoised = Memoise(get_kb_id)


def get_kb_name(kb_id):
    """
    Returns the name of the kb with given id.

    :param kb_id the id

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.

    :return string
    """
    return KnwKB.query.filter_by(id=kb_id).one().name


def get_kb_type(kb_id):
    """
    Returns the type of the kb with given id.

    :param kb_id knowledge base id

    :return kb_type
    """
    return KnwKB.query.filter_by(id=kb_id).one().kbtype


def get_kb_mappings(kb_name="", sortby="to", keylike="", valuelike="", match_type="s"):
    """
    Returns a list of all mappings from the given kb, ordered by key.

    :param kb_name knowledge base name. if "", return all

    :param sortby the sorting criteria ('from' or 'to')

    :keylike return only entries where key matches this

    :valuelike return only entries where value matches this
    """
    out = []

    if len(keylike) > 0:
        if match_type == "s":
            keylike = "%"+keylike+"%"
    else:
        keylike = '%'

    if len(valuelike) > 0:
        if match_type == "s":
            valuelike = "%"+valuelike+"%"
    else:
        valuelike = '%'

    query = db.session.query(KnwKBRVAL).join(KnwKB).filter(
        KnwKBRVAL.m_key.like(keylike),
        KnwKBRVAL.m_value.like(valuelike))

    if kb_name:
        query.filter(KnwKB.name == kb_name)

    if sortby == "from":
        query = query.order_by(KnwKBRVAL.m_key)
    else:
        query = query.order_by(KnwKBRVAL.m_value)

    res = query.all()

    for row in res:
        out.append(row.to_dict())
    return out


def get_kb_dyn_config(kb_id):
    """
    Returns a dictionary of 'field'=> y, 'expression'=> z
    for a knowledge base of type 'd'. The dictionary may have coll_id, collection.

    :param kb_id the id

    :return dict
    """
    dyn_config = KnwKBDDEF.query.filter_by(id_knwKB=kb_id).first()
    if dyn_config is None:
        return {}
    else:
        return dyn_config.to_dict()


def save_kb_dyn_config(kb_id, field, expression, collection=""):
    """
    Saves a dynamic knowledge base configuration.

    :param kb_id the id

    :param field the field where values are extracted

    :param expression ..using this expression

    :param collection ..in a certain collection (default is all)
    """
    #check that collection exists
    coll_id = None
    if collection:
        coll_id = Collection.query.filter_by(name=collection).first()

    KnwKBDDEF.query.filter_by(id_knwKB=kb_id).delete()

    knwKBDDEF = KnwKBDDEF(id_knwKB=kb_id, output_tag=field, search_expression=expression, id_collection=coll_id)

    db.session.add(knwKBDDEF)
    db.session.commit()

    return ""


def get_kb_description(kb_name):
    """
    Returns the description of the given kb.

    :param kb_id the id

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist.

    :return string
    """
    return KnwKB.query.filter_by(name=kb_name).one().description


def add_kb(kb_name, kb_description, kb_type=None):
    """
    Adds a new kb with given name and description. Returns the id of
    the kb.

    If name already exists replace old value

    :param kb_name the name of the kb to create

    :param kb_description a description for the kb

    :return the id of the newly created kb
    """
    kb_db = 'w'  # the typical written_as - change_to
    if not kb_type:
        pass
    else:
        if kb_type == 'taxonomy':
            kb_db = 't'
        if kb_type == 'dynamic':
            kb_db = 'd'

    knwKB = KnwKB.query.filter_by(name=kb_name).first()

    if(knwKB is None):
        knwKB = KnwKB(name=kb_name, description=kb_description, kbtype=kb_db)
        db.session.add(knwKB)
        db.session.commit()
    else:
        update_kb(kb_name, kb_name, kb_description, kb_type)

    return knwKB.id


def delete_kb(kb_name):
    """Deletes the given kb."""
    k_id = get_kb_id(kb_name)
    if k_id is None:
        return
    KnwKBRVAL.query.filter_by(id_knwKB=k_id).delete()
    KnwKB.query.filter_by(id=k_id).delete()
    KnwKBDDEF.query.filter_by(id_knwKB=k_id).delete()
    db.session.commit()
    return True


def kb_exists(kb_name):
    """Returns True if a kb with the given name exists."""
    if KnwKB.query.filter_by(name=kb_name).first():
        return True
    else:
        return False


def update_kb(kb_name, new_name, new_description='', kbtype=None):
    """Updates given kb with new name and (optionally) new description."""
    kb = KnwKB.query.filter_by(name=kb_name).one()
    kb.name = new_name
    kb.description = new_description
    kb.kbtype = kbtype
    try:
        db.session.merge(kb)
    except:
        # FIXME add re-raise exception
        db.session.rollback()
        return False
    finally:
        db.session.commit()
        return True


def add_kb_mapping(kb_name, key, value):
    """Adds new mapping key->value in given kb."""
    knwKB = KnwKB.query.filter_by(name=kb_name).first()
    kbrval = KnwKBRVAL.query.filter_by(m_key=key, id_knwKB=knwKB.id if knwKB else 0).first()
    ret = True
    if(kbrval is None):
        kbrval = KnwKBRVAL(m_key=key, m_value=value,
                           id_knwKB=knwKB.id if knwKB else None,
                           kb=knwKB)
        try:
            db.session.merge(kbrval)
        except:
            # FIXME add re-raise exception
            db.session.rollback()
            ret = False
        finally:
            db.session.commit()
    else:
        kbrval.m_key = key
        kbrval.m_value = value
        kbrval.id_knwKB = knwKB.id if knwKB else 0
        kbrval.kb = knwKB
        try:
            db.session.add(kbrval)
        except:
            # FIXME add re-raise exception
            db.session.rollback()
            ret = False
        finally:
            db.session.commit()

    return ret


def remove_kb_mapping(kb_name, key):
    """Removes mapping with given key from given kb."""
    k_id = get_kb_id(kb_name)
    KnwKBRVAL.query.filter_by(m_key=key, id_knwKB=k_id).delete()
    return True


def kb_mapping_exists(kb_name, key):
    """Returns true if the mapping with given key exists in the given kb."""
    if kb_exists(kb_name):
        k_id = get_kb_id(kb_name)
        return True if KnwKBRVAL.query.filter(KnwKBRVAL.m_key.like(key), KnwKBRVAL.id_knwKB.like(k_id)).first() is not None else False
    return False


def kb_key_rules(key):
    # FIXME rewrite docs
    """Returns a list of 4-tuples that have a key->value mapping in some KB
       The format of the tuples is [kb_id, kb_name,key,value]."""
    return KnwKBRVAL.query.filter_by(m_key=key).all()


def kb_value_rules(value):
    # FIXME rewrite docs
    """Returns a list of 4-tuples that have a key->value mapping in some KB
       The format of the tuples is [kb_id, kb_name,key,value]."""
    return KnwKBRVAL.query.filter_by(m_value=value).all()


def get_kb_mapping_value(kb_name, key):
    # FIXME rewrite docs
    """
    Returns a value of the given key from the given kb.
    If mapping not found, returns None #'default'

    :param kb_name the name of a knowledge base
    :param key the key to look for
    #:param default a default value to return if mapping is not found
    """
    k_id = get_kb_id(kb_name)
    kval = KnwKBRVAL.query.filter_by(m_key=key, id_knwKB=k_id).first()
    return kval.m_value if kval is not None else None


def update_kb_mapping(kb_name, key, new_key, new_value):
    # FIXME rewrite docs
    """Updates the mapping given by key with new key and value"""
    k_id = get_kb_id(kb_name)
    kval = KnwKBRVAL.query.filter_by(m_key=key, id_knwKB=k_id).one()
    kval.m_key = new_key
    kval.m_value = new_value
    kval.id_knwKB = k_id
    try:
        db.session.merge(kval)
    except:
        db.session.rollback()
        # FIXME add re-raise exception
    finally:
        db.session.commit()
    return True

# the following functions should be used by a higher level API


def get_kba_values(kb_name, searchname="", searchtype="s"):
    """Returns the "authority file" type of list of values for a
       given knowledge base.
       :param kb_name the name of the knowledge base
       :param searchname search by this..
       :param searchtype s=substring, e=exact, sw=startswith
    """
    k_id = get_kb_id(kb_name)
    if searchtype == 's' and searchname:
        searchname = '%'+searchname+'%'
    if searchtype == 'sw' and searchname:  # startswith
        searchname = searchname+'%'

    if not searchname:
        searchname = '%'

    vals = []
    kvals = KnwKBRVAL.query.filter(KnwKBRVAL.id_knwKB.like(k_id), KnwKBRVAL.m_value.like(searchname)).all()
    for kval in kvals:
        vals.append(kval.m_value)
    return vals


def get_kbr_keys(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Returns keys from a knowledge base
       :param kb_name the name of the knowledge base
       :param searchkey search using this key
       :param searchvalue search using this value
       :param searchtype s=substring, e=exact, sw=startswith
    """
    k_id = get_kb_id(kb_name)
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

    keys = []
    kkeys = KnwKBRVAL.query.filter(KnwKBRVAL.id_knwKB.like(k_id), KnwKBRVAL.m_key.like(searchkey)).all()
    for kkey in kkeys:
        keys.append(kkey.m_key)
    return keys


def get_kbr_values(kb_name, searchkey="%", searchvalue="", searchtype='s', use_memoise=False):
    """Returns values from a knowledge base

       Note the intentional asymmetry between searchkey and searchvalue:
       If searchkey is unspecified or empty for substring, it matches anything,
       but if it is empty for exact, it matches nothing.
       If searchvalue is unspecified or empty, it matches anything in all cases.

       :param kb_name the name of the knowledge base
       :param searchkey search using this key
       :param searchvalue search using this value
       :param searchtype s=substring, e=exact, sw=startswith
       :param use_memoise: can we memoise while doing lookups?
       :type use_memoise: bool
       :return a list of values
    """
    if use_memoise:
        k_id = get_kb_id_memoised(kb_name)
    else:
        k_id = get_kb_id(kb_name)
    if k_id is None:
        return []
    if searchkey is None:
        searchkey = '%'
    if searchtype == 's':
        searchkey = '%'+searchkey+'%'
    if searchtype == 's' and searchvalue:
        searchvalue = '%'+searchvalue+'%'
    if searchtype == 'sw' and searchvalue:  # startswith
        searchvalue = searchvalue+'%'
    if not searchvalue:
        searchvalue = '%'

    vals = []
    kvals = KnwKBRVAL.query.filter(KnwKBRVAL.id_knwKB.like(k_id), KnwKBRVAL.m_value.like(searchvalue), KnwKBRVAL.m_key.like(searchkey)).all()
    for kval in kvals:
        vals.append(kval.m_value)
    return vals


get_kbr_values_memoised = Memoise(get_kbr_values)


def get_kbr_items(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Returns dicts of 'key' and 'value' from a knowledge base
       :param kb_name the name of the knowledge base
       :param searchkey search using this key
       :param searchvalue search using this value
       :param searchtype s=substring, e=exact, sw=startswith
       :return a list of dictionaries [{'key'=>x, 'value'=>y},..]
    """
    k_id = get_kb_id(kb_name)
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

    vals = []
    kvals = KnwKBRVAL.query.filter(KnwKBRVAL.id_knwKB.like(k_id), KnwKBRVAL.m_value.like(searchvalue), KnwKBRVAL.m_key.like(searchkey)).all()
    for kval in kvals:
        vals.append({'key': kval.m_key, 'value': kval.m_value})

    return vals
