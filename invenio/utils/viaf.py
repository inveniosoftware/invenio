from urllib2 import urlopen
from lxml import etree
from invenio.modules.formatter.engine import BibFormatObject

CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD = "856"
CFG_VIAF_LINK_NAME_LABEL_SUBFIELD = 'n'
CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD = 'wikipedia'
CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD = 'a'

def get_wikipedia_link(viaf_id):
    ## Query viaf api and parse results
    url = "http://viaf.org/viaf/" + str(viaf_id) +"/viaf.xml"
    string_xml = urlopen(url).read()
    xml = etree.fromstring(str(string_xml))

    ## Do an xpath query for all the wikipedia links
    ## that can be found for the author and return the first one
    author_wikipedia_id = xml.xpath("/ns2:VIAFCluster/ns2:sources/ns2:source[contains(text(),'WKP')]/@nsid",namespaces={"ns2":"http://viaf.org/viaf/terms#"})
    url_to_wikipedia = None
    if type(author_wikipedia_id) is list and author_wikipedia_id:
        author_wikipedia_id = author_wikipedia_id[0]
        url_to_wikipedia = "http://www.wikipedia.com/wiki/"+author_wikipedia_id
    return url_to_wikipedia

def get_wiki_link_from_record(bfo):
    link = None
    fields = []
    if type(bfo) is BibFormatObject:
        fields = bfo.fields(CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD)
    else:
        fields = bfo.get(CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD,[])
    for field in fields:
        if type(field) is dict:
            if field.get(CFG_VIAF_LINK_NAME_LABEL_SUBFIELD,None) == CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD:
                link = field.get(CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD,None)
        else:
            record_dict = {}
            for subfields in field:
                if type(subfields) is list:
                    for subfield in subfields:
                        record_dict[subfield[0]] = subfield[1]
            if record_dict.get(CFG_VIAF_LINK_NAME_LABEL_SUBFIELD,None) == CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD:
                link = record_dict.get(CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD,None)
    return link


