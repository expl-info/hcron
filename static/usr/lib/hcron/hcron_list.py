#! /usr/bin/env python2
#
# hcron_list.py

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
import fnmatch
import re
import sys
from sys import stderr
import traceback

# hcron imports
from hcron.constants import *
from hcron.library import whoami

def print_usage():
    print("""\
usage: hcron list [<options>] [<pattern>]
       hcron list -h|--help

List (loaded) event names.

Where:
<pattern>           Event name pattern: * matches zero or more
                    characters; ? matches one character.

Options:
--show-all          Show all information for event.
--show-status       Show status for event.""")

def print_eventnames(pattern, showthings):
    try:
        cre = re.compile(fnmatch.translate(pattern))
    except:
        stderr.write("error: bad pattern\n")
        return

    try:
        username = whoami()
        usereventlistspath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, username)

        eventinfo = {}

        for line in open(usereventlistspath, "r").readlines():
            line = line.strip()
            status, evtype, reason, eventname = line.split(":", 3)
            if cre.match(eventname):
                l = []
                if "status" in showthings:
                    l.append(status)
                if "type" in showthings:
                    l.append(evtype)
                if "reason" in showthings:
                    l.append(reason)
                l.append(eventname)
                line = ":".join(l)
                eventinfo[eventname] = line
        for eventname, line in sorted(eventinfo.items()):
            print(line)
    except Exception:
        #traceback.print_exc()
        stderr.write("error: Could not read event status information\n")

def main(args):
    try:
        pattern = None
        showthings = set([])

        while args:
            arg = args.pop(0)
            if arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "--show-all":
                showthings.update(["status", "type", "reason"])
            elif arg == "--show-status":
                showthings.update(["status"])
            elif len(args) == 0:
                pattern = arg
            else:
                raise Exception()

        if pattern == None:
            pattern = "*"
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        print_eventnames(pattern, showthings)
    except:
        stderr.write("error: unexpected situation\n")
        sys.exit(1)

    sys.exit(0)
