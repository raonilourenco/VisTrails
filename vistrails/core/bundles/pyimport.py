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

"""module responsible for smartly importing python modules, checking
for necessary installs."""

import core.bundles.installbundle

##############################################################################

def _vanilla_import(module_name):
    return __import__(module_name, globals(), locals(), [])

def unknown_py_import(module_name, package_name):
    return _vanilla_import(module_name)

def py_import(module_name, dependency_dictionary):
    """Tries to import a python module. If unsuccessful, tries to install
the appropriate bundle and then reimport. py_import tries to be smart
about which system it runs on."""
    try:
        result = _vanilla_import(module_name)
        return result
    except ImportError, e:
        pass
    print "Import failed. Will try to install bundle"

    success = core.bundles.installbundle.install(dependency_dictionary)

    if not success:
        print "Package installation failed."
        print "Package might not be available in the provided repositories."
        raise e

    try:
        result = _vanilla_import(module_name)
        return result
    except ImportError, e:
        print "Package installation successful, but import still failed."
        print "This means py_import was called with bad arguments."
        print "Please report this bug to the package developer."
        raise e

##############################################################################
