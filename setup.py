# Encoding: utf-8

# --
# Copyright (c) 2008-2021 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as description:
    LONG_DESCRIPTION = description.read()

setup(
    name='nagare-commands-base',
    author='Net-ng',
    author_email='alain.poirier@net-ng.com',
    description="'nagare-admin' executable",
    long_description=LONG_DESCRIPTION,
    license='BSD',
    keywords='',
    url='https://github.com/nagareproject/commands-base',
    packages=find_packages(),
    zip_safe=False,
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=[
        'appdirs',
        'colorama',
        'nagare-config',
        'nagare-services',
        'nagare-commands'
    ],
    entry_points='''
    [console_scripts]
    nagare-admin = nagare.admin.admin:run

    [nagare.commands]
    info = nagare.admin.info:Info
    '''
)
