#!/usr/bin/env python3

from typing import Any

from .constants import ControlCharacter, TextContentAnchorType
from .easymain import log, BaseObject, Paths
from .easydoc import LODocument
from .easydrawpage import LODrawPage
from .easystyles import LOStyleFamilies


SERVICES = {
    'TEXT_TABLE': 'com.sun.star.text.TextTable',
    'GRAPHIC': 'com.sun.star.text.GraphicObject',
}



class LOTableRange(BaseObject):

    def __init__(self, table, obj):
        self._table = table
        super().__init__(obj)

    def __str__(self):
        return f'TextTable: Range - {self.name}'

    @property
    def name(self):
        if self.is_cell:
            n = self.obj.CellName
        else:
            c1 = self.obj[0,0].CellName
            c2 = self.obj[self.rows-1,self.columns-1].CellName
            n = f'{c1}:{c2}'
        return n

    @property
    def is_cell(self):
        return hasattr(self.obj, 'CellName')

    @property
    def data(self):
        return self.obj.getDataArray()
    @data.setter
    def data(self, values):
        self.obj.setDataArray(values)

    @property
    def rows(self):
        return len(self.data)

    @property
    def columns(self):
        return len(self.data[0])

    @property
    def string(self):
        return self.obj.String
    @string.setter
    def string(self, value):
        self.obj.String = value

    @property
    def value(self):
        return self.obj.Value
    @value.setter
    def value(self, value):
        self.obj.Value = value


class LORow(BaseObject):

    def __init__(self, rows, index):
        self._rows = rows
        self._index = index
        super().__init__(rows[index])

    def __str__(self):
        return 'TextTable: Row'

    @property
    def height(self):
        return self.obj.Height
    @height.setter
    def height(self, value):
        self.obj.Height = value

    def remove(self):
        self._rows.removeByIndex(self._index, 1)
        return


class LORows(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return 'TextTable: Rows'

    def __len__(self):
        return self.obj.Count

    def __getitem__(self, key):
        return LORow(self.obj, key)

    @property
    def count(self):
        return self.obj.Count

    def remove(self, index, count=1):
        self.obj.removeByIndex(index, count)
        return


class LOTextTable(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'Writer: TextTable - {self.name}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        """Interation cells"""
        try:
            name = self.obj.CellNames[self._i]
        except IndexError:
            raise StopIteration
        self._i += 1
        return self[name]

    def __getitem__(self, key):
        if isinstance(key, str):
            if ':' in key:
                rango = self.obj.getCellRangeByName(key)
            else:
                rango = self.obj.getCellByName(key)
        elif isinstance(key, tuple):
            if isinstance(key[0], slice):
                rango = self.obj.getCellRangeByPosition(
                    key[1].start, key[0].start, key[1].stop-1, key[0].stop-1)
            else:
                rango = self.obj[key]
        return LOTableRange(self.obj, rango)

    @property
    def name(self):
        return self.obj.Name
    @name.setter
    def name(self, value):
        self.obj.Name = value

    @property
    def data(self):
        return self.obj.DataArray
    @data.setter
    def data(self, values):
        self.obj.DataArray = values

    @property
    def style(self):
        return self.obj.TableTemplateName
    @style.setter
    def style(self, value):
        self.obj.autoFormat(value)

    @property
    def rows(self):
        return LORows(self.obj.Rows)


class LOTextTables(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return 'Writer: TextTables'

    def __contains__(self, item):
        return item in self.obj

    def __getitem__(self, key):
        return LOTextTable(self.obj[key])



class LOWriterTextPortion(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return 'Writer: TextPortion'

    @property
    def string(self):
        return self.obj.String


class LOWriterParagraph(BaseObject):
    TEXT_PORTION = 'SwXTextPortion'

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return 'Writer: Paragraph'

    def __iter__(self):
        self._iter = iter(self.obj)
        return self

    def __next__(self):
        obj = next(self._iter)
        type_obj = obj.ImplementationName
        if type_obj == self.TEXT_PORTION:
            obj = LOWriterTextPortion(obj)
        return obj

    @property
    def string(self):
        return self.obj.String

    @property
    def cursor(self):
        return self.obj.Text.createTextCursorByRange(self.obj)


class LOWriterTextRange(BaseObject):
    PARAGRAPH = 'SwXParagraph'

    def __init__(self, obj, create_instance):
        super().__init__(obj)
        self._create_instance = create_instance

    def __str__(self):
        return 'Writer: TextRange'

    def __getitem__(self, index):
        for i, v in enumerate(self):
            if index == i:
                return v
        if index > i:
            raise IndexError

    def __iter__(self):
        self._enum = self.obj.createEnumeration()
        return self

    def __next__(self):
        if self._enum.hasMoreElements():
            obj = self._enum.nextElement()
            type_obj = obj.ImplementationName
            if type_obj == self.PARAGRAPH:
                obj = LOWriterParagraph(obj)
        else:
            raise StopIteration
        return obj

    @property
    def string(self):
        return self.obj.String
    @string.setter
    def string(self, value):
        self.obj.String = value

    @property
    def cursor(self):
        #  return self.obj.Text.createTextCursorByRange(self.obj)
        cursor = self.text.createTextCursorByRange(self.obj)
        return cursor

    @property
    def text(self):
        return self.obj.Text

    def insert_content(self, text_content, cursor=None, replace=False):
        if cursor is None:
            cursor = self.cursor
            cursor.gotoEnd(False)
        cursor.Text.insertTextContent(cursor, text_content, replace)
        return LOWriterTextRange(cursor, self._create_instance)

    def insert_table(self, rows, columns):
        table = self._create_instance(SERVICES['TEXT_TABLE'])
        table.initialize(rows, columns)
        self.insert_content(table)
        return LOTextTable(table)

    def new_line(self, count=1):
        cursor = self.cursor
        cursor.gotoEnd(False)
        for i in range(count):
            cursor.Text.insertControlCharacter(cursor, ControlCharacter.PARAGRAPH_BREAK, False)
        return LOWriterTextRange(cursor, self._create_instance)

    def insert_image(self, path, args={}):
        w = args.get('Width', 5000)
        h = args.get('Height', 5000)
        anchor_type = args.get('AnchorType', TextContentAnchorType.AS_CHARACTER)

        image = self._create_instance(SERVICES['GRAPHIC'])
        image.GraphicURL = Paths.to_url(path)
        image.AnchorType = anchor_type
        image.Width = w
        image.Height = h
        return self.insert_content(image)


class LOWriterTextRanges(BaseObject):

    def __init__(self, obj, create_instance):
        super().__init__(obj)
        self._create_instance = create_instance
        # ~ self._doc = doc
        # ~ self._paragraphs = [LOWriterTextRange(p, doc) for p in obj]

    def __str__(self):
        return 'Writer: TextRanges'

    def __len__(self):
        return self.obj.Count

    def __getitem__(self, index):
        return LOWriterTextRange(self.obj[index], self._create_instance)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        try:
            obj = LOWriterTextRange(self.obj[self._index], self._create_instance)
        except IndexError:
            raise StopIteration

        self._index += 1
        return obj


class LOWriterViewCursor(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def goto_start(self, expand=False):
        return self.obj.gotoStart(expand)

    def goto_end(self, expand=False):
        return self.obj.gotoEnd(expand)


class LOWriter(LODocument):
    TEXT_RANGES = 'SwXTextRanges'
    _type = 'writer'

    def __init__(self, obj):
        super().__init__(obj)
        self._view_settings = self._cc.ViewSettings
        self._create_instance = obj.createInstance

    def __str__(self):
        return f'Doc: {self._type} - {self.title}'

    @property
    def zoom(self):
        return self._view_settings.ZoomValue
    @zoom.setter
    def zoom(self, value):
        self._view_settings.ZoomValue = value

    @property
    def view_web(self):
        return self._view_settings.ShowOnlineLayout
    @view_web.setter
    def view_web(self, value):
        self._view_settings.ShowOnlineLayout = value

    @property
    def selection(self):
        """Get current seleccion"""
        sel = None
        selection = self.obj.CurrentSelection
        type_obj = selection.ImplementationName

        if type_obj == self.TEXT_RANGES:
            sel = LOWriterTextRanges(selection, self._create_instance)
            if len(sel) == 1:
                sel = sel[0]
        else:
            log.debug(type_obj)
            log.debug(selection)
            sel = selection

        return sel

    @property
    def string(self):
        return self._obj.Text.String
    @string.setter
    def string(self, value):
        self._obj.Text.String = value

    @property
    def styles(self):
        ci = self.obj.createInstance
        return LOStyleFamilies(self.obj.StyleFamilies, ci)

    @property
    def draw_page(self):
        """Get draw page"""
        return LODrawPage(self.obj.DrawPage)
    @property
    def dp(self):
        return self.draw_page
    @property
    def shapes(self):
        return self.draw_page

    @property
    def cursor(self):
        return self.obj.Text.createTextCursor()

    @property
    def vc(self):
        return self.view_cursor
    @property
    def view_cursor(self):
        return LOWriterViewCursor(self._cc.ViewCursor)

    @property
    def tables(self):
        return LOTextTables(self.obj.TextTables)

    @property
    def text(self):
        ci = self.obj.createInstance
        return LOWriterTextRange(self.obj.Text, ci)

    def select(self, rango: Any):
        """"""
        obj = rango
        if hasattr(rango, 'obj'):
            obj = rango.obj
        self._cc.select(obj)
        return

