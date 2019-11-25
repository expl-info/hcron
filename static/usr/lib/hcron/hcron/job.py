#! /usr/bin/env python2
#
# hcron/job.py

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

from datetime import datetime
import errno
import os
import os.path
try:
    import Queue as queue
except:
    import queue
import stat
import time
import traceback

from hcron import globs
from hcron.clock import Clock
from hcron.constants import *
from hcron.event import get_event
from hcron.library import uid2username
from hcron.logger import *
from hcron.threadpool import ThreadPool

class Jobid:
    """Job id consisting of <48-bit time><16-bit counter>.
    """

    def __init__(self, tm, counter):
        self.tm = tm
        self.counter = counter
        self.value = (tm << 16)+counter

    def __str__(self):
        return "%x" % self.value

class JobidGenerator:
    """Generates unique job ids based on the time since epoch and a
    resetting 16-bit counter to produce a 64-bit number:
        <48-bit time><16-bit counter>
    """

    def __init__(self):
        self.counter = 0
        self.lasttm = 0

    def next(self):
        tm = int(time.time())
        if tm == self.lasttm:
            self.counter += 1
            if self.counter > 65500:
                # very unlikely, this is a problem!
                pass
        else:
            self.lasttm = tm
            self.counter = 0
        return Jobid(tm, self.counter)

jobidgen = JobidGenerator()

class Job:
    """Job corresponding to an event that has been triggered.

    The jobid is unique to each job. The jobgid is shared among all
    jobs that have the same parentage (via failover or next events).
    """

    def __init__(self, jobgid=None, pjobid=None):
        self.jobid = jobidgen.next()
        self.jobgid = jobgid or self.jobid
        self.pjobid = pjobid or self.jobid
        self.event = None
        self.eventchainnames = None
        self.eventname = None
        self.queue_datetime = None
        self.sched_datetime = None
        self.triggername = None
        self.triggerorigin = None
        self.username = None

class JobQueue:

    def __init__(self):
        #self.q = queue.Queue(globs.configfile.get().get("max_queued_jobs", CONFIG_MAX_QUEUED_JOBS))
        self.tp = ThreadPool(max(globs.configfile.get().get("max_activated_events", CONFIG_MAX_ACTIVATED_EVENTS), 1))

    def enqueue_ondemand_jobs(self):
        """Queue up on demand jobs.

        TODO: track if a file without a sentinel has been around for
        many iterations.
        """
        clock = Clock()

        while True:
            clock.set(None)
            for filename in sorted(os.listdir(HCRON_ONDEMAND_HOME)):
                try:
                    path = os.path.join(HCRON_ONDEMAND_HOME, filename)
                    st = os.stat(path)
                    uid = st[stat.ST_UID]
                    username = uid2username(uid)
                    triggerorigin = "%s@%s" % (username, globs.fqdn)
                    log_trigger("ondemand", triggerorigin)
                    log_message("debug", "filename (%s) user (%s) path (%s)" % (filename, username, path))

                    if st.st_size > 4096:
                        # too long
                        log_message("error", "filename (%s) user (%s) too big (%s)" % (filename, user, st.st_size))
                        raise Exception()

                    eventname = open(path).read(4096)
                    if not eventname.endswith("\n"):
                        # no sentinel; skip it
                        log_message("debug", "skipping filename (%s) user (%s) path (%s)" % (filename, username, path))
                        path = None
                        continue

                    eventname = eventname.strip()
                    try:
                        event = get_event(username, eventname)
                    except:
                        log_message("error", "cannot get event (%s) for user (%s)" % (eventname, username))
                        continue

                    job = Job()
                    job.triggername = "ondemand"
                    job.triggerorigin = triggerorigin
                    job.eventname = event.name
                    job.eventchainnames = event.name
                    job.queue_datetime = datetime.now()
                    job.sched_datetime = clock.now()
                    job.username = username
                    self.put(job)
                    log_queue(job.username, job.jobid, job.jobgid, job.pjobid,
                        job.triggername, job.triggerorigin, job.eventname,
                        job.eventchainnames, job.sched_datetime, job.queue_datetime)
                except:
                    log_message("warning", "failed to queue ondemand event (%s)" % eventname)
                finally:
                    if path:
                        os.remove(path)
            time.sleep(ENQUEUE_ONDEMAND_DELAY)

    def handle_job(self, job):
        """Handle a single job and queue related/followon chain jobs
        according to the event(s) defined.
        """
        try:
            event = get_event(job.username, job.eventname)
        except:
            log_message("error", "cannot get event (%s) for user (%s)" % (job.eventname, job.username))
            return

        max_chain_events = max(globs.configfile.get().get("max_chain_events", CONFIG_MAX_CHAIN_EVENTS), 1)
        max_next_events = max(globs.configfile.get().get("max_next_events", CONFIG_MAX_NEXT_EVENTS), 1)

        if job.eventchainnames:
            eventChainNames = job.eventchainnames.split(":")
        else:
            eventChainNames = []
        #eventChainNames.append(event.get_name())

        #log_message("info", "processing event (%s)." % event.get_name())
        try:
            # None, next_event, or failover_event is returned
            nexteventnames, nexteventtype = event.activate(job)
        except Exception as detail:
            log_message("error", "handle_job (%s)" % detail, username=event.username)
            nexteventnames, nexteventtype = [], None

        log_done(job.username, job.jobid, job.jobgid, job.pjobid, job.eventname,
            nexteventnames, nexteventtype)

        if nexteventnames:
            if len(eventChainNames) >= max_chain_events:
                log_message("error", "event chain limit (%s) reached at (%s)." % (max_chain_events, ":".join(nexteventnames)), username=event.username)
                return

            if len(nexteventnames) > max_next_events:
                log_message("error", "next event limit (%s) reached at (%s)." % (max_next_events, ":".join(nexteventnames)))
                return

            for nexteventname in nexteventnames:
                eventlist = globs.eventlistlist.get(event.username)
                nextevent = eventlist and eventlist.get(nexteventname)

                # problem cases for nextevent
                if nextevent == None:
                    log_message("error", "chained event (%s) does not exist." % nexteventname, username=event.username)
                elif nextevent.assignments == None and nextevent.reason not in [ None, "template" ]:
                    log_message("error", "chained event (%s) was rejected (%s)." % (nexteventname, nextevent.reason), username=event.username)
                    nextevent = None

                nextjob = Job(job.jobgid, job.jobid)
                nextjob.triggername = nexteventtype
                nextjob.triggerorigin = nextevent.name
                nextjob.eventname = nextevent.name
                nextjob.eventchainnames = "%s:%s" % (job.eventchainnames, nextjob.eventname)
                nextjob.queue_datetime = datetime.now()
                nextjob.sched_datetime = globs.clock.now()
                nextjob.username = job.username
                self.put(nextjob)
                log_queue(nextjob.username, nextjob.jobid, nextjob.jobgid, nextjob.pjobid,
                    nextjob.triggername, nextjob.triggerorigin, nextjob.eventname,
                    nextjob.eventchainnames, nextjob.sched_datetime, nextjob.queue_datetime)

    def handle_jobs(self):
        """Process jobs found on the job queue.
        """
        lastntotal = 0
        while True:
            try:
                try:
                    while self.tp.has_done():
                        res = self.tp.reap(timeout=1)
                    else:
                        res = self.tp.reap(timeout=2)
                except:
                    pass
                nqueued = self.tp.get_nwaiting()
                nrunning = self.tp.get_nrunning()
                ntotal = nqueued+nrunning
                if ntotal or lastntotal:
                    log_status(nqueued=nqueued, nrunning=nrunning, ntotal=ntotal)
                lastntotal = ntotal
            except Exception as detail:
                log_message("error", "unexpected exception (%s)." % str(detail))

    def put(self, job):
        """Enqueue the job.
        """
        try:
            if not isinstance(job, Job):
                raise Exception("not a job object")
            key = "%s--%s--%s" % (job.username, job.jobid, job.eventname)
            self.tp.add(key, self.handle_job, args=(job,))
        except:
            raise
