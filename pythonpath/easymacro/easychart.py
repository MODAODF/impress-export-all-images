#!/usr/bin/env python

from typing import Any, Union

from com.sun.star.awt import Rectangle, Point
from .easymain import Paths, log, create_instance, dict_to_property, set_properties


def _set_properties(obj, values):
    for k, v in values.items():
        if hasattr(obj, k):
            setattr(obj, k, v)


class LOChartAxisProperties(object):
    _type = 'Axis properties'

    def __init__(self, obj, name):
        self._obj = obj
        self._name = name
        if name == 'X':
            self._axis = obj.XAxis
            self._axis_title = obj.XAxisTitle
            self._axis_grid = obj.XMainGrid
            self._axis_help = obj.XHelpGrid
        else:
            self._axis = obj.YAxis
            self._axis_title = obj.YAxisTitle
            self._axis_grid = obj.YMainGrid
            self._axis_help = obj.YHelpGrid

    def __str__(self):
        return self._type

    @property
    def obj(self):
        return self._obj

    @property
    def title(self):
        return self._axis_title
    @title.setter
    def title(self, values):
        if self._name == 'X':
            self.obj.HasXAxisTitle = True
        else:
            self.obj.HasYAxisTitle = True
        if isinstance(values, str):
            self._axis_title.String = values
        else:
            _set_properties(self._axis_title, values)

    @property
    def style(self):
        return self._axis
    @style.setter
    def style(self, values):
        _set_properties(self._axis, values)

    @property
    def text_rotation(self):
        return self._axis.TextRotation
    @text_rotation.setter
    def text_rotation(self, value):
        self._axis.TextRotation = value

    @property
    def max(self):
        return self._axis.Max
    @max.setter
    def max(self, value):
        self._axis.Max = value

    @property
    def step_main(self):
        return self._axis.StepMain
    @step_main.setter
    def step_main(self, value):
        self._axis.StepMain = value

    @property
    def step_help_count(self):
        return self._axis.StepHelpCount
    @step_help_count.setter
    def step_help_count(self, value):
        self._axis.StepHelpCount = value

    @property
    def main_grid(self):
        return self._axis_grid
    @main_grid.setter
    def main_grid(self, values):
        _set_properties(self._axis_grid, values)

    @property
    def help_grid(self):
        return self._axis_help
    @help_grid.setter
    def help_grid(self, values):
        has_axis = f'Has{self._name}AxisHelpGrid'
        if values:
            _set_properties(self._axis_help, values)
            setattr(self.obj, has_axis, True)
        else:
            setattr(self.obj, has_axis, False)


class LOChartAxis(object):
    _type = 'Axis'

    def __init__(self, obj):
        self._obj = obj

    def __str__(self):
        return self._type

    @property
    def obj(self):
        return self._obj

    @property
    def x(self):
        return LOChartAxisProperties(self.obj, 'X')

    @property
    def y(self):
        return LOChartAxisProperties(self.obj, 'Y')


class LOChartDataSerie(object):
    _type = 'Chart Data Serie'

    def __init__(self, obj):
        self._obj = obj

    def __str__(self):
        return self._type

    @property
    def obj(self):
        return self._obj

    @property
    def data_caption(self):
        return self.obj.DataCaption
    @data_caption.setter
    def data_caption(self, value):
        self.obj.DataCaption = value

    @property
    def style(self):
        return self.obj
    @style.setter
    def style(self, values):
        _set_properties(self.obj, values)


class LOChartData(object):
    _type = 'Chart Data'

    def __init__(self, obj):
        self._obj = obj

    def __getitem__(self, index):
        return LOChartDataSerie(self.obj.getDataRowProperties(index))

    def __str__(self):
        return self._type

    @property
    def obj(self):
        return self._obj


class LOChart(object):
    _type = 'Chart'

    def __init__(self, obj, shape):
        self._obj = obj
        self._shape = shape
        self._chart = self._obj.EmbeddedObject
        self._diagram = self._chart.Diagram

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __str__(self):
        return f'{self._type}: {self.name}'

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self.obj.Name
    @name.setter
    def name(self, value):
        self.obj.Name = value

    @property
    def title(self):
        return self._chart.TitleObject
    @title.setter
    def title(self, values):
        if self.title is None:
            title = create_instance('com.sun.star.chart2.Title')
            fs = create_instance('com.sun.star.comp.chart.FormattedString')
            title.Text = (fs,)
            _set_properties(fs, values)
            self._chart.TitleObject = title
        else:
            string = values.pop('String', '')
            if string:
                self.title.Text[0].String = string
        _set_properties(self.title, values)

    @property
    def subtitle(self):
        return self._chart.SubTitle
    @subtitle.setter
    def subtitle(self, values):
        self._chart.HasSubTitle = True
        _set_properties(self.subtitle, values)

    @property
    def has_legend(self):
        return self._chart.HasLegend
    @has_legend.setter
    def has_legend(self, value):
        self._chart.HasLegend = value

    @property
    def area(self):
        return self._chart.Area
    @area.setter
    def area(self, values):
        _set_properties(self.area, values)

    @property
    def wall(self):
        return self._chart.Diagram.Wall
    @wall.setter
    def wall(self, values):
        _set_properties(self.wall, values)

    @property
    def axis(self):
        return LOChartAxis(self._chart.Diagram)

    @property
    def size(self):
        s = self._shape.size
        return s
    @size.setter
    def size(self, value):
        self._shape.size = value

    @property
    def width(self):
        """Width of shape"""
        s = self._shape.size
        return s.Width
    @width.setter
    def width(self, value):
        s = self.size
        s.Width = value
        self.size = s

    @property
    def height(self):
        """Height of shape"""
        s = self._shape.size
        return s.Height
    @height.setter
    def height(self, value):
        s = self.size
        s.Height = value
        self.size = s

    @property
    def position(self):
        return self._shape.position
    @property
    def x(self):
        """Position X"""
        return self.position.X
    @x.setter
    def x(self, value):
        self._shape.obj.Position = Point(value, self.y)
    @property
    def y(self):
        """Position Y"""
        return self.position.Y
    @y.setter
    def y(self, value):
        self._shape.obj.Position = Point(self.x, value)

    @property
    def dim_3d(self):
        return self._diagram.Dim3D
    @dim_3d.setter
    def dim_3d(self, value):
        self._diagram.Dim3D = value
    @property
    def is_3d(self):
        return self.dim_3d
    @is_3d.setter
    def is_3d(self, value):
        self.dim_3d = value

    @property
    def solid_type(self):
        return self._diagram.SolidType
    @solid_type.setter
    def solid_type(self, value):
        self._diagram.SolidType = value

    @property
    def rotate_angle(self):
        return self._shape.obj.RotateAngle
    @rotate_angle.setter
    def rotate_angle(self, value):
        self._shape.obj.RotateAngle = value

    @property
    def data(self):
        return LOChartData(self._chart.Diagram)

    def export(self, path, filters: dict={}):
        path = Paths(path)
        options = {'URL': path.url, 'MimeType': f'image/{path.ext}'}
        if filters:
            options.update(filters)
        options = dict_to_property(options)

        try:
            gef = create_instance('com.sun.star.drawing.GraphicExportFilter')
            gef.setSourceDocument(self._shape.obj)
            gef.filter(options)
            result = True
        except Exception as e:
            log.error(e)
            result = False

        return result


class LOCharts(object):
    INSTANCE = 'com.sun.star.chart.{}Diagram'
    _type = 'Charts'

    def __init__(self, obj, draw_page):
        self._obj = obj
        self._draw_page = draw_page

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
            chart = self.obj[self._index]
            shape = self._get_shape(chart)
            chart = LOChart(chart, shape)
        except IndexError:
            raise StopIteration

        self._index += 1
        return chart

    def __contains__(self, item):
        return item in self._obj

    def __getitem__(self, index):
        chart = self.obj[index]
        shape = self._get_shape(chart)
        return LOChart(chart, shape)

    def _get_shape(self, chart):
        shape = None
        for shape in self._draw_page:
            if chart.Name == shape.name:
                break
        return shape

    def __str__(self):
        return 'Charts'

    @property
    def obj(self):
        return self._obj

    def _get_range_address(self, data):
        range_address = (data.range_address,)
        return range_address

    def add(self, data, type_chart: str='', name: str='', pos_size: Union[Rectangle, tuple]=None,
        header_col: bool=True, header_row: bool=True):

        if not name:
            name = f'{type_chart}Chart_{self.obj.Count + 1}'
        if pos_size is None:
            pos_size = Rectangle(5000, 2500, 10000, 7500)
        elif isinstance(pos_size, tuple):
            pos_size = Rectangle(*pos_size)

        rangos = self._get_range_address(data)

        self.obj.addNewByName(name, pos_size, rangos, header_col, header_row)
        if type_chart:
            chart = self.obj[name].EmbeddedObject
            if type_chart == 'Bar':
                chart.Diagram.Vertical = True
            else:
                instance = self.INSTANCE.format(type_chart)
                chart.setDiagram(chart.createInstance(instance))

        chart = self.obj[name]
        shape = self._draw_page[-1]
        shape.name = name

        return LOChart(chart, shape)

    def new(self, data, type_chart: str='', name: str='', pos_size=None,
        header_col: bool=True, header_row: bool=True):
        return self.add(data, type_chart, name, pos_size, header_col, header_row)

    def remove(self, name):
        if isinstance(name, LOChart):
            name = name.name
        self.obj.removeByName(name)
        return
