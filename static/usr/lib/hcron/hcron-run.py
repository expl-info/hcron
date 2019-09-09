#! /usr/bin/env python2
#
# hcron-run.py

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
    d = {
        "progname": os.path.basename(sys.argv[0])
    }
    print("""\
usage: %(progname)s [<options>] <eventsdir> <startdatetime> <enddatetime>
       %(progname)s -h|--help

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
                    substitutions are applied.""" % d)

if __name__ == "__main__":
    try:
        confpath = None
        delay = 0
        enddatetime = None
        eventsdir = None
        startdatetime = None

        args = sys.argv[1:]
        while args:
            arg = args.pop(0)
            if arg == "-c" and args:
                confpath = args.pop(0)
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
        setup()

        globs.remote_execute_enabled = False
        globs.email_notify_enabled = False

        allowedUsers = [whoami()]

        minute = timedelta(minutes=1)
        now = startdatetime
        globs.clock.set(now)
        globs.simulate = True

        if confpath:
            constants.HCRON_CONFIG_PATH = os.path.realpath(confpath)
        else:
            etcdir = os.path.realpath("%s/../../etc" % os.path.dirname(sys.argv[0]))
            constants.HCRON_CONFIG_PATH = os.path.join(etcdir, "hcron/hcron-run.conf")
        globs.fqdn = eventsdir.split("/")[-2]

        globs.configfile = ConfigFile(constants.HCRON_CONFIG_PATH)
        globs.configfile.get()["log_path"] = None
        setup_logger()

        globs.eventlistlist = EventListList(allowedUsers)

        globs.server = Server(False)
        log_start()

        while now < enddatetime:
            globs.server.run_now("clock", "hcron-run", now)
            while globs.server.jobq.q.qsize():
                job = globs.server.jobq.get()
                globs.server.jobq.handle_job(job)
            time.sleep(delay)
            now += minute
            globs.clock.set(now)
    except:
        stderr.write("error: unexpected situation\n")
        sys.exit(1)

    sys.exit(0)
