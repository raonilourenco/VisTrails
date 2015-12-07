###############################################################################
##
## Copyright (C) 2014-2015, New York University.
## Copyright (C) 2011-2014, NYU-Poly.
## Copyright (C) 2006-2011, University of Utah.
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice,
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright
##    notice, this list of conditions and the following disclaimer in the
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the New York University nor the names of its
##    contributors may be used to endorse or promote products derived from
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################
from __future__ import division

import os.path

from vistrails.core.wrapper.specs import SpecList, ClassSpec, \
    FunctionSpec
from vistrails.core.wrapper.pythonclass import gen_class_module
from vistrails.core.wrapper.pythonfunction import gen_function_module

from identifiers import *

# fun_spec_name = os.path.join(current_dot_vistrails(),
#                          'numpy-%s-spec-%s-functions.xml' %
#                          (np.__version__.replace('.', '_'),
#                           version.replace('.', '_')))
# raw_fun_spec_name = fun_spec_name[:-4] + '-raw.xml'
# fun_spec_diff = os.path.join(this_dir, 'function-diff.xml')

this_dir = os.path.dirname(os.path.realpath(__file__))
_modules = []

class_spec_name = os.path.join(this_dir,'classes.xml')
class_list = SpecList.read_from_xml(class_spec_name, ClassSpec)
_modules.extend([gen_class_module(spec) for spec in class_list.module_specs])

func_spec_name = os.path.join(this_dir,'functions.xml')
func_list = SpecList.read_from_xml(func_spec_name, FunctionSpec)
_modules.extend([gen_function_module(spec) for spec in func_list.module_specs])