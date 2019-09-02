#! /usr/bin/env python2
#
# hcron/hcrontree.py

# GPL--start
# This file is part of hcron
# Copyright (C) 2019 Environment/Environnement Canada
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

"""Hcron tree support.
"""

# system imports
import os
import os.path
import shutil
try:
    # try this first since python-2.7 has io.StringIO
    # which we do not want for python2
    from StringIO import StringIO
except:
    from io import StringIO
import tarfile
import tempfile

#
from hcron import globs
from hcron.constants import *
from hcron.library import copyfile, tostr, username2uid
from hcron.logger import *

class HcronTreeCache:
    """Interface to packaged hcron tree file containing members, or
    a directory path, rooted at "events/".
    """

    #def __init__(self, path, ignorematchfn=None):
    def __init__(self, username, ignorematchfn=None):
        def false_match(*args):
            return False

        self.username = username
        self.ignorematchfn = ignorematchfn or false_match
        self.cache = {}
        self.ignored = {}
        self.path = os.path.realpath(get_hcron_tree_filename(username, globs.fqdn))
        self.load()

    def get_contents(self, tree_path):
        return self.cache.get(tree_path)

    def get_event_contents(self, name):
        if name.startswith("/"):
            return self.get_contents(os.path.normpath("events/"+name))
        return None

    def get_event_names(self):
        names = []
        for name in self.cache.keys():
            if name.startswith("events/"):
                names.append(name[6:])
        return names

    def get_include_contents(self, name):
        """Kept for backward compatibility with v0.14. Discard for v0.16.
        """
        if name.startswith("/"):
            st = self.get_contents(os.path.normpath("includes/"+name))
            if st == None:
                st = self.get_contents(os.path.normpath("events/"+name))
            return st
        else:
            return None

    def get_names(self):
        return list(self.cache.keys())

    def is_ignored_event(self, name):
        return os.path.normpath("events/"+name) in self.ignored

    def load(self):
        """Load events from hcron tree file:
        - event files are loaded
        - symlinks are resolved
        - ignored are tracked
        - non-file members are discarded
        """
        if not os.path.exists(self.path):
            return

        if os.path.isdir(self.path) \
            and os.path.basename(self.path) == "events":
            _f = StringIO()
            f = tarfile.open(mode="w", fileobj=_f)
            f.add(self.path, "events")
            _f = StringIO(_f.getvalue())
            f = tarfile.open(fileobj=_f)
        else:
            f = tarfile.open(self.path)

        cache = {}
        ignored = {}
        link_cache = {}

        for m in f.getmembers():
            if m.name.startswith("events/"):
                name = os.path.normpath(m.name)
                basename = os.path.basename(name)
                dirname = os.path.dirname(name)

                if self.ignorematchfn(basename) or dirname in ignored:
                    ignored[name] = None
                else:
                    if m.issym():
                        link_cache[m.name] = self.resolve_symlink(m.name, m.linkname)
                    elif m.isfile():
                        cache[m.name] = tostr(f.extractfile(m).read())
                    else:
                        # need to track
                        cache[m.name] = None
        f.close()

        # resolve for symlinks
        for name, linkname in link_cache.items():
            for _ in range(10):
                if linkname in cache:
                    cache[name] = cache[linkname]
                    break
                elif linkname in link_cache:
                    linkname = self.resolve_symlink(linkname, link_cache[linkname])
                else:
                    # not found; drop
                    break

        # discard non-files
        for name in list(cache.keys()):
            if cache[name] == None:
                del cache[name]

        self.cache = cache
        self.ignored = ignored

    def resolve_symlink(self, name, linkname):
        if linkname.startswith("/"):
            return None
        return os.path.normpath(os.path.dirname(name)+"/"+linkname)

def create_user_hcron_tree_file(username, hostname, dstpath=None, empty=False):
    """Create an hcron tree file at dstpath with select members from
    srcpath.
    """
    if dstpath == None:
        dstpath = get_user_hcron_tree_filename(username, hostname)

    if empty:
        # truncate
        open(dstpath, "w")
        return

    cwd = os.getcwd()
    f = None
    names = ["events"]

    try:
        # temp file
        user_hcron_tree_home = get_user_hcron_tree_home(username, hostname)
        _, tmppath = tempfile.mkstemp(prefix="snapshot-", dir=user_hcron_tree_home)

        # create tar
        os.chdir(user_hcron_tree_home)
        f = tarfile.open(tmppath, mode="w:gz")
        for name in names:
            try:
                f.add(name)
            except:
                pass
        f.close()

        # move into place
        if os.path.exists(dstpath):
            # in case following move() is not atomic
            os.remove(dstpath)
        shutil.move(tmppath, dstpath)
    except:
        if f:
            f.close()
    os.chdir(cwd)

    max_hcron_tree_snapshot_size = globs.config.get().get("max_hcron_tree_snapshot_size", CONFIG_MAX_HCRON_TREE_SNAPSHOT_SIZE)
    if os.path.getsize(dstpath) > max_hcron_tree_snapshot_size:
        raise Exception("snapshot file too big (>%s)" % max_hcron_tree_snapshot_size)

def get_hcron_tree_filename(username, hostname):
    """Saved hcron tree file for user.
    """
    return os.path.normpath("%s/%s" % (get_hcron_tree_home(username, hostname), username))

def get_hcron_tree_home(username, hostname):
    """Home of saved user hcron trees.
    """
    return os.path.normpath(HCRON_TREES_HOME)

def get_user_hcron_tree_filename(username, hostname):
    """Hcron tree file under user home.
    """
    return os.path.normpath("%s/snapshot" % get_user_hcron_tree_home(username, hostname))

def get_user_hcron_tree_home(username, hostname):
    """Hcron tree directory under user home.
    """
    return os.path.expanduser("~%s/.hcron/%s" % (username, hostname))

def install_hcron_tree_file(username, hostname):
    """Install/replace an hcron file for use by hcron-scheduler.

    SECURITY: src must be read as user, dst written as "root".
    """
    systemhthome = get_hcron_tree_home(username, hostname)
    srcpath = get_user_hcron_tree_filename(username, hostname)
    dstpath = get_hcron_tree_filename(username, hostname)

    if not os.path.exists(systemhthome):
        os.makedirs(systemhthome)

    try:
        uid = username2uid(username)
        os.seteuid(uid)
        src = open(srcpath, "r")
    except:
        os.seteuid(0)
        raise

    os.seteuid(0)
    try:
        os.remove(dstpath)
    except:
        pass

    if os.path.getsize(srcpath) > 0:
        max_hcron_tree_snapshot_size = globs.config.get().get("max_hcron_tree_snapshot_size", CONFIG_MAX_HCRON_TREE_SNAPSHOT_SIZE)
        copyfile(src, dstpath, max_hcron_tree_snapshot_size)
