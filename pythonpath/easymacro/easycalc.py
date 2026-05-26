#!/usr/bin/env python3

import datetime
from decimal import Decimal
from typing import Any, Union

from .easymain import (log,
    _DATE_OFFSET as DATE_OFFSET,
    BaseObject, Color, LOMain,
    dict_to_property, run_in_thread, set_properties
)
from .easychart import LOCharts, LOChart
from .easydoc import LODocument
from .easyevents import EventsRangeSelectionListener, LOEvents
from .easyshape import LOShapes, LOShape
from .easydrawpage import LODrawPage
from .easyshape import LOShape
from .easyforms import LOForms
from .easystyles import LOStyleFamilies
from .constants import ONLY_DATA, SECONDS_DAY, CellContentType, FillDirection, SearchType


gcolor = Color()


class LOSheetRows():

    def __init__(self, sheet, obj):
        self._sheet = sheet
        self._obj = obj

    def __getitem__(self, index):
        #  if isinstance(index, int):
            #  rows = LOSheetRows(self._sheet, self.obj[index])
        #  else:
            #  rango = self._sheet[index.start:index.stop,0:]
            #  rows = LOSheetRows(self._sheet, rango.obj.Rows)
        rows = LOSheetRows(self._sheet, self.obj[index])
        return rows

    def __len__(self):
        return self.obj.Count

    def __str__(self):
        rows = self.obj.AbsoluteName.split('$')
        name = f'Rows: {rows[3]}{rows[5]}'
        return name

    @property
    def obj(self):
        return self._obj

    @property
    def visible(self):
        return self._obj.IsVisible
    @visible.setter
    def visible(self, value):
        self._obj.IsVisible = value

    @property
    def is_filtered(self):
        return self._obj.IsFiltered
    @is_filtered.setter
    def is_filtered(self, value):
        self._obj.IsFiltered = value

    @property
    def is_manual_page_break(self):
        return self._obj.IsManualPageBreak
    @is_manual_page_break.setter
    def is_manual_page_break(self, value):
        self._obj.IsManualPageBreak = value

    @property
    def is_start_of_new_page(self):
        return self._obj.IsStartOfNewPage
    @is_start_of_new_page.setter
    def is_start_of_new_page(self, value):
        self._obj.IsStartOfNewPage = value

    @property
    def color(self):
        return self.obj.CellBackColor
    @color.setter
    def color(self, value):
        self.obj.CellBackColor = gcolor(value)

    @property
    def is_transparent(self):
        return self.obj.IsCellBackgroundTransparent
    @is_transparent.setter
    def is_transparent(self, value):
        self.obj.IsCellBackgroundTransparent = value

    @property
    def height(self):
        return self.obj.Height
    @height.setter
    def height(self, value):
        self.obj.Height = value

    def optimal(self):
        self.obj.OptimalHeight = True
        return

    def insert(self, index, count):
        self.obj.insertByIndex(index, count)
        return

    def remove(self, index, count):
        self.obj.removeByIndex(index, count)
        return


class LOCalcRanges(object):

    def __init__(self, obj):
        self._obj = obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __len__(self):
        return self._obj.Count

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        try:
            r = self.obj[self._index]
            rango = LOCalcRange(r)
        except IndexError:
            raise StopIteration

        self._index += 1
        return rango

    def __contains__(self, item):
        return self._obj.hasByName(item.name)

    def __getitem__(self, index):
        r = self.obj[index]
        rango = LOCalcRange(r)
        return rango

    def __str__(self):
        s = f'Ranges: {self.names}'
        return s

    @property
    def obj(self):
        return self._obj

    @property
    def names(self):
        return self.obj.ElementNames

    @property
    def data(self):
        rows = [r.data for r in self]
        return rows
    @data.setter
    def data(self, values):
        for i, data in enumerate(values):
            self[i].data = data

    @property
    def style(self):
        return self.obj.CellStyle
    @style.setter
    def style(self, value):
        self.obj.CellStyle = value

    def add(self, rangos: Any, merge: bool=False):
        if isinstance(rangos, LOCalcRange):
            rangos = (rangos,)
        for r in rangos:
            self.obj.addRangeAddress(r.range_address, merge)
        return

    def remove(self, rangos: Any):
        if isinstance(rangos, LOCalcRange):
            rangos = (rangos,)
        for r in rangos:
            self.obj.removeRangeAddress(r.range_address)
        return

    def clear(self, what: int=ONLY_DATA):
        """Clear contents"""
        self.obj.clearContents(what)
        return

    def copy(self, target):
        for rango in self:
            rango.copy(target)
            target = target.next_free
        return


class LOCalcRange():
    CELL = 'ScCellObj'

    def __init__(self, obj):
        self._obj = obj
        self._is_cell = obj.ImplementationName == self.CELL

    def __contains__(self, rango):
        if isinstance(rango, LOCalcRange):
            address = rango.range_address
        else:
            address = rango.RangeAddress
        result = self.cursor.queryIntersection(address)
        return bool(result.Count)

    def __getitem__(self, index):
        return LOCalcRange(self.obj[index])

    def __iter__(self):
        self._r = 0
        self._c = 0
        return self

    def __next__(self):
        try:
            rango = self[self._r, self._c]
        except Exception as e:
            raise StopIteration
        self._c += 1
        if self._c == self.obj.Columns.Count:
            self._c = 0
            self._r +=1
        return rango

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __len__(self):
        return self.obj.Rows.Count

    def __str__(self):
        s = f'Range: {self.name_absolute}'
        if self.is_cell:
            s = f'Cell: {self.name_absolute}'
        return s

    @property
    def obj(self):
        """Get original object pyUNO"""
        return self._obj

    @property
    def len_rows(self):
        """Get len rows"""
        ra = self.range_address
        rows = ra.EndRow - ra.StartRow + 1
        return rows

    @property
    def len_columns(self):
        """Get len columns"""
        ra = self.range_address
        cols = ra.EndColumn - ra.StartColumn + 1
        return cols

    @property
    def is_cell(self):
        """True if range is cell"""
        return self._is_cell

    @property
    def is_empty(self):
        """True if cell is empty"""
        return self.type == CellContentType.EMPTY

    @property
    def is_merged(self):
        """True if cell is merged"""
        return self.obj.IsMerged

    @property
    def is_range(self):
        """True if range is not cell"""
        return not self._is_cell

    @property
    def name(self):
        """Alias of name_absolute"""
        return self.name_absolute
    @property
    def name_absolute(self):
        """Return the range address like string"""
        return self.obj.AbsoluteName

    @property
    def name_relative(self):
        """Return the range address like string"""
        return self.name.replace('$', '')

    @property
    def address(self):
        """Return CellAddress or CellRangeAddress"""
        if self.is_cell:
            a = self.obj.CellAddress
        else:
            a = self.obj.RangeAddress
        return a

    @property
    def cell_address(self):
        """Return com.sun.star.table.CellAddress"""
        return self.obj.CellAddress

    @property
    def range_address(self):
        """Return com.sun.star.table.CellRangeAddress"""
        return self.obj.RangeAddress

    @property
    def sheet(self):
        """Return sheet parent"""
        return LOCalcSheet(self.obj.Spreadsheet)

    @property
    def doc(self):
        """Return doc parent"""
        doc = self.obj.Spreadsheet.DrawPage.Forms.Parent
        return LOCalc(doc)

    @property
    def empty_cells(self):
        """Get empty cells"""
        ranges = self.obj.queryEmptyCells()
        return LOCalcRanges(ranges)

    @property
    def content_cells(self):
        """Get cells with content: values, datetime, string, annotation and formulas"""
        ranges = self.obj.queryContentCells(31)
        return LOCalcRanges(ranges)

    @property
    def style(self):
        """Get or set cell style"""
        return self.obj.CellStyle
    @style.setter
    def style(self, value):
        self.obj.CellStyle = value

    @property
    def current_region(self):
        """Return current region"""
        cursor = self.cursor
        cursor.collapseToCurrentRegion()
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    @property
    def current_array(self):
        """Return current array, for matrix formulas"""
        cursor = self.cursor
        cursor.collapseToCurrentArray()
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    @property
    def merged_area(self):
        """Return merged area, for combined cells"""
        cursor = self.cursor
        cursor.collapseToMergedArea()
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    @property
    def entire_columns(self):
        """Get entire columns"""
        cursor = self.cursor
        cursor.expandToEntireColumns()
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    @property
    def entire_rows(self):
        """Get entire rows"""
        cursor = self.cursor
        cursor.expandToEntireRows()
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    @property
    def back_color(self):
        """Get or set cell back color"""
        return self._obj.CellBackColor
    @back_color.setter
    def back_color(self, value):
        self._obj.CellBackColor = gcolor(value)

    @property
    def type(self):
        """Get type of content.
        See https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1table.html#affea688ab9e00781fa35d8a790d10f0e
        """
        return self.obj.Type

    @property
    def error(self):
        """Get number error in formulas"""
        return self.obj.getError()

    @property
    def string(self):
        """Get or set content like string"""
        return self.obj.String
    @string.setter
    def string(self, value):
        self.obj.setString(value)

    @property
    def float(self):
        """Get or set content like value"""
        return self.obj.Value
    @float.setter
    def float(self, value):
        self.obj.setValue(value)

    @property
    def formula(self):
        """Get or set formula"""
        return self.obj.Formula
    @formula.setter
    def formula(self, value):
        self.obj.setFormula(value)

    @property
    def date(self):
        """Get or set date"""
        value = int(self.obj.Value)
        date = datetime.date.fromordinal(value + DATE_OFFSET)
        return date
    @date.setter
    def date(self, value):
        d = value.toordinal()
        self.float = d - DATE_OFFSET

    @property
    def time(self):
        """Get or set time"""
        seconds = self.obj.Value * SECONDS_DAY
        time_delta = datetime.timedelta(seconds=seconds)
        time = (datetime.datetime.min + time_delta).time()
        return time
    @time.setter
    def time(self, value):
        d = (value.hour * 3600 + value.minute * 60 + value.second) / SECONDS_DAY
        self.float = d

    @property
    def datetime(self):
        """Get or set datetime"""
        return datetime.datetime.combine(self.date, self.time)
    @datetime.setter
    def datetime(self, value):
        d = value.toordinal()
        t = (value - datetime.datetime.fromordinal(d)).seconds / SECONDS_DAY
        self.float = d - DATE_OFFSET + t

    @property
    def value(self):
        """Get or set value, automatically get type data"""
        v = None
        if self.type == CellContentType.VALUE:
            v = self.float
        elif self.type == CellContentType.TEXT:
            v = self.string
        elif self.type == CellContentType.FORMULA:
            v = self.formula
        return v
    @value.setter
    def value(self, value):
        if isinstance(value, str):
            if value[0] in '=':
                self.formula = value
            else:
                self.string = value
        elif isinstance(value, Decimal):
            self.float  = float(value)
        elif isinstance(value, (int, float, bool)):
            self.float = value
        elif isinstance(value, datetime.datetime):
            self.datetime = value
        elif isinstance(value, datetime.date):
            self.date = value
        elif isinstance(value, datetime.time):
            self.time = value

    @property
    def data_array(self):
        """Get or set DataArray"""
        return self.obj.DataArray
    @data_array.setter
    def data_array(self, data):
        self.obj.DataArray = data

    @property
    def formula_array(self):
        """Get or set FormulaArray"""
        return self.obj.FormulaArray
    @formula_array.setter
    def formula_array(self, data):
        self.obj.FormulaArray = data

    @property
    def data(self):
        """Get like data_array, for set, if range is cell, automatically ajust size range.
        """
        return self.data_array
    @data.setter
    def data(self, values):
        if self.is_cell:
            cols = len(values[0])
            rows = len(values)
            if cols == 1 and rows == 1:
                self.data_array = values
            else:
                self.to_size(cols, rows).data = values
        else:
            self.data_array = values

    @property
    def dict(self):
        """Get or set data from to dict"""
        rows = self.data
        k = rows[0]
        data = [dict(zip(k, r)) for r in rows[1:]]
        return data
    @dict.setter
    def dict(self, values):
        data = [tuple(values[0].keys())]
        data += [tuple(d.values()) for d in values]
        self.data = data

    @property
    def next_free(self):
        """Get next free cell"""
        ra = self.current_region.range_address
        col = ra.StartColumn
        row = ra.EndRow + 1
        return LOCalcRange(self.sheet[row, col].obj)

    @property
    def range_data(self):
        """Get range without headers"""
        rango = self.current_region
        ra = rango.range_address
        row1 = ra.StartRow + 1
        row2 = ra.EndRow + 1
        col1 = ra.StartColumn
        col2 = ra.EndColumn + 1
        return LOCalcRange(self.sheet[row1:row2, col1:col2].obj)

    @property
    def shape(self):
        """Get or set shape anchor"""
        shape = None
        for shape in self.sheet.dp:
            if shape.cell.name == self.name:
                break
        return shape
    @shape.setter
    def shape(self, shape):
        shape.anchor = self
        shape.resize_with_cell = True
        shape.possize = self.possize
        return

    @property
    def array_formula(self):
        """Get or set matrix formula"""
        return self.obj.ArrayFormula
    @array_formula.setter
    def array_formula(self, value):
        self.obj.ArrayFormula = value

    @property
    def cursor(self):
        """Get cursor by self range"""
        cursor = self.obj.Spreadsheet.createCursorByRange(self.obj)
        return cursor

    @property
    def position(self):
        """Get position X-Y"""
        return self.obj.Position

    @property
    def size(self):
        """Get size"""
        return self.obj.Size

    @property
    def height(self):
        """Get height"""
        return self.obj.Size.Height

    @property
    def width(self):
        """Get width"""
        return self.obj.Size.Width

    @property
    def x(self):
        """Get position X"""
        return self.obj.Position.X

    @property
    def y(self):
        """Get position Y"""
        return self.obj.Position.Y

    @property
    def possize(self):
        """Get position and size"""
        data = {
            'Width': self.width,
            'Height': self.height,
            'X': self.x,
            'Y': self.y,
        }
        return data

    @property
    def rows(self):
        """GEt rows"""
        return LOSheetRows(self.sheet, self.obj.Rows)

    @property
    def row(self):
        """Get row in current region"""
        r1 = self.address.Row
        r2 = r1 + 1
        ra = self.current_region.range_address
        c1 = ra.StartColumn
        c2 = ra.EndColumn + 1
        return LOCalcRange(self.sheet[r1:r2, c1:c2].obj)

    @property
    def end_used_area(self):
        """Get used area"""
        cursor = self.cursor
        cursor.gotoEndOfUsedArea(True)
        return LOCalcRange(self.sheet[cursor.AbsoluteName].obj)

    @property
    def start_used_area(self):
        """Get used area"""
        cursor = self.cursor
        cursor.gotoStartOfUsedArea(True)
        return LOCalcRange(self.sheet[cursor.AbsoluteName].obj)

    @property
    def visible_cells(self):
        """Get visible cells"""
        ranges = self.obj.queryVisibleCells()
        return LOCalcRanges(ranges)

    @property
    def validation(self):
        """Get or set validation cell"""
        return self.obj.Validation
    @validation.setter
    def validation(self, value):
        if isinstance(value, dict):
            values = self.validation
            for k, v in value.items():
                setattr(values, k, v)
        else:
            values = value
        self.obj.Validation = values

    @property
    def conditional_format(self):
        """Get or set conditional format"""
        return self.obj.ConditionalFormat
    @conditional_format.setter
    def conditional_format(self, value):
        if isinstance(value, dict):
            value = (value,)
        cf = self.conditional_format
        cf.clear()
        for v in value:
            condition = dict_to_property(v)
            cf.addNew(condition)
        self.obj.ConditionalFormat = cf

    @property
    def annotation(self):
        note = None
        if self.obj.Annotation.AnnotationShape:
            note = LOCalcSheetAnnotation(self.obj.Annotation)
        return note
    @property
    def note(self):
        return self.annotation

    def clear(self, what: int=ONLY_DATA):
        """Clear contents"""
        # ~ http://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1sheet_1_1CellFlags.html
        self.obj.clearContents(what)
        return

    def offset(self, rows: int=0, cols: int=1):
        """Get cell offset"""
        ra = self.range_address
        col = ra.EndColumn + cols
        row = ra.EndRow + rows
        return LOCalcRange(self.sheet[row, col].obj)

    def to_size(self, cols: int, rows: int):
        """Expande range to size"""
        cursor = self.cursor
        cursor.collapseToSize(cols, rows)
        rango = self.obj.Spreadsheet[cursor.AbsoluteName]
        return LOCalcRange(rango)

    def len(self):
        """Get size of range in rows and columns"""
        ra = self.range_address
        rows = ra.EndRow - ra.StartRow + 1
        cols = ra.EndColumn - ra.StartColumn + 1
        return rows, cols

    def select(self):
        """Self select"""
        self.doc.select(self.obj)
        return

    def to_image(self):
        """Self to image"""
        self.select()
        self.doc.copy()
        args = {'SelectedFormat': 141}
        url = 'ClipboardFormatItems'
        LOMain.dispatch(self.doc, url, args)
        return self.sheet.shapes[-1]

    def query_content_cells(self, value):
        """Get query content cells"""
        ranges = self.obj.queryContentCells(value)
        return LOCalcRanges(ranges)

    def query_formula_cells(self, value):
        """Return cells according to the type of result of the formula."""
        ranges = self.obj.queryFormulaCells(value)
        return LOCalcRanges(ranges)

    def column_differences(self, cell):
        """Return the different cells by column"""
        ranges = self.obj.queryColumnDifferences(cell.address)
        return LOCalcRanges(ranges)

    def row_differences(self, cell):
        """Return the different cells by row"""
        ranges = self.obj.queryRowDifferences(cell.address)
        return LOCalcRanges(ranges)

    def intersection(self, rango):
        """Return intersection range"""
        rango = self.obj.queryIntersection(rango.address)
        return LOCalcRange(rango)

    def copy(self, target):
        self.obj.Spreadsheet.copyRange(target.cell_address, self.range_address)
        return

    def move(self, target):
        self.obj.Spreadsheet.moveRange(target.cell_address, self.range_address)
        return

    def insert(self, mode):
        self.obj.Spreadsheet.insertCells(self.range_address, mode)
        return

    def remove(self, mode):
        self.obj.Spreadsheet.removeRange(self.range_address, mode)
        return

    def delete(self, mode):
        self.remove(mode)
        return

    def fill_auto(self, count_cells: int=1, fill_direction=FillDirection.TO_BOTTOM):
        self.obj.fillAuto(fill_direction, count_cells)
        return

    def find_all(self, searching: str, options: dict={}):
        #  SearchBackwards
        #  SearchByRow
        #  SearchSimilarity
        #  SearchSimilarityAdd
        #  SearchSimilarityExchange
        #  SearchSimilarityRelax
        #  SearchSimilarityRemove
        #  SearchStyles
        #  SearchWildcard
        #  WildcardEscapeCharacter
        default = {
            'SearchType': SearchType.VALUE,
            'SearchWords': False,
            'SearchCaseSensitive': False,
            'SearchRegularExpression': False,
        }

        for k, v in default.items():
            options.setdefault(k, v)

        descriptor = self.obj.Spreadsheet.createSearchDescriptor()
        descriptor.SearchString = searching
        for k, v in options.items():
            setattr(descriptor, k, v)

        results = self.obj.findAll(descriptor)
        if results:
            results = LOCalcRanges(results)
        return results

    def replace_all(self, searching: str, replace: str, options: dict={}):
        default = {
            'SearchType': SearchType.VALUE,
            'SearchWords': False,
            'SearchCaseSensitive': False,
            'SearchRegularExpression': False,
        }

        for k, v in default.items():
            options.setdefault(k, v)

        descriptor = self.obj.Spreadsheet.createReplaceDescriptor()
        descriptor.SearchString = searching
        descriptor.ReplaceString = replace
        for k, v in options.items():
            setattr(descriptor, k, v)

        counts = self.obj.replaceAll(descriptor)

        return counts


class LOPane():

    def __init__(self, obj):
        self._obj = obj

    def __str__(self):
        return 'Pane'

    @property
    def obj(self):
        return self._obj

    @property
    def visible_range(self):
        return self.obj.VisibleRange

    @property
    def first_visible_column(self):
        return self.obj.FirstVisibleColumn

    @property
    def first_visible_row(self):
        return self.obj.FirstVisibleRow

    @property
    def referred_cells(self):
        return LOCalcRange(self.obj.ReferredCells)


class LOViewPane():

    def __init__(self, obj):
        self._obj = obj

    def __getitem__(self, index):
        return LOPane(self.obj[index])

    @property
    def obj(self):
        return self._obj

    @property
    def count(self):
        return self.obj.Count

    @property
    def active(self):
        view_data = self.obj.ViewData.split(';')
        sheet = int(view_data[1]) + 3

        sep = '/'
        if '+' in view_data[sheet]:
            sep = '+'
        info = view_data[sheet].split(sep)

        return int(info[6])

    def activate(self, index):
        view_data = self.obj.ViewData.split(';')
        sheet = int(view_data[1]) + 3
        pane = self[index]

        if self.count == 1 and index == 0:
            new_pos = 2
        elif self.count == 2:
            if self.obj.SplitRow and index == 0:
                new_pos = 0
            elif self.obj.SplitRow and index == 1:
                new_pos = 2
            elif self.obj.SplitColumn and index == 0:
                new_pos = 2
            elif self.obj.SplitColumn and index == 1:
                new_pos = 3
        elif self.count == 4:
            new_pos = {0: 0, 1: 2, 2: 1, 3: 3}[index]

        sep = '/'
        if '+' in view_data[sheet]:
            sep = '+'

        info = view_data[sheet].split(sep)
        info[0] = str(pane.first_visible_column)
        info[1] = str(pane.first_visible_row)
        info[6] = str(new_pos)
        view_data[sheet] = sep.join(info)

        self.obj.restoreViewData(';'.join(view_data))
        return


class LOCalcSheetAnnotation(BaseObject):
    #  Text
    #  Start
    #  End

    def __init__(self, obj):
        super().__init__(obj)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @property
    def string(self):
        return self.obj.String
    @string.setter
    def string(self, value):
        self.obj.String = value

    @property
    def visible(self):
        return self.obj.IsVisible
    @visible.setter
    def visible(self, value):
        self.obj.IsVisible = value

    @property
    def parent(self):
        return LOCalcRange(self.obj.Parent)

    @property
    def cell(self):
        return self.parent

    @property
    def annotation_shape(self):
        return self.shape

    @property
    def shape(self):
        return LOShape(self.obj.AnnotationShape)

    @property
    def author(self):
        return self.obj.Author

    @property
    def date(self):
        #  template = '09/04/2024 22:05'
        template = '%m/%d/%Y %H:%M'
        dt = datetime.datetime.strptime(self.obj.Date, template)
        return dt

    def remove(self):
        notes = self.cell.sheet.obj.Annotations
        for i, note in enumerate(notes):
            if note.Position == self.cell.address:
                index = i
                break
        notes.removeByIndex(index)
        return

    def delete(self):
        self.remove()
        return


class LOCalcSheetAnnotations(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __len__(self):
        return self.obj.Count

    def __getitem__(self, index):
        return LOCalcSheetAnnotation(self.obj[index])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @property
    def count(self):
        return self.__len__()

    def insert_new(self, cell, value):
        self.obj.insertNew(cell.address, value)
        index = self.count-1
        return LOCalcSheetAnnotation(self.obj[index])

    def insert(self, cell, value):
        return self.insert_new(cell, value)

    def new(self, cell, value):
        return self.insert_new(cell, value)

    def remove(self, index):
        if not isinstance(index, int):
            for i, note in enumerate(self.obj):
                if note.Position == index.address:
                    index = i
                    break
        self.obj.removeByIndex(index)
        return

    def delete(self, index):
        self.remove(index)
        return


class LOCalcSheet(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        return LOCalcRange(self.obj[index])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __contains__(self, item):
        return item in self

    def __str__(self):
        return f'Sheet: {self.name}'

    @property
    def doc(self):
        """Get parent doc"""
        return LOCalc(self.obj.DrawPage.Forms.Parent)

    @property
    def name(self):
        """Get name sheet"""
        return self._obj.Name
    @name.setter
    def name(self, value):
        self._obj.Name = value

    @property
    def code_name(self):
        """Get code name"""
        return self._obj.CodeName
    @code_name.setter
    def code_name(self, value):
        self._obj.CodeName = value

    @property
    def visible(self):
        """Get visible"""
        return self._obj.IsVisible
    @visible.setter
    def visible(self, value):
        self._obj.IsVisible = value

    @property
    def color(self):
        """Get color tab"""
        return self._obj.TabColor
    @color.setter
    def color(self, value):
        self._obj.TabColor = gcolor(value)

    @property
    def used_area(self):
        """Get used area"""
        cursor = self.create_cursor()
        cursor.gotoStartOfUsedArea(False)
        cursor.gotoEndOfUsedArea(True)
        return self[cursor.AbsoluteName]

    @property
    def is_protected(self):
        """Get is protected"""
        return self._obj.isProtected()

    @property
    def password(self):
        return ''
    @password.setter
    def password(self, value):
        """Set password protect"""
        self.obj.protect(value)

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
    def forms(self):
        return LOForms(self.obj.DrawPage)

    @property
    def events(self):
        """Get events"""
        return LOEvents(self.obj.Events)

    @property
    def height(self):
        return self.obj.Size.Height

    @property
    def width(self):
        return self.obj.Size.Width

    @property
    def split_column(self):
        return self.doc._cc.SplitColumn

    @property
    def split_row(self):
        return self.doc._cc.SplitRow

    @property
    def view_pane(self):
        return LOViewPane(self.obj.DrawPage.Forms.Parent.CurrentController)

    @property
    def charts(self):
        return LOCharts(self.obj.Charts, self.draw_page)

    @property
    def index(self):
        return self.obj.RangeAddress.Sheet

    @property
    def annotations(self):
        return LOCalcSheetAnnotations(self.obj.Annotations)

    @property
    def notes(self):
        return self.annotations

    @property
    def active(self):
        vd = self.doc._cc.ViewData.split(';')
        data = vd[3:][self.index].split('/')
        return self[int(data[1]), int(data[0])]

    def protect(self, value):
        self.obj.protect(value)
        return

    def unprotect(self, value):
        """Unprotect sheet"""
        try:
            self.obj.unprotect(value)
            return True
        except:
            pass
        return False

    def move(self, pos: int=-1):
        """Move sheet"""
        index = pos
        if pos < 0:
            index = len(self.doc)
        self.doc.move(self.name, index)
        return

    def remove(self):
        """Auto remove"""
        self.doc.remove(self.name)
        return

    def copy(self, new_name: str='', pos: int=-1):
        """Copy sheet"""
        index = pos
        if pos < 0:
            index = len(self.doc)
        new_sheet = self.doc.copy_sheet(self.name, new_name, index)
        return new_sheet

    def copy_to(self, doc: Any, target: str='', pos: int=-1):
        """Copy sheet to other document."""
        index = pos
        if pos < 0:
            index = len(doc)

        new_name = target or self.name
        sheet = doc.copy_from(self.doc, self.name, new_name, index)
        return sheet

    def activate(self):
        """Activate sheet"""
        self.doc.activate(self.obj)
        return

    def create_cursor(self, rango: Any=None):
        if rango is None:
            cursor = self.obj.createCursor()
        else:
            obj = rango
            if hasattr(rango, 'obj'):
                obj = rango.obj
            cursor = self.obj.createCursorByRange(obj)
        return cursor


class LOCalcSheetsCodeName(BaseObject):
    """Access by code name sheet"""

    def __init__(self, obj):
        super().__init__(obj)
        self._sheets = obj.Sheets

    def __getitem__(self, index):
        """Index access"""
        for sheet in self._sheets:
            if sheet.CodeName == index:
                return LOCalcSheet(sheet)
        raise IndexError

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        """Interation sheets"""
        try:
            sheet = LOCalcSheet(self._sheets[self._i])
        except Exception as e:
            raise StopIteration
        self._i += 1
        return sheet

    def __contains__(self, item):
        """Contains"""
        for sheet in self._sheets:
            if sheet.CodeName == item:
                return True
        return False


class LOCalc(LODocument):
    """Classe for Calc module"""
    TYPE_RANGES = ('ScCellObj', 'ScCellRangeObj')
    RANGES = 'ScCellRangesObj'
    SHAPE = 'com.sun.star.drawing.SvxShapeCollection'
    _type = 'calc'

    def __init__(self, obj):
        super().__init__(obj)
        self._sheets = obj.Sheets
        self._listener_range_selection = None

    def __getitem__(self, index):
        """Index access"""
        return LOCalcSheet(self._sheets[index])

    def __setitem__(self, key: str, value: Any):
        """Insert new sheet"""
        self._sheets[key] = value

    def __delitem__(self, key):
        sheet = self._sheets[key]
        self._sheets.removeByName(sheet.Name)

    def __len__(self):
        """Count sheets"""
        return self._sheets.Count

    def __contains__(self, item):
        """Contains"""
        if not isinstance(item, str):
            item = item.name
        return item in self._sheets

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        """Interation sheets"""
        try:
            sheet = LOCalcSheet(self._sheets[self._i])
        except Exception as e:
            raise StopIteration
        self._i += 1
        return sheet

    def __str__(self):
        return f'Calc: {self.title}'

    @property
    def sheets(self):
        """Access by code name sheet"""
        return LOCalcSheetsCodeName(self.obj)

    @property
    def headers(self):
        """Get true if is visible columns/rows headers"""
        return self._cc.ColumnRowHeaders
    @headers.setter
    def headers(self, value):
        """Set visible columns/rows headers"""
        self._cc.ColumnRowHeaders = value

    @property
    def tabs(self):
        """Get true if is visible tab sheets"""
        return self._cc.SheetTabs
    @tabs.setter
    def tabs(self, value):
        """Set visible tab sheets"""
        self._cc.SheetTabs = value

    @property
    def selection(self):
        """Get current seleccion"""
        sel = None
        selection = self.obj.CurrentSelection
        type_obj = selection.ImplementationName

        if type_obj in self.TYPE_RANGES:
            sel = LOCalcRange(selection)
        elif type_obj == self.RANGES:
            sel = LOCalcRanges(selection)
        elif type_obj == self.SHAPE:
            if len(selection) == 1:
                sel = LOShape(selection[0])
                if selection[0].supportsService('com.sun.star.drawing.OLE2Shape'):
                    chart = self.active.obj.Charts[sel.name]
                    sel = LOChart(chart, sel)
            else:
                sel = LOShapes(selection)
        else:
            log.debug(type_obj)
        return sel

    @property
    def active(self):
        """Get active sheet"""
        return LOCalcSheet(self._cc.ActiveSheet)

    @property
    def names(self):
        """Get all sheet names"""
        names = self.obj.Sheets.ElementNames
        return names

    @property
    def events(self):
        """Get class events"""
        return LOEvents(self.obj.Events)

    @property
    def styles(self):
        ci = self.obj.createInstance
        return LOStyleFamilies(self.obj.StyleFamilies, ci)

    def ranges(self):
        """Create ranges container"""
        obj = self._create_instance('com.sun.star.sheet.SheetCellRanges')
        return LOCalcRanges(obj)

    def new_sheet(self):
        """Create new instance sheet"""
        s = self._create_instance('com.sun.star.sheet.Spreadsheet')
        return s

    def select(self, rango: Any):
        """Select range"""
        obj = rango
        if hasattr(rango, 'obj'):
            obj = rango.obj
        self._cc.select(obj)
        return

    def start_range_selection(self, controllers: Any, args: dict={}):
        """Start select range selection by user

        `See Api RangeSelectionArguments <https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1sheet_1_1RangeSelectionArguments.html>`_
        """
        if args:
            args['CloseOnMouseRelease'] = args.get('CloseOnMouseRelease', True)
        else:
            args = dict(
                Title = 'Please select a range',
                CloseOnMouseRelease = True)
        properties = dict_to_property(args)

        self._listener_range_selection = EventsRangeSelectionListener(controllers(self))
        self._cc.addRangeSelectionListener(self._listener_range_selection)
        self._cc.startRangeSelection(properties)
        return

    def remove_range_selection_listener(self):
        """Remove range listener"""
        if not self._listener_range_selection is None:
            self._cc.removeRangeSelectionListener(self._listener_range_selection)
        return

    def activate(self, sheet: Union[str, LOCalcSheet]):
        """Activate sheet

        :param sheet: Sheet to activate
        :type sheet: str, pyUno or LOCalcSheet
        """
        obj = sheet
        if isinstance(sheet, LOCalcSheet):
            obj = sheet.obj
        elif isinstance(sheet, str):
            obj = self._sheets[sheet]
        self._cc.setActiveSheet(obj)
        return

    def insert(self, name: Union[str, list, tuple]):
        """Insert new sheet

        :param name: Name new sheet, or iterable with names.
        :type name: str, list or tuple
        :return: New last instance sheet.
        :rtype: LOCalcSheet
        """
        names = name
        if isinstance(name, str):
            names = (name,)
        for n in names:
            self._sheets[n] = self._create_instance('com.sun.star.sheet.Spreadsheet')
        return LOCalcSheet(self._sheets[n])

    def move(self, sheet: Union[str, LOCalcSheet], pos: int=-1):
        """Move sheet name to position

        :param sheet: Instance or Name sheet to move
        :type sheet: LOCalcSheet or str
        :param pos: New position, if pos=-1 move to end
        :type pos: int
        """
        name = sheet
        index = pos
        if pos < 0:
            index = len(self)
        if isinstance(sheet, LOCalcSheet):
            name = sheet.name
        self._sheets.moveByName(name, index)
        return

    def remove(self, sheet: Union[int, str, LOCalcSheet]):
        """Remove sheet by index or name

        :param sheet: Instance or Name sheet to move
        :type sheet: LOCalcSheet or str
        """
        name = sheet
        if isinstance(sheet, LOCalcSheet):
            name = sheet.name
        elif isinstance(sheet, int):
            name = self._sheets[sheet].Name
        self._sheets.removeByName(name)
        return

    def _get_new_name_sheet(self, name):
        i = 1
        new_name = f'{name}_{i}'
        while new_name in self:
            i += 1
            new_name = f'{name}_{i}'
        return new_name

    def copy_sheet(self, sheet: Union[str, LOCalcSheet], new_name: str='', pos: int=-1):
        """Copy sheet
        """
        name = sheet
        if isinstance(sheet, LOCalcSheet):
            name = sheet.name
        index = pos
        if pos < 0:
            index = len(self)
        if not new_name:
            new_name = self._get_new_name_sheet(name)
        self._sheets.copyByName(name, new_name, index)
        return LOCalcSheet(self._sheets[new_name])

    def copy_from(self, doc: Any, source: Any=None, target: Any=None, pos: int=-1):
        """Copy sheet from document
        """
        index = pos
        if pos < 0:
            index = len(self)

        names = source
        if not source:
            names = doc.names
        elif isinstance(source, str):
            names = (source,)
        elif isinstance(source, LOCalcSheet):
            names = (source.name,)

        new_names = target
        if not target:
            new_names = names
        elif isinstance(target, str):
            new_names = (target,)

        for i, name in enumerate(names):
            self._sheets.importSheet(doc.obj, name, index + i)
            self[index + i].name = new_names[i]

        return LOCalcSheet(self._sheets[index])

    def sort(self, reverse=False):
        """Sort sheets by name

        :param reverse: For order in reverse
        :type reverse: bool
        """
        names = sorted(self.names, reverse=reverse)
        for i, n in enumerate(names):
            self.move(n, i)
        return

    def get_ranges(self, address: str):
        """Get the same range address in each sheet.
        """
        ranges = self.ranges()
        ranges.add([sheet[address] for sheet in self])
        return ranges

    @property
    def cs(self):
        return self.cell_styles
    @property
    def cell_styles(self):
        return self.styles['CellStyles']

    @property
    def named_ranges(self):
        return self.obj.NamedRanges


