# --
# Copyright (c) 2008-2024 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

import argcomplete

from nagare.admin import admin


class Completion(admin.Command):
    DESC = 'CLI auto-completion: `eval "$(nagare completion --<shell>)"`'
    WITH_CONFIG_FILENAME = False

    def set_arguments(self, parser):
        parser.add_argument(
            '-b', '--bash', action='store_const', const='bash', dest='shell', help='generate completion code for Bash'
        )
        parser.add_argument(
            '-z', '--zsh', action='store_const', const='zsh', dest='shell', help='generate completion code for Zsh'
        )
        parser.add_argument(
            '-f', '--fish', action='store_const', const='fish', dest='shell', help='generate completion code for Fish'
        )
        parser.add_argument(
            '-p',
            '--powershell',
            action='store_const',
            const='powershell',
            dest='shell',
            help='generate completion code for PowerShell',
        )

        super(Completion, self).set_arguments(parser)

    def _run(self, names, shell):
        shell = shell or os.path.basename(os.environ.get('SHELL', '')) or 'bash'

        shell_code = argcomplete.shellcode(['nagare', 'nagare-admin'], shell=shell)
        lines = [
            '            local IFS=" "; _alternative "$completions"'
            if shell == 'zsh' and line.lstrip().startswith('_describe')
            else line
            for line in shell_code.splitlines()
        ]
        print('\n'.join(lines))

        return 0
