#! /usr/bin/env python3
#
# hcron-show-log.py

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
import os.path
import sys
from sys import stderr
import traceback

jobs = {}
logs = []

HcronLog = namedtuple("HcronLog", "timestamp type username values")
Job = namedtuple("Job", "jobid jobgid, pjobid values childs")

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
        traceback.print_exc()
        return None

def load_logs(usernames, startdatetime, enddatetime):
    starttimestamp = datetime2timestamp(startdatetime)
    endtimestamp = datetime2timestamp(enddatetime)

    for line in open("/var/log/hcron/hcron.log"):
        line = line.strip()
        log = parse_logline(line)

        if not log:
            continue
        if log.timestamp < starttimestamp or log.timestamp > endtimestamp:
            continue
        if usernames:
            if log.username != "" and log.username not in usernames:
                continue

        logs.append(log)

        if log.type == "queue":
            values = log.values
            jobid = values.pop("jobid", None)
            jobgid = values.pop("jobgid", None)
            pjobid = values.pop("pjobid", None)
            job = Job(jobid, jobgid, pjobid, values, [])
            if jobid == None:
                # something is wrong
                continue
            jobs[jobid] = job
            if jobid != pjobid:
                pjob = jobs.setdefault(pjobid, None)
                if pjob:
                    pjob.childs.append(jobid)

def show_job(jobid, depth=1):
    job = jobs[jobid]
    indent = "    "*depth
    print("%sjobid: %s" % (indent, jobid))
    print("%svalues: %s" % (indent, job.values))

def show_jobtree(jobid, depth=1):
    job = jobs[jobid]
    show_job(jobid, depth)
    for cjobid in job.childs:
        show_jobtree(cjobid, depth+1)

def show_logs(showtypes, showjobtree):
    for log in logs:
        if showtypes and log.type not in showtypes:
            continue
        print("%s %s %s %s" % (log.timestamp, log.type, log.username, log.values))
        if log.type == "activate":
            jobid = log.values.get("jobid")
            if showjobtree:
                jobgid = log.values.get("jobgid")
                if jobid == jobgid:
                    show_jobtree(jobid)
            else:
                show_job(jobid)

def print_usage():
    d = {
        "progname": os.path.basename(sys.argv[0])
    }
    print("""\
usage: %(progname)s [<options>] <startdatetime> <enddatetime>

Show log entries between <startdatetime> and <enddatetime> (specified
as YYYYMMDD[hhmm]).

Where:
<enddatetime>       Filter out entries after this date and time.
<startdatetime>     Filter out entries before this date and time.

Options:
--show-jobtree      Show job information as a tree grouped together by
                    job group.
--show-types <type>[,...]
                    Show entries for given types. Default is all types.
-u <username>[,...] Filter for users.""" % d)

if __name__ == "__main__":
    try:
        enddatetime = None
        showjobtree = False
        showtypes = None
        startdatetime = None
        usernames = None

        args = sys.argv[1:]

        while args:
            arg = args.pop(0)
            if arg == "-u" and args:
                usernames = set(args.pop(0).split(","))
            elif arg == "--show-jobtree":
                showjobtree = True
            elif arg == "--show-types" and args:
                showtypes = set(args.pop(0).split(","))
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif len(args) == 1:
                startdatetime = arg
                enddatetime = args.pop(0)
            else:
                raise Exception()

        if None in [enddatetime, startdatetime]:
            raise Exception()
    except SystemExit:
        raise
    except:
        #traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        load_logs(usernames, startdatetime, enddatetime)
        show_logs(showtypes, showjobtree)
    except:
        #traceback.print_exc()
        stderr.write("error: failed to run\n")
        sys.exit(1)
