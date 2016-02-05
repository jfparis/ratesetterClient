# -*- coding: utf-8 -*-

#  Copyright 2014-2016 Jean-Francois Paris
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import ratesetterclient

setup(
    name='ratesetterClient',
    version=ratesetterclient.__version__,
    description='python library for ratesetter.com',
    author='Jean-Francois Paris',
    author_email='jfparis@rouge.eu.org',
    package_dir={'':'.'},
    url="https://github.com/jfparis/ratesetterClient",
    packages=['ratesetterclient'],
    license='LGPL 2.0',
    install_requires=[
        'lxml',
        'requests',
        'pandas',
    ],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',

    ),
)
