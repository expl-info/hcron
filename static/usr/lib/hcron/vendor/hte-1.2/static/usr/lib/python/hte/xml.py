#! /usr/bin/env python
#
# hte/xml.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from __future__ import absolute_import

from .base import TreeBuilder

class XmlTreeBuilder(TreeBuilder):

    def __init__(self, **kwargs):
        attrs = {
            "anytag": True,
            "attrminimize": False,
            "ignorecase": False,
            "lowercase": False,
            "opttags": [],
            "tags": [],
            "voidtags": [],
        }
        attrs.update(**kwargs)
        TreeBuilder.__init__(self, **attrs)
