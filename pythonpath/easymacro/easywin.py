#!/usr/bin/env python3

from typing import Any

from .easymain import (log, TITLE,
    BaseObject, Color,
    create_instance, set_properties)

# ~ from .easytools import _, LOInspect, Paths, Services, debug, mri


__all__ = [
    'LOWindow',
]


class Window(BaseObject):

    def __init__(self, properties: dict={}):
        obj = self._create(properties)
        super().__init__(obj)

    def _create(self, properties: dict):
        win = 'ok'
        return win


class LOWindow():
    @classmethod
    def create(cls, properties: dict={}):
        return Window(properties)


