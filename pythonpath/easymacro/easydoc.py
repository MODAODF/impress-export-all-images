#!/usr/bin/env python3

import uno
import unohelper

from .constants import Rectangle, ScrollBarOrientation, VclWindowPeerAttribute, WindowAttribute, \
    WindowClass, WindowDescriptor
from .easyevents import EventsButton, EventsItem, EventsMouse
from .easymain import (log, _CTX, _SM,
    BaseObject, LOMain, Paths,
    dict_to_property, create_instance
)
from .easyuno import IOStream
from .easyshape import LOShapes, LOShape

from com.sun.star.frame import XToolbarController
from com.sun.star.lang import XInitialization
from com.sun.star.util import XUpdatable
from com.sun.star.frame import XStatusListener


EVENTS = None
OPTIONS = {}
toolkit = _SM.createInstanceWithContext('com.sun.star.awt.Toolkit', _CTX)


class ToolBarItem(unohelper.Base, XInitialization, XUpdatable, XToolbarController, XStatusListener):
    #  https://api.libreoffice.org/docs/idl/ref/structcom_1_1sun_1_1star_1_1awt_1_1WindowDescriptor.html#abbe7984adc1b7d664ea00fefb8a006b0
    ATTRIBUTES = {
        'buttondialog': WindowAttribute.SHOW,
        'cancelbutton': WindowAttribute.SHOW,
        'checkbox': WindowAttribute.SHOW,
        'combobox': WindowAttribute.SHOW | VclWindowPeerAttribute.DROPDOWN,
        'fixedimage': WindowAttribute.SHOW,
        'imagebutton': WindowAttribute.SHOW,
        'scrollbar': WindowAttribute.SHOW,
        'pushbutton': WindowAttribute.SHOW,
        'listbox': WindowAttribute.SHOW | VclWindowPeerAttribute.DROPDOWN,
        'menubutton': WindowAttribute.SHOW,
    }

    def __init__(self, ctx, module, frame, sm, parent, identifier, cmd_url, p):
        data = cmd_url.Value.split('.')
        self.name = data[-1].lower()
        self.type = data[-2].lower()
        self.parent = parent.Value

    def initialize(self, args):
        pass

    def update(self):
        pass

    def statusChanged(self, state):
        pass

    def execute(self, KeyModifier):
        pass

    def click(self):
        print('click', self.name)
        return

    def doubleClick(self):
        pass

    def createPopupWindow(self):
        return

    def _make_window(self, args):
        #  toolkit = _SM.createInstanceWithContext('com.sun.star.awt.Toolkit', _CTX)

        wd = WindowDescriptor()
        wd.Type = WindowClass.SIMPLE
        wd.Parent = self.parent
        wd.Bounds = Rectangle(0, 0, args.get('Width', 25), args.get('Height', 25))
        wd.ParentIndex = -1
        wd.WindowAttributes = self.ATTRIBUTES[self.type]
        wd.WindowServiceName = self.type

        return toolkit.createWindow(wd)

    def _setting_buttondialog(self, control, args):
        pass

    def _setting_cancelbutton(self, control, args):
        pass

    def _setting_checkbox(self, control, args):
        control.Label = args['Label']
        control.addActionListener(EventsButton(EVENTS, args['Name']))
        control.addMouseListener(EventsMouse(EVENTS, args['Name']))
        control.addItemListener(EventsItem(EVENTS, args['Name']))
        return

    def _setting_combobox(self, control, args):
        control.addItems(args['Data'], 0)
        control.setDropDownLineCount(5)
        control.addItemListener(EventsItem(EVENTS, args['Name']))
        return

    def _setting_fixedimage(self, control, args):
        #  from easymacro import inspect
        #  control.addMouseListener(EventsMouse(EVENTS, args['Name']))
        return

    def _setting_imagebutton(self, control, args):
        control.Label = args['Label']
        control.addMouseListener(EventsMouse(EVENTS, args['Name']))
        return

    def _setting_listbox(self, control, args):
        control.addItems(args['Data'], 0)
        control.setDropDownLineCount(5)
        control.addItemListener(EventsItem(EVENTS, args['Name']))
        return

    def _setting_scrollbar(self, win):
        data = OPTIONS['scrollbar']
        win.addAdjustmentListener(EVENTS(), args['Name'])
        win.setOrientation(ScrollBarOrientation.HORIZONTAL)
        win.setValues(data['Value'], 10, data['Max'])
        return

    def _setting_pushbutton(self, control, args):
        control.Label = args['Label']
        control.addMouseListener(EventsMouse(EVENTS, args['Name']))
        return

    def createItemWindow(self, parent):
        args = OPTIONS[self.name]
        control = self._make_window(args)
        getattr(self, f'_setting_{self.type}')(control, args)
        return control


class LOLayoutManager(BaseObject):
    PR = 'private:resource'
    TB = 'toolbar'
    MB = 'menubar'
    SB = 'statusbar'

    def __init__(self, obj):
        super().__init__(obj.LayoutManager)
        self._frame = obj

    def __getitem__(self, index):
        """ """
        url = self._get_url(index)
        return self.obj.getElement(url)

    @property
    def visible(self):
        """ """
        return self.obj.isVisible()
    @visible.setter
    def visible(self, value):
        self.obj.Visible = value

    @property
    def elements(self):
        """ """
        return [e.ResourceURL[17:] for e in self.obj.Elements]

    def _get_url(self, url):
        if url.startswith(self.MB) or url.startswith(self.SB):
            url = f'{self.PR}/{url}'
        elif not url.startswith(self.TB):
            url = f'{self.PR}/{self.TB}/{url}'
        #  print('URL', url)
        return url

    def show(self, name):
        self.obj.showElement(self._get_url(name))
        return

    def hide(self, name):
        self.obj.hideElement(self._get_url(name))
        return

    def _create_service(self, name, item):
        global OPTIONS
        OPTIONS[item['Name'].lower()] = item

        service = f"{name}.ToolBar.{item['Type']}.{item['Name']}"
        service_impl = f'{service}.Impl'
        #  print(service)
        ssf = unohelper.createSingleServiceFactory(ToolBarItem, service_impl, (service,))
        if service in _SM.AvailableServiceNames:
            _SM.remove(service_impl)
        _SM.insert(ssf)
        return

    def _insert_items(self, name, items):
        #  tcf = _SM.createInstanceWithContext("com.sun.star.frame.ToolbarControllerFactory", _CTX)
        tcf = _CTX.getValueByName('/singletons/com.sun.star.frame.theToolbarControllerFactory')
        toolbar = self[name]
        settings = toolbar.getSettings(True)

        for item in items:
            service = f"{name}.ToolBar.{item['Type']}.{item['Name']}"
            cmd_url = f".uno:{service}"
            if tcf.hasController(cmd_url, ''):
                tcf.deregisterController(cmd_url, '')
            tcf.registerController(cmd_url, '', service)

            data = {'CommandURL': cmd_url, 'Label': item['Label']}
            properties = dict_to_property(data, True)
            uno.invoke(settings, 'insertByIndex', (settings.Count, properties))

        toolbar.setSettings(settings)

        return

    #  https://forum.openoffice.org//en/forum/viewtopic.php?t=108410
    def create(self, name: str, options: tuple, events):
        global EVENTS
        EVENTS = events()

        self.destroy(name)
        url = self._get_url(name)
        self.obj.createElement(url)
        new = self.obj.getElement(url)
        settings = new.getSettings(True)
        settings.UIName = name
        new.Settings = settings

        for item in options:
            self._create_service(name, item)

        self._insert_items(name, options)

        return

    def destroy(self, name):
        self.obj.destroyElement(self._get_url(name))
        return

    def execute(self, name):
        EXECUTE_DEFAULT = 0

        url = self._get_url(name)
        menu = self.obj.getElement(url).XMenuBar
        id0 = menu.getItemId(0)
        popup = menu.getPopupMenu(id0)
        popup.execute(self._frame.ContainerWindow, Rectangle(), EXECUTE_DEFAULT)
        return

    def dock(self, url):
        url = self._get_url(url)
        #  self.obj.dockWindow(url, com.sun.star.ui.DockingArea.DOCKINGAREA_TOP, Point(0, 0))
        return


class LODocProperties(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._set_properties()

    def _set_properties(self):
        self.author = self.obj.Author
        self.creation_date = self.obj.CreationDate
        return


class LODocument(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._cc = obj.getCurrentController()
        self._layout_manager = LOLayoutManager(self._cc.Frame)
        self._undo = True
        self._cw = self._cc.Frame.ContainerWindow

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def type(self):
        """Get type document"""
        return self._type

    @property
    def title(self):
        """Get title document"""
        return self.obj.getTitle()
    @title.setter
    def title(self, value):
        self.obj.setTitle(value)

    @property
    def uid(self):
        """Get Runtime UID"""
        return self.obj.RuntimeUID

    @property
    def is_saved(self):
        """Get is saved"""
        return self.obj.hasLocation()

    @property
    def is_modified(self):
        """Get is modified"""
        return self.obj.isModified()

    @property
    def is_read_only(self):
        """Get is read only"""
        return self.obj.isReadonly()

    @property
    def path(self):
        """Get path in system files"""
        return Paths.to_system(self.obj.URL)

    @property
    def dir(self):
        """Get directory from path"""
        return Paths(self.path).path

    @property
    def file_name(self):
        """Get only file name"""
        return Paths(self.path).file_name

    @property
    def name(self):
        """Get name without extension"""
        return Paths(self.path).name

    @property
    def visible(self):
        """Get windows visible"""
        w = self.frame.ContainerWindow
        return w.isVisible()
    @visible.setter
    def visible(self, value):
        w = self.frame.ContainerWindow
        w.setVisible(value)

    @property
    def zoom(self):
        """Get current zoom value"""
        return self._cc.ZoomValue
    @zoom.setter
    def zoom(self, value):
        self._cc.ZoomValue = value

    @property
    def status_bar(self):
        """Get status bar"""
        bar = self._cc.getStatusIndicator()
        return bar

    @property
    def selection(self):
        """Get current selecction"""
        sel = self.obj.CurrentSelection
        return sel

    @property
    def frame(self):
        """Get frame document"""
        return self._cc.getFrame()

    @property
    def properties(self):
        """ """
        return LODocProperties(self.obj.DocumentProperties)

    @property
    def layout_manager(self):
        """ """
        return self._layout_manager
    @property
    def lm(self):
        """ """
        return self.layout_manager

    def _create_instance(self, name):
        obj = self.obj.createInstance(name)
        return obj

    def save(self, path: str='', args: dict={}) -> bool:
        """Save document

        :param path: Path to save document
        :type path: str
        :param args: Optional: Extra argument for save
        :type args: dict
        :return: True if save correctly, False if not
        :rtype: bool
        """
        if not path:
            self.obj.store()
            return True

        path_save = Paths.to_url(path)
        opt = dict_to_property(args)

        try:
            self.obj.storeAsURL(path_save, opt)
        except Exception as e:
            log.error(e)
            return False

        return True

    def close(self):
        """Close document"""
        self.obj.close(True)
        return

    def to_pdf(self, path: str='', args: dict={}):
        """Export to PDF

        :param path: Path to export document
        :type path: str
        :param args: Optional: Extra argument for export
        :type args: dict
        :return: None if path or stream in memory
        :rtype: bytes or None

        `See PDF Export <https://wiki.documentfoundation.org/Macros/Python_Guide/PDF_export_filter_data>`_
        """
        stream = None
        path_pdf = 'private:stream'

        filter_name = f'{self.type}_pdf_Export'
        filter_data = dict_to_property(args, True)
        filters = {
            'FilterName': filter_name,
            'FilterData': filter_data,
        }
        if path:
            path_pdf = Paths.to_url(path)
        else:
            stream = IOStream.output()
            filters['OutputStream'] = stream

        opt = dict_to_property(filters)
        try:
            self.obj.storeToURL(path_pdf, opt)
        except Exception as e:
            error(e)

        if not stream is None:
            stream = stream.buffer

        return stream

    def export(self, path: str='', filter_name: str='', args: dict={}):
        """Export to others formats

        :param path: Path to export document
        :type path: str
        :param filter_name: Filter name to export
        :type filter_name: str
        :param args: Optional: Extra argument for export
        :type args: dict
        :return: None if path or stream in memory
        :rtype: bytes or None

        https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1document_1_1MediaDescriptor.html
        """
        FILTERS = {
            'xlsx': 'Calc MS Excel 2007 XML',
            'xls': 'MS Excel 97',
            'docx': 'MS Word 2007 XML',
            'doc': 'MS Word 97',
            'rtf': 'Rich Text Format',
        }

        stream = None
        path_target = 'private:stream'
        if filter_name == 'svg':
            filter_name = f'{self.type}_svg_Export'
        else:
            filter_name = FILTERS.get(filter_name, filter_name)

        filter_data = dict_to_property(args, True)
        filters = {
            'FilterName': filter_name,
            'FilterData': filter_data,
        }
        if path:
            path_target = Paths.to_url(path)
        else:
            stream = IOStream.output()
            filters['OutputStream'] = stream

        opt = dict_to_property(filters)
        try:
            self.obj.storeToURL(path_target, opt)
        except Exception as e:
            log.error(e)

        if not stream is None:
            stream = stream.buffer

        return stream

    def set_focus(self):
        """Send focus to windows"""
        w = self.frame.ComponentWindow
        w.setFocus()
        return

    def copy(self):
        """Copy current selection"""
        LOMain.dispatch(self.frame, 'Copy')
        return

    def cut(self):
        """Cut current selection"""
        LOMain.dispatch(self.frame, 'Cut')
        return

    def paste(self):
        """Paste current content in clipboard"""
        sc = create_instance('com.sun.star.datatransfer.clipboard.SystemClipboard')
        transferable = sc.getContents()
        self._cc.insertTransferable(transferable)
        return

    def paste_special(self):
        """Insert contents, show dialog box Paste Special"""
        LOMain.dispatch(self.frame, 'InsertContents')
        return

    def paste_values(self):
        """Paste only values"""
        args = {
            'Flags': 'SVD',
            # ~ 'FormulaCommand': 0,
            # ~ 'SkipEmptyCells': False,
            # ~ 'Transpose': False,
            # ~ 'AsLink': False,
            # ~ 'MoveMode': 4,
        }
        LOMain.dispatch(self.frame, 'InsertContents', args)
        return

    def clear_undo(self):
        """Clear history undo"""
        self.obj.getUndoManager().clear()
        return

    def replace_ext(self, new_ext):
        return Paths.with_suffix(self.path, new_ext)

    def deselect(self):
        LOMain.dispatch(self.frame, 'Deselect')
        return

    #  def clear_format(self):
        #  """Clear Direct Formatting"""
        #  LOMain.dispatch(self.frame, 'SetDefault')
        #  return


class LODrawImpress(LODocument):
    from .easydrawpage import LODrawPage

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        if isinstance(index, int):
            page = self.obj.DrawPages[index]
        else:
            page = self.obj.DrawPages.getByName(index)
        return self.LODrawPage(page)

    @property
    def selection(self):
        """Get current selection"""
        sel = self.obj.CurrentSelection
        if sel.Count == 1:
            sel = LOShape(sel[0])
        else:
            sel = LOShapes(sel)
        return sel

    @property
    def current_page(self):
        return self.LODrawPage(self._cc.CurrentPage)
    @property
    def active(self):
        return self.current_page
