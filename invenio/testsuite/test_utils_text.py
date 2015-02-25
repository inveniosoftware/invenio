# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

"""Unit tests for the textutils library."""

__revision__ = "$Id$"


try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

from unidecode import unidecode

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

decode_to_unicode = lazy_import('invenio.utils.text:decode_to_unicode')
escape_latex = lazy_import('invenio.utils.text:escape_latex')
guess_minimum_encoding = lazy_import('invenio.utils.text:guess_minimum_encoding')
show_diff = lazy_import('invenio.utils.text:show_diff')
strip_accents = lazy_import('invenio.utils.text:strip_accents')
translate_latex2unicode = lazy_import('invenio.utils.text:translate_latex2unicode')
translate_to_ascii = lazy_import('invenio.utils.text:translate_to_ascii')
transliterate_ala_lc = lazy_import('invenio.utils.text:transliterate_ala_lc')
wash_for_utf8 = lazy_import('invenio.utils.text:wash_for_utf8')
wash_for_xml = lazy_import('invenio.utils.text:wash_for_xml')
wrap_text_in_a_box = lazy_import('invenio.utils.text:wrap_text_in_a_box')


class GuessMinimumEncodingTest(InvenioTestCase):
    """Test functions related to guess_minimum_encoding function."""
    def test_guess_minimum_encoding(self):
        """textutils - guess_minimum_encoding."""
        self.assertEqual(guess_minimum_encoding('patata'), ('patata', 'ascii'))
        self.assertEqual(guess_minimum_encoding('àèéìòù'), ('\xe0\xe8\xe9\xec\xf2\xf9', 'latin1'))
        self.assertEqual(guess_minimum_encoding('Ιθάκη'), ('Ιθάκη', 'utf8'))


class WashForXMLTest(InvenioTestCase):
    """Test functions related to wash_for_xml function."""

    def test_latin_characters_washing_1_0(self):
        """textutils - washing latin characters for XML 1.0."""
        self.assertEqual(wash_for_xml('àèéìòùÀ'), 'àèéìòùÀ')

    def test_latin_characters_washing_1_1(self):
        """textutils - washing latin characters for XML 1.1."""
        self.assertEqual(wash_for_xml('àèéìòùÀ', xml_version='1.1'), 'àèéìòùÀ')

    def test_chinese_characters_washing_1_0(self):
        """textutils - washing chinese characters for XML 1.0."""
        self.assertEqual(wash_for_xml('''
        春眠暁を覚えず
        処処に啼鳥と聞く
        夜来風雨の声
        花落つること
        知んぬ多少ぞ'''), '''
        春眠暁を覚えず
        処処に啼鳥と聞く
        夜来風雨の声
        花落つること
        知んぬ多少ぞ''')

    def test_chinese_characters_washing_1_1(self):
        """textutils - washing chinese characters for XML 1.1."""
        self.assertEqual(wash_for_xml('''
        春眠暁を覚えず
        処処に啼鳥と聞く
        夜来風雨の声
        花落つること
        知んぬ多少ぞ''', xml_version='1.1'), '''
        春眠暁を覚えず
        処処に啼鳥と聞く
        夜来風雨の声
        花落つること
        知んぬ多少ぞ''')

    def test_greek_characters_washing_1_0(self):
        """textutils - washing greek characters for XML 1.0."""
        self.assertEqual(wash_for_xml('''
        ἄνδρα μοι ἔννεπε, μου̂σα, πολύτροπον, ὃς μάλα πολλὰ
        πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν:
        πολλω̂ν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,
        πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν,
        ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων.
        ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ:
        αὐτω̂ν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο,
        νήπιοι, οἳ κατὰ βου̂ς  ̔Υπερίονος  ̓Ηελίοιο
        ἤσθιον: αὐτὰρ ὁ τοι̂σιν ἀφείλετο νόστιμον ἠ̂μαρ.
        τω̂ν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμι̂ν.'''), '''
        ἄνδρα μοι ἔννεπε, μου̂σα, πολύτροπον, ὃς μάλα πολλὰ
        πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν:
        πολλω̂ν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,
        πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν,
        ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων.
        ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ:
        αὐτω̂ν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο,
        νήπιοι, οἳ κατὰ βου̂ς  ̔Υπερίονος  ̓Ηελίοιο
        ἤσθιον: αὐτὰρ ὁ τοι̂σιν ἀφείλετο νόστιμον ἠ̂μαρ.
        τω̂ν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμι̂ν.''')

    def test_greek_characters_washing_1_1(self):
        """textutils - washing greek characters for XML 1.1."""
        self.assertEqual(wash_for_xml('''
        ἄνδρα μοι ἔννεπε, μου̂σα, πολύτροπον, ὃς μάλα πολλὰ
        πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν:
        πολλω̂ν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,
        πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν,
        ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων.
        ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ:
        αὐτω̂ν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο,
        νήπιοι, οἳ κατὰ βου̂ς  ̔Υπερίονος  ̓Ηελίοιο
        ἤσθιον: αὐτὰρ ὁ τοι̂σιν ἀφείλετο νόστιμον ἠ̂μαρ.
        τω̂ν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμι̂ν.''',
        xml_version='1.1'), '''
        ἄνδρα μοι ἔννεπε, μου̂σα, πολύτροπον, ὃς μάλα πολλὰ
        πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν:
        πολλω̂ν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω,
        πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν,
        ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων.
        ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ:
        αὐτω̂ν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο,
        νήπιοι, οἳ κατὰ βου̂ς  ̔Υπερίονος  ̓Ηελίοιο
        ἤσθιον: αὐτὰρ ὁ τοι̂σιν ἀφείλετο νόστιμον ἠ̂μαρ.
        τω̂ν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμι̂ν.''')

    def test_russian_characters_washing_1_0(self):
        """textutils - washing greek characters for XML 1.0."""
        self.assertEqual(wash_for_xml('''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!''', xml_version='1.1'), '''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!''')

    def test_russian_characters_washing_1_1(self):
        """textutils - washing greek characters for XML 1.1."""
        self.assertEqual(wash_for_xml('''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!''', xml_version='1.1'), '''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!''')

    def test_illegal_characters_washing_1_0(self):
        """textutils - washing illegal characters for XML 1.0."""
        self.assertEqual(wash_for_xml(chr(8) + chr(9) + 'some chars'), '\tsome chars')
        self.assertEqual(wash_for_xml('$b\bar{b}$'), '$bar{b}$')

    def test_illegal_characters_washing_1_1(self):
        """textutils - washing illegal characters for XML 1.1."""
        self.assertEqual(wash_for_xml(chr(8) + chr(9) + 'some chars',
                                      xml_version='1.1'), '\x08\tsome chars')
        self.assertEqual(wash_for_xml('$b\bar{b}$', xml_version='1.1'), '$b\x08ar{b}$')


class WashForUTF8Test(InvenioTestCase):
    def test_normal_legal_string_washing(self):
        """textutils - testing UTF-8 washing on a perfectly normal string"""
        some_str = "This is an example string"
        self.assertEqual(some_str, wash_for_utf8(some_str))

    def test_chinese_string_washing(self):
        """textutils - testing washing functions on chinese script"""
        some_str = """春眠暁を覚えず
        処処に啼鳥と聞く
        夜来風雨の声
        花落つること
        知んぬ多少ぞ"""
        self.assertEqual(some_str, wash_for_utf8(some_str))

    def test_russian_characters_washing(self):
        """textutils - washing Russian characters for UTF-8"""
        self.assertEqual(wash_for_utf8('''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!'''), '''
        В тени дерев, над чистыми водами
        Дерновый холм вы видите ль, друзья?
        Чуть слышно там плескает в брег струя;
        Чуть ветерок там дышит меж листами;
        На ветвях лира и венец...
        Увы! друзья, сей холм - могила;
        Здесь прах певца земля сокрыла;
        Бедный певец!''')

    def test_remove_incorrect_unicode_characters(self):
        """textutils - washing out the incorrect characters"""
        self.assertEqual(wash_for_utf8("Ź\206dź\204bło żół\203wia \202"), "Źdźbło żółwia ")

    def test_empty_string_wash(self):
        """textutils - washing an empty string"""
        self.assertEqual(wash_for_utf8(""), "")

    def test_only_incorrect_unicode_wash(self):
        """textutils - washing an empty string"""
        self.assertEqual(wash_for_utf8("\202\203\204\205"), "")

    def test_raising_exception_on_incorrect(self):
        """textutils - assuring an exception on incorrect input"""
        self.assertRaises(UnicodeDecodeError, wash_for_utf8, "\202\203\204\205", correct=False)

    def test_already_utf8_input(self):
        """textutils - washing a Unicode string into UTF-8 binary string"""
        self.assertEqual('Göppert', wash_for_utf8(u'G\xf6ppert', True))


class WrapTextInABoxTest(InvenioTestCase):
    """Test functions related to wrap_text_in_a_box function."""

    def test_plain_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box plain."""
        result = """
**********************************************
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo bar'), result)

    def test_empty_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box empty."""
        result = """
**********************************************
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box(), result)

    def test_with_title_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box with title."""
        result = """
**********************************************
** a Title!                                 **
** **************************************** **
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo bar', title='a Title!'), result)

    def test_multiline_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box multiline."""
        result = """
**********************************************
** foo bar                                  **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo\n bar'), result)

    def test_real_multiline_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box real multiline."""
        result = """
**********************************************
** foo                                      **
** bar                                      **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foo\n\nbar'), result)

    def test_real_no_width_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box no width."""
        result = """
************
** foobar **
************
"""
        self.assertEqual(wrap_text_in_a_box('foobar', min_col=0), result)

    def test_real_nothing_at_all_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box nothing at all."""
        result = """
******
******
"""
        self.assertEqual(wrap_text_in_a_box(min_col=0), result)

    def test_real_squared_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box squared style."""
        result = """
+--------+
| foobar |
+--------+
"""
        self.assertEqual(wrap_text_in_a_box('foobar', style='squared', min_col=0), result)

    def test_indented_text_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box indented text."""
        text = """
    def test_real_squared_wrap_text_in_a_box(self):\n
        \"""wrap_text_in_a_box - squared style.\"""\n
        result = \"""\n
+--------+\n
| foobar |\n
+--------+
\"""
"""
        result = """
******************************
**     def test_real_square **
**     d_wrap_text_in_a_box **
**     (self):              **
**         \"""wrap_text_in_ **
**         a_box - squared  **
**         style.\"""        **
**         result = \"""     **
** +--------+               **
** | foobar |               **
** +--------+\"""            **
******************************
"""
        self.assertEqual(wrap_text_in_a_box(text, min_col=0, max_col=30, break_long=True), result)

    def test_single_new_line_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box single new line."""
        result = """
**********************************************
** ciao come và?                            **
**********************************************
"""
        self.assertEqual(wrap_text_in_a_box("ciao\ncome và?"), result)

    def test_indented_box_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box indented box."""
        result = """
    **********************************************
    ** foobar                                   **
    **********************************************
"""
        self.assertEqual(wrap_text_in_a_box('foobar', tab_num=1), result)

    def test_real_conclusion_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box conclusion."""
        result = """----------------------------------------
foobar                                  \n"""
        self.assertEqual(wrap_text_in_a_box('foobar', style='conclusion'), result)

    def test_real_longtext_wrap_text_in_a_box(self):
        """textutils - wrap_text_in_a_box long text."""
        text = """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat."""

        result = """
************************************************************************
** Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do   **
** eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut     **
** enim ad minim veniam, quis nostrud exercitation ullamco laboris    **
** nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in  **
** reprehenderit in voluptate velit esse cillum dolore eu fugiat      **
** nulla pariatur. Excepteur sint occaecat cupidatat non proident,    **
** sunt in culpa qui officia deserunt mollit anim id est laborum.     **
** At vero eos et accusamus et iusto odio dignissimos ducimus qui     **
** blanditiis praesentium voluptatum deleniti atque corrupti quos     **
** dolores et quas molestias excepturi sint occaecati cupiditate non  **
** provident, similique sunt in culpa qui officia deserunt mollitia   **
** animi, id est laborum et dolorum fuga. Et harum quidem rerum       **
** facilis est et expedita distinctio. Nam libero tempore, cum soluta **
** nobis est eligendi optio cumque nihil impedit quo minus id quod    **
** maxime placeat facere possimus, omnis voluptas assumenda est,      **
** omnis dolor repellendus. Temporibus autem quibusdam et aut         **
** officiis debitis aut rerum necessitatibus saepe eveniet ut et      **
** voluptates repudiandae sint et molestiae non recusandae. Itaque    **
** earum rerum hic tenetur a sapiente delectus, ut aut reiciendis     **
** voluptatibus maiores alias consequatur aut perferendis doloribus   **
** asperiores repellat.                                               **
************************************************************************
"""
        self.assertEqual(wrap_text_in_a_box(text), result)


class DecodeToUnicodeTest(InvenioTestCase):
    """Test functions related to decode_to_unicode function."""
    if CHARDET_AVAILABLE:
        def test_decode_to_unicode(self):
            """textutils - decode_to_unicode."""
            self.assertEqual(decode_to_unicode('\202\203\204\205', default_encoding='latin1'), u'\x82\x83\x84\x85')
            self.assertEqual(decode_to_unicode('àèéìòù'), u'\xe0\xe8\xe9\xec\xf2\xf9')
            self.assertEqual(decode_to_unicode('Ιθάκη'), u'\u0399\u03b8\u03ac\u03ba\u03b7')
    else:
        pass


class Latex2UnicodeTest(InvenioTestCase):
    """Test functions related to translating LaTeX symbols to Unicode."""

    def test_latex_to_unicode(self):
        """textutils - latex_to_unicode"""
        self.assertEqual(translate_latex2unicode("\\'a \\'i \\'U").encode('utf-8'), "á í Ú")
        self.assertEqual(translate_latex2unicode("\\'N \\k{i}"), u'\u0143 \u012f')
        self.assertEqual(translate_latex2unicode("\\AAkeson"), u'\u212bkeson')
        self.assertEqual(translate_latex2unicode("$\\mathsl{\\Zeta}$"), u'\U0001d6e7')


class TestStripping(InvenioTestCase):
    """Test for stripping functions like accents and control characters."""
    def test_text_to_ascii(self):
        """textutils - transliterate to ascii using unidecode"""
        self.assert_(translate_to_ascii(
            ["á í Ú", "H\xc3\xb6hne", "Åge Øst Vær", "normal"]) in
            (["a i U", "Hohne", "Age Ost Vaer", "normal"],  ## unidecode < 0.04.13
                ['a i U', 'Hoehne', 'Age Ost Vaer', 'normal']) ## unidecode >= 0.04.13
        )
        self.assertEqual(translate_to_ascii("àèéìòù"), ["aeeiou"])
        self.assertEqual(translate_to_ascii("ß"), ["ss"])
        self.assertEqual(translate_to_ascii(None), None)
        self.assertEqual(translate_to_ascii([]), [])
        self.assertEqual(translate_to_ascii([None]), [None])
        self.assertEqual(translate_to_ascii("√"), [""])

    def test_strip_accents(self):
        """textutils - transliterate to ascii (basic)"""
        self.assertEqual("memememe",
                         strip_accents('mémêmëmè'))
        self.assertEqual("MEMEMEME",
                         strip_accents('MÉMÊMËMÈ'))
        self.assertEqual("oe",
                         strip_accents('œ'))
        self.assertEqual("OE",
                         strip_accents('Œ'))

class TestDiffering(InvenioTestCase):
    """Test for differing two strings."""

    string1 = """Lorem ipsum dolor sit amet, consectetur adipiscing
elit. Donec fringilla tellus eget fringilla sagittis. Pellentesque
posuere lacus id erat tristique pulvinar. Morbi volutpat, diam
eget interdum lobortis, lacus mi cursus leo, sit amet porttitor
neque est vitae lectus. Donec tempor metus vel tincidunt fringilla.
Nam iaculis lacinia nisl, enim sollicitudin
convallis. Morbi ut mauris velit. Proin suscipit dolor id risus
placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
dui. Nunc commodo neque porttitor eros placerat, sed ultricies purus
accumsan. In velit nisi, accumsan molestie gravida a, rutrum in augue.
Nulla pharetra purus nec dolor ornare, ut aliquam odio placerat.
Aenean ultrices condimentum quam vitae pharetra."""

    string2 = """Lorem ipsum dolor sit amet, consectetur adipiscing
elit. Donec fringilla tellus eget fringilla sagittis. Pellentesque
posuere lacus id erat.
eget interdum lobortis, lacus mi cursus leo, sit amet porttitor
neque est vitae lectus. Donec tempor metus vel tincidunt fringilla.
Nam iaculis lacinia nisl, consectetur viverra enim sollicitudin
convallis. Morbi ut mauris velit. Proin suscipit dolor id risus
placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
dui. Nunc commodo neque porttitor eros placerat, sed ultricies purus
accumsan. In velit nisi, lorem ipsum lorem gravida a, rutrum in augue.
Nulla pharetra purus nec dolor ornare, ut aliquam odio placerat.
Aenean ultrices condimentum quam vitae pharetra."""

    def test_show_diff_plain_text(self):
        """textutils - show_diff() with plain text"""

        expected_result = """
 Lorem ipsum dolor sit amet, consectetur adipiscing
 elit. Donec fringilla tellus eget fringilla sagittis. Pellentesque
-posuere lacus id erat.
+posuere lacus id erat tristique pulvinar. Morbi volutpat, diam
 eget interdum lobortis, lacus mi cursus leo, sit amet porttitor
 neque est vitae lectus. Donec tempor metus vel tincidunt fringilla.
-Nam iaculis lacinia nisl, consectetur viverra enim sollicitudin
+Nam iaculis lacinia nisl, enim sollicitudin
 convallis. Morbi ut mauris velit. Proin suscipit dolor id risus
 placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
-placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
 dui. Nunc commodo neque porttitor eros placerat, sed ultricies purus
-accumsan. In velit nisi, lorem ipsum lorem gravida a, rutrum in augue.
+accumsan. In velit nisi, accumsan molestie gravida a, rutrum in augue.
 Nulla pharetra purus nec dolor ornare, ut aliquam odio placerat.
 Aenean ultrices condimentum quam vitae pharetra.
"""

        self.assertEqual(show_diff(self.string1, self.string2), expected_result)

    def test_show_diff_html(self):
        """textutils - show_diff() with plain text"""

        expected_result = """<pre>
Lorem ipsum dolor sit amet, consectetur adipiscing
elit. Donec fringilla tellus eget fringilla sagittis. Pellentesque
<strong class="diff_field_deleted">posuere lacus id erat.</strong>
<strong class="diff_field_added">posuere lacus id erat tristique pulvinar. Morbi volutpat, diam</strong>
eget interdum lobortis, lacus mi cursus leo, sit amet porttitor
neque est vitae lectus. Donec tempor metus vel tincidunt fringilla.
<strong class="diff_field_deleted">Nam iaculis lacinia nisl, consectetur viverra enim sollicitudin</strong>
<strong class="diff_field_added">Nam iaculis lacinia nisl, enim sollicitudin</strong>
convallis. Morbi ut mauris velit. Proin suscipit dolor id risus
placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet
<strong class="diff_field_deleted">placerat sodales nec id elit. Morbi vel lacinia lectus, eget laoreet</strong>
dui. Nunc commodo neque porttitor eros placerat, sed ultricies purus
<strong class="diff_field_deleted">accumsan. In velit nisi, lorem ipsum lorem gravida a, rutrum in augue.</strong>
<strong class="diff_field_added">accumsan. In velit nisi, accumsan molestie gravida a, rutrum in augue.</strong>
Nulla pharetra purus nec dolor ornare, ut aliquam odio placerat.
Aenean ultrices condimentum quam vitae pharetra.
</pre>"""

        self.assertEqual(show_diff(self.string1,
                                   self.string2,
                                   prefix="<pre>", suffix="</pre>",
                                   prefix_unchanged='',
                                   suffix_unchanged='',
                                   prefix_removed='<strong class="diff_field_deleted">',
                                   suffix_removed='</strong>',
                                   prefix_added='<strong class="diff_field_added">',
                                   suffix_added='</strong>'), expected_result)


class TestALALC(InvenioTestCase):
    """Test for handling ALA-LC transliteration."""

    def test_alalc(self):
        msg = "眾鳥高飛盡"
        encoded_text, encoding = guess_minimum_encoding(msg)
        unicode_text = unicode(encoded_text.decode(encoding))
        self.assertEqual("Zhong Niao Gao Fei Jin ",
                            transliterate_ala_lc(unicode_text))


class LatexEscape(InvenioTestCase):
    """Test for escape latex function"""

    def test_escape_latex(self):
        unescaped = "this is unescaped latex & % $ # _ { } ~  \ ^ and some multi-byte chars: żółw mémêmëmè"
        escaped = escape_latex(unescaped)
        self.assertEqual(escaped,
                         "this is unescaped latex \\& \\% \\$ \\# \\_ \\{ \\} \\~{}  \\textbackslash{} \\^{} and some multi-byte chars: \xc5\xbc\xc3\xb3\xc5\x82w m\xc3\xa9m\xc3\xaam\xc3\xabm\xc3\xa8")


TEST_SUITE = make_test_suite(WrapTextInABoxTest, GuessMinimumEncodingTest,
                             WashForXMLTest, WashForUTF8Test, DecodeToUnicodeTest,
                             Latex2UnicodeTest, TestStripping,
                             TestALALC, TestDiffering)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
