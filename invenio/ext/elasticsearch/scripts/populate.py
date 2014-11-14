"""Script to populate elasticsearch with multiple records"""

import pyelasticsearch

URL = "http://188.184.141.134:9200"
BULK_SIZE = 5


class Populate(object):

    def __init__(self, url):
        """Constructor to initialize the populator and create the connection
        with elasticsearch"""
        self.es_client = pyelasticsearch.ElasticSearch(url)

    def create_index(self):
        """Function to create the index and handle with mappings"""
        """The only extra parameter so far is to define that collections will
        not be analyzed, just an array of strings and that authors are nested
        objects"""
        mapping = {}
        mapping["records"] = {"properties": {}}
        mapping["records"]["properties"] = {"collections": {}}
        mapping["records"]["properties"] = {"collections": {}}
        mapping["records"]["properties"]["collections"] = {
            "type": "string",
            "index": "not_analyzed"
        }
        mapping["records"]["properties"]["authors"] = {"type": "nested"}
        mapping["records"]["properties"]["authors"] = {
            "properties": {
                "first_name": {
                    "type": "string"
                },
                "last_name": {
                    "type": "string"
                },
                "full_name": {
                    "type": "string"
                }
            }
        }
        #import json
        #print json.dumps(mapping, sort_keys=True,indent=4, i
        #                 separators=(',', ': '))
        settings_dict = {"mappings": mapping}
        return self.es_client.create_index("invenio", settings_dict)

    def get_record(self, recid):
        "Get record, remove medata and fix collections"
        from invenio.modules.records.api import get_record
        record_as_dict = get_record(recid, reset_cache=True)
        if record_as_dict is None:
            return None
        record_as_dict = record_as_dict.dumps()
        del record_as_dict["__meta_metadata__"]
        del record_as_dict["_id"]
        collections = [val.values()[0]
                       for val in record_as_dict["collections"]]
        record_as_dict["collections"] = collections
        return record_as_dict

    def bulk_drive(self):
        """Get records in groups of BULK_SIZE and bulk_index"""
        start = 83  # recid
        end = 143
        i = start
        while i <= end:
            rec_list = [self.get_record(k) for k in range(i, i+1+BULK_SIZE)]
            rec_list = filter(None, rec_list)
            if rec_list:
                self.bulk_index(rec_list)
            i += BULK_SIZE

    def bulk_index(self, rec):
        return self.es_client.bulk_index("invenio", "records", rec)


def main():
    client = Populate(URL)
    client.create_index()
    #client.bulk_drive()

if __name__ == '__main__':
    main()
