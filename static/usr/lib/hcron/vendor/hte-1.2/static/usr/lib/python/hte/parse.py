#! /usr/bin/env python
#
# hte/parse.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Parsers that produce HTE trees.

For HTML5:
    f = urllib2.urlopen("https://expl.info/display/HTE/Home")
    txt = f.read()
    p = HtmlParser(Html5TreeBuilder())
    doc = p.load(txt)
"""

from __future__ import absolute_import

import xml.parsers.expat
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

from . import Elem

class LocalHtmlParser(HTMLParser):
    pass

    #def handle_starttag(self, tag, attrs):
        #pass

    #def handle_endtag(self, tag):
        #pass

    #def handle_data(self, text):
        #pass

class BaseParser:
    """Base parser with element handlers.
    """

    def __init__(self, tb, ignorevoiderrors=False):
        self._tb = tb
        self._top = Elem(self._tb, None, False)
        self.stack = []

    def char_data(self, text):
        last = self.stack[-1]
        last.add(text)

    def end_element(self, name):
        #print "end (%s)" % (name,)
        if self._tb._isvoid(name):
            return
        last = self.stack[-1]
        while last.tag != name:
            if last.tag not in self._tb._opttags:
                raise Exception("error: end tag expected (%s) got (%s)" % (last.tag, name))
            self.stack.pop()
            last = self.stack[-1]
        self.stack.pop()

    def load(self, s):
        """Parse ML from string.
        """
        self.stack = [self._top]
        self.parse(s)
        return self.stack[0]

    def loadf(self, f):
        """Parse ML from file.
        """
        self.stack = [self._top]
        self.parsef(f)
        return self.stack[0]

    def start_element(self, name, attrs):
        #print "start (%s) (%s)" % (name, attrs)
        last = self.stack[-1]
        el = self._tb._elem(name, attrs=dict(attrs))
        last.add(el)
        if not el.isvoid():
            self.stack.append(el)

class HtmlParser(BaseParser):
    """Base parser for HTML.
    """

    def __init__(self, tb):
        BaseParser.__init__(self, tb)
        self.p = LocalHtmlParser()
        self.p.handle_data = self.char_data
        self.p.handle_endtag = self.end_element
        self.p.handle_starttag = self.start_element

    def parse(self, s):
        self.p.feed(s)

    def parsef(self, f):
        self.p.feed(f.read())

class XmlParser(BaseParser):
    """Base parser for XML.
    """

    def __init__(self, tb):
        BaseParser.__init__(self, tb)
        self.p = xml.parsers.expat.ParserCreate()
        self.p.CharacterDataHandler = self.char_data
        self.p.EndElementHandler = self.end_element
        self.p.StartElementHandler = self.start_element

    def parse(self, s):
        self.p.Parse(s)

    def parsef(self, f):
        self.p.ParseFile(f)
