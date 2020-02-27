#! /usr/bin/env python3
#
# hcron_doc.py

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

import os
import os.path
import re
import sys
from sys import stderr
import tempfile
import traceback

from hcron.constants import *
from hcron import globs
from hcron.event import Event, EventList
from hcron.hcrontree import create_user_hcron_tree_file
from hcron.library import whoami
from hcron.server import setup
from vendor import hte

def absname(dirname, name):
    """Return absolute event name.
    """
    return os.path.abspath(os.path.join(dirname, name))

def collect_info(events):
    """Collect event information into a dictionary.
    """
    info = {
        "events": {},
        "indexes": {},
    }

    # events
    d = info["events"]
    for name, ev in events.items():
        dd = d[name] = {}
        ddd = dd["fields"] ={}
        for k, v in ev.assignments:
            if k.islower():
                ddd[k] = v
        dd["lines_raw"] = ev.lines_raw[:]

    # indexes
    d = info["indexes"]
    for name in HCRON_DOC_EVENT_FIELD_NAMES:
        d[name] = {}
    for name, dd in info["events"].items():
        dirname = os.path.dirname(name)
        for k, v in dd["fields"].items():
            if not v:
                continue
            l = []
            if k in ["failover_event", "template_name"]:
                if "$" not in v:
                    l = [absname(dirname, v)]
            elif k in ["host"]:
                if "$" not in v:
                    l = [v]
            elif k in ["label"]:
                l = [v for v in v.split(",") if "$" not in v]
            elif k in ["contact", "notify_email"]:
                l = [v for v in v.split(",") if "$" not in v and "@" in v]
            elif k in ["next_event"]:
                l = [absname(dirname, v) for v in v.split(":") if "$" not in v]

            for v in l:
                d[k].setdefault(v, []).append(name)

    #import pprint
    #stderr.write("%s\n" % pprint.pformat(info))
    return info

def generate_doc(info, styling):
    """Generate html document using collected event information.
    """
    hreffmt = styling.get("hreffmt")
    showemptyfields = styling.get("showemptyfields")
    showsource = styling.get("showsource")
    toccode = styling.get("toccode")

    tb = hte.Html5TreeBuilder()
    doc = tb.html()

    # toc
    if toccode:
        doc.add(hte.Raw(toccode))
    else:
        doc.add(tb.h1("Contents"))
        toc = doc.add(tb.ul())
        toc.add([
            tb.li(tb.a("Summary", _href="#Summary")),
            tb.li(tb.a("Events", _href="#Events")),
            tb.li(tb.a("Indexes", _href="#Indexes")),
        ])

    eventsd = info["events"]
    indexesd = info["indexes"]

    # summary
    doc.add(tb.h1("Summary", _id="Summary"))
    table = doc.add(tb.table())
    table.add(tb.tr(tb.th("Name"), tb.th("Description"), tb.th("Contact"), tb.th("URL"), tb.th("Labels")))
    for name, d in sorted(eventsd.items()):
        fieldsd = d["fields"]
        table.add(tb.tr(
            tb.td(linkify_eventname(tb, "", name, hreffmt)),
            tb.td(fieldsd.get("description", "")),
            tb.td(linkify_email(tb, fieldsd.get("contact", ""))),
            tb.td(fieldsd.get("URL", "")),
            tb.td(fieldsd.get("label", "")),
        ))

    # event sections
    doc.add(tb.h1("Events", _id="Events"))
    for name, d in sorted(eventsd.items()):
        fieldsd = d["fields"]

        doc.add(tb.h2(name, _id="%s" % name))
        doc.add(tb.h3("Fields"))
        tab = doc.add(tb.table())
        dirname = os.path.dirname(name)
        for k in HCRON_DOC_EVENT_FIELD_NAMES:
            v = fieldsd.get(k, "")
            if showemptyfields == False and not v:
                continue
            if k in ["notify_email"]:
                tab.add(tb.tr(tb.th(k), tb.td(linkify_emails(tb, v))))
            elif k in ["template_name"]:
                tab.add(tb.tr(tb.th(k), tb.td(linkify_eventname(tb, dirname, v, hreffmt))))
            elif k in ["failover_event", "next_event"]:
                tab.add(tb.tr(tb.th(k), tb.td(linkify_eventnames(tb, dirname, v, hreffmt, ":"))))
            else:
                if k in ["command", "notify_message"]:
                    v = v and tb.pre(v)
                tab.add(tb.tr(tb.th(k), tb.td(v)))
        if showsource:
            doc.add(tb.h3("Source"))
            doc.add(tb.pre("\n".join(d["lines_raw"])))

    # indexes
    doc.add(tb.h1("Indexes", _id="Indexes"))
    for indexname in HCRON_DOC_INDEX_NAMES:
        doc.add(tb.h2("By %s" % indexname))
        table = doc.add(tb.table())
        table.add(tb.tr(tb.th("Field Value"), tb.th("Events")))
        for k, names in sorted(indexesd[indexname].items()):
            names = sorted(names)
            l = interleave_with_separator([linkify_eventname(tb, "", x, hreffmt) for x in names], " ")
            if indexname in ["failover_event", "next_event", "template_name"]:
                k = linkify_eventname(tb, "", k, hreffmt)
            if indexname == "notify_email":
                k = linkify_email(tb, k)
            table.add(tb.tr(tb.td(k), tb.td(l)))

    return doc.render()

def interleave_with_separator(l, sep):
    """Insert separator between each list item.
    """
    if not l:
        return []
    l2 = [l[0]]
    for x in l[1:]:
        l2.extend([sep, x])
    return l2

def linkify_email(tb, s):
    """Return link for email address.
    """
    if "@" in s:
        return tb.a(s, _href="mailto:%s" % s)
    return s

def linkify_emails(tb, s):
    """Return links for email addresses.
    """
    l = [linkify_email(tb, x) for x in s.split(",")]
    l = interleave_with_separator(l, ",")
    return l

def linkify_eventname(tb, dirname, s, hreffmt):
    """Return link for event name.
    """
    if "$" not in s:
        return tb.a(s, _href=hreffmt % os.path.join(dirname, s))
    return s

def linkify_eventnames(tb, dirname, s, hreffmt, sep=None):
    """Return links for event names.
    """
    l = not sep and [s] or s.split(":")
    l = [linkify_eventname(tb, dirname, x, hreffmt) for x in l]
    if sep:
        l = interleave_with_separator(l, sep)
    return l

def print_usage():
    print("""\
usage: hcron doc [<options>] <eventsdir>|<snapshotfile>
       hcron doc -h|--help

Generate documentation (in HTML) for all or part of the events defined
in <eventsdir> or <snapshotfile>.

Options:
-c <confpath>       Path of the hcron configuration file. Default is to
                    use the hcron.conf file provided with the package
                    (which is usually appropriate).
-e <pattern>        Filter by event name regexp pattern.
--href-fmt <fmt>    href format string. Default is "#%s" where the
                    event name is provided.
--show-empty-fields Show empty fields in event display.
--show-source       Include source in event display.""")

def main(args):
    try:
        configpath = None
        eventcre = None
        pattern = None
        showjson = False
        eventssrc = None
        styling = {
            "hreffmt": "#%s",
            "showemptyfields": False,
            "showsource": False,
            "toccode": None,
        }

        while args:
            arg = args.pop(0)
            if arg == "-c" and args:
                configpath = args.pop(0)
            elif arg == "--debug":
                globs.debug = True
            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "-e" and args:
                pattern = args.pop(0)
                eventcre = re.compile(pattern)
            elif arg == "--href-fmt" and args:
                styling["hreffmt"] = args.pop(0)
            elif arg == "--show-empty-fields":
                styling["showemptyfields"] = True
            elif arg == "--show-json":
                showjson = True
            elif arg == "--show-source":
                styling["showsource"] = True
            elif arg == "--toc-code" and args:
                styling["toccode"] = args.pop(0)
            elif not args:
                eventssrc = os.path.realpath(arg)
            else:
                raise Exception()

        if None in [configpath, eventssrc]:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: bad/missing argument\n")
        sys.exit(1)

    try:
        eventsdir = None
        snapshotpath = None

        if configpath:
            configpath = os.path.realpath(configpath)
        else:
            etcdir = os.path.realpath("%s/../../etc" % os.path.dirname(sys.argv[0]))
            configpath = os.path.join(etcdir, "hcron/hcron-run.conf")

        setup(configpath)

        if os.path.isdir(eventssrc):
            # prepare snapshot file
            eventsdir = os.path.dirname(eventssrc)
            # temp file
            _, snapshotpath = tempfile.mkstemp(prefix="hcrondoc-snapshot-", dir="/tmp")

            create_user_hcron_tree_file(whoami(), globs.servername, srcpath=eventsdir, dstpath=snapshotpath)
        else:
            # already have snapshot file
            snapshotpath = eventssrc

        el = EventList(whoami(), path=snapshotpath, dumptofile=False)
        if eventcre:
            for name in list(el.events.keys()):
                if not eventcre.match(name):
                    del el.events[name]

        info = collect_info(el.events)
        if showjson:
            import json
            print(json.dumps(info, indent=2))
        else:
            html = generate_doc(info, styling)
            print(html)
    except SystemExit:
        raise
    except:
        if globs.debug:
            traceback.print_exc()
        stderr.write("error: failed to run\n")
        sys.exit(1)
    finally:
        # only delete snapshot file if temporary built from dir
        if eventsdir and snapshotpath and os.path.exists(snapshotpath):
            os.remove(snapshotpath)
