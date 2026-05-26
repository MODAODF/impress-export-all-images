#!/usr/bin/env python

from typing import Any

from com.sun.star.awt import Size, Point
from com.sun.star.beans import NamedValue

from .easyevents import get_script_event_descriptor
from .easymain import log, BaseObject, set_properties, get_properties
from .easyuno import BaseObjectProperties
from .constants import SEPARATION, Direction


# ~ https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1form_1_1component.html
CONTROL_SHAPE = 'com.sun.star.drawing.ControlShape'

MODELS = {
    'hidden': 'com.sun.star.form.component.HiddenControl',
    'label': 'com.sun.star.form.component.FixedText',
    'text': 'com.sun.star.form.component.TextField',
    'checkbox': 'com.sun.star.form.component.CheckBox',
}

TYPE_CONTROLS = {
    'com.sun.star.form.OHiddenModel': 'hidden',
    'stardiv.Toolkit.UnoFixedTextControl': 'label',
    'com.sun.star.form.OEditControl': 'text',
    'com.sun.star.form.OCheckBoxControl': 'checkbox',
}
CONTROLS_TYPE = {
    'hidden': 'com.sun.star.form.OHiddenModel',
    'label': 'stardiv.Toolkit.UnoFixedTextControl',
    'text': 'com.sun.star.form.OEditControl',
    'checkbox': 'com.sun.star.form.OCheckBoxControl',
}

# ~ def _set_properties(model, properties):
    # ~ keys = tuple(properties.keys())
    # ~ values = tuple(properties.values())
    # ~ model.setPropertyValues(keys, values)
    # ~ return


class ShapeBase(BaseObjectProperties):

    def __init__(self, obj: Any):
        super().__init__(obj)


class FormBaseControl(BaseObjectProperties):

    def __init__(self, obj: Any, shape: Any):
        super().__init__(obj)
        self._shape = shape
        self._doc = obj.Parent.Parent.Parent
        self._index = -1
        try:
            self._view = self._doc.CurrentController.getControl(self.obj)
        except Exception as e:
            self._view = None

    @property
    def index(self):
        return self._index
    @index.setter
    def index(self, value):
        self._index = value

    @property
    def shape(self):
        return ShapeBase(self._shape)

    @property
    def name(self):
        return self.obj.Name

    @property
    def properties(self):
        return get_properties(self.obj)
    @properties.setter
    def properties(self, values: dict):
        set_properties(self.obj, values)

    @property
    def border(self):
        return self.obj.Border
    @border.setter
    def border(self, value):
        self.obj.Border = value

    @property
    def border_color(self):
        return self.obj.BorderColor
    @border_color.setter
    def border_color(self, value):
        self.obj.BorderColor = value

    @property
    def enabled(self):
        return self.obj.Enabled
    @enabled.setter
    def enabled(self, value):
        self.obj.Enabled = value

    @property
    def visible(self):
        return self._view.Visible
    @visible.setter
    def visible(self, value):
        self._view.Visible = value

    @property
    def value_binding(self):
        return self.cell
    @value_binding.setter
    def value_binding(self, value):
        self.cell = value
    @property
    def cell(self):
        return self.obj.ValueBinding.BoundCell
    @cell.setter
    def cell(self, value):
        SERVICE = 'com.sun.star.table.CellValueBinding'
        options = (NamedValue(Name='BoundCell', Value=value.address),)
        value_binding = self._doc.createInstanceWithArguments(SERVICE, options)
        self.obj.ValueBinding = value_binding

    @property
    def anchor(self):
        return self._shape.Anchor
    @anchor.setter
    def anchor(self, value):
        self._shape.Anchor = value.obj
        self._shape.ResizeWithCell = True

    @property
    def width(self):
        return self._shape.Size.Width
    @width.setter
    def width(self, value):
        self._shape.Size = Size(value, self.height)

    @property
    def height(self):
        return self._shape.Size.Height
    @height.setter
    def height(self, value):
        self._shape.Size = Size(self.width, value)

    @property
    def position(self):
        return self._shape.Position
    @position.setter
    def position(self, value):
        self._shape.Position = value

    @property
    def tag(self):
        return self.obj.Tag
    @tag.setter
    def tag(self, value):
        self.obj.Tag = value

    @property
    def char_height(self):
        return self.shape.CharHeight
    @char_height.setter
    def char_height(self, value):
        self.shape.CharHeight = value

    @property
    def font_name(self):
        return self.obj.FontName
    @font_name.setter
    def font_name(self, value):
        self.obj.FontName = value

    @property
    def font_height(self):
        return self.obj.FontHeight
    @font_height.setter
    def font_height(self, value):
        self.obj.FontHeight = value

    @property
    def font_color(self):
        return self.text_color
    @font_color.setter
    def font_color(self, value):
        self.text_color = value
    @property
    def text_color(self):
        return self.obj.TextColor
    @text_color.setter
    def text_color(self, value):
        self.obj.TextColor = value

    @property
    def background_color(self):
        return self.obj.BackgroundColor
    @background_color.setter
    def background_color(self, value):
        self.obj.BackgroundColor = value

    @property
    def align(self):
        return self.obj.Align
    @align.setter
    def align(self, value):
        self.obj.Align = value

    @property
    def vertical_align(self):
        return self.obj.VerticalAlign
    @vertical_align.setter
    def vertical_align(self, value):
        self.obj.VerticalAlign = value

    @property
    def read_only(self):
        return self.obj.ReadOnly
    @read_only.setter
    def read_only(self, value):
        self.obj.ReadOnly = value

    @property
    def data_field(self):
        return self.obj.DataField
    @data_field.setter
    def data_field(self, value):
        self.obj.DataField = value

    @property
    def printable(self):
        return self.obj.Printable
    @printable.setter
    def printable(self, value):
        self.obj.Printable = value

    def center(self):
        cell = self.anchor
        size = cell.Size
        pos = cell.Position
        pos.X += (size.Width / 2) - (self.width / 2)
        self.position = pos
        return

    def set_focus(self):
        self._view.setFocus()
        return

    def move(self, source: Any, direction: int=Direction.BOTTOM, separation: int=SEPARATION):
        position = source.position

        if direction == 1:
            position.Y = position.Y - self.height - separation
        elif direction == 2:
            position.X += source.width + separation
        elif direction == 3:
            position.Y += self.height + separation
        elif direction == 4:
            position.X = position.X - self.width - separation

        self.position = position
        return


class FormLabel(FormBaseControl):

    def __init__(self, obj: Any, shape: Any):
        super().__init__(obj, shape)

    def __str__(self):
        return f'{self.type}: {self.name}'

    @property
    def type(self):
        return 'label'

    @property
    def value(self):
        return self.obj.Label
    @value.setter
    def value(self, value):
        self.obj.Label = value


class FormText(FormBaseControl):

    def __init__(self, obj: Any, shape: Any):
        super().__init__(obj, shape)

    def __str__(self):
        return f'{self.type}: {self.name}'

    @property
    def type(self):
        return 'text'

    @property
    def value(self):
        return self.obj.Text
    @value.setter
    def value(self, value):
        self.obj.Text = value

    @property
    def echo_char(self):
        return self.obj.EchoChar
    @echo_char.setter
    def echo_char(self, value: str):
        self.obj.EchoChar = ord(value)

    @property
    def max_text_len(self):
        return self.obj.MaxTextLen
    @max_text_len.setter
    def max_text_len(self, value):
        self.obj.MaxTextLen = value

    @property
    def multi_line(self):
        return self.obj.MultiLine
    @multi_line.setter
    def multi_line(self, value):
        self.obj.MultiLine = value

    @property
    def rich_text(self):
        return self.obj.RichText
    @rich_text.setter
    def rich_text(self, value):
        self.obj.RichText = value

    @property
    def hscroll(self):
        return self.obj.HScroll
    @hscroll.setter
    def hscroll(self, value):
        self.obj.HScroll = value

    @property
    def vscroll(self):
        return self.obj.VScroll
    @vscroll.setter
    def vscroll(self, value):
        self.obj.VScroll = value


class FormCheckBox(FormBaseControl):

    def __init__(self, obj: Any, shape: Any):
        super().__init__(obj, shape)

    def __str__(self):
        return f'{self.type}: {self.name}'

    @property
    def type(self):
        return 'checkbox'

    @property
    def value(self):
        return self.obj.State
    @value.setter
    def value(self, value: int):
        self.obj.State = value

    @property
    def tri_state(self):
        return self.obj.TriState
    @tri_state.setter
    def tri_state(self, value: bool):
        self.obj.TriState = value

    @property
    def border(self):
        return self.obj.VisualEffect
    # ~ Not work
    @border.setter
    def border(self, value: int):
        self.obj.VisualEffect = value


class FormHidden(FormBaseControl):

    def __init__(self, obj: Any, shape: Any):
        super().__init__(obj, shape)

    def __str__(self):
        return f'{self.type}: {self.name}'

    @property
    def type(self):
        return 'hidden'

    @property
    def value(self):
        return self.obj.HiddenValue
    @value.setter
    def value(self, value):
        self.obj.HiddenValue = value


FORM_CLASSES = {
    'hidden': FormHidden,
    'label': FormLabel,
    'text': FormText,
    'checkbox': FormCheckBox,
}


class LOForm(BaseObject):

    def __init__(self, obj, draw_page):
        super().__init__(obj)
        self._dp = draw_page
        self._doc = obj.Parent.Parent
        self._events = None
        self._init_controls()

    def _init_controls(self):
        for model in self.obj:
            if model.ImplementationName == CONTROLS_TYPE['hidden']:
                view = None
                tipo = model.ImplementationName
            else:
                view = self._doc.CurrentController.getControl(model)
                tipo = view.ImplementationName

            if not tipo in TYPE_CONTROLS:
                log.error(f'For add form control: {tipo}')
                continue

            control = FORM_CLASSES[TYPE_CONTROLS[tipo]](model, view)
            setattr(self, model.Name, control)
        return

    def __str__(self):
        return f'Form: {self.name}'

    def __contains__(self, item):
        """Contains"""
        return item in self.obj.ElementNames

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        """Interation form"""
        try:
            control = self.obj[self._i]
            control = getattr(self, control.Name)
        except Exception as e:
            raise StopIteration
        self._i += 1
        return control

    def _create_instance(self, name):
        return self._doc.createInstance(name)

    @property
    def name(self):
        return self.obj.Name
    @name.setter
    def name(self, value: str):
        self.obj.setName(value)

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, controllers):
        self._events = controllers(self)

    @property
    def source(self):
        return self.data_source_name
    @source.setter
    def source(self, value):
        self.data_source_name = value
    @property
    def data_source_name(self):
        return self.obj.DataSourceName
    @data_source_name.setter
    def data_source_name(self, value: str):
        self.obj.DataSourceName = value

    @property
    def type_source(self):
        return self.command_type
    @type_source.setter
    def type_source(self, value: int):
        self.command_type = value
    @property
    def command_type(self):
        return self.obj.CommandType
    @command_type.setter
    def command_type(self, value: int):
        self.obj.CommandType = value

    @property
    def sql(self):
        return self.command
    @sql.setter
    def sql(self, value: str):
        self.command = value
    @property
    def command(self):
        return self.obj.Command
    @command.setter
    def command(self, value: str):
        self.obj.Command = value

    def _default_properties(self, tipo: str, properties: dict, shape: Any):
        WIDTH = 7500
        HEIGHT = 750

        width = properties.pop('Width', WIDTH)
        height = properties.pop('Height', HEIGHT)
        shape.Size = Size(width, height)

        x = properties.pop('X', 0)
        y = properties.pop('Y', 0)
        shape.Position = Point(x, y)

        return properties

    def _set_properties(self, model: Any, properties: dict):
        properties_model = {}
        properties_shape = {}

        for k, v in properties.items():
            if hasattr(model, k):
                properties_model[k] = v
            else:
                properties_shape[k] = v

        set_properties(model, properties_model)

        return properties_shape

    def insert(self, properties: dict):
        return self.add_control(properties)

    def add_control(self, properties: dict):
        tipo = properties.pop('Type').lower()
        name = properties['Name']

        shape = self._create_instance(CONTROL_SHAPE)
        self._default_properties(tipo, properties, shape)

        model = self._create_instance(MODELS[tipo])
        properties = self._set_properties(model, properties)

        if tipo == 'hidden':
            shape = None
        else:
            shape.Control = model

        index = self.obj.Count
        self.obj.insertByIndex(index, model)
        if not shape is None:
            self._dp.add(shape)
        control = FORM_CLASSES[tipo](model, shape)
        control.index = index
        setattr(self, name, control)

        if properties:
            set_properties(shape, properties)

        return control

    def get_event(self, name, macro):
        return get_script_event_descriptor(name, macro)


class LOForms(BaseObject):

    def __init__(self, obj):
        self._dp = obj
        super().__init__(obj.Forms)

    def __getitem__(self, index):
        """Index access"""
        return LOForm(self.obj[index], self._dp)

    def __setitem__(self, key: str, value: Any):
        """Insert new form"""
        self.obj[key] = value

    def __len__(self):
        """Count forms"""
        return len(self.obj)

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        """Interation forms"""
        try:
            form = LOForm(self.obj[self._i], self._dp)
        except Exception as e:
            raise StopIteration
        self._i += 1
        return form

    def __contains__(self, item):
        """Contains"""
        return item in self.obj

    def new_form(self):
        """Create new instance form"""
        form = self.obj.Parent.createInstance('com.sun.star.form.component.Form')
        return form

    def insert(self, name: str):
        """Insert new form

        :param name: Name new form.
        :type name: str
        :return: New instance LOForm.
        :rtype: LOForm
        """
        form = self.new_form()
        self.obj.insertByName(name, form)
        return LOForm(form, self._dp)
