#! /usr/bin/env python
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
from hcron.constants import *
from hcron import globls
from hcron.logger import *
from hcron import fspwd as pwd

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

def remote_execute(eventName, localUserName, remoteUserName, remoteHostName, command, timeout=None):
    """Securely execute a command at remoteUserName@remoteHostName from
    localUserName@localhost within timeout time.

    Two approaches are coded below:
        1) poll+sleep
        2) signal+wait

    childPid is a module global, accessible to the alarm_handler.

    Return values:
    0   okay
    -1  error/failure
    """
    global childPid

    # setup
    config = globls.config.get()
    allow_localhost = config.get("allow_localhost", CONFIG_ALLOW_LOCALHOST) 
    allow_root_events = config.get("allow_root_events", CONFIG_ALLOW_ROOT_EVENTS)
    localUid = pwd.getpwnam(localUserName).pw_uid
    remote_shell_type = config.get("remote_shell_type", CONFIG_REMOTE_SHELL_TYPE)
    remote_shell_exec = config.get("remote_shell_exec", CONFIG_REMOTE_SHELL_EXEC)
    timeout = timeout or globls.config.get().get("command_spawn_timeout", CONFIG_COMMAND_SPAWN_TIMEOUT)
    command = command.strip()

    retVal = 0
    if globls.remote_execute_enabled:
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
        retVal = -1
        if command != "":
            try:
                args = [ remote_shell_exec, "-f", "-n", "-t", "-l", remoteUserName, remoteHostName, command ]
                #args = [ remote_shell_exec, "-n", "-t", "-l", remoteUserName, remoteHostName, command ]
                childPid = os.fork()

                if childPid == 0:
                    #
                    # child
                    #
                    try:
                        os.setuid(localUid)
                        os.setsid()
                        os.execv(args[0], args)
                        #retVal = subprocess.call(args)
                    except (OSError, Exception), detail:
                        os._exit(256)
                        retVal = 256

                    os._exit(retVal)

                    # NEVER REACHES HERE

                #
                # parent
                #
                if 0:
                    # poll and wait
                    while timeout > 0:
                        waitPid, waitStatus = os.waitpid(childPid, os.WNOHANG)

                        #if waitPid != 0 and os.WIFEXITED(waitStatus):
                        if waitPid != 0:
                            break

                        time.sleep(0.01)
                        timeout -= 0.01

                    else:
                        os.kill(childPid, signal.SIGKILL)

                else:
                    # signal and wait
                    signal.signal(signal.SIGALRM, alarm_handler)
                    signal.alarm(timeout)
                    waitPid, waitStatus = os.waitpid(childPid, 0)
                    signal.signal(signal.SIGALRM, signal.SIG_IGN) # cancel alarm

                if os.WIFSIGNALED(waitStatus):
                    retVal = -2

                elif os.WIFEXITED(waitStatus):
                    retVal = (os.WEXITSTATUS(waitStatus) == 255) and -1 or 0

            except Exception, detail:
                log_message("error", "Execute failed (%s)." % detail)

    log_execute(localUserName, remoteUserName, remoteHostName, eventName, retVal)

    return retVal

