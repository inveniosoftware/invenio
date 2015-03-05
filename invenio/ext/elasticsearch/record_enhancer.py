"""This file is responsible for the enhancing the json records before storing
   them in Elasticsearch. Normally here all the calculated fields will be
   calculated.
"""

from invenio.base.wrappers import lazy_import
get_toks = lazy_import('invenio.legacy.bibindex.engine_utils:load_tokenizers')


class Enhancer(object):
    def __init__(self):
        tokenizers = get_toks()
        self.author_tokenizer = tokenizers['BibIndexAuthorTokenizer']()

    def _get_text(self, recid):
        """Return a list of dictionaries with filename and fulltext"""
        from invenio.legacy.bibdocfile.api import BibRecDocs
        bibrecdocs = BibRecDocs(recid)

        bibrecdocs.get_text()  # this creates the content for each text file
        documents = bibrecdocs.list_bibdocs_by_names()

        document_list = []
        for k, v in documents.iteritems():
            try:
                doc = {
                    "fulltext": v.get_text(),
                    "filename": k
                }
                document_list.append(doc)
            except AttributeError:
                pass
        return document_list

    def enhance_rec_content(self, record):
        """Add remove fields from the record to be stored in elasticsearch
           Here we will add all the calculated fields
        """
        del record["__meta_metadata__"]
        # FIXME handle mutliple collection types
        try:
            collections = [val.values()[0]
                           for val in record["collections"]]
        except KeyError as e:
            print "Record %s doesn't have %s" % (record["_id"], e)

        try:
            record['collections'] = collections
        except KeyError as e:
            print "Record %s doesn't have %s" % (record["_id"], e)

        try:
            record['title'] = record['title']['title']
        except KeyError as e:
            print "Record %s doesn't have %s" % (record["_id"], e)

        try:
            record['abstract'] = record['abstract']['summary']
        except KeyError as e:
            print "Record %s doesn't have %s" % (record["_id"], e)

        # get full text if any
        try:
            record['documents'] = self._get_text(record["_id"])

            # Create name iterations
            def _add_variations(x):
                name = x['full_name']
                value = self.author_tokenizer.tokenize_for_fuzzy_authors(name)
                x['name_variations'] = value
                return x
            record['authors'] = map(_add_variations, record['authors'])
            _add_variations(record["_first_author"])

        except KeyError as e:
            print "Record %s doesn't have %s" % (record["_id"], e)

        return record
