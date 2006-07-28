def format(bfo, separator='<br/>'):
    """
    Prints list of links to external publications.
    """
    publications = bfo.fields('909C4')
    out = map(lambda x: '<a href="'+x['d']+'">'+x['p']+'</a>', publications)

    return separator.join(out)
