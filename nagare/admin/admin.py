# --
# Copyright (c) 2008-2020 Net-ng.
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

import configobj
from nagare import commands
from colorama import init, Fore, Style
from nagare.services.services import Services

KAKEMONO = r"""
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

BANNER = r"""
 _   _
| \ | | __ _  __ _  __ _ _ __ ___
|  \| |/ _` |/ _` |/ _` | '__/ _ \
| |\  | (_| | (_| | (_| | | |  __/
|_| \_|\__,_|\__, |\__,_|_|  \___|
             |___/
                     http://naga.re
              http://www.nagare.org


""".lstrip('\n')  # noqa: W605, W291


def find_path(choices, name):
    choices = filter(None, choices + (os.getcwd(),))
    if name:
        choices = [os.path.join(dir, name) for dir in choices]

    return next(dropwhile(lambda dir: not os.path.isdir(dir), choices), '')


class Banner(object):
    def __init__(self, banner=BANNER, padding='  ', file=None):
        self.banner = banner
        self.kakemono = KAKEMONO.strip('\n').replace('|', ' ').splitlines()
        self.kakemono_width = max(map(len, self.kakemono))
        self.padding = padding
        self.first = True
        self.file = file or sys.stderr

    def display(self, lines=''):
        if self.first:
            self.first = False
            self.display(self.banner.splitlines())

        for line in ([lines] if isinstance(lines, str) else lines):
            kakemono = self.kakemono.pop(0) if self.kakemono else (' ' * self.kakemono_width)
            self.file.write(''.join((
                Fore.GREEN, Style.BRIGHT,
                kakemono.ljust(self.kakemono_width),
                Style.RESET_ALL,
                self.padding, line,
                '\n')
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
    def __init__(self, *args, **kw):
        super(ArgumentParser, self).__init__(*args, **kw)
        self.banner = Banner()

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

    @classmethod
    def _create_services(cls, config, config_filename, roots=(), **vars):
        root_path = find_path(roots, '')

        env_vars = {k: v.replace('$', '$$') for k, v in os.environ.items()}
        env_vars.update(vars)

        has_user_config, user_config = cls.get_user_data_file()

        return cls.SERVICES_FACTORY(
            config, '', 'nagare.services',
            root=root_path, root_path=root_path,
            here=os.path.dirname(config_filename) if config_filename else '',
            config_filename=config_filename or '',
            user_config_filename=user_config if has_user_config else '',
            **env_vars
        )

    @staticmethod
    def get_user_data_file():
        user_data_dir = appdirs.user_data_dir('nagare')
        user_data_file = os.path.join(user_data_dir, 'nagare.cfg')

        user_data_file = os.environ.get('NAGARE_USER_CONFIG', user_data_file)

        return os.path.isfile(user_data_file), user_data_file

    def _run(self, command_names, next_method=None, config_filename=None, **arguments):
        if self.WITH_CONFIG_FILENAME:
            has_user_data_file, user_data_file = self.get_user_data_file()

            config = configobj.ConfigObj(user_data_file if has_user_data_file else {}, interpolation=False)
            config.merge(configobj.ConfigObj(config_filename, interpolation=False))
        else:
            config = None

        services = self._create_services(config, config_filename)

        publisher = services.get('publisher')
        if self.WITH_STARTED_SERVICES and publisher:
            services(publisher.create_app)

        return services((next_method or self.run), **arguments)

    def _create_parser(self, name):
        return ArgumentParser(name, description=self.DESC)

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

    def _create_parser(self, name):
        return ArgumentParser(name, description=self.DESC)

    def set_arguments(self, parser):
        parser.add_argument('-a', '--all', action='store_true', help='show all the sub-commands')
        super(Commands, self).set_arguments(parser)

    def run(self, command_names, all, subcommands):
        if subcommands or not all:
            return super(Commands, self).run(command_names, subcommands)

        with Banner() as display:
            self.display_command(len(command_names) == 1, 0, display)

        return 0

    def usage(self, names):
        with Banner() as display:
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
            config = configobj.ConfigObj(sys.argv[-1])
        except configobj.ConfigObjError:
            config = {}

        exec(config.get('services', {}).get('preload_command', ''))

    init()
    return NagareCommands(name='nagare-admin', entry_points='nagare.commands').execute()
