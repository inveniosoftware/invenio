# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints authors
"""
__revision__ = "$Id$"

def format(bfo, limit, separator=' ; ', extension='[...]', print_links="yes", interactive="no", highlight="no"):
    """
    Prints the list of authors of a record.
    
    @param limit the maximum number of authors to display
    @param separator the separator between authors.
    @param extension a text printed if more authors than 'limit' exist
    @param print_links if yes, prints the authors as HTML link to their publications
    @param interactive if yes, enable user to show/hide authors when there are too many (html + javascript)
    @param highlight highlights authors corresponding to search query if set to 'yes'
    """
    from urllib import quote
    from cgi import escape
    from invenio.config import weburl
    from invenio.messages import gettext_set_language
    
    _ = gettext_set_language(bfo.lang)    # load the right message language
    
    authors = []
    authors_1 = bfo.fields('100__a')
    authors_2 = bfo.fields('700__a')
    
    authors.extend(authors_1)
    authors.extend(authors_2)
    
    nb_authors = len(authors)

    if highlight == 'yes':
        from invenio import bibformat_utils
        authors = [bibformat_utils.highlight(x, bfo.search_pattern) for x in authors]

    if print_links.lower() == "yes":
        authors = map(lambda x: '<a href="'+weburl+'/search?f=author&amp;p='+ quote(x) +'">'+escape(x)+'</a>', authors)

    if limit.isdigit() and  nb_authors > int(limit) and interactive != "yes":
        return separator.join(authors[:int(limit)]) + extension

    elif limit.isdigit() and nb_authors > int(limit) and interactive == "yes":
        out = '''
        <script>
        function toggle_authors_visibility(){
            var more = document.getElementById('more');
            var link = document.getElementById('link');
            var extension = document.getElementById('extension');
            if (more.style.display=='none'){
                more.style.display = '';
                extension.style.display = 'none';
                link.innerHTML = "%(show_less)s"
            } else {
                more.style.display = 'none';
                extension.style.display = '';
                link.innerHTML = "%(show_more)s"
            }
            link.style.color = "rgb(204,0,0);"
        }

        function set_up(){
            var extension = document.getElementById('extension');
            extension.innerHTML = "%(extension)s";
            toggle_authors_visibility();
        }
        
        </script>
        '''%{'show_less':_("Hide"), 'show_more':_("Show all %i authors") % nb_authors, 'extension':extension}
        out += '<a name="show_hide" />'
        out += separator.join(authors[:int(limit)])
        out += '<span id="more" style="">'+separator+separator.join(authors[int(limit):])+'</span>'
        out += ' <span id="extension"></span>'
        out += ' <small><i><a id="link" href="#" onclick="toggle_authors_visibility()" style="color:rgb(204,0,0);"></a></i></small>'
        out += '<script>set_up()</script>'
        return out
    elif nb_authors > 0:
        return separator.join(authors)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
