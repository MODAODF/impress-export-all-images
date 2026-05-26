#!/usr/bin/env python3

import uno
import unohelper
from com.sun.star.io import IOException, XOutputStream
from com.sun.star.lang import Locale
from .easymain import Paths, create_instance


# UNO Enum
class MessageBoxType():
    """Class for import enum

    `See Api MessageBoxType <https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1awt.html#ad249d76933bdf54c35f4eaf51a5b7965>`_
    """
    from com.sun.star.awt.MessageBoxType \
        import MESSAGEBOX, INFOBOX, WARNINGBOX, ERRORBOX, QUERYBOX


class LineStyle():
    from com.sun.star.drawing.LineStyle import NONE, SOLID, DASH


class FillStyle():
    from com.sun.star.drawing.FillStyle import NONE, SOLID, GRADIENT, HATCH, BITMAP


class BitmapMode():
    from com.sun.star.drawing.BitmapMode import REPEAT, STRETCH, NO_REPEAT


class CellContentType():
    from com.sun.star.table.CellContentType import EMPTY, VALUE, TEXT, FORMULA


class CellDeleteMode():
    from com.sun.star.sheet.CellDeleteMode import UP, LEFT, ROWS, COLUMNS


class ValidationType():
    from com.sun.star.sheet.ValidationType import ANY, WHOLE, DECIMAL, DATE, \
        TIME, TEXT_LEN, LIST, CUSTOM


class ValidationAlertStyle():
    from com.sun.star.sheet.ValidationAlertStyle import STOP, WARNING, INFO, MACRO


class WindowAttribute():
    from com.sun.star.awt.WindowAttribute import BORDER, CLOSEABLE, FULLSIZE, MINSIZE, MOVEABLE, \
        NODECORATION, OPTIMUMSIZE, SHOW, SIZEABLE, SYSTEMDEPENDENT
    DEFAULT = BORDER + CLOSEABLE + MOVEABLE + SIZEABLE


class WindowClass():
    from com.sun.star.awt.WindowClass import TOP, MODALTOP, CONTAINER, SIMPLE


class AnimationEffect():
    from com.sun.star.presentation.AnimationEffect import \
        FADE_FROM_LEFT, FADE_FROM_TOP, FADE_FROM_RIGHT, FADE_FROM_BOTTOM


class AnimationSpeed():
    from com.sun.star.presentation.AnimationSpeed import SLOW, MEDIUM, FAST


class TextContentAnchorType():
    from com.sun.star.text.TextContentAnchorType \
        import AT_PARAGRAPH, AS_CHARACTER, AT_PAGE, AT_FRAME, AT_CHARACTER


class IOStream(object):
    """Classe for input/output stream"""

    class OutputStream(unohelper.Base, XOutputStream):

        def __init__(self):
            self._buffer = b''
            self.closed = 0

        @property
        def buffer(self):
            return self._buffer

        def closeOutput(self):
            self.closed = 1

        def writeBytes(self, seq):
            if seq.value:
                self._buffer = seq.value

        def flush(self):
            pass

    @classmethod
    def buffer(cls):
        return io.BytesIO()

    @classmethod
    def input(cls, buffer):
        service = 'com.sun.star.io.SequenceInputStream'
        stream = create_instance(service, True)
        stream.initialize((uno.ByteSequence(buffer.getvalue()),))
        return stream

    @classmethod
    def output(cls):
        return cls.OutputStream()

    @classmethod
    def to_bin(cls, stream):
        buffer = cls.OutputStream()
        _, data = stream.readBytes(buffer, stream.available())
        return data.value


def get_input_stream(data):
    stream = create_instance('com.sun.star.io.SequenceInputStream', True)
    stream.initialize((data,))
    return stream


class BaseObjectProperties():

    def __init__(self, obj):
        self._obj = obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __contains__(self, item):
        return hasattr(self.obj, item)

    def __setattr__(self, name, value):
        if name == '_obj':
            super().__setattr__(name, value)
        else:
            if name in self:
                if name == 'FillBitmapURL':
                    value = Paths.to_url(value)
                setattr(self.obj, name, value)
            else:
                object.__setattr__(self, name, value)

    def __getattr__(self, name):
        return self.obj.getPropertyValue(name)

    @property
    def obj(self):
        return self._obj
