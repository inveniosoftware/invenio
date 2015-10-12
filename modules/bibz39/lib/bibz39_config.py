# coding=utf-8


CFG_Z39_SERVER = {
    "Library of congress": {"address": "lx2.loc.gov", "port": 210, "databasename": "LCDB",
                            "preferredRecordSyntax": 'USMARC'},
    "Library of congress MARC8": {"address": "lx2.loc.gov", "port": 210,
                                  "databasename": "LCDB_MARC8",
                                  "preferredRecordSyntax": 'USMARC', "default": True},
    "UNOG Library": {"address": "eu.alma.exlibrisgroup.com", "port": 1921,
                     "databasename": "41UNOG_INST",
                     "preferredRecordSyntax": 'USMARC', "default":True},

    "British library": {"address": "z3950cat.bl.uk", "port": 9909, "databasename": "BNB03U",
                        "preferredRecordSyntax": 'USMARC', 'user': 'UNCITR2906',
                        'password': 'E3H2fv6p', "default": False},

    "University of Chicago": {"address": "ole.uchicago.edu", "port": 210, "databasename": "ole",
                              "preferredRecordSyntax": 'USMARC', "default": False},

    "OCLC": {"address": "zcat.oclc.org", "port": 210, "databasename": "OLUCWorldCat",
                              "preferredRecordSyntax": 'USMARC', "default": False},
}
