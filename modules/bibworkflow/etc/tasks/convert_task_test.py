from invenio.flaskshell import *
from invenio.bibworkflow_api import run

t = open('input2.xml').read()
run('workflow3', [{'data': t}])
