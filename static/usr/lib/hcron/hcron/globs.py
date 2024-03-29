#! /usr/bin/env python2
#
# hcron/globs.py

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

"""Globals. Should be imported as "from hcron import globs".
"""

allowfile = None
clock = None
config = None
configfile = None
debug = False
email_notify_enabled = False
eventlistlist = None
fqdn = None
hcron_tree_cache = None
localhostnames = []
pidfile = None
remote_execute_enabled = False
server = None
servername = None
signaldir = None
simulate = False
simulate_fail_events = []
simulate_show_email = False
simulate_show_event = False
