#! /usr/bin/env python2
#
# hcron-info.py

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

"""Provide hcron related information.
Simply print the fully qualified host name of the executing machine.
"""

# system imports
import os
import os.path
import socket
import sys
from sys import stderr

# hcron imports
from hcron.constants import *
from hcron.library import whoami

def print_usage():
    d = {
        "progname": os.path.basename(sys.argv[0])
    }
    print("""\
usage: %(progname)s --allowed
       %(progname)s -es
       %(progname)s --fqdn
       %(progname)s -h|--help

Print hcron related information.

Where:
--allowed           Output "yes" if permitted to use hcron.
-es                 Event statuses.
--fqdn              Fully qualified hostname.""" % d)

def print_allowed():
    try:
        userName = whoami()
        userEventListsPath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, userName)

        if os.path.exists(userEventListsPath):
            print("yes")

    except Exception as detail:
        pass

def print_fqdn():
    try:
        print(socket.getfqdn())
    except Exception as detail:
        print("Error: Could not determine the fully qualified host name.")

def print_user_event_status():
    try:
        userName = whoami()
        userEventListsPath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, userName)

        print(open(userEventListsPath, "r").read(), end="")
    except Exception as detail:
        print("Error: Could not read event status information.")

if __name__ == "__main__":
    try:
        args = sys.argv[1:]

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
