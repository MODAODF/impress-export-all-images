#!/usr/bin/env python3

from .easydoc import LODocument


class LOBasicIDE(LODocument):
    _type = 'basicide'

    def __init__(self, obj):
        super().__init__(obj)
