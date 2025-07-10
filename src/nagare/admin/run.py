# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The ``nagare-admin`` executable."""

import os
import sys

from colorama import init

from nagare import log
from nagare.config import ConfigError, config_from_file

from . import admin


def run():
    if (len(sys.argv) > 1) and os.path.isfile(sys.argv[-1]):
        config_filename = os.path.abspath(sys.argv[-1])
        here = os.path.dirname(config_filename)
        try:
            config = config_from_file(config_filename, {'here': here}, 1)
        except (UnicodeDecodeError, ConfigError):
            config = {}

        exec(config.get('services', {}).get('preload_command', ''))  # noqa: S102

    init()

    command_name = os.path.basename(sys.argv[0])
    if command_name == '__main__.py':
        command_name = 'nagare'

    try:
        commands = admin.NagareCommands(name=command_name, entry_points='nagare.commands')
        return commands.execute(
            args=(command_name.split('-')[2:] if command_name.startswith('nagare-commands') else []) + sys.argv[1:]
        )
    except Exception:
        log.get_logger('nagare.services.exceptions').error('Unhandled exception', exc_info=True)
        return -1
