#! /usr/bin/env python
#
# hcron-run.py

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

from datetime import datetime, timedelta
import os
import os.path
import pwd
try:
    import cStringIO as StringIO
except:
    import StringIO
import sys
import tarfile
import time
import traceback

from hcron import constants
from hcron import globls
from hcron import event
from hcron.event import EventList, EventListList, handle_event
from hcron.file import ConfigFile
from hcron import hcrontree
from hcron.logger import *
from hcron.library import date_to_bitmasks

PROG_NAME = os.path.basename(sys.argv[0])

# override
def get_hcron_tree_filename(username, hostname):
    """Saved hcron tree file for user.
    """
    return eventsdir
hcrontree.get_hcron_tree_filename = get_hcron_tree_filename

def print_usage():
    print """\
usage: %s [<options>] <eventsdir> <startdatetime> <enddatetime>
       %s -h|--help

Simulate events that would fire. Events are taken from the eventsdir
directory and run over the period startdatetime to enddatetime (as
YYYYMMDD[hhmm]).

Chained events will fire, but failovers will not.

Options:
-c <confpath>   Path of the hcron configuration file. Default is to
                use the hcron-run.conf file provided with the
                package (which is usually sufficient).
-d <delay>      Delay (in seconds) to use between subsequent
                simulated datetimes for which there are events being
                fired. Default is 0s (no delay).
--show-all
--show-email
--show-event
                Show email and/or event information as it would be
                when an event fires. Early and late variable
                substitution are applied.""" % (PROG_NAME, PROG_NAME)

if __name__ == "__main__":
    whoami = pwd.getpwuid(os.getuid()).pw_name

    args = sys.argv[1:]
    try:
        confpath = None
        delay = 0
        enddatetime = None
        eventsdir = None
        startdatetime = None

        while args:
            arg = args.pop(0)
            if arg in ["-h", "--help"]:
                print_usage()
                sys.exit(1)
            elif arg == "-c" and args:
                confpath = args.pop(0)
            elif arg == "-d" and args:
                delay = max(0, float(args.pop(0)))
            elif arg in ["--show-all"]:
                globls.simulate_show_email = True
                globls.simulate_show_event = True
            elif arg in ["--show-email"]:
                globls.simulate_show_email = True
            elif arg in ["--show-event"]:
                globls.simulate_show_event = True
            elif len(args) == 2:
                eventsdir = os.path.realpath(arg)
                startdatetime = datetime.strptime((args.pop(0)+"0000")[:12], "%Y%m%d%H%M")
                enddatetime = datetime.strptime((args.pop(0)+"0000")[:12], "%Y%m%d%H%M")
            else:
                raise Exception()

        if None in [enddatetime, eventsdir, startdatetime]:
            raise Exception()
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        sys.stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    #
    # setup
    #
    globls.remote_execute_enabled = False
    globls.email_notify_enabled = False

    allowedUsers = [whoami]

    minute = timedelta(minutes=1)
    now = startdatetime
    globls.clock.set(now)
    globls.simulate = True

    if confpath:
        constants.HCRON_CONFIG_PATH = os.path.realpath(confpath)
    else:
        etcdir = os.path.realpath("%s/../../etc" % os.path.dirname(sys.argv[0]))
        constants.HCRON_CONFIG_PATH = os.path.join(etcdir, "hcron/hcron-run.conf")
    constants.HOST_NAME = eventsdir.split("/")[-2]

    globls.config = ConfigFile(constants.HCRON_CONFIG_PATH)
    globls.config.get()["log_path"] = None
    setup_logger()

    globls.eventListList = EventListList(allowedUsers)

    log_start()
    while now < enddatetime:
        hcronWeekday = now.isoweekday() % 7
        datemasks = date_to_bitmasks(now.year, now.month, now.day, now.hour, now.minute, hcronWeekday)
        events = globls.eventListList.test(datemasks)
        for event in events:
            handle_event(event, now)
            time.sleep(delay)
        now += minute
        globls.clock.set(now)
