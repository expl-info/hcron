#! /usr/bin/env python2
#
# hcron-event.py

# GPL--start
# This file is part of hcron
# Copyright (C) 2008-2010 Environment/Environnement Canada
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

# app import
from hcron.constants import *
from hcron.event import signal_reload

# constants
EDITOR = os.environ.get("EDITOR", "vi")

def print_usage():
    d = {
        "progname": os.path.basename(sys.argv[0])
    }
    print """\
usage: %(progname)s [-c] [-y] <path> [...]
       %(progname)s -h|--help

Create/edit an hcron event file at the given path(s). Start editor
unless -c is specified.

Where:
-c                  Create event file. Do not start editor.
-y                  Reload after create/edit.""" % d

if __name__ == "__main__":
    try:
        createonly = False
        reloadevents = False
        paths = None

        args = sys.argv[1:]
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
                args.insert(0, arg)
                paths = [arg]+args
                del args[:]

        if paths == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing arguments\n")
        sys.exit(1)

    for path in paths:
        try:
            if not os.path.exists(path):
                f = open(path, "w")
                f.write(HCRON_EVENT_DEFINITION)
                f.close()

            if not createonly:
                subprocess.call([EDITOR, path])

        except Exception as detail:
            stderr.write("error: problem creating/opening event file (%s)\n" % path)
            sys.exit(1)

    try:
        if reloadevents or raw_input("reload events (y/n)? ") == "y":
            signal_reload()
            now = datetime.datetime.now()
            next_interval = (now+datetime.timedelta(seconds=60)).replace(second=0,microsecond=0)
            print "Reload signalled for machine (%s) at next interval (%s; in %ss)." % (HOST_NAME, next_interval, (next_interval-now).seconds)
        else:
            print "Reload deferred."
    except Exception as detail:
        stderr.write("error: could not reload\n")
        #print detail
        sys.exit(1)
