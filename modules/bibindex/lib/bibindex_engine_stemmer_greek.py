# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import re

class greek_stemmer:
    """docstring"""

    def __init__(self):
        """docstring"""

        self.step1list = {}
        self.step1list['ΦΑΓΙΑ'] = 'ΦΑ'
        self.step1list['ΦΑΓΙΟΥ'] = 'ΦΑ'
        self.step1list['ΦΑΓΙΩΝ'] = 'ΦΑ'
        self.step1list['ΣΚΑΓΙΑ'] = 'ΣΚΑ'
        self.step1list['ΣΚΑΓΙΟΥ'] = 'ΣΚΑ'
        self.step1list['ΣΚΑΓΙΩΝ'] = 'ΣΚΑ'
        self.step1list['ΟΛΟΓΙΟΥ'] = 'ΟΛΟ'
        self.step1list['ΟΛΟΓΙΑ'] = 'ΟΛΟ'
        self.step1list['ΟΛΟΓΙΩΝ'] = 'ΟΛΟ'
        self.step1list['ΣΟΓΙΟΥ'] = 'ΣΟ'
        self.step1list['ΣΟΓΙΑ'] = 'ΣΟ'
        self.step1list['ΣΟΓΙΩΝ'] = 'ΣΟ'
        self.step1list['ΤΑΤΟΓΙΑ'] = 'ΤΑΤΟ'
        self.step1list['ΤΑΤΟΓΙΟΥ'] = 'ΤΑΤΟ'
        self.step1list['ΤΑΤΟΓΙΩΝ'] = 'ΤΑΤΟ'
        self.step1list['ΚΡΕΑΣ'] = 'ΚΡΕ'
        self.step1list['ΚΡΕΑΤΟΣ'] = 'ΚΡΕ'
        self.step1list['ΚΡΕΑΤΑ'] = 'ΚΡΕ'
        self.step1list['ΚΡΕΑΤΩΝ'] = 'ΚΡΕ'
        self.step1list['ΠΕΡΑΣ'] = 'ΠΕΡ'
        self.step1list['ΠΕΡΑΤΟΣ'] = 'ΠΕΡ'
        self.step1list['ΠΕΡΑΤΑ'] = 'ΠΕΡ'
        self.step1list['ΠΕΡΑΤΩΝ'] = 'ΠΕΡ'
        self.step1list['ΤΕΡΑΣ'] = 'ΤΕΡ'
        self.step1list['ΤΕΡΑΤΟΣ'] = 'ΤΕΡ'
        self.step1list['ΤΕΡΑΤΑ'] = 'ΤΕΡ'
        self.step1list['ΤΕΡΑΤΩΝ'] = 'ΤΕΡ'
        self.step1list['ΦΩΣ'] = 'ΦΩ'
        self.step1list['ΦΩΤΟΣ'] = 'ΦΩ'
        self.step1list['ΦΩΤΑ'] = 'ΦΩ'
        self.step1list['ΦΩΤΩΝ'] = 'ΦΩ'
        self.step1list['ΚΑΘΕΣΤΩΣ'] = 'ΚΑΘΕΣΤ'
        self.step1list['ΚΑΘΕΣΤΩΤΟΣ'] = 'ΚΑΘΕΣΤ'
        self.step1list['ΚΑΘΕΣΤΩΤΑ'] = 'ΚΑΘΕΣΤ'
        self.step1list['ΚΑΘΕΣΤΩΤΩΝ'] = 'ΚΑΘΕΣΤ'
        self.step1list['ΓΕΓΟΝΟΣ'] = 'ΓΕΓΟΝ'
        self.step1list['ΓΕΓΟΝΟΤΟΣ'] = 'ΓΕΓΟΝ'
        self.step1list['ΓΕΓΟΝΟΤΑ'] = 'ΓΕΓΟΝ'
        self.step1list['ΓΕΓΟΝΟΤΩΝ'] = 'ΓΕΓΟΝ'

        self.step1regexp = '(.*)(' + '|'.join(self.step1list.keys()) + ')$'

        self.v = '[ΑΕΗΙΟΥΩ]'
        self.v2 = '[ΑΕΗΙΟΩ]'

    def stem_word(self, w):
        """docstring"""

        test1 = True

        if len(w) < 4:
            return w

        # STEP 1
        fp = re.match(self.step1regexp, w)
        if fp:
            stem = fp.group(1)
            suffix = fp.group(2)
            w = stem + self.step1list[suffix]
            test1 = False

        # STEP 2A
        pat = '^(.+?)(ΑΔΕΣ|ΑΔΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            pat = '(ΟΚ|ΜΑΜ|ΜΑΝ|ΜΠΑΜΠ|ΠΑΤΕΡ|ΓΙΑΓΙ|ΝΤΑΝΤ|ΚΥΡ|ΘΕΙ|ΠΕΘΕΡ)$'
            if not re.match(pat, w):
                w = w + 'ΑΔ'

        # STEP 2B
        pat = '^(.+?)(ΕΔΕΣ|ΕΔΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            expat = '(ΟΠ|ΙΠ|ΕΜΠ|ΥΠ|ΓΗΠ|ΔΑΠ|ΚΡΑΣΠ|ΜΙΛ)$'
            if re.match(expat, w):
                w = w + 'ΕΔ'

        # STEP 2C
        pat = '^(.+?)(ΟΥΔΕΣ|ΟΥΔΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            expat = '(ΑΡΚ|ΚΑΛΙΑΚ|ΠΕΤΑΛ|ΛΙΧ|ΠΛΕΞ|ΣΚ|Σ|ΦΛ|ΦΡ|ΒΕΛ|ΛΟΥΛ|ΧΝ|ΣΠ|ΤΡΑΓ|ΦΕ)$'
            if re.match(expat, w):
                w = w + 'ΟΥΔ'

        # STEP 2D
        pat = '^(.+?)(ΕΩΣ|ΕΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(Θ|Δ|ΕΛ|ΓΑΛ|Ν|Π|ΙΔ|ΠΑΡ)$'
            if re.match(expat, w):
                w = w + 'Ε'

        # STEP 3
        pat = '^(.+?)(ΙΑ|ΙΟΥ|ΙΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat = self.v + '$'
            if re.match(pat, w):
                w = w + 'Ι'

        # STEP 4
        pat = '^(.+?)(ΙΚΑ|ΙΚΟ|ΙΚΟΥ|ΙΚΩΝ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat = self.v + '$'
            expat = '^(ΑΛ|ΑΔ|ΕΝΔ|ΑΜΑΝ|ΑΜΜΟΧΑΛ|ΗΘ|ΑΝΗΘ|ΑΝΤΙΔ|ΦΥΣ|ΒΡΩΜ|ΓΕΡ|ΕΞΩΔ|ΚΑΛΠ|ΚΑΛΛΙΝ|ΚΑΤΑΔ|ΜΟΥΛ|ΜΠΑΝ|ΜΠΑΓΙΑΤ|ΜΠΟΛ|ΜΠΟΣ|ΝΙΤ|ΞΙΚ|ΣΥΝΟΜΗΛ|ΠΕΤΣ|ΠΙΤΣ|ΠΙΚΑΝΤ|ΠΛΙΑΤΣ|ΠΟΣΤΕΛΝ|ΠΡΩΤΟΔ|ΣΕΡΤ|ΣΥΝΑΔ|ΤΣΑΜ|ΥΠΟΔ|ΦΙΛΟΝ|ΦΥΛΟΔ|ΧΑΣ)$'
            if ( re.match(pat, w) or re.match(expat, w) ):
                w = w + 'ΙΚ'

        # STEP 5A
        pat1 = '^(.+?)(ΑΜΕ)$'
        pat2 = '^(.+?)(ΑΓΑΜΕ|ΗΣΑΜΕ|ΟΥΣΑΜΕ|ΗΚΑΜΕ|ΗΘΗΚΑΜΕ)$'
        if w == 'ΑΓΑΜΕ':
            w = 'ΑΓΑΜ'
        fp = re.match(pat2, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(ΑΝΑΠ|ΑΠΟΘ|ΑΠΟΚ|ΑΠΟΣΤ|ΒΟΥΒ|ΞΕΘ|ΟΥΛ|ΠΕΘ|ΠΙΚΡ|ΠΟΤ|ΣΙΧ|Χ)$'
            if re.match(expat, w):
                w = w + 'ΑΜ'

        # STEP 5B
        pat1 = '^(.+?)(ΑΝΕ)$'
        pat2 = '^(.+?)(ΑΓΑΝΕ|ΗΣΑΝΕ|ΟΥΣΑΝΕ|ΙΟΝΤΑΝΕ|ΙΟΤΑΝΕ|ΙΟΥΝΤΑΝΕ|ΟΝΤΑΝΕ|ΟΤΑΝΕ|ΟΥΝΤΑΝΕ|ΗΚΑΝΕ|ΗΘΗΚΑΝΕ)$'
        fp = re.match(pat2, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat4 = '^(ΤΡ|ΤΣ)$'
            if re.match(pat4, w):
                w = w + 'ΑΓΑΝ'
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat3 = self.v2 + '$'
            expat = '^(ΒΕΤΕΡ|ΒΟΥΛΚ|ΒΡΑΧΜ|Γ|ΔΡΑΔΟΥΜ|Θ|ΚΑΛΠΟΥΖ|ΚΑΣΤΕΛ|ΚΟΡΜΟΡ|ΛΑΟΠΛ|ΜΩΑΜΕΘ|Μ|ΜΟΥΣΟΥΛΜ|Ν|ΟΥΛ|Π|ΠΕΛΕΚ|ΠΛ|ΠΟΛΙΣ|ΠΟΡΤΟΛ|ΣΑΡΑΚΑΤΣ|ΣΟΥΛΤ|ΤΣΑΡΛΑΤ|ΟΡΦ|ΤΣΙΓΓ|ΤΣΟΠ|ΦΩΤΟΣΤΕΦ|Χ|ΨΥΧΟΠΛ|ΑΓ|ΟΡΦ|ΓΑΛ|ΓΕΡ|ΔΕΚ|ΔΙΠΛ|ΑΜΕΡΙΚΑΝ|ΟΥΡ|ΠΙΘ|ΠΟΥΡΙΤ|Σ|ΖΩΝΤ|ΙΚ|ΚΑΣΤ|ΚΟΠ|ΛΙΧ|ΛΟΥΘΗΡ|ΜΑΙΝΤ|ΜΕΛ|ΣΙΓ|ΣΠ|ΣΤΕΓ|ΤΡΑΓ|ΤΣΑΓ|Φ|ΕΡ|ΑΔΑΠ|ΑΘΙΓΓ|ΑΜΗΧ|ΑΝΙΚ|ΑΝΟΡΓ|ΑΠΗΓ|ΑΠΙΘ|ΑΤΣΙΓΓ|ΒΑΣ|ΒΑΣΚ|ΒΑΘΥΓΑΛ|ΒΙΟΜΗΧ|ΒΡΑΧΥΚ|ΔΙΑΤ|ΔΙΑΦ|ΕΝΟΡΓ|ΘΥΣ|ΚΑΠΝΟΒΙΟΜΗΧ|ΚΑΤΑΓΑΛ|ΚΛΙΒ|ΚΟΙΛΑΡΦ|ΛΙΒ|ΜΕΓΛΟΒΙΟΜΗΧ|ΜΙΚΡΟΒΙΟΜΗΧ|ΝΤΑΒ|ΞΗΡΟΚΛΙΒ|ΟΛΙΓΟΔΑΜ|ΟΛΟΓΑΛ|ΠΕΝΤΑΡΦ|ΠΕΡΗΦ|ΠΕΡΙΤΡ|ΠΛΑΤ|ΠΟΛΥΔΑΠ|ΠΟΛΥΜΗΧ|ΣΤΕΦ|ΤΑΒ|ΤΕΤ|ΥΠΕΡΗΦ|ΥΠΟΚΟΠ|ΧΑΜΗΛΟΔΑΠ|ΨΗΛΟΤΑΒ)$'
            if ( re.match(pat3, w) or re.match(expat, w) ):
                w = w + 'ΑΝ'

        # STEP 5C
        pat1 = '^(.+?)(ΕΤΕ)$'
        pat2 = '^(.+?)(ΗΣΕΤΕ)$'
        fp = re.match(pat2, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat3 = self.v2 + '$'
            expat1 = '(ΟΔ|ΑΙΡ|ΦΟΡ|ΤΑΘ|ΔΙΑΘ|ΣΧ|ΕΝΔ|ΕΥΡ|ΤΙΘ|ΥΠΕΡΘ|ΡΑΘ|ΕΝΘ|ΡΟΘ|ΣΘ|ΠΥΡ|ΑΙΝ|ΣΥΝΔ|ΣΥΝ|ΣΥΝΘ|ΧΩΡ|ΠΟΝ|ΒΡ|ΚΑΘ|ΕΥΘ|ΕΚΘ|ΝΕΤ|ΡΟΝ|ΑΡΚ|ΒΑΡ|ΒΟΛ|ΩΦΕΛ)$'
            expat2 = '^(ΑΒΑΡ|ΒΕΝ|ΕΝΑΡ|ΑΒΡ|ΑΔ|ΑΘ|ΑΝ|ΑΠΛ|ΒΑΡΟΝ|ΝΤΡ|ΣΚ|ΚΟΠ|ΜΠΟΡ|ΝΙΦ|ΠΑΓ|ΠΑΡΑΚΑΛ|ΣΕΡΠ|ΣΚΕΛ|ΣΥΡΦ|ΤΟΚ|Υ|Δ|ΕΜ|ΘΑΡΡ|Θ)$'
            if ( re.match(pat3, w) or re.match(expat1, w) or re.match(expat2, w) ):
                w = w + 'ΕΤ'

        # STEP 5D
        pat = '^(.+?)(ΟΝΤΑΣ|ΩΝΤΑΣ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat1 = '^(ΑΡΧ)$'
            expat2 = '(ΚΡΕ)$'
            if re.match(expat1, w):
                w = w + 'ΟΝΤ'
            if re.match(expat2, w):
                w = w + 'ΩΝΤ'

        # STEP 5E
        pat = '^(.+?)(ΟΜΑΣΤΕ|ΙΟΜΑΣΤΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(ΟΝ)$'
            if re.match(expat, w):
                w = w + 'ΟΜΑΣΤ'

        # STEP 5F
        pat1 = '^(.+?)(ΕΣΤΕ)$'
        pat2 = '^(.+?)(ΙΕΣΤΕ)$'
        fp = re.match(pat2, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            pat3 = '^(Π|ΑΠ|ΣΥΜΠ|ΑΣΥΜΠ|ΑΚΑΤΑΠ|ΑΜΕΤΑΜΦ)$'
            if re.match(pat3, w):
                w = w + 'ΙΕΣΤ'
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(ΑΛ|ΑΡ|ΕΚΤΕΛ|Ζ|Μ|Ξ|ΠΑΡΑΚΑΛ|ΑΡ|ΠΡΟ|ΝΙΣ)$'
            if re.match(expat, w):
                w = w + 'ΕΣΤ'

        # STEP 5G
        pat1 = '^(.+?)(ΗΚΑ|ΗΚΕΣ|ΗΚΕ)$'
        pat2 = '^(.+?)(ΗΘΗΚΑ|ΗΘΗΚΕΣ|ΗΘΗΚΕ)$'
        fp = re.match(pat2, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat1 = '(ΣΚΩΛ|ΣΚΟΥΛ|ΝΑΡΘ|ΣΦ|ΟΘ|ΠΙΘ)$'
            expat2 = '^(ΔΙΑΘ|Θ|ΠΑΡΑΚΑΤΑΘ|ΠΡΟΣΘ|ΣΥΝΘ|)$'
            if ( re.match(expat1, w) or re.match(expat2, w) ):
                w = w + 'ΗΚ'

        # STEP 5H
        pat = '^(.+?)(ΟΥΣΑ|ΟΥΣΕΣ|ΟΥΣΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat1 = '^(ΦΑΡΜΑΚ|ΧΑΔ|ΑΓΚ|ΑΝΑΡΡ|ΒΡΟΜ|ΕΚΛΙΠ|ΛΑΜΠΙΔ|ΛΕΧ|Μ|ΠΑΤ|Ρ|Λ|ΜΕΔ|ΜΕΣΑΖ|ΥΠΟΤΕΙΝ|ΑΜ|ΑΙΘ|ΑΝΗΚ|ΔΕΣΠΟΖ|ΕΝΔΙΑΦΕΡ|ΔΕ|ΔΕΥΤΕΡΕΥ|ΚΑΘΑΡΕΥ|ΠΛΕ|ΤΣΑ)$'
            expat2 = '(ΠΟΔΑΡ|ΒΛΕΠ|ΠΑΝΤΑΧ|ΦΡΥΔ|ΜΑΝΤΙΛ|ΜΑΛΛ|ΚΥΜΑΤ|ΛΑΧ|ΛΗΓ|ΦΑΓ|ΟΜ|ΠΡΩΤ)$'
            if ( re.match(expat1, w) or re.match(expat2, w) ):
                w = w + 'ΟΥΣ'

        # STEP 5I
        pat = '^(.+?)(ΑΓΑ|ΑΓΕΣ|ΑΓΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat1 = '^(ΨΟΦ|ΝΑΥΛΟΧ)$'
            expat2 = '(ΚΟΛΛ)$'
            expat3 = '^(ΑΒΑΣΤ|ΠΟΛΥΦ|ΑΔΗΦ|ΠΑΜΦ|Ρ|ΑΣΠ|ΑΦ|ΑΜΑΛ|ΑΜΑΛΛΙ|ΑΝΥΣΤ|ΑΠΕΡ|ΑΣΠΑΡ|ΑΧΑΡ|ΔΕΡΒΕΝ|ΔΡΟΣΟΠ|ΞΕΦ|ΝΕΟΠ|ΝΟΜΟΤ|ΟΛΟΠ|ΟΜΟΤ|ΠΡΟΣΤ|ΠΡΟΣΩΠΟΠ|ΣΥΜΠ|ΣΥΝΤ|Τ|ΥΠΟΤ|ΧΑΡ|ΑΕΙΠ|ΑΙΜΟΣΤ|ΑΝΥΠ|ΑΠΟΤ|ΑΡΤΙΠ|ΔΙΑΤ|ΕΝ|ΕΠΙΤ|ΚΡΟΚΑΛΟΠ|ΣΙΔΗΡΟΠ|Λ|ΝΑΥ|ΟΥΛΑΜ|ΟΥΡ|Π|ΤΡ|Μ)$'
            expat4 = '(ΟΦ|ΠΕΛ|ΧΟΡΤ|ΛΛ|ΣΦ|ΡΠ|ΦΡ|ΠΡ|ΛΟΧ|ΣΜΗΝ)$'
            if ( ( re.match(expat3, w) or re.match(expat4, w) ) and not ( re.match(expat1, w) or re.match(expat2, w) ) ):
                w = w + 'ΑΓ'

        # STEP 5J
        pat = '^(.+?)(ΗΣΕ|ΗΣΟΥ|ΗΣΑ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(Ν|ΧΕΡΣΟΝ|ΔΩΔΕΚΑΝ|ΕΡΗΜΟΝ|ΜΕΓΑΛΟΝ|ΕΠΤΑΝ)$'
            if re.match(expat, w):
                w = w + 'ΗΣ'

        # STEP 5K
        pat = '^(.+?)(ΗΣΤΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(ΑΣΒ|ΣΒ|ΑΧΡ|ΧΡ|ΑΠΛ|ΑΕΙΜΝ|ΔΥΣΧΡ|ΕΥΧΡ|ΚΟΙΝΟΧΡ|ΠΑΛΙΜΨ)$'
            if re.match(expat, w):
                w = w + 'ΗΣΤ'

        # STEP 5L
        pat = '^(.+?)(ΟΥΝΕ|ΗΣΟΥΝΕ|ΗΘΟΥΝΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(Ν|Ρ|ΣΠΙ|ΣΤΡΑΒΟΜΟΥΤΣ|ΚΑΚΟΜΟΥΤΣ|ΕΞΩΝ)$'
            if re.match(expat, w):
                w = w + 'ΟΥΝ'

        # STEP 5M
        pat = '^(.+?)(ΟΥΜΕ|ΗΣΟΥΜΕ|ΗΘΟΥΜΕ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            expat = '^(ΠΑΡΑΣΟΥΣ|Φ|Χ|ΩΡΙΟΠΛ|ΑΖ|ΑΛΛΟΣΟΥΣ|ΑΣΟΥΣ)$'
            if re.match(expat, w):
                w = w + 'ΟΥΜ'

        # STEP 6
        pat1 = '^(.+?)(ΜΑΤΑ|ΜΑΤΩΝ|ΜΑΤΟΣ)$'
        pat2 = '^(.+?)(Α|ΑΓΑΤΕ|ΑΓΑΝ|ΑΕΙ|ΑΜΑΙ|ΑΝ|ΑΣ|ΑΣΑΙ|ΑΤΑΙ|ΑΩ|Ε|ΕΙ|ΕΙΣ|ΕΙΤΕ|ΕΣΑΙ|ΕΣ|ΕΤΑΙ|Ι|ΙΕΜΑΙ|ΙΕΜΑΣΤΕ|ΙΕΤΑΙ|ΙΕΣΑΙ|ΙΕΣΑΣΤΕ|ΙΟΜΑΣΤΑΝ|ΙΟΜΟΥΝ|ΙΟΜΟΥΝΑ|ΙΟΝΤΑΝ|ΙΟΝΤΟΥΣΑΝ|ΙΟΣΑΣΤΑΝ|ΙΟΣΑΣΤΕ|ΙΟΣΟΥΝ|ΙΟΣΟΥΝΑ|ΙΟΤΑΝ|ΙΟΥΜΑ|ΙΟΥΜΑΣΤΕ|ΙΟΥΝΤΑΙ|ΙΟΥΝΤΑΝ|Η|ΗΔΕΣ|ΗΔΩΝ|ΗΘΕΙ|ΗΘΕΙΣ|ΗΘΕΙΤΕ|ΗΘΗΚΑΤΕ|ΗΘΗΚΑΝ|ΗΘΟΥΝ|ΗΘΩ|ΗΚΑΤΕ|ΗΚΑΝ|ΗΣ|ΗΣΑΝ|ΗΣΑΤΕ|ΗΣΕΙ|ΗΣΕΣ|ΗΣΟΥΝ|ΗΣΩ|Ο|ΟΙ|ΟΜΑΙ|ΟΜΑΣΤΑΝ|ΟΜΟΥΝ|ΟΜΟΥΝΑ|ΟΝΤΑΙ|ΟΝΤΑΝ|ΟΝΤΟΥΣΑΝ|ΟΣ|ΟΣΑΣΤΑΝ|ΟΣΑΣΤΕ|ΟΣΟΥΝ|ΟΣΟΥΝΑ|ΟΤΑΝ|ΟΥ|ΟΥΜΑΙ|ΟΥΜΑΣΤΕ|ΟΥΝ|ΟΥΝΤΑΙ|ΟΥΝΤΑΝ|ΟΥΣ|ΟΥΣΑΝ|ΟΥΣΑΤΕ|Υ|ΥΣ|Ω|ΩΝ)$'
        fp = re.match(pat1, w)
        if fp:
            stem = fp.group(1)
            w = stem + 'ΜΑ'
        fp = re.match(pat2, w)
        if fp and test1:
            stem = fp.group(1)
            w = stem

        # STEP 7
        pat = '^(.+?)(ΕΣΤΕΡ|ΕΣΤΑΤ|ΟΤΕΡ|ΟΤΑΤ|ΥΤΕΡ|ΥΤΑΤ|ΩΤΕΡ|ΩΤΑΤ)$'
        fp = re.match(pat, w)
        if fp:
            stem = fp.group(1)
            w = stem

        return w
