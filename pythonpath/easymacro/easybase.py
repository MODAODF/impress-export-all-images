#!/usr/bin/env python3

from .easydoc import LODocument
from .easymain import BaseObject


class LOBaseSource(BaseObject):
    _type = 'Base Source'

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'{self._type}:'


# ~ main_form = frm_container.component.getDrawPage.getforms.getbyindex(0)
class LOBaseForm(BaseObject):
    _type = 'Base Form'

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'{self._type}: {self.name}'

    @property
    def name(self):
        return self.obj.Name

    def open(self):
        self.obj.open()
        return

    def close(self):
        return self.obj.close()


class LOBaseForms(BaseObject):
    _type = 'Base Forms'

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'Base Forms'

    def __len__(self):
        """Count forms"""
        return self.obj.Count

    def __contains__(self, item):
        """Contains"""
        return item in self.obj

    def __getitem__(self, index):
        """Index access"""
        return LOBaseForm(self.obj[index])


class LOBase(LODocument):
    _type = 'base'

    def __init__(self, obj):
        super().__init__(obj)

    def __str__(self):
        return f'Base: {self.title}'

    @property
    def forms(self):
        return LOBaseForms(self.obj.FormDocuments)