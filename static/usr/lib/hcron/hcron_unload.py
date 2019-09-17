#! /usr/bin/env python2
#
# hcron_unload.py

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

from hcron.constants import *
from hcron.event import signal_reload
from hcron.server import setup

def print_usage():
    print("""\
usage: hcron unload
       hcron unload -h|--help

Signal the hcron scheduler running on the local machine to unload one's
event files.""")

def main(args):
    try:
        while args:
            arg = args.pop(0)
            if arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            else:
                raise Exception()
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        setup()

        signal_reload(unload)
        now = datetime.datetime.now()
        next_interval = (now+datetime.timedelta(seconds=60)).replace(second=0,microsecond=0)
        print("Unload signalled for machine (%s) at next interval (%s; in %ss)." % (HOST_NAME, next_interval, (next_interval-now).seconds))
    except Exception as detail:
        #traceback.print_exc()
        stderr.write("error: failed to signal to unload events\n")
        sys.exit(1)

    sys.exit(0)
