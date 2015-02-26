# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""ORCID response fixture."""

orcid_bio = """{
  "message-version" : "1.1",
  "orcid-profile" : {
    "orcid" : null,
    "orcid-identifier" : {
      "value" : null,
      "uri" : "http://orcid.org/0000-0002-1825-0097",
      "path" : "0000-0002-1825-0097",
      "host" : "orcid.org"
    },
    "orcid-preferences" : {
      "locale" : "EN"
    },
    "orcid-history" : {
      "creation-method" : "WEBSITE",
      "completion-date" : {
        "value" : 1352727077585
      },
      "submission-date" : {
        "value" : 1352723476658
      },
      "last-modified-date" : {
        "value" : 1415635049863
      },
      "claimed" : {
        "value" : true
      },
      "source" : null,
      "visibility" : null
    },
    "orcid-bio" : {
      "personal-details" : {
        "given-names" : {
          "value" : "Josiah"
        },
        "family-name" : {
          "value" : "Carberry"
        },
        "other-names" : {
          "other-name" : [ {
            "value" : "J. Carberry, Josiah Stinkney Carberry, J. S. Carberry"
          } ],
          "visibility" : null
        }
      },
      "biography" : {
        "value" : "Josiah Carberry is a fictitious person. This account is used as a demonstration account by ORCID, CrossRef and others who wish to demonstrate the interaction of ORCID with other scholarly communication systems without having to use a real-person's account.\\n\\nJosiah Stinkney Carberry is a fictional professor, created as a joke in 1929. He is said to still teach at Brown University, and to be known for his work in \\"psychoceramics\\", the supposed study of \\"cracked pots\\". See his Wikipedia entry for more details.",
        "visibility" : null
      },
      "researcher-urls" : {
        "researcher-url" : [ {
          "url-name" : {
            "value" : "Wikipedia Entry"
          },
          "url" : {
            "value" : "http://en.wikipedia.org/wiki/Josiah_Carberry"
          }
        }, {
          "url-name" : {
            "value" : "Brown University Page"
          },
          "url" : {
            "value" : "http://library.brown.edu/about/hay/carberry.php"
          }
        } ],
        "visibility" : null
      },
      "keywords" : {
        "keyword" : [ {
          "value" : "psychoceramics"
        } ],
        "visibility" : null
      },
      "external-identifiers" : {
        "external-identifier" : [ {
          "external-id-orcid" : {
            "value" : null,
            "uri" : "http://orcid.org/0000-0002-5982-8983",
            "path" : "0000-0002-5982-8983",
            "host" : "orcid.org"
          },
          "external-id-common-name" : {
            "value" : "Scopus Author ID"
          },
          "external-id-reference" : {
            "value" : "7007156898"
          },
          "external-id-url" : {
            "value" : "http://www.scopus.com/inward/authorDetails.url?authorID=7007156898&partnerID=MN8TOARS"
          }
        } ],
        "visibility" : null
      },
      "delegation" : null,
      "applications" : null,
      "scope" : null
    },
    "orcid-activities" : {
      "affiliations" : null
    },
    "type" : "USER",
    "group-type" : null,
    "client-type" : null
  }
}"""
