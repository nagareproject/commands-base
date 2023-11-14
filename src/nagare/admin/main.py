# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
# PYTHON_ARGCOMPLETE_OK

import os

from . import complete


def run():
    if '_ARGCOMPLETE' in os.environ:
        complete.complete()

    from nagare.admin import run

    return run.run()