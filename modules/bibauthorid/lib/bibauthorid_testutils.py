from lxml.etree import tostring
from lxml.etree import SubElement
from lxml.etree import Element
from lxml.etree import fromstring


from invenio.dbquery import run_sql
from invenio.bibrecord import create_record
from invenio.bibupload import bibupload
from invenio.bibauthorid_name_utils import create_canonical_name
import invenio.bibauthorid_config

bconfig = invenio.bibauthorid_config


def person_in_aidpersonidpapers(name, recid):

    result = run_sql("select * from aidPERSONIDPAPERS where name = BINARY %s"
                     "and bibrec = %s", (name, recid))
    if result:
        return True
    else:
        return False


def person_in_aidpersoniddata(name):

    can_name = create_canonical_name(name) + '.1'
    result = run_sql("select * from aidPERSONIDDATA where data = %s",
                     (can_name,))
    if result:
        return True
    else:
        return False


def clean_authors_tables(recid):
        run_sql("delete from aidPERSONIDDATA where personid in"
                "(select personid from aidPERSONIDPAPERS where  bibrec=%s)",
                (recid,))
        run_sql("delete from aidPERSONIDPAPERS where bibrec=%s", (recid,))


def get_count_of_pids(papers_table=False):
    if papers_table:
        return run_sql("select count(distinct(personid)) from aidPERSONIDPAPERS")[0][0]

    return run_sql("select count(distinct(personid)) from aidPERSONIDDATA")[0][0]


def claim_test_paper(recid):
    run_sql("update aidPERSONIDPAPERS set flag=2 where bibrec = %s", (recid,))

def reject_test_paper(recid):
    run_sql("update aidPERSONIDPAPERS set flag=-2 where bibrec = %s", (recid,))

def get_bibref_value_for_name(name):
    result = run_sql("select bibref_value from aidPERSONIDPAPERS where name =%s", (name,))
    if result:
        return result[0][0]


def is_test_paper_claimed(recid, bibref_table):
    result = run_sql(
        "select * from aidPERSONIDPAPERS where bibrec=%s and flag=2 and bibref_table='%s' limit 1",
        (recid,
         bibref_table))
    if result:
        return True
    else:
        return False



def get_bibrec_for_record(marcxml, opt_mode):
    '''
    A record is uploaded to the system using mainly functionality
    of the bibupload module. Then a bibrec is returned for the record.
    '''
    recs = create_record(marcxml)
    _, recid, _ = bibupload(recs[0], opt_mode=opt_mode)
    return recid


def get_modified_marc_for_test(marcxml_string, author_name=None,
                               co_authors_names=None, ext_id=None):  # TODO: To refactor!
    marcxml = fromstring(marcxml_string)
    fields = marcxml.getchildren()
    author_exists = False
    coauthors_exist = False
    extids_exist = False
    if co_authors_names:
        co_authors_names = list(co_authors_names)
    coauthor_index = 0
    for field in fields:
        if field.items()[0][1] == '100':
            author_exists = True
            if author_name:
                author_subfields = field.findall('subfield')
                for subfield in author_subfields:
                    if 'i' in subfield.attrib.values():
                        extids_exist = True
                        subfield.text = ext_id
                    else:
                        subfield.text = author_name
                if ext_id and not extids_exist:
                    ext_field = SubElement(field, 'subfield', {'code': 'i'})
                    ext_field.text = ext_id
            else:
                marcxml.remove(field)
        if field.items()[0][1] == '700':
            coauthors_exist = True
            if co_authors_names:
                coauthor_subfield = field.find('subfield')
                coauthor_subfield.text = co_authors_names[coauthor_index]
                coauthor_index += 1
            else:
                marcxml.remove(field)

    if author_name and not author_exists:
        build_test_marcxml_field(marcxml, 100, author_name)
    if co_authors_names and not coauthors_exist:
        for co_author_name in co_authors_names:
            build_test_marcxml_field(marcxml, 700, co_author_name)

    return tostring(marcxml)


def build_test_marcxml_field(record, tag, content, is_controlfield=False):
    if is_controlfield:
        marc_field = SubElement(record, 'controlfield',
                                {'tag': str(tag)})
        marc_field.text = content
    else:
        marc_field = SubElement(record, 'datafield',
                                {'tag': str(tag),
                                    'ind1': '', 'ind2': ''})
        marc_sub = SubElement(marc_field, 'subfield', {'code': 'a'})
        marc_sub.text = content


def get_new_marc_for_test(name, author_name=None, co_authors_names=None,
                          ext_id=None):
    """
    Returns a MarcXML string base on the given arguments.
    """

    record = Element('record')
    build_test_marcxml_field(record, 245, name)
    if author_name:
        build_test_marcxml_field(record, 100, author_name)
    if co_authors_names:
        for co_author_name in co_authors_names:
            build_test_marcxml_field(record, 700, co_author_name)

    return tostring(record)


def add_001_field(marcxml_string, recid):
    marcxml = fromstring(marcxml_string)
    recid_field = SubElement(marcxml, 'controlfield', {'tag': '001'})
    recid_field.text = str(recid)
    return tostring(marcxml)

def get_last_recid():
    try:
        return run_sql("select bibrec from aidPERSONIDPAPERS order by bibrec desc  limit 1")[0][0]
    except IndexError:
        return 0

def get_last_bibref_value():
    try:
        return run_sql("select bibref_value from aidPERSONIDPAPERS order by bibref_value desc  limit 1")[0][0]
    except IndexError:
        return 0
