#! /usr/bin/env python2
#
# hcron/library.py

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

"""Library of routines, classes, etc. for hcron.
"""

# system imports
from datetime import datetime
import os
import os.path
import sys
try:
    from types import StringTypes
except:
    StringTypes = [str]
import traceback

# app imports
from hcron import globs
from hcron.constants import *
from hcron.fspwd import getpwnam, getpwuid
from hcron.logger import log_message

#
# bitmasks makes for easy comparisons (bitwise-and), where each value
# is a bit (e.g., 0-5/2 == 0, 2, 4 -> 0b010101). further all ranges
# are adjusted to start at 0 (e.g., 2009-2012 -> 0-3)
#

WHEN_NAMES = [ "when_year", "when_month", "when_day", "when_hour", "when_minute", "when_dow" ]
WHEN_INDEXES = dict([ (key, i) for i, key in enumerate(WHEN_NAMES) ])

# ignore wasted 0 as required
WHEN_MIN_MAX = {
    "when_year": (2000, 2050),
    "when_month": (1, 12),
    "when_day": (1, 31),
    "when_hour": (0, 23),
    "when_minute": (0, 59),
    "when_dow": (0, 6),
}

WHEN_BITMASKS = dict([(key, 2**(mx-mn+1)-1) for key, (mn,mx) in WHEN_MIN_MAX.items() ])

def date_to_bitmasks(*y_m_d_h_m_dow):
    """Mark the bit positions for year, month, day, etc.
    """
    datemasks = []
    for i, whenName in enumerate(WHEN_NAMES):
        mn, mx = WHEN_MIN_MAX[whenName]
        datemasks.append(2**(y_m_d_h_m_dow[i]-mn))
    return datemasks

    # no when_year
    datemasks = [ 2**x for x in m_d_h_m_dow ]
    return datemasks

    datemasks = {}
    for i in range(len(m_d_h_m_dow)):
        datemasks[i] = 2**(m_d_h_m_dow[i]-1)
    return datemasks
    
def list_st_to_bitmask(st, minMax, fullBitmask):
    """Using offset allows one to support small, but arbitrary ranges
    as bitmasks. The following is easier to understand for offset==0
    (e.g., hours, minutes, seconds).
    """
    mask = 0
    mn, mx = minMax
    offset, mn, mx = mn, 0, mx-mn   # index everything to 0

    #print("offset (%s) mn (%s) mx (%s) minMax (%s)" % (offset, mn, mx, minMax))
    for el in st.split(","):
        if el == "*":
            mask = fullBitmask
        else:
            l = el.split("/", 1)
            if len(l) == 1:
                step = 1
                rng = l[0]
            else:
                rng, step = l
                step = int(step)

            if rng == "*":
                low, hi = mn, mx
            else:
                l = rng.split("-", 1)
                low = int(l[0])-offset
                if len(l) == 1:
                    hi = low
                else:
                    hi = int(l[1])-offset
            if low < mn or hi > mx:
                raise Exception("Out of range.")
            values = range(low, hi+1, step)

            for el in values:
                mask |= 2**int(el)

        if mask == fullBitmask:
            break

    return mask

def copyfile(src, dst, max_size):
    """Copy a file up to a max size (typically, for copying to limited
    space filesystems). src and dst may be pathnames (if string type)
    or file objects; this allows for the src and dst to be accessed by
    different users (i.e., via seteuid as required by NFS with
    root_squash).
    """
    if type(src) in StringTypes:
        src = open(src, "rb")
    if type(dst) in StringTypes:
        dst = open(dst, "wb")

    try:
        buf = None
        while max_size > 0 and buf != b"":
            buf = src.read(2**16)
            max_size -= len(buf)
            if max_size < 0:
                buf = buf[:max_size]
            dst.write(buf)
    except Exception:
        pass

    if src:
        src.close()
    if dst:
        dst.close()

# hcron-specific signature
def dir_walk(top, topdown=True, onerror=None, ignoreMatchFn=None):
    """This is a slightly modified version of os.walk (python v2.4).
    """
    from os.path import join, isdir, islink
    from os import listdir
    from posix import error

    try:
        names = listdir(top)
    except error as err:
        if onerror is not None:
            onerror(err)
        return

    # hcron-specific
    if ignoreMatchFn != None:
        names = [ name for name in names if not ignoreMatchFn(name) ]

    dirs, nondirs = [], []
    for name in names:
        if isdir(join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = join(top, name)
        if not islink(path):
            for x in dir_walk(path, topdown, onerror, ignoreMatchFn):
                yield x
    if not topdown:
        yield top, dirs, nondirs

def get_events_home(username):
    """Returns the user-specific events/ directory path.
    """
    events_base_path = (globs.config.get("events_base_path") or "").strip()

    if events_base_path == "":
        path = os.path.expanduser("~%s/.hcron/%s/events" % (username, globs.servername))
    else:
        path = os.path.join(events_base_path, username, ".hcron/%s/events" % globs.servername)

    if path.startswith("~"):
        return None

    return path

def get_includes_home(username):
    """Returns the user-specific includes/ directory path.
    """
    events_base_path = (globs.config.get("events_base_path") or "").strip()

    if events_base_path == "":
        path = os.path.expanduser("~%s/.hcron/%s/includes" % (username, globs.servername))
    else:
        path = os.path.join(events_base_path, username, ".hcron/%s/includes" % globs.servername)

    if path.startswith("~"):
        return None

    return path
    
def get_events_home_snapshot(username):
    path = os.path.join(HCRON_EVENTS_SNAPSHOT_HOME, username)

    return path

def get_utcoffset():
    """Return UTC offset at the time of the call.

    TODO: Ugly. Fix to do it properly.
    """
    while True:
        now = datetime.now()
        utcnow = datetime.utcnow()
        if now.minute == utcnow.minute:
            break
    return utcnow.replace(second=0, microsecond=0)-now.replace(second=0, microsecond=0)

def makedirs(path, mode=None):
    """Make dirs upto and including path. Do not complain if
    directories exist.
    """
    try:
        if os.path.exists(path):
            return
        if mode == None:
            os.makedirs(path)
        else:
            os.makedirs(path, mode)
    except:
        pass

def serverize():
    if os.fork() != 0:
        # exit original/parent process
        sys.exit(0)

    try:
        # close streams - the Python way
        if sys.stdin:
            sys.stdin.close(); os.close(0); sys.stdin = open("/dev/null", "r")
        if sys.stdout:
            sys.stdout.close(); os.close(1); sys.stdout = open("/dev/null", "w")
        if sys.stderr:
            sys.stderr.close(); os.close(2); sys.stderr = os.fdopen(1, "wt")

        # detach from controlling terminal
        os.setsid()

        # misc
        os.chdir("/")   # / is always available
        os.umask(0o022)
    except:
        log_message("error", "failed to serverize (%s)" % (traceback.format_exc(),))
        sys.exit(1)

def time2seconds(s):
    """Convert time format (HH:MM:SS) to seconds.

    Error in time string returns None.
    """
    try:
        t = s.split(":", 2)
        total = 0
        total += int(t[-1])
        if len(t) > 1:
            total += int(t[-2])*60
        if len(t) > 2:
            total += int(t[-3])*3600
        return total
    except:
        return None

def uid2username(uid):
    return getpwuid(uid).pw_name

def username2ids(name):
    pw = getpwnam(name)
    return (pw.pw_uid, pw.pw_gid)

def username2uid(name):
    return getpwnam(name).pw_uid

def whoami():
    return uid2username(os.getuid())

def __tostrutf8(b):
    """Convert to "utf-8" for python3.
    """
    return str(b, "utf-8")

if sys.version_info.major == 3:
    tostr = __tostrutf8
else:
    tostr = str
