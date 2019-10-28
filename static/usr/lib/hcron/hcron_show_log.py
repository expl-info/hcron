#! /usr/bin/env python3
#
# hcron_show_log.py

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

from collections import namedtuple
from datetime import datetime
import os.path
import re
import sys
from sys import stderr
import traceback

SHOWLOG_FMT = "%s %s %s %s"
STRPTIME_DATETIME = "%Y-%m-%d %H:%M:%S"
STRPTIME_DATETIMEDEC = "%Y-%m-%d %H:%M:%S.%f"

jobs = {}
logs = []

HcronLog = namedtuple("HcronLog", "timestamp type username values")
Job = namedtuple("Job", "jobid jobgid, pjobid type2log childs")

def add_stats(jobid):
    """Add "stats" pseudo log entry.
    """
    job = jobs[jobid]

    queuelog = job.type2log.get("queue")
    activatelog = job.type2log.get("activate")
    expirelog = job.type2log.get("expire")
    executelog = job.type2log.get("execute")
    donelog = job.type2log.get("done")

    queuedatetime = queuelog and timestamp2datetime(queuelog.timestamp.replace("T", " "))
    activatedatetime = activatelog and timestamp2datetime(activatelog.timestamp.replace("T", " "))
    expiredatetime = expirelog and timestamp2datetime(expirelog.timestamp.replace("T", " "))
    executedatetime = executelog and timestamp2datetime(executelog.timestamp.replace("T", " "))
    donedatetime = donelog and timestamp2datetime(donelog.timestamp.replace("T", " "))

    values = {
        "jobid": jobid,
        "jobgid": job.jobgid,
        "pjobid": job.pjobid,
        "eventname": donelog.values.get("eventname"),
        "elapsed": None,
        "executetime": None,
        "spawntime": None,
        "waittime": None,
    }

    if queuedatetime:
        if donedatetime:
            values["elapsed"] = (donedatetime-queuedatetime).total_seconds()
        if activatedatetime:
            values["waittime"] = (activatedatetime-queuedatetime).total_seconds()
    if executedatetime:
        if donedatetime:
            values["executetime"] = (donedatetime-executedatetime).total_seconds()
        if activatedatetime:
            values["spawntime"] = (executedatetime-activatedatetime).total_seconds()

    log = HcronLog(donelog.timestamp, "stats", donelog.username, values)
    logs.append(log)

def datetime2timestamp(datetime):
    s = (datetime+"0000")[:12]
    year = s[:4]
    month = s[4:6]
    day = s[6:8]
    hour = s[8:10]
    minute = s[10:12]
    return "%s-%s-%sT%s:%s" % (year, month, day, hour, minute)

def parse_logline(line):
    #print(line)
    try:
        t = line.split("|")
        values = dict([tt.split("=", 1) for tt in t[3:]])
        log = HcronLog(t[0], t[1], t[2], values)
        return log
    except:
        #traceback.print_exc()
        pass

    try:
        # old format?
        values = dict([(str(i), tt) for i, tt in enumerate(t[3:])])
        log = HcronLog(t[0], t[1], t[2], values)
        return log
    except:
        #traceback.print_exc()
        return None

def load_logs(path, eventnamecre, usernames, starttimestamp, endtimestamp):
    joblogtypes = set(["queue", "activate", "expire", "execute", "done"])

    for line in open(path):
        line = line.strip()
        log = parse_logline(line)

        if not log:
            continue

        values = log.values
        eventname = values.get("eventname")

        if log.timestamp < starttimestamp or log.timestamp > endtimestamp:
            continue
        if usernames:
            if log.username != "" and log.username not in usernames:
                continue
        if eventname:
            if eventnamecre and not eventnamecre.match(eventname):
                continue

        logs.append(log)

        if log.type in joblogtypes:
            jobid = values.get("jobid", None)
            jobgid = values.get("jobgid", None)
            pjobid = values.get("pjobid", None)

            if jobid == None:
                # something is wrong
                continue

            job = jobs.get(jobid)
            if not job:
                job = jobs.setdefault(jobid, Job(jobid, jobgid, pjobid, {}, []))
            job.type2log[log.type] = log

            if jobid != pjobid:
                pjob = jobs.setdefault(pjobid, None)
                if pjob:
                    pjob.childs.append(jobid)

            if log.type == "done":
                add_stats(jobid)

def show_job(jobid, depth=1):
    job = jobs[jobid]
    indent = "    "*depth
    log = job.type2log.get("queue")
    print("%sjobid: %s" % (indent, jobid))
    print("%svalues: %s" % (indent, log.values))

def show_jobtree(jobid, depth=1):
    job = jobs[jobid]
    show_job(jobid, depth)
    for cjobid in job.childs:
        show_jobtree(cjobid, depth+1)

def show_logs(showtypes, showjobtree):
    for log in logs:
        if showtypes and log.type not in showtypes:
            continue
        print(SHOWLOG_FMT % (log.timestamp, log.type, log.username, log.values))
        if log.type == "activate":
            jobid = log.values.get("jobid")
            if showjobtree:
                jobgid = log.values.get("jobgid")
                if jobid == jobgid:
                    show_jobtree(jobid)
            else:
                show_job(jobid)

def timestamp2datetime(s):
    if s == None:
        return None
    elif "." in s:
        return datetime.strptime(s, STRPTIME_DATETIMEDEC)
    else:
        return datetime.strptime(s, STRPTIME_DATETIME)

def print_usage():
    print("""\
usage: hcron show-log [<options>] <startdatetime> [<enddatetime>]
       hcron show-log -h|--help

Show log entries between <startdatetime> and <enddatetime> (specified
as YYYYMMDD[hhmm]).

Where:
<enddatetime>       Filter out entries after this date and time.
<startdatetime>     Filter out entries before this date and time.

Options:
-e <pattern>        Filter by event name regexp pattern.
-f <path>           Use alternate log file.
--show-jobtree      Show job information as a tree grouped together by
                    job group.
--show-types <type>[,...]
                    Show entries for given types. Default is all types.
-u <username>[,...] Filter for users.""")

def main(args):
    try:
        enddatetime = None
        endtimestamp = None
        eventnamepatt = None
        logfilepath = "/var/log/hcron/hcron.log"
        showjobtree = False
        showtypes = None
        startdatetime = None
        starttimestamp = None
        usernames = None

        while args:
            arg = args.pop(0)
            if arg == "-e" and args:
                eventnamepatt = args.pop(0)
            elif arg == "-f" and args:
                logfilepath = args.pop(0)
            elif arg == "--show-jobtree":
                showjobtree = True
            elif arg == "--show-types" and args:
                showtypes = set(args.pop(0).split(","))
            elif arg == "-u" and args:
                usernames = set(args.pop(0).split(","))
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif len(args) in [0, 1]:
                startdatetime = arg
                if len(args) == 1:
                    enddatetime = args.pop(0)
                else:
                    enddatetime = "30000101"
            else:
                raise Exception()

        if None in [enddatetime, startdatetime]:
            raise Exception()

        starttimestamp = datetime2timestamp(startdatetime)
        endtimestamp = datetime2timestamp(enddatetime)
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        if not os.path.isfile(logfilepath):
            stderr.write("error: bad log file path (%s)" % (logfilepath,))
            sys.exit(1)

        try:
            if eventnamepatt:
                eventnamecre = re.compile(eventnamepatt)
            else:
                eventnamecre = None
        except:
            stderr.write("error: bad eventname pattern (%s)\n" % (eventnamepatt,))
            sys.exit(1)

        load_logs(logfilepath, eventnamecre, usernames, starttimestamp, endtimestamp)
        show_logs(showtypes, showjobtree)
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: failed to run\n")
        sys.exit(1)
