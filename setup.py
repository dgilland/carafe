"""
carafe
======

Flask application factory with extensions geared towards JSON APIs.

Documentation: https://github.com/dgilland/carafe
"""

from setuptools import setup, find_packages


meta = {}
with open('carafe/__meta__.py') as fp:
    exec(fp.read(), meta)


setup(
    name=meta['__title__'],
    version=meta['__version__'],
    url=meta['__url__'],
    license=meta['__license__'],
    author=meta['__author__'],
    author_email=meta['__email__'],
    description=meta['__summary__'],
    long_description=__doc__,
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    install_requires=[
        'Flask>=0.10.1',
        'Flask-Cache>=0.12',
        'Flask-Principal>=0.4.0',
        'Flask-Testing>=0.4',
        'blinker>=1.3',
    ],
    test_suite='tests',
    keywords='flask',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ]
)
