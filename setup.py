#!/usr/bin/env python2
import os

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), 'rb') as f:
    long_description = f.read().decode('utf8')

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'django_nameko/VERSION')) as f:
    __version__ = f.read()

from setuptools import setup

setup(
    name='django-nameko',
    version=__version__,
    description=' Django wrapper for nameko microservice framework.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/and3rson/django-nameko',
    author='Andrew Dunai',
    author_email='andrew@dun.ai',
    maintainer='Vincent Anh Tran',
    maintainer_email='tranvietanh1991@gmail.com',
    license='GPLv2',
    packages=['django_nameko'],
    zip_safe=False,
    install_requires=[
        'nameko>=2.11.0',
        'django>=1.10'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
