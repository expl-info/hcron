#! /usr/bin/env python
#
# hte/__init__.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from __future__ import absolute_import

import string
from xml.sax.saxutils import escape, quoteattr

from .lib import ListType, StringTypes

FIND_PATH = 1
FIND_ELEM = 2

class Node(object):

    def __init__(self, tb, children=None):
        self.tb = tb
        self.children = children or []

    def __eq__(self, other):
        return False

    def _findn(self, count, matcher, parent, path, findtype):
        """A generator to return matches according to the provided
        matcher. Returned values are matched elements or the full
        path to the element (relative to the base element).
        """
        path = path or [parent]
        for i, child in enumerate(parent.children):
            if matcher.match(child):
                if findtype == FIND_PATH:
                    yield path+[child]
                    count -= 1
                else:
                    yield child
                    count -= 1
                if count <= 0:
                    return
            if isinstance(child, Node):
                for val in self._findn(count, matcher, child, path+[child], findtype):
                    yield val
                    count -= 1
                    if count <= 0:
                        return

    def _render(self):
        """Render all children to a flat list and return.
        """
        l = []
        for child in self.children:
            if isinstance(child, Node):
                l.extend(child._render())
            else:
                # warn?
                pass
        return l

    def add(self, *children):
        """Add zero/one or more children.
        """
        if children and type(children[0]) == ListType:
            children = children[0]
        for child in children:
            if isinstance(child, Node):
                if child.tb != None and type(self.tb) != type(child.tb):
                    # dissimilar builders
                    self.tb.warnings.append("mismatched tree type for child (%s)" % child)
                self.children.append(child)
            elif hasattr(child, "_render") and callable(child._render):
                self.children.append(child)
            else:
                # warn?
                pass
        return children and children[0]

    def find(self, matcher, findtype=FIND_ELEM):
        """Return the single/first match or None.
        """
        for e in self._findn(1, matcher, self, None, findtype):
            return e
        return None

    def findall(self, matcher, findtype=FIND_ELEM):
        """Return a generator to find all matches.
        """
        return self.findn(1<<31, matcher, findtype)

    def findn(self, count, matcher, findtype=FIND_ELEM):
        """Return a generator to find n matches.
        """
        return self._findn(count, matcher, self, None, findtype)

    def render(self):
        """Return the rendered list as a "joined" string.
        """
        return "".join(self._render())

class Elem(Node):
    """Generic element with tag specified. Children are optional, as
    are: id, class, and generic element attribute settings. Void
    element tags may be identified.
    """

    def __init__(self, tb, tag, void, *children, **kwargs):
        """Initialize the object where **kwargs provides all element
        attributes.
        """
        # to ensure string->Text promotion, set children via
        # Elem.set() or Elem.add() not Node.__init__()
        Node.__init__(self, tb)
        self.tag = tag
        self.void = void
        self.attrs = {}

        children = list(children)
        if children and type(children[0]) == ListType:
            children = children[0]
        self.set(children, **kwargs)

    def __eq__(self, other):
        if isinstance(other, Elem) \
            and self.tag == other.tag \
            and len(self.attrs) == len(other.attrs):
            oattrs = other.attrs
            for k, v in self.attrs.items():
                if k not in oattrs or v != oattrs[k]:
                    return False
            return True
        return False

    def __str__(self):
        return "<Elem tag=%s nattrs=%s nchildren=%s>" % (self.tag, len(self.attrs), len(self.children))

    def __repr__(self):
        return self.__str__()

    def _render(self):
        """Render the current element and its children, returning
        them in a flat list.
        """
        l = []
        if self.tag:
            al = []
            for k, v, in sorted(self.attrs.items()):
                if v == True:
                    al.append(k)
                elif v not in [None, False]:
                    # WARNING: does not handle non-string values
                    al.append("%s=%s" % (k, quoteattr(v)))
            attrs = " ".join(al)
            l.append("<%s%s%s>" % (self.tag, attrs and " " or "", attrs))
        l.extend(Node._render(self))
        if self.tag and not self.void:
            l.append("</%s>" % self.tag)
        return l

    def isvoid(self):
        return self.void

    def update_attrs(self, **kwargs):
        for k, v in kwargs.items():
            if k[0:1] == "_":
                k = k[1:]
                self.attrs[k] = v
            elif k == "attrs":
                self.attrs.update(v)

    def add(self, *children):
        """Override to support automatic conversion of strings to Text node.
        """
        children = list(children)
        if children:
            if type(children[0]) == ListType:
                children = children[0]
            children = [type(child) in StringTypes and Text(child) or child for child in children]
        return Node.add(self, children)

    def set(self, children=None, **kwargs):
        if children:
            # reset and add
            self.children = []
            self.add(children)
        if kwargs:
            self.attrs = {}
            self.update_attrs(**kwargs)
        return self

class Raw(Node):
    """Raw/unprocessed text.
    """

    def __init__(self, txt):
        Node.__init__(self, None)
        self.txt = txt

    def __eq__(self, other):
        return isinstance(other, Raw) and self.txt == other.txt

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Raw txt='%s'>" % (self.txt.replace("'", "\\'"),)

    def _render(self):
        """Render raw text as is (no escaping).
        """
        return [self.txt]

class Text(Node):

    def __init__(self, txt):
        """Text node.
        """
        Node.__init__(self, None)
        self.txt = txt

    def __eq__(self, other):
        return isinstance(other, Text) and self.txt == other.txt

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Text txt='%s'>" % (self.txt.replace("'", "\\'"),)

    def _render(self):
        """Return the text string.
        """
        return [escape(self.txt)]

class TreeBuilder:
    """Dynamically supports methods named to match tags subject to
    configuration.

    All top-level (i.e., non-prefixed) methods are reserved for
    element names (determined by the configuration). At
    instantiation, the following keyword arguments are supported:
    * anytag - allow any tag (bool)
    * attrminimize - automatically minimize attribute names (bool)
    * ignorecase - ignore tag case (bool)
    * lowercase - automatically lowercase tag name (bool)
    * voidtags - list of void tags (i.e., do not need closing tag)

    They affect handling and rendering.
    """

    def __init__(self, **kwargs):
        self._warnings = []

        # flags
        self._anytag = kwargs.get("anytag", False)
        self._attrminimize = kwargs.get("attrminimize", False)
        self._ignorecase = kwargs.get("ignorecase", False)
        self._lowercase = kwargs.get("lowercase", False)
        self._voidtags = kwargs.get("voidtags", [])

        opttags = kwargs.get("opttags", [])
        tags = kwargs.get("tags", [])
        voidtags = kwargs.get("voidtags", [])
        if self._lowercase or self._ignorecase:
            opttags = [s.lower() for s in opttags]
            tags = [s.lower() for s in tags]
            voidtags = [s.lower() for s in voidtags]
        self._opttags = set(opttags)
        self._tags = set(tags)
        self._voidtags = set(voidtags)

    def __getattr__(self, attr):
        """Return a special object which can be instatiated to an
        Elem object with the tag corresponding to the method name
        used and according to the configuration.
        """
        tag = self._normtag(attr)
        if tag == None:
            raise AttributeError(attr)
        def _Elem(*args, **kwargs):
            return self._elem(tag, *args, **kwargs)
        return _Elem

    def _elem(self, tag, *args, **kwargs):
        """Return instatiated Elem object according to the
        configuration.
        """
        tag = self._normtag(tag)
        if tag == None:
            raise AttributeError(tag)
        return Elem(self, tag, tag in self._voidtags, *args, **kwargs)

    def _isvoid(self, tag):
        return tag in self._voidtags

    def _normtag(self, tag):
        """Normalize tag according to the configuration.
        """
        _tag = self._ignorecase and tag.lower() or tag
        if _tag in self._tags or self._anytag:
            if not self._lowercase:
                _tag = tag
            return _tag
        return None
