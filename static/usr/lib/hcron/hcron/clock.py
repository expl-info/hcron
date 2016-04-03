#! /usr/bin/env python
#
# clock.py

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