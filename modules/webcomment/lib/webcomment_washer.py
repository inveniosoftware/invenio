from invenio.htmlutils import HTMLWasher
import htmlentitydefs

class EmailWasher(HTMLWasher):
    """
    Wash comments before being send by email
    """

    def handle_starttag(self, tag, attrs):
        """Function called for new opening tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() == 'ol':
                # we need a list to store the last
                # number used  in the previous ordered lists
                self.previous_nbs.append(self.nb)
                self.nb = 0
                # we need to know which is the tag list
                self.previous_type_lists.append(tag.lower())
            elif tag.lower() == 'ul':
                self.previous_type_lists.append(tag.lower())
            elif tag.lower() == 'li':
                if self.previous_type_lists[-1] == 'ol':
                    self.nb += 1
                    self.result += str(self.nb) + '. '
                else:
                    self.result += '* '
            elif tag.lower() == 'a':
                self.previous_type_lists.append(tag.lower())
                for (attr, value) in attrs:
                    if attr.lower() == 'href':
                        self.url = value
                        self.result += '<' + value + '>'

    def handle_endtag(self, tag):
        """Function called for ending of tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() in ['ul', 'ol']:
                self.previous_type_lists = self.previous_type_lists[:-1]
                if tag.lower() == 'ol':
                    self.nb = self.previous_nbs[-1]
                    self.previous_nbs = self.previous_nbs[:-1]

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
