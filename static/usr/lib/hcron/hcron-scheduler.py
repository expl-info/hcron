#! /usr/bin/env python3
#! /usr/bin/env python2
#
# hcron-scheduler.py

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

"""This is the backend event scheduler. It is typically run by root
although it can be run by individual users, but with reduced
functionality (i.e., it only handlers the user's own events).
"""

# secure by restricting sys.path to /usr and first path entry
import sys
firstPath = sys.path[0]
sys.path = [ path for path in sys.path if path.startswith("/usr") ]
sys.path.insert(0, firstPath)
del firstPath

# system imports
import os.path
import signal
from sys import stderr
import tempfile
import traceback

# app imports
from hcron import globs
from hcron import library
from hcron.constants import *
from hcron.event import EventListList
from hcron.file import PidFile
from hcron.logger import *
from hcron.server import Server, setup
from hcron.trackablefile import AllowFile, ConfigFile, SignalDir

def dump_signal_handler(num, frame):
    log_message("info", "received signal to dump.")
    signal.signal(num, dump_signal_handler)

    try:
        library.makedirs(HCRON_DUMPDIR_BASE, 0o700)
        dumpdir = tempfile.mkdtemp(dir=HCRON_DUMPDIR_BASE)
        elsdumpdir = os.path.join(dumpdir, "event_lists")
        library.makedirs(elsdumpdir, 0o700)
    except:
        # something went wrong!
        return

    # config
    try:
        globs.configfile.dump(os.path.join(dumpdir, "hcron.conf"))
    except Exception:
        pass

    # allowed users
    try:
        globs.allowfile.dump(os.path.join(dumpdir, "hcron.allow"))
    except Exception:
        pass

    # event list
    try:
        ell = globs.eventlistlist
        for username in globs.allowfile.get():
            el = ell.eventlists.get(username)
            if el:
                el.dump(elsdumpdir)
    except:
        pass

    # threadpool information
    try:
        tp = globs.server.jobq.tp
        l = []
        l.append("ndone (%s)" % tp.get_ndone())
        l.append("nrunning (%s)" % tp.get_nrunning())
        l.append("nwaiting (%s)" % tp.get_nwaiting())
        l.append("nworkers (%s)" % tp.get_nworkers())
        l.append("\nrunning:")
        l.append("\n".join(["%s" % x for x in tp.runs]))
        open(os.path.join(dumpdir, "threadpool"), "w+").write("\n".join(l))
    except:
        pass

def reload_signal_handler(num, frame):
    log_message("info", "received signal to reload.")
    signal.signal(num, reload_signal_handler)
    globs.eventlistlist.load(globs.allowfile.get())

def quit_signal_handler(num, frame):
    log_message("info", "received signal to exit.")
    globs.pidfile.remove()
    sys.exit(0)

def print_usage():
    d = {
        "progname": os.path.basename(sys.argv[0])
    }
    print("""\
usage: %(progname)s [--immediate]
       %(progname)s -h|--help

This program loads a collection of event files from one or more users
and executes commands according their defined schedulues. When run as
root, event files are read from registered users (listed in hcron.allow)
for the local host. Otherwise, this is done for the current user, only.

Options:
--immediate         Forces the scheduling of events to be done
                    immediately (i.e., now, the current interval)
                    rather than wait for the next interval.""" % d)

if __name__ == "__main__":
    try:
        immediate = False

        args = sys.argv[1:]
        while args:
            arg = args.pop(0)
            if arg == "--immediate":
                immediate = True
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

    try:
        setup()

        globs.remote_execute_enabled = True
        globs.email_notify_enabled = True

        globs.configfile = ConfigFile(HCRON_CONFIG_PATH)
        setup_logger()
        globs.allowfile = AllowFile(HCRON_ALLOW_PATH)
        globs.signaldir = SignalDir(HCRON_SIGNAL_DIR)
        globs.eventlistlist = EventListList(globs.allowfile.get())

        signal.signal(signal.SIGHUP, reload_signal_handler)
        signal.signal(signal.SIGUSR1, dump_signal_handler)
        signal.signal(signal.SIGTERM, quit_signal_handler)
        signal.signal(signal.SIGQUIT, quit_signal_handler)
        ###signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # we don't care about children/zombies

        library.serverize()  # don't catch SystemExit

        globs.server = Server()
        globs.pidfile = PidFile(HCRON_PID_FILE_PATH)
        globs.pidfile.create()

        log_start()
        globs.server.run(immediate=immediate)
    except Exception as detail:
        log_message("error", "unexpected error (%s)." % detail)

    try:
        globs.pidfile.remove()
        log_exit()
    except:
        pass

    sys.exit(1)
