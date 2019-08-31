#! /usr/bin/env python2
#
# hcron/assign.py

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

"""Support for variable substitution in hcron event lines.
"""

import fnmatch
import re
import traceback

#SUBST_NAME_RE = "(?P<op>[#$])(?P<name>HCRON_\w*)"
SUBST_NAME_RE = "(?P<op>[#$])(?P<name>\w+)"
SUBST_NAME_CRE = re.compile(SUBST_NAME_RE)
       
#SUBST_NAME_SELECT_RE = "(?P<op>[#$])(?P<name>HCRON_\w*)(((?P<square_bracket>\[)(?P<square_select>.*)\])|((?P<curly_bracket>\{)(?P<curly_select>.*)\}))?"
SUBST_NAME_SELECT_RE = "(?P<op>[#$])(?P<name>\w+)(((?P<square_bracket>\[)(?P<square_select>.*)\])|((?P<curly_bracket>\{)(?P<curly_select>.*)\}))?"
#SUBST_SEP_LIST_RE = "(?:(?P<sep>.*)!)?(?P<list>.*)"
SUBST_SEP_RE = "(?P<split_sep>[^?!]*)((?:\?)(?P<join_sep>[^!]*))?!"
SUBST_SEP_LIST_RE = "(?:(%s))?(?P<list>.*)" % SUBST_SEP_RE
SUBST_LIST_RE = "(.*)(?:,(.*))?"
SUBST_SLICE_RE = "(-?\d*)(:(-?\d*))?(:(-?\d*))?"
SUBST_NAME_SELECT_CRE = re.compile(SUBST_NAME_SELECT_RE)
SUBST_SEP_LIST_CRE = re.compile(SUBST_SEP_LIST_RE)
SUBST_LIST_CRE = re.compile(SUBST_LIST_RE)
SUBST_SLICE_CRE = re.compile(SUBST_SLICE_RE)

def hcron_variable_substitution(value, varinfo, depth=1):
    """Perform variable substitution.

    Search for substitutable segments, substitute, repeat. Once a
    substitution is done, that segment is not treated again.
    """
    l = []
    lastpos = 0
    while True:
        if 0:
            s = SUBST_NAME_SELECT_CRE.search(value, lastpos)
            if s == None:
                break
            startpos, endpos = s.span()

        startpos, endpos = search_name_select(value, lastpos)

        if startpos == None:
            break

        l.append(value[lastpos:startpos])
        l.append(hcron_variable_substitution2(value[startpos:endpos], varinfo))
        lastpos = endpos

    l.append(value[lastpos:])

    #open("/tmp/hc", "a").write("value (%s) -> (%s)\n" % (value, "".join(l)))

    return "".join(l)

def hcron_variable_substitution2(value, varinfo, depth=1):
    """Recursively resolve all variables in value with settings in
    varinfo. The mechanism is:
    1) match
    2) resolve
    3) proceed to next match level (name, select, ...)
    """
    try:
        # default
        substSplitSep = ":"

        nid = SUBST_NAME_SELECT_CRE.match(value).groupdict()
        #open("/tmp/hc", "a").write("nid (%s)\n" % str(nid))

        op = nid.get("op")
        substName = nid.get("name")
        nameValue = varinfo.get(substName)
        substBracket = nid.get("square_bracket") and "[" or (nid.get("curly_bracket") and "{") or None
        #open("/tmp/hc", "a").write(" **** substBracket *** (%s)\n" % substBracket)
        if substBracket == "[":
            substSelect = nid.get("square_select", "")
        elif substBracket == "{":
            substSelect = nid.get("curly_select", "")
        else:
            substSelect = None
        substSelect = hcron_variable_substitution2(substSelect, varinfo, depth+1)


        if substSelect == None:
            # no select
            if nameValue != None:
                value = nameValue
        else:
            sid = SUBST_SEP_LIST_CRE.match(substSelect).groupdict()
            substSplitSep = sid.get("split_sep")
            substJoinSep = sid.get("join_sep")
            if substSplitSep == None:
                # special case!
                substSplitSep = substName == "HCRON_EVENT_NAME" and "/" or ":"
            elif substSplitSep == "":
                pass
            else:
                substSplitSep = hcron_variable_substitution2(substSplitSep, varinfo, depth+1)
            if substJoinSep == None:
                substJoinSep = substSplitSep
            else:
                substJoinSep = hcron_variable_substitution2(substJoinSep, varinfo, depth+1)

            if substSplitSep == "":
                nameValues = list(nameValue)
            else:
                nameValues = nameValue.split(substSplitSep)

            substList = sid["list"]
            substList = hcron_variable_substitution2(substList, varinfo, depth+1)

            # fix RE to avoid having to check for None for single list value
            ll = substList.split(",")
            #open("/tmp/hc", "a").write("-- ll (%s)\n" % str(ll))

            if substBracket == "[":
                # indexing
                for i in range(len(ll)):
                    ll[i] = hcron_variable_substitution2(ll[i], varinfo, depth+1)
                    #open("/tmp/hc", "a").write("---- ll (%s) i (%s) ll[i] (%s)\n" % (str(ll), i, ll[i]))
                    # normalize: empty -> None
                    irl = [ el != "" and el or None for el in SUBST_SLICE_CRE.match(ll[i]).groups() ]
                    #open("/tmp/hc", "a").write("------- irl (%s)\n" % str(irl))
                    start, endColon, end, stepColon, step = irl[0:5]
                    start = hcron_variable_substitution2(start, varinfo, depth+1)
                    end = hcron_variable_substitution2(end, varinfo, depth+1)
                    step = hcron_variable_substitution2(step, varinfo, depth+1)

                    if step != None:
                        step = int(step)
                    else:
                        step = 1
                    if start != None:
                        start = int(start)
                    if end != None:
                        end = int(end)
                    else:
                        if endColon == None:
                            if start < 0:
                                end = start-1
                                step = -1
                            else:
                                end = start+1
                                step = 1

                    ll[i] = substJoinSep.join(nameValues[start:end:step])
                    #open("/tmp/hc", "a").write("------------ ll[i] (%s)\n" % str(ll[i]))
            elif substBracket == "{":
                # matching: substitute, match, flatten
                ll = [ hcron_variable_substitution2(x, varinfo, depth+1) for x in ll ]
                #open("/tmp/hc", "a").write("---- ll (%s) nameValues (%s)\n" % (str(ll), nameValues))
                ll = [ el for x in ll for el in fnmatch.filter(nameValues, x) ]
                #open("/tmp/hc", "a").write("------ ll (%s)\n" % str(ll))

            value = substJoinSep.join(ll)

        if op == "#" and nameValue != None:
            #open("/tmp/hc", "a").write("*** name (%s) nameValue (%s) sep (%s) value (%s) count (%s)\n" % (substName, nameValue, substSplitSep, value, value.count(substSplitSep)+1))
            value = str(value.count(substSplitSep)+1)
    except:
        #print(traceback.print_exc())
        pass

    return value

def search_name_select(st, lastpos):
    """Find startpos and endpos for:
    1. [#$]<name>[<body>]
    2. [#$]<name>{<body>}
    3. [#$]<name>
    otherwise:
    3. None, None
    """
    startpos, endpos = None, None
    s = SUBST_NAME_CRE.search(st, lastpos)
    if s:
        startpos, endpos = s.span()
        if endpos < len(st):
            openb = st[endpos]
            if openb in [ "[", "{" ]:
                if openb == "[":
                    closeb = "]"
                elif openb == "{":
                    closeb = "}"

                depth = 0
                for ch in st[endpos:]:
                    if ch == openb:
                        depth += 1
                    elif ch == closeb:
                        depth -= 1
                        if depth == 0:
                            endpos += 1
                            break
                    endpos += 1
                else:
                    # no closing bracket
                    startpos = None
                    endpos = None

    return startpos, endpos
 
def eval_assignments(assignments, varinfo):
    """Evaluate assignments using the settings in varinfo and storing the
    results back to varinfo.
    """
    for name, value in assignments:
        varinfo[name] = hcron_variable_substitution(value, varinfo)

def load_assignments(lines):
    """Load lines with the format name=value into a list of
    (name, value) tuples.
    """
    l = []

    for line in lines:
        name, value  = line.split("=", 1)
        l.append((name.strip(), value.strip()))

    return l
