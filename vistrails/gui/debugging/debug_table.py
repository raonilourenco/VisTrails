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

from getpass import getuser

from PyQt4 import QtCore, QtGui
from ast import literal_eval
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape, unescape
from vistrails.core.vistrail.module_param import ModuleParam
from vistrails.gui.theme import CurrentTheme
from vistrails.gui.common_widgets import QPromptWidget
from vistrails.gui.modules.autodebug import QParameterEditor
from vistrails.gui.debugging.param_view import QParameterTreeWidget
from vistrails.gui.utils import show_warning
from vistrails.core import debug
from vistrails.core.modules.basic_modules import Constant
from vistrails.core.modules.module_registry import get_module_registry
from vistrails.core.system import current_time, strftime
from vistrails.core.debugging.param import PEParam
from vistrails.core.debugging.parameter import DebugParameter
from vistrails.core.vistrail.module import Module as VistrailModule
from vistrails.core.debugging.debugging import Debugging
import vistrails.core.db.action

""" The file describes the parameter exploration table for VisTrails

QParameterExplorationTable
"""


################################################################################
class QDebugWidget(QtGui.QScrollArea):
    """
    QDebugWidget is a place holder for
    QParameterExplorationTable

    is a grid layout widget having 4 comlumns corresponding to 4
    dimensions of exploration. It accept method/alias drops and can be
    fully configured onto any dimension. For each parameter, 3
    different approach can be chosen to assign the value of that
    parameter during the exploration: linear interpolation (for int,
    float), list (for int, float, string and boolean) and user-define
    function (for int, float, string and boolean)
    
    """
    def __init__(self, parent=None):
        """ QParameterExplorationWidget(parent: QWidget)
                                       -> QParameterExplorationWidget
        Put the QParameterExplorationTable as a main widget
        
        """
        QtGui.QScrollArea.__init__(self, parent)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.table = QParameterExplorationTable()
        self.setWidget(self.table)

    def dragEnterEvent(self, event):
        """ dragEnterEvent(event: QDragEnterEvent) -> None
        Set to accept drops from the parameter list
        
        """
        if isinstance(event.source(), QParameterTreeWidget):
            data = event.mimeData()
            if hasattr(data, 'items'):
                event.accept()
                return
        event.ignore()
        
    def dropEvent(self, event):
        """ dropEvent(event: QDragMoveEvent) -> None
        Accept drop event to add a new method
        
        """
        if isinstance(event.source(), QParameterTreeWidget):
            data = event.mimeData()
            if hasattr(data, 'items'):
                event.accept()
                self.setFocus()
                for item in data.items:
                    self.table.addParameter(item.parameter)
            vsb = self.verticalScrollBar()
            vsb.setValue(vsb.maximum())

    def updatePipeline(self, pipeline):
        """ updatePipeline(pipeline: Pipeline) -> None
        Assign a pipeline to the table
        
        """
        self.table.setPipeline(pipeline)

    
    def getParameterExploration(self):
        """ getParameterExploration() -> ParameterExploration
        Generates a ParameterExploration object hat represents the current
        parameter exploration, and which can be loaded with
        setParameterExploration().
        
        """
        # Construct xml for persisting parameter exploration
        escape_dict = { "'":"&apos;", '"':'&quot;', '\n':'&#xa;' }
        palette = self.get_palette()
        id_scope = self.controller.id_scope
        functions = []
        for i in xrange(self.table.layout().count()):
            pEditor = self.table.layout().itemAt(i).widget()
            if pEditor and isinstance(pEditor, QParameterSetEditor):
                function = None
                firstParam = True
                for paramWidget in pEditor.paramWidgets:
                    paramInfo = paramWidget.param
                    interpolator = paramWidget.editor.stackedEditors.currentWidget()
                    intType = interpolator.exploration_name
                    # Write function tag prior to the first parameter of the function
                    if firstParam:
                        function = DebugParameter(id=id_scope.getNewId(DebugParameter.vtType),
                                              module_id=paramInfo.module_id,
                                              port_name=paramInfo.name,
                                              is_alias = 1 if paramInfo.is_alias else 0, input_port_name = paramInfo.input_port_name)
                        firstParam = False

                    if intType in ['Linear Interpolation', 'RGB Interpolation',
                                   'HSV Interpolation']:
                        value = '["%s", "%s"]' % (interpolator.fromEdit.get_value(),
                                                  interpolator.toEdit.get_value())
                    elif intType == 'List':
                        value = '%s' % escape(str(interpolator._str_values), escape_dict)
                    elif intType == 'User-defined Function':
                        value ='%s' % escape(interpolator.function, escape_dict)
                    else:
                        assert False
                    # Write parameter tag
                    param = PEParam(id=id_scope.getNewId(PEParam.vtType),
                                    pos=paramInfo.pos,
                                    interpolator=intType,
                                    value=value)
                    function.addParameter(param)
                functions.append(function)
        pe = Debugging(layout=repr(palette.virtual_cell.getConfiguration()[2]),
                      date=current_time(),
                      user=getuser(),
                      functions=functions)
        return pe

    def setParameterExploration(self, pe, update_inspector=True):
        """ setParameterExploration(pe: ParameterExploration) -> None
        Sets the current parameter exploration to the one defined by pe
        
        """
        self.table.clear()
        palette = self.get_palette()
        if update_inspector:
            palette.stateChanged()
        if not pe:
            return
        unescape_dict = { "&apos;":"'", '&quot;':'"', '&#xa;':'\n' }
        paramView = self.get_param_view()
    
        # Set the virtual cell layout
        palette.virtual_cell.setConfiguration(pe.layout)
        # Populate parameter exploration window with stored functions and aliases
        for f in pe.functions:
            # Search the parameter treeWidget for this function and add it directly
            newEditor = None
            for tidx in xrange(paramView.treeWidget.topLevelItemCount()):
                moduleItem = paramView.treeWidget.topLevelItem(tidx)
                for cidx in xrange(moduleItem.childCount()):
                    paramInfo = moduleItem.child(cidx).parameter
                    name, params = paramInfo
                    if params[0].module_id == f.module_id and \
                       params[0].name == f.port_name and \
                       bool(params[0].is_alias) == bool(f.is_alias):
                        newEditor = self.table.addParameter(paramInfo)
                        break
                if newEditor:
                    break
                        
            # Retrieve params for this function and set their values in the UI
            if newEditor:
                for p in f.parameters:
                    # Locate the param in the newly added param editor and set values
                    for paramWidget in newEditor.paramWidgets:
                        if paramWidget.param.pos == p.pos:
                            # Set Interpolator Type (dropdown list)
                            paramWidget.editor.selectInterpolator(p.interpolator)
                            # Set Interpolator Value(s)
                            interpolator = paramWidget.editor.stackedEditors.currentWidget()
                            if p.interpolator in ['Linear Interpolation',
                                                  'RGB Interpolation',
                                                  'HSV Interpolation']:
                                try:
                                    # Set min/max
                                    i_range = literal_eval('%s' % unescape(
                                                           p.value,
                                                           unescape_dict))
                                    p_min = str(i_range[0])
                                    p_max =str(i_range[1])
                                    interpolator.fromEdit.set_value(p_min)
                                    interpolator.toEdit.set_value(p_max)
                                except Exception:
                                    pass
                            elif p.interpolator == 'List':
                                p_values = '%s' % unescape(p.value,
                                                        unescape_dict)
                                # Set internal list structure
                                interpolator._str_values = \
                                        literal_eval(p_values)
                                # Update UI list
                                if interpolator.type == 'String':
                                    interpolator.listValues.setText(p_values)
                                else:
                                    interpolator.listValues.setText(
                                     p_values.replace("'","").replace('"',''))
                            elif p.interpolator == 'User-defined Function':
                                # Set function code
                                interpolator.function = '%s' % unescape(
                                                  str(p.value), unescape_dict)

    
    def get_palette(self):
        from vistrails.gui.debugging.debug_inspector import QDebugInspector
        return QDebugInspector.instance()
    
    def get_param_view(self):
        from vistrails.gui.debugging.param_view import QDebugParameterView
        return QDebugParameterView.instance()
    
class QParameterExplorationTable(QPromptWidget):
    """
    QParameterExplorationTable is a grid layout widget having 4
    comlumns corresponding to 4 dimensions of exploration. It accept
    method/alias drops and can be fully configured onto any
    dimension. For each parameter, 3 different approach can be chosen
    to assign the value of that parameter during the exploration:
    linear interpolation (for int, float), list (for int, float,
    string and boolean) and user-define function (for int, float,
    string and boolean)
    
    """
    def __init__(self, parent=None):
        """ QParameterExplorationTable(parent: QWidget)
                                       -> QParameterExplorationTable
        Create an grid layout and accept drops
        
        """
        QPromptWidget.__init__(self, parent)
        self.pipeline = None
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
        self.setPromptText('Drag aliases/parameters here for a parameter '
                           'exploration')
        self.showPrompt()
        
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.setSpacing(0)
        vLayout.setMargin(0)
        vLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(vLayout)


        for i in xrange(2):
            hBar = QtGui.QFrame()
            hBar.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Sunken)
            vLayout.addWidget(hBar)
        self._parameterCount = 0

    def addParameter(self, paramInfo):
        """ addParameter(paramInfo: (str, [ParameterInfo]) -> None
        Add a parameter to the table. The parameter info is specified
        in QParameterTreeWidgetItem
        
        """
        # Check to see paramInfo is not a subset of some other parameter set
        params = paramInfo[1]
        for i in xrange(self.layout().count()):
            pEditor = self.layout().itemAt(i).widget()
            if pEditor and isinstance(pEditor, QParameterSetEditor):
                subset = True
                for p in params:
                    if not (p in pEditor.info[1]):
                        subset = False
                        break                    
                if subset:
                    show_warning('Parameter Exists',
                                 'The parameter you are trying to add is '
                                 'already in the list.')
                    return
        self.showPrompt(False)
        newEditor = QParameterSetEditor(paramInfo, self)

        # Make sure to disable all duplicated parameter
        for p in xrange(len(params)):
            for i in xrange(self.layout().count()):
                pEditor = self.layout().itemAt(i).widget()
                if pEditor and isinstance(pEditor, QParameterSetEditor):
                    if params[p] in pEditor.info[1]:
                        widget = newEditor.paramWidgets[p]
                        widget.setDuplicate(True)
                        widget.setEnabled(False)
                        break
        
        self.layout().addWidget(newEditor)
        newEditor.show()
        self.setMinimumHeight(self.layout().minimumSize().height())
        self.emit(QtCore.SIGNAL('debugChange(bool)'), self.layout().count() > 3)
        return newEditor

    def addBelieve(self, believed,keys):
        for belief in believed:
            show_warning('Belief', 'The parameter %s leads to %s result if it takes the value %s' % (keys[belief[0]],belief[1],belief[2]))
        
    def removeParameter(self, ps):
        """ removeParameterSet(ps: QParameterSetEditor) -> None
        Remove a parameter set from the table and validate the rest
        
        """
        self.layout().removeWidget(ps)
        # Restore disabled parameter
        for i in xrange(self.layout().count()):
            pEditor = self.layout().itemAt(i).widget()
            if pEditor and isinstance(pEditor, QParameterSetEditor):
                for p in xrange(len(pEditor.info[1])):
                    param = pEditor.info[1][p]
                    widget = pEditor.paramWidgets[p]                    
                    if param in ps.info[1] and not widget.isEnabled():
                        widget.setDuplicate(False)
                        widget.setEnabled(True)
                        break
        self.showPrompt(self.layout().count()<=3)
        self.emit(QtCore.SIGNAL('debugChange(bool)'), self.layout().count() > 3)


    def clear(self):
        """ clear() -> None
        Clear all widgets
        
        """
        for i in reversed(range(self.layout().count())):
            pEditor = self.layout().itemAt(i).widget()
            if pEditor and isinstance(pEditor, QParameterSetEditor):
                pEditor.table = None
                self.layout().removeWidget(pEditor)
                pEditor.hide()
                pEditor.deleteLater()
        self.showPrompt()
        self.emit(QtCore.SIGNAL('debugChange(bool)'), self.layout().count() > 3)

    def setPipeline(self, pipeline):
        """ setPipeline(pipeline: Pipeline) -> None
        Assign a pipeline to the current table
        
        """
        if pipeline:
            to_be_deleted = []
            for i in xrange(self.layout().count()):
                pEditor = self.layout().itemAt(i).widget()
                if pEditor and isinstance(pEditor, QParameterSetEditor):
                    for param in pEditor.info[1]:
                        # We no longer require the parameter to exist
                        # we check if the module still exists
                        if not pipeline.db_has_object(VistrailModule.vtType,
                                                      param.module_id):
                            to_be_deleted.append(pEditor)
            for pEditor in to_be_deleted:
                pEditor.removeSelf()
        else:
            self.clear()
        self.pipeline = pipeline

    
class QParameterSetEditor(QtGui.QWidget):
    """
    QParameterSetEditor is a widget controlling a set of
    parameters. The set can contain a single parameter (aliases) or
    multiple of them (module methods).
    
    """
    def __init__(self, info, table=None, parent=None):
        """ QParameterSetEditor(info: paraminfo,
                                table: QParameterExplorationTable,
                                parent: QWidget)
                                -> QParameterSetEditor
        Construct a parameter editing widget based on the paraminfo
        (described in QParameterTreeWidgetItem)
        
        """
        QtGui.QWidget.__init__(self, parent)
        self.info = info
        self.table = table
        (name, paramList) = info
        size = 1
        
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.setMargin(0)
        vLayout.setSpacing(0)
        self.setLayout(vLayout)

        label = QParameterSetLabel(name)
        self.connect(label.removeButton, QtCore.SIGNAL('clicked()'),
                     self.removeSelf)
        vLayout.addWidget(label)
        
        self.paramWidgets = []
        for param in paramList:
            paramWidget = QParameterWidget(param, size)
            vLayout.addWidget(paramWidget)
            self.paramWidgets.append(paramWidget)

        vLayout.addSpacing(10)

        hBar = QtGui.QFrame()
        hBar.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Sunken)
        vLayout.addWidget(hBar)

    def removeSelf(self):
        """ removeSelf() -> None
        Remove itself out of the parent layout()
        
        """
        if self.table:
            self.table.removeParameter(self)            
            self.table = None
            self.close()
            self.deleteLater()

class QParameterSetLabel(QtGui.QWidget):
    """
    QParameterSetLabel is the label bar showing at the top of the
    parameter set editor. It also has a Remove button to remove the
    parameter
    
    """
    def __init__(self, text, parent=None):
        """ QParameterSetLabel(text: str, parent: QWidget) -> QParameterSetLabel
        Init a label and a button
        
        """
        QtGui.QWidget.__init__(self, parent)        
        hLayout = QtGui.QHBoxLayout(self)
        hLayout.setMargin(0)
        hLayout.setSpacing(0)
        self.setLayout(hLayout)

        hLayout.addSpacing(5)

        label = QtGui.QLabel(text)
        font = QtGui.QFont(label.font())
        font.setBold(True)
        label.setFont(font)
        hLayout.addWidget(label)

        hLayout.addSpacing(5)
        
        self.removeButton = QtGui.QToolButton()
        self.removeButton.setAutoRaise(True)
        self.removeButton.setIcon(QtGui.QIcon(
            self.style().standardPixmap(QtGui.QStyle.SP_DialogCloseButton)))
        self.removeButton.setIconSize(QtCore.QSize(12, 12))
        self.removeButton.setFixedWidth(16)
        hLayout.addWidget(self.removeButton)

        hLayout.addStretch()
        
class QParameterWidget(QtGui.QWidget):
    """
    QParameterWidget is a row widget containing a label, a parameter
    editor and a radio group.
    
    """
    def __init__(self, param, size, parent=None):
        """ QParameterWidget(param: ParameterInfo, size: int, parent: QWidget)
                             -> QParameterWidget
        """
        QtGui.QWidget.__init__(self, parent)
        self.param = param
        self.prevWidget = 0
        
        hLayout = QtGui.QHBoxLayout(self)
        hLayout.setMargin(0)
        hLayout.setSpacing(0)        
        self.setLayout(hLayout)

        hLayout.addSpacing(5+16+5)

        self.label = QtGui.QLabel(param.spec.module)
        self.label.setFixedWidth(50)
        hLayout.addWidget(self.label)

        module = param.spec.descriptor.module
        assert issubclass(module, Constant)

        self.editor = QParameterEditor(param, size)
        hLayout.addWidget(self.editor)

        '''
        self.selector = QDimensionSelector()
        self.connect(self.selector.radioButtons[4],
                     QtCore.SIGNAL('toggled(bool)'),
                     self.disableParameter)
        hLayout.addWidget(self.selector)
        '''
    '''
    def getDimension(self):
        """ getDimension() -> int        
        Return a number 0-4 indicating which radio button is
        selected. If none is selected (should not be in this case),
        return -1
        
        """
        for i in xrange(5):
            if self.selector.radioButtons[i].isChecked():
                return i
        return -1
    '''
    def disableParameter(self, disabled=True):
        """ disableParameter(disabled: bool) -> None
        Disable/Enable this parameter when disabled is True/False
        
        """
        self.label.setEnabled(not disabled)
        self.editor.setEnabled(not disabled)


    '''
    def setDimension(self, dim):
        """ setDimension(dim: int) -> None
        Select a dimension for this parameter
        
        """
        if dim in xrange(5):
            self.selector.radioButtons[dim].setChecked(True)
    '''

    def setDuplicate(self, duplicate):
        """ setDuplicate(duplicate: True) -> None
        Set if this parameter is a duplicate parameter
        
        """
        if duplicate:
            self.prevWidget = self.editor.stackedEditors.currentIndex()
            self.editor.stackedEditors.setCurrentIndex(3)
        else:
            self.editor.stackedEditors.setCurrentIndex(self.prevWidget)



'''
class QDimensionSelector(QtGui.QWidget):
    """
    QDimensionSelector provides 5 radio buttons to select dimension of
    exploration or just skipping it.
    
    """
    def __init__(self, parent=None):
        """ QDimensionSelector(parent: QWidget) -> QDimensionSelector
        Initialize the horizontal layout and set the width to be fixed
        equal to the QDimensionLabel
        
        """
        QtGui.QWidget.__init__(self, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum,
                           QtGui.QSizePolicy.Maximum)
        
        hLayout = QtGui.QHBoxLayout(self)
        hLayout.setMargin(0)
        hLayout.setSpacing(0)        
        self.setLayout(hLayout)

        self.radioButtons = []
        for i in xrange(5):
            hLayout.addSpacing(2)
            button = QDimensionRadioButton()
            self.radioButtons.append(button)
            button.setFixedWidth(32)
            hLayout.addWidget(button)
        self.radioButtons[0].setChecked(True)
'''
'''
class QDimensionRadioButton(QtGui.QRadioButton):
    """
    QDimensionRadioButton is a replacement of QRadioButton with
    simpler appearance. We just need to override the paint event
    
    """
    def paintEvent(self, event):
        """ paintEvent(event: QPaintEvent) -> None
        Draw an outer circle and another solid one in side
        
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.palette().color(QtGui.QPalette.Dark))
        painter.setBrush(QtCore.Qt.NoBrush)
        l = min(self.width()-2, self.height()-2, 12)
        r = QtCore.QRect(0, 0, l, l)
        r.moveCenter(self.rect().center())
        painter.drawEllipse(r)

        if self.isChecked():
            r.adjust(3, 3, -3, -3)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self.palette().color(QtGui.QPalette.WindowText))
            painter.drawEllipse(r)
        
        painter.end()

    def mousePressEvent(self, event):
        """ mousePressEvent(event: QMouseEvent) -> None
        Force toggling the radio button
        
        """
        self.click()
'''