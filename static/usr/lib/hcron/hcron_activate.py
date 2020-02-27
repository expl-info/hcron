#! /usr/bin/env python2
#
# hcron_activate.py

# GPL--start
# This file is part of hcron
# Copyright (C) 2008-2019 Environment/Environnement Canada
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# GPL--end

"""Front-end to request an event be activated on demand.
"""

# system imports
import os
import sys
from sys import stderr
import tempfile
import traceback

# app imports
from hcron.constants import *
from hcron import globs

def print_usage():
    print("""\
usage: hcron activate <eventname>
       hcron activate -h|--help

Request for the named event to activate now.""")

def main(args):
    try:
        eventname = None

        while args:
            arg = args.pop(0)
            if arg == "--debug":
                globs.debug = True
            elif arg in [ "-h", "--help" ]:
                print_usage()
                sys.exit(0)
            elif not args:
                eventname = arg
            else:
                raise Exception()

        if eventname == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        fd, path = tempfile.mkstemp(dir=HCRON_ONDEMAND_HOME)
        os.write(fd, str.encode("%s\n" % eventname))
        os.close(fd)
    except Exception:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: unexpected error\n")
        sys.exit(1)

    sys.exit(0)
