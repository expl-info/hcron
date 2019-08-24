#! /usr/bin/env python2
#
# hcron/job.py

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

import errno
import os
import os.path
import pwd
import Queue
import stat
import time
import traceback

from clock import Clock
from hcron.constants import *
from hcron import globls
from hcron.event import handle_event
from hcron.logger import *

class Job:

    def __init__(self):
        self.jobid = None
        self.event = None
        self.eventname = None
        self.sched_datetime = None
        self.triggername = None

class JobQueue:

    def __init__(self):
        self.q = Queue.Queue(globls.config.get().get("jobq_size", JOBQ_SIZE))

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
                    username = pwd.getpwuid(uid).pw_name
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
                    eventlist = globls.eventListList.get(username)
                    if not eventlist:
                        log_message("error", "Cannot find eventlist for user (%s)" % username)
                        raise Exception()

                    event = eventlist.get(eventname)
                    if not event:
                        log_message("error", "Cannot find event by name (%s)" % eventname)
                        raise Exception()

                    job = Job()
                    job.triggername = "ondemand"
                    job.event = event
                    job.eventname = event.name
                    job.sched_datetime = clock.now()
                    self.q.put(job)
                    log_message("info", "Queued ondemand event (%s)" % eventname)
                except:
                    log_message("warning", "Failed to queue ondemand event (%s)" % eventname)
                finally:
                    if path:
                        os.remove(path)
            time.sleep(ENQUEUE_ONDEMAND_DELAY)

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def handle_jobs(self):
        """Read jobs from the job queue. This function is run in a
        separate thread.

        handle_event() is called for each event to run in an independent
        forked process.

        The main/parent process spawns a process for each event. Each
        event (with its chained events) runs in its own process. This
        allows Event to be simple (i.e., no process management, chain
        management).

        Process management (parent): we can regulate the number of
        processes running from here, based on the number of children.

        Chain management (child): we can track and call chain events
        from here based on the return values of the event.activate.
        """
        def reap_children(childPids):
            if not childPids:
                return

            while 1:
                try:
                    pid, status = os.waitpid(-1, os.WNOHANG)
                    if (pid, status) == (0, 0):
                        break
                    del childPids[pid]
                except OSError, detail:
                    if detail.errno == errno.ECHILD:
                        childPids.clear()
                        break

        childPids = {}
        max_activated_events = max(globls.config.get().get("max_activated_events", CONFIG_MAX_ACTIVATED_EVENTS), 1)

        while True:
            try:
                reap_children(childPids)
                job = self.q.get(timeout=5)
            except Queue.Empty:
                continue
            except Exception, detail:
                if self.q != None:
                    log_message("error", "Unexpected exception (%s)." % str(detail))
                return

            while len(childPids) >= max_activated_events:
                # reap 1+ child processes
                try:
                    # block-wait for one
                    pid, status = os.waitpid(-1, 0)
                    while pid != 0:
                        del childPids[pid]
                        # opportunistic clean up others without waiting
                        pid, status = os.waitpid(-1, os.WNOHANG)
                except OSError, detail:
                    log_message("warning", "Unexpected exception (%s)." % str(detail))
                    if detail.errno == errno.ECHILD:
                        childPids.clear()
                except Exception, detail:
                    traceback.print_exc()
                    log_message("error", "Unexpected exception (%s)." % str(detail))

            pid = os.fork()
            childPids[pid] = None

            if pid == 0:
                # child
                handle_event(job.triggername, job.event, job.sched_datetime)
                os._exit(0)
            else:
                # parent
                pass

            if 0:
                # reap remaining child processes
                while childPids:
                    try:
                        pid, status = os.waitpid(-1, 0)
                        del childPids[pid]
                    except Exception, detail:
                        traceback.print_exc()
                        log_message("error", "Unexpected exception (%s)." % str(detail))

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)
