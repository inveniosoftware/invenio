# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2014 CERN.
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

_LIST_STEP1 = {}
_LIST_STEP1['ΦΑΓΙΑ'] = 'ΦΑ'
_LIST_STEP1['ΦΑΓΙΟΥ'] = 'ΦΑ'
_LIST_STEP1['ΦΑΓΙΩΝ'] = 'ΦΑ'
_LIST_STEP1['ΣΚΑΓΙΑ'] = 'ΣΚΑ'
_LIST_STEP1['ΣΚΑΓΙΟΥ'] = 'ΣΚΑ'
_LIST_STEP1['ΣΚΑΓΙΩΝ'] = 'ΣΚΑ'
_LIST_STEP1['ΟΛΟΓΙΟΥ'] = 'ΟΛΟ'
_LIST_STEP1['ΟΛΟΓΙΑ'] = 'ΟΛΟ'
_LIST_STEP1['ΟΛΟΓΙΩΝ'] = 'ΟΛΟ'
_LIST_STEP1['ΣΟΓΙΟΥ'] = 'ΣΟ'
_LIST_STEP1['ΣΟΓΙΑ'] = 'ΣΟ'
_LIST_STEP1['ΣΟΓΙΩΝ'] = 'ΣΟ'
_LIST_STEP1['ΤΑΤΟΓΙΑ'] = 'ΤΑΤΟ'
_LIST_STEP1['ΤΑΤΟΓΙΟΥ'] = 'ΤΑΤΟ'
_LIST_STEP1['ΤΑΤΟΓΙΩΝ'] = 'ΤΑΤΟ'
_LIST_STEP1['ΚΡΕΑΣ'] = 'ΚΡΕ'
_LIST_STEP1['ΚΡΕΑΤΟΣ'] = 'ΚΡΕ'
_LIST_STEP1['ΚΡΕΑΤΑ'] = 'ΚΡΕ'
_LIST_STEP1['ΚΡΕΑΤΩΝ'] = 'ΚΡΕ'
_LIST_STEP1['ΠΕΡΑΣ'] = 'ΠΕΡ'
_LIST_STEP1['ΠΕΡΑΤΟΣ'] = 'ΠΕΡ'
_LIST_STEP1['ΠΕΡΑΤΑ'] = 'ΠΕΡ'
_LIST_STEP1['ΠΕΡΑΤΩΝ'] = 'ΠΕΡ'
_LIST_STEP1['ΤΕΡΑΣ'] = 'ΤΕΡ'
_LIST_STEP1['ΤΕΡΑΤΟΣ'] = 'ΤΕΡ'
_LIST_STEP1['ΤΕΡΑΤΑ'] = 'ΤΕΡ'
_LIST_STEP1['ΤΕΡΑΤΩΝ'] = 'ΤΕΡ'
_LIST_STEP1['ΦΩΣ'] = 'ΦΩ'
_LIST_STEP1['ΦΩΤΟΣ'] = 'ΦΩ'
_LIST_STEP1['ΦΩΤΑ'] = 'ΦΩ'
_LIST_STEP1['ΦΩΤΩΝ'] = 'ΦΩ'
_LIST_STEP1['ΚΑΘΕΣΤΩΣ'] = 'ΚΑΘΕΣΤ'
_LIST_STEP1['ΚΑΘΕΣΤΩΤΟΣ'] = 'ΚΑΘΕΣΤ'
_LIST_STEP1['ΚΑΘΕΣΤΩΤΑ'] = 'ΚΑΘΕΣΤ'
_LIST_STEP1['ΚΑΘΕΣΤΩΤΩΝ'] = 'ΚΑΘΕΣΤ'
_LIST_STEP1['ΓΕΓΟΝΟΣ'] = 'ΓΕΓΟΝ'
_LIST_STEP1['ΓΕΓΟΝΟΤΟΣ'] = 'ΓΕΓΟΝ'
_LIST_STEP1['ΓΕΓΟΝΟΤΑ'] = 'ΓΕΓΟΝ'
_LIST_STEP1['ΓΕΓΟΝΟΤΩΝ'] = 'ΓΕΓΟΝ'

_V = '[ΑΕΗΙΟΥΩ]'
_V2 = '[ΑΕΗΙΟΩ]'

_RE_STEP1PAT = re.compile('(.*)(' + '|'.join(_LIST_STEP1.keys()) + ')$')
_RE_STEP2APAT1 = re.compile('^(.+?)(ΑΔΕΣ|ΑΔΩΝ)$')
_RE_STEP2APAT2 = re.compile(
    '(ΟΚ|ΜΑΜ|ΜΑΝ|ΜΠΑΜΠ|ΠΑΤΕΡ|ΓΙΑΓΙ|ΝΤΑΝΤ|ΚΥΡ|ΘΕΙ|ΠΕΘΕΡ)$')
_RE_STEP2BPAT = re.compile('^(.+?)(ΕΔΕΣ|ΕΔΩΝ)$')
_RE_STEP2BEXPAT = re.compile('(ΟΠ|ΙΠ|ΕΜΠ|ΥΠ|ΓΗΠ|ΔΑΠ|ΚΡΑΣΠ|ΜΙΛ)$')
_RE_STEP2CPAT = re.compile('^(.+?)(ΟΥΔΕΣ|ΟΥΔΩΝ)$')
_RE_STEP2CEXPAT = re.compile(
    '(ΑΡΚ|ΚΑΛΙΑΚ|ΠΕΤΑΛ|ΛΙΧ|ΠΛΕΞ|ΣΚ|Σ|ΦΛ|ΦΡ|ΒΕΛ|ΛΟΥΛ|ΧΝ|ΣΠ|ΤΡΑΓ|ΦΕ)$')
_RE_STEP2DPAT = re.compile('^(.+?)(ΕΩΣ|ΕΩΝ)$')
_RE_STEP2DEXPAT = re.compile('^(Θ|Δ|ΕΛ|ΓΑΛ|Ν|Π|ΙΔ|ΠΑΡ)$')
_RE_STEP3PAT1 = re.compile('^(.+?)(ΙΑ|ΙΟΥ|ΙΩΝ)$')
_RE_STEP3PAT2 = re.compile(_V + '$')
_RE_STEP4PAT1 = re.compile('^(.+?)(ΙΚΑ|ΙΚΟ|ΙΚΟΥ|ΙΚΩΝ)$')
_RE_STEP4PAT2 = re.compile(_V + '$')
_RE_STEP4EXPAT = re.compile(
    '^(ΑΛ|ΑΔ|ΕΝΔ|ΑΜΑΝ|ΑΜΜΟΧΑΛ|ΗΘ|ΑΝΗΘ|ΑΝΤΙΔ|ΦΥΣ|ΒΡΩΜ|ΓΕΡ|ΕΞΩΔ|ΚΑΛΠ|ΚΑΛΛΙΝ|ΚΑΤΑΔ|ΜΟΥΛ|ΜΠΑΝ|ΜΠΑΓΙΑΤ|ΜΠΟΛ|ΜΠΟΣ|ΝΙΤ|ΞΙΚ|ΣΥΝΟΜΗΛ|ΠΕΤΣ|ΠΙΤΣ|ΠΙΚΑΝΤ|ΠΛΙΑΤΣ|ΠΟΣΤΕΛΝ|ΠΡΩΤΟΔ|ΣΕΡΤ|ΣΥΝΑΔ|ΤΣΑΜ|ΥΠΟΔ|ΦΙΛΟΝ|ΦΥΛΟΔ|ΧΑΣ)$')
_RE_STEP5APAT1 = re.compile('^(.+?)(ΑΜΕ)$')
_RE_STEP5APAT2 = re.compile('^(.+?)(ΑΓΑΜΕ|ΗΣΑΜΕ|ΟΥΣΑΜΕ|ΗΚΑΜΕ|ΗΘΗΚΑΜΕ)$')
_RE_STEP5AEXPAT = re.compile(
    '^(ΑΝΑΠ|ΑΠΟΘ|ΑΠΟΚ|ΑΠΟΣΤ|ΒΟΥΒ|ΞΕΘ|ΟΥΛ|ΠΕΘ|ΠΙΚΡ|ΠΟΤ|ΣΙΧ|Χ)$')
_RE_STEP5BPAT1 = re.compile('^(.+?)(ΑΝΕ)$')
_RE_STEP5BPAT2 = re.compile(
    '^(.+?)(ΑΓΑΝΕ|ΗΣΑΝΕ|ΟΥΣΑΝΕ|ΙΟΝΤΑΝΕ|ΙΟΤΑΝΕ|ΙΟΥΝΤΑΝΕ|ΟΝΤΑΝΕ|ΟΤΑΝΕ|ΟΥΝΤΑΝΕ|ΗΚΑΝΕ|ΗΘΗΚΑΝΕ)$')
_RE_STEP5BPAT4 = re.compile('^(ΤΡ|ΤΣ)$')
_RE_STEP5BPAT3 = re.compile(_V2 + '$')
_RE_STEP5BEXPAT = re.compile(
    '^(ΒΕΤΕΡ|ΒΟΥΛΚ|ΒΡΑΧΜ|Γ|ΔΡΑΔΟΥΜ|Θ|ΚΑΛΠΟΥΖ|ΚΑΣΤΕΛ|ΚΟΡΜΟΡ|ΛΑΟΠΛ|ΜΩΑΜΕΘ|Μ|ΜΟΥΣΟΥΛΜ|Ν|ΟΥΛ|Π|ΠΕΛΕΚ|ΠΛ|ΠΟΛΙΣ|ΠΟΡΤΟΛ|ΣΑΡΑΚΑΤΣ|ΣΟΥΛΤ|ΤΣΑΡΛΑΤ|ΟΡΦ|ΤΣΙΓΓ|ΤΣΟΠ|ΦΩΤΟΣΤΕΦ|Χ|ΨΥΧΟΠΛ|ΑΓ|ΟΡΦ|ΓΑΛ|ΓΕΡ|ΔΕΚ|ΔΙΠΛ|ΑΜΕΡΙΚΑΝ|ΟΥΡ|ΠΙΘ|ΠΟΥΡΙΤ|Σ|ΖΩΝΤ|ΙΚ|ΚΑΣΤ|ΚΟΠ|ΛΙΧ|ΛΟΥΘΗΡ|ΜΑΙΝΤ|ΜΕΛ|ΣΙΓ|ΣΠ|ΣΤΕΓ|ΤΡΑΓ|ΤΣΑΓ|Φ|ΕΡ|ΑΔΑΠ|ΑΘΙΓΓ|ΑΜΗΧ|ΑΝΙΚ|ΑΝΟΡΓ|ΑΠΗΓ|ΑΠΙΘ|ΑΤΣΙΓΓ|ΒΑΣ|ΒΑΣΚ|ΒΑΘΥΓΑΛ|ΒΙΟΜΗΧ|ΒΡΑΧΥΚ|ΔΙΑΤ|ΔΙΑΦ|ΕΝΟΡΓ|ΘΥΣ|ΚΑΠΝΟΒΙΟΜΗΧ|ΚΑΤΑΓΑΛ|ΚΛΙΒ|ΚΟΙΛΑΡΦ|ΛΙΒ|ΜΕΓΛΟΒΙΟΜΗΧ|ΜΙΚΡΟΒΙΟΜΗΧ|ΝΤΑΒ|ΞΗΡΟΚΛΙΒ|ΟΛΙΓΟΔΑΜ|ΟΛΟΓΑΛ|ΠΕΝΤΑΡΦ|ΠΕΡΗΦ|ΠΕΡΙΤΡ|ΠΛΑΤ|ΠΟΛΥΔΑΠ|ΠΟΛΥΜΗΧ|ΣΤΕΦ|ΤΑΒ|ΤΕΤ|ΥΠΕΡΗΦ|ΥΠΟΚΟΠ|ΧΑΜΗΛΟΔΑΠ|ΨΗΛΟΤΑΒ)$')
_RE_STEP5CPAT1 = re.compile('^(.+?)(ΕΤΕ)$')
_RE_STEP5CPAT2 = re.compile('^(.+?)(ΗΣΕΤΕ)$')
_RE_STEP5CPAT3 = re.compile(_V2 + '$')
_RE_STEP5CEXPAT1 = re.compile(
    '(ΟΔ|ΑΙΡ|ΦΟΡ|ΤΑΘ|ΔΙΑΘ|ΣΧ|ΕΝΔ|ΕΥΡ|ΤΙΘ|ΥΠΕΡΘ|ΡΑΘ|ΕΝΘ|ΡΟΘ|ΣΘ|ΠΥΡ|ΑΙΝ|ΣΥΝΔ|ΣΥΝ|ΣΥΝΘ|ΧΩΡ|ΠΟΝ|ΒΡ|ΚΑΘ|ΕΥΘ|ΕΚΘ|ΝΕΤ|ΡΟΝ|ΑΡΚ|ΒΑΡ|ΒΟΛ|ΩΦΕΛ)$')
_RE_STEP5CEXPAT2 = re.compile(
    '^(ΑΒΑΡ|ΒΕΝ|ΕΝΑΡ|ΑΒΡ|ΑΔ|ΑΘ|ΑΝ|ΑΠΛ|ΒΑΡΟΝ|ΝΤΡ|ΣΚ|ΚΟΠ|ΜΠΟΡ|ΝΙΦ|ΠΑΓ|ΠΑΡΑΚΑΛ|ΣΕΡΠ|ΣΚΕΛ|ΣΥΡΦ|ΤΟΚ|Υ|Δ|ΕΜ|ΘΑΡΡ|Θ)$')
_RE_STEP5DPAT = re.compile('^(.+?)(ΟΝΤΑΣ|ΩΝΤΑΣ)$')
_RE_STEP5DEXPAT1 = re.compile('^(ΑΡΧ)$')
_RE_STEP5DEXPAT2 = re.compile('(ΚΡΕ)$')
_RE_STEP5EPAT = re.compile('^(.+?)(ΟΜΑΣΤΕ|ΙΟΜΑΣΤΕ)$')
_RE_STEP5EEXPAT = re.compile('^(ΟΝ)$')
_RE_STEP5FPAT1 = re.compile('^(.+?)(ΕΣΤΕ)$')
_RE_STEP5FPAT2 = re.compile('^(.+?)(ΙΕΣΤΕ)$')
_RE_STEP5FPAT3 = re.compile('^(Π|ΑΠ|ΣΥΜΠ|ΑΣΥΜΠ|ΑΚΑΤΑΠ|ΑΜΕΤΑΜΦ)$')
_RE_STEP5FEXPAT = re.compile('^(ΑΛ|ΑΡ|ΕΚΤΕΛ|Ζ|Μ|Ξ|ΠΑΡΑΚΑΛ|ΑΡ|ΠΡΟ|ΝΙΣ)$')
_RE_STEP5GPAT1 = re.compile('^(.+?)(ΗΚΑ|ΗΚΕΣ|ΗΚΕ)$')
_RE_STEP5GPAT2 = re.compile('^(.+?)(ΗΘΗΚΑ|ΗΘΗΚΕΣ|ΗΘΗΚΕ)$')
_RE_STEP5GEXPAT1 = re.compile('(ΣΚΩΛ|ΣΚΟΥΛ|ΝΑΡΘ|ΣΦ|ΟΘ|ΠΙΘ)$')
_RE_STEP5GEXPAT2 = re.compile('^(ΔΙΑΘ|Θ|ΠΑΡΑΚΑΤΑΘ|ΠΡΟΣΘ|ΣΥΝΘ|)$')
_RE_STEP5HPAT = re.compile('^(.+?)(ΟΥΣΑ|ΟΥΣΕΣ|ΟΥΣΕ)$')
_RE_STEP5HEXPAT1 = re.compile(
    '^(ΦΑΡΜΑΚ|ΧΑΔ|ΑΓΚ|ΑΝΑΡΡ|ΒΡΟΜ|ΕΚΛΙΠ|ΛΑΜΠΙΔ|ΛΕΧ|Μ|ΠΑΤ|Ρ|Λ|ΜΕΔ|ΜΕΣΑΖ|ΥΠΟΤΕΙΝ|ΑΜ|ΑΙΘ|ΑΝΗΚ|ΔΕΣΠΟΖ|ΕΝΔΙΑΦΕΡ|ΔΕ|ΔΕΥΤΕΡΕΥ|ΚΑΘΑΡΕΥ|ΠΛΕ|ΤΣΑ)$')
_RE_STEP5HEXPAT2 = re.compile(
    '(ΠΟΔΑΡ|ΒΛΕΠ|ΠΑΝΤΑΧ|ΦΡΥΔ|ΜΑΝΤΙΛ|ΜΑΛΛ|ΚΥΜΑΤ|ΛΑΧ|ΛΗΓ|ΦΑΓ|ΟΜ|ΠΡΩΤ)$')
_RE_STEP5IPAT = re.compile('^(.+?)(ΑΓΑ|ΑΓΕΣ|ΑΓΕ)$')
_RE_STEP5IEXPAT1 = re.compile('^(ΨΟΦ|ΝΑΥΛΟΧ)$')
_RE_STEP5IEXPAT2 = re.compile('(ΚΟΛΛ)$')
_RE_STEP5IEXPAT3 = re.compile(
    '^(ΑΒΑΣΤ|ΠΟΛΥΦ|ΑΔΗΦ|ΠΑΜΦ|Ρ|ΑΣΠ|ΑΦ|ΑΜΑΛ|ΑΜΑΛΛΙ|ΑΝΥΣΤ|ΑΠΕΡ|ΑΣΠΑΡ|ΑΧΑΡ|ΔΕΡΒΕΝ|ΔΡΟΣΟΠ|ΞΕΦ|ΝΕΟΠ|ΝΟΜΟΤ|ΟΛΟΠ|ΟΜΟΤ|ΠΡΟΣΤ|ΠΡΟΣΩΠΟΠ|ΣΥΜΠ|ΣΥΝΤ|Τ|ΥΠΟΤ|ΧΑΡ|ΑΕΙΠ|ΑΙΜΟΣΤ|ΑΝΥΠ|ΑΠΟΤ|ΑΡΤΙΠ|ΔΙΑΤ|ΕΝ|ΕΠΙΤ|ΚΡΟΚΑΛΟΠ|ΣΙΔΗΡΟΠ|Λ|ΝΑΥ|ΟΥΛΑΜ|ΟΥΡ|Π|ΤΡ|Μ)$')
_RE_STEP5IEXPAT4 = re.compile('(ΟΦ|ΠΕΛ|ΧΟΡΤ|ΛΛ|ΣΦ|ΡΠ|ΦΡ|ΠΡ|ΛΟΧ|ΣΜΗΝ)$')
_RE_STEP5JPAT = re.compile('^(.+?)(ΗΣΕ|ΗΣΟΥ|ΗΣΑ)$')
_RE_STEP5JEXPAT = re.compile('^(Ν|ΧΕΡΣΟΝ|ΔΩΔΕΚΑΝ|ΕΡΗΜΟΝ|ΜΕΓΑΛΟΝ|ΕΠΤΑΝ)$')
_RE_STEP5KPAT = re.compile('^(.+?)(ΗΣΤΕ)$')
_RE_STEP5KEXPAT = re.compile(
    '^(ΑΣΒ|ΣΒ|ΑΧΡ|ΧΡ|ΑΠΛ|ΑΕΙΜΝ|ΔΥΣΧΡ|ΕΥΧΡ|ΚΟΙΝΟΧΡ|ΠΑΛΙΜΨ)$')
_RE_STEP5LPAT = re.compile('^(.+?)(ΟΥΝΕ|ΗΣΟΥΝΕ|ΗΘΟΥΝΕ)$')
_RE_STEP5LEXPAT = re.compile('^(Ν|Ρ|ΣΠΙ|ΣΤΡΑΒΟΜΟΥΤΣ|ΚΑΚΟΜΟΥΤΣ|ΕΞΩΝ)$')
_RE_STEP5MPAT = re.compile('^(.+?)(ΟΥΜΕ|ΗΣΟΥΜΕ|ΗΘΟΥΜΕ)$')
_RE_STEP5MEXPAT = re.compile('^(ΠΑΡΑΣΟΥΣ|Φ|Χ|ΩΡΙΟΠΛ|ΑΖ|ΑΛΛΟΣΟΥΣ|ΑΣΟΥΣ)$')
_RE_STEP6PAT1 = re.compile('^(.+?)(ΜΑΤΑ|ΜΑΤΩΝ|ΜΑΤΟΣ)$')
_RE_STEP6PAT2 = re.compile(
    '^(.+?)(Α|ΑΓΑΤΕ|ΑΓΑΝ|ΑΕΙ|ΑΜΑΙ|ΑΝ|ΑΣ|ΑΣΑΙ|ΑΤΑΙ|ΑΩ|Ε|ΕΙ|ΕΙΣ|ΕΙΤΕ|ΕΣΑΙ|ΕΣ|ΕΤΑΙ|Ι|ΙΕΜΑΙ|ΙΕΜΑΣΤΕ|ΙΕΤΑΙ|ΙΕΣΑΙ|ΙΕΣΑΣΤΕ|ΙΟΜΑΣΤΑΝ|ΙΟΜΟΥΝ|ΙΟΜΟΥΝΑ|ΙΟΝΤΑΝ|ΙΟΝΤΟΥΣΑΝ|ΙΟΣΑΣΤΑΝ|ΙΟΣΑΣΤΕ|ΙΟΣΟΥΝ|ΙΟΣΟΥΝΑ|ΙΟΤΑΝ|ΙΟΥΜΑ|ΙΟΥΜΑΣΤΕ|ΙΟΥΝΤΑΙ|ΙΟΥΝΤΑΝ|Η|ΗΔΕΣ|ΗΔΩΝ|ΗΘΕΙ|ΗΘΕΙΣ|ΗΘΕΙΤΕ|ΗΘΗΚΑΤΕ|ΗΘΗΚΑΝ|ΗΘΟΥΝ|ΗΘΩ|ΗΚΑΤΕ|ΗΚΑΝ|ΗΣ|ΗΣΑΝ|ΗΣΑΤΕ|ΗΣΕΙ|ΗΣΕΣ|ΗΣΟΥΝ|ΗΣΩ|Ο|ΟΙ|ΟΜΑΙ|ΟΜΑΣΤΑΝ|ΟΜΟΥΝ|ΟΜΟΥΝΑ|ΟΝΤΑΙ|ΟΝΤΑΝ|ΟΝΤΟΥΣΑΝ|ΟΣ|ΟΣΑΣΤΑΝ|ΟΣΑΣΤΕ|ΟΣΟΥΝ|ΟΣΟΥΝΑ|ΟΤΑΝ|ΟΥ|ΟΥΜΑΙ|ΟΥΜΑΣΤΕ|ΟΥΝ|ΟΥΝΤΑΙ|ΟΥΝΤΑΝ|ΟΥΣ|ΟΥΣΑΝ|ΟΥΣΑΤΕ|Υ|ΥΣ|Ω|ΩΝ)$')
_RE_STEP7PAT = re.compile('^(.+?)(ΕΣΤΕΡ|ΕΣΤΑΤ|ΟΤΕΡ|ΟΤΑΤ|ΥΤΕΡ|ΥΤΑΤ|ΩΤΕΡ|ΩΤΑΤ)$')

_ACCENTED_VOWELS = 'ΆΈΉΊΌΎΏΪΫΐάέήίόύώϊϋ'.decode('UTF-8', 'ignore')
_NON_ACCENTED_VOWELS = 'ΑΕΗΙΟΥΩΙΥιαεηιουωιυ'.decode('UTF-8', 'ignore')
_TRANSLATION_TABLE = dict((ord(i), o)
                          for i, o in zip(_ACCENTED_VOWELS, _NON_ACCENTED_VOWELS))


class GreekStemmer(object):

    """
    A python implementation of a greek stemmer. It is based on a PHP
    implementation by Panos Kyriakakis (http://www.salix.gr/greek_stemmer)
    which in turn is based on a JavaScript implementation by
    Georgios Ntais (http://people.dsv.su.se/~hercules/greek_stemmer.gr.html)
    for his master thesis "Development of a Stemmer for the Greek Language"
    (http://people.dsv.su.se/~hercules/papers/Ntais_greek_stemmer_thesis_final.pdf).
    """

    def _remove_accents_from_word(self, word):
        """
        Replaces all the accented vowels in the given word to their
        non-accented versions.
        """
        return word.translate(_TRANSLATION_TABLE)

    def _convert_word_to_uppercase(self, word):
        """
        Converts the given word to uppercase.
        """
        if not word.isupper():
            word = word.upper()
        return word

    def _prepare_word(self, word):
        """
        Prepares the word for stemming.
        """
        word = word.decode('UTF-8', 'ignore')
        word = self._remove_accents_from_word(word)
        word = self._convert_word_to_uppercase(word)
        word = word.encode('UTF-8', 'ignore')
        return word

    def stemWord(self, w):
        """
        The function to calculate the stem of a word.
        Takes a word as input and returns its stem.
        """

        test1 = True

        w = self._prepare_word(w)

        if len(w) < 4:
            return w

        # STEP 1
        fp = _RE_STEP1PAT.match(w)
        if fp:
            stem = fp.group(1)
            suffix = fp.group(2)
            w = stem + _LIST_STEP1[suffix]
            test1 = False

        # STEP 2A
        fp = _RE_STEP2APAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            if not _RE_STEP2APAT2.match(w):
                w = w + 'ΑΔ'

        # STEP 2B
        fp = _RE_STEP2BPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            if _RE_STEP2BEXPAT.match(w):
                w = w + 'ΕΔ'

        # STEP 2C
        fp = _RE_STEP2CPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            if _RE_STEP2CEXPAT.match(w):
                w = w + 'ΟΥΔ'

        # STEP 2D
        fp = _RE_STEP2DPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP2DEXPAT.match(w):
                w = w + 'Ε'

        # STEP 3
        fp = _RE_STEP3PAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP3PAT2.match(w):
                w = w + 'Ι'

        # STEP 4
        fp = _RE_STEP4PAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if (_RE_STEP4PAT2.match(w) or _RE_STEP4EXPAT.match(w)):
                w = w + 'ΙΚ'

        # STEP 5A
        if w == 'ΑΓΑΜΕ':
            w = 'ΑΓΑΜ'
        fp = _RE_STEP5APAT2.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = _RE_STEP5APAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5AEXPAT.match(w):
                w = w + 'ΑΜ'

        # STEP 5B
        fp = _RE_STEP5BPAT2.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5BPAT4.match(w):
                w = w + 'ΑΓΑΝ'
        fp = _RE_STEP5BPAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if (_RE_STEP5BPAT3.match(w) or _RE_STEP5BEXPAT.match(w)):
                w = w + 'ΑΝ'

        # STEP 5C
        fp = _RE_STEP5CPAT2.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = _RE_STEP5CPAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if (_RE_STEP5CPAT3.match(w) or _RE_STEP5CEXPAT1.match(w) or _RE_STEP5CEXPAT2.match(w)):
                w = w + 'ΕΤ'

        # STEP 5D
        fp = _RE_STEP5DPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5DEXPAT1.match(w):
                w = w + 'ΟΝΤ'
            if _RE_STEP5DEXPAT2.match(w):
                w = w + 'ΩΝΤ'

        # STEP 5E
        fp = _RE_STEP5EPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5EEXPAT.match(w):
                w = w + 'ΟΜΑΣΤ'

        # STEP 5F
        fp = _RE_STEP5FPAT2.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5FPAT3.match(w):
                w = w + 'ΙΕΣΤ'
        fp = _RE_STEP5FPAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5FEXPAT.match(w):
                w = w + 'ΕΣΤ'

        # STEP 5G
        fp = _RE_STEP5GPAT2.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
        fp = _RE_STEP5GPAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if (_RE_STEP5GEXPAT1.match(w) or _RE_STEP5GEXPAT2.match(w)):
                w = w + 'ΗΚ'

        # STEP 5H
        fp = _RE_STEP5HPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if (_RE_STEP5HEXPAT1.match(w) or _RE_STEP5HEXPAT2.match(w)):
                w = w + 'ΟΥΣ'

        # STEP 5I
        fp = _RE_STEP5IPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if ((_RE_STEP5IEXPAT3.match(w) or _RE_STEP5IEXPAT4.match(w)) and not (_RE_STEP5IEXPAT1.match(w) or _RE_STEP5IEXPAT2.match(w))):
                w = w + 'ΑΓ'

        # STEP 5J
        fp = _RE_STEP5JPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5JEXPAT.match(w):
                w = w + 'ΗΣ'

        # STEP 5K
        fp = _RE_STEP5KPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5KEXPAT.match(w):
                w = w + 'ΗΣΤ'

        # STEP 5L
        fp = _RE_STEP5LPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5LEXPAT.match(w):
                w = w + 'ΟΥΝ'

        # STEP 5M
        fp = _RE_STEP5MPAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem
            test1 = False
            if _RE_STEP5MEXPAT.match(w):
                w = w + 'ΟΥΜ'

        # STEP 6
        fp = _RE_STEP6PAT1.match(w)
        if fp:
            stem = fp.group(1)
            w = stem + 'ΜΑ'
        fp = _RE_STEP6PAT2.match(w)
        if fp and test1:
            stem = fp.group(1)
            w = stem

        # STEP 7
        fp = _RE_STEP7PAT.match(w)
        if fp:
            stem = fp.group(1)
            w = stem

        return w

    def stemWords(self, words):
        """
        Calculates the stems of a list of words.
        Takes a list (or tuple) of words as input
        and returns their stems as a list.
        """
        stemmed_words = []
        for word in words:
            stemmed_words.append(self.stemWord(word))
        return stemmed_words
