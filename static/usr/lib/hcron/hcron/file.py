#! /usr/bin/env python2
#
# hcron/file.py

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

"""File oriented classes.
"""

# system imports
import os
import os.path

# app imports
from hcron.logger import *

class PidFile:
    def __init__(self, path):
        self.path = path

    def create(self):
        try:
            if os.path.exists(self.path):
                log_message("warning", "found pid file (%s)." % self.path)
                self.remove()

            log_message("info", "creating pid file (%s)." % self.path)
            pid = os.getpid()
            open(self.path, "w").write("%s" % pid)
        except:
            log_message("error", "cannot create pid file (%s)." % self.path)
        return int(pid)

    def remove(self):
        try:
            log_message("info", "removing pid file (%s)." % self.path)
            os.remove(self.path)
        except Exception:
            log_message("error", "cannot remove pid file (%s)." % self.path)
