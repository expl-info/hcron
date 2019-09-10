#! /usr/bin/env python2
#
# hcron/server.py

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

"""Library of routines, classes, etc. for hcron.
"""

# system imports
from datetime import timedelta
import os
import sys
import threading
from time import sleep, time

# app imports
from hcron import globs
from hcron.constants import *
from hcron.event import EventListList, reload_events
from hcron.job import Job, JobQueue
from hcron.library import date_to_bitmasks
from hcron.logger import *

class Server:

    def __init__(self, threads=True):
        self.jobq = JobQueue()

        if threads:
            self.jobqth = threading.Thread(target=self.jobq.handle_jobs)
            self.jobqth.daemon = True
            self.jobqth.start()

            self.odth = threading.Thread(target=self.jobq.enqueue_ondemand_jobs)
            self.odth.daemon = True
            self.odth.start()
        else:
            self.jobqth = None
            self.odth = None

    def __del__(self):
        # will trigger jobqth to exit
        self.jobq = None

    def run(self, immediate=False):
        """Run scheduling loop.
        """
        now = globs.clock.now()
        next = now # special case
        triggerorigin = "hcron-scheduler"

        if immediate:
            # special case: run with the current "now" time instead of
            # waiting for the next interval
            log_trigger("immediate", triggerorigin)
            self.run_now("immediate", triggerorigin, now)

        while True:
            #
            # prep for next interval; increment by 1 minute relative
            # to previous minute (not now() which may have passed 1
            # minute to get work done!)
            #
            next = (next+MINUTE_DELTA).replace(second=0, microsecond=0)
            now = globs.clock.now()
            if next > now:
                # we need to wait
                delta = (next-now).seconds+1
            else:
                # we're behind, run immediately
                log_message("info", "behind schedule (%s), sheduling immediately" % (next-now))
                delta = 0
    
            log_sleep(delta)
            sleep(delta)
            now = globs.clock.now()
            log_message("info", "scheduling for next interval (%s)" % next)

            #
            # check and update as necessary
            #
            if globs.configfile.is_modified():
                ### this is a problem if we are behind schedule!!!
                log_message("info", "hcron.conf was modified")
                # restart
                globs.pidfile.remove()
                if "--immediate" not in sys.argv:
                    # do not miss current "now" time
                    sys.argv.append("--immediate")
                os.execv(sys.argv[0], sys.argv)
            if globs.allowfile.is_modified():
                log_message("info", "hcron.allow was modified")
                globs.allowfile.load()
                globs.eventlistlist = EventListList(globs.allowfile.get())
            if globs.signaldir.is_modified():
                log_message("info", "signalHome was modified")
                globs.signaldir.load()
                reload_events(globs.signaldir.get_modified_time())

            log_trigger("clock", triggerorigin)
            self.run_now("clock", triggerorigin, next)

    # TODO: should run_now fork so that the child handled the "now"
    # events and the parent returns to wait for the next "now"?
    def run_now(self, triggername, triggerorigin, now):
        """Run using the "now" time value.
        """
        #
        # match events and act
        #
        t0 = time()
        # hcron: 0=sun - 6=sat; isoweekday: 1=mon = 7=sun
        hcronWeekday = now.isoweekday() % 7
        datemasks = date_to_bitmasks(now.year, now.month, now.day, now.hour, now.minute, hcronWeekday)
        events = globs.eventlistlist.test(datemasks)
        if events:
            for event in events:
                job = Job()
                job.triggername = triggername
                job.triggerorigin = triggerorigin
                job.eventname = event.name
                job.eventchainnames = event.name
                job.sched_datetime = now
                job.username = event.username
                log_queue(job.jobid, job.jobgid, job.pjobid, job.triggername, job.triggerorigin, job.username, job.eventname, job.eventchainnames, job.sched_datetime)
                self.jobq.put(job)
        log_work(len(events), (time()-t0))

def setup():
    """Do general/common setup.

    Must be called by hcron-run and hcron-scheduler.
    """
    import socket
    from hcron.clock import Clock

    globs.clock = Clock()
    globs.fqdn = socket.getfqdn()
    globs.localhostname = [globs.fqdn, socket.gethostname(), "localhost"]
