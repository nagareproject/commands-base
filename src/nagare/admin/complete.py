# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os
import itertools
from argparse import ArgumentParser
from importlib import metadata
from collections import defaultdict

import argcomplete


def FilesCompleter():
    return (
        lambda **kw: ['files#file#_files']
        if os.environ['_ARGCOMPLETE_SHELL'] == 'zsh'
        else argcomplete.FilesCompleter()
    )


class ActiveParsers(list):
    def append(self, parser):
        entry_point = getattr(parser, 'entry_point', None)
        if entry_point is not None:
            entry_point.load()('', None).set_arguments(parser)

        return super().append(parser)


class CompletionFinder(argcomplete.CompletionFinder):
    @property
    def active_parsers(self):
        return self._active_parsers

    @active_parsers.setter
    def active_parsers(self, value):
        self._active_parsers = ActiveParsers()

    def _get_completions(self, *args):
        completions = super(CompletionFinder, self)._get_completions(*args)

        is_zsh = os.environ.pop('_ARGCOMPLETE_SHELL', '') == 'zsh'
        if (len(completions) != 1) or ('#' not in completions[0]):
            if is_zsh:
                completions = [
                    c + (f':"{self._display_completions[c]}"' if c in self._display_completions else '')
                    for c in completions
                ]
                completions = ['args:arguments:(({}))'.format('\013'.join(completions))]
        else:
            if is_zsh:
                completions = completions[0].split('#')
                completions = [':'.join(completions[:3])] + completions[3:]
            else:
                completions = []

        return completions


def complete():
    all_commands = defaultdict(dict)

    entry_points = metadata.entry_points()
    if hasattr(entry_points, 'values'):
        entry_points = itertools.chain(*entry_points.values())

    for entry in entry_points:
        if not entry.group.startswith('nagare.commands'):
            continue

        command = all_commands
        for command_name in entry.group.split('.')[2:] + [entry.name]:
            command = command.setdefault(command_name, defaultdict(dict, _entry=entry))

    def add_sub_parsers(parser, all_commands):
        subparsers = parser.add_subparsers()
        for command_name, command in all_commands.items():
            if not command_name.startswith('_'):
                subparser = subparsers.add_parser(command_name)
                if len(command) > 1:
                    add_sub_parsers(subparser, command)
                else:
                    subparser.entry_point = command['_entry']

        return parser

    CompletionFinder()(
        add_sub_parsers(ArgumentParser(), all_commands),
        always_complete_options=False,
        exclude=['-h', '--help'],
        default_completer=FilesCompleter(),
        validator=lambda completion, prefix: ('#' in completion) or (completion.startswith(prefix)),
    )

    return 0
