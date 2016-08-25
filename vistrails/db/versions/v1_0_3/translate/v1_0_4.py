###############################################################################
##
## Copyright (C) 2014-2016, New York University.
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

import copy
from vistrails.db.versions.v1_0_3.domain import DBVistrail, DBAnnotation, \
    DBWorkflow, DBLog, DBRegistry, DBPortSpec, DBAdd, DBChange, DBDelete, \
    DBMashuptrail, DBMachine
from vistrails.core import debug
from vistrails.core.system import get_elementtree_library
ElementTree = get_elementtree_library()

id_scope = None

def translateVistrail(_vistrail):
    """ Translate new DBVistrailVariable based vistrail variables to old
         annotation based type """
    global id_scope
    
    def update_workflow(old_obj, trans_dict):
        return DBWorkflow.update_version(old_obj.db_workflow, 
                                         trans_dict, DBWorkflow())

    def update_operations(old_obj, trans_dict):
        new_ops = []
        for obj in old_obj.db_operations:
            if obj.vtType == 'delete':
                new_ops.append(DBDelete.update_version(obj, trans_dict))
            elif obj.vtType == 'add':
                new_op = DBAdd.update_version(obj, trans_dict)
                new_ops.append(new_op)
            elif obj.vtType == 'change':
                new_op = DBChange.update_version(obj, trans_dict)
                new_ops.append(new_op)
        return new_ops

    vistrail = DBVistrail()
    id_scope = vistrail.idScope

    translate_dict = {'DBAction': {'operations': update_operations},
                      'DBGroup': {'workflow': update_workflow}
                      }

    if _vistrail.db_controlParameters:
        debug.warning(("Vistrail contains %s control parameters that "
                      "cannot be converted") % len(_vistrail.db_controlParameters))
    vistrail = DBVistrail.update_version(_vistrail, translate_dict, vistrail)

    vistrail.db_version = '1.0.3'
    return vistrail

machine_id = 1
machine_id_remap = {}

def translateLog(_log):
    global machine_id, machine_id_remap
    machines = {}
    def update_machines(old_obj, trans_dict):
        global machine_id, machine_id_remap
        machine_id_remap = {}
        for m in old_obj.db_machines:
            old_id = m.db_id
            m_key = (m.db_name, m.db_os, m.db_architecture, m.db_processor,
                     m.db_ram)
            if m_key not in machines:
                new_machine = DBMachine.update_version(m, trans_dict)
                new_machine.db_id = machine_id
                machines[m_key] = new_machine
                machine_id_remap[old_id] = machine_id
                machine_id += 1
            else:
                machine_id_remap[old_id] = machines[m_key].db_id
        return old_obj.db_completed
    def update_machine_id(old_obj, trans_dict):
        if old_obj.db_machine_id in machine_id_remap:
            return machine_id_remap[old_obj.db_machine_id]
        return old_obj.db_machine_id
    translate_dict = {'DBWorkflowExec': {'completed': update_machines},
                      'DBModuleExec': {'machine_id': update_machine_id},
                      'DBGroupExec': {'machine_id': update_machine_id}}
    log = DBLog.update_version(_log, translate_dict)
    for m in machines.itervalues():
        log.db_add_machine(m)
    log.db_version = '1.0.3'
    return log