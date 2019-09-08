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
from hcron.library import username2uid
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
    config = globs.configfile.get()
    allow_localhost = config.get("allow_localhost", CONFIG_ALLOW_LOCALHOST) 
    allow_root_events = config.get("allow_root_events", CONFIG_ALLOW_ROOT_EVENTS)
    localuid = username2uid(localusername)
    remote_shell_type = config.get("remote_shell_type", CONFIG_REMOTE_SHELL_TYPE)
    remote_shell_exec = config.get("remote_shell_exec", CONFIG_REMOTE_SHELL_EXEC)
    timeout = timeout or config.get("command_spawn_timeout", CONFIG_COMMAND_SPAWN_TIMEOUT)
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
        rv = -1
        try:
            args = [remote_shell_exec, "-f", "-n", "-t", "-l", remoteusername, remotehostname, command]
            pid = os.fork()

            if pid == 0:
                ### child
                try:
                    os.setuid(localuid)
                    os.setsid()
                    os.execv(args[0], args)
                except (OSError, Exception) as detail:
                    rv = 256
                os._exit(rv)

                # NEVER REACHES HERE

            ### parent
            # poll and wait
            while timeout > 0:
                waitpid, waitst = os.waitpid(pid, os.WNOHANG)
                if waitpid != 0:
                    break

                time.sleep(0.01)
                timeout -= 0.01
            else:
                os.kill(pid, signal.SIGKILL)

            if os.WIFSIGNALED(waitst):
                rv = -2
            elif os.WIFEXITED(waitst):
                rv = (os.WEXITSTATUS(waitst) == 255) and -1 or 0
        except Exception as detail:
            log_message("error", "Execute failed (%s)." % detail)

        spawn_endtime = time.time()
        log_execute(job.jobid, job.jobgid, localusername, remoteusername, remotehostname, eventname, pid, spawn_endtime-spawn_starttime, rv)

    return rv
