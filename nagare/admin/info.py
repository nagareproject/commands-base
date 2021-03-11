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
from collections import defaultdict

import pkg_resources

from nagare.admin import admin
from nagare.services.services import Services
from nagare.services.reporters import Reporter, PackagesReporter


class Info(admin.Command):
    DESC = 'display runtime informations'
    WITH_CONFIG_FILENAME = False

    def set_arguments(self, parser):
        super(Info, self).set_arguments(parser)

        parser.add_argument(
            '-p', '--packages', action='store_true', dest='packages_info',
            help='display packages informations'
        )

        parser.add_argument(
            '-s', '--services', action='store_true', dest='services_info',
            help='display services informations'
        )

        parser.add_argument(
            '-a', '--applications', action='store_true', dest='applications_info',
            help='display applications informations'
        )

        parser.add_argument(
            '-l', '--location', action='store_true',
            help='display Nagare package locations'
        )

        parser.add_argument(
            '-r', '--registrations', action='store_true',
            help='display the services registered by the Nagare packages'
        )

    @classmethod
    def run(cls, packages_info, services_info, applications_info, location, registrations, services_service):
        if not packages_info and not services_info and not applications_info:
            packages_info = services_info = applications_info = True

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

            if packages_info:
                display('')
                display('Nagare packages:')
                display('')

                activated_columns = {'package', 'version'}
                if location:
                    activated_columns.add('location')

                if registrations:
                    activated_columns.add('services')

                nagare_packages = [
                    (dist,)
                    for dist in pkg_resources.working_set
                    if dist.project_name.startswith('nagare-') or (dist.project_name == 'nagare')
                ]

                services = defaultdict(list)
                for entry_point in services_service.iter_entry_points():
                    services[entry_point.dist.project_name].append(entry_point.name)

                package_reporter = PackagesReporter(
                    PackagesReporter.COLUMNS + (
                        ('Services', lambda dist, *args: ', '.join(sorted(services[dist.project_name])), True),
                    )
                )
                package_reporter.report(activated_columns, nagare_packages, display=display)

            if services_info:
                display('')
                display('Services:')
                display('')

                service_reporter = Reporter((
                    ('Name', lambda entry_point, _: entry_point.name, True),
                    ('Package', lambda entry_point, _: entry_point.dist.project_name, True),
                    (
                        'Location',
                        lambda entry_point, cls: '{}:{}'.format(sys.modules[cls.__module__].__file__, cls.__name__),
                        True
                    )
                ))

                activated_columns = {'name', 'package'}
                if location:
                    activated_columns.add('location')

                service_reporter.report(
                    activated_columns,
                    services_service.load_activated_plugins(),
                    display=display
                )

            if applications_info:
                display('')
                display('Applications:')
                display('')

                app_reporter = Reporter((
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

                apps = Services(entry_points='nagare.applications').load_activated_plugins()
                app_reporter.report(activated_columns, apps, display=display)

            return 0
