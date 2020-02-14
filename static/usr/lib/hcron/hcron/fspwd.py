#! /usr/bin/env python2
#
# hcron/fspwd.py

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

"""Failsafe pwd.

Will not return unless a valid response is obtained from pwd, e.g.,
because of server problem.
"""

# system imports
import pwd
import time

# app imports
from hcron import globs
from hcron.constants import *

def get_test_net_delay():
    try:
        test_net_delay = globs.config.get("test_net_delay", CONFIG_TEST_NET_DELAY)
    except:
        test_net_delay = CONFIG_TEST_NET_DELAY
    return test_net_delay

def get_test_net_retry():
    try:
        test_net_retry = globs.config.get("test_net_retry", CONFIG_TEST_NET_RETRY)
    except:
        test_net_retry = CONFIG_TEST_NET_RETRY
    return test_net_retry

def getpwnam(name):
    """Wrapper for pwd.getpwnam().

    Attempts to obtain user information by querying via pwd. If a
    failure is observed it is retried. Because a non-existent user and
    a missing/non-answering service show up a a KeyError, we need a
    way to differentiate between to two. Thus, the test_net_username
    which is a known network username and should always return a valid
    response if the service is working properly. The expectation is
    that the time between calls to pwd.getpwnam for the given name and
    the test name is virtually 0, so that we can confidently say whether
    a failure is service related or a real, non-existent user error.
    """
    test_net_retry = get_test_net_retry()
    for try_count in range(test_net_retry):
        try:
            return pwd.getpwnam(name)
        except:
            test_service()

    raise Exception("Error getting user information with getpwnam() for username (%s)." % name)

def getpwuid(uid):
    test_net_retry = get_test_net_retry()
    for try_count in range(test_net_retry):
        try:
            return pwd.getpwuid(uid)
        except:
            test_service()

    raise Exception("Error getting user information with getpwuid() for uid (%s)." % uid)

def test_service():
    # check if network service is really answering
    test_net_username = globs.config.get("test_net_username")
    test_net_delay = get_test_net_delay()
    if test_net_username:
        # test with known username until success
        while True:
            try:
                pwd.getpwnam(test_net_username)
                break
            except Exception:
                time.sleep(test_net_delay)
