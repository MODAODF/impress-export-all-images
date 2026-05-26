#!/usr/bin/env python3

import uno
import unohelper

from com.sun.star.awt import XActionListener
from com.sun.star.awt import XFocusListener
from com.sun.star.awt import XItemListener
from com.sun.star.awt import XMouseListener
from com.sun.star.awt import XMouseMotionListener
from com.sun.star.awt import XTextListener
from com.sun.star.awt import XTopWindowListener
from com.sun.star.awt import XWindowListener

from com.sun.star.lang import XEventListener
from com.sun.star.util import XModifyListener
from com.sun.star.sheet import XRangeSelectionListener
from com.sun.star.script import ScriptEventDescriptor

from .constants import APPFONT, Size
from .easymain import Macro, Color, dict_to_property


__all__ = [
    'EventsButton',
    'EventsFocus',
    'EventsItem',
    'EventsModify',
    'EventsMouse',
    'EventsMouseLink',
    'EventsRangeSelectionListener',
    'EventsText',
    'EventsWindow',
]


class EventsListenerBase(unohelper.Base, XEventListener):

    def __init__(self, controller, name, window=None):
        self._controller = controller
        self._name = name
        self._window = window

    @property
    def name(self):
        return self._name

    def disposing(self, event):
        self._controller = None
        if not self._window is None:
            self._window.setMenuBar(None)


class LOEvents():

    def __init__(self, obj):
        self._obj = obj

    def __contains__(self, item):
        return self.obj.hasByName(item)

    def __getitem__(self, index):
        """Index access"""
        return self.obj.getByName(index)

    def __setitem__(self, name: str, macro: dict):
        """Set macro to event

        :param name: Event name
        :type name: str
        :param macro: Macro execute in event
        :type name: dict
        """
        pv = '[]com.sun.star.beans.PropertyValue'
        args = ()
        if macro:
            url = Macro.get_url_script(macro)
            args = dict_to_property(dict(EventType='Script', Script=url))
        uno.invoke(self.obj, 'replaceByName', (name, uno.Any(pv, args)))

    @property
    def obj(self):
        return self._obj

    @property
    def names(self):
        return self.obj.ElementNames

    def remove(self, name):
        pv = '[]com.sun.star.beans.PropertyValue'
        uno.invoke(self.obj, 'replaceByName', (name, uno.Any(pv, ())))
        return


class EventsRangeSelectionListener(EventsListenerBase, XRangeSelectionListener):

    def __init__(self, controller):
        super().__init__(controller, '')

    def done(self, event):
        event_name = 'range_selection_done'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event.RangeDescriptor)
        return

    def aborted(self, event):
        event_name = 'range_selection_aborted'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)()
        return


class EventsButton(EventsListenerBase, XActionListener):
    """
        See: https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1XActionListener.html
    """

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def actionPerformed(self, event):
        event_name = f'{self.name}_action'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsMouse(EventsListenerBase, XMouseListener, XMouseMotionListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def mousePressed(self, event):
        event_name = f'{self._name}_click'
        if event.ClickCount == 2:
            event_name = f'{self._name}_double_click'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def mouseReleased(self, event):
        pass

    def mouseEntered(self, event):
        pass

    def mouseExited(self, event):
        pass

    # ~ XMouseMotionListener
    def mouseMoved(self, event):
        event_name = f'{self._name}_mouse_moved'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def mouseDragged(self, event):
        pass


class EventsMouseLink(EventsMouse):

    def mouseEntered(self, event):
        obj = event.Source.Model
        obj.TextColor = Color()('blue')
        return

    def mouseExited(self, event):
        obj = event.Source.Model
        obj.TextColor = 0
        return


class EventsFocus(EventsListenerBase, XFocusListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def focusGained(self, event):
        service = event.Source.Model.ImplementationName
        if service == 'stardiv.Toolkit.UnoControlListBoxModel':
            return

        event_name = f'{self._name}_focus_gained'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)

        # ~ obj = event.Source.ModelBackgroundColor = 16777184
        return

    def focusLost(self, event):
        event_name = f'{self._name}_focus_lost'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)

        # ~ event.Source.Model.BackgroundColor = -1
        return


class EventsModify(EventsListenerBase, XModifyListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def modified(self, event):
        event_name = f'{self._name}_modified'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsText(EventsListenerBase, XTextListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def textChanged(self, event):
        event_name = f'{self._name}_text_changed'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsItem(EventsListenerBase, XItemListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def itemStateChanged(self, event):
        event_name = f'{self._name}_state_changed'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsWindow(EventsListenerBase, XTopWindowListener, XWindowListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def windowOpened(self, event):
        event_name = f'{self._name}_opened'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowClosing(self, event):
        event_name = f'{self._name}_closing'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def windowClosed(self, event):
        event_name = f'{self._name}_closed'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    # ~ XWindowListener
    def windowResized(self, event):
        size = event.Source.convertSizeToLogic(Size(event.Width, event.Height), APPFONT)
        event_name = f'{self._name}_resized'
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event, size)
        return

    def windowMoved(self, event):
        pass

    def windowShown(self, event):
        pass

    def windowHidden(self, event):
        pass


EVENT_METHODS = {
    'text_changed': 'textChanged',
    'action': 'actionPerformed',
    'click': 'mousePressed',
}
LISTENER_TYPE = {
    'textChanged': 'XTextListener',
    'actionPerformed': 'XActionListener',
    'mousePressed': 'XMouseListener',
}


def get_script_event_descriptor(name, macro):
    event = ScriptEventDescriptor()
    event.AddListenerParam = ''
    event.EventMethod = EVENT_METHODS[name]
    event.ListenerType = LISTENER_TYPE[event.EventMethod]
    event.ScriptCode = Macro.get_url_script(macro)
    event.ScriptType = 'Script'
    return event
