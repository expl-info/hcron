#! /usr/bin/env python2
#
# hcron/constants.py

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

"""Constants.
"""

__all__ = [
    "CONFIG_ALLOW_LOCALHOST",
    "CONFIG_ALLOW_ROOT_EVENTS",
    "CONFIG_COMMAND_SPAWN_TIMEOUT",
    "CONFIG_ERROR_ON_EMPTY_COMMAND",
    "CONFIG_LOG_PATH",
    "CONFIG_MAX_ACTIVATED_EVENTS",
    "CONFIG_MAX_CHAIN_EVENTS",
    "CONFIG_MAX_EVENT_FILE_SIZE",
    "CONFIG_MAX_EVENTS_PER_USER",
    "CONFIG_MAX_HCRON_TREE_SNAPSHOT_SIZE",
    "CONFIG_MAX_NEXT_EVENTS",
    "CONFIG_REMOTE_SHELL_EXEC",
    "CONFIG_REMOTE_SHELL_TYPE",
    "CONFIG_TEST_NET_DELAY",
    "CONFIG_TEST_NET_RETRY",
    "CONFIG_USE_SYSLOG",
    "CRONTAB_ALIASES_MAP",
    "DOW_NAMES_MAP",
    "ENQUEUE_ONDEMAND_DELAY",
    "HCRON_ALLOW_PATH",
    "HCRON_ALLOWED_USERS_DUMP_PATH",
    "HCRON_CONFIG_DUMP_PATH",
    "HCRON_CONFIG_PATH",
    "HCRON_ETC_PATH",
    "HCRON_EVENT_DEFINITION",
    "HCRON_EVENT_DEFINITION_MAP",
    "HCRON_EVENT_DEFINITION_NAMES",
    "HCRON_EVENT_LISTS_DUMP_DIR",
    "HCRON_EVENTS_SNAPSHOT_HOME",
    "HCRON_HOME",
    "HCRON_LIB_HOME",
    "HCRON_LOG_HOME",
    "HCRON_ONDEMAND_HOME",
    "HCRON_PID_FILE_PATH",
    "HCRON_SIGNAL_HOME",
    "HCRON_SPOOL_HOME",
    "HCRON_TREES_HOME",
    "HCRON_VAR_PATH",
    "HOST_NAME",
    "JOBQ_SIZE",
    "LOCAL_HOST_NAMES",
    "MINUTE_DELTA",
    "MONTH_NAMES_MAP",
    "PROG_NAME",
    "SHORT_HOST_NAME",
    "USER_ID",
    "USER_NAME",
]

# system imports
import datetime
import os
import os.path
import pwd
import socket
import sys

# constants
PROG_NAME = os.path.basename(sys.argv[0])

HCRON_HOME = os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), "..", ".."))
if HCRON_HOME.startswith("/usr"):
    HCRON_ETC_PATH = "/etc/hcron"
    HCRON_VAR_PATH = "/var"
else:
    HCRON_ETC_PATH = os.path.join(HCRON_HOME, "etc/hcron")
    HCRON_VAR_PATH = os.path.join(HCRON_HOME, "var")
# etc
HCRON_CONFIG_PATH = os.path.join(HCRON_ETC_PATH, "hcron.conf")
HCRON_ALLOW_PATH = os.path.join(HCRON_ETC_PATH, "hcron.allow")
# var/lib
HCRON_LIB_HOME = os.path.join(HCRON_VAR_PATH, "lib/hcron")
HCRON_ALLOWED_USERS_DUMP_PATH = os.path.join(HCRON_LIB_HOME, "allowed_users.dump")
HCRON_CONFIG_DUMP_PATH = os.path.join(HCRON_LIB_HOME, "config.dump")
HCRON_EVENT_LISTS_DUMP_DIR = os.path.join(HCRON_LIB_HOME, "event_lists")
HCRON_EVENTS_SNAPSHOT_HOME = os.path.join(HCRON_LIB_HOME, "events")
# var/log
HCRON_LOG_HOME = os.path.join(HCRON_VAR_PATH, "log/hcron")
# var/spool
HCRON_SPOOL_HOME = os.path.join(HCRON_VAR_PATH, "spool/hcron")
HCRON_SIGNAL_HOME = os.path.join(HCRON_SPOOL_HOME, "signal")
HCRON_ONDEMAND_HOME = os.path.join(HCRON_SPOOL_HOME, "ondemand")

HCRON_PID_FILE_PATH = os.path.join(HCRON_VAR_PATH, "run/hcron.pid")

HCRON_TREES_HOME = os.path.join(HCRON_LIB_HOME, "trees")

HCRON_EVENT_DEFINITION_NAMES = [
    "as_user",
    "host",
    "command",
    "notify_email",
    "notify_message",
    "when_month",
    "when_day",
    "when_hour",
    "when_minute",
    "when_dow",
    "template_name",
]

HCRON_EVENT_DEFINITION = "\n".join([ "%s=" % name for name in HCRON_EVENT_DEFINITION_NAMES ])
HCRON_EVENT_DEFINITION_MAP = dict([ (name, "") for name in HCRON_EVENT_DEFINITION_NAMES ])

CONFIG_ALLOW_LOCALHOST = False              # allow_localhost
CONFIG_ALLOW_ROOT_EVENTS = False            # allow_root_events
CONFIG_COMMAND_SPAWN_TIMEOUT = 15           # command_spawn_timeout
CONFIG_ERROR_ON_EMPTY_COMMAND = False       # error_on_empty_command
CONFIG_LOG_PATH = os.path.join(HCRON_LOG_HOME, "hcron.log") # log_path
CONFIG_MAX_ACTIVATED_EVENTS = 20            # max_activated_events
CONFIG_MAX_CHAIN_EVENTS = 5                 # max_chain_events
CONFIG_MAX_EVENT_FILE_SIZE = 5000           # max_event_file_size
CONFIG_MAX_EVENTS_PER_USER = 25             # max_events_per_user
CONFIG_MAX_NEXT_EVENTS = 8                  # max_next_events
CONFIG_REMOTE_SHELL_EXEC = "/usr/bin/ssh"   # remote_shell_exec
CONFIG_REMOTE_SHELL_TYPE = "ssh"            # remote_shell_type
CONFIG_USE_SYSLOG = False                   # use_syslog
CONFIG_MAX_HCRON_TREE_SNAPSHOT_SIZE = 2**18 # 256KB
CONFIG_TEST_NET_DELAY = 1                   # test_net_delay
CONFIG_TEST_NET_RETRY = 5                   # test_net_retry

MONTH_NAMES_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

DOW_NAMES_MAP = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}

CRONTAB_ALIASES_MAP = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# at invocation (user should be root)
USER_ID = os.getuid()
USER_NAME = pwd.getpwuid(USER_ID).pw_name
HOST_NAME = socket.getfqdn()
SHORT_HOST_NAME = socket.gethostname()
LOCAL_HOST_NAMES = {
    "localhost": None,
    HOST_NAME: None,
    SHORT_HOST_NAME: None,
}

MINUTE_DELTA = datetime.timedelta(minutes=1)

JOBQ_SIZE = 100000
ENQUEUE_ONDEMAND_DELAY = 5
