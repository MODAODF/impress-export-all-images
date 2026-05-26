#!/usr/bin/env python3

from .easydoc import LODrawImpress


class LOImpress(LODrawImpress):
    _type = 'impress'

    def __init__(self, obj):
        super().__init__(obj)
