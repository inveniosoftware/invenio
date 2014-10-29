from bfe_date import format_element as date_element


def format_element(bfo, date_format='%d %B %Y', source_formats='%Y-%m-%d', source_fields="260__c",
                   guess_source_format="no", ignore_date_format_for_year_only="yes"):

    """
    Prints the imprint publication date and pagination (if applicable)
    Uses the date format element, and thus the same parameters.


    Parameter <code>date_format</code> allows to specify the string
    representation of the output.

    The format string has the same behaviour as the strftime() function:
        <pre>Eg: 1982-09-24 07:32:00
            "%d %B %Y"   -> 24 September 1982
            "%I:%M"      -> 07:32
        </pre>

    Note that if input date is simply a year (4 digits), it is
    returned as such if <code>ignore_date_format_for_year_only</code>
    is set to 'yes', regardless of <code>date_format</code>.

    Parameter <code>source_formats</code> allows to specify the
    expected format of the date in the metadata. If the format does
    not match, the date cannot be parsed, and cannot be formatted
    according to <code>date_format</code>. Comma-separated values can
    be provided in order to test several input formats.

    Parameter <code>source_fields</code> defined the list of MARC
    fields where we would like to retrieve the date. First one
    matching <code>source_formats</code> is used. if none, fall back to
    first non-empty one.

    Parameter <code>guess_source_formats</code> when set to 'yes'
    allows to guess the date source format.


    @see: pagination.py, publisher.py, reprints.py, imprint.py, place.py
    @param date_format: output date format.
    @param source_formats: expected (comma-separated values) input date format.
    @param source_fields: the MARC fields (comma-separated values) to look up
                   for the date. First non-empty one is used.
    @param guess_source_format: if 'yes', ignore 'source_format' and
                                try to guess format using Python mxDateTime module.
    #param ignore_date_format_for_year_only: if 'yes', ignore 'date_format' when the
                                             metadata in the record contains a single
                                             year (4 digits).
    """

    date = date_element(bfo, date_format, source_formats, source_fields, guess_source_format, ignore_date_format_for_year_only)
    pagination = bfo.field('300__a')

    return " - ".join(filter(None, [date, pagination]))
