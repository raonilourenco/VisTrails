############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
################################################################################
# RichText plugin for VisTrails Spreadsheet
################################################################################
from richtext import RichTextCell

################################################################################

def widgetName():
    """ widgetName() -> str
    Return the name of this widget plugin
    
    """
    return 'HTML Viewer'

def registerWidget(reg, basicModules, basicWidgets):    
    """ registerWidget(reg: module_registry,
                       basicModules: python package,
                       basicWidgets: python package) -> None
    Register all widgets in this package to VisTrails module_registry
    
    """
    reg.add_module(RichTextCell)
    reg.add_input_port(RichTextCell, "Location", basicWidgets.CellLocation)
    reg.add_input_port(RichTextCell, "File", basicModules.File)
