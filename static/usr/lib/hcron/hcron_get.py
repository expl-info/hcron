#! /usr/bin/env python2
#
# hcron_get.py

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

import os.path
import socket
import sys
from sys import stderr
import traceback

from hcron.constants import *
from hcron import globs
from hcron.library import whoami

def print_allowed(args):
    try:
        username = whoami()
        usereventlistspath = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, username)

        if os.path.exists(usereventlistspath):
            print("yes")
        else:
            print("no")
    except Exception:
        stderr.write("error: could not determine allowed value\n")
        sys.exit(1)
    sys.exit(0)

def print_fqdn(args):
    try:
        print(socket.getfqdn())
    except:
        stderr.write("error: could not determine the fully qualified host name\n")
        sys.exit(1)
    sys.exit(0)

def print_servername(args):
    try:
        print(globs.servername)
    except:
        stderr.write("error: could not determine servername\n")
        sys.exit(1)
    sys.exit(0)

def print_usage():
    print("""\
usage: hcron get <name>
       hcron get -h|--help

Get and print hcron information.

Where <name> is:
allowed             Is allowed to use hcron: yes or no.
fqdn                Fully qualified host name.
servername          Name of server for which events are scheduled.""")

def main(args):
    try:
        name = None

        while args:
            arg = args.pop(0)
            if arg == "--debug":
                globs.debug = True
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg in ["allowed", "fqdn", "servername"] and not args:
                name = arg
                break
            else:
                raise Exception()

        if name == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        if name == "allowed":
            print_allowed(args)
        elif name == "fqdn":
            print_fqdn(args)
        elif name == "servername":
            print_servername(args)
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: unexpected error\n")
        sys.exit(1)

    sys.exit(0)
