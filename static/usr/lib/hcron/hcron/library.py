#! /usr/bin/env python2
#
# library.py

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

"""Library of routines, classes, etc. for hcron.
"""

# system imports
import os
import os.path
import types
import sys

# app imports
from hcron.constants import *
from hcron import globs

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
    for i in xrange(len(m_d_h_m_dow)):
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

    #print "offset (%s) mn (%s) mx (%s) minMax (%s)" % (offset, mn, mx, minMax)
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
    if type(src) in types.StringTypes:
        src = open(src, "r")
    if type(dst) in types.StringTypes:
        dst = open(dst, "w")

    try:
        buf = None
        while max_size > 0 and buf != "":
            buf = src.read(2**16)
            max_size -= len(buf)
            if max_size < 0:
                buf = buf[:max_size]
            dst.write(buf)
    except Exception, detail:
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
    except error, err:
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

def get_events_home(userName):
    """Returns the user-specific events/ directory path.
    """
    config = globs.config.get()
    events_base_path = (config.get("events_base_path") or "").strip()

    if events_base_path == "":
        path = os.path.expanduser("~%s/.hcron/%s/events" % (userName, HOST_NAME))
    else:
        path = os.path.join(events_base_path, userName, ".hcron/%s/events" % HOST_NAME)

    if path.startswith("~"):
        return None

    return path

def get_includes_home(userName):
    """Returns the user-specific includes/ directory path.
    """
    config = globs.config.get()
    events_base_path = (config.get("events_base_path") or "").strip()

    if events_base_path == "":
        path = os.path.expanduser("~%s/.hcron/%s/includes" % (userName, HOST_NAME))
    else:
        path = os.path.join(events_base_path, userName, ".hcron/%s/includes" % HOST_NAME)

    if path.startswith("~"):
        return None

    return path
    
def get_events_home_snapshot(userName):
    path = os.path.join(HCRON_EVENTS_SNAPSHOT_HOME, userName)

    return path

def serverize():
    if os.fork() != 0:
        # exit original/parent process
        sys.exit(0)

    # close streams - the Python way
    sys.stdin.close(); os.close(0); os.open("/dev/null", os.O_RDONLY)
    sys.stdout.close(); os.close(1); os.open("/dev/null", os.O_RDWR)
    sys.stderr.close(); os.close(2); os.open("/dev/null", os.O_RDWR)

    # detach from controlling terminal
    os.setsid()

    # misc
    os.chdir("/")   # / is always available
    os.umask(0022)
