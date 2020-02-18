#! /usr/bin/env python
#
# hte/html5.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from __future__ import absolute_import

from .base import TreeBuilder

TAGS = [
    "a", "abbr", "acronym", "address", "applet", "area", "article", "aside", "audio",
    "b", "base", "basefont", "bdi", "bdo", "big", "blockquote", "body", "br", "button",
    "canvas", "caption", "center", "cite", "code", "col", "colgroup",
    "datalist", "dd", "del", "details", "dfn", "dialog", "dir", "div", "dl", "dt",
    "em", "embed",
    "fieldset", "figcaption", "figure", "font", "footer", "form", "frame", "frameset",
    "head", "header", "hgroup", "h1", "h2", "h3", "h4", "h5", "h6","hr", "html",
    "i", "iframe", "img", "input", "ins",
    "kbd", "keygen",
    "label", "legend", "li", "link",
    "main", "map", "mark", "menu", "menuitem", "meta", "meter",
    "nav", "noframes", "noscript",
    "object", "ol", "optgroup", "option", "output",
    "p", "param", "pre", "progress",
    "q",
    "rp", "rt", "ruby",
    "s", "samp", "script", "section", "select", "small", "source", "span", "strike",
        "strong", "style", "sub", "summary", "sup",
    "table", "tbody", "td", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "tt",
    "u", "ul",
    "var", "video",
    "wbr",
]

# omision of end tags for non-void tag elements in HTML5 is cookoo
# (e.g., http://www.w3.org/TR/html-markup/li.html#li-tags)
VOIDTAGS = [ "area", "base", "br", "col", "embed", "hr", "img",
    "input", "keygen", "link", "meta", "param", "source", "track", "wbr",

    "basefont", "frame", "isindex",
]

OPTTAGS = [
    "body", "colgroup", "dd", "dt", "head", "html", "li", "optgroup",
    "option", "p", "tbody", "td", "tfoot", "th", "thead", "tr",
]

class Html5TreeBuilder(TreeBuilder):

    def __init__(self, **kwargs):
        attrs = {
            "anytag": False,
            "attrminimize": True,
            "ignorecase": True,
            "lowercase": True,
            "opttags": OPTTAGS[:],
            "tags": TAGS[:],
            "voidtags": VOIDTAGS[:],
        }
        attrs.update(**kwargs)
        TreeBuilder.__init__(self, **attrs)

class XHtml5TreeBuilder(TreeBuilder):

    def __init__(self, **kwargs):
        attrs = {
            "anytag": False,
            "attrminimize": False,
            "ignorecase": False,
            "lowercase": True,
            "opttags": [],
            "tags": TAGS[:],
            "voidtags": [],
        }
        attrs.update(**kwargs)
        TreeBuilder.__init__(self, **attrs)
