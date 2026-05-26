#!/usr/bin/env python


from .easymain import log, BaseObject, set_properties, get_properties


STYLE_FAMILIES = 'StyleFamilies'


class LOBaseStyles(BaseObject):

    def __init__(self, obj, create_instance=None):
        super().__init__(obj)
        self._create_intance = create_instance

    def __len__(self):
        return self.obj.Count

    def __contains__(self, item):
        return self.obj.hasByName(item)

    def __getitem__(self, index):
        if index in self:
            style = self.obj.getByName(index)
        else:
            raise IndexError

        if self.NAME == STYLE_FAMILIES:
            s = LOStyles(style, index, self._create_intance)
        else:
            s = LOStyle(style)
        return s

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < self.obj.Count:
            style = self[self.names[self._index]]
        else:
            raise StopIteration

        self._index += 1
        return style

    @property
    def names(self):
        return self.obj.ElementNames


class LOStyle():
    NAME = 'Style'

    def __init__(self, obj):
        self._obj = obj

    def __str__(self):
        return f'Style: {self.name}'

    def __contains__(self, item):
        return hasattr(self.obj, item)

    def __setattr__(self, name, value):
        if name != '_obj':
            self.obj.setPropertyValue(name, value)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        return self.obj.getPropertyValue(name)

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self.obj.Name

    @property
    def is_in_use(self):
        return self.obj.isInUse()

    @property
    def is_user_defined(self):
        return self.obj.isUserDefined()

    @property
    def properties(self):
        return get_properties(self.obj)
    @properties.setter
    def properties(self, values):
        set_properties(self.obj, values)


class LOStyles(LOBaseStyles):
    NAME = 'Styles'

    def __init__(self, obj, type_style, create_instance):
        super().__init__(obj)
        self._type_style = type_style
        self._create_instance = create_instance

    def __str__(self):
        return f'Styles: {self._type_style}'

    def __setitem__(self, key, value):
        if key in self:
            style = self.obj.getByName(key)
        else:
            name = f'com.sun.star.style.{self._type_style[:-1]}'
            style = self._create_instance(name)
            self.obj.insertByName(key, style)
        set_properties(style, value)

    def __delitem__(self, key):
        self.obj.removeByName(key)


class LOStyleFamilies(LOBaseStyles):
    NAME = STYLE_FAMILIES

    def __init__(self, obj, create_instance):
        super().__init__(obj, create_instance)

    def __str__(self):
        return f'Style Families: {self.names}'

    def _validate_name(self, name):
        if not name.endswith('Styles'):
            name = f'{name}Styles'
        return name

    def __contains__(self, item):
        return self.obj.hasByName(self._validate_name(item))

    def __getitem__(self, index):
        if isinstance(index, int):
            index = self.names[index]
        else:
            index = self._validate_name(index)
        return super().__getitem__(index)
