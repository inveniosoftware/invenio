from urllib2 import urlopen
from lxml import etree


def get_wikipedia_link(viaf_id):
    url = "http://viaf.org/viaf/" + str(viaf_id) +"/viaf.xml"
    string_xml = urlopen(url).read()
    xml = etree.fromstring(str(string_xml))
    author_wikipedia_id = xml.xpath("/ns2:VIAFCluster/ns2:sources/ns2:source[contains(text(),'WKP')]/@nsid",namespaces={"ns2":"http://viaf.org/viaf/terms#"})
    if type(author_wikipedia_id) is list:
        author_wikipedia_id = author_wikipedia_id[0]
    url_to_wikipedia = "http://www.wikipedia.com/wiki/"+author_wikipedia_id
    return url_to_wikipedia

