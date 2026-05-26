#!/usr/bin/env python3

from pathlib import Path
from com.sun.star.awt import Size, Point

from .easymain import (
    BaseObject,
    create_instance,
    dict_to_property,
    set_properties)
from .easyshape import LOShape
from .easydoc import IOStream


DEFAULT_WH = 3000
DEFAULT_XY = 1000

TYPE_SHAPES = ('Line', 'Measure', 'Rectangle', 'Ellipse', 'Text', 'Connector',
    'ClosedBezier', 'OpenBezier', 'PolyLine', 'PolyPolygon', 'ClosedFreeHand',
    'OpenFreeHand')

# ~ class LOShapeBK(BaseObject):

    # ~ @property
    # ~ def linked(self):
        # ~ l = False
        # ~ if self.is_image:
            # ~ l = self.obj.GraphicURL.Linked
        # ~ return l

    # ~ def save2(self, path: str):
        # ~ size = len(self.obj.Bitmap.DIB)
        # ~ data = self.obj.GraphicStream.readBytes((), size)
        # ~ data = data[-1].value
        # ~ path = _P.join(path, f'{self.name}.png')
        # ~ _P.save_bin(path, b'')
        # ~ return


class LODrawPage(BaseObject):
    _type = 'draw_page'

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        if isinstance(index, int):
            shape = LOShape(self.obj[index])
        else:
            for i, o in enumerate(self.obj):
                shape = self.obj[i]
                name = shape.Name or f'shape{i}'
                if name == index:
                    shape = LOShape(shape)
                    break
        return shape

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index == self.count:
            raise StopIteration
        shape = self[self._index]
        self._index += 1
        return shape

    def __contains__(self, source_name):
        result = False
        for i, o in enumerate(self.obj):
            shape = self.obj[i]
            name = shape.Name or f'shape{i}'
            if name == source_name:
                result = True
                break
        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __len__(self):
        """Count shapes"""
        return self.count

    @property
    def name(self):
        return self.obj.Name

    @property
    def doc(self):
        return self.obj.Forms.Parent

    @property
    def width(self):
        return self.obj.Width

    @property
    def height(self):
        return self.obj.Height

    @property
    def count(self):
        return self.obj.Count

    @property
    def last(self):
        return self[self.count - 1]

    def _create_instance(self, name):
        return self.doc.createInstance(name)

    def select(self, shape):
        if hasattr(shape, 'obj'):
            shape = shape.obj
        controller = self.doc.CurrentController
        controller.select(shape)
        return

    def add(self, type_shape, options={}):
        properties = options.copy()
        """Insert a shape in page, type shapes:
            Line
            Measure
            Rectangle
            Ellipse
            Text
            Connector
            ClosedBezier
            OpenBezier
            PolyLine
            PolyPolygon
            ClosedFreeHand
            OpenFreeHand
        """
        index = self.count
        default_height = DEFAULT_WH
        if type_shape == 'Line':
            default_height = 0
        w = properties.pop('Width', DEFAULT_WH)
        h = properties.pop('Height', default_height)
        x = properties.pop('X', DEFAULT_XY)
        y = properties.pop('Y', DEFAULT_XY)
        name = properties.pop('Name', f'{type_shape.lower()}{index}')

        if type_shape in TYPE_SHAPES:
            service = f'com.sun.star.drawing.{type_shape}Shape'
        else:
            service = 'com.sun.star.drawing.CustomShape'
        shape = self._create_instance(service)
        shape.Size = Size(w, h)
        shape.Position = Point(x, y)
        shape.Name = name
        self.obj.add(shape)

        if not type_shape in TYPE_SHAPES:
            shape.CustomShapeGeometry = dict_to_property({'Type': type_shape})

        if properties:
            set_properties(shape, properties)

        return LOShape(self.obj[index])

    def remove(self, shape):
        if hasattr(shape, 'obj'):
            shape = shape.obj
        return self.obj.remove(shape)

    def remove_all(self):
        while self.count:
            self.obj.remove(self.obj[0])
        return

    def insert_image(self, path, options={}):
        args = options.copy()
        index = self.count
        w = args.get('Width', 3000)
        h = args.get('Height', 3000)
        x = args.get('X', 1000)
        y = args.get('Y', 1000)
        name = args.get('Name', f'image{index}')

        image = self._create_instance('com.sun.star.drawing.GraphicObjectShape')
        if isinstance(path, str):
            image.GraphicURL = Path(path).as_uri()
        else:
            # ~ URL = path
            gp = create_instance('com.sun.star.graphic.GraphicProvider')
            stream = IOStream.input(path)
            properties = dict_to_property({'InputStream': stream})
            image.Graphic = gp.queryGraphic(properties)

        self.obj.add(image)
        image.Size = Size(w, h)
        image.Position = Point(x, y)
        image.Name = name
        return LOShape(self.obj[index])


class LOGalleryItem(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'Gallery Item: {self.name}'

    @property
    def name(self):
        return self.obj.Title

    @property
    def url(self):
        return self.obj.URL

    @property
    def type(self):
        """https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1gallery_1_1GalleryItemType.html"""
        item_type = {0: 'empty', 1: 'graphic', 2: 'media', 3: 'drawing'}
        return item_type[self.obj.GalleryItemType]


class LOGallery(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._names = [i.Title for i in obj]

    def __str__(self):
        return f'Gallery: {self.name}'

    def __len__(self):
        return len(self.obj)

    def __getitem__(self, index):
        """Index access"""
        if isinstance(index, str):
            index = self._names.index(index)
        return LOGalleryItem(self.obj[index])

    def __iter__(self):
        self._iter = iter(range(len(self)))
        return self

    def __next__(self):
        """Interation items"""
        try:
            item = LOGalleryItem(self.obj[next(self._iter)])
        except Exception as e:
            raise StopIteration
        return item

    @property
    def name(self):
        return self.obj.Name

    @property
    def names(self):
        return self._names


class LOGalleries(BaseObject):

    def __init__(self):
        service_name = 'com.sun.star.gallery.GalleryThemeProvider'
        service = create_instance(service_name)
        super().__init__(service)

    def __getitem__(self, index):
        """Index access"""
        name = index
        if isinstance(index, int):
            name = self.names[index]
        return LOGallery(self.obj[name])

    def __len__(self):
        return len(self.obj)

    def __contains__(self, item):
        """Contains"""
        return item in self.obj

    def __iter__(self):
        self._iter = iter(self.names)
        return self

    def __next__(self):
        """Interation galleries"""
        try:
            gallery = LOGallery(self.obj[next(self._iter)])
        except Exception as e:
            raise StopIteration
        return gallery

    @property
    def names(self):
        return self.obj.ElementNames

