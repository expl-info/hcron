#! /usr/bin/env python3
#! /usr/bin/env python2
#
# hcron-frontend.py

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

"""Frontend.
"""

import sys
from sys import stderr
import traceback

from hcron.constants import VERSION

def print_usage():
    print("""\
usage: hcron <subcommand> ...
             -h|--help

Subcommands:
activate            Activate event.
conv                Convert between hcron and crontab.
doc                 Generate documentation for events.
event               Create/edit event.
get                 Get hcron information.
list                List events.
reload              Reload events.
run                 Simulate events.
show-log            Show log.
unload              Unload events.
version             Print version.

All subcommands except version support -h and --help to get help.""")

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        subcommand = args.pop(0)
        if subcommand in ["-h", "--help"]:
            print_usage()
            sys.exit(0)

        if subcommand == "activate":
            from hcron_activate import main
        elif subcommand == "conv":
            from hcron_conv import main
        elif subcommand == "doc":
            from hcron_doc import main
        elif subcommand == "event":
            from hcron_event import main
        elif subcommand == "get":
            from hcron_get import main
        elif subcommand == "list":
            from hcron_list import main
        elif subcommand == "reload":
            from hcron_reload import main
        elif subcommand == "run":
            from hcron_run import main
        elif subcommand == "show-log":
            from hcron_show_log import main
        elif subcommand == "unload":
            from hcron_unload import main
        elif subcommand == "version":
            print(VERSION)
            sys.exit(0)
        else:
            raise Exception()
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        main(args)
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: unexpected error\n")
        sys.exit(1)
