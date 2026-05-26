#!/usr/bin/env python

from enum import IntEnum
from com.sun.star.awt import Rectangle, Size
from com.sun.star.awt import WindowDescriptor
from com.sun.star.awt.PosSize import POSSIZE, POS
from com.sun.star.awt import ScrollBarOrientation
from com.sun.star.awt import VclWindowPeerAttribute
from com.sun.star.chart import ChartDataCaption, ChartSolidType
from com.sun.star.sheet import CellFlags, FormulaResult
from com.sun.star.sheet import ConditionOperator2 as ConditionOperator
from com.sun.star.text import ControlCharacter
from com.sun.star.util.MeasureUnit import APPFONT

from .easyuno import (
    AnimationEffect,
    AnimationSpeed,
    BitmapMode,
    CellContentType,
    CellDeleteMode,
    FillStyle,
    LineStyle,
    TextContentAnchorType,
    ValidationAlertStyle,
    ValidationType,
    WindowAttribute,
    WindowClass,
    )


__all__ = [
    'ALL',
    'ONLY_DATA',
    'AnimationSpeed',
    'AnimationEffect',
    'BitmapMode',
    'CellFlags',
    'CellInsertMode',
    'CellContentType',
    'CellDeleteMode',
    'ChartDataCaption',
    'ChartSolidType',
    'ConditionOperator',
    'ControlCharacter',
    'Direction',
    'FillStyle',
    'FillDirection',
    'FormulaResult',
    'LineStyle',
    'Rectangle',
    'SearchType',
    'TextContentAnchorType',
    'TypeAlign',
    'TypeBorder',
    'TypeSource',
    'TypeVerticalAlign',
    'ValidationAlertStyle',
    'ValidationType',
]

# ~ Is de sum of:
# ~ https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1sheet_1_1CellFlags.html
# ~ VALUE, DATETIME, STRING, ANNOTATION, FORMULA
ONLY_DATA = 31

ALL = 1023

SECONDS_DAY = 86400

SEPARATION = 100


class CellInsertMode(IntEnum):
    NONE = 0
    DOWN = 1
    RIGTH = 2
    ROWS = 3
    COLUMNS = 4


class Direction(IntEnum):
    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    LEFT = 4


class FillDirection(IntEnum):
    TO_BOTTOM = 0
    TO_RIGHT = 1
    TO_TOP = 2
    TO_LEFT = 3


class SearchType(IntEnum):
    FORMULA = 0
    VALUE = 1
    NOTE = 2


class TypeBorder(IntEnum):
    WITHOUT_FRAME = 0
    THREE_D = 1
    FLAT = 2


class TypeAlign(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class TypeVerticalAlign(IntEnum):
    TOP = 0
    MIDDLE = 1
    BOTTOM = 2


class TypeSource(IntEnum):
    TABLE = 0
    QUERY = 1
    SQL = 2
