# --
# Copyright (c) 2008-2021 Net-ng.
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

import appdirs

from nagare import commands
from colorama import init, Fore, Style
from nagare.services.services import Services
from nagare.config import ConfigError, config_from_dict, config_from_file

NAGARE_KAKEMONO = r"""
 ,,       ;
  '; ''';'''''''
,,     ,' ,,,;,
 ';   '''''   '
   ,   ;  ;  ;
  ,;   ;  ;  ;
 ,;    ;  ;  ; ,
,;   ,;'  '  ',;

    ;
    ;   ,,,
 '''; ,;'  ;
    ;;'    ;
   ,;      ;
 ,;';      ;   ,
    ;      ',,;'
    '
"""

NAGARE_BANNER = r"""
 _   _
| \ | | __ _  __ _  __ _ _ __ ___
|  \| |/ _` |/ _` |/ _` | '__/ _ \
| |\  | (_| | (_| | (_| | | |  __/
|_| \_|\__,_|\__, |\__,_|_|  \___|
             |___/
                     http://naga.re
              http://www.nagare.org


""".lstrip('\n')  # noqa: W605, W291

NAGARE_COLOR = Fore.GREEN


def find_path(choices, name):
    choices = filter(None, choices + (os.getcwd(),))
    if name:
        choices = [os.path.join(dir, name) for dir in choices]

    return next(dropwhile(lambda dir: not os.path.isdir(dir), choices), '')


class Banner(object):
    def __init__(self, banner='', kakemono='', color=None, bright=False, padding='', file=None):
        self.banner = banner
        self.kakemono = kakemono.strip('\n').replace('|', ' ').splitlines()
        self.kakemono_width = max(map(len, self.kakemono)) if self.kakemono else 0
        self.color = color
        self.bright = bright
        self.padding = padding
        self.first = True
        self.file = file or sys.stderr

    def display(self, lines=''):
        if self.first:
            self.first = False
            self.display(self.banner.splitlines())

        for line in ([lines] if isinstance(lines, str) else lines):
            kakemono = self.kakemono.pop(0) if self.kakemono else (' ' * self.kakemono_width)
            self.file.write('{}{}{}{}{}{}\n'.format(
                self.color if self.color is not None else '',
                Style.BRIGHT if (self.color is not None) and self.bright else '',
                kakemono.ljust(self.kakemono_width),
                Style.RESET_ALL if self.color is not None else '',
                self.padding,
                line
            ))
            self.file.flush()

    def end(self):
        if not self.first:
            while self.kakemono:
                self.display()

    def __enter__(self):
        return self.display

    def __exit__(self, *args):
        self.end()


class ArgumentParser(commands.ArgumentParser):
    def __init__(self, banner, *args, **kw):
        super(ArgumentParser, self).__init__(*args, **kw)
        self.banner = banner

    def _print_message(self, message, file=None):
        self.banner.display(message.splitlines())

    def end(self):
        self.banner.end()

    def exit(self, status=0, message=None):
        if message:
            self._print_message('\n' + message)

        self.banner.end()

        super(ArgumentParser, self).exit(status)


class Command(commands.Command):
    """The base class of all the commands"""
    WITH_CONFIG_FILENAME = True
    WITH_STARTED_SERVICES = False
    SERVICES_FACTORY = Services

    def create_banner(self, names):
        if names.startswith('nagare-admin'):
            banner = Banner(NAGARE_BANNER, NAGARE_KAKEMONO, NAGARE_COLOR, True, '  ')
        else:
            banner = Banner()

        return banner

    @classmethod
    def _create_services(cls, config, config_filename, roots=(), global_config=None, create_application=False):
        root_path = find_path(roots, '')
        has_user_config, user_config = cls.get_user_data_file()

        global_config = dict(
            global_config or {},
            root=root_path, root_path=root_path,
            config_filename=config_filename or '',
            user_config_filename=user_config if has_user_config else ''
        )

        if not create_application:
            initial_config = config['application'].dict()
            initial_config['_global_config'] = global_config
            config['application']['_initial_config'] = initial_config

        return cls.SERVICES_FACTORY().load_plugins('services', config, global_config, True)

    @staticmethod
    def get_user_data_file():
        user_data_dir = appdirs.user_data_dir('nagare')
        user_data_file = os.path.join(user_data_dir, 'nagare.cfg')

        user_data_file = os.environ.get('NAGARE_USER_CONFIG', user_data_file)

        return os.path.isfile(user_data_file), user_data_file

    def _run(self, command_names, next_method=None, config_filename=None, **arguments):
        if self.WITH_CONFIG_FILENAME:
            has_user_data_file, user_data_file = self.get_user_data_file()

            config = config_from_file(user_data_file) if has_user_data_file else config_from_dict({})
            config.merge(config_from_file(config_filename))
        else:
            config = None

        services = self._create_services(config, config_filename)

        publisher = services.get('publisher')
        if self.WITH_STARTED_SERVICES and publisher:
            services(publisher.create_app)

        return services((next_method or self.run), **arguments)

    def execute(self, command_names=(), args=None):
        try:
            return super(Command, self).execute(command_names, args)
        except ConfigError as e:
            print(e)
            return -2

    def _create_parser(self, name):
        banner = self.create_banner(name)
        return ArgumentParser(banner, name, description=self.DESC)

    def set_arguments(self, parser):
        super(Command, self).set_arguments(parser)

        if self.WITH_CONFIG_FILENAME:
            parser.add_argument('config_filename', nargs='?', help='configuration file')

    def parse(self, parser, args):
        arguments = super(Command, self).parse(parser, args)

        if self.WITH_CONFIG_FILENAME:
            try:
                config_filename = arguments['config_filename']
                if config_filename is None:
                    config_filename = os.environ.get('NAGARE_CONFIG')

                if config_filename is None:
                    raise commands.ArgumentError("config filename missing")

                if not os.path.exists(config_filename):
                    raise commands.ArgumentError("config filename <%s> doesn't exist" % config_filename)

                arguments['config_filename'] = os.path.abspath(os.path.expanduser(config_filename))
            except commands.ArgumentError:
                parser.print_usage(sys.stderr)
                parser.end()
                raise

        return arguments

    def display_command(self, top_level, indent, display):
        display('{}- {}: {}'.format(' ' * (indent * 4), self.name, self.DESC))


class Commands(commands.Commands):
    def usage_name(self, ljust=0):
        return Style.BRIGHT + super(Commands, self).usage_name(ljust) + Style.RESET_ALL

    def create_banner(self, names):
        if names.startswith('nagare-admin'):
            banner = Banner(NAGARE_BANNER, NAGARE_KAKEMONO, NAGARE_COLOR, True, '  ')
        else:
            banner = Banner()

        return banner

    def _create_parser(self, name):
        return ArgumentParser(self.create_banner(name), name, description=self.DESC)

    def set_arguments(self, parser):
        parser.add_argument('-a', '--all', action='store_true', help='show all the sub-commands')
        super(Commands, self).set_arguments(parser)

    def run(self, command_names, all, subcommands):
        if subcommands or not all:
            return super(Commands, self).run(command_names, subcommands)

        with self.create_banner(' '.join(command_names)) as display:
            self.display_command(len(command_names) == 1, 0, display)

        return 0

    def usage(self, names):
        with self.create_banner(' '.join(names)) as display:
            super(Commands, self).usage(names, display)

    def display_command(self, top_level, indent, display):
        display('{}* {} ({})'.format(' ' * (indent * 4), self.name, self.DESC))
        display()

        for _, sub_command in sorted(self.items()):
            sub_command.display_command(False, indent + 1, display)
            if top_level:
                display()


class NagareCommands(Commands):
    DESC = 'Nagare commands'

# ---------------------------------------------------------------------------


def run():
    if (len(sys.argv) > 1) and os.path.isfile(sys.argv[-1]):
        try:
            config = config_from_file(sys.argv[-1], 1)
        except ConfigError:
            config = {}

        exec(config.get('services', {}).get('preload_command', ''))

    init()
    return NagareCommands(name='nagare-admin', entry_points='nagare.commands').execute()
