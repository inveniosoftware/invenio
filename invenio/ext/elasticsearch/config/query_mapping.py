"""Configuration of search fields to map them with the elasticsearch
   equivalent.
   For those not defined here, the search key will be used to retrieve
   elasticsearch results
"""

fields = {
    "author": ["authors.first_name", "authors.last_name",
               "authors.full_name", "_first_author.first_name",
               "_first_author.last_name", "_first_author.full_name",
               "authors.first_name.raw", "authors.last_name.raw",
               "authors.full_name.raw", "_first_author.first_name.raw",
               "_first_author.last_name.raw", "_first_author.full_name.raw",
               "_first_author.name_variations", "authors.name_variations"],

    "raw_fields": ["title.raw", "authors.first_name.raw",
                   "authors.last_name.raw", "authors.full_name.raw",
                   "_first_author.first_name.raw",
                   "_first_author.last_name.raw",
                   "_first_author.full_name.raw",
                   "_first_author.name_variations", "authors.name_variations"],
    }
