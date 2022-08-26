# Encoding: utf-8

# --
# Copyright (c) 2008-2022 Net-ng.
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
from nagare.packaging import Distribution
from nagare.services.services import Services
from nagare.services.reporters import Reporter, PackagesReporter


class Info(admin.Command):
    DESC = 'display runtime informations'
    WITH_CONFIG_FILENAME = False

    def set_arguments(self, parser):
        super(Info, self).set_arguments(parser)

        parser.add_argument(
            '-g', '--general', action='store_true', dest='general_info',
            help='display general informations'
        )

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

    def _create_services(self, *args, **kw):
        return self.SERVICES_FACTORY()

    @classmethod
    def run(cls, general_info, packages_info, services_info, applications_info, location, registrations, services_service):
        nb_sections = general_info + packages_info + services_info + applications_info
        if nb_sections == 0:
            general_info = packages_info = services_info = applications_info = True

        implementation = getattr(sys, 'subversion', None)
        if implementation:
            implementation = implementation[0]
        else:
            implementation = sys.implementation.name.capitalize()

        with admin.Banner(file=sys.stdout) as display:
            if general_info:
                display((implementation + ' ' + sys.version).splitlines())
                display()

                has_user_data_file, user_data_file = cls.get_user_data_file()
                display('User configuration [%sFOUND]: ' % ('NOT ' if not has_user_data_file else ''))
                display('')
                display('  ' + user_data_file)
                display('')

            if packages_info:
                if nb_sections != 1:
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
                for name, entry_point in services_service.iter_entry_points(None, 'nagare.services', {}):
                    services[entry_point.dist.project_name].append(name)

                package_reporter = PackagesReporter(
                    PackagesReporter.COLUMNS + (
                        ('Services', lambda dist, *args: ', '.join(sorted(services[dist.project_name])), True),
                    )
                )
                package_reporter.report(
                    activated_columns,
                    nagare_packages,
                    True,
                    display,
                    0 if nb_sections == 1 else 2
                )
                display('')

            if services_info:
                if nb_sections != 1:
                    display('Services:')
                    display('')

                service_reporter = Reporter((
                    (
                        'Name',
                        lambda level, name, e, c: ' ' * (4 * level) + name,
                        True
                    ),
                    (
                        'Order',
                        lambda l, n, e, cls: str(cls.LOAD_PRIORITY),
                        False
                    ),
                    (
                        'Package',
                        lambda l, n, entry_point, c: entry_point.dist.project_name,
                        True
                    ),
                    (
                        'Location',
                        lambda l, n, e, cls: '{}:{}'.format(sys.modules[cls.__module__].__file__, cls.__name__),
                        True
                    )
                ))

                activated_columns = {'name', 'order', 'package'}
                if location:
                    activated_columns.add('location')

                def extract_infos(plugins, level=0):
                    infos = []
                    for plugin in plugins:
                        f, (entry, name, cls, plugin, children) = plugin
                        infos.append((level, name, entry, cls))

                        for plugins in extract_infos(children, level + 1):
                            infos.append(plugins)

                    return infos

                services = services_service.walk1(
                    'services',
                    'nagare.services',
                    {},
                    {},
                    services_service.activated_by_default
                )

                service_reporter.report(
                    activated_columns,
                    extract_infos(services),
                    False,
                    display,
                    0 if nb_sections == 1 else 2
                )
                display('')

            if applications_info:
                if nb_sections != 1:
                    display('Applications:')
                    display('')

                app_reporter = Reporter((
                    ('Name', lambda name, entry_point, cls: name, True),
                    ('Class', lambda name, entry_points, cls: cls.__module__ + '.' + cls.__name__, True),
                    ('Package', lambda name, entry_point, cls: entry_point.dist.project_name, True),
                    ('Version', lambda name, entry_point, cls: entry_point.dist.version, True),
                    ('Class location', lambda name, entry_point, cls: sys.modules[cls.__module__].__file__, True),
                    (
                        'Package location',
                        lambda name, entry_point, cls: (
                            Distribution(entry_point.dist).editable_project_location or entry_point.dist.location
                        ),
                        True
                    )
                ))

                activated_columns = {'name', 'class', 'package', 'version'}
                if location:
                    activated_columns.add('class location')
                    activated_columns.add('package location')

                applications = Services()
                entry_points = applications.iter_entry_points(None, 'nagare.applications', {})
                applications = applications.load_entry_points(entry_points, {})

                app_reporter.report(
                    activated_columns,
                    applications,
                    True,
                    display,
                    0 if nb_sections == 1 else 2
                )

            return 0
