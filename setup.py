#!/usr/bin/env python

# //******************************************************************************
# //
# //  setup.py
# //
# //  RPN command-line calculator, setup script
# //  copyright (c) 2015 (1988), Rick Gutleber (rickg@his.com)
# //
# //  License: GNU GPL 3.0 (see <http://www.gnu.org/licenses/gpl.html> for more
# //  information).
# //
# //******************************************************************************

import os

from setuptools import setup, find_packages

def read( *paths ):
    """Build a file path from *paths* and return the contents."""
    with open( os.path.join( *paths ), 'r') as f:
        return f.read( )

setup(
    name = 'whereis',
    version = '3.10.0',
    description = 'command-line file searching utility',
    long_description =
'''
''',

    url = 'http://github.com/ConceptJunkie/whereis/',
    license = 'GPL3',
    author = 'Rick Gutleber',
    author_email = 'rickg@his.com',
    py_modules = [ 'whereis' ],
    install_requires = open( 'requirements.txt' ).read( ).splitlines( ),
    include_package_data = True,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Environment :: Console',
    ],
    entry_points = {
        'console_scripts': [
            'sample=sample:main',
        ],
    },
)

