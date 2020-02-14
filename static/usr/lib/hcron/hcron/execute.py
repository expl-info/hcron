#! /usr/bin/env python2
#
# hcron/execute.py

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

"""Routines for handling command execution.
"""

# system imports
import os
import signal
import time

# app imports
from hcron import globs
from hcron.constants import *
from hcron.library import username2ids
from hcron.logger import *

class RemoteExecuteException(Exception):
    pass

def remote_execute(job, eventname, localusername, remoteusername, remotehostname, command, timeout=None):
    """Securely execute a command at remoteusername@remotehostname from
    localusername@localhost within timeout time.

    A poll+sleep approach is used.

    Return values:
    0   okay
    -1  error/failure
    """
    # setup
    allow_localhost = globs.config.get("allow_localhost", CONFIG_ALLOW_LOCALHOST) 
    allow_root_events = globs.config.get("allow_root_events", CONFIG_ALLOW_ROOT_EVENTS)
    localuid, localgid = username2ids(localusername)
    remote_shell_type = globs.config.get("remote_shell_type", CONFIG_REMOTE_SHELL_TYPE)
    remote_shell_exec = globs.config.get("remote_shell_exec", CONFIG_REMOTE_SHELL_EXEC)
    spawn_timeout = timeout or globs.config.get("command_spawn_timeout", CONFIG_COMMAND_SPAWN_TIMEOUT)
    kill_timeout = 10
    command = command.strip()
    spawn_starttime = time.time()

    if not globs.remote_execute_enabled:
        # simulation
        pid = 0
        rv = 0
    else:
        # validate
        if remotehostname in globs.localhostname and not allow_localhost:
            raise RemoteExecuteException("Execution on local host is not allowed.")
        if remotehostname == "":
            raise RemoteExecuteException("Missing host name for event (%s)." % eventname)
        if not allow_root_events and localuid == 0:
            raise RemoteExecuteException("Root user not allowed to execute.")
        if remote_shell_type != "ssh":
            raise RemoteExecuteException("Unknown remote shell type (%s)." % remote_shell_type)

        # spawn
        pid = 0
        rv = EXECUTE_FAILURE
        try:
            args = [remote_shell_exec, "-f", "-n", "-t", "-l", remoteusername, remotehostname, command]
            pid = os.fork()

            if pid == 0:
                ### child
                try:
                    os.setgid(localgid)
                    os.setuid(localuid)
                    os.setsid()
                    os.execv(args[0], args)
                except (OSError, Exception):
                    rv = EXECUTE_EXECFAIL
                os._exit(rv)

                # NEVER REACHES HERE

            ### parent
            # poll and wait
            elapsed = 0
            interval = 0.01
            while elapsed < spawn_timeout:
                waitpid, waitst = os.waitpid(pid, os.WNOHANG)
                if waitpid != 0:
                    break

                time.sleep(interval)
                elapsed += interval
            else:
                log_alarm(localusername, job.jobid, job.jobgid, job.pjobid, eventname, pid, "execute timeout expired (%s)" % spawn_timeout)

            # kill if timed out
            if waitpid == 0:
                elapsed = 0
                interval = 0.1
                while elapsed < kill_timeout:
                    os.kill(pid, signal.SIGKILL)
                    waitpid, waitst = os.waitpid(pid, os.WNOHANG)
                    if waitpid != 0:
                        break
                    time.sleep(interval)
                    elapsed += interval
                else:
                    log_alarm(localusername, job.jobid, job.jobgid, job.pjobid, eventname, pid, "kill timeout expired (%s)" % kill_timeout)

            # tailor rv
            if waitpid == 0:
                rv = EXECUTE_KILLFAIL
            else:
                if os.WIFSIGNALED(waitst):
                    rv = EXECUTE_SIGNALED
                elif os.WIFEXITED(waitst):
                    ev = os.WEXITSTATUS(waitst)
                    if ev == 0:
                        rv = EXECUTE_SUCCESS
                    elif ev == 255:
                        rv = EXECUTE_SSHFAIL
                    else:
                        rv = EXECUTE_FAILURE
        except Exception as detail:
            log_message("error", "execute failed (%s)." % detail)

        spawn_endtime = time.time()
        log_execute(localusername, job.jobid, job.jobgid, job.pjobid, remoteusername, remotehostname, eventname, pid, spawn_endtime-spawn_starttime, rv)

    return rv
