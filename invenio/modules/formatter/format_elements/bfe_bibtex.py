# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints BibTeX meta-data
"""
__revision__ = "$Id$"

from invenio.config import CFG_SITE_LANG

def format_element(bfo, width="50"):
    """
    Prints a full BibTeX record.

    'width' must be bigger than or equal to 30.
    This format element is an example of large element, which does
    all the formatting by itself

    @param width: the width (in number of characters) of the record
    """
    out = "@"
    width = int(width)
    if width < 30:
        width = 30

    name_width = 20
    value_width = width-name_width
    recID = bfo.control_field('001')

    #Print entry type
    import invenio.modules.formatter.format_elements.bfe_collection as bfe_collection
    collection = bfe_collection.format_element(bfo=bfo, kb="DBCOLLID2BIBTEX")
    if collection == "":
        out += "article"
    else:
        out += collection

    out += "{"

    #Print BibTeX key
    #
    #Try to have: author_name:recID
    #If author_name cannot be found, use primary_report_number
    #If primary_report_number cannot be found, use additional_report_number
    #If additional_report_number cannot be found, use title:recID
    #If title cannot be found, use only recID
    #
    #The construction of this key is inherited from old BibTeX format
    #written in EL, in old BibFormat.
    key = recID
    author = bfo.field("100__a")
    if author != "":
        key = get_name(author)+":"+recID
    else:
        author = bfo.field("700__a")
        if author != "":
            key = get_name(author)+":"+recID
        else:
            primary_report_number = bfo.field("037__a")
            if primary_report_number != "":
                key = primary_report_number
            else:
                additional_report_number = bfo.field("088__a")
                if additional_report_number != "":
                    key = primary_report_number
                else:
                    title = bfo.field("245__a")
                    if title != "":
                        key = get_name(title)+":"+recID
    out += key +","

    #Print authors
    #If author cannot be found, print a field key=recID
    import invenio.modules.formatter.format_elements.bfe_authors as bfe_authors
    authors = bfe_authors.format_element(bfo=bfo,
                                         limit="",
                                         separator=" and ",
                                         extension="",
                                         print_links="no")
    if authors == "":
        out += format_bibtex_field("key",
                                   recID,
                                   name_width,
                                   value_width)
    else:
        out += format_bibtex_field("author",
                                   authors,
                                   name_width,
                                   value_width)

    #Print editors
    import invenio.modules.formatter.format_elements.bfe_editors as bfe_editors
    editors = bfe_editors.format_element(bfo=bfo, limit="",
                                         separator=" and ",
                                         extension="",
                                         print_links="no")
    out += format_bibtex_field("editor",
                               editors,
                               name_width,
                               value_width)

    #Print title
    import invenio.modules.formatter.format_elements.bfe_title as bfe_title
    title = bfe_title.format_element(bfo=bfo, separator = ". ")
    out += format_bibtex_field("title",
                               '{' + title + '}',
                               name_width,
                               value_width)

    #Print institution
    if collection ==  "techreport":
        publication_name = bfo.field("269__b")
        out += format_bibtex_field("institution",
                                   publication_name,
                                   name_width, value_width)

    #Print organization
    if collection == "inproceedings" or collection == "proceedings":
        organization = []
        organization_1 = bfo.field("260__b")
        if organization_1 != "":
            organization.append(organization_1)
        organization_2 = bfo.field("269__b")
        if organization_2 != "":
            organization.append(organization_2)
        out += format_bibtex_field("organization",
                                   ". ".join(organization),
                                   name_width,
                                   value_width)

    #Print publisher
    if collection == "book" or \
           collection == "inproceedings" \
           or collection == "proceedings":
        publishers = []
        import invenio.modules.formatter.format_elements.bfe_publisher as bfe_publisher
        publisher = bfe_publisher.format_element(bfo=bfo)
        if publisher != "":
            publishers.append(publisher)
        publication_name = bfo.field("269__b")
        if publication_name != "":
            publishers.append(publication_name)
        imprint_publisher_name = bfo.field("933__b")
        if imprint_publisher_name != "":
            publishers.append(imprint_publisher_name)
        imprint_e_journal__publisher_name = bfo.field("934__b")
        if imprint_e_journal__publisher_name != "":
            publishers.append(imprint_e_journal__publisher_name)

        out += format_bibtex_field("publisher",
                                   ". ".join(publishers),
                                   name_width,
                                   value_width)

    #Print journal
    if collection == "article":
        journals = []
        host_title = bfo.field("773__p")
        if host_title != "":
            journals.append(host_title)
        journal = bfo.field("909C4p")
        if journal != "":
            journals.append(journal)

        out += format_bibtex_field("journal",
                                   ". ".join(journals),
                                   name_width,
                                   value_width)

    #Print school
    if collection == "phdthesis":
        university = bfo.field("502__b")

        out += format_bibtex_field("school",
                                   university,
                                   name_width,
                                   value_width)

    # Collaboration
    collaborations = []
    for collaboration in bfo.fields("710__g"):
        if collaboration not in collaborations:
            collaborations.append(collaboration)
    out += format_bibtex_field("collaboration",
                               ", ".join(collaborations),
                                   name_width,
                                   value_width)

    #Print address
    if collection == "book" or \
           collection == "inproceedings" or \
           collection == "proceedings" or \
           collection == "phdthesis" or \
           collection == "techreport":
        addresses = []
        publication_place = bfo.field("260__a")
        if publication_place != "":
            addresses.append(publication_place)
        publication_place_2 = bfo.field("269__a")
        if publication_place_2 != "":
            addresses.append(publication_place_2)
        imprint_publisher_place = bfo.field("933__a")
        if imprint_publisher_place != "":
            addresses.append(imprint_publisher_place)
        imprint_e_journal__publisher_place = bfo.field("934__a")
        if imprint_e_journal__publisher_place != "":
            addresses.append(imprint_e_journal__publisher_place)

        out += format_bibtex_field("address",
                                   ". ".join(addresses),
                                   name_width,
                                   value_width)

    #Print number
    if collection == "techreport" or \
           collection == "article":
        numbers = []
        primary_report_number = bfo.field("037__a")
        if primary_report_number != "":
            numbers.append(primary_report_number)
        additional_report_numbers = bfo.fields("088__a")
        additional_report_numbers = ". ".join(additional_report_numbers)
        if additional_report_numbers != "":
            numbers.append(additional_report_numbers)
        host_number = bfo.field("773__n")
        if host_number != "":
            numbers.append(host_number)
        number = bfo.field("909C4n")
        if number != "":
            numbers.append(number)
        out += format_bibtex_field("number",
                                   ". ".join(numbers),
                                   name_width,
                                   value_width)

    #Print volume
    if collection == "article" or \
           collection == "book":
        volumes = []
        host_volume = bfo.field("773__v")
        if host_volume != "":
            volumes.append(host_volume)
        volume = bfo.field("909C4v")
        if volume != "":
            volumes.append(volume)

        out += format_bibtex_field("volume",
                                   ". ".join(volumes),
                                   name_width,
                                   value_width)

    #Print series
    if collection == "book":
        series = bfo.field("490__a")
        out += format_bibtex_field("series",
                                   series,
                                   name_width,
                                   value_width)

    #Print pages
    if collection == "article" or \
           collection == "inproceedings":
        pages = []
        host_pages = bfo.field("773c")
        if host_pages != "":
            pages.append(host_pages)
        nb_pages = bfo.field("909C4c")
        if nb_pages != "":
            pages.append(nb_pages)
        phys_pagination = bfo.field("300__a")
        if phys_pagination != "":
            pages.append(phys_pagination)

        out += format_bibtex_field("pages",
                                   ". ".join(pages),
                                   name_width,
                                   value_width)

    #Print month
    month = get_month(bfo.field("269__c"))
    if month == "":
        month = get_month(bfo.field("260__c"))
        if month == "":
            month = get_month(bfo.field("502__c"))

    out += format_bibtex_field("month",
                               month,
                               name_width,
                               value_width)

    #Print year
    year = get_year(bfo.field("269__c"))
    if year == "":
        year = get_year(bfo.field("260__c"))
        if year == "":
            year = get_year(bfo.field("502__c"))
            if year == "":
                year = get_year(bfo.field("909C0y"))

    out += format_bibtex_field("year",
                               year,
                               name_width,
                               value_width)

    #Print note
    note = bfo.field("500__a")
    out += format_bibtex_field("note",
                               note,
                               name_width,
                               value_width)

    #Print doi
    fields = bfo.fields("0247_")
    for field in fields:
        if field.get('2', 'DOI') == 'DOI' and 'a' in field:
            out += format_bibtex_field("doi",
                                       "{%s}" % field['a'],
                                       name_width,
                                       value_width)
            out += format_bibtex_field("url",
                                       "{http://dx.doi.org/%s}" % field['a'],
                                       name_width,
                                       value_width)

    out += "\n}"

    return out


def format_bibtex_field(name, value, name_width=20, value_width=40):
    """
    Formats a name and value to display as BibTeX field.

    'name_width' is the width of the name of the field (everything before " = " on first line)
    'value_width' is the width of everything after " = ".

    6 empty chars are printed before the name, then the name and then it is filled with spaces to meet
    the required width. Therefore name_width must be > 6 + len(name)

    Then " = " is printed (notice spaces).

    So the total width will be::
        name_width + value_width + len(" = ")
                                        (3)

    if value is empty string, then return empty string.

    For example format_bibtex_field('author', 'a long value for this record', 13, 15) will
    return :
    >>
    >>      name    = "a long value
    >>                 for this record",
    """
    if name_width < 6 + len(name):
        name_width = 6 + len(name)
    if value_width < 2:
        value_width = 2
    if value is None or value == "":
        return ""

    #format name
    name = "\n      "+name
    name = name.ljust(name_width)

    #format value
    value = '"'+value+'"' #Add quotes to value
    value_lines = []
    last_cut = 0
    cursor = value_width -1 #First line is smaller because of quote
    increase = False
    while cursor < len(value):
        if cursor == last_cut: #Case where word is bigger than the max
                               #number of chars per line
            increase = True
            cursor = last_cut+value_width-1

        if value[cursor] != " " and not increase:
            cursor -= 1
        elif value[cursor] != " " and increase:
            cursor += 1
        else:
            value_lines.append(value[last_cut:cursor])
            last_cut = cursor
            cursor += value_width
            increase = False
    #Take rest of string
    last_line = value[last_cut:]
    if last_line != "":
        value_lines.append(last_line)

    tabs = "".ljust(name_width + 2)
    value = ("\n"+tabs).join(value_lines)

    return name + ' = ' + value + ","

def get_name(string):
    """
    Tries to return the last name contained in a string.

    In fact returns the text before any comma in 'string', whith
    spaces removed. If comma not found, get longest word in 'string'

    Behaviour inherited from old GET_NAME function defined as UFD in
    old BibFormat. We need to return the same value, to keep back
    compatibility with already generated BibTeX records.

    Eg: get_name("سtlund, عvind B") returns "سtlund".
    """
    names = string.split(',')

    if len(names) == 1:
        #Comma not found.
        #Split around any space
        longest_name = ""
        words = string.split()
        for word in words:
            if len(word) > len(longest_name):
                longest_name = word
        return longest_name
    else:
        return names[0].replace(" ", "")


def get_year(date, default=""):
    """
    Returns the year from a textual date retrieved from a record

    The returned value is a 4 digits string.
    If year cannot be found, returns 'default'
    Returns first value found.

    @param date: the textual date to retrieve the year from
    @param default: a default value to return if year not fount
    """
    import re
    year_pattern = re.compile(r'\d\d\d\d')
    result = year_pattern.search(date)
    if result is not None:
        return result.group()

    return default

def get_month(date, ln=CFG_SITE_LANG, default=""):
    """
    Returns the year from a textual date retrieved from a record

    The returned value is the 3 letters short month name in language 'ln'
    If year cannot be found, returns 'default'

    @param date: the textual date to retrieve the year from
    @param default: a default value to return if year not fount
    """
    import re
    from invenio.utils.date import get_i18n_month_name
    from invenio.base.i18n import language_list_long

    #Look for textual month like "Jan" or "sep" or "November" or "novem"
    #Limit to CFG_SITE_LANG as language first (most probable date)
    #Look for short months. Also matches for long months
    short_months = [get_i18n_month_name(month).lower()
                    for month in range(1, 13)] # ["jan","feb","mar",...]
    short_months_pattern = re.compile(r'('+r'|'.join(short_months)+r')',
                                      re.IGNORECASE) # (jan|feb|mar|...)
    result = short_months_pattern.search(date)
    if result is not None:
        try:
            month_nb = short_months.index(result.group().lower()) + 1
            return get_i18n_month_name(month_nb, "short", ln)
        except:
            pass

    #Look for month specified as number in the form 2004/03/08 or 17 02 2004
    #(always take second group of 2 or 1 digits separated by spaces or - etc.)
    month_pattern = re.compile(r'\d([\s]|[-/.,])+(?P<month>(\d){1,2})([\s]|[-/.,])')
    result = month_pattern.search(date)
    if result is not None:
        try:
            month_nb = int(result.group("month"))
            return get_i18n_month_name(month_nb, "short", ln)
        except:
            pass

    #Look for textual month like "Jan" or "sep" or "November" or "novem"
    #Look for the month in each language

    #Retrieve ['en', 'fr', 'de', ...]
    language_list_short = [x[0]
                           for x in language_list_long()]
    for lang in language_list_short: #For each language
        #Look for short months. Also matches for long months
        short_months = [get_i18n_month_name(month, "short", lang).lower()
                        for month in range(1, 13)] # ["jan","feb","mar",...]
        short_months_pattern = re.compile(r'('+r'|'.join(short_months)+r')',
                                          re.IGNORECASE) # (jan|feb|mar|...)
        result = short_months_pattern.search(date)
        if result is not None:
            try:
                month_nb = short_months.index(result.group().lower()) + 1
                return get_i18n_month_name(month_nb, "short", ln)
            except:
                pass

    return default


