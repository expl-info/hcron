#! /usr/bin/env python2
#
# hcron_run.py

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

from datetime import datetime, timedelta
import os
import os.path
import sys
from sys import stderr
import time
import traceback

from hcron import constants
from hcron import globs
from hcron import hcrontree
from hcron.event import EventListList
from hcron.library import date_to_bitmasks, whoami
from hcron.logger import *
from hcron.server import Server, setup
from hcron.trackablefile import ConfigFile

# override
def get_hcron_tree_filename(username, hostname):
    """Saved hcron tree file for user.
    """
    return eventsdir
hcrontree.get_hcron_tree_filename = get_hcron_tree_filename

def print_usage():
    print("""\
usage: hcron run [<options>] <eventsdir> <startdatetime> <enddatetime>
       hcron run -h|--help

Simulate events that would execute. Events are taken from the <eventsdir>
directory and run over the period <startdatetime> to <enddatetime>
(specified as YYYYMMDD[hhmm]).

Chained events will execute, but failovers will not.

Options:
-c <confpath>       Path of the hcron configuration file. Default is to
                    use the hcron-run.conf file provided with the package
                    (which is usually sufficient).
-d <delay>          Delay (in seconds) to use between subsequent simulated
                    datetimes for which there are events being executed.
                    Default is 0s (no delay).
--fail-events <eventname>[:...]
                    Names of events that will fail.
--show-all
--show-email
--show-event
                    Show email and/or event information as it would be
                    when an event executes. Early and late variable
                    substitutions are applied.""")

def main(args):
    try:
        global eventsdir

        configpath = None
        delay = 0
        enddatetime = None
        eventsdir = None
        startdatetime = None

        while args:
            arg = args.pop(0)
            if arg == "-c" and args:
                configpath = args.pop(0)
            elif arg == "-d" and args:
                delay = max(0, float(args.pop(0)))
            elif arg == "--fail-events" and args:
                globs.simulate_fail_events = args.pop(0).split(":")
            elif arg == "--show-all":
                globs.simulate_show_email = True
                globs.simulate_show_event = True
            elif arg == "--show-email":
                globs.simulate_show_email = True
            elif arg == "--show-event":
                globs.simulate_show_event = True
            elif len(args) == 2:
                eventsdir = os.path.realpath(arg)
                startdatetime = datetime.strptime((args.pop(0)+"0000")[:12], "%Y%m%d%H%M")
                enddatetime = datetime.strptime((args.pop(0)+"0000")[:12], "%Y%m%d%H%M")
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(1)
            else:
                raise Exception()

        if None in [enddatetime, eventsdir, startdatetime]:
            raise Exception()

        if not os.path.isdir(eventsdir):
            stderr.write("error: events directory (%s) not valid\n" % eventsdir)
            sys.exit(1)

        if startdatetime > enddatetime:
            stderr.write("error: start time (%s) is after end time (%s)\n" % (startdatetime, enddatetime))
            sys.exit(1)
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        if configpath:
            configpath = os.path.realpath(configpath)
        else:
            etcdir = os.path.realpath("%s/../../etc" % os.path.dirname(sys.argv[0]))
            configpath = os.path.join(etcdir, "hcron/hcron-run.conf")

        setup(configpath)

        globs.remote_execute_enabled = False
        globs.email_notify_enabled = False

        allowedUsers = [whoami()]

        minute = timedelta(minutes=1)
        now = startdatetime
        globs.clock.set(now)
        globs.simulate = True

        globs.fqdn = eventsdir.split("/")[-2]

        globs.config["log_path"] = None
        setup_logger()

        globs.eventlistlist = EventListList(allowedUsers)

        globs.server = Server(False)
        log_start()

        jobq = globs.server.jobq
        while now < enddatetime:
            # queue up, then handle asynchronously in the threadpool
            globs.server.run_now("clock", "hcron-run", now)
            while jobq.tp.get_nwaiting()+jobq.tp.get_nrunning():
                time.sleep(0.00001)
            time.sleep(delay)
            now += minute
            globs.clock.set(now)
    except:
        stderr.write("error: unexpected error\n")
        sys.exit(1)

    sys.exit(0)
