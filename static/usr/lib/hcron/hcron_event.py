#! /usr/bin/env python2
#
# hcron_event.py

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

# system imports
import datetime
import os
import os.path
import subprocess
import sys
from sys import stderr
import traceback
try:
    # python2
    raw_input = raw_input
except:
    # python3
    raw_input = input

# app import
from hcron.constants import *
from hcron.event import signal_reload
from hcron.server import setup

# constants
EDITOR = os.environ.get("EDITOR", "vi")

def print_usage():
    print("""\
usage: hcron event [-c] [-y] <path> [...]
       hcron event -h|--help

Create/edit an hcron event file at the given path(s). Start editor
unless -c is specified.

Where:
-c                  Create event file. Do not start editor.
-y                  Reload after create/edit.""")

def main(args):
    try:
        createonly = False
        paths = None
        reloadevents = False

        while args:
            arg = args.pop(0)

            if arg == "-c":
                createonly = True
            elif arg == "-y":
                reloadevents = True
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            else:
                paths = [arg]+args
                del args[:]

        if paths == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    for path in paths:
        try:
            if not os.path.exists(path):
                f = open(path, "w")
                f.write(HCRON_EVENT_DEFINITION)
                f.close()

            if not createonly:
                subprocess.call([EDITOR, path])

        except Exception:
            stderr.write("error: problem creating/opening event file (%s)\n" % path)
            sys.exit(1)

    try:
        setup()

        if reloadevents or raw_input("Reload events (y/n)? ") == "y":
            signal_reload()
            now = datetime.datetime.now()
            next_interval = (now+datetime.timedelta(seconds=60)).replace(second=0,microsecond=0)
            print("Reload signalled for machine (%s) at next interval (%s; in %ss)." % (HOST_NAME, next_interval, (next_interval-now).seconds))
        else:
            print("Reload deferred.")
    except Exception:
        #traceback.print_exc()
        stderr.write("error: could not reload\n")
        sys.exit(1)

    sys.exit(0)
