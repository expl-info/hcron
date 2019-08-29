#! /usr/bin/env python2
#
# notify.py

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

"""Routines for handling notification.
"""

# system imports
import smtplib
import textwrap

# app imports
from hcron.constants import *
from hcron import globs
from hcron.logger import *

tw = textwrap.TextWrapper()
tw.initial_indent = "    "
tw.subsequent_indent = "    "
tw.width = 1024
tw.replace_whitespace = False

def send_email_notification(eventName, fromUserName, toAddr, subject, content):
    config = globs.config.get()
    smtp_server = config.get("smtp_server", "localhost")

    fromAddr = "%s@%s" % (fromUserName, HOST_NAME)
    message = """From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s""" % \
        (fromAddr, toAddr, subject, content)
    try:
        if globs.email_notify_enabled:
            m = smtplib.SMTP(smtp_server)
            m.sendmail(fromAddr, toAddr, message)
            m.quit()
        log_notify_email(fromUserName, toAddr, eventName)
        if globs.simulate:
            if globs.simulate_show_email:
                for line in message.split("\n"):
                    print tw.fill(line)
    except Exception, detail:
        log_message("error", "Failed to send email (%s) for event (%s)." % (detail, eventName))
