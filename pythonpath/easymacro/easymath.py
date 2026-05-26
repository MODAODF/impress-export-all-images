#!/usr/bin/env python3

from .easydoc import LODocument


class LOMath(LODocument):
    _type = 'math'

    def __init__(self, obj):
        super().__init__(obj)
