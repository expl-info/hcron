#! /usr/bin/env python2
#
# hcron-scheduler.py

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

# app imports
from hcron.constants import *
from hcron import globls
from hcron.event import EventListList, handle_jobs
from hcron.file import AllowedUsersFile, ConfigFile, PidFile, SignalHome
from hcron import library
from hcron.logger import *
from hcron.server import Server

def dump_signal_handler(num, frame):
    log_message("info", "Received signal to dump.")
    signal.signal(num, dump_signal_handler)
    pp = pprint.PrettyPrinter(indent=4)

    # config
    try:
        config = globls.config.get()
        f = open(HCRON_CONFIG_DUMP_PATH, "w+")
        f.write(pp.pformat(config))
        f.close()
    except Exception, detail:
        if f != None:
            f.close()

    # allowed users
    try:
        allowedUsers = globls.allowedUsers.get()
        f = open(HCRON_ALLOWED_USERS_DUMP_PATH, "w+")
        f.write("\n".join(allowedUsers))
        f.close()
    except Exception, detail:
        if f != None:
            f.close()

    # event list
    ell = globls.eventListList
    for userName in globls.allowedUsers.get():
        el = ell.eventLists.get(userName)
        if el:
            el.dump()

def reload_signal_handler(num, frame):
    log_message("info", "Received signal to reload.")
    signal.signal(num, reload_signal_handler)
    globls.eventListList.load(globls.allowedUsers.get())

def quit_signal_handler(num, frame):
    log_message("info", "Received signal to exit.")
    globls.pidFile.remove()
    sys.exit(0)

def print_usage(progName):
    print """\
usage: %s [--immediate]

This program loads a collection of event definitions from one or
more users and executes commands according their defined schedulues.
When run as root, event definitions are read from registered users
(listed in hcron.allow) for the local host; otherwise, this is done
for the current user, only.

Options:
--immediate         Forces the scheduling of events to be done
                    immediately (i.e., now, the current interval)
                    rather than wait for the next interval""" % progName

if __name__ == "__main__":
    progName = os.path.basename(sys.argv[0])

    #
    # parse command line
    #
    args = sys.argv[1:]
    if len(args) > 0:
        if args[0] in [ "-h", "--help" ]:
            print_usage(progName)
            sys.exit(0)
        elif "--immediate" in args:
            # picked up by server.run()
            pass
        else:
            print_usage(progName)
            sys.exit(-1)

    #
    # setup
    #
    globls.remote_execute_enabled = True
    globls.email_notify_enabled = True

    globls.config = ConfigFile(HCRON_CONFIG_PATH)
    setup_logger()
    globls.allowedUsers = AllowedUsersFile(HCRON_ALLOW_PATH)
    globls.signalHome = SignalHome(HCRON_SIGNAL_HOME)
    globls.eventListList = EventListList(globls.allowedUsers.get())

    signal.signal(signal.SIGHUP, reload_signal_handler)
    #signal.signal(signal.SIGUSR1, dump_signal_handler)
    signal.signal(signal.SIGTERM, quit_signal_handler)
    signal.signal(signal.SIGQUIT, quit_signal_handler)
    ###signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # we don't care about children/zombies

    library.serverize()  # don't catch SystemExit

    globls.server = Server()
    globls.pidFile = PidFile(HCRON_PID_FILE_PATH)
    globls.pidFile.create()

    try:
        log_start()
        globls.server.run()
    except Exception, detail:
        log_message("warning", "Unexpected exception (%s)." % detail)
        #import traceback
        #log_message("warning", "trace (%s)." % traceback.format_exc())
        #print detail
        pass

    globls.pidFile.remove()
    log_exit()
    sys.exit(-1)
