#! /usr/bin/env python2
#
# execute.py

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

"""Routines for handling command execution.
"""

# system imports
import os
import signal
import subprocess
import time

# app imports
from hcron import globs
from hcron.constants import *
from hcron.library import username2uid
from hcron.logger import *

# global
childPid = None

class RemoteExecuteException(Exception):
    pass

def alarm_handler(signum, frame):
    """Terminate process with pid stashed in module childPid.
    """
    global childPid

    log_alarm("process (%s) to be killed" % childPid)
    try:
        os.kill(childPid, signal.SIGKILL)
        log_alarm("process (%s) killed" % childPid)
        return
    except:
        pass

    try:
        time.sleep(1)
        os.kill(childPid, 0)
        log_alarm("process (%s) could not be killed" % childPid)
    except:
        pass

def remote_execute(job, eventName, localUserName, remoteUserName, remoteHostName, command, timeout=None):
    """Securely execute a command at remoteUserName@remoteHostName from
    localUserName@localhost within timeout time.

    A poll+sleep approach is used.

    Return values:
    0   okay
    -1  error/failure
    """
    # setup
    config = globs.config.get()
    allow_localhost = config.get("allow_localhost", CONFIG_ALLOW_LOCALHOST) 
    allow_root_events = config.get("allow_root_events", CONFIG_ALLOW_ROOT_EVENTS)
    localUid = username2uid(localUserName)
    remote_shell_type = config.get("remote_shell_type", CONFIG_REMOTE_SHELL_TYPE)
    remote_shell_exec = config.get("remote_shell_exec", CONFIG_REMOTE_SHELL_EXEC)
    timeout = timeout or globs.config.get().get("command_spawn_timeout", CONFIG_COMMAND_SPAWN_TIMEOUT)
    command = command.strip()
    spawn_starttime = time.time()

    childPid = 0

    rv = 0
    if globs.remote_execute_enabled:
        # validate
        if remoteHostName in LOCAL_HOST_NAMES and not allow_localhost:
            raise RemoteExecuteException("Execution on local host is not allowed.")

        if remoteHostName == "":
            raise RemoteExecuteException("Missing host name for event (%s)." % eventName)

        if not allow_root_events and localUid == 0:
            raise RemoteExecuteException("Root user not allowed to execute.")

        if remote_shell_type != "ssh":
            raise RemoteExecuteException("Unknown remote shell type (%s)." % remote_shell_type)

        # spawn
        rv = -1
        if command != "":
            try:
                args = [ remote_shell_exec, "-f", "-n", "-t", "-l", remoteUserName, remoteHostName, command ]
                #args = [ remote_shell_exec, "-n", "-t", "-l", remoteUserName, remoteHostName, command ]
                childPid = os.fork()

                if childPid == 0:
                    ### child
                    try:
                        os.setuid(localUid)
                        os.setsid()
                        os.execv(args[0], args)
                    except (OSError, Exception) as detail:
                        rv = 256
                    os._exit(rv)

                    # NEVER REACHES HERE

                ### parent
                # poll and wait
                while timeout > 0:
                    waitPid, waitStatus = os.waitpid(childPid, os.WNOHANG)
                    if waitPid != 0:
                        break

                    time.sleep(0.01)
                    timeout -= 0.01
                else:
                    os.kill(childPid, signal.SIGKILL)

                if os.WIFSIGNALED(waitStatus):
                    rv = -2
                elif os.WIFEXITED(waitStatus):
                    rv = (os.WEXITSTATUS(waitStatus) == 255) and -1 or 0
            except Exception as detail:
                log_message("error", "Execute failed (%s)." % detail)

    spawn_endtime = time.time()
    log_execute(job.jobid, job.jobgid, localUserName, remoteUserName, remoteHostName, eventName, childPid, spawn_endtime-spawn_starttime, rv)

    return rv
