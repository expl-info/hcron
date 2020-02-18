#! /usr/bin/env python
#
# hte/lib.py

# Copyright 2014 John Marshall. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import sys as _sys

ListType = list

if _sys.version_info.major == 2:
    StringTypes = [str, unicode]
else:
    StringTypes = [str]

del _sys
