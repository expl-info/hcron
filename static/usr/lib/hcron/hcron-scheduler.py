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
import pprint
import signal
from sys import stderr

# app imports
from hcron import globs
from hcron import library
from hcron.constants import *
from hcron.event import EventListList
from hcron.file import AllowedUsersFile, ConfigFile, PidFile, SignalHome
from hcron.logger import *
from hcron.server import Server

def dump_signal_handler(num, frame):
    log_message("info", "Received signal to dump.")
    signal.signal(num, dump_signal_handler)
    pp = pprint.PrettyPrinter(indent=4)

    # config
    try:
        config = globs.config.get()
        f = open(HCRON_CONFIG_DUMP_PATH, "w+")
        f.write(pp.pformat(config))
        f.close()
    except Exception as detail:
        if f != None:
            f.close()

    # allowed users
    try:
        allowedUsers = globs.allowedUsers.get()
        f = open(HCRON_ALLOWED_USERS_DUMP_PATH, "w+")
        f.write("\n".join(allowedUsers))
        f.close()
    except Exception as detail:
        if f != None:
            f.close()

    # event list
    ell = globs.eventlistlist
    for username in globs.allowedUsers.get():
        el = ell.eventlists.get(username)
        if el:
            el.dump()

def reload_signal_handler(num, frame):
    log_message("info", "Received signal to reload.")
    signal.signal(num, reload_signal_handler)
    globs.eventlistlist.load(globs.allowedUsers.get())

def quit_signal_handler(num, frame):
    log_message("info", "Received signal to exit.")
    globs.pidFile.remove()
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

    #
    # setup
    #
    globs.remote_execute_enabled = True
    globs.email_notify_enabled = True

    globs.config = ConfigFile(HCRON_CONFIG_PATH)
    setup_logger()
    globs.allowedUsers = AllowedUsersFile(HCRON_ALLOW_PATH)
    globs.signalHome = SignalHome(HCRON_SIGNAL_HOME)
    globs.eventlistlist = EventListList(globs.allowedUsers.get())

    signal.signal(signal.SIGHUP, reload_signal_handler)
    #signal.signal(signal.SIGUSR1, dump_signal_handler)
    signal.signal(signal.SIGTERM, quit_signal_handler)
    signal.signal(signal.SIGQUIT, quit_signal_handler)
    ###signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # we don't care about children/zombies

    library.serverize()  # don't catch SystemExit

    globs.server = Server()
    globs.pidFile = PidFile(HCRON_PID_FILE_PATH)
    globs.pidFile.create()

    try:
        log_start()
        globs.server.run(immediate=immediate)
    except Exception as detail:
        log_message("warning", "Unexpected exception (%s)." % detail)
        #import traceback
        #log_message("warning", "trace (%s)." % traceback.format_exc())
        #print(detail)
        pass

    globs.pidFile.remove()
    log_exit()
    sys.exit(-1)
