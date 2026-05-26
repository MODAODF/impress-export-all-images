#!/usr/bin/env python3

# ~ easymacro - for easily develop macros in LibreOffice
# ~ Copyright (C) 2020-2025  Mauricio Baeza (elmau)

# ~ This program is free software: you can redistribute it and/or modify it
# ~ under the terms of the GNU General Public License as published by the
# ~ Free Software Foundation, either version 3 of the License, or (at your
# ~ option) any later version.

# ~ This program is distributed in the hope that it will be useful, but
# ~ WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# ~ or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# ~ for more details.

# ~ You should have received a copy of the GNU General Public License along
# ~ with this program.  If not, see <http://www.gnu.org/licenses/>.


from .constants import *
from .easydialog import *
from .easydocs import LODocuments
# ~ from .easywin import *
# ~ from .easydrawpage import LOGalleries
from .easymain import *
from .easytools import *


__version__ = '0.10.0'
__author__ = 'Mauricio B. Servin (elMau)'


docs = LODocuments()


def __getattr__(name):
    classes = {
        'active': docs.active,
        'clipboard': ClipBoard,
        'cmd': LOMain.commands,
        'color': Color(),
        'config': Config,
        'dates': Dates,
        'dialog': LODialog,
        'dispatch': LOMain.dispatch,
        'docs': docs,
        'email': Email,
        # ~ 'galleries': LOGalleries(),
        'get_config': get_app_config,
        'filters': LOMain.filters,
        'fonts': LOMain.fonts,
        'hash': Hash,
        'inspect': LOInspect,
        'macro': Macro,
        'menus': LOMenus(),
        'paths': Paths,
        'url': URL,
        'recent_documents': RecentDocuments(),
        'set_config': set_app_config,
        'setting': Setting,
        'shell': Shell,
        'shortcuts': LOShortCuts(),
        'timer': Timer,
        'toolbars': LOToolBars(),
        # ~ 'window': LOWindow,
    }

    if name in classes:
        return classes[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
