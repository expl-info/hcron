#! /usr/bin/env python2
#
# hcron_info.py

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

"""Provide hcron related information.
Simply print the fully qualified host name of the executing machine.
"""

from __future__ import print_function

# system imports
import os
import os.path
import socket
import sys
from sys import stderr
import traceback

# hcron imports
from hcron.constants import *
from hcron.library import whoami

def print_usage():
    print("""\
usage: hcron info --allowed
       hcron info -es
       hcron info --fqdn
       hcron info -h|--help

Print hcron related information.

Where:
--allowed           Output "yes" if permitted to use hcron.
-es                 Event statuses.
--fqdn              Fully qualified hostname.""")

def print_allowed():
    try:
        username = whoami()
        usereventlistspath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, username)

        if os.path.exists(usereventlistspath):
            print("yes")

    except Exception as detail:
        #traceback.print_exc()
        pass

def print_fqdn():
    try:
        print(socket.getfqdn())
    except Exception as detail:
        #traceback.print_exc()
        stderr.write("error: could not determine the fully qualified host name\n")

def print_user_event_status():
    try:
        username = whoami()
        usereventlistspath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, username)

        print(open(usereventlistspath, "r").read(), end="")
    except Exception as detail:
        #traceback.print_exc()
        stderr.write("error: Could not read event status information\n")

def main(args):
    try:
        # expect at least 1 arg
        arg = args.pop(0)
        if arg == "--allowed":
            print_allowed()
        elif arg == "-es":
            print_user_event_status()
        elif arg == "--fqdn":
            print_fqdn()

        elif arg in ["-h", "--help"]:
            print_usage()
            sys.exit(0)
        else:
            raise Exception()
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    sys.exit(0)
