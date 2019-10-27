#
# threadpool/__init__.py
#

# license--start
#
# Copyright (c) 2016, John Marshall. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the author nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# license--end

"""ThreadPool class.
"""

class ThreadPool:
    """Manage a pool of threads used to run tasks. Tasks are added
    to a wait queue, scheduled to run when a worker is available,
    and the task return value is added to the done queue. Done tasks
    may be reaped from the done queue. The scheduling of threads to
    run may be enabled and disabled. At no time are running threads
    interrupted or terminated. A threadpool may be drained at any
    time to remove waiting tasks and halt further scheduling;
    running threads are waited on until they complete.
    """

    def __init__(self, nworkers):
        try:
            import Queue as queue
        except:
            import queue
        import threading

        self.nworkers = nworkers
        self.doneq = queue.Queue()
        self.enabled = True
        self.runs = set()
        self.waitq = queue.Queue()
        self.schedlock = threading.Lock()

    def __del__(self):
        self.enabled = False

    def _schedule(self):
        """Schedule task(s) on waiting queue if workers are
        available. Exiting tasks trigger a follow on scheduling
        operation.
        """
        import threading

        def _worker(key, fn, args, kwargs):
            rv = fn(*args, **kwargs)
            self.doneq.put((key, rv))
            self.runs.discard(threading.current_thread())
            self._schedule()

        try:
            self.schedlock.acquire()
            if self.enabled:
                while not self.waitq.empty() and len(self.runs) < self.nworkers:
                    args = self.waitq.get()
                    key = args[0]
                    key = key and str(key)
                    th = threading.Thread(target=_worker, name=key, args=args)
                    self.runs.add(th)
                    th.start()
        finally:
            self.schedlock.release()

    def add(self, key, fn, args=None, kwargs=None):
        """Add task to wait queue and trigger scheduler. Each tasks
        is associated with a key and optionally args and kwargs.
        """
        args = args != None and args or ()
        kwargs = kwargs != None and kwargs or {}
        self.waitq.put((key, fn, args, kwargs))
        self._schedule()

    def disable(self):
        """Disable scheduling of tasks. Does not affect running
        tasks.
        """
        self.enabled = False

    def drain(self, delay=0.5):
        """Disable scheduling, empty the wait queue, and wait until
        running tasks have completed.
        """
        import time

        self.disable()
        while not self.waitq.empty():
            self.waitq.get()
        while self.runs:
            time.sleep(delay)

    def enable(self):
        """Enable scheduling of tasks.
        """
        self.enabled = True
        self._schedule()

    def get_ndone(self):
        """Return number of completed tasks are waiting to be reaped.
        """
        return self.doneq.qsize()

    def get_nrunning(self):
        """Return number of running tasks.
        """
        return len(self.runs)

    def get_nwaiting(self):
        """Return number of waiting tasks.
        """
        return self.waitq.qsize()

    def get_nworkers(self):
        """Return number of workers.
        """
        return self.nworkers

    def has_done(self):
        """Return True is a task is done and ready to be reaped.
        """
        return self.doneq.qsize() > 0

    def has_running(self):
        """Return True if a task is currently running.
        """
        return self.runs and True or False

    def has_waiting(self):
        """Returns True if a task is waiting to be run.
        """
        return self.waitq.qsize() > 0

    def is_empty(self):
        """Returns whether there is at least 1 task in the waiting,
        running, or done state.
        """
        return not (self.has_waiting() or self.has_running() or self.has_done())

    def is_enabled(self):
        """Returns whether the scheduler is enabled.
        """
        return self.enabled

    def reap(self, block=True, timeout=None):
        """Reap result returning (key, value).
        """
        try:
            t = self.doneq.get(block, timeout)
        except:
            raise Exception("no results to reap")
        return t

    def set_nworkers(self, nworkers):
        """Adjust the number of worker threads. An increase takes
        immediate effect as new threads may be started. A decrease
        will take effect only as running threads exit.
        """
        self.nworkers = max(nworkers, 0)
        self._schedule()
