#! /usr/bin/env python2
#
# server.py

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

"""Library of routines, classes, etc. for hcron.
"""

# system imports
from datetime import timedelta
import os
import Queue
import sys
import threading
from time import sleep, time

# app imports
from hcron.constants import *
from hcron import globls
from hcron.event import EventListList, handle_jobs, reload_events
from hcron.library import date_to_bitmasks
from hcron.logger import *

class Server:

    def __init__(self):
        self.jobq = Queue.Queue(globls.config.get().get("jobq_size", JOBQ_SIZE))
        self.jobqth = threading.Thread(target=handle_jobs, args=(self,))
        self.jobqth.daemon = True
        self.jobqth.start()

    def __del__(self):
        # will trigger jobqth to exit
        self.jobq = None

    def serverize(self):
        if os.fork() != 0:
            # exit original/parent process
            sys.exit(0)
   
        # close streams - the Python way
        sys.stdin.close(); os.close(0); os.open("/dev/null", os.O_RDONLY)
        sys.stdout.close(); os.close(1); os.open("/dev/null", os.O_RDWR)
        sys.stderr.close(); os.close(2); os.open("/dev/null", os.O_RDWR)
    
        # detach from controlling terminal
        os.setsid()
    
        # misc
        os.chdir("/")   # / is always available
        os.umask(0022)

    def run(self, immediate=False):
        """Run scheduling loop.
        """
        now = globls.clock.now()
        next = now # special case

        if immediate:
            # special case: run with the current "now" time instead of
            # waiting for the next interval
            self.run_now(now)

        while True:
            #
            # prep for next interval; increment by 1 minute relative
            # to previous minute (not now() which may have passed 1
            # minute to get work done!)
            #
            next = (next+MINUTE_DELTA).replace(second=0, microsecond=0)
            now = globls.clock.now()
            if next > now:
                # we need to wait
                delta = (next-now).seconds+1
            else:
                # we're behind, run immediately
                log_message("info", "behind schedule (%s), sheduling immediately" % (next-now))
                delta = 0
    
            log_sleep(delta)
            sleep(delta)
            now = globls.clock.now()
            log_message("info", "scheduling for next interval (%s)" % next)

            #
            # check and update as necessary
            #
            if globls.config.is_modified():
                ### this is a problem if we are behind schedule!!!
                log_message("info", "hcron.conf was modified")
                # restart
                globls.pidFile.remove()
                if "--immediate" not in sys.argv:
                    # do not miss current "now" time
                    sys.argv.append("--immediate")
                os.execv(sys.argv[0], sys.argv)
            if globls.allowedUsers.is_modified():
                log_message("info", "hcron.allow was modified")
                globls.allowedUsers.load()
                globls.eventListList = EventListList(globls.allowedUsers.get())
            if globls.signalHome.is_modified():
                log_message("info", "signalHome was modified")
                globls.signalHome.load()
                reload_events(globls.signalHome.get_modified_time())

            self.run_now(next)

    # TODO: should run_now fork so that the child handled the "now"
    # events and the parent returns to wait for the next "now"?
    def run_now(self, now):
        """Run using the "now" time value.
        """
        #
        # match events and act
        #
        t0 = time()
        # hcron: 0=sun - 6=sat; isoweekday: 1=mon = 7=sun
        hcronWeekday = now.isoweekday() % 7
        datemasks = date_to_bitmasks(now.year, now.month, now.day, now.hour, now.minute, hcronWeekday)
        events = globls.eventListList.test(datemasks)
        if events:
            for event in events:
                self.jobq.put((event, now))
        log_work(len(events), (time()-t0))
