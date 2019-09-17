#! /usr/bin/env python2
#
# hcron_show_fqdn.py

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

def print_usage():
    print("""\
usage: hcron show-fqdn
       hcron show-fqdn -h|--help

Print fully qualified hostname.""")

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
        print(socket.getfqdn())
    except:
        stderr.write("error: could not determine the fully qualified host name\n")
        sys.exit(1)

    sys.exit(0)
