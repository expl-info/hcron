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
import traceback

# app imports
from hcron import globs
from hcron.constants import *

# globals
logger = None

def setup_logger():
    global logger

    if globs.config.get("use_syslog", CONFIG_USE_SYSLOG):
        handler = logging.SysLogHandler()
    else:
        log_path = globs.config.get("log_path", CONFIG_LOG_PATH)
        if log_path:
            if not log_path.startswith("/"):
                log_path = os.path.join(HCRON_LOG_HOME, log_path)
            handler = logging.FileHandler(log_path)
        else:
            handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger("")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    log("start-logging")

def log(logtype, **kwargs):
    """Add log entry with all fields tagged with the field name.

    All calls should include in kwargs values for type, username is
    optional but always output. All other kwargs settings are provided
    in alphabetical order.
    """
    try:
        d = kwargs.copy()
        l = [
                globs.clock.now().isoformat(),
                logtype,
                d.pop("username", "")
        ]
        l.extend(["%s=%s" % t for t in sorted(d.items())])
        logger.info("|".join(l))
    except:
        try:
            l = [
                globs.clock.now().isoformat(),
                "error",
                "",
                "message=failed to log entry",
                "values=%s" % str(kwargs),
            ]
            logger.info("|".join(l))
        except:
            pass

# specific logging functions
def log_activate(username, jobid, jobgid, pjobid, triggername, triggerorigin, eventname, eventchainnames):
    log("activate", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        triggername=triggername, triggerorigin=triggerorigin,
        eventname=eventname, eventchain=eventchainnames)

def log_alarm(username, jobid, jobgid, pjobid, eventname, pid, message):
    log("alarm", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        eventname=eventname, pid=pid, message=message)

def log_discard_events(username, count):
    log("discard-events", username=username, count=count)

def log_done(username, jobid, jobgid, pjobid, eventname, nexteventnames, nexteventtype):
    nexteventnames = nexteventnames or []
    log("done", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        eventname=eventname, nnextevents=len(nexteventnames),
        nexteventnames=":".join(nexteventnames),
        nexteventtype=nexteventtype)

def log_end():
    log("end")

def log_execute(username, jobid, jobgid, pjobid, asuser, host, eventname, pid, spawn_elapsed, retVal):
    log("execute", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        asuser=asuser, host=host, eventname=eventname, pid=pid, elapsed="%f" % spawn_elapsed, rv=retVal)

def log_exit():
    log("exit")

def log_expire(username, jobid, jobgid, pjobid, triggername, triggerorigin, eventname, eventchainnames):
    log("expire", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        triggername=triggername, triggerorigin=triggerorigin,
        eventname=eventname, eventchain=eventchainnames)

def log_load_allow():
    log("load-allow")

def log_load_config():
    log("load-config")

def log_load_events(username, nevents, naccepted, nrejected, ntemplates, elapsed):
    log("load-events", username=username, nevents=nevents, naccepted=naccepted, nrejected=nrejected, ntemplates=ntemplates, elapsed="%f" % elapsed)

def log_message(typ, msg, username=""):
    log("message", username=username, type=typ, message=msg)

def log_notify_email(username, addrs, eventName):
    log("notify-email", username=username, addrs=addrs, eventname=eventName)

def log_queue(username, jobid, jobgid, pjobid, triggername, triggerorigin, eventname, eventchainnames, schedtime, queuetime):
    log("queue", username=username, jobid=jobid, jobgid=jobgid, pjobid=pjobid,
        triggername=triggername, triggerorigin=triggerorigin,
        eventname=eventname, eventchain=eventchainnames,
        schedtime=schedtime, queuetime=queuetime)

def log_sleep(seconds):
    log("sleep", sleeptime=seconds)

def log_start():
    log("start", version=VERSION, servername=globs.servername, fqdn=globs.fqdn)

def log_status(**kwargs):
    log("status", **kwargs)

def log_trigger(triggername, triggerorigin):
    log("trigger", triggername=triggername, triggerorigin=triggerorigin)

def log_work(count, elapsed):
    log("work", count=count, elapsed="%f" % elapsed)
