<protect>#!/usr/bin/env python
# -*- encoding: utf8 -*-

# Converted from the original japanese.ms932 encoding to utf8.

# encdet.py - An encoding detector
# by Yusuke Shinyama
#  * public domain *

import sys, re


##  EncodingRecognizer
##  - a finite automaton which receives octets
##
class EncodingRecognizer:

  SCORE_DEFAULT = 0.5
  DEATH_PENALTY = -100
  GIVEUP_THRESHOLD = -1000
  
  # character sets: must be exclusive!
  CHARSET = [
    # zenkaku-kana
    (1.5, re.compile(u"[ぁ-ん]"), 0x01),
    (1.5, re.compile(u"[ァ-ヴ]"), 0x02),
    (1.0, re.compile(u"[ーヽヾゝゞ]"), 0x03),

    # hankaku latin
    (1.2, re.compile(u"[a-zA-Z0-9]"), 0x04),
    (0.0, re.compile(u"[\u00c0-\u00ff]"), 0x04),

    # hankaku-kana
    (0.8, re.compile(u"[\uff66-\uff9d]"), 0x08),

    # zenkaku-alphanum
    (1.2, re.compile(u"[Ａ-Ｚａ-ｚ０-９]"), 0x10),
    
    # kanji
    (1.0, re.compile(u"[\u4e00-\u9fff]"), 0x20),

    ]
  
  def __init__(self, encoding):
    self.encoding = encoding
    self.ch = ""
    self.state = 1
    self.partial_score = 0.0
    self.total_score = 0.0
    self.chunk_type = 0
    return

  def __repr__(self):
    return "<EncodingRecognizer: %s, state=%d, chunk_type=%s, partial_score=%d, total_score=%d>" % \
           (self.encoding, self.state, self.chunk_type, self.partial_score, self.total_score)
  
  def die(self):
    #print "died:", self
    self.total_score += self.DEATH_PENALTY
    if self.total_score <= self.GIVEUP_THRESHOLD:
      # game is over...
      #print "giveup:", self
      self.state = 0
    else:
      # try again...
      self.state = 1
      self.partial_score = 0
      self.ch = ""
    return
    
  def flush(self):
    self.total_score += self.partial_score * self.partial_score
    self.partial_score = 0.0
    return

  def accept(self, s):
    try:
      c = unicode(s, self.encoding)
    except UnicodeError:
      c = ""
    for (score, pat, flags) in self.CHARSET:
      if pat.match(c):
        if self.chunk_type == 0 or not (self.chunk_type & flags):
          self.flush()
        self.chunk_type = flags
        self.partial_score += score
        break
    else:
      self.flush()
      self.chunk_type = 0
      self.partial_score += self.SCORE_DEFAULT
    return

  def finish(self):
    self.flush()
    if 1 < self.state:
      self.die()
    return


##  CHARACTER SETS


##  ISO-8859-*
##
class ISO8859_Recognizer(EncodingRecognizer):
  
  def __init__(self):
    return EncodingRecognizer.__init__(self, "iso8859_1")
  
  def feed(self, c):
    if self.state == 0:                 # already dead?
      return          

    elif self.state == 1:               # ascii or iso?
      if c < 0x7f or (0xa0 <= c and c <= 0xff):
        self.state = 1
        self.accept(chr(c))

      else:
        self.die()
    
    return


##  EUC-JP
##
class EUCJP_Recognizer(EncodingRecognizer):

  def __init__(self):
    self.hankaku = False
    return EncodingRecognizer.__init__(self, "japanese.euc_jp")
  
  def feed(self, c):
    if self.state == 0:                 # already dead?
      return          

    # 1stbyte
    elif self.state == 1:
      if c < 0x7f:                      # ascii?
        # succeed
        self.state = 1
        self.accept(chr(c))
        self.ch = ""
# IGNORE EUC-JP hankaku chars,  no one is using
#      elif 0x8e == c:                   # hankaku-kana 1stbyte?
#        # next
#        self.state = 2
#        self.ch = chr(c)
#        self.hankaku = True
      elif 0xa1 <= c and c <= 0xfe:     # kanji 1stbyte?
        # next
        self.state = 2
        self.ch = chr(c)
        self.hankaku = False
      else:
        self.die()

    # 2ndbyte
    elif self.state == 2:
      if self.hankaku and (0xa1 <= c and c <= 0xdf): # hankaku-kana 2ndbyte?
        # succeed
        self.ch += chr(c)        
        self.accept(self.ch)
        self.state = 1
        self.ch = ""
      elif not self.hankaku and (0xa1 <= c and c <= 0xfe): # kanji 2ndbyte?
        # succeed
        self.ch += chr(c)        
        self.accept(self.ch)
        self.state = 1
        self.ch = ""
      else:
        self.die()
        
    return


##  CP932
##
class CP932_Recognizer(EncodingRecognizer):
  
  def __init__(self):
    return EncodingRecognizer.__init__(self, "japanese.ms932")
  
  def feed(self, c):
    if self.state == 0:                 # already dead?
      return          

    # 1stbyte
    elif self.state == 1:
      if c < 0x7f:                      # ascii?
        # succeed
        self.state = 1
        self.accept(chr(c))
        self.ch = ""
      elif 0xa1 <= c and c <= 0xdf:     # hankaku-kana?
        # succeed
        self.state = 1
        self.accept(chr(c))
        self.ch = ""
      elif (0x81 <= c and c <= 0x9f) or (0xe0 <= c and c <= 0xee) \
           or (0xfa <= c and c <= 0xfc): # kanji 1stbyte?
        # next
        self.state = 2
        self.ch = chr(c)
      else:
        self.die()

    # 2ndbyte
    elif self.state == 2:
      if 0x40 <= c and c <= 0xfc and c != 0x7f: # kanji 2ndbyte?
        # succeed
        self.accept(self.ch+chr(c))
        self.state = 1
        self.ch = ""
      else:
        self.die()
        
    return


##  UTF-8
##
class UTF8_Recognizer(EncodingRecognizer):

  def __init__(self):
    self.left = 0
    return EncodingRecognizer.__init__(self, "utf8")
  
  def feed(self, c):
    if self.state == 0:                 # already dead?
      return          

    # 1stbyte
    elif self.state == 1:
      if c <= 0x7f:                     # 00xxxxxx: 1byte only?
        # succeed
        self.state = 1
        self.accept(chr(c))
        self.ch = ""
      elif c & 0xe0 == 0xc0:            # 110xxxxx: 2bytes
        # next
        self.state = 2
        self.left = 1
        self.ch = chr(c)
      elif c & 0xf0 == 0xe0:            # 1110xxxx: 3bytes
        # next
        self.state = 2
        self.left = 2
        self.ch = chr(c)
      elif c & 0xf8 == 0xf0:            # 11110xxx: 4bytes
        # next
        self.state = 2
        self.left = 3
        self.ch = chr(c)
      elif c & 0xfc == 0xf8:            # 111110xx: 5bytes
        # next
        self.state = 2
        self.left = 4
        self.ch = chr(c)
      else:
        self.die()
        
    # n-th byte (where 2<=n)
    else:
      if c & 0xc0 == 0x80:              # 10xxxxxx: continuous?
        self.state += 1
        self.left -= 1
        self.ch += chr(c)
        if self.left == 0:              # finished?
          # succeed
          self.state = 1
          self.accept(self.ch)
          self.ch = ""
        else:
          # next
          pass
      else:
        self.die()
        
    return


# guess
def guess(s):
  recognizer = [
    EUCJP_Recognizer(),
    CP932_Recognizer(),
    ISO8859_Recognizer(),
    UTF8_Recognizer()
    ]
  for c in s:
    for r in recognizer:
      r.feed(ord(c))
  for r in recognizer:
    r.finish()
    #print r
  recognizer.sort(lambda a,b: cmp(b.total_score, a.total_score))
  return recognizer[0].encoding

# test suite
def test(s0, test_encodings):
  false_encodings = [ "japanese.euc_jp", "japanese.ms932", "utf8", "iso8859_1" ]
  for enc1 in test_encodings:
    try:
      s = s0.encode(enc1)
    except UnicodeError:
      continue
    print "try '%s' in %s (%s)" % (s0.encode('utf8'), enc1.encode('utf8'), " ".join(map(lambda c:"%02x" % ord(c), s)))
    for enc2 in false_encodings:
      if enc1 != enc2:
        try:
          x = str(unicode(s, enc2))
          print "  (could be: '%s' in %s)" % (x, enc2)
        except UnicodeError:
          continue
    genc = guess(s)
    if genc == enc1:
      print "  CORRECT:", genc
    else:
      print "  ! INCORRECT:", genc
    print
  return

def test_suite():
  # kana only
  test(u"こんにちは", ["japanese.euc_jp", "japanese.ms932", "utf8"])
  # kana + alphanum
  test(u"AはBとCである", ["japanese.euc_jp", "japanese.ms932", "utf8"])
  # kana + kanji
  test(u"毎朝新聞ニュース", ["japanese.euc_jp", "japanese.ms932", "utf8"])
  # kanji + hankakukana
  test(u"無題ﾄﾞｷｭﾒﾝﾄ", ["japanese.ms932", "utf8"])
  # iso8859-1
  test(u"Enzyklop\u00e4die", ["utf8", "iso8859_1"])
  return

# main
test_suite(); sys.exit(0)
if __name__ == "__main__":
  import fileinput
  for s in fileinput.input():
    print guess(s)</protect>
