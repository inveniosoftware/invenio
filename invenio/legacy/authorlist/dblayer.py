# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

import time
from invenio.legacy.authorlist import config as cfg

from invenio.legacy.dbquery import run_sql

def now():
    """
    Returns a unix epoch time stamp as integer.
    """
    return int(time.time())

def clone(paper_id, user_id):
    """
    Clones a whole paper data having the given id and returns the paper
    information of the clone as a dictionary. If the paper_id was a falsy value
    (None usually) or the id of the paper to be cloned does not exist in the
    database. The function will create a new empty record, save it and return it
    instead.
    """
    data = {}
    clone_id = clone_paper(paper_id, user_id)

    if (clone_id == 0):
        data = load(None)
        clone_id = save(None, user_id, data)
    else:
        clone_references(paper_id, clone_id)
        clone_affiliations(paper_id, clone_id)
        clone_authors(paper_id, clone_id)

    load_paper(clone_id, data)
    data[cfg.JSON.PAPER_ID] = clone_id

    return data

def clone_paper(paper_id, user_id):
    """
    Clones the general paper information - i.e. title, collaboration and
    experiment number. Furthermore, the last modified timestamp will be set
    to the current time. All of this is only done, if the requested paper id
    was found in the database, otherwise 0 is returned. This function
    should NOT be called alone as long as you are really sure that you want
    to do this. Refer to clone() instead.
    """
    return run_sql("""INSERT INTO aulPAPERS (id, id_user, title, collaboration,
                      experiment_number, last_modified) SELECT %s, id_user, title,
                      collaboration, experiment_number, %s FROM aulPAPERS
                      WHERE id = %s;""", (None, now(), paper_id,))

def clone_references(paper_id, clone_id):
    """
    Clones the references of the paper with the given id and assigns the new
    clone id instead. Returns the clone id again for convenience reasons. The
    function should NOT be used alone as long as you are really sure that you
    want to do this. Have a look on clone() instead.
    """
    run_sql("""INSERT INTO aulREFERENCES (item, reference, paper_id)
               SELECT item, reference, %s FROM aulREFERENCES
               WHERE paper_id = %s;""", (clone_id, paper_id,))
    return clone_id

def clone_affiliations(paper_id, clone_id):
    """
    Clones the affiliations of the given paper id and assigns the clone id
    instead. Returns the clone id for convenience reasons. The function should
    NOT be used alone as long as you are really sure that you want to do this.
    Have a look on clone() instead.
    """
    run_sql("""INSERT INTO aulAFFILIATIONS (item, acronym, umbrella,
               name_and_address, domain, member, spires_id, paper_id)
               SELECT item, acronym, umbrella, name_and_address,
               domain, member, spires_id, %s FROM aulAFFILIATIONS
               WHERE paper_id = %s;""", (clone_id, paper_id,))
    return clone_id

def clone_authors(paper_id, clone_id):
    """
    Clones the authors of the paper with the passed id and assigns the new clone
    id instead. It also invokes the cloning of the affiliations of the authors.
    The clone id will be returned again for convenience reasons. The function
    should NOT be used alone as long as you are really sure that you want to do
    this. Have a look on clone() instead.
    """
    run_sql("""INSERT INTO aulAUTHORS (item, family_name, given_name,
               name_on_paper, status, paper_id)
               SELECT item, family_name, given_name, name_on_paper,
               status, %s FROM aulAUTHORS
               WHERE paper_id = %s;""", (clone_id, paper_id,))
    clone_author_affiliations(paper_id, clone_id)
    clone_author_identifiers(paper_id, clone_id)
    return clone_id

def clone_author_affiliations(paper_id, clone_id):
    """
    Clones the affiliations of the authors of the paper with the given id and
    assigns the new clone id to them. Returns the clone_id again for convenience
    reasons. Should NOT be used alone but only as part of clone() as long as you
    are not really sure what you are doing.
    """
    run_sql("""INSERT INTO aulAUTHOR_AFFILIATIONS (item, affiliation_acronym,
               affiliation_status, author_item, paper_id)
               SELECT item, affiliation_acronym, affiliation_status,
               author_item, %s FROM aulAUTHOR_AFFILIATIONS
               WHERE paper_id = %s;""", (clone_id, paper_id,))
    return clone_id

def clone_author_identifiers(paper_id, clone_id):
    """
    Clones the identifiers of the authors of the paper with the given id and
    assigns the new clone id to them. Returns the clone_id again for convenience
    reasons. Should NOT be used alone but only as part of clone() as long as you
    are not really sure what you are doing.
    """
    run_sql("""INSERT INTO aulAUTHOR_IDENTIFIERS (item, identifier_number,
               identifier_name, author_item, paper_id)
               SELECT item, identifier_number, identifier_name,
               author_item, %s FROM aulAUTHOR_IDENTIFIERS
               WHERE paper_id = %s;""", (clone_id, paper_id,))
    return clone_id

def delete(paper_id):
    """
    Deletes the paper with the given id completely from the database. There is
    no backup copy so better we sure that you want to do this :). Returns the
    id of the deleted paper again for convenience reasons.
    """
    data = {cfg.JSON.PAPER_ID : paper_id}

    delete_paper(paper_id)
    delete_references(paper_id)
    delete_affiliations(paper_id)
    delete_authors(paper_id)
    delete_author_affiliations(paper_id)
    delete_author_identifiers(paper_id)

    return data

def delete_paper(paper_id):
    """
    Deletes the general informations of a paper without making any backup copy
    and safety net for the paper with the given id. Should NOT be used alone
    unless you are sure that you want to do this. Refer to delete() instead.
    Returns the paper_id for convenience reasons.
    """
    run_sql("""DELETE FROM aulPAPERS WHERE id = %s;""", (paper_id,))
    return paper_id

def delete_references(paper_id):
    """
    Deletes the paper references from the database with the given id. It does
    not create any backup copy. Should NOT be used unless you are really sure
    that you want to do this. Refer to delete() instead. Returns the paper_id
    for convenience reasons.
    """
    run_sql("""DELETE FROM aulREFERENCES WHERE paper_id = %s;""", (paper_id,))
    return paper_id

def delete_affiliations(paper_id):
    """
    Deletes the affiliations of the paper with the given paper id completely
    from the database. There is no safety net or backup copy. Should NOT be used
    alone unless you are sure that you want to do this. Refer to delete()
    instead. Returns the paper id for convenience reasons.
    """
    run_sql("""DELETE FROM aulAFFILIATIONS WHERE paper_id = %s;""", (paper_id,))
    return paper_id

def delete_authors(paper_id):
    """
    Deletes the authors of the paper with the given id completely from the
    database. There is no backup copy or safety net, make sure you want to do
    this. This function should NOT be used alone unless you know what you are
    doing. Refer to delete() instead. Returns the paper id for convenience
    reasons.
    """
    run_sql("""DELETE FROM aulAUTHORS WHERE paper_id = %s;""", (paper_id,))
    return paper_id

def delete_author_affiliations(paper_id):
    """
    Deletes the affiliations of each author that is part of the paper of the
    passed id. There is no backup copy or safety net, so make sure you want to
    call this function. This function should NOT be called alone unless you know
    what you are doing. Refer to delete() instead. Returns the paper id for
    convenience reasons.
    """
    run_sql("""DELETE FROM aulAUTHOR_AFFILIATIONS
               WHERE paper_id = %s;""", (paper_id,))
    return paper_id

def delete_author_identifiers(paper_id):
    """
    Deletes the identifiers of each author that is part of the paper of the
    passed id. There is no backup copy or safety net, so make sure you want to
    call this function. This function should NOT be called alone unless you know
    what you are doing. Refer to delete() instead. Returns the paper id for
    convenience reasons.
    """
    run_sql("""DELETE FROM aulAUTHOR_IDENTIFIERS
               WHERE paper_id = %s;""", (paper_id,))
    return paper_id

def itemize(id_user):
    """
    Returns the general information of all papers ordered descending by the last
    modification date. Each items is represented by a dictionary having the keys
    as can be found in the authorlist_config.
    """
    data = {}
    papers = run_sql("""SELECT id, title, collaboration, experiment_number,
                        last_modified FROM aulPAPERS WHERE id_user = %s
                        ORDER BY last_modified DESC;""" % (id_user))
    out_papers = data.setdefault('data', [])
    for paper in papers:
        paper_id, title, collaboration, experiment_number, last_modified = paper
        out_papers.append({cfg.JSON.PAPER_ID          : paper_id,
                           cfg.JSON.PAPER_TITLE       : title,
                           cfg.JSON.COLLABORATION     : collaboration,
                           cfg.JSON.EXPERIMENT_NUMBER : experiment_number,
                           cfg.JSON.LAST_MODIFIED     : last_modified})
    return data

def load(paper_id):
    """
    Loads all data of a paper data set with the given paper id. If the paper id
    is a falsy value or is not yet in the database the function will create a
    basic empty paper object and return it including the requested id (a falsy
    value will just be reused without any modification). The returned object is
    a dictionary using the standard keys as defined in authorlist_config.
    """
    data = {}
    load_id = load_paper(paper_id, data)
    data[cfg.JSON.PAPER_ID] = load_id
    load_references(paper_id, data)
    load_affiliations(paper_id, data)
    load_authors(paper_id, data)

    return data

def load_paper(paper_id, data):
    """
    Loads only the general paper information of the given id and adds them to
    the passed data dictionary. Should NOT be used alone as long as you are not
    sure what you are doing. Refer to load() instead. Returns the paper id for
    convenience reasons.
    """
    paper = run_sql("""SELECT title, collaboration, experiment_number,
                       last_modified  FROM aulPAPERS
                       WHERE id = %s;""", (paper_id,))
    if (not paper):
        # TODO add message here
        data[cfg.JSON.PAPER_TITLE]        = ''
        data[cfg.JSON.COLLABORATION]      = ''
        data[cfg.JSON.EXPERIMENT_NUMBER]  = ''
        data[cfg.JSON.LAST_MODIFIED]      = now()

        return paper_id

    title, collaboration, experiment_number, last_modified = paper[ 0 ]
    data[cfg.JSON.PAPER_TITLE]        = title
    data[cfg.JSON.COLLABORATION]      = collaboration
    data[cfg.JSON.EXPERIMENT_NUMBER]  = experiment_number
    data[cfg.JSON.LAST_MODIFIED]      = last_modified

    return paper_id

def load_references(paper_id, data):
    """
    Lodas only the reference information of the paper with the given id and adds
    them to the passed data dictionary. Should NOT be used alone as long as you
    are not sure what you are doing. Refer to load() instead. Returns the passed
    id for convenience reasons.
    """
    references = run_sql("""SELECT reference FROM aulREFERENCES
                            WHERE paper_id = %s;""", (paper_id,))
    reference_ids = [reference[0] for reference in references]
    data[cfg.JSON.REFERENCE_IDS] = reference_ids

    return paper_id

def load_affiliations(paper_id, data):
    """
    Loads only the affiliations information of the paper with the given id and
    adds them to the passed data dictionary. Should NOT be used alone as long as
    you do not know what you are doing. Refer to load() instead. Returns the
    passed id for convenience reasons.
    """
    result = run_sql("""SELECT item, acronym, umbrella, name_and_address, domain,
                        member, spires_id FROM aulAFFILIATIONS
                        WHERE paper_id = %s ORDER BY item;""", (paper_id,))
    affiliations = data.setdefault(cfg.JSON.AFFILIATIONS_KEY, [])

    for affiliation in result:
        item, acronym, umbrella, name, domain, member, spires_id = affiliation
        affiliations.append([item + 1, '', acronym, umbrella, name,
                             domain, bool(member), spires_id])

    return data

def load_authors(paper_id, data):
    """
    Loads the authors information of the paper with the passed id and adds them
    to the passed data dicitionary. This function will automatically also load
    all affiliations of the respective author. Should NOT be used alone as long
    as you do not know what you are doing. Refer to load() instead. Returns the
    passed id for convenience reasons.
    """
    result = run_sql("""SELECT item, family_name, given_name, name_on_paper,
                        status FROM aulAUTHORS
                        WHERE paper_id = %s ORDER BY item;""", (paper_id,))
    authors = data.setdefault(cfg.JSON.AUTHORS_KEY, [])

    for author in result:
        item, family_name, given_name, paper_name, status = author
        author_affiliations = load_author_affiliations(paper_id, item)
        author_identifiers = load_author_identifiers(paper_id, item)
        authors.append([item + 1, '', family_name, given_name, paper_name,
                        status, author_affiliations, author_identifiers])

    return data

def load_author_affiliations(paper_id, author_id):
    """
    Loads the affiliations of the author with the passed id that is part of the
    author lists of the paper with the given id. Should NOT be used alone as
    long as you are not sure what you are doing. Refer to load() instead. In
    this case the paper id is NOT returned but the author affiliations.
    """
    result = run_sql("""SELECT affiliation_acronym, affiliation_status
                        FROM aulAUTHOR_AFFILIATIONS WHERE author_item = %s
                        AND paper_id = %s ORDER BY item;""", (author_id, paper_id,))
    author_affiliations = []

    for author_affiliation in result:
        acronym, status = author_affiliation
        author_affiliations.append([acronym, status])

    return author_affiliations

def load_author_identifiers(paper_id, author_id):
    """
    Loads the identifiers of the author with the passed id that is part of the
    author lists of the paper with the given id. Should NOT be used alone as
    long as you are not sure what you are doing. Refer to load() instead. In
    this case the paper id is NOT returned but the author affiliations.
    """
    result = run_sql("""SELECT identifier_number, identifier_name
                        FROM aulAUTHOR_IDENTIFIERS WHERE author_item = %s
                        AND paper_id = %s ORDER BY item;""", (author_id, paper_id,))
    author_identifiers = []

    for author_identifier in result:
        number, name = author_identifier
        author_identifiers.append([number, name])

    return author_identifiers

def save(paper_id, user_id, in_data):
    """
    Saves the passed data dictionary using the standard authorlist_config keys
    in the database using the passed paper_id. If the id is falsy or not yet in
    the database a new data set is created, otherwise the old data set will be
    overwritten. Returns a dictionary the holds the id of the saved data set.
    """
    out_data = {}

    new_paper_id = save_paper(paper_id, user_id, in_data)
    if (paper_id is None):
        paper_id = new_paper_id
    out_data[cfg.JSON.PAPER_ID] = paper_id

    save_references(paper_id, in_data)
    save_affliations(paper_id, in_data)
    save_authors(paper_id, in_data)

    return out_data

def save_paper(paper_id, user_id, data):
    """
    Saves the general paper information from the passed data dictionary using
    the standard authorlist_config keys of the paper with the given id. Updates
    the last modified timestamp. Should NOT be used alone as long as you are not
    sure what you are doing. Refer to save() instead. Returns the paper if of
    the dataset.
    """
    if (not paper_id):
        paper_id = None
    timestamp = now()
    paper_title = data.get(cfg.JSON.PAPER_TITLE)
    if not paper_title:
        paper_title = 'Untitled paper'

    data_tuple = (  # insert values
                    paper_id,
                    user_id,
                    paper_title,
                    data[cfg.JSON.COLLABORATION],
                    data[cfg.JSON.EXPERIMENT_NUMBER],
                    timestamp,

                    # update values
                    paper_title,
                    data[cfg.JSON.COLLABORATION],
                    data[cfg.JSON.EXPERIMENT_NUMBER],
                    timestamp)

    return run_sql("""INSERT INTO aulPAPERS (id, id_user, title, collaboration,
                      experiment_number, last_modified)
                      VALUES (%s, %s, %s, %s, %s, %s)
                      ON DUPLICATE KEY UPDATE
                      title = %s,
                      collaboration = %s,
                      experiment_number = %s,
                      last_modified = %s;""", data_tuple)

def save_references(paper_id, data):
    """
    Saves the references of the passed data dictionary using the standard
    authorlist_config keys of the paper data set with the given id. Should NOT
    be used alone as long as you are not sure what you are doing. Refer to
    save() instead. Returns the paper id.
    """
    reference_ids = data[cfg.JSON.REFERENCE_IDS]

    # Insert or update old references
    for index, reference in enumerate(reference_ids):
        data_tuple = (# insert values
                      index,
                      reference,
                      paper_id,

                      # update values
                      reference)

        run_sql("""INSERT INTO
                   aulREFERENCES (item, reference, paper_id)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   reference = %s;""", data_tuple)

    # Delete old references that are out of bounds - i.e. have a higher index
    # than the length of the reference list
    run_sql("""DELETE FROM aulREFERENCES WHERE item >= %s AND paper_id = %s;""",
            (len(reference_ids), paper_id))

    return paper_id

def save_affliations(paper_id, data):
    """
    Saves the affiliations of the passed data dictionary using the standard
    authorlist_config keys to the data set of the paper with the given id.
    Should NOT be used alone as long as you are not sure what you are doing.
    Refer to save() instead. Returns the paper_id for convenience reasons.
    """
    affiliations = data[cfg.JSON.AFFILIATIONS_KEY]

    for index, affiliation in enumerate(affiliations):
        data_tuple = (# insert values
                      index,
                      affiliation[cfg.JSON.ACRONYM],
                      affiliation[cfg.JSON.UMBRELLA],
                      affiliation[cfg.JSON.NAME],
                      affiliation[cfg.JSON.DOMAIN],
                      affiliation[cfg.JSON.MEMBER],
                      affiliation[cfg.JSON.SPIRES_ID],
                      paper_id,

                      # update values
                      affiliation[cfg.JSON.ACRONYM],
                      affiliation[cfg.JSON.UMBRELLA],
                      affiliation[cfg.JSON.NAME],
                      affiliation[cfg.JSON.DOMAIN],
                      affiliation[cfg.JSON.MEMBER],
                      affiliation[cfg.JSON.SPIRES_ID])

        run_sql("""INSERT INTO
                   aulAFFILIATIONS (item, acronym, umbrella, name_and_address,
                                    domain, member, spires_id, paper_id)
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   acronym = %s,
                   umbrella = %s,
                   name_and_address = %s,
                   domain = %s,
                   member = %s,
                   spires_id = %s;""", data_tuple)

    # Delete old affiliations that are out of bounds - i.e. have a higher index
    # than the length of the affiliations list
    run_sql("""DELETE FROM aulAFFILIATIONS WHERE item >= %s AND paper_id = %s;""",
            (len(affiliations), paper_id))

    return paper_id

def save_authors(paper_id, data):
    """
    Saves the authors of the passed data dictionary using the standard
    authorlist_config keys in the database of the paper with the given id.
    Should NOT be used alone as long as you do not know what you are doing.
    Refer to save() instead. Returns the paper_id.
    """
    authors = data[cfg.JSON.AUTHORS_KEY]

    for index, author in enumerate(authors):
        data_tuple = (# insert values
                      index,
                      author[cfg.JSON.FAMILY_NAME],
                      author[cfg.JSON.GIVEN_NAME],
                      author[cfg.JSON.PAPER_NAME],
                      author[cfg.JSON.STATUS],
                      paper_id,

                      # update values
                      author[cfg.JSON.FAMILY_NAME],
                      author[cfg.JSON.GIVEN_NAME],
                      author[cfg.JSON.PAPER_NAME],
                      author[cfg.JSON.STATUS])

        run_sql("""INSERT INTO
                   aulAUTHORS (item, family_name, given_name, name_on_paper,
                               status, paper_id)
                   VALUES(%s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   family_name = %s,
                   given_name = %s,
                   name_on_paper = %s,
                   status = %s;""", data_tuple)

        save_author_affiliations(paper_id, index, len(authors),
                                 author[cfg.JSON.AFFILIATIONS])
        save_author_identifiers(paper_id, index, len(authors),
                                author[cfg.JSON.IDENTIFIERS])

    # Delete old authors that are out of bounds - i.e. have a higher index
    # than the length of the affiliations list
    run_sql("""DELETE FROM aulAUTHORS WHERE item >= %s AND paper_id = %s;""",
            (len(authors), paper_id))

    return paper_id

def save_author_affiliations(paper_id, author_id, number_of_authors, data):
    """
    Saves the affiliations of the passed author using the data dictionary and
    the standard authorlist_config keys and the paper id. Deletes also all old
    entries that are 'out of bounds' facilitating the number_of_authors
    paramter. Should NOT be used alone as long as you do not exactly know what
    you are doing. Refer to save() instead. Returns the paper id.
    """
    for index, affiliation in enumerate(data):
        data_tuple = (# insert values
                      index,
                      affiliation[cfg.JSON.AFFILIATION_ACRONYM],
                      affiliation[cfg.JSON.AFFILIATION_STATUS],
                      author_id,
                      paper_id,

                      # update values
                      affiliation[cfg.JSON.AFFILIATION_ACRONYM],
                      affiliation[cfg.JSON.AFFILIATION_STATUS])

        run_sql("""INSERT INTO
                   aulAUTHOR_AFFILIATIONS (item, affiliation_acronym,
                                           affiliation_status, author_item,
                                           paper_id)
                   VALUES(%s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   affiliation_acronym = %s,
                   affiliation_status = %s;""", data_tuple)

    # Delete entries that the author does not have anymore
    run_sql("""DELETE FROM aulAUTHOR_AFFILIATIONS WHERE item >= %s
               AND author_item = %s AND paper_id = %s;""",
            (len(data), author_id, paper_id))

    # Delete entries of non existing author
    run_sql("""DELETE FROM aulAUTHOR_AFFILIATIONS WHERE author_item >= %s
                AND paper_id = %s;""",
            (number_of_authors, paper_id))

    return paper_id

def save_author_identifiers(paper_id, author_id, number_of_authors, data):
    """
    Saves the identifiers of the passed author using the data dictionary and
    the standard authorlist_config keys and the paper id. Deletes also all old
    entries that are 'out of bounds' facilitating the number_of_authors
    paramter. Should NOT be used alone as long as you do not exactly know what
    you are doing. Refer to save() instead. Returns the paper id.
    """
    for index, identifier in enumerate(data):
        data_tuple = (# insert values
                      index,
                      identifier[cfg.JSON.IDENTIFIER_NUMBER],
                      identifier[cfg.JSON.IDENTIFIER_NAME],
                      author_id,
                      paper_id,

                      # update values
                      identifier[cfg.JSON.IDENTIFIER_NUMBER],
                      identifier[cfg.JSON.IDENTIFIER_NAME])

        run_sql("""INSERT INTO
                   aulAUTHOR_IDENTIFIERS (item, identifier_number,
                                           identifier_name, author_item,
                                           paper_id)
                   VALUES(%s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   identifier_number = %s,
                   identifier_name = %s;""", data_tuple)

    # Delete entries that the author does not have anymore
    run_sql("""DELETE FROM aulAUTHOR_IDENTIFIERS WHERE item >= %s
               AND author_item = %s AND paper_id = %s;""",
            (len(data), author_id, paper_id))

    # Delete entries of non existing author
    run_sql("""DELETE FROM aulAUTHOR_IDENTIFIERS WHERE author_item >= %s
                AND paper_id = %s;""",
            (number_of_authors, paper_id))

    return paper_id

def get_owner(paper_id):
    """Returns the id_user of a paper"""
    result = run_sql("SELECT id_user FROM aulPAPERS WHERE id = %s;" % \
        (paper_id))[0][0]
    if result:
        return result
    return None
