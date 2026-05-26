#!/usr/bin/env python3

from typing import Any

from com.sun.star.awt import Size, Point
from .easymain import (
    BaseObject, Paths,
    create_instance, dict_to_property, log, set_properties, get_properties
    )
from .easyuno import (
    AnimationEffect,
    BaseObjectProperties,
    IOStream,
    get_input_stream)

IMAGE = 'com.sun.star.drawing.GraphicObjectShape'

MIME_TYPE = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/svg': 'svg',
}

TYPE_MIME = {
    'svg': 'image/svg',
    'png': 'image/png',
    'jpg': 'image/jpeg',
}


class LOShapes(object):
    _type = 'ShapeCollection'

    def __init__(self, obj):
        self._obj = obj

    def __len__(self):
        return self.obj.Count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        try:
            s = self.obj[self._index]
            shape = LOShape(s)
        except IndexError:
            raise StopIteration

        self._index += 1
        return shape

    def __str__(self):
        return 'Shapes'

    @property
    def obj(self):
        return self._obj


class LOShape(BaseObjectProperties):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'Shape: {self.name}'

    @property
    def sheet(self):
        return self.anchor
    @sheet.setter
    def sheet(self, value):
        self.anchor = value
    @property
    def cell(self):
        return self.anchor
    @cell.setter
    def cell(self, value):
        self.anchor = value
    @property
    def anchor(self):
        from .easycalc import LOCalcSheet, LOCalcRange
        TYPE_ANCHOR = {
            'ScTableSheetObj': LOCalcSheet,
            'ScCellObj': LOCalcRange,
        }
        """Get anchor object"""
        obj = self.obj.Anchor
        implementation = obj.ImplementationName
        if implementation in TYPE_ANCHOR:
            obj = TYPE_ANCHOR[implementation](obj)
        else:
            log.debug(implementation)
        return obj
    @anchor.setter
    def anchor(self, obj):
        if hasattr(obj, 'obj'):
            obj = obj.obj
        self.obj.Anchor = obj
        return

    @property
    def resize_with_cell(self):
        """If resize with cell"""
        return self.obj.ResizeWithCell
    @resize_with_cell.setter
    def resize_with_cell(self, value):
        self.obj.ResizeWithCell = value
        return

    @property
    def properties(self):
        """Get all properties"""
        return get_properties(self.obj)
    @properties.setter
    def properties(self, values):
        set_properties(self.obj, values)

    @property
    def shape_type(self):
        """Get type shape"""
        return self.obj.ShapeType
    @property
    def type(self):
        value = ''
        if hasattr(self.obj, 'CustomShapeGeometry'):
            for p in self.obj.CustomShapeGeometry:
                if p.Name == 'Type':
                    value = p.Value
                    break
        else:
            value = self.shape_type
        return value

    @property
    def name(self):
        """Get name"""
        return self.obj.Name
    @name.setter
    def name(self, value):
        self.obj.Name = value

    @property
    def is_image(self):
        #  FrameShape
        return self.shape_type == IMAGE

    @property
    def is_shape(self):
        return self.shape_type != IMAGE

    @property
    def size(self):
        s = self.obj.Size
        return s
    @size.setter
    def size(self, value):
        self.obj.Size = value

    @property
    def width(self):
        """Width of shape"""
        s = self.obj.Size
        return s.Width
    @width.setter
    def width(self, value):
        s = self.size
        s.Width = value
        self.size = s

    @property
    def height(self):
        """Height of shape"""
        s = self.obj.Size
        return s.Height
    @height.setter
    def height(self, value):
        s = self.size
        s.Height = value
        self.size = s

    @property
    def position(self):
        return self.obj.Position
    @property
    def x(self):
        """Position X"""
        return self.position.X
    @x.setter
    def x(self, value):
        self.obj.Position = Point(value, self.y)

    @property
    def y(self):
        """Position Y"""
        return self.position.Y
    @y.setter
    def y(self, value):
        self.obj.Position = Point(self.x, value)

    @property
    def possize(self):
        data = {
            'Width': self.size.Width,
            'Height': self.size.Height,
            'X': self.position.X,
            'Y': self.position.Y,
        }
        return data
    @possize.setter
    def possize(self, value):
        self.obj.Size = Size(value['Width'], value['Height'])
        self.obj.Position = Point(value['X'], value['Y'])

    @property
    def string(self):
        return self.obj.String
    @string.setter
    def string(self, value):
        self.obj.String = value

    @property
    def title(self):
        return self.obj.Title
    @title.setter
    def title(self, value):
        self.obj.Title = value

    @property
    def description(self):
        return self.obj.Description
    @description.setter
    def description(self, value):
        self.obj.Description = value

    @property
    def in_background(self):
        return self.obj.LayerID
    @in_background.setter
    def in_background(self, value):
        self.obj.LayerID = value

    @property
    def layerid(self):
        return self.obj.LayerID
    @layerid.setter
    def layerid(self, value):
        self.obj.LayerID = value

    @property
    def mime_type(self):
        mt = self.obj.GraphicURL.MimeType
        mime_type = MIME_TYPE.get(mt, mt)
        return mime_type

    @property
    def path(self):
        return self.url
    @property
    def url(self):
        if self.is_image:
            url = Paths.to_system(self.obj.GraphicURL.OriginURL)
        else:
            url = self.obj.FillBitmapName
        return url
    @url.setter
    def url(self, value):
        self.obj.FillBitmapURL = Paths.to_url(value)

    @property
    def visible(self):
        return self.obj.Visible
    @visible.setter
    def visible(self, value):
        self.obj.Visible = value

    @property
    def doc(self):
        return self.obj.Parent.Forms.Parent

    @property
    def text_box(self):
        return self.obj.TextBox
    @text_box.setter
    def text_box(self, value):
        self.obj.TextBox = value

    @property
    def text_box_content(self):
        return self.obj.TextBoxContent
    # ~ @property
    # ~ def text_box_content(self):
        # ~ controller = self.doc.CurrentController
        # ~ vc = controller.ViewCursor
        # ~ tbx = self.obj.TextBoxContent
        # ~ vc.gotoRange(tbx.Start, False)
        # ~ vc.gotoRange(tbx.End, True)
        # ~ text = controller.getTransferable()
        # ~ return text

    @property
    def fill_color(self):
        return self.obj.FillColor
    @fill_color.setter
    def fill_color(self, value):
        self.obj.FillColor = value

    # Only for Impress
    @property
    def effect(self):
        self.obj.Effect
    @effect.setter
    def effect(self, value):
        self.obj.Effect = value

    @property
    def speed(self):
        self.obj.Speed
    @speed.setter
    def speed(self, value):
        self.obj.Speed = value

    def get_path(self, path: str='', name: str='', mime_type: str=''):
        if not path:
            path = Paths(self.doc.URL).path
        if not name:
            name = self.name.replace(' ', '_')
        if mime_type:
            file_name = f'{name}.{mime_type}'
        else:
            if self.is_image:
                file_name = f'{name}.{self.mime_type}'
            else:
                file_name = f'{name}.svg'
        path = Paths.join(path, file_name)
        return path

    def select(self):
        controller = self.doc.CurrentController
        controller.select(self.obj)
        return

    def delete(self):
        self.remove()
        return
    def remove(self):
        """Auto remove"""
        self.obj.Parent.remove(self.obj)
        return

    def export(self, path: str=''):
        if not path:
            path = self.get_path()
        mime_type = Paths(path).ext
        options = {
            'URL': Paths.to_url(path),
            'MimeType': TYPE_MIME.get(mime_type, mime_type)}
        args = dict_to_property(options)
        export = create_instance('com.sun.star.drawing.GraphicExportFilter')
        export.setSourceDocument(self.obj)
        export.filter(args)
        return path

    def save(self, path: str=''):
        """Save image"""
        if not path:
            path = self.get_path()

        if self.is_image:
            data = IOStream.to_bin(self.obj.GraphicStream)
            Paths.save_bin(path, data)
        else:
            self.export(path)

        return path

    def _get_graphic(self):
        stream = self.obj.GraphicStream
        buffer = IOStream.output()
        _, data = stream.readBytes(buffer, stream.available())
        stream = get_input_stream(data)
        gp = create_instance('com.sun.star.graphic.GraphicProvider')
        properties = dict_to_property({'InputStream': stream})
        graphic = gp.queryGraphic(properties)
        return graphic

    def clone(self, draw_page: Any=None, x: int=1000, y: int=1000):
        """Clone image"""
        image = self.doc.createInstance('com.sun.star.drawing.GraphicObjectShape')
        image.Graphic = self._get_graphic()
        if draw_page is None:
            draw_page = self.obj.Parent
        else:
            if hasattr(draw_page, 'obj'):
                draw_page = draw_page.obj

        draw_page.add(image)
        image.Size = self.size
        position = self.position
        position.X += x
        position.Y += y
        image.Position = position
        return LOShape(image)

    def original_size(self):
        self.size = self.obj.ActualSize
        return

