#! /usr/bin/env python
#
# hcron-reload.py

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

"""Signal to the hcron-scheduler to reload a user's event
definition files.
"""

# system imports
import datetime
import os
import os.path
import pwd
import shutil
import sys

# app imports
from hcron.constants import *
from hcron.event import signal_reload
from hcron.file import ConfigFile
from hcron import globls

def print_usage(progName):
    print """\
usage: %s [--unload]

Signal to the hcron-scheduler running of the local machine to reload
one's event defintion files. Use --unload to unload events at the
scheduler.""" % progName

if __name__ == "__main__":
    progName = os.path.basename(sys.argv[0])

    #
    # parse command line
    #
    unload = False

    args = sys.argv[1:]
    while args:
        arg = args.pop(0)
        if arg in [ "-h", "--help" ]:
            print_usage(progName)
            sys.exit(0)
        elif arg == "--unload":
            unload = True
        else:
            print_usage(progName)
            sys.exit(-1)

    #
    # work
    #
    try:
        signal_reload(unload)
        now = datetime.datetime.now()
        next_interval = (now+datetime.timedelta(seconds=60)).replace(second=0,microsecond=0)
        print "Reload signalled for machine (%s) at next interval (%s; in %ss)." % (HOST_NAME, next_interval, (next_interval-now).seconds)
    except Exception, detail:
        print detail
        sys.exit(-1)

    sys.exit(0)
