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
