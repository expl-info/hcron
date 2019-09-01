#! /usr/bin/env python2
#
# hcron/logger.py

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

"""This module provide routines for all supported logging operations.
"""

# system imports
import logging
import os.path
import sys

# app imports
from hcron import globs
from hcron.constants import *

# globals
logger = None

def setup_logger():
    global logger

    config = globs.config.get()
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

def log_any2(op, username="", *args):
    global logger

    if args:
        extra = "|".join([ str(el) for el in args ])
    else:
        extra = ""
    logger.info("%s|%s|%s|%s" % (globs.clock.now().isoformat(), op, username, extra))

# specific logging functions
def log_activate(jobid, jobgid, triggername, username, eventname, eventchainnames):
    log_any("activate", jobid, jobgid, triggername, username, eventname, eventchainnames)

def log_alarm(msg=""):
    log_any("alarm", "", msg)

def log_discard_events(username, count):
    log_any("discard-events", username, count)

def log_end():
    log_any("end")

def log_execute(jobid, jobgid, username, asUser, host, eventName, pid, spawn_elapsed, retVal):
    log_any("execute", jobid, jobgid, username, asUser, host, eventName, pid, "%f" % spawn_elapsed, retVal)

def log_exit():
    log_any("exit")

def log_load_allow():
    log_any("load-allow")

def log_load_config():
    log_any("load-config")

def log_load_events(username, count, elapsed):
    log_any("load-events", username, count, "%f" % elapsed)

def log_message(typ, msg, user_name=""):
    log_any("message", user_name, typ, msg)

def log_notify_email(username, addrs, eventName):
    log_any("notify-email", username, addrs, eventName)

def log_queue(jobid, jobgid, triggername, username, eventname, eventchainnames, queuetime):
    log_any("queue", jobid, jobgid, triggername, username, eventname, eventchainnames, queuetime)

def log_sleep(seconds):
    log_any("sleep", "", seconds)

def log_start():
    log_any("start")

def log_trigger(triggername, triggerorigin):
    log_any("trigger", triggername, triggerorigin)

def log_work(count, elapsed):
    log_any("work", "", count, "%f" % elapsed)


