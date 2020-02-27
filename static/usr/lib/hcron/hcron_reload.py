#! /usr/bin/env python2
#
# hcron_reload.py

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

"""Signal to the hcron-scheduler to reload/unload a user's event
files.
"""

import datetime
import sys
from sys import stderr
import traceback

from hcron import globs
from hcron.event import signal_reload
from hcron.server import setup

def print_usage():
    print("""\
usage: hcron reload
       hcron reload -h|--help

Signal the hcron scheduler running on the local machine to reload one's
event files.""")

def main(args):
    try:
        while args:
            arg = args.pop(0)
            if arg == "--debug":
                globs.debug = True
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            else:
                raise Exception()
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        setup()

        signal_reload()
        now = datetime.datetime.now()
        next_interval = (now+datetime.timedelta(seconds=60)).replace(second=0,microsecond=0)
        print("Reload signalled for servername (%s) on host/fqdn (%s) at next interval (%s; in %ss)." % (globs.servername, globs.fqdn, next_interval, (next_interval-now).seconds))
    except Exception:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: failed to signal to reload events\n")
        sys.exit(1)

    sys.exit(0)
