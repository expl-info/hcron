#! /usr/bin/env python2
#
# hcron/trackablefile.py

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

"""Trackable file classes.
"""

# system imports
import ast
import os
import pprint
import re
import stat
import sys

# app imports
from hcron.constants import *
from hcron.logger import *

class TrackableFile:
    def __init__(self, path):
        self.path = path
        self.contents = None
        self.mtime = None
        self.load()

    def load(self):
        pass

    def is_modified(self):
        if self.path:
            mtime = os.stat(self.path)[stat.ST_MTIME]
            return mtime != self.mtime

    def get_modified_time(self):
        return self.mtime

    def get(self):
        return self.contents

class ConfigFile(TrackableFile):

    def dump(self, path):
        try:
            f = None
            f = open(path, "w+")
            pprint.pprint(self.get(), stream=f, indent=4)
        finally:
            if f:
                f.close()

    def load(self):
        d = {}

        try:
            mtime = os.stat(self.path)[stat.ST_MTIME]
            st = open(self.path, "r").read()
            d = ast.literal_eval(st)
            log_load_config()
        except Exception:
            log_message("error", "cannot load hcron.config file (%s)." % self.path)
            sys.exit(1)

        # augment
        if "names_to_ignore_regexp" in d:
            try:
                d["names_to_ignore_cregexp"] = re.compile(d["names_to_ignore_regexp"])
            except:
                pass

        self.contents = d
        self.mtime = mtime

class AllowFile(TrackableFile):

    def dump(self, path):
        try:
            f = None
            f = open(path, "w+")
            f.write("\n".join(self.get()))
        finally:
            if f:
                f.close()

    def load(self):
        allowedusers = []
        try:
            mtime = os.stat(self.path)[stat.ST_MTIME]
            st = open(self.path, "r").read()

            for line in st.split("\n"):
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue

                username = line
                if username != "":
                    allowedusers.append(username)

            log_load_allow()
        except Exception:
                log_message("error", "cannot load hcron.allow file (%s)." % self.path)

        self.contents = list(set(allowedusers))
        self.mtime = mtime

class SignalDir(TrackableFile):
    def load(self):
        try:
            self.mtime = os.stat(self.path)[stat.ST_MTIME]
        except Exception:
            log_message("error", "cannot stat signal directory (%s)." % self.path)
            raise
