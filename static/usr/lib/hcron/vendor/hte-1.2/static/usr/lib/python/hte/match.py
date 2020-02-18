#! /usr/bin/env python
#
# hte/match.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Collection of match functions for use with the Node.find()
methods.
"""

from __future__ import absolute_import

from .base import Elem, Node, Raw, Text

class Matcher:

    def __init__(self, x, matchfn):
        self.x = x
        self.matchfn = matchfn

    def match(self, child):
        if self.matchfn == None:
            return True
        return self.matchfn(child, self.x)

def match_all(child, x, **kwargs):
    """Match all. Simple iterator.
    """
    return True

def match_any(child, x, **kwargs):
    """Match against text or element.
    """
    return isinstance(child, Node) and child == x

def match_anytext(child, x, **kwargs):
    """Match against text (Text or Raw).
    """
    return (isinstance(child, Text) or isinstance(child, Raw)) and child == x

def match_childregexp(child, x, **kwargs):
    """Match against element with a child that matches against a
    compiled regexp.
    """
    return isinstance(child, Elem) \
        and child.children \
        and match_regexp(child.children[0], x)

def match_childtext(child, x, **kwargs):
    """Match against element with a child that matches against text.
    """
    return isinstance(child, Elem) \
        and child.children \
        and match_text(child.children[0], x)

def match_elem(child, x, **kwargs):
    """Match minimally against an element (name only).
    """
    return isinstance(child, Elem) and child.tag == x.tag

def match_elemall(child, x, **kwargs):
    """Match against an element: name, attributes.
    """
    return isinstance(child, Elem) and child == x

def match_regexp(child, x, **kwargs):
    """Match against a compiled regexp.
    """
    return (isinstance(child, Text) or isinstance(child, Raw)) \
        and x.match(child.txt)

def match_text(child, x, **kwargs):
    """Match against text.
    """
    return isinstance(child, Text) and child == x
