# Encoding: utf-8

# --
# Copyright (c) 2008-2021 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys

import pkg_resources

from nagare.admin import admin
from nagare.services import services, reporters


class Info(admin.Command):
    DESC = 'display runtime informations'
    WITH_CONFIG_FILENAME = False

    def set_arguments(self, parser):
        super(Info, self).set_arguments(parser)

        parser.add_argument(
            '-l', '--location', action='store_true',
            help='display the Python package locations'
        )

    @classmethod
    def run(cls, location):
        implementation = getattr(sys, 'subversion', None)
        if implementation:
            implementation = implementation[0]
        else:
            implementation = sys.implementation.name.capitalize()

        with admin.Banner(file=sys.stdout) as display:
            display((implementation + ' ' + sys.version).splitlines())
            display()

            has_user_data_file, user_data_file = cls.get_user_data_file()
            display('User configuration [%sFOUND]: ' % ('NOT ' if not has_user_data_file else ''))
            display('')
            display('  ' + user_data_file)
            display('')

            display('Applications:')
            display('')

            app_reporter = reporters.Reporter((
                ('Name', lambda entry_point, _: entry_point.name, True),
                ('Class', lambda _, cls: cls.__module__ + '.' + cls.__name__, True),
                ('Package', lambda entry_point, _: entry_point.dist.project_name, True),
                ('Class location', lambda _, cls: sys.modules[cls.__module__].__file__, True),
                ('Package location', lambda entry_point, _: entry_point.dist.location, True)
            ))

            activated_columns = {'name', 'class', 'package'}
            if location:
                activated_columns.add('class location')
                activated_columns.add('package location')

            apps = services.Services(entry_points='nagare.applications').load_activated_plugins()
            app_reporter.report(activated_columns, apps, display=display)

            activated_columns = {'package', 'version'}
            if location:
                activated_columns.add('location')

            display('')
            display('Nagare packages:')
            display('')
            nagare_packages = [
                (dist,)
                for dist in pkg_resources.working_set
                if dist.project_name.startswith('nagare-') or (dist.project_name == 'nagare')
            ]
            reporters.PackagesReporter().report(activated_columns, nagare_packages, display=display)

            return 0
