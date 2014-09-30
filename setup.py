# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""
Invenio is Fun.

Links
-----

* `website <http://invenio-software.org/>`_
* `documentation <http://invenio.readthedocs.org/en/latest/>`_
* `development version <https://github.com/inveniosoftware/invenio>`_

"""

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install_lib import install_lib
from distutils.command.build import build


class _build(build):

    """Compile catalog before building the package."""

    sub_commands = [('compile_catalog', None)] + build.sub_commands


class _install_lib(install_lib):

    """Custom install_lib command."""

    def run(self):
        """Compile catalog before running installation command."""
        self.run_command('compile_catalog')
        install_lib.run(self)

dependency_links = [
    "git+git://github.com/mrjoes/flask-admin.git#egg=Flask-Admin-1.0.9.dev0",
    "git+git://github.com/inveniosoftware/workflow.git@e41299579501704b1486c72cc2509a9f82e63ea6#egg=workflow",
]

install_requires = [
    "alembic>=0.6.6",
    "Babel>=1.3",
    "bagit>=1.5.1",
    "BeautifulSoup>=3.2.1",
    "BeautifulSoup4>=4.3.2",
    "celery>=3.1.8",
    # Cerberus>=0.7.1 api changes and is not yet supported
    "Cerberus>=0.7,<0.7.1",
    "dictdiffer>=0.0.3",
    "feedparser>=5.1",
    "fixture>=1.5",
    "Flask>=0.10.1",
    # Development version is used, will switch to >=1.0.9 once released.
    "Flask-Admin>=1.0.9.dev0",
    "Flask-Assets>=0.10",
    "Flask-Babel>=0.9",
    "Flask-Breadcrumbs>=0.1",
    "Flask-Cache>=0.12",
    "Flask-Collect>=0.2.3",
    "Flask-Email>=1.4.4",
    "Flask-Gravatar>=0.4",
    "Flask-Login>=0.2.7",
    "Flask-Menu>=0.1",
    "Flask-OAuthlib>=0.6.0,<0.7",  # quick fix for issue #2158
    "Flask-Principal>=0.4",
    "Flask-Registry>=0.2",
    "Flask-RESTful>=0.2.12",
    "Flask-Script>=2.0.5",
    # Development version is used, will switch to >=2.0 once released.
    "Flask-SQLAlchemy>=2.0",
    "Flask-WTF>=0.9.5",
    "fs>=0.4",
    "intbitset>=2.0",
    "jellyfish>=0.3.2",
    "Jinja2>=2.7",
    "libmagic>=1.0",
    "lxml>=3.3",
    "mechanize>=0.2.5",
    "msgpack-python>=0.3",
    "MySQL-python>=1.2.5",
    "numpy>=1.7",
    "nydus>=0.10.8",
    # pyparsing>=2.0.2 has a new api and is not compatible yet
    "pycrypto>=2.0.1",
    "pyparsing>=2.0.1,<2.0.2",
    "python-twitter>=0.8.7",
    "pyPDF>=1.13",
    "pyPDF2",
    "PyLD>=0.5.2",
    "pyStemmer>=1.3",
    # python-dateutil>=2.0 is only for Python3
    "python-dateutil>=1.5,<2.0",
    "python-magic>=0.4.6",
    "pytz",
    "rauth",
    "raven>=5.0.0",
    "rdflib>=4.1.2",
    "redis==2.8.0",  # Is it explicitly required?
    "reportlab>=2.7,<3.2",
    "requests>=2.3,<2.4",
    "setuptools>=2.2",
    "six>=1.7.2",
    "Sphinx",
    # SQLAlchemy 0.9 is not compatible yet
    "SQLAlchemy>=0.8.3,<0.9",
    # SQLAlchemy-Utils>0.24 depends on SQLAlchemy>=0.9.3
    "SQLAlchemy-Utils>=0.23.5,<0.24",
    "unidecode",
    "workflow>=1.1.0",
    # Flask-WTF 0.9.5 doesn't support WTForms 2.0 as of yet.
    "WTForms>=1.0.5,<2.0",
    "wtforms-alchemy>=0.12.6"
]


extras_require = {
    "docs": [
        "sphinx_rtd_theme"
    ],
    "development": [
        "Flask-DebugToolbar==0.9.0",
    ],
    "elasticsearch": [
        "pyelasticsearch>=0.6.1"
    ],
    "img": [
        "qrcode",
        "Pillow"
    ],
    "mongo": [
        "pymongo"
    ],
    "misc": [  # was requirements-extras
        "apiclient",  # extra=cloud?
        "dropbox",  # extra=cloud?
        "gnuplot-py==1.8",
        "flake8",  # extra=kwalitee?
        "pep8",  # extra=kwalitee?
        "pychecker==0.8.19",  # extra=kwalitee?
        "pylint",  # extra=kwalitee?
        "nosexcover",  # test?
        "oauth2client",  # extra=cloud?
        "python-onedrive",  # extra=cloud?
        "python-openid",  # extra=sso?
        "urllib3",  # extra=cloud?
    ],
    "sso": [
        "Flask-SSO>=0.1"
    ],
    "postgresql": [
        "psycopg2>=2.5",
    ],
    # Alternative XML parser
    #
    # For pyRXP, the version on PyPI many not be the right one.
    #
    # $ pip install
    # >    https://www.reportlab.com/ftp/pyRXP-1.16-daily-unix.tar.gz#egg=pyRXP
    #
    "pyrxp": [
        # Any other versions are not supported.
        "pyRXP==1.16-daily-unix"
    ],
    "github": [
        "github3.py>=0.9"
    ],
}

extras_require["docs"] += extras_require["elasticsearch"]
extras_require["docs"] += extras_require["img"]
extras_require["docs"] += extras_require["mongo"]
extras_require["docs"] += extras_require["sso"]
extras_require["docs"] += extras_require["github"]

tests_require = [
    "httpretty>=0.8",
    "Flask-Testing>=0.4.1",
    "mock",
    "nose",
    "selenium",
    "unittest2>=0.5",
]


# Compatibility with Python 2.6
if sys.version_info < (2, 7):
    install_requires += [
        "argparse",
        "importlib"
    ]


# Get the version string.  Cannot be done with import!
g = {}
with open(os.path.join("invenio", "version.py"), "rt") as fp:
    exec(fp.read(), g)
version = g["__version__"]

packages = find_packages(exclude=['docs'])
packages.append('invenio_docs')

setup(
    name='Invenio',
    version=version,
    url='https://github.com/inveniosoftware/invenio',
    license='GPLv2',
    author='CERN',
    author_email='info@invenio-software.org',
    description='Digital library software',
    long_description=__doc__,
    packages=packages,
    package_dir={'invenio_docs': 'docs'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    entry_points={
        'console_scripts': [
            'inveniomanage = invenio.base.manage:main',
            'plotextractor = invenio.utils.scripts.plotextractor:main',
            # Legacy
            'alertengine = invenio.legacy.webalert.scripts.alertengine:main',
            'batchuploader = invenio.legacy.bibupload.scripts.batchuploader',
            'bibcircd = invenio.legacy.bibcirculation.scripts.bibcircd:main',
            'bibauthorid = invenio.legacy.bibauthorid.scripts.bibauthorid:main',
            'bibclassify = invenio.modules.classifier.scripts.classifier:main',
            'bibconvert = invenio.legacy.bibconvert.scripts.bibconvert:main',
            'bibdocfile = invenio.legacy.bibdocfile.scripts.bibdocfile:main',
            'bibedit = invenio.legacy.bibedit.scripts.bibedit:main',
            'bibencode = invenio.modules.encoder.scripts.encoder:main',
            'bibindex = invenio.legacy.bibindex.scripts.bibindex:main',
            'bibmatch = invenio.legacy.bibmatch.scripts.bibmatch:main',
            'bibrank = invenio.legacy.bibrank.scripts.bibrank:main',
            'bibrankgkb = invenio.legacy.bibrank.scripts.bibrankgkb:main',
            'bibreformat = invenio.legacy.bibformat.scripts.bibreformat:main',
            'bibsort = invenio.legacy.bibsort.scripts.bibsort:main',
            'bibsched = invenio.legacy.bibsched.scripts.bibsched:main',
            'bibstat = invenio.legacy.bibindex.scripts.bibstat:main',
            'bibtaskex = invenio.legacy.bibsched.scripts.bibtaskex:main',
            'bibtasklet = invenio.legacy.bibsched.scripts.bibtasklet:main',
            'bibupload = invenio.legacy.bibupload.scripts.bibupload:main',
            'dbexec = invenio.legacy.miscutil.scripts.dbexec:main',
            'dbdump = invenio.legacy.miscutil.scripts.dbdump:main',
            'docextract = invenio.legacy.docextract.scripts.docextract:main',
            'elmsubmit = invenio.legacy.elmsubmit.scripts.elmsubmit:main',
            'gotoadmin = invenio.modules.redirector.scripts.redirector:main',
            'inveniocfg = invenio.legacy.inveniocfg:main',
            'inveniogc = invenio.legacy.websession.scripts.inveniogc:main',
            'inveniounoconv = invenio.legacy.websubmit.scripts.inveniounoconv:main',
            'oaiharvest = invenio.legacy.oaiharvest.scripts.oaiharvest:main',
            'oairepositoryupdater = invenio.legacy.oairepository.scripts.oairepositoryupdater:main',
            'arxiv-pdf-checker = invenio.legacy.pdfchecker:main',
            'refextract = invenio.legacy.refextract.scripts.refextract:main',
            'textmarc2xmlmarc = invenio.legacy.bibrecord.scripts.textmarc2xmlmarc:main',
            'webaccessadmin = invenio.modules.access.scripts.webaccessadmin:main',
            'webauthorprofile = invenio.legacy.webauthorprofile.scripts.webauthorprofile:main',
            'webcoll = invenio.legacy.websearch.scripts.webcoll:main',
            'webmessageadmin = invenio.legacy.webmessage.scripts.webmessageadmin:main',
            'webstatadmin = invenio.legacy.webstat.scripts.webstatadmin:main',
            'websubmitadmin = invenio.legacy.websubmit.scripts.websubmitadmin:main',
            'xmlmarc2textmarc = invenio.legacy.bibrecord.scripts.xmlmarc2textmarc:main',
            'xmlmarclint = invenio.legacy.bibrecord.scripts.xmlmarclint:main',
        ],
        "distutils.commands": [
            "inveniomanage = invenio.base.setuptools:InvenioManageCommand",
        ]
    },
    install_requires=install_requires,
    dependency_links=dependency_links,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv2 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    test_suite='invenio.testsuite.suite',
    tests_require=tests_require,
    cmdclass={
        'build': _build,
        'install_lib': _install_lib,
    },
)
