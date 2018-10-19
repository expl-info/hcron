#! /usr/bin/env python2
#
# safeeval.py

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

"""This code is taken from:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/364469

Title: "Sage" Eval
Submitter: Michael Spencer
Last Updated: 2006/03/26
Version no: 1.1
Category: Text

Description:

Evaluate constant expressions, including list, dict and tuple using
the abstract syntax tree created by compiler.parse. Since compiler
does the work, handling arbitratily nested structures is transparent,
and the implemenation is very straightforward.

Support for None is added in visitName() [JM].
Support for True|False is added in visitName() [JM - 2008/05/02].
"""

import compiler

class Unsafe_Source_Error(Exception):
    def __init__(self,error,descr = None,node = None):
        self.error = error
        self.descr = descr
        self.node = node
        self.lineno = getattr(node,"lineno",None)
        
    def __repr__(self):
        return "Line %d.  %s: %s" % (self.lineno, self.error, self.descr)
    __str__ = __repr__    
           
class SafeEval(object):
    
    def visit(self, node,**kw):
        cls = node.__class__
        meth = getattr(self,'visit'+cls.__name__,self.default)
        return meth(node, **kw)
            
    def default(self, node, **kw):
        for child in node.getChildNodes():
            return self.visit(child, **kw)
            
    visitExpression = default
    
    def visitConst(self, node, **kw):
        return node.value

    def visitDict(self,node,**kw):
        return dict([(self.visit(k),self.visit(v)) for k,v in node.items])
        
    def visitTuple(self,node, **kw):
        return tuple([self.visit(i) for i in node.nodes])
        
    def visitList(self,node, **kw):
        return [self.visit(i) for i in node.nodes]

    def visitName(self, node, **kw):
        if node.name == "None":
            return None
        elif node.name == "True":
            return True
        elif node.name == "False":
            return False

class SafeEvalWithErrors(SafeEval):

    def default(self, node, **kw):
        raise Unsafe_Source_Error("Unsupported source construct",
                                node.__class__,node)
            
    def xxxvisitName(self,node, **kw):
        # taken from comments by Niki Spahiev, 2005/06/28
        if node.name == 'None':
            return None

        raise Unsafe_Source_Error("Strings must be quoted", 
                                 node.name, node)
                                 
    # Add more specific errors if desired
            

def safe_eval(source, fail_on_error = True):
    walker = fail_on_error and SafeEvalWithErrors() or SafeEval()
    try:
        ast = compiler.parse(source,"eval")
    except SyntaxError, err:
        raise
    try:
        return walker.visit(ast)
    except Unsafe_Source_Error, err:
        raise
