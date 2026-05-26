#!/usr/bin/env python3

from typing import Any

from com.sun.star.view.SelectionType import SINGLE, MULTI, RANGE

from .constants import APPFONT, POS, POSSIZE, \
    Rectangle, Size, WindowClass, WindowDescriptor, WindowAttribute
from .easyevents import *
from .easydocs import LODocuments
from .easymain import (log, TITLE,
    BaseObject, Color,
    create_instance, set_properties)
from .easytools import _, LOInspect, Paths, Services, debug, mri


__all__ = [
    'LODialog',
    'inputbox',
]


# ~ COLOR_ON_FOCUS = 'LightYellow'
# ~ COLOR_ON_FOCUS = 16777184
SEPARATION = 5

MODELS = {
    'label': 'com.sun.star.awt.UnoControlFixedTextModel',
    'text': 'com.sun.star.awt.UnoControlEditModel',
    'button': 'com.sun.star.awt.UnoControlButtonModel',
    'link': 'com.sun.star.awt.UnoControlFixedHyperlinkModel',
    'image': 'com.sun.star.awt.UnoControlImageControlModel',
    'pattern': 'com.sun.star.awt.UnoControlPatternFieldModel',
    'combobox': 'com.sun.star.awt.UnoControlComboBoxModel',
    'checkbox': 'com.sun.star.awt.UnoControlCheckBoxModel',
    'spinbutton': 'com.sun.star.awt.UnoControlSpinButtonModel',
    'numeric': 'com.sun.star.awt.UnoControlNumericFieldModel',
    'listbox': 'com.sun.star.awt.UnoControlListBoxModel',
    'line': 'com.sun.star.awt.UnoControlFixedLineModel',
    # ~ ToDo
    'radio': 'com.sun.star.awt.UnoControlRadioButtonModel',
    'roadmap': 'com.sun.star.awt.UnoControlRoadmapModel',
    'tree': 'com.sun.star.awt.tree.TreeControlModel',
    'grid': 'com.sun.star.awt.grid.UnoControlGridModel',
    'pages': 'com.sun.star.awt.UnoMultiPageModel',
    'groupbox': 'com.sun.star.awt.UnoControlGroupBoxModel',
}

TYPE_CONTROL = {
    'stardiv.Toolkit.UnoFixedTextControl': 'label',
    'stardiv.Toolkit.UnoEditControl': 'text',
    'stardiv.Toolkit.UnoButtonControl': 'button',
    'stardiv.Toolkit.UnoImageControlControl': 'image',
    'stardiv.Toolkit.UnoSpinButtonModel': 'spinbutton',
}

IMPLEMENTATIONS = {
    'grid': 'stardiv.Toolkit.GridControl',
    'link': 'stardiv.Toolkit.UnoFixedHyperlinkControl',
    'roadmap': 'stardiv.Toolkit.UnoRoadmapControl',
    'pages': 'stardiv.Toolkit.UnoMultiPageControl',
    'text': 'stardiv.Toolkit.UnoEditControl',
    'spinbutton': 'stardiv.Toolkit.UnoSpinButtonModel',
}


def add_listeners(events, control):
    name = control.Model.Name
    listeners = {
        'addActionListener': EventsButton,
        'addMouseListener': EventsMouse,
        'addFocusListener': EventsFocus,
        'addTextListener': EventsText,
        # ~ 'addItemListener': EventsItem,
        # ~ 'addKeyListener': EventsKey,
        # ~ 'addTabListener': EventsTab,
        # ~ 'addSpinListener': EventsSpin,
    }
    if hasattr(control, 'obj'):
        control = control.obj
    # ~ log.debug(control.ImplementationName)
    is_grid = control.ImplementationName == IMPLEMENTATIONS['grid']
    is_link = control.ImplementationName == IMPLEMENTATIONS['link']
    is_roadmap = control.ImplementationName == IMPLEMENTATIONS['roadmap']
    is_pages = control.ImplementationName == IMPLEMENTATIONS['pages']

    for key, value in listeners.items():
        if hasattr(control, key):
            if is_grid and key == 'addMouseListener':
                control.addMouseListener(EventsMouseGrid(events, name))
                continue
            if is_link and key == 'addMouseListener':
                control.addMouseListener(EventsMouseLink(events, name))
                continue
            if is_roadmap and key == 'addItemListener':
                control.addItemListener(EventsItemRoadmap(events, name))
                continue

            getattr(control, key)(value(events, name))

    if is_grid:
        controllers = EventsGrid(events, name)
        control.addSelectionListener(controllers)
        control.Model.GridDataModel.addGridDataListener(controllers)
    return


# ~ getAccessibleActionKeyBinding
class UnoActions():
    ACTIONS = {
        'press': 0,
        'activate': 0,
    }

    def __init__(self, obj: Any):
        self._obj = obj
        self._ac = obj.AccessibleContext
        self._actions = hasattr(self._ac, 'AccessibleActionCount')

    def __str__(self):
        return ', '.join(self.get())

    def get(self):
        actions = ()
        if self._actions:
            actions = [self._ac.getAccessibleActionDescription(i) for i in
                range(self._ac.AccessibleActionCount)]
        return actions

    def press(self):
        result = self._ac.doAccessibleAction(self.ACTIONS['press'])
        return result

    def activate(self):
        result = self._ac.doAccessibleAction(self.ACTIONS['activate'])
        return result


class UnoBaseObject(object):

    def __init__(self, obj: Any):
        self._obj = obj
        self._model = obj.Model

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @property
    def obj(self):
        return self._obj

    @property
    def model(self):
        return self._model
    @property
    def m(self):
        return self._model

    @property
    def properties(self):
        properties = self.model.PropertySetInfo.Properties
        data = {p.Name: getattr(self.model, p.Name) for p in properties}
        return data
    @properties.setter
    def properties(self, properties: dict):
        set_properties(self.model, properties)

    @property
    def name(self):
        return self.model.Name

    @property
    def parent(self):
        return self.obj.Context

    @property
    def tag(self):
        return self.model.Tag
    @tag.setter
    def tag(self, value):
        self.model.Tag = value

    @property
    def visible(self):
        return self.obj.Visible
    @visible.setter
    def visible(self, value):
        self.obj.setVisible(value)

    @property
    def enabled(self):
        return self.model.Enabled
    @enabled.setter
    def enabled(self, value):
        self.model.Enabled = value

    @property
    def step(self):
        return self.model.Step
    @step.setter
    def step(self, value):
        self.model.Step = value

    @property
    def align(self):
        return self.model.Align
    @align.setter
    def align(self, value):
        self.model.Align = value

    @property
    def valign(self):
        return self.model.VerticalAlign
    @valign.setter
    def valign(self, value):
        self.model.VerticalAlign = value

    @property
    def font_weight(self):
        return self.model.FontWeight
    @font_weight.setter
    def font_weight(self, value):
        self.model.FontWeight = value

    @property
    def font_height(self):
        return self.model.FontHeight
    @font_height.setter
    def font_height(self, value):
        self.model.FontHeight = value

    @property
    def font_name(self):
        return self.model.FontName
    @font_name.setter
    def font_name(self, value):
        self.model.FontName = value

    @property
    def font_underline(self):
        return self.model.FontUnderline
    @font_underline.setter
    def font_underline(self, value):
        self.model.FontUnderline = value

    @property
    def text_color(self):
        return self.model.TextColor
    @text_color.setter
    def text_color(self, value):
        self.model.TextColor = value

    @property
    def back_color(self):
        return self.model.BackgroundColor
    @back_color.setter
    def back_color(self, value):
        self.model.BackgroundColor = value

    @property
    def multi_line(self):
        return self.model.MultiLine
    @multi_line.setter
    def multi_line(self, value):
        self.model.MultiLine = value

    @property
    def help_text(self):
        return self.model.HelpText
    @help_text.setter
    def help_text(self, value):
        self.model.HelpText = value

    @property
    def border(self):
        return self.model.Border
    @border.setter
    def border(self, value):
        # ~ Bug for report
        self.model.Border = value

    @property
    def width(self):
        return self._model.Width
    @width.setter
    def width(self, value):
        self.model.Width = value

    @property
    def height(self):
        return self.model.Height
    @height.setter
    def height(self, value):
        self.model.Height = value

    def _get_possize(self, name):
        ps = self.obj.getPosSize()
        return getattr(ps, name)

    def _set_possize(self, name, value):
        ps = self.obj.getPosSize()
        setattr(ps, name, value)
        self.obj.setPosSize(ps.X, ps.Y, ps.Width, ps.Height, POSSIZE)
        return

    @property
    def x(self):
        if hasattr(self.model, 'PositionX'):
            return self.model.PositionX
        return self._get_possize('X')
    @x.setter
    def x(self, value):
        if hasattr(self.model, 'PositionX'):
            self.model.PositionX = value
        else:
            self._set_possize('X', value)

    @property
    def y(self):
        if hasattr(self.model, 'PositionY'):
            return self.model.PositionY
        return self._get_possize('Y')
    @y.setter
    def y(self, value):
        if hasattr(self.model, 'PositionY'):
            self.model.PositionY = value
        else:
            self._set_possize('Y', value)

    @property
    def tab_index(self):
        return self._model.TabIndex
    @tab_index.setter
    def tab_index(self, value):
        self.model.TabIndex = value

    @property
    def tab_stop(self):
        return self._model.Tabstop
    @tab_stop.setter
    def tab_stop(self, value):
        self.model.Tabstop = value

    @property
    def ps(self):
        ps = self.obj.getPosSize()
        return ps
    @ps.setter
    def ps(self, ps):
        self.obj.setPosSize(ps.X, ps.Y, ps.Width, ps.Height, POSSIZE)

    @property
    def actions(self):
        return UnoActions(self.obj)

    def remove(self):
        self.parent.Model.removeByName(self.name)
        return

    def set_focus(self):
        self.obj.setFocus()
        return

    def ps_from(self, source):
        self.ps = source.ps
        return

    def center(self, horizontal=True, vertical=False):
        p = self.parent.Model
        w = p.Width
        h = p.Height
        if horizontal:
            x = w / 2 - self.width / 2
            self.x = x
        if vertical:
            y = h / 2 - self.height / 2
            self.y = y
        return

    def move(self, origin, x=0, y=5, center=False):
        if x:
            self.x = origin.x + origin.width + x
        else:
            self.x = origin.x
        if y:
            h = origin.height
            if y < 0:
                h = 0
            self.y = origin.y + h + y
        else:
            self.y = origin.y

        if center:
            self.center()
        return


class UnoLabel(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'label'

    @property
    def value(self):
        return self.model.Label
    @value.setter
    def value(self, value):
        self.model.Label = value


class UnoLabelLink(UnoLabel):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'link'

    @property
    def value(self):
        """Get link"""
        return self.model.URL
    @value.setter
    def value(self, value):
        self.model.Label = value
        self.model.URL = value

    @property
    def url(self):
        """Get link"""
        return self.model.URL
    @url.setter
    def url(self, value):
        self.model.URL = value

    @property
    def label(self):
        """Get label"""
        return self.model.Label
    @label.setter
    def label(self, value):
        self.model.Label = value


# ~ https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1awt_1_1UnoControlEditModel.html
class UnoText(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'text'

    @property
    def value(self):
        return self.model.Text.strip()
    @value.setter
    def value(self, value):
        self.model.Text = value

    @property
    def echochar(self):
        return chr(self.model.EchoChar)
    @echochar.setter
    def echochar(self, value):
        if value:
            self.model.EchoChar = ord(value[0])
        else:
            self.model.EchoChar = 0

    def validate(self):
        return


class UnoButton(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'button'

    @property
    def value(self):
        return self.model.Label
    @value.setter
    def value(self, value):
        self.model.Label = value

    @property
    def image(self):
        return self.model.ImageURL
    @image.setter
    def image(self, value):
        self.model.ImageURL = Paths.to_url(value)


class UnoImage(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'image'

    @property
    def value(self):
        return self.model.ImageURL
    @value.setter
    def value(self, value):
        if isinstance(value, str):
            self.model.ImageURL = value
        else:
            self.model.Graphic = value._get_graphic()


class UnoPattern(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'pattern'

    @property
    def value(self):
        return self.model.Text
    @value.setter
    def value(self, value):
        self.model.Text = value

    @property
    def edit_mask(self):
        return self.model.EditMask
    @edit_mask.setter
    def edit_mask(self, value):
        self.model.EditMask = value

    @property
    def literal_mask(self):
        return self.model.LiteralMask
    @literal_mask.setter
    def literal_mask(self, value):
        self.model.LiteralMask = value

    @property
    def strict_format(self):
        return self.model.StrictFormat
    @strict_format.setter
    def strict_format(self, value):
        self.model.StrictFormat = value


class UnoComboBox(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'combobox'

    @property
    def count(self):
        return self.model.ItemCount

    @property
    def value(self):
        return self.model.Text.strip()
    @value.setter
    def value(self, value):
        self.model.Text = value

    @property
    def data(self):
        return self.model.StringItemList
    @data.setter
    def data(self, value):
        self.model.StringItemList = value

    @property
    def dropdown(self):
        return self.model.Dropdown
    @dropdown.setter
    def dropdown(self, value):
        self.model.Dropdown = value

    def insert(self, text: str, pos: int=-1, image: str=''):
        if pos == -1:
            pos = self.count
        self.model.insertItemText(pos, text)
        return

class UnoCheckBox(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'checkbox'

    @property
    def value(self):
        return self.model.State
    @value.setter
    def value(self, value):
        self.model.State = value

    @property
    def label(self):
        return self.model.Label
    @label.setter
    def label(self, value):
        self.model.Label = value

    @property
    def tri_state(self):
        return self.model.TriState
    @tri_state.setter
    def tri_state(self, value):
        self.model.TriState = value


class UnoSpinButton(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'spinbutton'

    @property
    def value(self):
        return self.model.SpinValue
    @value.setter
    def value(self, value):
        self.model.SpinValue = value


class UnoNumericField(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'numeric'

    @property
    def int(self):
        return int(self.value)

    @property
    def value(self):
        return self.model.Value
    @value.setter
    def value(self, value):
        self.model.Value = value


class UnoListBox(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._path = ''

    #  def __setattr__(self, name, value):
        #  if name in ('_path',):
            #  self.__dict__[name] = value
        #  else:
            #  super().__setattr__(name, value)

    @property
    def type(self):
        return 'listbox'

    @property
    def value(self):
        return self.obj.getSelectedItem()

    @property
    def count(self):
        return len(self.data)

    @property
    def data(self):
        return self.model.StringItemList
    @data.setter
    def data(self, values):
        self.model.StringItemList = list(sorted(values))

    #  @property
    #  def path(self):
        #  return self._path
    #  @path.setter
    #  def path(self, value):
        #  self._path = value

    @property
    def selected_item_pos(self):
        return self.obj.SelectedItemPos
    @property
    def pos(self):
        return self.selected_item_pos

    def unselect(self):
        self.obj.selectItem(self.value, False)
        return

    def select(self, pos=0):
        if isinstance(pos, str):
            self.obj.selectItem(pos, True)
        else:
            self.obj.selectItemPos(pos, True)
        return

    def clear(self):
        self.model.removeAllItems()
        return

    def _set_image_url(self, image):
        if _P.exists(image):
            return _P.to_url(image)

        path = _P.join(self._path, DIR['images'], image)
        return _P.to_url(path)

    def insert(self, value, path='', pos=-1, show=True):
        if pos < 0:
            pos = self.count
        if path:
            self.model.insertItem(pos, value, self._set_image_url(path))
        else:
            self.model.insertItemText(pos, value)
        if show:
            self.select(pos)
        return

    def remove(self, pos=-1):
        if pos == -1:
            pos = self.pos
        self.model.removeItem(pos)
        return


UNO_CLASSES = {
    'label': UnoLabel,
    'button': UnoButton,
    'text': UnoText,
    'link': UnoLabelLink,
    'image': UnoImage,
    'pattern': UnoPattern,
    'combobox': UnoComboBox,
    'checkbox': UnoCheckBox,
    'spinbutton': UnoSpinButton,
    'numeric': UnoNumericField,
    'listbox': UnoListBox,
    # ~ 'radio': UnoRadio,
    # ~ 'roadmap': UnoRoadmap,
    # ~ 'tree': UnoTree,
    # ~ 'grid': UnoGrid,
    # ~ 'pages': UnoPages,
}


class DialogBox(BaseObject):
    SERVICE = 'com.sun.star.awt.DialogProvider'
    SERVICE_DIALOG = 'com.sun.star.awt.UnoControlDialog'
    DIALOG_EMPTY = 'dialog.xml'

    def __init__(self, properties: dict={}):
        self._resizable = False
        self._window = None
        obj = self._create(properties)
        super().__init__(obj)
        self._init_controls()
        self._events = None
        self._modal = False
        self._dir_images = 'images'
        self._id_extension = ''
        self._path_extension = ''
        self._path_images = ''

    def _create_from_path(self, path: str):
        dp = create_instance(self.SERVICE, True)
        dialog = dp.createDialog(Paths.to_url(path))
        return dialog

    def _create_from_location(self, properties: dict):
        # ~ uid = docs.active.uid
        # ~ url = f'vnd.sun.star.tdoc:/{uid}/Dialogs/{library}/{name}.xml'

        name = properties['Name']
        library = properties.get('Library', 'Standard')
        location = properties.get('Location', 'application').lower()

        if location == 'user':
            location = 'application'

        url = f'vnd.sun.star.script:{library}.{name}?location={location}'

        if location == 'document':
            doc = properties.get('Document', LODocuments().active)
            if hasattr(doc, 'obj'):
                doc = doc.obj
            dp = create_instance(self.SERVICE, arguments=doc)
        else:
            dp = create_instance(self.SERVICE, True)

        dialog = dp.createDialog(url)
        return dialog

    def _create_from_properties(self, properties: dict):
        dialog = create_instance(self.SERVICE_DIALOG, True)
        model = create_instance(f'{self.SERVICE_DIALOG}Model', True)

        properties['Width'] = properties.get('Width', 200)
        properties['Height'] = properties.get('Height', 150)

        set_properties(model, properties)
        dialog.setModel(model)
        dialog.setVisible(False)
        dialog.createPeer(Services.toolkit, None)
        return dialog

    def _create_resizable(self, properties: dict):
        path_xml = Paths.get_path(__file__, self.DIALOG_EMPTY)

        x = properties.pop('X', 0)
        y = properties.pop('Y', 0)
        w = properties.pop('Width', 250)
        h = properties.pop('Height', 200)

        parent = LODocuments().active._cw
        toolkit = parent.Toolkit

        wd = WindowDescriptor()
        wd.Type = WindowClass.SIMPLE
        wd.WindowServiceName = 'dialog'
        wd.Parent = parent
        wd.ParentIndex = -1
        wd.Bounds = Rectangle()
        wd.WindowAttributes = WindowAttribute.DEFAULT
        self._window = toolkit.createWindow(wd)

        service = 'com.sun.star.awt.ContainerWindowProvider'
        cwp = create_instance(service, True)
        dialog = cwp.createContainerWindow(path_xml, '', self._window, None)

        ps = dialog.getPosSize()
        pixel = dialog.convertSizeToPixel(Size(w, h), APPFONT)
        w = pixel.Width
        h = pixel.Height

        dialog.setPosSize(x, y, w, h, POSSIZE)
        dialog.setVisible(True)
        self._window.setPosSize(x, y, w, h, POSSIZE)

        set_properties(dialog.Model, properties)
        for k, v in properties.items():
            if hasattr(self._window, k):
                setattr(self._window, k, v)

        return dialog

    def _create(self, properties: dict):
        path = properties.pop('Path', '')
        self._resizable = properties.pop('Resizable', False)
        if path:
            dialog = self._create_from_path(path)
        elif 'Location' in properties and not self._resizable:
            dialog = self._create_from_location(properties)
        elif self._resizable:
            dialog = self._create_resizable(properties)
        else:
            dialog = self._create_from_properties(properties)

        return dialog

    def _init_controls(self):
        for control in self.obj.Controls:
            tipo = control.ImplementationName
            name = control.Model.Name
            if not tipo in TYPE_CONTROL:
                debug(f'Type control: {tipo}')
                raise AttributeError(f"Has no class '{tipo}'")
            control = UNO_CLASSES[TYPE_CONTROL[tipo]](control)
            setattr(self, name, control)
        return

    def execute(self):
        d = self.obj
        if self._resizable:
            d = self._window
        return d.execute()

    def open(self, modal=False):
        self._modal = modal
        if modal:
            self.visible = True
            return
        return self.execute()

    def close(self, value=0):
        if self._modal:
            self.visible = False
            self.obj.dispose()
        else:
            d = self.obj
            if self._resizable:
                d = self._window
            value = d.endDialog(value)
        return value

    @property
    def model(self):
        return self.obj.Model

    @property
    def name(self):
        return self.model.Name

    @property
    def height(self):
        return self.model.Height
    @height.setter
    def height(self, value):
        self.model.Height = value

    @property
    def width(self):
        return self.model.Width
    @width.setter
    def width(self, value):
        self.model.Width = value

    @property
    def visible(self):
        return self.obj.Visible
    @visible.setter
    def visible(self, value):
        self.obj.Visible = value

    @property
    def step(self):
        return self.model.Step
    @step.setter
    def step(self, value):
        self.model.Step = value

    @property
    def color_on_focus(self):
        return self._color_on_focus
    @color_on_focus.setter
    def color_on_focus(self, value):
        self._color_on_focus = get_color(value)

    @property
    def properties(self):
        properties = self.model.PropertySetInfo.Properties
        data = {}
        for p in properties:
            try:
                data[p.Name] = getattr(self.model, p.Name)
            except:
                continue
        return data

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, controllers):
        self._events = controllers(self)
        self._connect_listeners()

    @property
    def title(self):
        return self.obj.Title
    @title.setter
    def title(self, value):
        self.obj.Title = value
        if self._resizable:
            self._window.Title = value

    @property
    def resizable(self):
        return self._resizable

    @property
    def dir_images(self):
        return self._dir_images
    @dir_images.setter
    def dir_images(self, value):
        self._dir_images = value
        self._set_paths()

    @property
    def id_extension(self):
        return self._id_extension
    @id_extension.setter
    def id_extension(self, value):
        self._id_extension = value
        self._set_paths()

    def _set_paths(self):
        self._path_extension = Paths.extension(self.id_extension)
        self._path_images = Paths.join(self._path_extension, self.dir_images)
        return

    def _connect_listeners_dialog(self):
        listeners = {
            'addTopWindowListener': EventsWindow,
            'addWindowListener': EventsWindow,
        }
        obj = self.obj
        if self._resizable:
            obj = self._window
        for key, value in listeners.items():
            if hasattr(self._window, key):
                getattr(self._window, key)(value(self._events, self.name))

        listeners = {
            'addMouseListener': EventsMouse,
        }
        for key, value in listeners.items():
            if hasattr(self.obj, key):
                getattr(self.obj, key)(value(self._events, self.name))
        return

    def _connect_listeners(self):
        for control in self.obj.Controls:
            add_listeners(self.events, control)
        self._connect_listeners_dialog()
        return

    def _set_image_url(self, image: str):
        if Paths.exists(image):
            return Paths.to_url(image)

        path_image = Paths.join(self._path_images, image)
        return Paths.to_url(path_image)

    def _special_properties(self, tipo, properties):
        if tipo == 'link' and 'URL' in properties and not 'Label' in properties:
            properties['Label'] = properties['URL']
            return properties

        if tipo == 'label':
            properties['VerticalAlign'] = properties.get('VerticalAlign', 1)
            return properties

        if tipo == 'button':
            if 'ImageURL' in properties:
                properties['ImageURL'] = self._set_image_url(properties['ImageURL'])
                properties['ImageAlign'] = properties.get('ImageAlign', 0)
            properties['FocusOnClick'] = properties.get('FocusOnClick', False)
            return properties

        if tipo == 'roadmap':
            properties['Height'] = properties.get('Height', self.height)
            if 'Title' in properties:
                properties['Text'] = properties.pop('Title')
            return properties

        if tipo == 'tree':
            properties['SelectionType'] = properties.get('SelectionType', SINGLE)
            return properties

        if tipo == 'grid':
            properties['X'] = properties.get('X', SEPARATION)
            properties['Y'] = properties.get('Y', SEPARATION)
            properties['Width'] = properties.get('Width', self.width - SEPARATION * 2)
            properties['Height'] = properties.get('Height', self.height - SEPARATION * 2)
            properties['ShowRowHeader'] = properties.get('ShowRowHeader', True)
            return properties

        if tipo == 'pages':
            properties['Width'] = properties.get('Width', self.width)
            properties['Height'] = properties.get('Height', self.height)

        return properties

    def add_control(self, properties):
        tipo = properties.pop('Type').lower()
        root = properties.pop('Root', '')
        sheets = properties.pop('Sheets', ())
        columns = properties.pop('Columns', ())

        properties = self._special_properties(tipo, properties)
        model = self.model.createInstance(MODELS[tipo])

        set_properties(model, properties)
        name = properties['Name']
        self.model.insertByName(name, model)
        control = self.obj.getControl(name)
        add_listeners(self.events, control)
        control = UNO_CLASSES[tipo](control)

        #  if tipo in ('listbox',):
            #  control.path = self.path

        if tipo == 'tree' and root:
            control.root = root
        elif tipo == 'grid' and columns:
            control.columns = columns
        elif tipo == 'pages' and sheets:
            control.sheets = sheets
            control.events = self.events

        setattr(self, name, control)

        return control

    def remove_control(self, name):
        self.model.removeByName(name)
        return


class LODialog():
    @classmethod
    def create(cls, properties: dict={}):
        return DialogBox(properties)


def inputbox(message, default: str='', title: str=TITLE, echochar: str=''):

    class ControllersInput(object):

        def __init__(self, dialog):
            self.d = dialog

        def cmd_ok_action(self, event):
            self.d.close(1)
            return

    properties = {
        'Title': title,
        'Width': 200,
        'Height': 80,
    }
    dlg = DialogBox(properties)
    dlg.events = ControllersInput

    properties = {
        'Type': 'Label',
        'Name': 'lbl_msg',
        'Label': message,
        'Width': 140,
        'Height': 50,
        'X': 5,
        'Y': 5,
        'MultiLine': True,
        'Border': 1,
    }
    dlg.add_control(properties)

    properties = {
        'Type': 'Text',
        'Name': 'txt_value',
        'Text': default,
        'Width': 190,
        'Height': 15,
    }
    if echochar:
        properties['EchoChar'] = ord(echochar[0])
    dlg.add_control(properties)
    dlg.txt_value.move(dlg.lbl_msg)

    properties = {
        'Type': 'button',
        'Name': 'cmd_ok',
        'Label': _('OK'),
        'Width': 40,
        'Height': 15,
        'DefaultButton': True,
        'PushButtonType': 1,
    }
    dlg.add_control(properties)
    dlg.cmd_ok.move(dlg.lbl_msg, 10, 0)

    properties = {
        'Type': 'button',
        'Name': 'cmd_cancel',
        'Label': _('Cancel'),
        'Width': 40,
        'Height': 15,
        'PushButtonType': 2,
    }
    dlg.add_control(properties)
    dlg.cmd_cancel.move(dlg.cmd_ok)

    value = ''
    if dlg.open():
        value = dlg.txt_value.value

    return value
