#! /usr/bin/env python
#
# logger.py

"""This module provide routines for all supported logging operations.
"""

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

# system imports
import logging
import os.path
import sys

# app imports
from hcron.constants import *
from hcron import globls

# globals
logger = None

def setup_logger():
    global logger

    config = globls.config.get()
    if config.get("use_syslog", CONFIG_USE_SYSLOG):
        handler = logging.SysLogHandler()
    else:
        log_path = config.get("log_path", CONFIG_LOG_PATH)
        if log_path:
            if not log_path.startswith("/"):
                log_path = os.path.join(HCRON_LOG_HOME, log_path)
            handler = logging.FileHandler(log_path)
        else:
            handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger("")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    log_any("start-logging")

def log_any(*args):
    """Get around chicken and egg problem with logger.
    """
    global logger, log_any

    if logger:
        log_any = log_any2

def log_any2(op, userName="", *args):
    global logger

    if args:
        extra = "|".join([ str(el) for el in args ])
    else:
        extra = ""
    logger.info("%s|%s|%s|%s" % (globls.clock.now().isoformat(), op, userName, extra))

# specific logging functions
def log_alarm(msg=""):
    log_any("alarm", "", msg)

def log_chain_events(userName, eventName0, eventName1, eventChainNames, cycleDetected=False):
    cycleMsg = cycleDetected and "cycle" or ""
    log_any("chain-events", userName, eventName0, eventName1, ":".join(eventChainNames), cycleMsg)

def log_discard_events(userName, count):
    log_any("discard-events", userName, count)

def log_end():
    log_any("end")

def log_execute(userName, asUser, host, eventName, pid, spawn_elapsed, retVal):
    log_any("execute", userName, asUser, host, eventName, pid, spawn_elapsed, retVal)

def log_exit():
    log_any("exit")

def log_load_allow():
    log_any("load-allow")

def log_load_config():
    log_any("load-config")

def log_load_events(userName, count, elapsed):
    log_any("load-events", userName, count, elapsed)

def log_message(typ, msg, user_name=""):
    log_any("message", user_name, typ, msg)

def log_notify_email(userName, addrs, eventName):
    log_any("notify-email", userName, addrs, eventName)

def log_sleep(seconds):
    log_any("sleep", "", seconds)

def log_start():
    log_any("start")

def log_work(count, elapsed):
    log_any("work", "", count, elapsed)


