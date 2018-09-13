# --
# Copyright (c) 2008-2018 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The ``nagare-admin`` executable
"""

import os
import sys
from itertools import dropwhile

from nagare import commands
from nagare.services.services import Services


BANNER = '''\
   _   _
  | \ | | __ _  __ _  __ _ _ __ ___
  |  \| |/ _` |/ _` |/ _` | '__/ _ \ 
  | |\  | (_| | (_| | (_| | | |  __/
  |_| \_|\__,_|\__, |\__,_|_|  \___|
               |___/

                http://www.nagare.org\
'''  # noqa: W291


def find_path(choices, name):
    choices = filter(None, choices + (os.getcwd(),))
    if name:
        choices = [os.path.join(dir, name) for dir in choices]

    return next(dropwhile(lambda dir: not os.path.isdir(dir), choices), '')


class ArgumentParser(commands.ArgumentParser):
    def format_help(self):
        return BANNER + '\n\n\n' + super(ArgumentParser, self).format_help()


class Command(commands.Command):
    """The base class of all the commands"""
    WITH_CONFIG_FILENAME = True
    WITH_STARTED_SERVICES = False
    SERVICES_FACTORY = Services

    @classmethod
    def _create_service(cls, config_filename, activated_by_default, roots=(), **vars):
        root_path = find_path(roots, '')

        env_vars = {k: v.replace('$', '$$') for k, v in os.environ.items()}
        env_vars.update(vars)

        return cls.SERVICES_FACTORY(
            config_filename, '', 'nagare.services', activated_by_default,
            root=root_path, root_path=root_path,
            here=os.path.dirname(config_filename) if config_filename else '',
            config_filename=config_filename or '',
            **env_vars
        )

    def _run(self, next_method=None, config_filename=None, **arguments):
        config = Services().read_config(
            {'activated_by_default': 'boolean(default=True)'},
            config_filename, 'services'
        )

        services = self._create_service(config_filename, config['activated_by_default'])

        publisher = services.get('publisher')
        if self.WITH_STARTED_SERVICES and publisher:
            services(publisher.create_app)

        return services((next_method or self.run), **arguments)

    def _create_parser(self, name):
        return ArgumentParser(name, description=self.DESC)

    def set_arguments(self, parser):
        super(Command, self).set_arguments(parser)

        if self.WITH_CONFIG_FILENAME:
            parser.add_argument('config_filename', nargs='?', help='Configuration file')

    def parse(self, command_name, args):
        parser, arguments = super(Command, self).parse(command_name, args)

        if self.WITH_CONFIG_FILENAME:
            try:
                config_filename = arguments['config_filename']
                if config_filename is None:
                    config_filename = os.environ.get('NAGARE_CONF')

                if config_filename is None:
                    raise commands.ArgumentError(message="config filename missing")

                if not os.path.exists(config_filename):
                    raise commands.ArgumentError(message="config filename <%s> doesn't exist" % config_filename)

                arguments['config_filename'] = os.path.abspath(os.path.expanduser(config_filename))
            except commands.ArgumentError:
                parser.print_usage(sys.stderr)
                raise

        return parser, arguments


class Commands(commands.Commands):
    def usage(self, names, args):
        print(BANNER + '\n\n')

        return super(Commands, self).usage(names, args)

# ---------------------------------------------------------------------------


def run():
    return Commands(entry_points='nagare.commands').execute()
