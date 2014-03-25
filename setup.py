"""
carafe
======

Flask application factory with extensions geared towards JSON APIs.

Documentation: https://github.com/dgilland/carafe
"""

from setuptools import setup, find_packages

setup(
    name='carafe',
    version='0.1.5',
    url='https://github.com/dgilland/carafe',
    license='MIT',
    author='Derrick Gilland',
    author_email='dgilland@gmail.com',
    description='Flask application factory with extensions geared towards JSON APIs.',
    long_description=__doc__,
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    install_requires=[
        'Flask>=0.10.1',
        'Flask-Cache>=0.12',
        'Flask-Classy>=0.6.8',
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
