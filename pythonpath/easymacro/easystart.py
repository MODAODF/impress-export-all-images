#!/usr/bin/env python3


class LOStart():
    _type = 'start'

    def __init__(self, obj):
        self._obj = obj

    def __enter__(self):
        return self

    @property
    def obj(self):
        """Return original pyUno object"""
        return self._obj

    @property
    def type(self):
        """Get type document"""
        return self._type

    @property
    def title(self):
        """Get title document"""
        return 'StartModule'
