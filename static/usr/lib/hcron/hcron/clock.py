#! /usr/bin/env python2
#
# hcron/clock.py

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

from datetime import datetime

class Clock:

    def __init__(self, tz=None):
        self._now = None
        self._tz = tz

    def now(self, tz=None):
        if self._now == None:
            now = datetime.now(tz or self._tz)
        else:
            now = self._now
        return now

    def utcnow(self):
        if self._now == None:
            now = datetime.utcnow()
        else:
            now = self._now
        return now

    def set(self, now):
        if now == None or issubclass(type(now), datetime):
            self._now = now
        else:
            raise Exception("expected datetime object")
