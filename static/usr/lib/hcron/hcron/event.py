#! /usr/bin/env python2
#
# event.py

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

"""Event related classes, etc.
"""

# system imports
from datetime import datetime
import fnmatch
import os
import os.path
import re
import socket
import stat
import textwrap
import time
import traceback

# app imports
from hcron import globs
from hcron.constants import *
from hcron.execute import remote_execute
from hcron.hcrontree import HcronTreeCache, create_user_hcron_tree_file, install_hcron_tree_file
from hcron.library import WHEN_BITMASKS, WHEN_INDEXES, WHEN_MIN_MAX, list_st_to_bitmask, uid2username, username2uid
from hcron.logger import *
from hcron.notify import send_email_notification

tw = textwrap.TextWrapper()
tw.initial_indent = "    "
tw.subsequent_indent = "    "
tw.width = 128

def get_event(username, eventname):
    """Return event object.
    """
    try:
        return globs.eventlistlist.get(username).get(eventname)
    except:
        raise Exception("cannot find event (%s) for user (%s)" % (eventname, username))

def reload_events(signalHomeMtime):
    """Reload events for all users whose signal file mtime is <= to
    that of the signal home directory. Any signal files that are
    created subsequently, will be caught in the next pass.
    """
    usernames = {}  # to ensure reload only once per user

    for filename in os.listdir(HCRON_SIGNAL_HOME):
        path = os.path.join(HCRON_SIGNAL_HOME, filename)
        st = os.stat(path)
        mtime = st[stat.ST_MTIME]

        if mtime <= signalHomeMtime:
            username = uid2username(st[stat.ST_UID])

            if username not in usernames:
                try:
                    install_hcron_tree_file(username, HOST_NAME)
                    globs.eventlistlist.reload(username)
                    usernames[username] = None
                except Exception as detail:
                    log_message("warning", "Could not install snapshot file for user (%s)." % username)

            try:
                os.remove(path) # remove singles and multiples
            except Exception as detail:
                log_message("warning", "Could not remove signal file (%s)." % path)

def signal_reload(unload=False):
    """Signal to reload.
    """
    import tempfile
    from hcron.file import AllowedUsersFile, ConfigFile

    globs.config = ConfigFile(HCRON_CONFIG_PATH)
    globs.allowedUsers = AllowedUsersFile(HCRON_ALLOW_PATH)
    config = globs.config.get()
    signalHome = config.get("signalHome") or HCRON_SIGNAL_HOME
    username = uid2username(os.getuid())

    if username not in globs.allowedUsers.get():
        raise Exception("Warning: You are not an allowed hcron user.")

    try:
        create_user_hcron_tree_file(username, HOST_NAME, empty=unload)
    except Exception as detail:
        raise Exception("Error: Could not create hcron snapshot file (%s)." % detail)

    try:
        tempfile.mkstemp(prefix=username, dir=signalHome)
    except:
        raise Exception("Error: Could not signal for reload.")

class CannotLoadFileException(Exception):
    pass

class BadEventDefinitionException(Exception):
    pass

class BadVariableSubstitutionException(Exception):
    pass

class TemplateEventDefinitionException(Exception):
    pass

class EventListList:
    """Event list list.

    All event lists are keyed on user name.
    """
    def __init__(self, usernames):
        log_message("info", "Initializing events list.")
        self.load(usernames)

    def get(self, username):
        return self.eventlists.get(username)

    def load(self, usernames=None):
        """Load from scratch.
        """
        log_message("info", "Loading events.")

        t0 = time.time()
        self.eventlists = {}
        self.usernames = usernames
        total = 0 

        for username in self.usernames:
            self.reload(username)

    def reload(self, username):
        if username not in self.usernames:
            return

        if username in self.eventlists:
            self.remove(username)

        t0 = time.time()
        el = EventList(username)
        t1 = time.time()

        if el:
            self.eventlists[username] = el
            count = len(el.events)
            log_load_events(username, count, t1-t0)

    def remove(self, username):
        if username in self.eventlists:
            count = len(self.eventlists[username].events)

            log_discard_events(username, count)
            del self.eventlists[username]

    def test(self, datemasks, usernames=None):
        events = []
        usernames = usernames or self.usernames

        for username in usernames:
            el = self.eventlists.get(username)

            if el:
                events.extend(el.test(datemasks))
        return events

class EventList:
    """Event list for a user.

    All events are key on their name (i.e., path relative to
    ~/.hcron/<hostName>/events).
    """

    def __init__(self, username):
        self.username = username
        self.events = None
        self.load()

    def dump(self):
        """Dump event list to a file.
        """
        path = "%s/%s" % (HCRON_EVENT_LISTS_DUMP_DIR, self.username)
        if not path.startswith(HCRON_EVENT_LISTS_DUMP_DIR):
            # paranoia?
            return

        oldumask = os.umask(0o337)

        try:
            os.remove(path)
        except:
            pass

        try:
            f = None
            f = open(path, "w+")
            os.chown(path, username2uid(self.username), 0)

            events = self.events
            for name in sorted(events.keys()):
                reason = events[name].reason
                if reason == None:
                    f.write("accepted::%s\n" % name)
                else:
                    f.write("rejected:%s:%s\n" % (reason, name))
        except Exception as detail:
            pass
        finally:
            if f != None:
                f.close()

        os.umask(oldumask)

    def get(self, name):
        return self.events.get(name)

    def load(self):
        self.events = {}

        try:
            max_events_per_user = globs.config.get().get("max_events_per_user", CONFIG_MAX_EVENTS_PER_USER)
            names_to_ignore_cregexp = globs.config.get().get("names_to_ignore_cregexp")
            ignoreMatchFn = names_to_ignore_cregexp and names_to_ignore_cregexp.match

            # global cache assumes single-threaded load!
            hcron_tree_cache = globs.hcron_tree_cache = HcronTreeCache(self.username, ignoreMatchFn)
            for name in hcron_tree_cache.get_event_names():
                try:
                    if hcron_tree_cache.is_ignored_event(name):
                        continue

                    event = Event(name, self.username)
                except Exception as detail:
                    # bad Event definition
                    pass
                    #continue

                self.events[name] = event

                if len(self.events) >= max_events_per_user:
                    event.reason = "maximum events reached"
                    log_message("warning", "Reached maximum events allowed (%s)." % max_events_per_user)

        except Exception as detail:
            log_message("error", "Could not load events.")

        # delete any caches (and references) before moving on with or
        # without an prior exception!
        hcron_tree_cache = globs.hcron_tree_cache = None

        self.dump()

    def print_events(self):
        for name, event in self.events.items():
            print("name (%s) event (%s)" % (name, event))

    def test(self, datemasks):
        events = []
        for event in self.events.values():
            if event.test(datemasks):
                events.append(event)
        return events

class Event:
    def __init__(self, name, username):
        self.name = name
        self.username = username
        self.assignments = None
        self.deleted = False
        self.masks = None
        self.reason = None
        self.when = None

        self.load()

    def __repr__(self):
        return """<Event name (%s) when (%s)>""" % (self.name, self.when)

    def activate(self, job):
        """Activate event and return next event in chain.

        The job object provides context.
        """
        eventchainnames = job.eventchainnames.split(":")
        sched_datetime = job.sched_datetime

        varinfo = self.get_varinfo(job.triggername, eventchainnames, sched_datetime)
        nexteventname = None
        nexteventtype = None

        # late substitution
        eval_assignments(self.assignments, varinfo)
        #open("/tmp/hc", "a").write("self.name (%s) varinfo (%s)\n" % (self.name, str(varinfo)))

        # get event file def
        event_as_user = varinfo.get("as_user")
        event_command = varinfo.get("command")
        if event_as_user == "":
            event_as_user = self.username
        event_host = varinfo.get("host")
        event_notify_email = varinfo.get("notify_email")
        event_notify_subject = varinfo.get("notify_subject", "").strip()
        event_notify_message = varinfo.get("notify_message", "")
        event_notify_message = event_notify_message.replace("\\n", "\n").replace("\\t", "\t")
        event_next_event = varinfo.get("next_event", "")
        event_failover_event = varinfo.get("failover_event", "")

        log_activate(job.jobid, job.jobgid, job.triggername, job.username, job.eventname, job.eventchainnames)

        if event_command:
            rv = remote_execute(job, self.name, self.username, event_as_user, event_host, event_command)
        else:
            error_on_empty_command = globs.config.get().get("error_on_empty_command", CONFIG_ERROR_ON_EMPTY_COMMAND)
            if error_on_empty_command:
                rv = -1
            else:
                rv = 0

        if globs.simulate:
            if globs.simulate_show_event:
                fmt = "%s=%s"
                print(tw.fill(fmt % ("as_user", event_as_user)))
                print(tw.fill(fmt % ("host", event_host)))
                print(tw.fill(fmt % ("command", event_command)))
                print(tw.fill(fmt % ("notify_email", event_notify_email)))
                print(tw.fill(fmt % ("notify_subject", event_notify_subject)))
                print(tw.fill(fmt % ("notify_message", event_notify_message)))
                print(tw.fill(fmt % ("when_year", sched_datetime and sched_datetime.year)))
                print(tw.fill(fmt % ("when_month", sched_datetime and sched_datetime.month)))
                print(tw.fill(fmt % ("when_day", sched_datetime and sched_datetime.day)))
                print(tw.fill(fmt % ("when_hour", sched_datetime and sched_datetime.hour)))
                print(tw.fill(fmt % ("when_minute", sched_datetime and sched_datetime.minute)))
                print(tw.fill(fmt % ("when_dow", sched_datetime and sched_datetime.weekday())))
                print(tw.fill(fmt % ("next_event", event_next_event)))
                print(tw.fill(fmt % ("failover_event", event_failover_event)))

        if rv == 0:
            # success
            # notify
            if event_notify_email:
                if event_notify_subject == "":
                    subject = """hcron (%s): "%s" executed at %s@%s""" % (HOST_NAME, self.name, event_as_user, event_host)
                else:
                    subject = event_notify_subject
                subject = subject[:1024]
                send_email_notification(self.name, self.username, event_notify_email, subject, event_notify_message)

            nexteventname, nexteventtype = event_next_event, "next"
        else:
            # child, with problem
            nexteventname, nexteventtype = event_failover_event, "failover"

        # handle None, "", and valid string
        nexteventnames = []
        if nexteventname:
            for name in nexteventname.split(":"):
                nexteventnames.append(self.resolve_event_name_to_name(self.name, name.strip()))
        nexteventtype = nexteventnames and nexteventtype or None

        return nexteventnames, nexteventtype

    def get_name(self):
        return self.name

    def get_varinfo(self, triggername=None, eventchainnames=None, sched_datetime=None):
        """Set variable values.

        Early substitution: at event load time.
        Late substitution: at event activate time.

        eventchainnames != None means late since every event activate
        has at least itself in the eventchainnames.
        """

        # early and late
        varinfo = {
            "when_year": "*",
            "template_name": None,
            "HCRON_HOST_NAME": socket.getfqdn(),
            "HCRON_EVENT_NAME": self.name,
            "HCRON_TRIGGER_NAME": triggername,
        }
        
        if eventchainnames:
            # late
            selfeventchainnames = []
            lasteventchainname = eventchainnames[-1]
            for eventChainName in reversed(eventchainnames):
                if eventChainName != lasteventchainname:
                    break
                selfeventchainnames.append(eventChainName)
            varinfo["HCRON_EVENT_CHAIN"] = ":".join(eventchainnames)
            varinfo["HCRON_SELF_CHAIN"] = ":".join(selfeventchainnames)

            activate_datetime = globs.clock.now()
            activate_datetime_utc = globs.clock.utcnow()
            varinfo["HCRON_ACTIVATE_DATETIME"] = activate_datetime.strftime("%Y:%m:%d:%H:%M:%S:%W:%w")
            varinfo["HCRON_ACTIVATE_DATETIME_UTC"] = activate_datetime_utc.strftime("%Y:%m:%d:%H:%M:%S:%W:%w")
            varinfo["HCRON_ACTIVATE_EPOCHTIME"] = activate_datetime.strftime("%s")
            varinfo["HCRON_ACTIVATE_EPOCHTIME_UTC"] = activate_datetime_utc.strftime("%s")

            if sched_datetime:
                varinfo["HCRON_SCHEDULE_DATETIME"] = sched_datetime.strftime("%Y:%m:%d:%H:%M:%S:%W:%w")
                varinfo["HCRON_SCHEDULE_DATETIME_UTC"] = sched_datetime.strftime("%Y:%m:%d:%H:%M:%S:%W:%w")
                varinfo["HCRON_SCHEDULE_EPOCHTIME"] = sched_datetime.strftime("%s")
                varinfo["HCRON_SCHEDULE_EPOCHTIME_UTC"] = sched_datetime.strftime("%s")
        else:
            varinfo["HCRON_EVENT_CHAIN"] = ""
            varinfo["HCRON_SELF_CHAIN"] = ""

        return varinfo

    def load(self):
        varinfo = self.get_varinfo()

        masks = {
            WHEN_INDEXES["when_year"]: list_st_to_bitmask("*", WHEN_MIN_MAX["when_year"], WHEN_BITMASKS["when_year"]),
        }

        try:
            try:
                lines = globs.hcron_tree_cache.get_event_contents(self.name).split("\n")
                lines = self.process_lines(lines)
            except Exception as detail:
                self.reason = "cannot load file"
                raise CannotLoadFileException("Ignored event file (%s)." % self.name)

            try:
                lines = self.process_includes(self.name, lines)
            except Exception as detail:
                self.reason = "cannot process include(s)"
                raise CannotLoadFileException("Ignored event file (%s)." % self.name)

            try:
                assignments = load_assignments(lines)
            except Exception as detail:
                self.reason = "bad definition"
                raise BadEventDefinitionException("Ignored event file (%s)." % self.name)

            try:
                # early substitution
                eval_assignments(assignments, varinfo)
            except Exception as detail:
                self.reason = "bad variable substitution"
                raise BadVariableSubstitutionException("Ignored event file (%s)." % self.name)

            # for backward compatibility: rejected events may have
            # invalid when_* settings but assignments otherwise; useful
            # for non-scheduled events in event chains
            #
            # *** keep until alternate solution ***
            self.assignments = assignments

            # template check (this should preced when_* checks)
            if varinfo["template_name"] == self.name.split("/")[-1]:
                self.reason = "template"
                raise TemplateEventDefinitionException("Ignored event file (%s). Template name (%s)." % (self.name, varinfo["template_name"]))
    
            # bad definition check
            try:
                for name, value in varinfo.items():
                    if name.startswith("when_"):
                        masks[WHEN_INDEXES[name]] = list_st_to_bitmask(value, WHEN_MIN_MAX[name], WHEN_BITMASKS[name])
    
            except Exception as detail:
                self.reason = "bad when_* setting"
                raise BadEventDefinitionException("Ignored event file (%s)." % self.name)

            self.masks = masks

            # full specification check
            for name in HCRON_EVENT_DEFINITION_NAMES:
                if name not in varinfo:
                    self.reason = "not fully specified, missing field (%s)" % name
                    raise BadEventDefinitionException("Ignored event file (%s). Missing field (%s)." % \
                        (self.name, name))

            self.when = "%s %s %s %s %s %s" % \
                (varinfo.get("when_year"),
                    varinfo.get("when_month"),
                    varinfo.get("when_day"),
                    varinfo.get("when_hour"),
                    varinfo.get("when_minute"),
                    varinfo.get("when_dow"))
        except:
            if self.reason == None:
                self.reason = "unknown problem"

    def process_includes(self, callername, lines, depth=1):
        if depth > 3:
            raise Exception("Reached include depth maximum (%s)." % depth)

        l = []
        for line in lines:
            t = line.split()
            if len(t) == 2 and t[0] == "include":
                include_name = self.resolve_event_name_to_name(callername, t[1])
                lines2 = globs.hcron_tree_cache.get_include_contents(include_name).split("\n")
                lines2 = self.process_lines(lines2)
                lines2 = self.process_includes(include_name, lines2, depth+1)
                l.extend(lines2)
            else:
                l.append(line)

        return l

    def process_lines(self, lines):
        """Line processing:
        - non-continuation lines, left-stripped, starting with # are
          discarded
        - lines ending in \ are concatenated, unconditionally, with
          the next line resulting in a replacement line
        - lines stripped to "" are discarded
        """
        l = []
        while lines:
            line = lines.pop(0)
            if line.lstrip().startswith("#"):
                continue
            while lines and line.endswith("\\"):
                line = line[:-1]+lines.pop(0)

            line = line.strip()
            if line == "":
                continue
            l.append(line)

        return l
        
    def test(self, datemasks):
        if self.reason != None:
            return 0

        masks = self.masks
        for i in range(len(datemasks)):
            try:
                if not (datemasks[i] & masks[i]):
                    return 0
            except Exception as detail:
                # should not get here
                log_message("error", "detail (%s) self.reason (%s) user (%s) name (%s) when (%s)." % \
                    (detail, self.reason, self.username, self.name, self.when))
                return 0

        return 1

    def resolve_event_name_to_name(self, callername, name):
        """Resolve event name relative to the caller event.
        
        1) relative to .../events, if starts with "/"
        2) relative to the current path
        """
        if not name.startswith("/"):
            # absolutize name
            name = os.path.join("/", os.path.dirname(callername), name)

        return name

import re

#SUBST_NAME_RE = "(?P<op>[#$])(?P<name>HCRON_\w*)"
SUBST_NAME_RE = "(?P<op>[#$])(?P<name>\w+)"
SUBST_NAME_CRE = re.compile(SUBST_NAME_RE)
def search_name_select(st, lastpos):
    """Find startpos and endpos for:
    1. [#$]<name>[<body>]
    2. [#$]<name>{<body>}
    3. [#$]<name>
    otherwise:
    3. None, None
    """
    startpos, endpos = None, None
    s = SUBST_NAME_CRE.search(st, lastpos)
    if s:
        startpos, endpos = s.span()
        if endpos < len(st):
            openb = st[endpos]
            if openb in [ "[", "{" ]:
                if openb == "[":
                    closeb = "]"
                elif openb == "{":
                    closeb = "}"

                depth = 0
                for ch in st[endpos:]:
                    if ch == openb:
                        depth += 1
                    elif ch == closeb:
                        depth -= 1
                        if depth == 0:
                            endpos += 1
                            break
                    endpos += 1
                else:
                    # no closing bracket
                    startpos = None
                    endpos = None

    return startpos, endpos
        
#SUBST_NAME_SELECT_RE = "(?P<op>[#$])(?P<name>HCRON_\w*)(((?P<square_bracket>\[)(?P<square_select>.*)\])|((?P<curly_bracket>\{)(?P<curly_select>.*)\}))?"
SUBST_NAME_SELECT_RE = "(?P<op>[#$])(?P<name>\w+)(((?P<square_bracket>\[)(?P<square_select>.*)\])|((?P<curly_bracket>\{)(?P<curly_select>.*)\}))?"
#SUBST_SEP_LIST_RE = "(?:(?P<sep>.*)!)?(?P<list>.*)"
SUBST_SEP_RE = "(?P<split_sep>[^?!]*)((?:\?)(?P<join_sep>[^!]*))?!"
SUBST_SEP_LIST_RE = "(?:(%s))?(?P<list>.*)" % SUBST_SEP_RE
SUBST_LIST_RE = "(.*)(?:,(.*))?"
SUBST_SLICE_RE = "(-?\d*)(:(-?\d*))?(:(-?\d*))?"
SUBST_NAME_SELECT_CRE = re.compile(SUBST_NAME_SELECT_RE)
SUBST_SEP_LIST_CRE = re.compile(SUBST_SEP_LIST_RE)
SUBST_LIST_CRE = re.compile(SUBST_LIST_RE)
SUBST_SLICE_CRE = re.compile(SUBST_SLICE_RE)

def hcron_variable_substitution(value, varinfo, depth=1):
    """Perform variable substitution.

    Search for substitutable segments, substitute, repeat. Once a
    substitution is done, that segment is not treated again.
    """
    l = []
    lastpos = 0
    while True:
        if 0:
            s = SUBST_NAME_SELECT_CRE.search(value, lastpos)
            if s == None:
                break
            startpos, endpos = s.span()

        startpos, endpos = search_name_select(value, lastpos)

        if startpos == None:
            break

        l.append(value[lastpos:startpos])
        l.append(hcron_variable_substitution2(value[startpos:endpos], varinfo))
        lastpos = endpos

    l.append(value[lastpos:])

    #open("/tmp/hc", "a").write("value (%s) -> (%s)\n" % (value, "".join(l)))

    return "".join(l)

def hcron_variable_substitution2(value, varinfo, depth=1):
    """Recursively resolve all variables in value with settings in
    varinfo. The mechanism is:
    1) match
    2) resolve
    3) proceed to next match level (name, select, ...)
    """
    try:
        # default
        substSplitSep = ":"

        nid = SUBST_NAME_SELECT_CRE.match(value).groupdict()
        #open("/tmp/hc", "a").write("nid (%s)\n" % str(nid))

        op = nid.get("op")
        substName = nid.get("name")
        nameValue = varinfo.get(substName)
        substBracket = nid.get("square_bracket") and "[" or (nid.get("curly_bracket") and "{") or None
        #open("/tmp/hc", "a").write(" **** substBracket *** (%s)\n" % substBracket)
        if substBracket == "[":
            substSelect = nid.get("square_select", "")
        elif substBracket == "{":
            substSelect = nid.get("curly_select", "")
        else:
            substSelect = None
        substSelect = hcron_variable_substitution2(substSelect, varinfo, depth+1)


        if substSelect == None:
            # no select
            if nameValue != None:
                value = nameValue
        else:
            sid = SUBST_SEP_LIST_CRE.match(substSelect).groupdict()
            substSplitSep = sid.get("split_sep")
            substJoinSep = sid.get("join_sep")
            if substSplitSep == None:
                # special case!
                substSplitSep = substName == "HCRON_EVENT_NAME" and "/" or ":"
            elif substSplitSep == "":
                pass
            else:
                substSplitSep = hcron_variable_substitution2(substSplitSep, varinfo, depth+1)
            if substJoinSep == None:
                substJoinSep = substSplitSep
            else:
                substJoinSep = hcron_variable_substitution2(substJoinSep, varinfo, depth+1)

            if substSplitSep == "":
                nameValues = list(nameValue)
            else:
                nameValues = nameValue.split(substSplitSep)

            substList = sid["list"]
            substList = hcron_variable_substitution2(substList, varinfo, depth+1)

            # fix RE to avoid having to check for None for single list value
            ll = substList.split(",")
            #open("/tmp/hc", "a").write("-- ll (%s)\n" % str(ll))

            if substBracket == "[":
                # indexing
                for i in range(len(ll)):
                    ll[i] = hcron_variable_substitution2(ll[i], varinfo, depth+1)
                    #open("/tmp/hc", "a").write("---- ll (%s) i (%s) ll[i] (%s)\n" % (str(ll), i, ll[i]))
                    # normalize: empty -> None
                    irl = [ el != "" and el or None for el in SUBST_SLICE_CRE.match(ll[i]).groups() ]
                    #open("/tmp/hc", "a").write("------- irl (%s)\n" % str(irl))
                    start, endColon, end, stepColon, step = irl[0:5]
                    start = hcron_variable_substitution2(start, varinfo, depth+1)
                    end = hcron_variable_substitution2(end, varinfo, depth+1)
                    step = hcron_variable_substitution2(step, varinfo, depth+1)

                    if step != None:
                        step = int(step)
                    else:
                        step = 1
                    if start != None:
                        start = int(start)
                    if end != None:
                        end = int(end)
                    else:
                        if endColon == None:
                            if start < 0:
                                end = start-1
                                step = -1
                            else:
                                end = start+1
                                step = 1

                    ll[i] = substJoinSep.join(nameValues[start:end:step])
                    #open("/tmp/hc", "a").write("------------ ll[i] (%s)\n" % str(ll[i]))
            elif substBracket == "{":
                # matching: substitute, match, flatten
                ll = [ hcron_variable_substitution2(x, varinfo, depth+1) for x in ll ]
                #open("/tmp/hc", "a").write("---- ll (%s) nameValues (%s)\n" % (str(ll), nameValues))
                ll = [ el for x in ll for el in fnmatch.filter(nameValues, x) ]
                #open("/tmp/hc", "a").write("------ ll (%s)\n" % str(ll))

            value = substJoinSep.join(ll)

        if op == "#" and nameValue != None:
            #open("/tmp/hc", "a").write("*** name (%s) nameValue (%s) sep (%s) value (%s) count (%s)\n" % (substName, nameValue, substSplitSep, value, value.count(substSplitSep)+1))
            value = str(value.count(substSplitSep)+1)
    except:
        #print(traceback.print_exc())
        pass

    return value

def eval_assignments(assignments, varinfo):
    """Evaluate assignments using the settings in varinfo and storing the
    results back to varinfo.
    """
    for name, value in assignments:
        varinfo[name] = hcron_variable_substitution(value, varinfo)

def load_assignments(lines):
    """Load lines with the format name=value into a list of
    (name, value) tuples.
    """
    l = []

    for line in lines:
        name, value  = line.split("=", 1)
        l.append((name.strip(), value.strip()))

    return l
