<protect># lextab.py.  This file automatically created by PLY. Don't edit.
_lexre = '(?P<t_CDSON>\\s*cdson:::\\n+)|(?P<t_KEY>(?<=\\n)[\\ \\t]*_+\\w+?_+\\s*\\n+)|(?P<t_VALUE>.+?\\S+.*?(?=([\\ \\t]*_+\\w+?_+\\s*\\n|\\n\\s*cdsoff:::)))|(?P<t_CDSOFF>(?s)\\n\\s*cdsoff:::(\\n.*)?)'
_lextab = [
  None,
  ('t_CDSON','CDSON'),
  ('t_KEY','KEY'),
  ('t_VALUE','VALUE'),
  None,
  ('t_CDSOFF','CDSOFF'),
]
_lextokens = {'VALUE': None, 'CDSON': None, 'CDSOFF': None, 'KEY': None}
_lexignore = None
_lexerrorf = 't_error'
</protect>
