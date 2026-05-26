#!/usr/bin/env python3

from .easydoc import LODrawImpress
from .easydrawpage import LODrawPage
from .easymain import LOMain


class LODraw(LODrawImpress):
    _type = 'draw'

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        if isinstance(index, int):
            page = self.obj.DrawPages[index]
        else:
            page = self.obj.DrawPages.getByName(index)
        return LODrawPage(page)

    @property
    def active(self):
        """Get active page"""
        return LODrawPage(self._cc.CurrentPage)

    def paste(self):
        """Paste"""
        LOMain.dispatch(self.frame, 'Paste')
        return

