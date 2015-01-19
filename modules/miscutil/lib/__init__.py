"""
Invenio software enables you to run your own electronic preprint server,
your own online library catalogue or a digital document system on the
web.

To learn more about Invenio software, please go to U{Invenio software
distribution site <http://invenio-software.org/>}.

To learn more about Invenio modules and programming, please go to
U{Hacking Invenio <http://demo.invenio-software.org/help/hacking/>} web pages.

To browse Invenio source code repository, inspect commits,
revisions and the like, please go to U{Invenio git web repository
<http://invenio-software.org/repo/invenio>}.

This place enables you to browse Invenio source code documentation
as well as the source code snippets themselves.
"""

# Let's globally set the default encoding to UTF-8. This is needed
# when a unicode object is concatenated with a Python string, and this
# latter is casted to unicode.
# See: <http://stackoverflow.com/questions/2276200/changing-default-encoding-of-python>
import sys
reload(sys)
sys.setdefaultencoding('utf8')

## Because we use getLogger calls to do logging, handlers aren't initialised
## unless we explicitly call/import this code somewhere.
import elasticsearch_logging
