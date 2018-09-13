# Encoding: utf-8

#  --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys

import pkg_resources

from nagare.admin import admin
from nagare.services import reporters


class Info(admin.Command):
    DESC = 'Display various informations'
    WITH_CONFIG_FILENAME = False

    def set_arguments(self, parser):
        super(Info, self).set_arguments(parser)

        parser.add_argument(
            '-l', '--location', action='store_true',
            help='Display the Python package locations'
        )

    @staticmethod
    def run(location):
        implementation = getattr(sys, 'subversion', None)
        if implementation:
            implementation = implementation[0]
        else:
            implementation = sys.implementation.name.capitalize()

        print(admin.BANNER + '\n\n')
        print('%s %s\n' % (implementation, sys.version))

        activated_columns = {'package', 'version'}
        if location:
            activated_columns.add('location')

        print('Nagare packages:\n')
        nagare_packages = [(dist,) for dist in pkg_resources.working_set if dist.project_name.startswith('nagare-')]
        reporters.PackagesReporter().report(activated_columns, nagare_packages)

        return 0
