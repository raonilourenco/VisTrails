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

from PyQt4 import QtCore

from vistrails.gui.base_view import BaseView
from vistrails.gui.debugging.debug_table import QDebugWidget
from vistrails.gui.theme import CurrentTheme
from vistrails.core import debug

class QDebugView(QDebugWidget, BaseView):
    explorationId = 0
    
    def __init__(self, parent=None):
        QDebugWidget.__init__(self, parent)
        BaseView.__init__(self)

        self.set_title("Debug")
        self.connect(self.table,
                     QtCore.SIGNAL('debugChange(bool)'),
                     self.debugChange)

    def set_controller(self, controller):
        if self.controller == controller:
            return
        self.controller = controller
        self.set_exploration()
        
    def updatePipeline(self, pipeline):
        name = self.controller.get_pipeline_name()
        self.set_title("Debug: %s" % name)

    def set_exploration(self, pe=None):
        if not pe:
            pe = self.controller.current_debugging
        self.setParameterExploration(pe)

    def set_default_layout(self):
        from vistrails.gui.paramexplore.pe_inspector import QParamExploreInspector
        from vistrails.gui.debugging.param_view import QDebugParameterView
        self.set_palette_layout(
            {QtCore.Qt.LeftDockWidgetArea: QParamExploreInspector,
             QtCore.Qt.RightDockWidgetArea: QDebugParameterView,
             })
            
    def set_action_links(self):
        self.action_links = \
            {
              'execute': ('debug_changed', self.explore_non_empty),
            }

    def set_action_defaults(self):
        self.action_defaults.update(
            { 'execute': [('setEnabled', True, self.set_execute_action),
                          ('setIcon', False, CurrentTheme.EXECUTE_DEBUG_ICON),
                          ('setToolTip', False, 'Execute debugging')],
              'publishWeb': [('setEnabled', False, False)],
              'publishPaper': [('setEnabled', False, False)],
            })
            
    def set_execute_action(self):
        if self.controller and self.controller.vistrail:
            versionId = self.controller.current_version
            return self.controller.vistrail.get_paramexp(versionId) is not None
        return False
    
    def explore_non_empty(self, on):
        return on
    
    def debugChange(self, on):
        from vistrails.gui.vistrails_window import _app
        _app.notify('debug_changed', on)
        
    def execute(self):
        """ execute() -> None        
        Perform the exploration by collecting a list of actions
        corresponding to each dimension
        
        """
        # persist the parameter exploration
        pe = self.getParameterExploration()
        pe.action_id = self.controller.current_version

        # check if pe has changed
        changed = False
        if not self.controller.current_debugging or \
         pe != self.controller.current_debugging:
            changed = True
            pe.name = ''
            self.controller.current_debugging = pe
            self.controller.vistrail.add_paramexp(pe)
            self.controller.set_changed(True)
        else:
            pe = self.controller.current_debugging

        errors = self.controller.executeDebugging(pe,
                                     self.get_param_view().pipeline_view.scene())
        if errors:
            errors = '\n'.join(['Position %s: %s' % (error[0], error[1]) for error in errors])
            debug.critical("Debugging Execution had errors", errors)
        if changed:
            from vistrails.gui.vistrails_window import _app
            _app.notify('exploration_changed')
