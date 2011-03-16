from invenio.htmlutils import HTMLWasher
import htmlentitydefs

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

    def handle_charref(self, name):
        """Process character references of the form "&#ref;". Transform to text whenever possible."""
        try:
            self.result += unichr(int(name)).encode("utf-8")
        except:
            return

    def handle_entityref(self, name):
        """Process a general entity reference of the form "&name;".
        Transform to text whenever possible."""
        char_code = htmlentitydefs.name2codepoint.get(name, None)
        if char_code is not None:
            try:
                self.result += unichr(char_code).encode("utf-8")
            except:
                return
