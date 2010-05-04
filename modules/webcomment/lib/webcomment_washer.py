from invenio.htmlutils import HTMLWasher, cfg_html_buffer_allowed_tag_whitelist,\
                              cfg_html_buffer_allowed_attribute_whitelist

class EmailWasher(HTMLWasher):
    """
    Wash comments before being send by email
    """

    def handle_starttag(self, tag, attrs):
        """Function called for new opening tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() in ['ul', 'ol']:
                self.result += '\n'
            elif tag.lower() == 'li':
                self.result += '* '
            elif tag.lower() == 'a':
                for (attr, value) in attrs:
                    if attr.lower() == 'href':
                        self.result += '<' + value + '>' + '('

    def handle_endtag(self, tag):
        """Function called for ending of tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() in ['li', 'ul', 'ol']:
                self.result += '\n'
            elif tag.lower() == 'a':
                self.result += ')'

    def handle_startendtag(self, tag, attrs):
        """Function called for empty tags (e.g. <br />)"""
        self.result += ""

    def handle_entityref(self, name):
        """Process a general entity reference of the form "&name;".
        Return it as it is."""
        if name == 'nbsp':
            self.result += ' '
        else:
            self.result += '&' + name + ';'
