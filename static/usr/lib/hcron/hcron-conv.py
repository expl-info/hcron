#! /usr/bin/env python2
#
# hcron-conv.py

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

"""Convert between crontab and hcron formats.
"""

# system imports
import os
import os.path
import socket
import sys
from sys import stderr

# app import
from hcron.constants import *
from hcron.event import Event

def convert_to_events_main(args):
    """main for "--to-events".
    """
    try:
        crontabpath = None
        dirpath = None
        hostname = None
        mailaddr = ""

        while args:
            arg = args.pop(0)
            if arg in [ "--mail" ]:
                mailaddr = args.pop(0)
            elif len(args) == 2:
                hostname, crontabpath, dirpath = [arg]+args
                del args[:]
            else:
                raise Exception()

        if None in [crontabpath, dirpath, hostname]:
            raise Exception()

        convert_to_events(hostName, crontabPath, dirPath, mailAddr=mailaddr)
    except:
        raise

def convert_to_events(hostName, crontabPath, dirPath, mailAddr=""):
    try:
        if crontabPath == "-":
            crontabFile = sys.stdin
        else:
            crontabFile = open(crontabPath, "r")
    except Exception as detail:
        raise Exception("Error: Could not open crontab file (%s)." % crontabPath)

    # generate and store each event
    events = []
    try:
        l = [ "# generated by hcron-conv" ]
        for line in crontabFile:
            line = line.strip()

            if line == "":
                continue

            if line.startswith("#"):
                l.append(line)
                continue
            elif line.startswith("@"):
                alias, cmd = line.split(None, 1)
                if alias in CRONTAB_ALIASES_MAP:
                    min, hour, dom, mon, dow = CRONTAB_ALIASES_MAP[alias].split(None, 4)
                else:
                    # unsupported alias
                    continue
            elif not line[0].isdigit():
                # variable
                continue
            else:
                min, hour, dom, mon, dow, cmd = line.split(None, 5)
            if mon.isalpha():
                monName = mon.lower()[:3]
                mon = MONTH_NAMES_MAP.get(monName)
            if dow.isalpha():
                dowName = dow.lower()[:3]
                dow = DOW_NAMES_MAP.get(dowName)

            if mon == None or dow == None:
                # error in spec
                continue

            d = HCRON_EVENT_DEFINITION_MAP.copy()
            d["host"] = hostName
            d["command"] = cmd
            d["notify_email"] = mailAddr
            d["when_month"] = mon
            d["when_day"] = dom
            d["when_hour"] = hour
            d["when_minute"] = min
            d["when_dow"] = dow

            st = "\n".join([ "%s=%s" % (name, d[name]) for name in HCRON_EVENT_DEFINITION_NAMES ])

            l.append(st)
            events.append("\n".join(l))
            l = [ "# generated by hcron-conv" ]
    except Exception as detail:
        raise Exception("Error: Could not process crontab file (%s)." % crontabPath)

    crontabFile.close()

    # make sure the dir exists
    try:
        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)
    except Exception as detail:
        raise Exception("Error: Could not create directory (%s)." % dirPath)

    # write the events to individual event definition files
    for num, event in zip(xrange(len(events)), events):
        path = os.path.join(dirPath, str(num))
        try:
            open(path, "w+").write(event)
        except Exception as detail:
            raise Exception("Error: Could not create event definition file (%s)." % path)

def convert_to_crontab_main(args):
    """main for "--to-crontab".
    """
    try:
        crontabpath = None
        dirpath = None
        remoteshell = "ssh"

        while args:
            arg = args.pop(0)
            if arg in ["--remoteshell", "--remoteShell"]:
                remoteshell = args.pop(0)
            elif len(args) == 1:
                crontabpath, dirpath = [arg]+args
                del args[:]
            else:
                raise Exception()

        if None in [crontabpath, dirpath]:
            raise Exception()

        convert_to_crontab(crontabpath, dirpath, remoteShell=remoteshell)
    except:
        raise

def convert_to_crontab(crontabPath, dirPath, remoteShell):
    try:
        if crontabPath == "-":
            crontabFile = sys.stdout
        else:
            crontabFile = open(crontabPath, "w+")
    except Exception as detail:
        raise Exception("Error: Could not open crontab file (%s)." % crontabPath)

    # collect all events in dir tree
    l = [ "# generated by hcron-conv" ]
    for root, dirNames, fileNames in os.walk(dirPath):
        for fileName in fileNames:
            path = os.path.join(root, fileName)
            event = Event(path, "", "")
            l.append("# %s" % path)
            st = "%(when_minute)s %(when_hour)s %(when_day)s %(when_month)s %(when_dow)s" % event.d
            if event.d.get("host") in [ "", None ]:
                st2 = ""
            else:
                if event.d.get("as_user"):
                    st2 = "%s %s@%s" % (remoteShell, event.d["as_user"], event.d["host"])
                else:
                    st2 = "%s %s" % (remoteShell, event.d["host"])

            l.append("%s %s %s" % (st, st2, event.d["command"]))

    # write crontab file
    crontabFile.write("\n".join(l))
    crontabFile.close()

def print_usage():
    d = {
        "progname": os.path.basename(sys.argv[0])
    }

    print("""\
usage: %(progname)s --to-events [<options>] <host> <crontabpath> <dirpath>
       %(progname)s --to-crontab [<options>] <crontabpath> <dirpath>
       %(progname)s -h|--help

Convert between crontab and hcron event file formats.

Use --to-events to convert from a basic crontab to hcron event files.
An event file is created for each crontab command. Event files are
put into a directory.

Use --to-crontab to convert hcron event files to a crontab. A crontab
command is created for each event file. Event files are taken from a
directory.

Options for --to-events:
--mail <address>    Email address used when populating the "mail"
                    setting.

Options for --to-crontab:
--remoteshell <shell>
                    Remote shell to prepend to each crontab command when
                    the "host" setting is not empty. Default is ssh.""" % d)

if __name__ == "__main__":
    try:
        args = sys.argv[1:]

        arg = args.pop(0)
        if arg == "--to-events":
            convert_to_events_main(args)
        elif arg == "--to-crontab":
            convert_to_crontab_main(args)
        elif arg in ["-h", "--help"]:
            print_usage()
        else:
            raise Exception()
    except SystemExit as detail:
        raise
    except Exception as detail:
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    sys.exit(0)
