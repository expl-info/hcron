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

import socket
import sys
from sys import stderr
import traceback

def print_fqdn(args):
    try:
        print(socket.getfqdn())
    except:
        stderr.write("error: could not determine the fully qualified host name\n")
        sys.exit(1)
    sys.exit(0)

def print_usage():
    print("""\
usage: hcron get <name>
       hcron get -h|--help

Get and print hcron information.

Where <name> is:
fqdn                Fully qualified host name.""")

def main(args):
    try:
        name = None

        while args:
            arg = args.pop(0)
            if arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "fqdn" and not args:
                name = "fqdn"
                if args:
                    raise Exception()
                break
            else:
                raise Exception()

        if name == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        if name == "fqdn":
            print_fqdn(args)
    except SystemExit:
        raise
    except:
        stderr.write("error: unexpected error\n")
        sys.exit(1)

    sys.exit(0)
